import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock

# Set testing environment
os.environ["TESTING"] = "1"
os.environ["TELEGRAM_BOT_TOKEN"] = "mock_bot_token_123456:ABCDEF"

import main

class TestTelegramBotCommands(unittest.TestCase):
    def setUp(self):
        self.sent_messages = []
        self.sent_photos = []
        
    def mock_post(self, url, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "ok": True,
            "result": {"message_id": 999, "chat": {"id": 12345678}}
        }
        
        json_data = kwargs.get("json", {})
        if "sendMessage" in url:
            self.sent_messages.append(json_data)
        elif "sendPhoto" in url:
            self.sent_photos.append(json_data)
        return mock_resp

    def simulate_message(self, text, user_id=12345678, username="anaa2700", wait_sec=2.5, condition=None):
        update = {
            "update_id": 10001,
            "message": {
                "message_id": 101,
                "from": {"id": user_id, "username": username, "first_name": "Admin"},
                "chat": {"id": user_id, "type": "private"},
                "date": 1700000000,
                "text": text
            }
        }
        with patch("requests.post", side_effect=self.mock_post):
            main.xu_ly_telegram_update(update)
            start_time = time.time()
            if condition:
                while time.time() - start_time < wait_sec:
                    if condition(self.sent_messages, self.sent_photos):
                        break
                    time.sleep(0.1)
            else:
                time.sleep(wait_sec)

    def test_start_menu(self):
        self.sent_messages.clear()
        self.simulate_message("/start")
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("HỆ THỐNG ANX", all_text)
        print("PASS: /start menu")

    def test_tintuc(self):
        self.sent_messages.clear()
        self.sent_photos.clear()
        mock_articles = [
            {
                "title": "Bản tin thời sự thử nghiệm",
                "description": "Nội dung tóm tắt bài báo thời sự",
                "source": "🌐 VnExpress",
                "link": "https://vnexpress.net/test-1",
                "image": "https://vnexpress.net/thumb.jpg"
            }
        ]
        with patch.object(main, "lay_bai_viet_moi_chua_gui", return_value=mock_articles), \
             patch.object(main, "job_cap_nhat_docs_tin_tuc", return_value=None):
            self.simulate_message(
                "/tintuc",
                wait_sec=5.0,
                condition=lambda msgs, photos: any("BẢN TIN TIÊU ĐIỂM" in m.get("text", "") for m in msgs)
            )
            all_text = " ".join([m.get("text", "") for m in self.sent_messages])
            self.assertIn("BẢN TIN TIÊU ĐIỂM", all_text)
            self.assertTrue(len(self.sent_photos) > 0 or "Bản tin thời sự" in all_text)
            print("PASS: /tintuc")

    def test_thoitiethientai(self):
        self.sent_messages.clear()
        self.simulate_message(
            "/thoitiethientai",
            wait_sec=10.0,
            condition=lambda msgs, photos: any("THỜI TIẾT HIỆN TẠI" in m.get("text", "") for m in msgs)
        )
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("THỜI TIẾT HIỆN TẠI", all_text)
        print("PASS: /thoitiethientai")

    def test_thoitiet_diadiem(self):
        self.sent_messages.clear()
        self.simulate_message(
            "/thoitiet Đà Nẵng",
            wait_sec=10.0,
            condition=lambda msgs, photos: any("THỜI TIẾT TẠI" in m.get("text", "") for m in msgs)
        )
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("THỜI TIẾT TẠI", all_text)
        print("PASS: /thoitiet [địa điểm]")

    def test_vung(self):
        self.sent_messages.clear()
        self.simulate_message(
            "/vung Hà Nội",
            wait_sec=5.0,
            condition=lambda msgs, photos: any("Đã chuyển vùng mặc định" in m.get("text", "") for m in msgs)
        )
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("Đã chuyển vùng mặc định", all_text)
        print("PASS: /vung [tên vùng]")

    def test_websitecn(self):
        self.sent_messages.clear()
        mock_articles = [
            {
                "title": "Tin thời tiết công nghệ",
                "description": "Chi tiết tin tức",
                "source": "Báo Mới",
                "link": "https://baomoi.com/1",
                "image": ""
            }
        ]
        with patch.object(main, "lay_bai_viet_moi_chua_gui", return_value=mock_articles):
            self.simulate_message(
                "/websitecn",
                wait_sec=12.0,
                condition=lambda msgs, photos: any("Giao Diện Web" in m.get("text", "") or "Mở website:" in m.get("text", "") for m in msgs)
            )
            all_text = " ".join([m.get("text", "") for m in self.sent_messages])
            self.assertTrue("Giao Diện Web" in all_text or "Mở website:" in all_text)
            self.assertIn("http", all_text)
            print("PASS: /websitecn")

    def test_shopee(self):
        self.sent_messages.clear()
        self.simulate_message("/shopee", wait_sec=2.0)
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("KHO MÃ SHOPEE", all_text)
        print("PASS: /shopee")

    def test_shopeefd(self):
        self.sent_messages.clear()
        self.simulate_message("/shopeefd", wait_sec=2.0)
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("DEAL SHOPEEFOOD", all_text)
        print("PASS: /shopeefd")

    def test_tinhcn_flow(self):
        self.sent_messages.clear()
        # Reset session
        main.user_sessions["12345678"] = {"step": None, "data": {}}
        self.simulate_message("/tinhcn", wait_sec=2.0)
        all_text1 = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("QUẢN LÝ TÍNH TIỀN PHÒNG & ĐIỆN NƯỚC", all_text1)
        self.assertIn("1682;1820;811;819;8", all_text1)
        
        # Now enter values: 1682;1820;811;819;8
        self.sent_messages.clear()
        self.simulate_message("1682;1820;811;819;8", wait_sec=2.0)
        all_text2 = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("HÓA ĐƠN TIỀN NHÀ", all_text2)
        self.assertIn("TỔNG CỘNG:", all_text2)
        # Check tracking_data saved lock key
        self.assertEqual(main.tracking_data.get("12345678"), 8)
        self.assertTrue(main.user_sessions["12345678"].get("pending_sonuocngay"))
        print("PASS: /tinhcn quick 1-line workflow")

    def test_tinh_interactive_flow(self):
        self.sent_messages.clear()
        # Reset session
        main.user_sessions["12345678"] = {"step": None, "data": {}}
        self.simulate_message("/tinh", wait_sec=2.0)
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("Bước 1/5", all_text)

        # Step 1: nhap_dien_cu
        self.sent_messages.clear()
        self.simulate_message("1682", wait_sec=2.0)
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("Bước 2/5", all_text)

        # Step 2: nhap_dien_moi
        self.sent_messages.clear()
        self.simulate_message("1820", wait_sec=2.0)
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("Bước 3/5", all_text)

        # Step 3: nhap_nuoc_cu
        self.sent_messages.clear()
        self.simulate_message("811", wait_sec=2.0)
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("Bước 4/5", all_text)

        # Step 4: nhap_nuoc_moi
        self.sent_messages.clear()
        self.simulate_message("819", wait_sec=2.0)
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("Bước 5/5", all_text)

        # Step 5: nhap_so_khoa
        self.sent_messages.clear()
        self.simulate_message("8", wait_sec=2.0)
        all_text = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("HÓA ĐƠN TIỀN NHÀ", all_text)
        self.assertIn("TỔNG CỘNG:", all_text)
        self.assertEqual(main.tracking_data.get("12345678"), 8)
        self.assertTrue(main.user_sessions["12345678"].get("pending_sonuocngay"))
        print("PASS: /tinh interactive 5-step workflow")

    def test_sonuocngay_flow(self):
        self.sent_messages.clear()
        main.user_sessions["12345678"] = {"step": None, "pending_sonuocngay": True, "data": {}}
        main.tracking_data["12345678"] = 8
        self.simulate_message(".sonuocngay", wait_sec=2.0)
        all_text1 = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("BÁO CÁO NƯỚC NGÀY", all_text1)
        
        # Admin inputs: 0.5
        self.sent_messages.clear()
        with patch.object(main, "them_lich_chot_nuoc", return_value=(True, "Đã thêm vào Google Calendar thành công!")):
            self.simulate_message("0.5", wait_sec=2.0)
            all_text2 = " ".join([m.get("text", "") for m in self.sent_messages])
            self.assertIn("LỊCH CHỐT NƯỚC", all_text2)
            self.assertIn("Đã thêm vào Google Calendar thành công!", all_text2)
            # Pending flag should now be False
            self.assertFalse(main.user_sessions["12345678"].get("pending_sonuocngay"))
            print("PASS: .sonuocngay workflow with Calendar integration")

    def test_gemini_chat_flow(self):
        self.sent_messages.clear()
        self.simulate_message("/startgemini", wait_sec=2.0)
        all_text1 = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("PHIÊN AI ĐÃ MỞ", all_text1)
        
        self.sent_messages.clear()
        self.simulate_message("/endgemini", wait_sec=2.0)
        all_text2 = " ".join([m.get("text", "") for m in self.sent_messages])
        self.assertIn("PHIÊN AI KẾT THÚC", all_text2)
        print("PASS: /startgemini and /endgemini")

    def test_baocao_flow(self):
        self.sent_messages.clear()
        with patch.object(main, "tao_bao_cao_powerpoint", return_value="📊 <b>BÁO CÁO TIẾN ĐỘ POWERPOINT</b>\nTổng số bài: 10"), \
             patch.object(main, "day_du_lieu_google_sheets", return_value=(True, "Đã đồng bộ 2 tab TOAN và TIENGVIET")):
            self.simulate_message(
                "/baocao",
                wait_sec=5.0,
                condition=lambda msgs, photos: any("Đồng bộ Google Sheets" in m.get("text", "") for m in msgs)
            )
            all_text = " ".join([m.get("text", "") for m in self.sent_messages])
            self.assertIn("BÁO CÁO TIẾN ĐỘ POWERPOINT", all_text)
            self.assertIn("Đồng bộ Google Sheets", all_text)
            print("PASS: /baocao workflow with PowerPoint and Sheets sync")

    def test_jobs(self):
        # Hourly weather job
        main.active_auto_news_chats.add("12345678")
        with patch("requests.post", side_effect=self.mock_post):
            main.job_thoi_tiet_hang_gio()
        # Hourly news job
        main.user_last_news_sent.clear()
        with patch("requests.post", side_effect=self.mock_post):
            main.job_tu_dong_day_tin()
        print("PASS: scheduler jobs")

if __name__ == "__main__":
    unittest.main()
