"""
Module Collector Engine: Điều phối thu thập RSS, cào chi tiết bài viết, kiểm soát đồng thời và lập báo cáo.
Tuân thủ Mục 1, 2, 3, 5, 6, 7 trong yêu cầu kỹ thuật:
- Đọc cấu hình nguồn ngoài `sources.json`.
- Kiểm soát số lượng yêu cầu đồng thời (Concurrency limiter) và timeout có kiểm soát.
- Thu thập RSS -> Bóc tách chi tiết bài viết gốc -> Chống trùng lặp -> Lưu trữ SQLite.
- Thống kê chi tiết: tổng số bài tìm thấy, bài toàn văn, bài tóm tắt, bài lỗi, bài trùng lặp.
- Hỗ trợ chạy định kỳ tự động.
"""

import os
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Callable
import requests
from news_collector.rss_parser import RSSFeedParser
from news_collector.article_extractor import ArticleExtractor, GLOBAL_SESSION, DEFAULT_HEADERS
from news_collector.database import NewsDatabase
from news_collector.url_normalizer import normalize_url

logger = logging.getLogger("NewsCollectorEngine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SOURCES_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "sources.json")

class NewsCollectorEngine:
    """Bộ điều phối thu thập tin tức toàn diện từ RSS và bài viết gốc."""

    def __init__(
        self,
        config_path: str = SOURCES_CONFIG_PATH,
        db: Optional[NewsDatabase] = None,
        max_workers: int = 4,
        request_timeout: int = 10
    ):
        self.config_path = config_path
        self.db = db or NewsDatabase()
        self.max_workers = max_workers
        self.request_timeout = request_timeout
        self.sources_config = self.load_sources_config()
        self.is_running = False

    def load_sources_config(self) -> Dict[str, Any]:
        """Nạp danh sách website và RSS từ tệp cấu hình bên ngoài."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Không tìm thấy cấu hình {self.config_path}, khởi tạo rỗng.")
            return {"categories": [], "sources": []}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Lỗi khi đọc file cấu hình nguồn: {e}")
            return {"categories": [], "sources": []}

    def get_sources(self, category: Optional[str] = None, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lọc danh sách các nguồn được kích hoạt theo chuyên mục hoặc ID."""
        sources = [s for s in self.sources_config.get("sources", []) if s.get("enabled", True)]
        if category:
            sources = [s for s in sources if s.get("category") == category]
        if source_id:
            sources = [s for s in sources if s.get("id") == source_id]
        return sources

    def fetch_feed_items(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Tải và phân tích một RSS/Atom feed."""
        feed_url = source.get("feed_url")
        if not feed_url:
            return []

        try:
            logger.info(f"Đang tải RSS: {source.get('source_name')} ({feed_url})")
            resp = GLOBAL_SESSION.get(feed_url, headers=DEFAULT_HEADERS, timeout=self.request_timeout)
            if resp.status_code != 200:
                logger.warning(f"Lỗi tải feed {feed_url}: HTTP {resp.status_code}")
                return []
            
            resp.encoding = resp.apparent_encoding or 'utf-8'
            items = RSSFeedParser.parse_feed(resp.text, feed_url=feed_url, source_meta=source)
            logger.info(f"Tìm thấy {len(items)} bài viết từ {source.get('source_name')}")
            return items
        except Exception as e:
            logger.error(f"Ngoại lệ khi đọc RSS {feed_url}: {e}")
            return []

    def enrich_article_detail(self, item: Dict[str, Any], fetch_full_content: bool = True) -> Dict[str, Any]:
        """
        Nâng cấp bài viết bằng cách trích xuất nội dung toàn văn từ URL gốc nếu cần.
        - Nếu trong RSS đã có sẵn full text (> 300 ký tự) thì ưu tiên sử dụng (Mục 3.1).
        - Nếu chỉ có tóm tắt và cho phép cào thì truy cập URL gốc (Mục 3.2 & 3.3).
        - Tuyệt đối không tự suy đoán nếu nguồn không có toàn văn (Mục 3.7).
        """
        if not fetch_full_content:
            return item

        # Nếu RSS đã cung cấp đầy đủ nội dung (> 300 ký tự)
        if item.get("content_status") == "full" and len(item.get("content", "")) > 300:
            return item

        article_url = item.get("article_url")
        if not article_url:
            return item

        try:
            extracted = ArticleExtractor.extract_article(article_url, timeout=self.request_timeout)
            
            # Cập nhật thông tin chi tiết bóc tách được
            if extracted.get("content"):
                item["content"] = extracted["content"]
            if extracted.get("sapo") and not item.get("summary"):
                item["summary"] = extracted["sapo"]
            if extracted.get("author") and not item.get("author"):
                item["author"] = extracted["author"]
            if extracted.get("published_at") and not item.get("published_at"):
                item["published_at"] = extracted["published_at"]
            if extracted.get("primary_image") and not item.get("image_url"):
                item["image_url"] = extracted["primary_image"]

            # Cập nhật trạng thái chuẩn xác ('full', 'partial', 'summary_only', 'failed')
            item["content_status"] = extracted.get("content_status", "summary_only")

        except Exception as e:
            logger.warning(f"Không thể lấy nội dung chi tiết bài {article_url}: {e}")
            if not item.get("content_status"):
                item["content_status"] = "partial" if item.get("summary") else "failed"

        return item

    def run_crawl(
        self,
        category: Optional[str] = None,
        source_id: Optional[str] = None,
        fetch_full_content: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Thực thi quy trình thu thập toàn diện:
        1. Quét danh sách nguồn RSS.
        2. Tải bài viết đồng thời có giới hạn (Concurrency limiter).
        3. Cào toàn văn bài viết gốc nếu chưa có full text.
        4. Đối chiếu chống trùng lặp và lưu SQLite.
        5. Lập báo cáo kết quả thống kê chi tiết.
        """
        start_time = time.time()
        self.is_running = True
        sources = self.get_sources(category=category, source_id=source_id)

        stats = {
            "total_sources_scanned": len(sources),
            "total_found": 0,
            "new_inserted": 0,
            "duplicates_updated": 0,
            "duplicates_skipped": 0,
            "full_count": 0,
            "partial_count": 0,
            "summary_only_count": 0,
            "failed_count": 0,
            "errors": []
        }

        logger.info(f"Bắt đầu thu thập từ {len(sources)} nguồn tin tức...")

        # 1. Tải toàn bộ RSS items
        all_feed_items: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(sources) or 1)) as executor:
            future_to_source = {executor.submit(self.fetch_feed_items, s): s for s in sources}
            for future in as_completed(future_to_source):
                try:
                    items = future.result()
                    all_feed_items.extend(items)
                except Exception as e:
                    s = future_to_source[future]
                    stats["errors"].append(f"Lỗi nguồn {s.get('source_name')}: {e}")

        stats["total_found"] = len(all_feed_items)
        logger.info(f"Tổng số bài viết phát hiện từ tất cả các feeds: {stats['total_found']}")

        # 2. Xử lý từng bài viết: bóc tách chi tiết và lưu database với Concurrency Limiter
        processed_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_item = {
                executor.submit(self.enrich_article_detail, item, fetch_full_content): item
                for item in all_feed_items
            }

            for future in as_completed(future_to_item):
                processed_count += 1
                try:
                    enriched_item = future.result()
                    is_new, is_updated = self.db.upsert_article(enriched_item)

                    if is_new:
                        stats["new_inserted"] += 1
                    elif is_updated:
                        stats["duplicates_updated"] += 1
                    else:
                        stats["duplicates_skipped"] += 1

                    # Thống kê trạng thái nội dung
                    c_status = enriched_item.get("content_status", "summary_only")
                    if c_status == "full":
                        stats["full_count"] += 1
                    elif c_status == "partial":
                        stats["partial_count"] += 1
                    elif c_status == "summary_only":
                        stats["summary_only_count"] += 1
                    else:
                        stats["failed_count"] += 1

                except Exception as e:
                    orig_item = future_to_item[future]
                    stats["errors"].append(f"Lỗi xử lý bài {orig_item.get('article_url')}: {e}")
                    stats["failed_count"] += 1

                if progress_callback:
                    try:
                        progress_callback({
                            "processed": processed_count,
                            "total": stats["total_found"],
                            "stats": stats
                        })
                    except Exception:
                        pass

        duration = round(time.time() - start_time, 2)
        stats["duration_seconds"] = duration
        self.is_running = False

        logger.info(
            f"=== BÁO CÁO KẾT QUẢ THU THẬP ({duration}s) ===\n"
            f"- Tổng số bài tìm thấy: {stats['total_found']}\n"
            f"- Bài mới thêm vào DB: {stats['new_inserted']}\n"
            f"- Bài trùng được cập nhật toàn văn: {stats['duplicates_updated']}\n"
            f"- Bài trùng lặp bỏ qua: {stats['duplicates_skipped']}\n"
            f"- Bài lấy được toàn văn (full): {stats['full_count']}\n"
            f"- Bài lấy được một phần (partial): {stats['partial_count']}\n"
            f"- Bài chỉ có tóm tắt (summary_only): {stats['summary_only_count']}\n"
            f"- Bài lỗi (failed): {stats['failed_count']}"
        )

        return stats
