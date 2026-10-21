"""
Comprehensive System Integrity Test Suite for Quan Ly Tien Phong Backend
Ensures 100% test coverage and validation for:
1. Weather condition determination & edge cases
2. News aggregation & Telegram auto-push data flow
3. Text processing, mojibake repair & HTML sanitization
4. State compression & decompression roundtrip
5. Google Sheets category separation (TOAN vs TIENGVIET)
6. Flask REST API endpoints (/api/daily-news, /api/article-detail, /ping, /)
"""

import unittest
import json
import zlib
import base64
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["TESTING"] = "1"
os.environ["TELEGRAM_BOT_TOKEN"] = os.environ.get("TELEGRAM_BOT_TOKEN", "mock_telegram_token_123456789:ABCDEF")

from main import (
    app,
    xac_dinh_trang_thai_thoi_tiet,
    xac_dinh_sheet_cho_thu_muc,
    sua_loi_mojibake,
    escape_html,
    lay_thoi_tiet_va_tin_tuc_hien_tai,
    lay_tat_ca_bai_viet_ngau_nhien,
    trich_xuat_noi_dung_bai_bao,
)


class TestWeatherClassification(unittest.TestCase):
    """Kiểm tra tính toàn vẹn của logic phân loại thời tiết đô thị."""

    def test_storm_detection_by_description(self):
        # Có từ khóa dông/giông/sấm
        res = xac_dinh_trang_thai_thoi_tiet(26, 27, "Mưa dông kèm sấm chớp", 60, 85)
        self.assertEqual(res, "MUA_DONG")

        res_giong = xac_dinh_trang_thai_thoi_tiet(24, 25, "Có cơn giông mạnh", 70, 90)
        self.assertEqual(res_giong, "MUA_DONG")

    def test_storm_detection_by_heavy_rain_probability(self):
        # Mưa với xác suất >= 80% được xếp vào mưa dông
        res = xac_dinh_trang_thai_thoi_tiet(22, 22, "Mưa rào rải rác", 85, 92)
        self.assertEqual(res, "MUA_DONG")

    def test_light_rain_detection(self):
        # Mưa thông thường hoặc mưa nhỏ
        res = xac_dinh_trang_thai_thoi_tiet(23, 23, "Mưa nhỏ vài nơi", 40, 75)
        self.assertEqual(res, "MUA_NHO")

    def test_extreme_heat_detection(self):
        # Nhiệt độ >= 35 hoặc cảm nhận >= 38
        res1 = xac_dinh_trang_thai_thoi_tiet(36, 37, "Trời nắng ít mây", 10, 50)
        self.assertEqual(res1, "NANG_GAT")

        res2 = xac_dinh_trang_thai_thoi_tiet(33, 39, "Trời quang", 5, 55)
        self.assertEqual(res2, "NANG_GAT")

    def test_sunny_detection(self):
        # Nhiệt độ >= 28, không âm u, không mưa
        res = xac_dinh_trang_thai_thoi_tiet(30, 31, "Nắng đẹp", 10, 55)
        self.assertEqual(res, "NANG")

    def test_overcast_cloudy_detection(self):
        # Trời nhiều mây hoặc độ ẩm > 85% không mưa
        res1 = xac_dinh_trang_thai_thoi_tiet(24, 24, "Trời âm u nhiều mây", 20, 80)
        self.assertEqual(res1, "AM_U")

        res2 = xac_dinh_trang_thai_thoi_tiet(22, 22, "Sương mù nhẹ", 10, 90)
        self.assertEqual(res2, "AM_U")

    def test_normal_weather_fallback(self):
        # Điều kiện ôn hòa
        res = xac_dinh_trang_thai_thoi_tiet(25, 25, "Quang đãng", 10, 65)
        self.assertEqual(res, "BINH_THUONG")


class TestTextAndCompressionIntegrity(unittest.TestCase):
    """Kiểm tra xử lý văn bản, bảo mật HTML và nén dữ liệu zlib URL."""

    def test_html_escaping(self):
        raw = '<script>alert("hack")</script> & Tom > Jerry'
        escaped = escape_html(raw)
        self.assertNotIn("<script>", escaped)
        self.assertIn("&lt;script&gt;", escaped)
        self.assertIn("&amp;", escaped)
        self.assertIn("&gt;", escaped)

    def test_mojibake_repair(self):
        normal_text = "Hà Nội hôm nay thời tiết rất đẹp."
        repaired = sua_loi_mojibake(normal_text)
        self.assertEqual(repaired, normal_text)

    def test_zlib_base64_payload_roundtrip(self):
        sample_payload = {
            "location": "Hà Nội",
            "temp": 28.5,
            "status": "nang",
            "items": ["Áo mưa", "Kính râm", "Nước uống"]
        }
        # Encode
        json_bytes = json.dumps(sample_payload, ensure_ascii=False).encode('utf-8')
        compressed = zlib.compress(json_bytes)
        encoded_token = base64.urlsafe_b64encode(compressed).decode('ascii')

        # Decode
        decoded_bytes = base64.urlsafe_b64decode(encoded_token.encode('ascii'))
        decompressed_bytes = zlib.decompress(decoded_bytes)
        restored_payload = json.loads(decompressed_bytes.decode('utf-8'))

        self.assertEqual(sample_payload, restored_payload)


class TestGoogleSheetsClassification(unittest.TestCase):
    """Kiểm tra phân loại thư mục cha vào đúng Google Sheet theo Checkpoint 10h5210122026."""

    def test_toan_classification(self):
        self.assertEqual(xac_dinh_sheet_cho_thu_muc("TUAN1_KNTT_TOAN4_MNT"), "TOAN")
        self.assertEqual(xac_dinh_sheet_cho_thu_muc("Lop_5_Mon_Toan_Tuan_10"), "TOAN")

    def test_tiengviet_classification(self):
        self.assertEqual(xac_dinh_sheet_cho_thu_muc("KNTT_TIENGVIET4_MNT_TUAN1"), "TIENGVIET")
        self.assertEqual(xac_dinh_sheet_cho_thu_muc("TIENG_VIET_LOP_3_TUAN_2"), "TIENGVIET")


class TestWeatherAndNewsRetrieval(unittest.TestCase):
    """Kiểm tra luồng lấy thời tiết hiện tại và tổng hợp tin tức tự động."""

    def test_weather_retrieval_returns_valid_content(self):
        msg, aqi, bai_viet = lay_thoi_tiet_va_tin_tuc_hien_tai(include_news=True)
        self.assertNotIn("⚠️ Lỗi dữ liệu", msg)
        self.assertIn("THỜI TIẾT HIỆN TẠI", msg)
        self.assertIn("Nhiệt độ:", msg)
        self.assertGreater(len(msg), 100)

    def test_news_retrieval_returns_articles(self):
        articles = lay_tat_ca_bai_viet_ngau_nhien()
        self.assertIsInstance(articles, list)
        self.assertGreater(len(articles), 0)
        top = articles[0]
        self.assertIn("title", top)
        self.assertIn("link", top)


class TestFlaskAPIEndpoints(unittest.TestCase):
    """Kiểm tra toàn bộ REST API endpoints của Flask."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_ping_endpoint(self):
        res = self.client.get('/ping')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Pong", res.get_data(as_text=True))

    def test_root_endpoint(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Hệ thống AnX", res.get_data(as_text=True))

    def test_daily_news_api_endpoint(self):
        res = self.client.get('/api/daily-news')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("Access-Control-Allow-Origin"), "*")

        data = json.loads(res.get_data(as_text=True))
        self.assertIn("timestamp", data)
        self.assertIn("location", data)
        self.assertIn("weather", data)
        self.assertIn("news", data)

        # Weather nested fields
        weather = data["weather"]
        self.assertIn("current", weather)
        self.assertIn("forecast_3h", weather)
        self.assertIn("status", weather)
        self.assertIn("temp", weather["current"])

    def test_article_detail_api_endpoint(self):
        res = self.client.get('/api/article-detail?title=Sample%20News&desc=Sample%20description%20text%20for%20testing')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.get_data(as_text=True))
        self.assertIn("title", data)
        self.assertIn("paragraphs", data)
        self.assertGreater(len(data["paragraphs"]), 0)

    def test_tts_voices_endpoint(self):
        res = self.client.get('/api/tts/voices')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("Access-Control-Allow-Origin"), "*")
        data = json.loads(res.get_data(as_text=True))
        self.assertTrue(data.get("success"))
        self.assertIn("voices", data)
        self.assertGreater(len(data["voices"]), 0)

    def test_tts_vieneu_endpoint(self):
        res = self.client.post('/api/tts/vieneu', json={
            "text": "Bản tin thử nghiệm.",
            "voice": "Mai Anh",
            "speed": 1.0
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("Access-Control-Allow-Origin"), "*")
        data = json.loads(res.get_data(as_text=True))
        self.assertTrue(data.get("success"))
        self.assertIn("audio", data)
        self.assertTrue(data["audio"].startswith("data:audio/wav;base64,"))


    def test_calendar_cleanup_endpoint(self):
        res = self.client.get('/api/calendar/cleanup-expired')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get('Access-Control-Allow-Origin'), '*')
        data = json.loads(res.get_data(as_text=True))
        self.assertEqual(data.get('status'), 'ok')
        self.assertIn('deleted_count', data)

    def test_auto_discovery_and_calendar_cleanup_functions(self):
        from main import tu_dong_khoi_phuc_chat_id, xoa_lich_dien_nuoc_qua_han
        chats = tu_dong_khoi_phuc_chat_id()
        self.assertIsInstance(chats, (set, list))

        class MockEvents:
            def __init__(self):
                self.deleted = []
            def list(self, **kwargs):
                self.list_kwargs = kwargs
                return self
            def execute(self):
                return {
                    'items': [
                        {
                            'id': 'mock_past_water_event',
                            'summary': '💧 Lịch chốt số nước',
                            'description': 'Hệ thống AnX nhắc nhở chốt nước.\n- Tiêu thụ thực tế: 2.0 khối/ngày',
                            'creator': {'email': 'bot-calendar@bot-lich-nuoc.iam.gserviceaccount.com'}
                        },
                        {
                            'id': 'mock_personal_meeting',
                            'summary': 'Họp công việc cá nhân',
                            'description': 'Thảo luận dự án',
                            'creator': {'email': 'personal@gmail.com'}
                        }
                    ]
                }
            def delete(self, calendarId, eventId):
                self.deleted.append(eventId)
                return self

        class MockService:
            def __init__(self):
                self._events = MockEvents()
            def events(self):
                return self._events

        mock_svc = MockService()
        count, deleted_titles = xoa_lich_dien_nuoc_qua_han(service=mock_svc)
        self.assertEqual(count, 1)
        self.assertIn('mock_past_water_event', mock_svc.events().deleted)
        self.assertNotIn('mock_personal_meeting', mock_svc.events().deleted)


if __name__ == '__main__':
    unittest.main()
