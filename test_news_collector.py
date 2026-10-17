"""
Bộ kiểm thử toàn diện hệ thống Thu thập Tin tức & Bóc tách Toàn văn (VietNews Collector).
Kiểm tra 100% các tiêu chí từ Mục 1 đến Mục 7 theo tài liệu đặc tả yêu cầu kỹ thuật.
"""

import os
import sys
import json
import unittest
import tempfile
import pandas as pd

# Đảm bảo đường dẫn module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from news_collector.url_normalizer import normalize_url, generate_title_signature
from news_collector.rss_parser import RSSFeedParser, parse_vietnamese_or_rfc_date
from news_collector.article_extractor import ArticleExtractor
from news_collector.database import NewsDatabase
from news_collector.collector_engine import NewsCollectorEngine

class TestNewsCollectorSystem(unittest.TestCase):

    def setUp(self):
        # Tạo file SQLite tạm thời cho kiểm thử
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db = NewsDatabase(db_path=self.temp_db_path)

    def tearDown(self):
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────
    # MỤC 1: KIỂM TRA NGUỒN DỮ LIỆU & CẤU HÌNH NGOÀI
    # ─────────────────────────────────────────────────────────────
    def test_sources_configuration_loaded(self):
        """Mục 1: Kiểm tra nạp danh sách website và RSS ngoài, phân loại theo 7 chuyên mục."""
        engine = NewsCollectorEngine(db=self.db)
        config = engine.sources_config
        self.assertIn("categories", config)
        self.assertIn("sources", config)

        categories = {c["id"] for c in config["categories"]}
        expected_cats = {
            "thoi_su_xa_hoi",
            "cong_nghe_ai",
            "gioi_tre_doi_song",
            "giao_duc_tuyen_sinh",
            "kinh_te_tai_chinh",
            "giai_tri_van_hoa",
            "khoa_hoc_suc_khoe"
        }
        self.assertTrue(expected_cats.issubset(categories), "Cấu hình phải có đủ 7 nhóm chuyên mục theo yêu cầu")
        self.assertGreater(len(config["sources"]), 10, "Cần có danh sách nguồn RSS thực tế phong phú")

    # ─────────────────────────────────────────────────────────────
    # MỤC 2: KIỂM TRA THU THẬP DỮ LIỆU RSS & ATOM
    # ─────────────────────────────────────────────────────────────
    def test_rss_feed_parsing(self):
        """Mục 2: Bóc tách đầy đủ các trường của bài viết từ RSS 2.0."""
        sample_rss = """<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
            <channel>
                <title>Báo Tiền Phong - Xã hội</title>
                <link>https://tienphong.vn</link>
                <item>
                    <title><![CDATA[ Hà Nội triển khai cắt tỉa hoa sữa giảm mùi hương ]]></title>
                    <link>https://tienphong.vn/ha-noi-trien-khai-cat-tia-hoa-sua-post12345.tpo?utm_source=rss&amp;utm_medium=feed</link>
                    <guid isPermaLink="false">tienphong_12345</guid>
                    <pubDate>Sun, 18 Oct 2026 00:05:00 +0700</pubDate>
                    <description><![CDATA[ <a href="#"><img src="https://static.tienphong.vn/images/hoa-sua.jpg" /></a>Lực lượng chức năng tiến hành cắt tỉa các chùm hoa sữa tại các tuyến phố trọng điểm. ]]></description>
                    <author>Tiến Dũng</author>
                    <category>Xã hội</category>
                </item>
            </channel>
        </rss>
        """
        articles = RSSFeedParser.parse_feed(sample_rss, feed_url="https://tienphong.vn/rss/xa-hoi.rss")
        self.assertEqual(len(articles), 1)
        a = articles[0]
        self.assertEqual(a["title"], "Hà Nội triển khai cắt tỉa hoa sữa giảm mùi hương")
        self.assertEqual(a["article_url"], "https://tienphong.vn/ha-noi-trien-khai-cat-tia-hoa-sua-post12345.tpo")
        self.assertEqual(a["guid"], "tienphong_12345")
        self.assertEqual(a["author"], "Tiến Dũng")
        self.assertIn("Lực lượng chức năng", a["summary"])
        self.assertEqual(a["image_url"], "https://static.tienphong.vn/images/hoa-sua.jpg")
        self.assertIn("2026-10-18", a["published_at"])

    def test_atom_feed_parsing(self):
        """Mục 2: Bóc tách bài viết từ chuẩn Atom feed."""
        sample_atom = """<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>VnExpress Atom Feed</title>
            <entry>
                <title>Startup AI Việt Nam gọi vốn thành công 10 triệu USD</title>
                <link rel="alternate" href="https://vnexpress.net/startup-ai-goi-von-10-trieu-usd.html?fbclid=xyz" />
                <id>urn:vnexpress:news:9999</id>
                <published>2026-10-17T15:30:00+07:00</published>
                <updated>2026-10-17T16:00:00+07:00</updated>
                <summary>Doanh nghiệp khởi nghiệp công nghệ AI vừa hoàn tất vòng hạt giống.</summary>
                <author><name>Hoàng Nam</name></author>
            </entry>
        </feed>
        """
        articles = RSSFeedParser.parse_feed(sample_atom, feed_url="https://vnexpress.net/atom.xml")
        self.assertEqual(len(articles), 1)
        a = articles[0]
        self.assertEqual(a["title"], "Startup AI Việt Nam gọi vốn thành công 10 triệu USD")
        self.assertEqual(a["article_url"], "https://vnexpress.net/startup-ai-goi-von-10-trieu-usd.html")
        self.assertEqual(a["guid"], "urn:vnexpress:news:9999")
        self.assertEqual(a["author"], "Hoàng Nam")

    # ─────────────────────────────────────────────────────────────
    # MỤC 3: KIỂM TRA LẤY NỘI DUNG CHI TIẾT & BẢO TOÀN DỮ LIỆU
    # ─────────────────────────────────────────────────────────────
    def test_article_extractor_full_content(self):
        """Mục 3: Trích xuất tiêu đề, sapo, thân bài, tiêu đề phụ, ảnh minh họa, chú thích; lọc sạch quảng cáo."""
        sample_html = """<!DOCTYPE html>
        <html>
        <head>
            <title>Hoa sữa nở nồng nặc - Báo VietNamNet</title>
            <meta property="og:title" content="Hoa sữa nở nồng nặc, người dân có được tự ý cắt tỉa cây trước nhà?" />
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "NewsArticle",
                "headline": "Hoa sữa nở nồng nặc, người dân có được tự ý cắt tỉa cây trước nhà?",
                "datePublished": "2026-10-18T00:05:00+07:00",
                "author": {"@type": "Person", "name": "Tiến Dũng"}
            }
            </script>
        </head>
        <body>
            <nav><a href="/">Trang chủ</a></nav>
            <div class="ads">Quảng cáo sốc</div>
            <div class="content-detail">
                <h1 class="title">Hoa sữa nở nồng nặc, người dân có được tự ý cắt tỉa cây trước nhà?</h1>
                <div class="content-detail-sapo">
                    Hoa sữa nở rộ, tỏa mùi hương nồng nặc, ảnh hưởng đến sinh hoạt của người dân. Vậy người dân có được tự ý cắt tỉa cây trước nhà?
                </div>
                <div id="maincontent" class="maincontent">
                    <p>Ngày 16/10, lực lượng chức năng Hà Nội triển khai cắt tỉa các chùm hoa sữa tại một số khu vực có mật độ cây cao.</p>
                    <figure>
                        <img data-original="https://static-images.vnncdn.net/images/hoa-sua-1.jpg" alt="Hàng hoa sữa" />
                        <figcaption>Những hàng cây hoa sữa trước nhà dân</figcaption>
                    </figure>
                    <p>Vào mùa hoa nở, hương hoa sữa có thể lan tỏa trên diện rộng. Với những người nhạy cảm, mùi hương gây khó chịu.</p>
                    <p><strong>Không được tự ý cắt tỉa cây xanh công cộng</strong></p>
                    <p>Trao đổi về vấn đề này, luật sư Vũ Anh Tuấn cho biết cần phân biệt cây trồng trước nhà là tài sản cá nhân hay cây xanh công cộng.</p>
                    <p>Như vậy, dù cây hoa sữa nằm ngay trước nhà, người dân không nên tự ý chặt tỉa mà cần báo cáo chính quyền.</p>
                    <div class="ck-cms-insert-neww-group">
                        <a href="/tin-khac.html">Hà Nội đang dùng xe chuyên dụng cắt tỉa hoa sữa</a>
                    </div>
                </div>
            </div>
            <footer>Bản quyền thuộc về VietNamNet</footer>
        </body>
        </html>
        """
        extracted = ArticleExtractor.parse_html_content(sample_html, "https://vietnamnet.vn/bai-viet.html")
        self.assertEqual(extracted["title"], "Hoa sữa nở nồng nặc, người dân có được tự ý cắt tỉa cây trước nhà?")
        self.assertEqual(extracted["author"], "Tiến Dũng")
        self.assertIn("Hoa sữa nở rộ", extracted["sapo"])
        self.assertEqual(extracted["content_status"], "full")
        self.assertGreaterEqual(extracted["paragraph_count"], 4)
        
        # Kiểm tra tiêu đề phụ nhận diện định dạng markdown ###
        self.assertIn("### Không được tự ý cắt tỉa cây xanh công cộng", extracted["content"])
        # Kiểm tra ảnh và chú thích
        self.assertEqual(len(extracted["images"]), 1)
        self.assertEqual(extracted["images"][0]["caption"], "Những hàng cây hoa sữa trước nhà dân")
        # Kiểm tra các phần tử rác (quảng cáo, footer, tin liên quan) đã được loại bỏ
        self.assertNotIn("Quảng cáo sốc", extracted["content"])
        self.assertNotIn("Bản quyền thuộc về VietNamNet", extracted["content"])

    def test_article_extractor_summary_only_no_fabrication(self):
        """Mục 3.6 & 3.7: Trang bị tường phí / chặn không tự bịa đặt nội dung, đánh dấu summary_only hoặc partial."""
        paywall_html = """<!DOCTYPE html>
        <html>
        <head><title>Tin tức VIP</title></head>
        <body>
            <h1>Bài viết phân tích chuyên sâu</h1>
            <div class="sapo">Nội dung tóm tắt được công bố rộng rãi cho độc giả.</div>
            <div class="paywall-lock">Vui lòng đăng nhập để đọc tiếp toàn văn bài viết.</div>
        </body>
        </html>
        """
        extracted = ArticleExtractor.parse_html_content(paywall_html, "https://baovip.vn/bai-1.html")
        self.assertEqual(extracted["content_status"], "summary_only")
        # Tuyệt đối không tự suy đoán thêm văn bản
        self.assertEqual(extracted["content"], "Nội dung tóm tắt được công bố rộng rãi cho độc giả.")

    # ─────────────────────────────────────────────────────────────
    # MỤC 4 & MỤC 5: CHUẨN HÓA DỮ LIỆU & CHỐNG TRÙNG LẶP
    # ─────────────────────────────────────────────────────────────
    def test_url_normalization(self):
        """Mục 5: Chuẩn hóa URL, loại bỏ toàn bộ tham số tracking."""
        raw_url = "https://Vietnamnet.vn/bai-viet-123.html/?utm_source=facebook&utm_medium=cpc&fbclid=IwAR123&ref=home#comment"
        clean = normalize_url(raw_url)
        self.assertEqual(clean, "https://vietnamnet.vn/bai-viet-123.html")

    def test_database_deduplication_and_update(self):
        """Mục 5: Chống trùng lặp theo URL/GUID và cập nhật bản ghi nếu có nội dung toàn văn tốt hơn."""
        # 1. Chèn bài viết ở dạng chỉ có tóm tắt
        initial_article = {
            "source_name": "VietNamNet - Thời sự",
            "category": "thoi_su_xa_hoi",
            "feed_url": "https://vietnamnet.vn/rss/thoi-su.rss",
            "article_url": "https://vietnamnet.vn/hoa-sua.html?utm_source=rss",
            "title": "Hoa sữa nở nồng nặc tại Hà Nội",
            "author": "Tiến Dũng",
            "published_at": "2026-10-18T00:05:00+07:00",
            "summary": "Tóm tắt ngắn gọn trong RSS feed",
            "content": "",
            "image_url": "https://vnncdn.net/img.jpg",
            "tags": ["Hoa sữa", "Hà Nội"],
            "content_status": "summary_only",
            "guid": "vnn_hoa_sua_1"
        }
        is_new, is_updated = self.db.upsert_article(initial_article)
        self.assertTrue(is_new, "Bài viết đầu tiên phải được chèn mới")
        self.assertFalse(is_updated)

        # 2. Cùng bài viết đó nhưng sau khi cào chi tiết lấy được full content
        full_article = {
            "source_name": "VietNamNet - Thời sự",
            "category": "thoi_su_xa_hoi",
            "feed_url": "https://vietnamnet.vn/rss/thoi-su.rss",
            "article_url": "https://vietnamnet.vn/hoa-sua.html?fbclid=xyz",  # URL khác param tracking nhưng cùng canonical
            "title": "Hoa sữa nở nồng nặc tại Hà Nội",
            "author": "Tiến Dũng",
            "published_at": "2026-10-18T00:05:00+07:00",
            "summary": "Tóm tắt ngắn gọn trong RSS feed",
            "content": "Toàn văn 10 đoạn văn thân bài chi tiết đã được trích xuất thành công...",
            "image_url": "https://vnncdn.net/img.jpg",
            "tags": ["Hoa sữa", "Hà Nội"],
            "content_status": "full",
            "guid": "vnn_hoa_sua_1"
        }
        is_new_2, is_updated_2 = self.db.upsert_article(full_article)
        self.assertFalse(is_new_2, "Không được tạo bài viết mới khi URL/GUID trùng")
        self.assertTrue(is_updated_2, "Bản ghi cũ phải được nâng cấp lên 'full'")

        # 3. Gửi lại bài full một lần nữa -> phải bỏ qua (không tạo bản sao, không tốn tài nguyên update)
        is_new_3, is_updated_3 = self.db.upsert_article(full_article)
        self.assertFalse(is_new_3)
        self.assertFalse(is_updated_3)

        # Kiểm tra tổng số bài trong DB vẫn là 1 và trạng thái là 'full'
        articles = self.db.query_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["content_status"], "full")
        self.assertIn("Toàn văn 10 đoạn", articles[0]["content"])

    # ─────────────────────────────────────────────────────────────
    # MỤC 6: KIỂM TRA LƯU TRỮ, BỘ LỌC VÀ XUẤT DỮ LIỆU
    # ─────────────────────────────────────────────────────────────
    def test_database_queries_and_export(self):
        """Mục 6: Lọc bài viết đa chiều và xuất dữ liệu JSON, CSV, Excel."""
        # Chèn vài bài test
        self.db.upsert_article({
            "source_name": "VnExpress - Số hóa",
            "category": "cong_nghe_ai",
            "article_url": "https://vnexpress.net/ai-1.html",
            "title": "Mô hình ngôn ngữ lớn tiếng Việt đột phá",
            "author": "Bảo Trâm",
            "published_at": "2026-10-18T10:00:00+07:00",
            "summary": "AI Việt Nam đạt chuẩn benchmark mới.",
            "content": "Thân bài phân tích chi tiết công nghệ AI...",
            "content_status": "full",
            "guid": "vne_ai_1"
        })
        self.db.upsert_article({
            "source_name": "Tiền Phong - Xã hội",
            "category": "thoi_su_xa_hoi",
            "article_url": "https://tienphong.vn/giao-thong-1.html",
            "title": "Đảm bảo an toàn giao thông đô thị",
            "author": "Quang Minh",
            "published_at": "2026-10-17T08:00:00+07:00",
            "summary": "Kế hoạch tuần tra xử lý vi phạm giao thông.",
            "content": "",
            "content_status": "summary_only",
            "guid": "tp_gt_1"
        })

        # 1. Kiểm tra bộ lọc category
        ai_articles = self.db.query_articles(category="cong_nghe_ai")
        self.assertEqual(len(ai_articles), 1)
        self.assertEqual(ai_articles[0]["title"], "Mô hình ngôn ngữ lớn tiếng Việt đột phá")

        # 2. Kiểm tra bộ lọc status
        full_articles = self.db.query_articles(content_status="full")
        self.assertEqual(len(full_articles), 1)

        # 3. Kiểm tra tìm kiếm từ khóa
        search_res = self.db.query_articles(keyword="giao thông")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0]["category"], "thoi_su_xa_hoi")

        # 4. Kiểm tra xuất JSON
        temp_json = tempfile.mktemp(suffix=".json")
        self.db.export_json(temp_json)
        self.assertTrue(os.path.exists(temp_json))
        with open(temp_json, "r", encoding="utf-8") as f:
            j_data = json.load(f)
            self.assertEqual(len(j_data), 2)
        os.remove(temp_json)

        # 5. Kiểm tra xuất CSV
        temp_csv = tempfile.mktemp(suffix=".csv")
        self.db.export_csv(temp_csv)
        self.assertTrue(os.path.exists(temp_csv))
        df_csv = pd.read_csv(temp_csv, encoding="utf-8-sig")
        self.assertEqual(len(df_csv), 2)
        os.remove(temp_csv)

        # 6. Kiểm tra xuất Excel (.xlsx)
        temp_xlsx = tempfile.mktemp(suffix=".xlsx")
        self.db.export_excel(temp_xlsx)
        self.assertTrue(os.path.exists(temp_xlsx))
        df_xlsx = pd.read_excel(temp_xlsx)
        self.assertEqual(len(df_xlsx), 2)
        os.remove(temp_xlsx)

    # ─────────────────────────────────────────────────────────────
    # MỤC 7: KIỂM TRA BÁO CÁO THỐNG KÊ
    # ─────────────────────────────────────────────────────────────
    def test_statistics_reporting(self):
        """Mục 7: Báo cáo kết quả tổng hợp chính xác các chỉ số."""
        self.db.upsert_article({
            "source_name": "Dân Trí - Sức khỏe",
            "category": "khoa_hoc_suc_khoe",
            "article_url": "https://dantri.com.vn/sk-1.html",
            "title": "Chế độ dinh dưỡng mùa đông",
            "content_status": "full",
            "published_at": "2026-10-18T09:00:00+07:00",
            "guid": "dt_sk_1"
        })
        self.db.upsert_article({
            "source_name": "Dân Trí - Sức khỏe",
            "category": "khoa_hoc_suc_khoe",
            "article_url": "https://dantri.com.vn/sk-2.html",
            "title": "Lợi ích của việc chạy bộ",
            "content_status": "partial",
            "published_at": "2026-10-18T09:30:00+07:00",
            "guid": "dt_sk_2"
        })

        stats = self.db.get_statistics()
        self.assertEqual(stats["total_articles"], 2)
        self.assertEqual(stats["full_count"], 1)
        self.assertEqual(stats["partial_count"], 1)
        self.assertEqual(stats["summary_only_count"], 0)
        self.assertEqual(stats["failed_count"], 0)
        self.assertEqual(stats["by_category"].get("khoa_hoc_suc_khoe"), 2)

if __name__ == "__main__":
    unittest.main()
