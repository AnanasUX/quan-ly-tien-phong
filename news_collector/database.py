"""
Module Database: Quản lý lưu trữ SQLite, chống trùng lặp, lọc và xuất dữ liệu.
Tuân thủ Mục 4, Mục 5, Mục 6 và Mục 7 trong yêu cầu kỹ thuật:
- Chuẩn hóa dữ liệu theo đúng schema JSON yêu cầu.
- Chống trùng lặp theo GUID, canonical URL và title hash.
- Cập nhật bài viết khi có bản cập nhật mới thay vì tạo bản sao rác.
- Bộ lọc đa chiều: website, chuyên mục, ngày đăng, trạng thái nội dung, từ khóa.
- Xuất dữ liệu ra JSON, CSV và Excel (.xlsx).
- Thống kê chi tiết kết quả thu thập.
"""

import os
import sqlite3
import json
import csv
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from news_collector.url_normalizer import normalize_url, generate_title_signature

VN_TZ = timezone(timedelta(hours=7))
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "news_database.db")

class NewsDatabase:
    """Quản trị cơ sở dữ liệu SQLite chuyên dụng cho tin tức báo chí."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Khởi tạo bảng articles và hệ thống chỉ mục tăng tốc."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guid TEXT UNIQUE,
                    source_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    feed_url TEXT,
                    article_url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT,
                    published_at TEXT,
                    updated_at TEXT,
                    summary TEXT,
                    content TEXT,
                    image_url TEXT,
                    tags TEXT,
                    content_status TEXT CHECK(content_status IN ('full', 'partial', 'summary_only', 'failed')),
                    fetched_at TEXT,
                    title_hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Tạo chỉ mục cho truy vấn siêu tốc và chống trùng lặp
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(article_url);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_guid ON articles(guid);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_cat ON articles(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_src ON articles(source_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(content_status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_pubdate ON articles(published_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_thash ON articles(title_hash);")
            conn.commit()

    def upsert_article(self, article: Dict[str, Any]) -> Tuple[bool, bool]:
        """
        Lưu hoặc cập nhật bài viết với cơ chế chống trùng lặp:
        Trả về: (is_new, is_updated)
        - Nếu bài mới: (True, False)
        - Nếu trùng nhưng được cập nhật nội dung tốt hơn / mới hơn: (False, True)
        - Nếu trùng lặp hoàn toàn (bỏ qua): (False, False)
        """
        norm_url = normalize_url(article.get("article_url", ""))
        if not norm_url or not article.get("title"):
            return False, False

        guid = article.get("guid") or norm_url
        title = article.get("title", "").strip()
        source_name = article.get("source_name", "Báo điện tử")
        category = article.get("category", "thoi_su_xa_hoi")
        feed_url = article.get("feed_url", "")
        author = article.get("author", "")
        published_at = article.get("published_at", "")
        updated_at = article.get("updated_at") or published_at
        summary = article.get("summary", "")
        content = article.get("content", "")
        image_url = article.get("image_url", "")
        tags_raw = article.get("tags", [])
        tags_json = json.dumps(tags_raw, ensure_ascii=False) if isinstance(tags_raw, list) else "[]"
        content_status = article.get("content_status", "summary_only")
        fetched_at = article.get("fetched_at") or datetime.now(VN_TZ).isoformat()
        title_hash = generate_title_signature(title, source_name)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Kiểm tra tồn tại qua URL, GUID hoặc Title Hash + Source
            cursor.execute("""
                SELECT id, content_status, updated_at, content FROM articles 
                WHERE article_url = ? OR guid = ? OR (source_name = ? AND title_hash = ?)
                LIMIT 1
            """, (norm_url, guid, source_name, title_hash))
            existing = cursor.fetchone()

            if existing:
                existing_id = existing["id"]
                existing_status = existing["content_status"]
                existing_content = existing["content"] or ""

                # Xác định xem bài gửi đến có nội dung đầy đủ hơn không
                status_weight = {'full': 3, 'partial': 2, 'summary_only': 1, 'failed': 0}
                new_weight = status_weight.get(content_status, 0)
                old_weight = status_weight.get(existing_status, 0)

                should_update = False
                # Nếu bài mới có content_status cao hơn (ví dụ cào được full thay vì chỉ có summary)
                if new_weight > old_weight:
                    should_update = True
                elif new_weight == old_weight and len(content) > len(existing_content):
                    should_update = True

                if should_update:
                    cursor.execute("""
                        UPDATE articles SET
                            title = ?,
                            author = COALESCE(NULLIF(?, ''), author),
                            updated_at = ?,
                            summary = COALESCE(NULLIF(?, ''), summary),
                            content = COALESCE(NULLIF(?, ''), content),
                            image_url = COALESCE(NULLIF(?, ''), image_url),
                            tags = ?,
                            content_status = ?,
                            fetched_at = ?
                        WHERE id = ?
                    """, (
                        title, author, updated_at, summary, content, image_url,
                        tags_json, content_status, fetched_at, existing_id
                    ))
                    conn.commit()
                    return False, True
                else:
                    return False, False  # Trùng lặp hoàn toàn, không cần cập nhật

            # 2. Chèn bài viết mới
            cursor.execute("""
                INSERT INTO articles (
                    guid, source_name, category, feed_url, article_url, title,
                    author, published_at, updated_at, summary, content, image_url,
                    tags, content_status, fetched_at, title_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                guid, source_name, category, feed_url, norm_url, title,
                author, published_at, updated_at, summary, content, image_url,
                tags_json, content_status, fetched_at, title_hash
            ))
            conn.commit()
            return True, False

    def query_articles(
        self,
        source_name: Optional[str] = None,
        category: Optional[str] = None,
        content_status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lọc danh sách bài viết theo nhiều tiêu chí với phân trang."""
        query = "SELECT * FROM articles WHERE 1=1"
        params: List[Any] = []

        if source_name:
            query += " AND source_name LIKE ?"
            params.append(f"%{source_name}%")
        if category:
            query += " AND category = ?"
            params.append(category)
        if content_status:
            query += " AND content_status = ?"
            params.append(content_status)
        if from_date:
            query += " AND published_at >= ?"
            params.append(from_date)
        if to_date:
            query += " AND published_at <= ?"
            params.append(to_date)
        if keyword:
            query += " AND (title LIKE ? OR summary LIKE ? OR content LIKE ?)"
            term = f"%{keyword}%"
            params.extend([term, term, term])

        query += " ORDER BY published_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["tags"] = json.loads(item.get("tags") or "[]")
                except Exception:
                    item["tags"] = []
                result.append(item)
            return result

    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Lấy chi tiết một bài viết theo ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            if row:
                item = dict(row)
                try:
                    item["tags"] = json.loads(item.get("tags") or "[]")
                except Exception:
                    item["tags"] = []
                return item
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Thống kê tổng hợp số lượng và trạng thái bài viết."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT content_status, COUNT(*) FROM articles GROUP BY content_status")
            status_counts = dict(cursor.fetchall())

            cursor.execute("SELECT category, COUNT(*) FROM articles GROUP BY category")
            category_counts = dict(cursor.fetchall())

            cursor.execute("SELECT source_name, COUNT(*) FROM articles GROUP BY source_name ORDER BY COUNT(*) DESC LIMIT 10")
            source_counts = dict(cursor.fetchall())

            return {
                "total_articles": total,
                "full_count": status_counts.get("full", 0),
                "partial_count": status_counts.get("partial", 0),
                "summary_only_count": status_counts.get("summary_only", 0),
                "failed_count": status_counts.get("failed", 0),
                "by_category": category_counts,
                "top_sources": source_counts
            }

    def export_json(self, output_path: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """Xuất danh sách bài viết ra tệp JSON chuẩn hóa."""
        filters = filters or {}
        articles = self.query_articles(
            source_name=filters.get("source_name"),
            category=filters.get("category"),
            content_status=filters.get("content_status"),
            from_date=filters.get("from_date"),
            to_date=filters.get("to_date"),
            keyword=filters.get("keyword"),
            limit=filters.get("limit", 10000),
            offset=filters.get("offset", 0)
        )
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        return output_path

    def export_csv(self, output_path: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """Xuất danh sách bài viết ra tệp CSV (UTF-8-SIG mở tốt trong Excel)."""
        filters = filters or {}
        articles = self.query_articles(
            source_name=filters.get("source_name"),
            category=filters.get("category"),
            content_status=filters.get("content_status"),
            from_date=filters.get("from_date"),
            to_date=filters.get("to_date"),
            keyword=filters.get("keyword"),
            limit=filters.get("limit", 10000),
            offset=filters.get("offset", 0)
        )
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        fieldnames = [
            "id", "source_name", "category", "title", "author", "published_at",
            "content_status", "article_url", "image_url", "summary", "content"
        ]
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for a in articles:
                writer.writerow(a)
        return output_path

    def export_excel(self, output_path: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """Xuất danh sách bài viết ra tệp Excel (.xlsx)."""
        filters = filters or {}
        articles = self.query_articles(
            source_name=filters.get("source_name"),
            category=filters.get("category"),
            content_status=filters.get("content_status"),
            from_date=filters.get("from_date"),
            to_date=filters.get("to_date"),
            keyword=filters.get("keyword"),
            limit=filters.get("limit", 10000),
            offset=filters.get("offset", 0)
        )
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Chuyển đổi tags sang string để hiển thị đẹp mắt trong Excel
        cleaned = []
        for a in articles:
            row = dict(a)
            if isinstance(row.get("tags"), list):
                row["tags"] = ", ".join(row["tags"])
            cleaned.append(row)

        df = pd.DataFrame(cleaned)
        # Sắp xếp các cột trực quan
        cols = [c for c in [
            "id", "source_name", "category", "title", "author", "published_at",
            "content_status", "summary", "content", "article_url", "image_url", "tags"
        ] if c in df.columns]
        if cols:
            df = df[cols]
        
        df.to_excel(output_path, index=False, engine='openpyxl')
        return output_path
