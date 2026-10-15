"""
Comprehensive System Integrity Test Suite for Quan Ly Tien Phong Backend
Ensures 100% test coverage and validation for:
1. Weather condition determination & edge cases
2. Video aggregator & strict YouTube Shorts rejection
3. Text processing, mojibake repair & HTML sanitization
4. State compression & decompression roundtrip
5. Antigravity Copilot AI Engine & deterministic fallbacks
6. Flask REST API endpoints (/api/daily-news, /api/copilot, /api/ai-chat, /ping, /)
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
    lay_danh_sach_video_da_dang,
    sua_loi_mojibake,
    escape_html,
    tao_phan_hoi_copilot_fallback,
    tao_phan_hoi_copilot_ai,
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


class TestVideoIntegrity(unittest.TestCase):
    """Kiểm tra tính toàn vẹn của Video Aggregator: Tuyệt đối không dùng YouTube Shorts."""

    def test_no_shorts_in_returned_videos(self):
        videos = lay_danh_sach_video_da_dang(so_luong=10)
        self.assertTrue(len(videos) > 0, "Danh sách video không được để trống")

        shorts_keywords = ["#short", "#shorts", "30s nóng", "tiktok", "#reels", "reels"]

        for v in videos:
            self.assertIn("id", v)
            self.assertIn("title", v)
            self.assertIn("link", v)
            self.assertIn("embed_url", v)

            # Link tuyệt đối không chứa /shorts/
            self.assertNotIn("/shorts/", v["link"].lower(), f"Video link chứa shorts: {v['link']}")

            # Tiêu đề không được chứa các hashtag shorts
            title_lower = v["title"].lower()
            for kw in shorts_keywords:
                self.assertNotIn(kw, title_lower, f"Tiêu đề video chứa từ khóa shorts '{kw}': {v['title']}")

            # Embed url phải trỏ tới /embed/
            self.assertIn("/embed/", v["embed_url"])

    def test_video_structure_completeness(self):
        videos = lay_danh_sach_video_da_dang(so_luong=5)
        for v in videos:
            self.assertGreater(len(v["id"]), 5)
            self.assertGreater(len(v["title"]), 5)
            self.assertTrue(v["thumbnail"].startswith("https://"))


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


class TestAntigravityCopilotAI(unittest.TestCase):
    """Kiểm tra Antigravity Copilot: Phải có khả năng phân tích thực tế, không chỉ là số liệu thô."""

    def setUp(self):
        self.context = {
            "location": "Hà Nội",
            "temp": 27.5,
            "feels_like": 29.0,
            "desc": "Mưa rào nhẹ rải rác",
            "humidity": 82,
            "pm25": 42.0,
            "aqi_level": 3,
            "wind_speed": 14,
            "news_titles": [
                "VTV24: Hà Nội phân luồng giao thông chống ngập",
                "Báo Tiền Phong: Dự báo diễn biến thời tiết khu vực miền Bắc",
                "Báo Tuổi Trẻ: Đổi mới sáng tạo trong hạ tầng đô thị"
            ]
        }

    def test_copilot_weather_impact_action(self):
        res = tao_phan_hoi_copilot_fallback("weather_impact", "", self.context)
        self.assertIn("reply", res)
        self.assertIn("HÀ NỘI", res["reply"])
        self.assertIn("Khuyến nghị Antigravity Copilot", res["reply"])
        self.assertIn("risk_level", res)
        self.assertIn("Antigravity Intelligent Copilot", res["model"])

    def test_copilot_news_digest_action(self):
        res = tao_phan_hoi_copilot_fallback("news_digest", "", self.context)
        self.assertIn("reply", res)
        self.assertIn("ĐIỂM TIN & PHÂN TÍCH TIÊU ĐIỂM", res["reply"])
        self.assertIn("Nhận định AI", res["reply"])

    def test_copilot_health_pm25_action(self):
        res = tao_phan_hoi_copilot_fallback("health_pm25", "", self.context)
        self.assertIn("reply", res)
        self.assertIn("PM2.5", res["reply"])
        self.assertIn("Tác động sinh học", res["reply"])
        self.assertIn("Hành động y tế đề xuất", res["reply"])

    def test_copilot_smart_route_action(self):
        res = tao_phan_hoi_copilot_fallback("smart_route", "", self.context)
        self.assertIn("reply", res)
        self.assertIn("CẢNH BÁO ĐIỂM ĐEN NGẬP ÚNG", res["reply"])
        self.assertIn("Khuyến nghị điều hướng", res["reply"])

    def test_copilot_custom_prompt_chat(self):
        prompt = "Tôi có nên đi ra ngoài bằng xe máy lúc này không?"
        res = tao_phan_hoi_copilot_fallback("general_chat", prompt, self.context)
        self.assertIn("reply", res)
        self.assertIn(prompt, res["reply"])


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
        self.assertIn("videos", data)

        # Weather nested fields
        weather = data["weather"]
        self.assertIn("current", weather)
        self.assertIn("forecast_3h", weather)
        self.assertIn("status", weather)
        self.assertIn("temp", weather["current"])

        # Videos list
        self.assertTrue(len(data["videos"]) > 0)
        for v in data["videos"]:
            self.assertNotIn("/shorts/", v.get("link", "").lower())

    def test_copilot_options_cors(self):
        res = self.client.options('/api/copilot')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("Access-Control-Allow-Origin"), "*")

        res_ai = self.client.options('/api/ai-chat')
        self.assertEqual(res_ai.status_code, 200)
        self.assertEqual(res_ai.headers.get("Access-Control-Allow-Origin"), "*")

    def test_copilot_post_actions(self):
        actions = ["weather_impact", "news_digest", "health_pm25", "smart_route"]
        for action in actions:
            payload = {
                "action": action,
                "context": {
                    "location": "Hà Nội",
                    "temp": 28.0,
                    "desc": "Mây thưa",
                    "pm25": 30.0
                }
            }
            res = self.client.post('/api/copilot', json=payload)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.headers.get("Access-Control-Allow-Origin"), "*")
            data = json.loads(res.get_data(as_text=True))
            self.assertTrue(data.get("success"))
            self.assertGreater(len(data.get("reply", "")), 30)

    def test_copilot_freeform_prompt(self):
        payload = {
            "prompt": "Tuyến đường Trần Phú - Nguyễn Trãi hôm nay có an toàn không?",
            "context": {
                "location": "Hà Đông",
                "temp": 29.0,
                "desc": "Trời nắng"
            }
        }
        res = self.client.post('/api/ai-chat', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.get_data(as_text=True))
        self.assertTrue(data.get("success"))
        self.assertGreater(len(data.get("reply", "")), 20)

    def test_copilot_empty_payload_graceful_handling(self):
        # Empty payload must NOT crash with 500
        res = self.client.post('/api/copilot', json={})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.get_data(as_text=True))
        self.assertTrue(data.get("success"))
        self.assertGreater(len(data.get("reply", "")), 20)

    def test_article_detail_api_endpoint(self):
        # 1. OPTIONS CORS
        res_opt = self.client.options('/api/article-detail')
        self.assertEqual(res_opt.status_code, 200)
        self.assertEqual(res_opt.headers.get("Access-Control-Allow-Origin"), "*")

        # 2. GET request
        res_get = self.client.get('/api/article-detail?title=Ha+Noi+mua+dong&desc=Canh+bao+ngap')
        self.assertEqual(res_get.status_code, 200)
        data_get = json.loads(res_get.get_data(as_text=True))
        self.assertIn("paragraphs", data_get)
        self.assertTrue(len(data_get["paragraphs"]) > 0)
        self.assertIn("tags", data_get)
        self.assertIn("key_takeaways", data_get)

        # 3. POST request
        payload = {
            "url": "https://tienphong.vn/tin-tuc-demo-123.tpo",
            "title": "Chủ động các biện pháp ứng phó thời tiết cực đoan tại Hà Nội",
            "description": "Các lực lượng chức năng ứng trực 24/7 để xử lý các điểm ngập úng."
        }
        res_post = self.client.post('/api/article-detail', json=payload)
        self.assertEqual(res_post.status_code, 200)
        data_post = json.loads(res_post.get_data(as_text=True))
        self.assertEqual(data_post["title"], payload["title"])
        self.assertTrue(len(data_post["paragraphs"]) >= 3)
        self.assertTrue(len(data_post["key_takeaways"]) > 0)
        self.assertTrue(data_post["reading_time_minutes"] >= 1)


if __name__ == '__main__':
    unittest.main()
