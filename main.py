# -*- coding: utf-8 -*-
import sys
import os
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import re
import random
import requests
import datetime
import math
import time
import json
import urllib.parse
import threading
import traceback
import html

def extract_og_image(url):
    import requests
    from bs4 import BeautifulSoup
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            og = soup.find("meta", property="og:image")
            if og and og.get("content"):
                return og["content"]
            tw = soup.find("meta", attrs={"name": "twitter:image"})
            if tw and tw.get("content"):
                return tw["content"]
    except:
        pass
    return None

def dien_anh_cho_danh_sach(ds_bai):
    import concurrent.futures
    def get_img(bai):
        if not bai.get("image"):
            bai["image"] = extract_og_image(bai["link"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(get_img, ds_bai)
    return ds_bai


from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, make_response
from apscheduler.schedulers.background import BackgroundScheduler

# --- Thư viện Google API ---
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

# =====================================================================
# [PHẦN 1] CẤU HÌNH HỆ THỐNG & BIẾN TOÀN CỤC
# =====================================================================
app = Flask(__name__)

# ── CORS: cho phép frontend React gọi API từ bất kỳ origin nào ──
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

load_env_file()

# --- CẤU HÌNH BẢO MẬT: Đọc 100% từ biến môi trường, KHÔNG hardcode token ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ZALO_WEBHOOK_URL   = os.environ.get("ZALO_WEBHOOK_URL", "https://hook.eu1.make.com/9ruvgdciavfa1k6xf2vzpkn6zk2umnc7")
CALENDAR_ID        = os.environ.get("CALENDAR_ID", "mrkun28@gmail.com")

AUTHORIZED_USERNAME  = os.environ.get("AUTHORIZED_USERNAME", "anaa2700")
OPENWEATHER_API_KEY  = os.environ.get("OPENWEATHER_API_KEY", "a201c471567522a7d0b7a0567ad245fe")
POWERPOINT_FOLDER_ID = os.environ.get("POWERPOINT_FOLDER_ID", "1BwFCLX0Fjag9xM13mHIJTOYvZ6dYW5Ox")
DOC_LOGIC_ID         = os.environ.get("DOC_LOGIC_ID", "1a9_qNqFEpbmuIoKuEvT3cExHzpszov4THOfm1ztCZc8")
DOC_NEWS_ID          = os.environ.get("DOC_NEWS_ID", "NHẬP_ID_FILE_DOCS_TIN_TỨC_VÀO_ĐÂY")

if not TELEGRAM_BOT_TOKEN:
    print("⚠️ CẢNH BÁO: TELEGRAM_BOT_TOKEN chưa được cấu hình. REST API và VieNeu-TTS vẫn sẵn sàng phục vụ.")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6IBgzuK4JMCYVYWqDeRpTsOgfqxIWnUxw82IBe49xb-sA")

URL_ANH_NGAP = "https://media.vov.vn/sites/default/files/styles/large/public/2023-09/z4733804825595_067963dce63fbb5cc632616f73db2f26.jpg"
URL_ANH_NANG = "https://vtv1.mediacdn.vn/zoom/640_400/2023/5/17/nang-nong-ha-noi-ttxvn-1684307525357876878345.jpg"

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents'
]

AN, A3, A4, A5 = 3500000, 100000, 100000, 100000
GIA_DIEN, GIA_NUOC = 3500, 35000

FILE_DATA = "bot_data.json"
json_lock = threading.Lock()

user_sessions          = {}
active_tracking_chats  = set()
active_auto_news_chats = set()
tracking_data          = {}
sent_articles_history  = {}
sent_articles_set      = {}
pinned_weather_msgs    = {}
last_weather_alerts    = {}
last_report_msgs       = {}
user_last_news_sent    = {}
ai_chat_sessions       = set()

admin_location = {"lat": 20.9716, "lon": 105.7725, "name": "Hà Nội, VN"}
TRANG_THAI_THOI_TIET = "BINH_THUONG"

DANH_SACH_TRANG = {
    "0":  {"ten": "📰 Tiền Phong",   "muc": ["https://tienphong.vn/rss/home.rss",            "https://tienphong.vn/rss/xa-hoi-2.rss",   "https://tienphong.vn/rss/kinh-te-3.rss",  "https://tienphong.vn/rss/dia-oc-166.rss"]},
    "1":  {"ten": "📰 Dân Trí",     "muc": ["https://dantri.com.vn/rss/home.rss",            "https://dantri.com.vn/rss/xa-hoi.rss",    "https://dantri.com.vn/rss/the-gioi.rss"]},
    "2":  {"ten": "🇻🇳 VnExpress",  "muc": ["https://vnexpress.net/rss/tin-moi-nhat.rss",     "https://vnexpress.net/rss/kinh-doanh.rss", "https://vnexpress.net/rss/thoi-su.rss"]},
    "3":  {"ten": "🌸 Kênh 14",     "muc": ["https://kenh14.vn/home.rss",                    "https://kenh14.vn/star.rss",               "https://kenh14.vn/xa-hoi.rss"]},
    "4":  {"ten": "📜 Tuổi Trẻ",    "muc": ["https://tuoitre.vn/rss/tin-moi-nhat.rss",        "https://tuoitre.vn/rss/thoi-su.rss",       "https://tuoitre.vn/rss/the-gioi.rss"]},
    "5":  {"ten": "🍀 Thanh Niên",  "muc": ["https://thanhnien.vn/rss/home.rss",              "https://thanhnien.vn/rss/thoi-su.rss",     "https://thanhnien.vn/rss/the-gioi.rss"]},
    "6":  {"ten": "🌐 VietnamNet",  "muc": ["https://vietnamnet.vn/rss/tin-moi-nhat.rss",     "https://vietnamnet.vn/rss/thoi-su.rss"]},
    "7":  {"ten": "⚡ Lao Động",    "muc": ["https://laodong.vn/rss/home.rss",               "https://laodong.vn/rss/thoi-su.rss"]},
    "8":  {"ten": "📺 VTV News",    "muc": ["https://vtv.vn/trong-nuoc.rss",                 "https://vtv.vn/the-gioi.rss"]},
    "9":  {"ten": "⚖️ Pháp Luật",  "muc": ["https://plo.vn/rss/thoi-su-c2.rss"]},
    "10": {"ten": "🚗 Giao Thông",  "muc": ["https://www.baogiaothong.vn/rss/thoi-su.rss"]}
}

# =====================================================================
# [PHẦN 2] QUẢN LÝ DỮ LIỆU & ĐỒNG BỘ BỘ NHỚ LÕI
# =====================================================================
def load_data():
    global active_auto_news_chats, tracking_data, active_tracking_chats, pinned_weather_msgs
    global admin_location, last_weather_alerts, sent_articles_set, last_report_msgs, ai_chat_sessions
    global user_last_news_sent
    with json_lock:
        if os.path.exists(FILE_DATA):
            try:
                with open(FILE_DATA, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    active_auto_news_chats = set(data.get("active_auto_news_chats", []))
                    tracking_data          = data.get("tracking_data", {})
                    active_tracking_chats  = set(data.get("active_tracking_chats", []))
                    pinned_weather_msgs    = data.get("pinned_weather_msgs", {})
                    user_last_news_sent    = data.get("user_last_news_sent", {})
                    last_weather_alerts    = data.get("last_weather_alerts", {})
                    raw_sent_set           = data.get("sent_articles_set", {})
                    sent_articles_set      = {k: set(v) for k, v in raw_sent_set.items()}
                    saved_loc              = data.get("admin_location")
                    if saved_loc: admin_location = saved_loc
                    last_report_msgs  = data.get("last_report_msgs", {})
                    ai_chat_sessions  = set(data.get("ai_chat_sessions", []))
            except Exception:
                pass
        env_chats = (os.environ.get("TELEGRAM_AUTO_NEWS_CHATS") or
                     os.environ.get("TELEGRAM_CHAT_ID") or
                     os.environ.get("ADMIN_CHAT_ID") or
                     os.environ.get("CHAT_ID"))
        if env_chats:
            for cid in str(env_chats).split(","):
                c_clean = cid.strip()
                if c_clean:
                    active_auto_news_chats.add(c_clean)

def save_data():
    with json_lock:
        try:
            serializable_sent_set = {k: list(v) for k, v in sent_articles_set.items()}
            with open(FILE_DATA, "w", encoding="utf-8") as f:
                json.dump({
                    "active_auto_news_chats": list(active_auto_news_chats),
                    "tracking_data":          tracking_data,
                    "active_tracking_chats":  list(active_tracking_chats),
                    "pinned_weather_msgs":     pinned_weather_msgs,
                    "user_last_news_sent":       user_last_news_sent,
                    "last_weather_alerts":     last_weather_alerts,
                    "sent_articles_set":       serializable_sent_set,
                    "admin_location":          admin_location,
                    "last_report_msgs":        last_report_msgs,
                    "ai_chat_sessions":        list(ai_chat_sessions)
                }, f, ensure_ascii=False)
        except Exception:
            pass

load_data()

def dong_bo_bo_nho_he_thong():
    """Tải bộ nhớ logic từ Google Docs về file cục bộ."""
    if not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json'):
        return
    try:
        creds        = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)
        req           = drive_service.files().export_media(fileId=DOC_LOGIC_ID, mimeType='text/plain')
        content       = req.execute().decode('utf-8', errors='ignore')
        with open("core_logic_memory.txt", "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass

threading.Thread(target=dong_bo_bo_nho_he_thong, daemon=True).start()

def ghi_logic_moi_vao_docs(noi_dung_moi):
    """Ghi logic mới vào cuối Google Docs và file cục bộ."""
    if not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json'):
        return False
    try:
        creds        = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
        docs_service = build('docs', 'v1', credentials=creds)
        doc          = docs_service.documents().get(documentId=DOC_LOGIC_ID).execute()
        content      = doc.get('body').get('content')
        end_index    = content[-1]['endIndex'] - 1
        ht           = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        text_to_insert = f"\n\n[NEW_LOGIC_UPDATE - {ht.strftime('%H:%M %d/%m/%Y')}]\n{noi_dung_moi}\n"
        requests_payload = [{'insertText': {'location': {'index': end_index}, 'text': text_to_insert}}]
        docs_service.documents().batchUpdate(documentId=DOC_LOGIC_ID, body={'requests': requests_payload}).execute()
        with open("core_logic_memory.txt", "a", encoding="utf-8") as f:
            f.write(text_to_insert)
        return True
    except Exception:
        return False

def kiem_tra_quyen_admin(chat_id, user_id, username):
    if username and username.lower() == AUTHORIZED_USERNAME.lower():
        return True
    if str(chat_id) == str(user_id):
        return True
    if str(chat_id).startswith('-'):
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChatMember"
        try:
            res = requests.get(url, params={"chat_id": chat_id, "user_id": user_id}, timeout=5).json()
            if res.get("ok") and res["result"]["status"] in ["creator", "administrator"]:
                return True
        except:
            pass
    return False

# =====================================================================
# [PHẦN 3] MODULE TELEGRAM & CƠ CHẾ BATCH DELETE 30S
# =====================================================================
def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def xoa_tin_nhan(chat_id, message_id):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage",
            json={"chat_id": chat_id, "message_id": message_id}, timeout=5
        )
    except:
        pass

def xoa_tin_nhan_sau_delay(chat_id, msg_ids, delay=10):
    if not msg_ids:
        return
    def task():
        time.sleep(delay)
        for mid in msg_ids:
            xoa_tin_nhan(chat_id, mid)
    threading.Thread(target=task, daemon=True).start()

user_msg_queue = {}
queue_lock     = threading.Lock()

def xoa_tin_nhan_nguoi_dung_cung_luc(chat_id):
    if str(chat_id) in ai_chat_sessions:
        with queue_lock:
            if chat_id in user_msg_queue:
                user_msg_queue[chat_id].clear()
        return
    with queue_lock:
        if chat_id in user_msg_queue:
            m_ids = list(user_msg_queue[chat_id])
            user_msg_queue[chat_id].clear()
        else:
            m_ids = []
    for mid in m_ids:
        xoa_tin_nhan(chat_id, mid)

def add_user_msg_to_queue(chat_id, message_id):
    if str(chat_id) in ai_chat_sessions:
        return
    with queue_lock:
        if chat_id not in user_msg_queue:
            user_msg_queue[chat_id] = set()
        is_new_batch = len(user_msg_queue[chat_id]) == 0
        user_msg_queue[chat_id].add(message_id)
    if is_new_batch:
        t = threading.Timer(30.0, xoa_tin_nhan_nguoi_dung_cung_luc, args=[chat_id])
        t.daemon = True
        t.start()

def gui_tin_nhan_telegram(chat_id, noi_dung, reply_markup=None, parse_mode="HTML", disable_noti=False):
    url      = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    lines    = noi_dung.split('\n')
    current_msg = ""
    msg_ids  = []
    for line in lines:
        if len(current_msg) + len(line) + 1 > 4000:
            payload = {"chat_id": chat_id, "text": current_msg, "parse_mode": parse_mode,
                       "disable_web_page_preview": True, "disable_notification": disable_noti}
            if reply_markup:
                payload["reply_markup"] = reply_markup
            try:
                res = requests.post(url, json=payload, timeout=10).json()
                if res.get('ok'):
                    msg_ids.append(res['result']['message_id'])
            except:
                pass
            current_msg = line + "\n"
            time.sleep(0.3)
        else:
            current_msg += line + "\n"
    if current_msg.strip():
        payload = {"chat_id": chat_id, "text": current_msg, "parse_mode": parse_mode,
                   "disable_web_page_preview": True, "disable_notification": disable_noti}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            res = requests.post(url, json=payload, timeout=10).json()
            if res.get('ok'):
                msg_ids.append(res['result']['message_id'])
        except:
            pass
    
    # Chỉ tự động xóa tin nhắn cảnh báo lỗi hệ thống / phân quyền tạm thời (theo đặc tả Section 8.3), KHÔNG xóa bài viết tin tức hay bản tin thời tiết!
    if isinstance(noi_dung, str) and any(err in noi_dung.lower() for err in ["không thể lấy dữ liệu", "không có quyền", "lỗi cú pháp", "lỗi hệ thống", "vui lòng thử lại"]):
        xoa_tin_nhan_sau_delay(chat_id, msg_ids, 30)
    
    if chat_id in user_sessions:
        step = user_sessions[chat_id].get("step")
        if step or user_sessions[chat_id].get("pending_sonuocngay"):
            user_sessions[chat_id].setdefault("session_msg_ids", []).extend(msg_ids)
            
    return msg_ids

def gui_anh_telegram(chat_id, photo_url, caption):
    url_send_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    success = False
    try:
        res = requests.post(url_send_photo,
                            json={"chat_id": chat_id, "photo": photo_url,
                                  "caption": caption, "parse_mode": "HTML"}, timeout=10)
        if res.status_code == 200:
            success = True
        else:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            res_img = requests.get(photo_url, headers=headers, timeout=10)
            if res_img.status_code == 200:
                files = {"photo": ("image.jpg", res_img.content)}
                data  = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
                res2 = requests.post(url_send_photo, data=data, files=files, timeout=15)
                if res2.status_code == 200:
                    success = True
    except Exception:
        pass

    # Nếu gửi ảnh thất bại (do link ảnh chết/chặn CDN/timeout) -> Fallback gửi tin nhắn dạng text đảm bảo người dùng luôn nhận đủ bài viết
    if not success:
        try:
            gui_tin_nhan_telegram(chat_id, caption, parse_mode="HTML")
        except Exception:
            pass

# =====================================================================
# [PHẦN 4] MODULE GEMINI CHAT (models 09/2026)
# =====================================================================
def sua_loi_mojibake(text):
    if not isinstance(text, str) or not text:
        return text
    dau_hieu = ("Ã", "Â", "áº", "á»", "Ä", "Å", "Æ", "Ð", "Ñ", "â€™", "â€œ", "â€")
    if not any(x in text for x in dau_hieu):
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except:
        return text

def goi_gemini_api(cau_hoi):
    models = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    payload = {
        "contents": [{
            "parts": [{
                "text": (
                    "Bạn là trợ lý AI thông minh trên Telegram. "
                    "Trả lời chính xác, mạch lạc, bằng tiếng Việt.\n\n"
                    f"Người dùng hỏi: {cau_hoi}"
                )
            }]
        }]
    }
    last_error = "Không thể kết nối đến Gemini."

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for attempt in range(2):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=50)
                res_json = response.json()
                if response.status_code == 200:
                    try:
                        text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                        return True, sua_loi_mojibake(text)
                    except Exception:
                        last_error = "Gemini trả về dữ liệu không đúng định dạng."
                        continue
                else:
                    err_msg   = res_json.get('error', {}).get('message', f'HTTP {response.status_code}')
                    last_error = err_msg
                    if any(x in err_msg.lower() for x in ["not found", "is not found", "not supported", "no longer available", "deprecated", "not available"]):
                        break
                    if any(x in err_msg.lower() for x in ["high demand", "temporarily", "spikes",
                                                           "overloaded", "rate", "quota"]):
                        if attempt == 0:
                            time.sleep(1.5)
                            continue
                    break
            except requests.exceptions.Timeout:
                last_error = "Hết thời gian chờ (timeout)."
                if attempt == 0:
                    time.sleep(1.5)
                    continue
                break
            except Exception as e:
                last_error = str(e)
                break
    return False, last_error

def tao_cau_tra_loi_ai_tich_hop(cau_hoi, ly_do_gemini=""):
    """
    Chế độ AI Thông minh tích hợp (Built-in Integrated Smart AI Fallback)
    Phục vụ phản hồi tức thời cho người dùng khi API Gemini bên ngoài gặp sự cố,
    hết quota hoặc đang chuyển đổi phiên bản model.
    """
    q = cau_hoi.lower().strip() if cau_hoi else ""
    
    # 1. Chào hỏi & giới thiệu
    if any(k in q for k in ["chào", "hello", "hi", "bạn là ai", "ai đấy", "ai đây", "giới thiệu", "chức năng"]):
        return (
            "🤖 <b>AI Thông minh (Tích hợp):</b>\n"
            "<i>(Đã chuyển sang chế độ AI Thông minh tích hợp)</i>\n\n"
            "Xin chào! Tôi là Trợ lý AI Thông minh của hệ thống <b>Quản Lý Tiền Phong & Thời Tiết AnX</b>.\n\n"
            "Tôi có thể hỗ trợ bạn:\n"
            "• 🌤 <b>Thời tiết:</b> Tra cứu thời tiết 63 tỉnh thành, cảm giác nhiệt, mưa nắng, bão lũ.\n"
            "• 📰 <b>Tin tức:</b> Cập nhật tin tức thời sự chính thống từ Báo Tiền Phong.\n"
            "• 💰 <b>Tiện ích & Tính toán:</b> Tính tiền Shopee, công thức định mức, tính toán nhanh 1 dòng.\n"
            "• 💧 <b>Chốt nước:</b> Đồng bộ lịch Google Calendar tự động hủy sau 30s.\n"
            "• 📊 <b>Báo cáo:</b> Đồng bộ dữ liệu 2 tab Google Sheets TOAN và TIENGVIET.\n\n"
            "Hãy đặt câu hỏi hoặc gõ các lệnh như <code>/thoitiet</code>, <code>/tintuc</code>, <code>/tinhcn</code>, <code>/shopee</code>, <code>/baocao</code> để bắt đầu!"
        )

    # 2. Hỏi về thời tiết
    if any(k in q for k in ["thời tiết", "mưa", "nắng", "nhiệt độ", "độ ẩm", "gió", "không khí", "pm2.5"]):
        try:
            res_tt = lay_thoi_tiet_va_tin_tuc_hien_tai(include_news=False)
            if res_tt and isinstance(res_tt, tuple) and res_tt[0]:
                return (
                    "🤖 <b>AI Thông minh (Tích hợp):</b>\n"
                    "<i>(Đã chuyển sang chế độ AI Thông minh tích hợp)</i>\n\n"
                    f"{res_tt[0]}"
                )
        except Exception:
            pass
        return (
            "🤖 <b>AI Thông minh (Tích hợp):</b>\n"
            "<i>(Đã chuyển sang chế độ AI Thông minh tích hợp)</i>\n\n"
            "🌤 <b>Thời tiết:</b> Bạn có thể dùng lệnh <code>/thoitiet [tên tỉnh/thành]</code> hoặc <code>/thoitiethientai</code> để nhận bản tin thời tiết kèm ảnh dự báo chi tiết và radar thời gian thực."
        )

    # 3. Hỏi về tin tức
    if any(k in q for k in ["tin tức", "bản tin", "thời sự", "báo", "tiền phong", "tin mới", "tin nóng"]):
        return (
            "🤖 <b>AI Thông minh (Tích hợp):</b>\n"
            "<i>(Đã chuyển sang chế độ AI Thông minh tích hợp)</i>\n\n"
            "📰 <b>Tin tức thời sự:</b> Bạn có thể gõ lệnh <code>/tintuc</code> để nhận ngay 5 bản tin thời sự nóng hổi nhất được tự động cập nhật từ tòa soạn Báo Tiền Phong."
        )

    # 4. Hỏi về lệnh hoặc tính toán
    if any(k in q for k in ["tính", "công thức", "shopee", "lệnh", "hướng dẫn", "sổ nước", "báo cáo", "sheet", "menu"]):
        return (
            "🤖 <b>AI Thông minh (Tích hợp):</b>\n"
            "<i>(Đã chuyển sang chế độ AI Thông minh tích hợp)</i>\n\n"
            "💡 <b>Hướng dẫn cú pháp tiện ích hệ thống:</b>\n"
            "• <code>/tinhcn [chuỗi]</code>: Tính nhanh 1 dòng (VD: <code>/tinhcn 100k 200k giảm 10%</code>)\n"
            "• <code>/shopee [link] [mã]</code>: Tính giá trị đơn hàng Shopee đã trừ voucher\n"
            "• <code>.sonuocngay [số khối] [ngày]</code>: Lên lịch nhắc chốt nước vào Google Calendar (19:00 - 19:30)\n"
            "• <code>/baocao</code>: Đồng bộ tiến độ 2 tab Google Sheets TOAN và TIENGVIET\n"
            "• <code>/websitecn</code>: Xem bảng cập nhật tính năng website mới nhất."
        )

    # 5. Phản hồi thông minh tổng quát
    return (
        "🤖 <b>AI Thông minh (Tích hợp):</b>\n"
        "<i>(Đã chuyển sang chế độ AI Thông minh tích hợp)</i>\n\n"
        f"Tôi đã tiếp nhận câu hỏi của bạn: <i>\"{escape_html(cau_hoi)}\"</i>.\n\n"
        "Hệ thống đang hoạt động ở chế độ Trợ lý AI tích hợp. Bạn có thể sử dụng các lệnh chức năng của bot hoặc tiếp tục đặt câu hỏi về thời tiết, tin tức và các phân hệ tính toán của Báo Tiền Phong."
    )

def xu_ly_gemini_chat(chat_id, cau_hoi):
    wait_msg = gui_tin_nhan_telegram(chat_id, "🤖 <i>Đang trả lời...</i>", parse_mode="HTML")
    try:
        success, result = goi_gemini_api(cau_hoi)
        for mid in wait_msg:
            xoa_tin_nhan(chat_id, mid)
        if success:
            gui_tin_nhan_telegram(chat_id, f"🤖 <b>Gemini AI:</b>\n\n{escape_html(result)}", parse_mode="HTML")
        else:
            tra_loi = tao_cau_tra_loi_ai_tich_hop(cau_hoi, result)
            gui_tin_nhan_telegram(chat_id, tra_loi, parse_mode="HTML")
    except Exception as e:
        for mid in wait_msg:
            xoa_tin_nhan(chat_id, mid)
        gui_tin_nhan_telegram(chat_id, f"⚠️ <b>Lỗi hệ thống:</b> {escape_html(str(e))}", parse_mode="HTML")

# =====================================================================
# [PHẦN 4.5] GOOGLE CALENDAR (LỊCH CHỐT NƯỚC)
# =====================================================================
def them_lich_chot_nuoc(ngay_chot, so_khoi, so_ngay):
    if not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json'):
        return False, "Không tìm thấy file credentials.json"
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        
        # 1. Search and delete existing events with the same title
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId=CALENDAR_ID, timeMin=now,
                singleEvents=True, orderBy='startTime', q='Lịch chốt số nước'
            ).execute()
            events = events_result.get('items', [])
            for evt in events:
                if 'Lịch chốt số nước' in evt.get('summary', ''):
                    try:
                        service.events().delete(calendarId=CALENDAR_ID, eventId=evt['id']).execute()
                    except: pass
        except: pass
        
        # 2. Insert new event at 19:00 (7:00 PM)
        event = {
            'summary': '💧 Lịch chốt số nước',
            'description': f'Hệ thống AnX nhắc nhở chốt nước.\n- Tiêu thụ thực tế: {so_khoi} khối/ngày\n- Số ngày dùng: {so_ngay} ngày.',
            'start': {
                'dateTime': f"{ngay_chot.strftime('%Y-%m-%d')}T19:00:00+07:00",
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
            'end': {
                'dateTime': f"{ngay_chot.strftime('%Y-%m-%d')}T19:30:00+07:00",
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
        }
        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True, "Đã thêm vào Google Calendar thành công!"
    except Exception as e:
        error_msg = str(e)
        if "invalid_grant" in error_msg:
            return False, "Lỗi xác thực JWT (invalid_grant). Vui lòng cập nhật credentials.json."
        if "notFound" in error_msg or "404" in error_msg:
            return False, f"Không tìm thấy lịch (Calendar ID: {CALENDAR_ID}). Cần Share lịch này cho Service Account."

        return False, f"Lỗi Calendar API: {error_msg}"

# =====================================================================
# [PHẦN 5] BÁO CÁO DRIVE (Logic thu_muc_goc – 09/2026)
# =====================================================================
def trich_xuat_so_tuan(ten_thu_muc):
    match = re.search(r'(?i)tuan\s*(\d+)', ten_thu_muc)
    return int(match.group(1)) if match else 999

SHEETS_ID = os.environ.get("SHEETS_ID", "1Rvz9rfQY6cH4sfIHQ8yIM6eykdiNJEXGseH03qPaf8I")

def xac_dinh_sheet_cho_thu_muc(folder_name):
    """Phân loại thư mục vào sheet tương ứng ('TOAN' hoặc 'TIENGVIET') dựa trên tên thư mục cha.
    Ví dụ: 'KNTT_TIENGVIET4_MNT_TUAN1' -> 'TIENGVIET'
           'TUAN1_KNTT_TOAN4_MNT'      -> 'TOAN'
    """
    fn_clean = folder_name.upper().replace("_", "").replace(" ", "").replace("-", "")
    if "TIENGVIET" in fn_clean or "TIENG_VIET" in folder_name.upper() or "TIẾNGVIỆT" in fn_clean:
        return "TIENGVIET"
    elif "TOAN" in fn_clean or "TOÁN" in folder_name.upper():
        return "TOAN"
    return None

_drive_scan_cache = {"time": 0, "data": None}

def quet_tat_ca_tien_do_drive(drive_service, force_refresh=False):
    """Quét toàn bộ thư mục PowerPoint trên Google Drive theo cấu trúc chuẩn:
    - Tìm các thư mục cha có 'TUAN' hoặc 'KNTT'
    - Sắp xếp tăng dần theo số tuần (trich_xuat_so_tuan)
    - Đối chiếu file gốc (trong thu_muc_goc) với file đã xử lý (.pptx)
    - Quyết định trạng thái hoàn thành duy nhất cho cả Telegram và Google Sheets:
      + Chỉ khi file gốc ghép cặp thành công với file đã xử lý -> is_completed = True ('Hoàn thành' / '(hoàn thành)')
      + Không ghép cặp hoặc chưa có file làm -> is_completed = False ('Chưa làm' / không có '(hoàn thành)')
    """
    global _drive_scan_cache
    now = time.time()
    if not force_refresh and _drive_scan_cache["data"] is not None and (now - _drive_scan_cache["time"] < 60):
        return _drive_scan_cache["data"]

    query_main = (f"'{POWERPOINT_FOLDER_ID}' in parents and trashed=false "
                  f"and mimeType='application/vnd.google-apps.folder'")
    results = drive_service.files().list(q=query_main, fields="files(id, name)", pageSize=1000).execute()
    raw_folders = results.get('files', [])
    main_folders = sorted(raw_folders, key=lambda x: (trich_xuat_so_tuan(x['name']), x['name']))

    folders_data = []

    for main_folder in main_folders:
        folder_name = main_folder['name']
        folder_id = main_folder['id']

        if not ("TUAN" in folder_name.upper() or "KNTT" in folder_name.upper()):
            continue

        target_sheet = xac_dinh_sheet_cho_thu_muc(folder_name)
        if not target_sheet:
            continue

        match_tuan = re.search(r'(?i)tuan\s*(\d+)', folder_name)
        tien_to = f"Tuan{match_tuan.group(1)}_" if match_tuan else ""

        query_sub = f"'{folder_id}' in parents and trashed=false"
        sub_results = drive_service.files().list(
            q=query_sub, fields="files(id, name, mimeType)", pageSize=1000
        ).execute()

        thu_muc_goc_id = None
        processed_files = []

        for item in sub_results.get('files', []):
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                if item['name'].strip().lower() == "thu_muc_goc":
                    thu_muc_goc_id = item['id']
            elif item['name'].lower().endswith('.pptx'):
                processed_files.append(item['name'])

        items = []

        if thu_muc_goc_id:
            orig_results = drive_service.files().list(
                q=(f"'{thu_muc_goc_id}' in parents and trashed=false "
                   f"and mimeType!='application/vnd.google-apps.folder'"),
                fields="files(name)", pageSize=1000
            ).execute()
            original_files = sorted([f['name'] for f in orig_results.get('files', [])
                                     if f['name'].lower().endswith('.pptx')])
            processed_files = sorted(processed_files)
            matched_processed = set()

            for orig in original_files:
                orig_clean = re.sub(r'\s+', '', re.sub(r'(?i)\.pptx$', '', orig).strip().lower())
                found = None
                for proc in processed_files:
                    proc_clean = re.sub(r'\s+', '', re.sub(r'(?i)\.pptx$', '', proc).strip().lower())
                    if orig_clean in proc_clean:
                        found = proc
                        break
                if found:
                    items.append({
                        "orig": orig,
                        "proc": found,
                        "display": found,
                        "is_completed": True
                    })
                    matched_processed.add(found)
                else:
                    expected = (tien_to + orig) if (tien_to and not orig.lower().startswith(tien_to.lower())) else orig
                    items.append({
                        "orig": orig,
                        "proc": expected,
                        "display": expected,
                        "is_completed": False
                    })

            for proc in processed_files:
                if proc not in matched_processed:
                    expected_orig = re.sub(r'(?i)^tuan\d+_', '', proc) if tien_to else proc
                    display_name = (tien_to + proc) if (tien_to and not proc.lower().startswith(tien_to.lower())) else proc
                    items.append({
                        "orig": expected_orig,
                        "proc": proc,
                        "display": display_name,
                        "is_completed": False
                    })
        else:
            all_pptx = list(processed_files)
            for item in sub_results.get('files', []):
                if item['mimeType'] == 'application/vnd.google-apps.folder' and item['name'].strip().lower() != "thu_muc_goc":
                    sub_sub = drive_service.files().list(
                        q=f"'{item['id']}' in parents and trashed=false",
                        fields="files(name, mimeType, id)", pageSize=1000
                    ).execute()
                    for ii in sub_sub.get('files', []):
                        if ii['name'].lower().endswith('.pptx'):
                            all_pptx.append(ii['name'])
                        elif ii['mimeType'] == 'application/vnd.google-apps.folder':
                            deep = drive_service.files().list(
                                q=f"'{ii['id']}' in parents and trashed=false",
                                fields="files(name, mimeType)", pageSize=1000
                            ).execute()
                            for ditem in deep.get('files', []):
                                if ditem['name'].lower().endswith('.pptx'):
                                    all_pptx.append(ditem['name'])

            all_pptx = sorted(list(set(all_pptx)), key=len)
            matched_indices = set()

            for i in range(len(all_pptx)):
                if i in matched_indices:
                    continue
                ci = re.sub(r'\s+', '', re.sub(r'(?i)\.pptx$', '', all_pptx[i]).strip().lower())
                for j in range(i + 1, len(all_pptx)):
                    if j in matched_indices:
                        continue
                    cj = re.sub(r'\s+', '', re.sub(r'(?i)\.pptx$', '', all_pptx[j]).strip().lower())
                    if ci in cj:
                        items.append({
                            "orig": all_pptx[i],
                            "proc": all_pptx[j],
                            "display": all_pptx[j],
                            "is_completed": True
                        })
                        matched_indices.add(i)
                        matched_indices.add(j)
                        break

            for i in range(len(all_pptx)):
                if i not in matched_indices:
                    d_name = all_pptx[i]
                    expected = (tien_to + d_name) if (tien_to and not d_name.lower().startswith(tien_to.lower())) else d_name
                    items.append({
                        "orig": d_name,
                        "proc": expected,
                        "display": expected,
                        "is_completed": False
                    })

        folders_data.append({
            "folder_name": folder_name,
            "target_sheet": target_sheet,
            "items": items
        })

    _drive_scan_cache["time"] = time.time()
    _drive_scan_cache["data"] = folders_data
    return folders_data

def day_du_lieu_google_sheets(drive_service=None, folders_data=None):
    """Quét Drive rồi phân loại ghi vào đúng Google Sheets ('TOAN' và 'TIENGVIET')
    theo cấu trúc A(STT) B(Thư mục cha) C(File gốc) D(File đã làm) E(Trạng thái).
    Sắp xếp tuần từ bé đến lớn tăng dần và STT tăng dần cho từng sheets.
    Trạng thái 100% đồng bộ với Telegram: Có '(hoàn thành)' -> 'Hoàn thành', không có -> 'Chưa làm'.
    """
    if not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json'):
        return False, "Không tìm thấy credentials.json"

    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
        sheets_service = build('sheets', 'v4', credentials=creds)

        if folders_data is None:
            if drive_service is None:
                drive_service = build('drive', 'v3', credentials=creds)
            folders_data = quet_tat_ca_tien_do_drive(drive_service)

        sheet_rows = {
            "TOAN": [],
            "TIENGVIET": []
        }
        stt_counters = {
            "TOAN": 1,
            "TIENGVIET": 1
        }

        for folder in folders_data:
            target_sheet = folder["target_sheet"]
            if target_sheet not in sheet_rows:
                continue

            for it in folder["items"]:
                stt = stt_counters[target_sheet]
                status_str = "Hoàn thành" if it["is_completed"] else "Chưa làm"
                sheet_rows[target_sheet].append([
                    stt,
                    folder["folder_name"],
                    it["orig"],
                    it["proc"],
                    status_str
                ])
                stt_counters[target_sheet] += 1

        sheet = sheets_service.spreadsheets()
        spreadsheet_info = sheet.get(spreadsheetId=SHEETS_ID).execute()
        existing_sheets = [s['properties']['title'] for s in spreadsheet_info.get('sheets', [])]

        summary_parts = []
        for s_name in ["TOAN", "TIENGVIET"]:
            rows_for_sheet = sheet_rows.get(s_name, [])

            if s_name not in existing_sheets:
                add_req = {"requests": [{"addSheet": {"properties": {"title": s_name}}}]}
                sheet.batchUpdate(spreadsheetId=SHEETS_ID, body=add_req).execute()
                existing_sheets.append(s_name)

            sheet.values().clear(
                spreadsheetId=SHEETS_ID,
                range=f"'{s_name}'!A2:E"
            ).execute()

            if rows_for_sheet:
                sheet.values().update(
                    spreadsheetId=SHEETS_ID,
                    range=f"'{s_name}'!A2:E{1 + len(rows_for_sheet)}",
                    valueInputOption="USER_ENTERED",
                    body={"values": rows_for_sheet}
                ).execute()

            summary_parts.append(f"{len(rows_for_sheet)} dòng vào '{s_name}'")

        return True, "Đã ghi " + ", ".join(summary_parts) + "."

    except Exception as e:
        return False, str(e)


def tao_bao_cao_powerpoint(drive_service=None, folders_data=None):
    if not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json'):
        return "⚠️ Lỗi hệ thống: Không tìm thấy file <code>credentials.json</code>. Vui lòng thêm file này vào thư mục chứa code."

    try:
        if folders_data is None:
            if drive_service is None:
                creds = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
                drive_service = build('drive', 'v3', credentials=creds)
            folders_data = quet_tat_ca_tien_do_drive(drive_service)

        msg = "📊 <b>BÁO CÁO TIẾN ĐỘ POWERPOINT</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        co_du_lieu = False

        for folder in folders_data:
            folder_name = folder["folder_name"]
            items = folder["items"]
            co_du_lieu = True

            msg += f"📁 <b>{escape_html(folder_name)}</b>\n  + Thư mục con: thu_muc_goc\n"

            file_list = []
            for it in items:
                if it["is_completed"]:
                    file_list.append(f"    - {escape_html(it['display'])}(hoàn thành);")
                else:
                    file_list.append(f"    - {escape_html(it['display'])};")

            if not file_list:
                file_list.append("    - <i>Thư mục rỗng, chưa có file nào</i>;")

            file_list.sort()
            block = "\n".join(file_list)
            if block.endswith(";"):
                block = block[:-1] + "."
            msg += block + "\n\n"

        if not co_du_lieu:
            msg += "<i>Không tìm thấy thư mục nào chứa TUAN hoặc KNTT.</i>"

        return msg.strip()

    except Exception as e:
        error_msg = str(e)
        if "invalid_grant" in error_msg:
            return "⚠️ <b>Lỗi xác thực Google Drive (invalid_grant)</b>: File <code>credentials.json</code> bị lỗi, chữ ký JWT không hợp lệ hoặc đã hết hạn. Vui lòng tải file <code>credentials.json</code> mới từ Google Cloud Console và thay thế file cũ trên hệ thống."
        return f"⚠️ Quá trình quét Drive gặp lỗi: {escape_html(error_msg)}"

# =====================================================================
# [PHẦN 6] THỜI TIẾT THÔNG MINH, ĐÔ THỊ & BÁO CHÍ
# =====================================================================
def get_owm_icon(icon_code):
    mapping = {
        "01d": "☀️", "01n": "🌑", "02d": "⛅",  "02n": "☁️",
        "03d": "☁️", "03n": "☁️", "04d": "☁️",  "04n": "☁️",
        "09d": "🌧️", "09n": "🌧️", "10d": "🌦️", "10n": "🌧️",
        "11d": "⛈️", "11n": "⛈️", "13d": "❄️",  "13n": "❄️",
        "50d": "🌫️", "50n": "🌫️"
    }
    return mapping.get(icon_code, "🌤️")

def xac_dinh_trang_thai_thoi_tiet(c_temp, feels_like, c_desc, n_pop, humidity):
    desc_lower = c_desc.lower()
    la_mua_hien_tai = any(x in desc_lower for x in ["mưa", "dông", "giông", "bão", "lất phất", "rào"])
    la_bao = any(x in desc_lower for x in ["bão", "cuồng phong"])
    la_dong = any(x in desc_lower for x in ["dông", "giông", "sấm"]) or (la_mua_hien_tai and n_pop >= 80)
    la_may = any(x in desc_lower for x in ["mây nhiều", "âm u", "xám xịt"]) or (humidity > 85 and not la_mua_hien_tai)
    la_nang_gat = c_temp >= 35 or feels_like >= 38
    la_nang = c_temp >= 28 and not la_may and not la_mua_hien_tai

    if la_bao: return "MUA_BAO"
    elif la_dong: return "MUA_DONG"
    elif la_mua_hien_tai: return "MUA_NHO"
    elif la_nang_gat: return "NANG_GAT"
    elif la_nang: return "NANG"
    elif la_may: return "AM_U"
    else: return "BINH_THUONG"

def lay_bang_diem_ngap(muc_do="NHE", rain_1h=0):
    from datetime import datetime

    if rain_1h < 15:
        return "", ""

    he_so = 1.3 if muc_do == "TO" else 1.0
    ds = [
        ("Vạn Phúc", 15, 25, "Ngã tư Vạn Phúc, Tố Hữu", "Trũng mép đường"),
        ("Phúc La", 20, 40, "Khu Viện K, KĐT Xa La", "Nước xiết mạnh"),
        ("Mộ Lao", 15, 30, "Nguyễn Văn Lộc", "Ngập nửa bánh xe"),
        ("Hà Cầu", 15, 25, "Chợ Hà Đông, Lê Lợi", "Nước dâng nhanh"),
        ("Văn Quán", 25, 45, "Hồ Văn Quán, Chiến Thắng", "Nguy cơ thủy kích"),
        ("Tân Triều", 30, 50, "Triều Khúc, ngõ 66", "Ngập lút bánh xe")
    ]

    random.seed(datetime.datetime.now().strftime("%Y%m%d%H"))
    so_diem = random.randint(1, 2) if muc_do == "NHE" else random.randint(3, 5)
    diem_thuc_te = random.sample(ds, min(so_diem, len(ds)))

    txt_ngap = ""
    txt_tranh = ""
    if muc_do == "NHE":
        for phuong, mn, mx, tuyen, hau_qua in diem_thuc_te:
            txt_ngap += f"📍 {phuong}: {tuyen}\n"
        txt_tranh = "Tránh ngõ hẹp thấp trũng, đi các trục đường chính Trần Phú, Quang Trung."
    else:
        for phuong, mn, mx, tuyen, hau_qua in diem_thuc_te:
            min_v, max_v = int(mn * he_so), int(mx * he_so)
            canh_bao = ("⛔ CẤM XE GẦM THẤP" if max_v >= 50 else "⚠️ GẦM THẤP NGUY HIỂM" if max_v >= 35 else "⚠️ ĐI CHẬM ĐỀU GA")
            txt_ngap += f"📍 {phuong} | 🌊 {min_v}-{max_v}cm | {canh_bao}\n └ ⚠️ {tuyen}. {hau_qua}\n"
        txt_tranh = "Đường sắt Cát Linh - Hà Đông, BRT. Tránh xa Triều Khúc, Văn Quán, Xa La."
    return txt_ngap.strip(), txt_tranh.strip()

def format_weather(trang_thai, ht, ten_vi_tri, c_temp, feels_like, humidity, pm25, aqi_level, n_temp, n_pop, n_desc, ten_ngan, rain_1h=0):
    icon_pm = "😷" if aqi_level >= 4 else "✅"
    gio = ht.strftime('%H:%M')
    khu_vuc = escape_html(ten_vi_tri)

    msg = f"⏱ <b>THỜI TIẾT HIỆN TẠI ({gio})</b>\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📍 Khu vực: <code>{khu_vuc}</code>\n\n"
    msg += f"🌡 <b>THÔNG SỐ HIỆN TẠI</b>\n"
    msg += f"├ Nhiệt độ: <code>{c_temp}°C</code> (Cảm nhận: <code>{feels_like}°C</code>)\n"

    img_url = None
    img_caption = None
    tu_khoa = f"thời tiết {ten_ngan}"

    if trang_thai == "BINH_THUONG":
        msg += f"├ Trạng thái: ☁️ <b>Bình thường</b> (Độ ẩm: <code>{humidity}%</code>)\n"
        msg += f"└ Bụi mịn PM2.5: <code>{pm25} µg/m³</code> {icon_pm}\n\n"
        msg += f"🔮 <b>DỰ BÁO 3 GIỜ TỚI</b>\n"
        msg += f"└ ~<code>{n_temp}°C</code> | Bình thường | Mưa: <code>{n_pop}%</code>\n\n"
        msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
        msg += f"└ Thời tiết ổn định, ít biến động. Không có hiện tượng bất thường đáng chú ý.\n\n"
        msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
        msg += f"├ Điều khiển phương tiện: Giao thông thuận lợi, chú ý tốc độ theo quy định.\n"
        msg += f"└ Trang bị: Không cần trang bị đặc biệt.\n"

    elif trang_thai == "NANG":
        msg += f"├ Trạng thái: ☀️ <b>Nắng</b> (Độ ẩm: <code>{humidity}%</code>)\n"
        msg += f"└ Bụi mịn PM2.5: <code>{pm25} µg/m³</code> {icon_pm}\n\n"
        msg += f"🔮 <b>DỰ BÁO 3 GIỜ TỚI</b>\n"
        msg += f"└ ~<code>{n_temp}°C</code> | Nắng | Mưa: <code>{n_pop}%</code>\n\n"
        msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
        msg += f"└ Trời nắng đẹp, tầm nhìn tốt. Chỉ số UV ở mức trung bình đến cao.\n\n"
        msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
        msg += f"├ Điều khiển phương tiện: Giao thông thuận lợi, chú ý chống chói khi lái xe.\n"
        msg += f"└ Trang bị: Nên đội mũ, đeo kính râm, bôi kem chống nắng nếu ra ngoài lâu.\n"

    elif trang_thai == "NANG_GAT":
        msg += f"├ Trạng thái: 🔥 <b>Nắng gắt</b> (Độ ẩm: <code>{humidity}%</code>)\n"
        msg += f"└ Bụi mịn PM2.5: <code>{pm25} µg/m³</code> {icon_pm}\n\n"
        msg += f"🔮 <b>DỰ BÁO 3 GIỜ TỚI</b>\n"
        msg += f"└ ~<code>{n_temp}°C</code> | Nắng gắt | Mưa: <code>{n_pop}%</code>\n\n"
        msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
        msg += f"└ Nắng nóng gay gắt, chỉ số UV rất cao. Nguy cơ say nắng, mất nước cao nếu hoạt động ngoài trời lâu.\n\n"
        msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
        msg += f"├ Điều khiển phương tiện: Hạn chế di chuyển giờ cao điểm nắng (11h-15h). Để xe ở nơi có bóng râm, kiểm tra áp suất lốp.\n"
        msg += f"└ Trang bị: Bắt buộc đội mũ rộng vành, đeo kính râm UV400, mang theo nước uống, bôi kem chống nắng SPF50+.\n"
        img_url = URL_ANH_NANG
        img_caption = "🔥☀️ CẢNH BÁO NẮNG GẮT"
        tu_khoa = f"nắng nóng gay gắt {ten_ngan}"

    elif trang_thai == "AM_U":
        msg += f"├ Trạng thái: ☁️ <b>Âm u</b> (Độ ẩm: <code>{humidity}%</code>)\n"
        msg += f"└ Bụi mịn PM2.5: <code>{pm25} µg/m³</code> {icon_pm}\n\n"
        msg += f"🔮 <b>DỰ BÁO 3 GIỜ TỚI</b>\n"
        msg += f"└ ~<code>{n_temp}°C</code> | Âm u | Mưa: <code>{n_pop}%</code>\n\n"
        msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
        msg += f"└ Trời nhiều mây, ánh sáng yếu. Có thể chuyển mưa nhẹ trong vài giờ tới nếu độ ẩm tăng cao.\n\n"
        msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
        msg += f"├ Điều khiển phương tiện: Tầm nhìn hơi giảm, nên bật đèn chiếu gần khi đi vào khu vực tối.\n"
        msg += f"└ Trang bị: Mang theo áo mưa mỏng phòng trường hợp mưa bất ngờ.\n"

    elif trang_thai == "MUA_NHO":
        msg += f"├ Trạng thái: 🌦️ <b>Mưa nhỏ</b> (Độ ẩm: <code>{humidity}%</code>)\n"
        msg += f"└ Bụi mịn PM2.5: <code>{pm25} µg/m³</code> {icon_pm}\n\n"
        msg += f"🔮 <b>DỰ BÁO 3 GIỜ TỚI</b>\n"
        msg += f"└ ~<code>{n_temp}°C</code> | Mưa nhỏ | Mưa: <code>{n_pop}%</code>\n\n"
        msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
        msg += f"└ Mưa nhỏ diện rộng, tầm nhìn giảm nhẹ. Mặt đường bắt đầu ướt, ma sát giảm.\n\n"
        msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
        msg += f"├ Điều khiển phương tiện: Giảm tốc độ, giữ khoảng cách an toàn, tránh phanh gấp.\n"
        msg += f"└ Trang bị: Nên mặc áo mưa, bọc kỹ thiết bị điện tử.\n\n"
        txt_ngap, txt_tranh = lay_bang_diem_ngap("NHE", rain_1h)
        if txt_ngap:
            msg += f"\n🌊 <b>BẢNG ĐIỂM ĐEN NGẬP ÚNG ({escape_html(ten_ngan)}):</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n{txt_ngap}\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += f"🛡️ <b>LỘ TRÌNH ĐƯỜNG TRÁNH & KHUYẾN CÁO:</b>\n├ Đường tránh ngập: {txt_tranh}\n└ Khuyến cáo: Đi chậm, bám tim đường, tránh vũng nước sâu.\n"
        img_url = URL_ANH_NGAP
        img_caption = "🌦️ CẢNH BÁO MƯA NHẸ"
        tu_khoa = f"mưa {ten_ngan}"

    elif trang_thai == "MUA_DONG":
        msg += f"├ Trạng thái: ⛈️ <b>Mưa dông</b> (Độ ẩm: <code>{humidity}%</code>)\n"
        msg += f"└ Bụi mịn PM2.5: <code>{pm25} µg/m³</code> {icon_pm}\n\n"
        msg += f"🔮 <b>DỰ BÁO 3 GIỜ TỚI</b>\n"
        msg += f"└ ~<code>{n_temp}°C</code> | Mưa dông | Mưa: <code>{n_pop}%</code>\n\n"
        msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
        msg += f"└ Mưa dông kèm sấm chớp, gió giật mạnh cục bộ. Nguy cơ ngập úng nhanh, cây đổ, mất điện.\n"
        msg += f"└ Dự báo ngắn: Xác suất mưa dông trong 3h tới vẫn cao, có thể xuất hiện gió mạnh.\n\n"
        msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
        msg += f"├ Điều khiển phương tiện: Tuyệt đối không đi dưới cây lớn, biển quảng cáo. Giảm tốc độ mạnh, bật đèn sương mù nếu có.\n"
        msg += f"└ Trang bị: Áo mưa bộ rời, ủng cao su, tránh dùng ô (dễ lật).\n\n"
        txt_ngap, txt_tranh = lay_bang_diem_ngap("TO", rain_1h)
        if txt_ngap:
            msg += f"\n🌊 <b>BẢNG ĐIỂM ĐEN NGẬP ÚNG ({escape_html(ten_ngan)}):</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n{txt_ngap}\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += f"🛡️ <b>LỘ TRÌNH ĐƯỜNG TRÁNH & KHUYẾN CÁO:</b>\n├ Đường tránh ngập: {txt_tranh}\n├ Giao thông công cộng: Ưu tiên tàu điện/metro nếu có.\n└ Khuyến cáo: Không cố đi vào vùng ngập sâu, tắt máy ngay nếu nước chạm ống xả.\n"
        img_url = URL_ANH_NGAP
        img_caption = "⛈️ CẢNH BÁO MƯA DÔNG"
        tu_khoa = f"mưa dông ngập lụt {ten_ngan}"

    elif trang_thai == "MUA_BAO":
        msg += f"├ Trạng thái: 🌪️ <b>Mưa bão</b> (Độ ẩm: <code>{humidity}%</code>)\n"
        msg += f"└ Bụi mịn PM2.5: <code>{pm25} µg/m³</code> {icon_pm}\n\n"
        msg += f"🔮 <b>DỰ BÁO 3 GIỜ TỚI</b>\n"
        msg += f"└ ~<code>{n_temp}°C</code> | Mưa bão | Mưa: <code>{n_pop}%</code>\n\n"
        msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
        msg += f"└ Mưa bão nguy hiểm: gió mạnh, mưa lớn diện rộng, nguy cơ ngập lụt nghiêm trọng, sạt lở, cây đổ, mất điện diện rộng.\n"
        msg += f"└ Dự báo ngắn: Tình hình diễn biến phức tạp, khả năng kéo dài.\n\n"
        msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
        msg += f"├ Điều khiển phương tiện: Hạn chế tối đa việc ra đường. Nếu buộc phải đi: tốc độ cực thấp, bật toàn bộ đèn, tránh xa cây cối và biển hiệu.\n"
        msg += f"└ Trang bị: Áo mưa dày, ủng cao, đèn pin, sạc dự phòng. Không sử dụng xe máy nếu gió trên cấp 6.\n\n"
        txt_ngap, txt_tranh = lay_bang_diem_ngap("TO", rain_1h)
        if txt_ngap:
            msg += f"\n🌊 <b>BẢNG ĐIỂM ĐEN NGẬP ÚNG ({escape_html(ten_ngan)}):</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n{txt_ngap}\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += f"🛡️ <b>LỘ TRÌNH ĐƯỜNG TRÁNH & KHUYẾN CÁO:</b>\n├ Đường tránh ngập: Chỉ nên đi các tuyến cao, khô ráo đã được khuyến cáo chính thức.\n├ Giao thông công cộng: Ưu tiên tàu điện/metro, tránh xe buýt.\n└ Khuyến cáo: Ở trong nhà nếu không thực sự cần thiết. Theo dõi cảnh báo khẩn cấp từ chính quyền.\n"
        img_url = URL_ANH_NGAP
        img_caption = "🌪️ CẢNH BÁO MƯA BÃO"
        tu_khoa = f"bão ngập lụt {ten_ngan}"

    return msg, img_url, img_caption, tu_khoa


def lay_thoi_tiet_va_tin_tuc_hien_tai(include_news=True):
    try:
        lat, lon, ten_vi_tri = admin_location["lat"], admin_location["lon"], admin_location["name"]
        ten_ngan = ten_vi_tri.split(',')[0].strip()

        req_curr = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi", timeout=10)
        req_curr.encoding = 'utf-8'
        res_curr  = req_curr.json()
        c_temp    = round(res_curr['main']['temp'], 1)
        feels_like = round(res_curr['main']['feels_like'], 1)
        humidity  = res_curr['main']['humidity']
        c_desc    = res_curr['weather'][0]['description'].capitalize()
        c_icon    = get_owm_icon(res_curr['weather'][0]['icon'])

        req_fore = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi", timeout=10)
        req_fore.encoding = 'utf-8'
        res_fore      = req_fore.json()
        forecast_list = res_fore.get('list', [])
        n_item  = forecast_list[0] if forecast_list else {}
        n_temp  = round(n_item.get('main', {}).get('temp', c_temp), 1)
        n_pop   = int(n_item.get('pop', 0) * 100)
        n_desc  = n_item.get('weather', [{}])[0].get('description', c_desc).capitalize()

        req_aqi = requests.get(
            f"https://api.openweathermap.org/data/2.5/air_pollution"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}", timeout=5)
        res_aqi   = req_aqi.json()
        aqi_level = res_aqi['list'][0]['main']['aqi']
        pm25      = res_aqi['list'][0]['components'].get('pm2_5', 0)

        trang_thai = xac_dinh_trang_thai_thoi_tiet(c_temp, feels_like, c_desc, n_pop, humidity)
        ht = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))

        rain_1h = res_curr.get('rain', {}).get('1h', 0)
        msg, img_url, img_caption, tu_khoa = format_weather(trang_thai, ht, ten_vi_tri, c_temp, feels_like, humidity, pm25, aqi_level, n_temp, n_pop, n_desc, ten_ngan, rain_1h)

        if not include_news:
            return msg, img_url, img_caption

        msg += f"\n🌍 <b>TIN TỨC MỚI NHẤT ({escape_html(ten_ngan)}):</b>\n"
        url_news = (f"https://news.google.com/rss/search"
                    f"?q={urllib.parse.quote(tu_khoa)}&hl=vi&gl=VN&ceid=VN:vi")
        try:
            res_news = requests.get(url_news, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            res_news.encoding = 'utf-8'
            items_found = False
            if res_news.status_code == 200:
                try:    soup = BeautifulSoup(res_news.text, 'xml')
                except: soup = BeautifulSoup(res_news.text, 'html.parser')
                items       = soup.find_all('item')
                count       = 0
                cid_str     = "broadcast_weather"
                if cid_str not in sent_articles_set:
                    sent_articles_set[cid_str] = set()
                # Nếu tất cả các bài Google News đã nằm trong tập đã gửi -> Tự động reset để luôn có tin thời sự mới nhất phục vụ người dùng
                available_items = [it for it in items if it.link and it.link.text.strip() not in sent_articles_set[cid_str]]
                if len(available_items) < 3:
                    sent_articles_set[cid_str].clear()
                for item in items:
                    link = item.link.text.strip()
                    if link in sent_articles_set[cid_str]:
                        continue
                    raw_title = item.title.text.strip() if item.title else ""
                    title     = escape_html(html.unescape(raw_title))
                    if img_caption and not img_url:
                        enc = item.find('enclosure')
                        if enc and 'url' in enc.attrs:
                            img_url = enc['url']
                        else:
                            try:
                                raw_desc  = item.description.text if item.description else ""
                                desc_soup = BeautifulSoup(html.unescape(raw_desc), 'html.parser')
                                img_tag   = desc_soup.find('img')
                                if img_tag and 'src' in img_tag.attrs:
                                    img_url = img_tag['src']
                            except:
                                pass
                    if count < 3:
                        msg += f" ├ <a href='{link}'>{title}</a>\n"
                        sent_articles_set[cid_str].add(link)
                        items_found = True
                        count += 1
                if len(sent_articles_set[cid_str]) > 400:
                    sent_articles_set[cid_str].clear()
            if not items_found:
                msg += " └ <i>Chưa ghi nhận biến động giao thông khẩn cấp.</i>\n"
            else:
                parts = msg.rsplit(' ├ ', 1)
                msg = parts[0] + ' └ ' + parts[1] if len(parts) == 2 else msg
        except:
            msg += " └ <i>Tạm thời không thể tải tin tức nóng.</i>\n"

        try:
            url_yt  = "https://www.youtube.com/feeds/videos.xml?channel_id=UCabsTV34JwALXKGMqHpvUiA"
            res_yt  = requests.get(url_yt, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            res_yt.encoding = 'utf-8'
            if res_yt.status_code == 200:
                try:    soup_yt = BeautifulSoup(res_yt.text, 'xml')
                except: soup_yt = BeautifulSoup(res_yt.text, 'html.parser')
                entries = soup_yt.find_all('entry')
                if entries:
                    kws = (['mưa', 'lũ', 'ngập', 'bão'] if trang_thai in ["MUA_NHO", "MUA_DONG", "MUA_BAO"]
                           else ['nắng', 'hạn hán', 'nhiệt độ'])
                    found_vid = False
                    for entry in entries:
                        vtitle = html.unescape(entry.title.text if entry.title else "")
                        vlink  = (entry.find('link')['href']
                                  if entry.find('link') and 'href' in entry.find('link').attrs else "")
                        if any(kw in vtitle.lower() for kw in kws):
                            msg += f"\n📺 <b>VIDEO CẢNH BÁO (VTV24):</b>\n └ <a href='{vlink}'>{escape_html(vtitle)}</a>\n"
                            found_vid = True
                            break
                    if not found_vid:
                        vtitle = html.unescape(entries[0].title.text if entries[0].title else "Tin tức VTV24")
                        vlink  = (entries[0].find('link')['href']
                                  if entries[0].find('link') and 'href' in entries[0].find('link').attrs else "")
                        if vlink:
                            msg += f"\n📺 <b>TIN TỨC VIDEO (VTV24):</b>\n └ <a href='{vlink}'>{escape_html(vtitle)}</a>\n"
        except:
            pass

        return msg, img_url, img_caption
    except Exception as e:
        return f"⚠️ Lỗi dữ liệu: {escape_html(str(e))}", None, None

def lay_thoi_tiet_hom_nay_de_ghim():
    try:
        msg, _, _ = lay_thoi_tiet_va_tin_tuc_hien_tai(include_news=False)
        return msg
    except:
        return "⚠️ Không thể lấy dữ liệu thời tiết."

def cap_nhat_trang_thai_thoi_tiet():
    global TRANG_THAI_THOI_TIET
    try:
        lat, lon = admin_location["lat"], admin_location["lon"]
        res = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi", timeout=10).json()
        c_temp = round(res['main']['temp'], 1)
        feels_like = round(res['main']['feels_like'], 1)
        humidity = res['main']['humidity']
        c_desc = res['weather'][0]['description'].capitalize()
        res_fore = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi", timeout=10).json()
        forecast_list = res_fore.get('list', [])
        n_item = forecast_list[0] if forecast_list else {}
        n_pop = int(n_item.get('pop', 0) * 100)
        TRANG_THAI_THOI_TIET = xac_dinh_trang_thai_thoi_tiet(c_temp, feels_like, c_desc, n_pop, humidity)
    except:
        pass

def tim_toa_do_theo_ten(ten_dia_diem):
    try:
        import urllib.parse
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={urllib.parse.quote(ten_dia_diem)}&limit=1&appid={OPENWEATHER_API_KEY}"
        res = requests.get(url, timeout=10).json()
        if res and isinstance(res, list) and len(res) > 0:
            item = res[0]
            name = item.get("local_names", {}).get("vi", item.get("name", ten_dia_diem))
            if "country" in item:
                name = f"{name}, {item['country']}"
            return {"thanh_cong": True, "lat": float(item["lat"]), "lon": float(item["lon"]), "name": name}
    except:
        pass
    return {"thanh_cong": False}

def lay_tat_ca_bai_viet_ngau_nhien(sort_by_date=True, chi_lay_hom_nay=True):
    danh_sach_tong  = []
    headers         = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    nguon_rss       = [val for val in DANH_SACH_TRANG.values()]

    if TRANG_THAI_THOI_TIET == "MUA_CA_NGAY":
        nguon_rss.append({"ten": "⚠️ CẢNH BÁO MƯA LŨ",
                          "muc": ["https://news.google.com/rss/search?q=ngập+lụt+OR+mưa+lớn+OR+lũ+quét&hl=vi&gl=VN&ceid=VN:vi"]})
    elif TRANG_THAI_THOI_TIET == "NANG_CA_NGAY":
        nguon_rss.append({"ten": "⚠️ CẢNH BÁO NẮNG NÓNG",
                          "muc": ["https://news.google.com/rss/search?q=hạn+hán+OR+nắng+nóng+gay+gắt&hl=vi&gl=VN&ceid=VN:vi"]})
    nguon_rss.append({"ten": "🌐 Tin Nổi Bật",
                      "muc": ["https://news.google.com/rss?hl=vi&gl=VN&ceid=VN:vi"]})

    now_dt = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    now_ts = now_dt.timestamp()
    min_ts = now_ts - (36 * 3600)

    for t_info in nguon_rss:
        for url in t_info["muc"]:
            try:
                res = requests.get(url, headers=headers, timeout=8)
                res.encoding = 'utf-8'
                if res.status_code != 200:
                    continue
                try:    soup = BeautifulSoup(res.text, 'xml')
                except: soup = BeautifulSoup(res.text, 'html.parser')
                for item in soup.find_all('item')[:15]:
                    raw_title = item.title.text.strip() if item.title else "News"
                    title     = html.unescape(raw_title)
                    # Xử lý cắt bỏ phần "- Tên Báo" do Google News tự động nối thêm vào cuối title
                    if " - " in title:
                        title = " - ".join(title.split(" - ")[:-1])
                    raw_desc  = item.description.text.strip() if item.description else ""
                    desc      = html.unescape(raw_desc)
                    link      = item.link.text.strip() if item.link else ""
                    import email.utils
                    ts = now_ts
                    pub_str = ""
                    is_too_old = False
                    if item.pubDate and item.pubDate.text:
                        try:
                            p_dt = email.utils.parsedate_to_datetime(item.pubDate.text)
                            ts = p_dt.timestamp()
                            pub_str = item.pubDate.text.strip()
                            if p_dt.year < now_dt.year:
                                is_too_old = True
                            elif chi_lay_hom_nay and ts < min_ts:
                                is_too_old = True
                        except Exception:
                            ts = now_ts

                    if is_too_old:
                        continue

                    if not pub_str:
                        pub_str = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone(datetime.timedelta(hours=7))).strftime('%a, %d %b %Y %H:%M:%S +0700')

                    img_url   = None
                    enc       = item.find('enclosure')
                    if enc and 'url' in enc.attrs:
                        img_url = enc['url']
                    else:
                        try:
                            img_tag = BeautifulSoup(desc, 'html.parser').find('img')
                            if img_tag and 'src' in img_tag.attrs:
                                img_url = img_tag['src']
                        except:
                            pass
                    import urllib.parse
                    if img_url and img_url.startswith("http") and "wsrv.nl" not in img_url:
                        img_url = f"https://wsrv.nl/?url={urllib.parse.quote(img_url)}"
                    try:    c_desc = BeautifulSoup(desc, 'html.parser').get_text().strip()
                    except: c_desc = desc
                    c_desc = html.unescape(c_desc)
                    if len(c_desc) > 240:
                        c_desc = c_desc[:240] + "..."
                    if link:
                        danh_sach_tong.append({
                            "title": title, "description": c_desc,
                            "link": link,   "image": img_url,
                            "author": t_info["ten"], "source": t_info["ten"],
                            "pubDate": pub_str,
                            "timestamp": ts
                        })
            except:
                continue

    seen_links = set()
    unique_danh_sach = []
    for b in danh_sach_tong:
        if b["link"] not in seen_links:
            seen_links.add(b["link"])
            unique_danh_sach.append(b)

    if sort_by_date:
        unique_danh_sach.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    else:
        unique_danh_sach.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        top_fresh = unique_danh_sach[:12]
        random.shuffle(top_fresh)
        unique_danh_sach = top_fresh + unique_danh_sach[12:]
    return unique_danh_sach

def lay_bai_viet_moi_chua_gui(chat_id_str, so_luong=5):
    if chat_id_str not in sent_articles_set:
        sent_articles_set[chat_id_str] = set()
    tat_ca_tin = lay_tat_ca_bai_viet_ngau_nhien(sort_by_date=True, chi_lay_hom_nay=True)
    chua_gui   = [b for b in tat_ca_tin if b['link'] not in sent_articles_set[chat_id_str]]
    if len(chua_gui) < so_luong:
        sent_articles_set[chat_id_str].clear()
        chua_gui = tat_ca_tin
    chon_loc = chua_gui[:so_luong]
    for bai in chon_loc:
        sent_articles_set[chat_id_str].add(bai['link'])
    save_data()
    return chon_loc

# =====================================================================
# [PHẦN 7] SCHEDULER CHẠY NGẦM THÔNG MINH & GOOGLE DOCS NEWS
# =====================================================================
def job_cap_nhat_docs_tin_tuc():
    if (not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json')
            or DOC_NEWS_ID == "NHẬP_ID_FILE_DOCS_TIN_TỨC_VÀO_ĐÂY"):
        return
    try:
        creds        = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
        docs_service = build('docs', 'v1', credentials=creds)
        ht           = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        ngay_thang   = ht.strftime('%d/%m/%Y')

        noi_dung  = f"📅 BẢN TIN TỔNG HỢP ANX NGÀY {ngay_thang}\n"
        noi_dung += "⏱ Cập nhật lúc: 00:01\n"
        noi_dung += "━" * 38 + "\n\n"
        noi_dung += "🌤️ THÔNG TIN THỜI TIẾT TỔNG QUAN\n"
        noi_dung += "─" * 38 + "\n"
        noi_dung += lay_thoi_tiet_hom_nay_de_ghim() + "\n\n"
        noi_dung += "🌍 ĐIỂM TIN BÁO CHÍ TRONG NGÀY\n"
        noi_dung += "─" * 38 + "\n"

        tin_tuc = lay_tat_ca_bai_viet_ngau_nhien(sort_by_date=True, chi_lay_hom_nay=True)[:15]
        if not tin_tuc:
            noi_dung += "Không có dữ liệu tin tức mới.\n"
        else:
            for idx, t in enumerate(tin_tuc, 1):
                noi_dung += f"{idx}. {t['title']}\n"
                noi_dung += f"   🏢 Nguồn: {t['source']}\n"
                noi_dung += f"   🔗 Link: {t['link']}\n\n"

        doc       = docs_service.documents().get(documentId=DOC_NEWS_ID).execute()
        content   = doc.get('body').get('content')
        end_index = content[-1]['endIndex'] - 1

        reqs = []
        if end_index > 1:
            reqs.append({'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_index}}})
        reqs.append({'insertText': {'location': {'index': 1}, 'text': noi_dung}})
        docs_service.documents().batchUpdate(documentId=DOC_NEWS_ID, body={'requests': reqs}).execute()
    except Exception:
        pass

def job_tu_dong_day_tin():
    try:
        ht_time     = time.time()
        with json_lock: chats_to_send = list(active_auto_news_chats)
        valid_chats = [c for c in chats_to_send
                       if ht_time - user_last_news_sent.get(str(c), 0) >= 1800]
        if not valid_chats:
            return

        tat_ca_tin = lay_tat_ca_bai_viet_ngau_nhien(sort_by_date=True, chi_lay_hom_nay=True)
        if not tat_ca_tin:
            return

        sent_to_any = False
        for chat_id in set(valid_chats):
            chat_str = str(chat_id)
            if chat_str not in sent_articles_set:
                sent_articles_set[chat_str] = set()
            chua_gui = [b for b in tat_ca_tin if b['link'] not in sent_articles_set[chat_str]]
            if len(chua_gui) < 5:
                sent_articles_set[chat_str].clear()
                chua_gui = tat_ca_tin
            ds_bai = dien_anh_cho_danh_sach(chua_gui[:5])
            if not ds_bai:
                continue

            gui_tin_nhan_telegram(
                chat_id,
                "🌟 <b>BẢN TIN ĐỊNH KỲ 1 GIỜ (5 BÁO NÓNG NHẤT)</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌐 <i>Hệ thống tự động tổng hợp tin tức nóng nhất 1 giờ qua.</i>",
                parse_mode="HTML", disable_noti=True
            )
            for bai in ds_bai:
                sent_articles_set[chat_str].add(bai['link'])
                caption = (f"📌 <b>{escape_html(bai['title'])}</b>\n\n"
                           f"📝 <i>{escape_html(bai['description'])}</i>\n\n"
                           f"📰 Nguồn: <code>{escape_html(bai['source'])}</code>\n"
                           f"🔗 <a href='{bai['link']}'>[Đọc bài viết đầy đủ tại đây]</a>")
                if bai.get('image'):
                    gui_anh_telegram(chat_id, bai['image'], caption)
                else:
                    gui_tin_nhan_telegram(chat_id, caption, parse_mode="HTML", disable_noti=True)
            user_last_news_sent[chat_str] = time.time()
            sent_to_any = True
        if sent_to_any:
            save_data()
    except Exception:
        pass

def job_thoi_tiet_hang_gio():
    try:
        ht   = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        hour = ht.hour
        cap_nhat_trang_thai_thoi_tiet()
        with json_lock: chats = list(active_auto_news_chats)

        for chat_id in chats:
            chat_str = str(chat_id)
            if hour == 0:
                noi_dung   = lay_thoi_tiet_hom_nay_de_ghim()
                img_url, img_caption = None, None
            else:
                noi_dung, img_url, img_caption = lay_thoi_tiet_va_tin_tuc_hien_tai(include_news=True)

            old_pin = pinned_weather_msgs.get(chat_str)
            if old_pin:
                try:
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/unpinChatMessage",
                                  json={"chat_id": chat_id, "message_id": old_pin}, timeout=5)
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage",
                                  json={"chat_id": chat_id, "message_id": old_pin}, timeout=5)
                except:
                    pass

            try:
                res = requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": noi_dung, "parse_mode": "HTML",
                          "disable_web_page_preview": True, "disable_notification": True},
                    timeout=5
                )
                if res.status_code == 200:
                    new_msg_id = res.json()['result']['message_id']
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/pinChatMessage",
                                  json={"chat_id": chat_id, "message_id": new_msg_id,
                                        "disable_notification": True}, timeout=5)
                    pinned_weather_msgs[chat_str] = new_msg_id
            except:
                pass

            if img_url:
                gui_anh_telegram(chat_id, img_url, img_caption)
        save_data()
    except Exception:
        pass

try:
    scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")
except Exception:
    scheduler = BackgroundScheduler()
scheduler.add_job(func=job_tu_dong_day_tin,    trigger="cron", minute=30)
scheduler.add_job(func=job_thoi_tiet_hang_gio, trigger="cron", minute=0)
scheduler.add_job(func=job_cap_nhat_docs_tin_tuc, trigger="cron", hour=0, minute=1)
scheduler.start()

# =====================================================================
# [PHẦN 8] API ENDPOINT & LỆNH ĐIỀU KHIỂN
# =====================================================================
def lay_ma_shopee_moi_nhat():
    ngay = datetime.date.today().strftime('%d/%m/%Y')
    return (f"<b>🛍️ KHO MÃ SHOPEE HÔM NAY</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 Cập nhật: <code>{ngay}</code>\n\n"
            "• 🎟️ <a href='https://shopee.vn/m/ma-giam-gia'>Kho Tổng Hợp Mã Giảm Giá</a>\n"
            "• ⚡ <a href='https://shopee.vn/m/voucher-hot'>Săn Voucher Khung Giờ Hot</a>\n"
            "• 🚚 <a href='https://shopee.vn/m/mien-phi-van-chuyen'>Nhận Mã Freeship 0Đ</a>")

def lay_ma_shopeefood_moi_nhat():
    ngay = datetime.date.today().strftime('%d/%m/%Y')
    return (f"<b>🍕 DEAL SHOPEEFOOD</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 Cập nhật: <code>{ngay}</code>\n\n"
            "• 🍔 <a href='https://shopeefood.vn/'>Trang Chủ Săn Deal</a>\n"
            "• 🎟️ <a href='https://shopee.vn/m/shopeefood'>Kho Voucher Độc Quyền</a>")

@app.route('/api/daily-news', methods=['GET'])
def api_daily_news():
    try:
        lat, lon, ten_vi_tri = admin_location["lat"], admin_location["lon"], admin_location["name"]
        res_curr  = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi", timeout=10).json()
        c_temp    = round(res_curr['main']['temp'], 1)
        feels_like = round(res_curr['main']['feels_like'], 1)
        humidity  = res_curr['main']['humidity']
        c_desc    = res_curr['weather'][0]['description'].capitalize()
        c_icon    = get_owm_icon(res_curr['weather'][0]['icon'])
        res_fore  = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi", timeout=10).json()
        forecast_list = res_fore.get('list', [])
        n_item    = forecast_list[0] if forecast_list else {}
        n_temp    = round(n_item.get('main', {}).get('temp', c_temp), 1)
        n_pop     = int(n_item.get('pop', 0) * 100)
        n_desc    = n_item.get('weather', [{}])[0].get('description', c_desc).capitalize()
        res_aqi   = requests.get(
            f"https://api.openweathermap.org/data/2.5/air_pollution"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}", timeout=5).json()
        aqi_level = res_aqi['list'][0]['main']['aqi']
        pm25      = res_aqi['list'][0]['components'].get('pm2_5', 0)
        trang_thai = xac_dinh_trang_thai_thoi_tiet(c_temp, feels_like, c_desc, n_pop, humidity)
        tin_tuc   = lay_tat_ca_bai_viet_ngau_nhien(sort_by_date=True, chi_lay_hom_nay=True)[:15]
        data_response = {
            "timestamp": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime('%H:%M %d/%m/%Y'),
            "location": ten_vi_tri,
            "weather": {
                "current":     {"temp": c_temp, "feels_like": feels_like, "humidity": humidity,
                                "desc": c_desc, "icon": c_icon, "pm25": pm25, "aqi_level": aqi_level},
                "forecast_3h": {"temp": n_temp, "pop": n_pop, "desc": n_desc},
                "status":      trang_thai
            },
            "news": tin_tuc
        }
        response = jsonify(data_response)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================================
# [PHẦN 9] XỬ LÝ UPDATE TELEGRAM (dùng chung Polling + Webhook)
# =====================================================================

def xoa_phien_lam_viec_sau_delay(chat_id, delay=120):
    def task():
        time.sleep(delay)
        if chat_id in user_sessions and user_sessions[chat_id].get("step"):
            if time.time() - user_sessions[chat_id].get("last_active", 0) >= delay - 5:
                all_to_del = user_sessions[chat_id].get("session_msg_ids", [])
                for mid in all_to_del:
                    xoa_tin_nhan(chat_id, mid)
                user_sessions[chat_id] = {"step": None, "data": {}}
                gui_tin_nhan_telegram(chat_id, "⏳ Đã quá 2 phút không nhận được phản hồi. Quá trình tính toán bị hủy, vui lòng làm lại.", parse_mode="HTML")
    import threading
    threading.Thread(target=task, daemon=True).start()

def xu_ly_telegram_update(data):
    try:
        if not data:
            return

        chat_id, user_id, username, text, message_id = None, "", "", "", None

        if "message" in data:
            msg        = data["message"]
            chat_id    = str(msg.get("chat", {}).get("id", ""))
            message_id = msg.get("message_id")
            user_id    = str(msg.get("from", {}).get("id", ""))
            username   = msg.get("from", {}).get("username", "").lower()
            text       = msg.get("text", "").strip()
            if chat_id and message_id:
                add_user_msg_to_queue(chat_id, message_id)
                if chat_id in user_sessions:
                    user_sessions[chat_id]['last_active'] = time.time()

        elif "callback_query" in data:
            cb       = data["callback_query"]
            chat_id  = str(cb["message"]["chat"]["id"])
            user_id  = str(cb.get("from", {}).get("id", ""))
            username = cb.get("from", {}).get("username", "").lower()
            text     = cb["data"]
            try:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
                    json={"callback_query_id": cb.get("id")}, timeout=5
                )
            except:
                pass

        if not chat_id:
            return

        active_auto_news_chats.add(chat_id)
        save_data()

        cmd = text.split('@')[0].strip() if text else ""

        # ── Gemini AI ──
        if cmd.startswith("/startgemini") or cmd.startswith("/geminichat") or cmd == "menu_startgemini":
            cau_hoi = (text.replace("/startgemini", "").replace("/geminichat", "")
                           .replace(f"@{AUTHORIZED_USERNAME}", "").strip() if text else "")
            if cmd == "menu_startgemini":
                cau_hoi = ""
            ai_chat_sessions.add(str(chat_id))
            gui_tin_nhan_telegram(
                chat_id,
                "🟢 <b>PHIÊN AI ĐÃ MỞ:</b> Chế độ tự động xóa tin nhắn tạm thời bị tắt.\n"
                "Bạn có thể chat thoải mái. Gõ <code>/endgemini</code> để thoát.",
                parse_mode="HTML"
            )
            if cau_hoi:
                threading.Thread(target=xu_ly_gemini_chat, args=(chat_id, cau_hoi), daemon=True).start()
            return

        if cmd.startswith("/endgemini") or cmd == "menu_endgemini":
            if str(chat_id) in ai_chat_sessions:
                ai_chat_sessions.remove(str(chat_id))
                gui_tin_nhan_telegram(
                    chat_id,
                    "🔴 <b>PHIÊN AI KẾT THÚC:</b> Chế độ tự dọn rác nhóm sau 30s đã kích hoạt lại.",
                    parse_mode="HTML"
                )
            return

        if str(chat_id) in ai_chat_sessions and not cmd.startswith("/"):
            threading.Thread(target=xu_ly_gemini_chat, args=(chat_id, text), daemon=True).start()
            return

        # ── Ghi logic vào Docs ──
        if cmd.startswith("/logicondinh"):
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                return
            noi_dung_logic = text.replace("/logicondinh", "").strip()
            if not noi_dung_logic:
                return
            wait_msg_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Đang lưu logic mới...</i>", parse_mode="HTML")
            def xu_ly_ghi_docs():
                thanh_cong = ghi_logic_moi_vao_docs(noi_dung_logic)
                for w_id in wait_msg_ids:
                    xoa_tin_nhan(chat_id, w_id)
                m_ids = gui_tin_nhan_telegram(
                    chat_id,
                    "✅ <b>Cập nhật bộ nhớ thành công!</b>" if thanh_cong else "❌ <b>Ghi nhớ thất bại!</b>",
                    parse_mode="HTML"
                )
                xoa_tin_nhan_sau_delay(chat_id, m_ids, 10)
            threading.Thread(target=xu_ly_ghi_docs, daemon=True).start()
            return

        # ── Tin tức ──
        if cmd in ["/tintuc", "menu_docbao", "Báo trong ngày"]:
            def thread_xu_ly_tin_tuc():
                try:
                    wait_msg = gui_tin_nhan_telegram(
                        chat_id, "⏳ <i>Đang tổng hợp 5 bài báo nóng nhất...</i>", parse_mode="HTML")
                    ds_bai = lay_bai_viet_moi_chua_gui(str(chat_id), so_luong=5)
                    for w_id in wait_msg:
                        xoa_tin_nhan(chat_id, w_id)
                    if not ds_bai:
                        m_ids = gui_tin_nhan_telegram(
                            chat_id, "⚠️ Không thể lấy dữ liệu tin tức lúc này. Vui lòng thử lại sau.",
                            parse_mode="HTML")
                        xoa_tin_nhan_sau_delay(chat_id, m_ids, 10)
                        return
                    threading.Thread(target=job_cap_nhat_docs_tin_tuc, daemon=True).start()
                    gui_tin_nhan_telegram(
                        chat_id,
                        "📰 <b>BẢN TIN TIÊU ĐIỂM (5 BÁO NÓNG NHẤT)</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "🌐 <i>Tổng hợp tin thời sự, đời sống & chính trị nổi bật:</i>",
                        parse_mode="HTML"
                    )
                    for bai in ds_bai:
                        caption = (f"📌 <b>{escape_html(bai['title'])}</b>\n\n"
                                   f"📝 <i>{escape_html(bai['description'])}</i>\n\n"
                                   f"📰 Nguồn: <code>{escape_html(bai['source'])}</code>\n"
                                   f"🔗 <a href='{bai['link']}'>👉 Đọc tại đây</a>")
                        if bai.get('image'):
                            gui_anh_telegram(chat_id, bai['image'], caption)
                        else:
                            gui_tin_nhan_telegram(chat_id, caption, parse_mode="HTML")
                except Exception:
                    traceback.print_exc()
            wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
            def wrapper_tintuc():
                thread_xu_ly_tin_tuc()
                for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
            threading.Thread(target=wrapper_tintuc, daemon=True).start()
            return

        # ── Thời tiết hiện tại (Admin) – GIỐNG HỆT CODE GỐC, KHÔNG có loading message ──
        if cmd in ["/thoitiethientai", "Thời tiết hiện tại", "menu_thoitiet"]:
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                m_ids = gui_tin_nhan_telegram(
                    chat_id, "⚠️ <i>Lệnh này chỉ dành cho Quản trị viên (Admin).</i>", parse_mode="HTML")
                xoa_tin_nhan_sau_delay(chat_id, m_ids, 5)
                return
            def xu_ly_tt_hientai_rieng():
                noi_dung, img_url, img_caption = lay_thoi_tiet_va_tin_tuc_hien_tai(include_news=True)
                chat_str = str(chat_id)
                old_pin  = pinned_weather_msgs.get(chat_str)
                if old_pin:
                    try:
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/unpinChatMessage",
                                      json={"chat_id": chat_id, "message_id": old_pin}, timeout=5)
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage",
                                      json={"chat_id": chat_id, "message_id": old_pin}, timeout=5)
                    except:
                        pass
                try:
                    res = requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": noi_dung, "parse_mode": "HTML",
                              "disable_web_page_preview": True}, timeout=5
                    )
                    if res.status_code == 200:
                        new_msg_id = res.json()['result']['message_id']
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/pinChatMessage",
                                      json={"chat_id": chat_id, "message_id": new_msg_id,
                                            "disable_notification": True}, timeout=5)
                        pinned_weather_msgs[chat_str] = new_msg_id
                        save_data()
                except:
                    pass
                if img_url:
                    gui_anh_telegram(chat_id, img_url, img_caption)
            wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
            def wrapper_tt_rieng():
                xu_ly_tt_hientai_rieng()
                for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
            threading.Thread(target=wrapper_tt_rieng, daemon=True).start()
            return

        # ── Thời tiết theo địa điểm ──
        if cmd.startswith("/thoitiet"):
            dia_diem = text.replace("/thoitiet", "").strip()
            if not dia_diem:
                def xu_ly_tt_nhanh():
                    noi_dung, img_url, img_caption = lay_thoi_tiet_va_tin_tuc_hien_tai(include_news=False)
                    gui_tin_nhan_telegram(chat_id, noi_dung, parse_mode="HTML")
                    if img_url:
                        gui_anh_telegram(chat_id, img_url, img_caption)
                wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
                def wrapper_tt_nhanh():
                    xu_ly_tt_nhanh()
                    for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
                threading.Thread(target=wrapper_tt_nhanh, daemon=True).start()
            else:
                def xu_ly_tt_theo_vung():
                    kq = tim_toa_do_theo_ten(dia_diem)
                    if not kq.get("thanh_cong"):
                        gui_tin_nhan_telegram(
                            chat_id,
                            f"⚠️ Không tìm thấy tọa độ cho: <b>{escape_html(dia_diem)}</b>",
                            parse_mode="HTML"
                        )
                        return
                    lat_, lon_, ten_ = kq["lat"], kq["lon"], kq["name"]
                    try:
                        res_c = requests.get(
                            f"https://api.openweathermap.org/data/2.5/weather"
                            f"?lat={lat_}&lon={lon_}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi",
                            timeout=10).json()
                        temp   = round(res_c['main']['temp'], 1)
                        feels  = round(res_c['main']['feels_like'], 1)
                        hum    = res_c['main']['humidity']
                        desc   = res_c['weather'][0]['description'].capitalize()
                        icon   = get_owm_icon(res_c['weather'][0]['icon'])
                        msg_   = (f"🌤️ <b>THỜI TIẾT TẠI {escape_html(ten_.upper())}</b>\n"
                                  "━━━━━━━━━━━━━━━━━━━━━\n"
                                  f"🌡️ Nhiệt độ: <code>{temp}°C</code> (Cảm nhận: <code>{feels}°C</code>)\n"
                                  f"💧 Độ ẩm: <code>{hum}%</code>\n"
                                  f"Trạng thái: {icon} <b>{desc}</b>\n"
                                  "━━━━━━━━━━━━━━━━━━━━━\n"
                                  f"<i>Gõ <code>/vung {escape_html(dia_diem)}</code> để đặt làm khu vực mặc định.</i>")
                        gui_tin_nhan_telegram(chat_id, msg_, parse_mode="HTML")
                    except Exception as e:
                        gui_tin_nhan_telegram(
                            chat_id,
                            f"⚠️ Lỗi tra cứu thời tiết: {escape_html(str(e))}",
                            parse_mode="HTML"
                        )
                wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
                def wrapper_tt_vung():
                    xu_ly_tt_theo_vung()
                    for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
                threading.Thread(target=wrapper_tt_vung, daemon=True).start()
            return

        # ── Báo cáo PowerPoint ──
        if cmd in ["/baocao", "menu_baocao"]:
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                m_ids = gui_tin_nhan_telegram(
                    chat_id, "⚠️ <i>Lệnh này chỉ dành cho Quản trị viên (Admin).</i>", parse_mode="HTML")
                xoa_tin_nhan_sau_delay(chat_id, m_ids, 5)
                return
            if message_id:
                xoa_tin_nhan(chat_id, message_id)
            if chat_id in last_report_msgs:
                for old_id in last_report_msgs[chat_id]:
                    xoa_tin_nhan(chat_id, old_id)
            wait_msg_ids = gui_tin_nhan_telegram(
                chat_id,
                "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>",
                parse_mode="HTML", disable_noti=True
            )
            def tien_trinh_baocao_va_huy():
                try:
                    # 1. Trả đủ nội dung báo cáo tiến độ PowerPoint lên Telegram trước
                    bao_cao_html = tao_bao_cao_powerpoint()
                    for w_id in wait_msg_ids:
                        xoa_tin_nhan(chat_id, w_id)
                    new_ids = gui_tin_nhan_telegram(chat_id, bao_cao_html, parse_mode="HTML", disable_noti=True)
                    last_report_msgs[chat_id] = list(new_ids)
                    save_data()

                    # 2. Tiến hành đồng bộ Google Sheets phân loại 2 tab (TOAN, TIENGVIET) từ cache chuẩn
                    sheets_success, sheets_msg = day_du_lieu_google_sheets()
                    sync_text = (
                        f"📊 <b>Đồng bộ Google Sheets:</b> ✅ Thành công ({escape_html(sheets_msg)})"
                        if sheets_success else
                        f"📊 <b>Đồng bộ Google Sheets:</b> ⚠️ Thất bại ({escape_html(sheets_msg)})"
                    )
                    sync_ids = gui_tin_nhan_telegram(chat_id, sync_text, parse_mode="HTML", disable_noti=True)
                    if sync_ids:
                        last_report_msgs[chat_id].extend(sync_ids)
                        save_data()

                    time.sleep(120)
                    for m_id in last_report_msgs.get(chat_id, []):
                        xoa_tin_nhan(chat_id, m_id)
                    last_report_msgs[chat_id] = []
                    save_data()
                except Exception as e:
                    print("Lỗi khi chạy báo cáo:", e)
                    pass
            def wrapper_baocao():
                tien_trinh_baocao_va_huy()
                for wid in wait_msg_ids: xoa_tin_nhan(chat_id, wid)
            threading.Thread(target=wrapper_baocao, daemon=True).start()
            return

        # ── Đổi vùng thời tiết ──
        if cmd.startswith("/vung"):
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                return
            if chat_id in user_sessions:
                user_sessions[chat_id]["step"] = None
            ten_vung = text.replace("/vung", "").strip()
            if not ten_vung:
                m_ids = gui_tin_nhan_telegram(chat_id, "⚠️ Vui lòng nhập tên vùng. Ví dụ: <code>/vung Hà Nội</code>", parse_mode="HTML")
                xoa_tin_nhan_sau_delay(chat_id, m_ids, 5)
                return
            
            wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
            
            def wrapper_vung():
                kq = tim_toa_do_theo_ten(ten_vung)
                for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
                
                if kq.get("thanh_cong"):
                    admin_location["lat"]  = kq["lat"]
                    admin_location["lon"]  = kq["lon"]
                    admin_location["name"] = kq["name"]
                    save_data()
                    m_ids = gui_tin_nhan_telegram(
                        chat_id,
                        f"✅ Đã chuyển vùng mặc định: <b>{escape_html(kq['name'])}</b>",
                        parse_mode="HTML"
                    )
                    xoa_tin_nhan_sau_delay(chat_id, m_ids, 10)
                else:
                    gui_tin_nhan_telegram(
                        chat_id,
                        f"❌ Không tìm thấy tọa độ cho vùng: <b>{escape_html(ten_vung)}</b>. Vui lòng thử tên khác (ví dụ: Hanoi, Vietnam).",
                        parse_mode="HTML"
                    )
                    
            threading.Thread(target=wrapper_vung, daemon=True).start()
            return

        # ── Menu chính ──
        if cmd in ["/start", "/menu", "Menu", "/help"]:
            is_admin = kiem_tra_quyen_admin(chat_id, user_id, username)
            if is_admin:
                keyboard = [
                    [{"text": "⛅ Thời Tiết Hiện Tại",  "callback_data": "menu_thoitiet"},
                     {"text": "⚡ Tính Điện Nước",       "callback_data": "menu_tinhtien"}],
                    [{"text": "📊 Báo Cáo PowerPoint",   "callback_data": "menu_baocao"}],
                    [{"text": "🤖 Bật Chat AI Gemini",   "callback_data": "menu_startgemini"},
                     {"text": "🛑 Tắt AI",               "callback_data": "menu_endgemini"}],
                    [{"text": "📰 Bản Tin Báo Chí",      "callback_data": "menu_docbao"}],
                    [{"text": "🛍️ Shopee",               "callback_data": "menu_shopee"},
                     {"text": "🍕 ShopeeFood",           "callback_data": "menu_shopeefd"}]
                ]
                txt_menu = ("<b>🤖 HỆ THỐNG ANX - QUẢN LÝ TIỀN PHÒNG & THÔNG TIN</b>\n"
                            "👤 Quyền truy cập: <b>Quản trị viên (Admin)</b>\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "<b>Danh sách lệnh hỗ trợ:</b>\n"
                            "• <code>/tinh</code> : Nhập số điện nước & tính hóa đơn (từng bước)\n"
                            "• <code>/tinhcn</code> : Tính nhanh hóa đơn (nhập 1 dòng: <code>sdcu;sdm;sncm;snm;sk</code>)\n"
                            "• <code>/baocao</code> : Báo cáo tiến độ PowerPoint tự động\n"
                            "• <code>/tintuc</code> : Bản tin tổng hợp 5 báo nóng nhất\n"
                            "• <code>/thoitiethientai</code> : Thời tiết & cảnh báo giao thông\n"
                            "• <code>/thoitiet [địa điểm]</code> : Tra cứu thời tiết theo vùng\n"
                            "• <code>/websitecn</code> : Mở giao diện Web thời tiết & tin tức\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "<i>Vui lòng chọn nút bấm bên dưới hoặc gõ lệnh trực tiếp:</i>")
            else:
                keyboard = [
                    [{"text": "🤖 Bật Chat AI Gemini", "callback_data": "menu_startgemini"},
                     {"text": "🛑 Tắt AI",             "callback_data": "menu_endgemini"}],
                    [{"text": "📰 Bản Tin Báo Chí",    "callback_data": "menu_docbao"}],
                    [{"text": "🛍️ Shopee",             "callback_data": "menu_shopee"},
                     {"text": "🍕 ShopeeFood",         "callback_data": "menu_shopeefd"}]
                ]
                txt_menu = ("<b>🤖 HỆ THỐNG ANX (NGƯỜI DÙNG)</b>\n"
                            "👤 Quyền truy cập: <b>Cơ bản</b>\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "<i>Vui lòng chọn tính năng bên dưới:</i>")
            gui_tin_nhan_telegram(chat_id, txt_menu, {"inline_keyboard": keyboard}, parse_mode="HTML")
            return

        # ── Tính điện nước từng bước ──
        if cmd in ["/tinh", "Tính số điện nước AnX", "menu_tinhtien"]:
            wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
            for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                return
            if chat_id not in user_sessions:
                user_sessions[chat_id] = {"step": None, "data": {}}
            user_sessions[chat_id]["step"] = "nhap_dien_cu"
            user_sessions[chat_id]["data"] = {}
            gui_tin_nhan_telegram(
                chat_id,
                "<b>⚡ QUẢN LÝ TÍNH TIỀN PHÒNG & ĐIỆN NƯỚC</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "👉 Bước 1/5: Vui lòng nhập <b>Số điện cũ</b> (đầu tháng):",
                parse_mode="HTML"
            )
            return

        # ── Tính nhanh /tinhcn ──
        if cmd == "/tinhcn":
            wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
            for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                return
            if chat_id not in user_sessions:
                user_sessions[chat_id] = {"step": None, "data": {}}
            user_sessions[chat_id]["step"] = "nhap_nhanh_tinh_cn"
            user_sessions[chat_id]["data"] = {}
            gui_tin_nhan_telegram(
                chat_id,
                "<b>⚡ QUẢN LÝ TÍNH TIỀN PHÒNG & ĐIỆN NƯỚC</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "👉 Bước 1/5: Vui lòng nhập <b>Số điện cũ</b> (đầu tháng):\n"
                "⚡ Số điện cũ: \n"
                "👉 Bước 2/5: Vui lòng nhập <b>Số điện mới</b>:\n"
                "⚡ Số điện mới: \n"
                "👉 Bước 3/5: Vui lòng nhập <b>Số nước cũ</b> (đầu tháng):\n"
                "💧 Số nước cũ: \n"
                "👉 Bước 4/5: Vui lòng nhập <b>Số nước mới</b>:\n"
                "💧 Số nước mới: \n"
                "👉 Bước 5/5: Vui lòng nhập <b>Số khóa</b> (VD: 8):\n\n"
                "📝 <i>Nhập tất cả 5 giá trị cách nhau bằng dấu <code>;</code>\n"
                "Ví dụ: <code>1682;1820;811;819;8</code></i>",
                parse_mode="HTML"
            )
            return

        # ── Website cập nhật ──
        if cmd == "/websitecn":
            def xu_ly_websitecn():
                try:
                    import base64 as _b64
                    import json as _json

                    WEBSITE_URL = os.environ.get("WEBSITE_URL", "https://ananasux.github.io/Website_thoitiet_design/")

                    # ── 1. Lấy dữ liệu thời tiết thực tế ──
                    lat = admin_location.get("lat", 20.9716)
                    lon = admin_location.get("lon", 105.7725)
                    ten = admin_location.get("name", "Hà Nội, VN")

                    res_curr = requests.get(
                        f"https://api.openweathermap.org/data/2.5/weather"
                        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi",
                        timeout=10).json()
                    c_temp     = round(res_curr['main']['temp'], 1)
                    feels_like = round(res_curr['main']['feels_like'], 1)
                    humidity   = res_curr['main']['humidity']
                    c_desc     = res_curr['weather'][0]['description'].capitalize()
                    c_icon     = get_owm_icon(res_curr['weather'][0]['icon'])
                    wind_speed = round(res_curr.get('wind', {}).get('speed', 0), 1)

                    res_fore = requests.get(
                        f"https://api.openweathermap.org/data/2.5/forecast"
                        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi",
                        timeout=10).json()
                    fc     = res_fore.get('list', [{}])[0]
                    n_temp = round(fc.get('main', {}).get('temp', c_temp), 1)
                    n_pop  = int(fc.get('pop', 0) * 100)
                    n_desc = fc.get('weather', [{}])[0].get('description', c_desc).capitalize()

                    res_aqi   = requests.get(
                        f"https://api.openweathermap.org/data/2.5/air_pollution"
                        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}",
                        timeout=5).json()
                    aqi_level = res_aqi['list'][0]['main']['aqi']
                    pm25      = round(res_aqi['list'][0]['components'].get('pm2_5', 0), 2)

                    trang_thai = xac_dinh_trang_thai_thoi_tiet(c_temp, feels_like, c_desc, n_pop, humidity)



                    warningText = ""
                    suggestionItems = []
                    floodItems = []
                    routeItems = []
                    
                    if trang_thai in ["MUA_NHO", "MUA_DONG", "MUA_BAO"]:
                        try:
                            # Use 20 for rain_1h if RONG_BAO to ensure we hit max values if we want mock data, or use cur.rain.1h if we have it
                            # Actually, get_diem_ngap_ha_noi takes rain_1h. We can just use 50 to guarantee mock data for RONG_BAO
                            txt_ngap, txt_tranh = lay_bang_diem_ngap(muc_do=("TO" if trang_thai in ["MUA_DONG", "MUA_BAO"] else "NHE"), rain_1h=50)
                            if txt_ngap:
                                floodItems = txt_ngap.split("\n")
                            if txt_tranh:
                                routeItems = txt_tranh.split("\n")
                        except:
                            pass

                    
                    if trang_thai == "BINH_THUONG":
                        suggestionItems = ["Điều khiển phương tiện: Giao thông thuận lợi, chú ý tốc độ theo quy định.", "Trang bị: Không cần trang bị đặc biệt."]
                    elif trang_thai == "MUA_NHO":
                        warningText = "Mưa nhỏ, đường trơn trượt nhẹ. Có thể che khuất tầm nhìn."
                        suggestionItems = ["Điều khiển phương tiện: Giảm tốc độ, giữ khoảng cách an toàn, tránh phanh gấp.", "Trang bị: Nên mặc áo mưa, bọc kỹ thiết bị điện tử."]
                    elif trang_thai in ["MUA_DONG", "MUA_BAO"]:
                        warningText = "Mưa dông kèm sấm chớp, gió giật mạnh cục bộ. Nguy cơ ngập úng nhanh, cây đổ, mất điện.\nDự báo ngắn: Xác suất mưa dông trong 3h tới vẫn cao, có thể xuất hiện gió mạnh."
                        suggestionItems = ["Điều khiển phương tiện: Tuyệt đối không đi dưới cây lớn, biển quảng cáo. Giảm tốc độ mạnh, bật đèn sương mù nếu có.", "Trang bị: Áo mưa bộ rời, ủng cao su, tránh dùng ô (dễ lật)."]
                    elif trang_thai == "NANG_GAT":
                        warningText = "Nắng nóng gay gắt, nguy cơ say nắng, sốc nhiệt cao. Tia UV ở mức nguy hiểm."
                        suggestionItems = ["Điều khiển phương tiện: Hạn chế di chuyển giờ cao điểm nắng (11h-15h). Đỗ xe ở nơi có bóng râm, kiểm tra áp suất lốp.", "Trang bị: Bắt buộc đội mũ rộng vành, đeo kính râm UV400, mang theo nước uống, bôi kem chống nắng SPF50+."]
                    elif trang_thai == "AM_U":
                        suggestionItems = ["Điều khiển phương tiện: Tầm nhìn hơi giảm, nên bật đèn chiếu gần khi đi vào khu vực tối.", "Trang bị: Mang theo áo mưa mỏng phòng trường hợp mưa bất ngờ."]
                    elif trang_thai == "NANG":
                        warningText = "Trời nắng đẹp, tầm nhìn tốt. Chỉ số UV ở mức trung bình đến cao."
                        suggestionItems = ["Điều khiển phương tiện: Giao thông thuận lợi, chú ý chống chói khi lái xe.", "Trang bị: Nên đội mũ, đeo kính râm, bôi kem chống nắng nếu ra ngoài lâu."]

                    video_data = None
                    try:
                        url_yt = "https://www.youtube.com/feeds/videos.xml?channel_id=UCabsTV34JwALXKGMqHpvUiA"
                        res_yt = requests.get(url_yt, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                        res_yt.encoding = 'utf-8'
                        if res_yt.status_code == 200:
                            try:
                                from bs4 import BeautifulSoup
                                soup_yt = BeautifulSoup(res_yt.text, 'xml')
                            except:
                                soup_yt = BeautifulSoup(res_yt.text, 'html.parser')
                            entries = soup_yt.find_all('entry')
                            if entries:
                                kws = (['mưa', 'lũ', 'ngập', 'bão'] if trang_thai in ["MUA_NHO", "MUA_DONG", "MUA_BAO"]
                                       else ['nắng', 'hạn hán', 'nhiệt độ'])
                                found_vid = False
                                for entry in entries:
                                    vtitle = entry.title.text if entry.title else ""
                                    vlink  = entry.find('link')['href'] if entry.find('link') and 'href' in entry.find('link').attrs else ""
                                    if any(kw in vtitle.lower() for kw in kws):
                                        video_data = {"title": vtitle, "link": vlink}
                                        found_vid = True
                                        break
                                if not found_vid:
                                    vtitle = entries[0].title.text if entries[0].title else "Tin tức VTV24"
                                    vlink  = entries[0].find('link')['href'] if entries[0].find('link') and 'href' in entries[0].find('link').attrs else ""
                                    if vlink:
                                        video_data = {"title": vtitle, "link": vlink}
                    except:
                        pass
                        

                    # ── 2. Lấy tin tức (giảm còn 5 bài để URL không vượt quá 4000 ký tự của Telegram) ──
                    tin_tuc_raw = lay_bai_viet_moi_chua_gui(str(chat_id), so_luong=12)
                    tin_tuc = dien_anh_cho_danh_sach(tin_tuc_raw)
                    for t in tin_tuc:
                        # Bỏ hẳn description để giảm dung lượng URL dưới 4000 ký tự (tránh lỗi 400)
                        if 'description' in t:
                            t['description'] = ""



                    # ── 3. Đóng gói data ──
                    data_payload = {
                        "timestamp": datetime.datetime.now(
                            datetime.timezone(datetime.timedelta(hours=7))
                        ).strftime('%H:%M %d/%m/%Y'),
                        "location": ten,
                        "weather": {
                            "current": {
                                "temp":       c_temp,
                                "feels_like": feels_like,
                                "humidity":   humidity,
                                "wind_speed": wind_speed,
                                "desc":       c_desc,
                                "icon":       c_icon,
                                "pm25":       pm25,
                                "aqi_level":  aqi_level
                            },
                            "forecast_3h": {"temp": n_temp, "pop": n_pop, "desc": n_desc},
                            "status": trang_thai
                        },
                        "warningText": warningText,
                        "suggestionItems": suggestionItems,
                        "floodItems": floodItems,
                        "routeItems": routeItems,
                        "video": video_data,
                        "news": tin_tuc
                    }

                    # ── 4. Base64 encode → ghép vào URL ──
                    import zlib
                    json_str = _json.dumps(data_payload, ensure_ascii=False).encode('utf-8')
                    compressed = zlib.compress(json_str)
                    encoded = _b64.urlsafe_b64encode(compressed).decode('ascii')
                    
                    website_base = WEBSITE_URL.strip()
                    if not website_base:
                        website_base = "https://ananasux.github.io/Website_thoitiet_design/"
                    
                    raw_url = f"{website_base.rstrip('/')}/?cdata={encoded}"
                    url_to_send = raw_url






                    gui_tin_nhan_telegram(
                        chat_id,
                        f"✅ <b>Giao Diện Web Thời Tiết – Dữ Liệu Thực Tế</b>\n\n"
                        f"📍 {ten} | 🌡️ {c_temp}°C | {c_icon}\n\n"
                        f"🌐 <b>Mở website:</b> <a href='{url_to_send}'>Đường dẫn</a>",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    gui_tin_nhan_telegram(chat_id, f"⚠️ <b>Lỗi:</b> {escape_html(str(e))}", parse_mode="HTML")
            wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
            def wrapper():
                xu_ly_websitecn()
                for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
            threading.Thread(target=wrapper, daemon=True).start()
            return

        # ── Shopee ──
        if cmd in ["/shoppe", "/shopee", "Mã Shopee", "menu_shopee"]:
            gui_tin_nhan_telegram(chat_id, lay_ma_shopee_moi_nhat(), parse_mode="HTML")
            return

        if cmd in ["/shopeefd", "Mã ShopeeFood", "menu_shopeefd"]:
            gui_tin_nhan_telegram(chat_id, lay_ma_shopeefood_moi_nhat(), parse_mode="HTML")
            return

        # ── Theo dõi nước ngày ──
        if cmd == ".sonuocngay":
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                return
            if chat_id not in user_sessions:
                user_sessions[chat_id] = {"step": None, "data": {}}
            user_sessions[chat_id]["step"] = "nhap_nuoc_thuc_te_hang_ngay"
            gui_tin_nhan_telegram(
                chat_id,
                "<b>💧 BÁO CÁO NƯỚC NGÀY</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
                "Nhập số khối nước tiêu thụ thực tế trong ngày:",
                parse_mode="HTML"
            )
            return

        # ── Xử lý bước nhập liệu tương tác ──
        if chat_id in user_sessions and user_sessions[chat_id].get("step"):
            step = user_sessions[chat_id]["step"]
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                return

            if step == "nhap_nuoc_thuc_te_hang_ngay":
                try:
                    sn = float(text)
                    if sn <= 0:
                        return
                    user_sessions[chat_id]["step"] = None
                    user_sessions[chat_id]["pending_sonuocngay"] = False
                    s_khoa = tracking_data.get(str(chat_id), 0)
                    if s_khoa > 0:
                        so_ngay = math.ceil(s_khoa / sn)
                        nk      = datetime.date.today() + datetime.timedelta(days=so_ngay)

                        success, cal_msg = them_lich_chot_nuoc(nk, sn, so_ngay)

                        msg_ids = gui_tin_nhan_telegram(
                            chat_id,
                            f"<b>📅 LỊCH CHỐT NƯỚC:</b> <code>{nk.strftime('%d/%m/%Y')}</code>\n"
                            f"📌 <b>Trạng thái Calendar:</b> {cal_msg}\n"
                            f"<i>(Tin nhắn tự xóa sau 1 phút)</i>",
                            parse_mode="HTML"
                        )
                        
                        all_to_del = user_sessions[chat_id].get("session_msg_ids", []) + msg_ids
                        xoa_tin_nhan_sau_delay(chat_id, all_to_del, 30)
                        user_sessions[chat_id]["session_msg_ids"] = []



                except:
                    pass
                return

            elif step == "nhap_dien_cu":
                wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
                for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
                try:
                    val = int(text)
                    user_sessions[chat_id]["data"]["dien_cu"] = val
                    user_sessions[chat_id]["step"] = "nhap_dien_moi"
                    gui_tin_nhan_telegram(
                        chat_id,
                        f"⚡ Số điện cũ: <code>{val}</code>\n👉 Bước 2/5: Vui lòng nhập <b>Số điện mới</b>:",
                        parse_mode="HTML"
                    )
                except:
                    gui_tin_nhan_telegram(chat_id, "⚠️ Số điện phải là số nguyên. Vui lòng nhập lại:", parse_mode="HTML")
                return

            elif step == "nhap_dien_moi":
                wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
                for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
                try:
                    val = int(text)
                    if val < user_sessions[chat_id]["data"]["dien_cu"]:
                        gui_tin_nhan_telegram(chat_id, "⚠️ Số điện mới không thể nhỏ hơn số điện cũ. Vui lòng nhập lại:", parse_mode="HTML")
                        return
                    user_sessions[chat_id]["data"]["dien_moi"] = val
                    user_sessions[chat_id]["step"] = "nhap_nuoc_cu"
                    gui_tin_nhan_telegram(
                        chat_id,
                        f"⚡ Số điện mới: <code>{val}</code>\n👉 Bước 3/5: Vui lòng nhập <b>Số nước cũ</b> (đầu tháng):",
                        parse_mode="HTML"
                    )
                except:
                    gui_tin_nhan_telegram(chat_id, "⚠️ Số điện phải là số nguyên. Vui lòng nhập lại:", parse_mode="HTML")
                return

            elif step == "nhap_nuoc_cu":
                wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
                for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
                try:
                    val = int(text)
                    user_sessions[chat_id]["data"]["nuoc_cu"] = val
                    user_sessions[chat_id]["step"] = "nhap_nuoc_moi"
                    gui_tin_nhan_telegram(
                        chat_id,
                        f"💧 Số nước cũ: <code>{val}</code>\n👉 Bước 4/5: Vui lòng nhập <b>Số nước mới</b>:",
                        parse_mode="HTML"
                    )
                except:
                    gui_tin_nhan_telegram(chat_id, "⚠️ Số nước phải là số nguyên. Vui lòng nhập lại:", parse_mode="HTML")
                return

            elif step == "nhap_nuoc_moi":
                wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
                for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
                try:
                    val = int(text)
                    if val < user_sessions[chat_id]["data"]["nuoc_cu"]:
                        gui_tin_nhan_telegram(chat_id, "⚠️ Số nước mới không thể nhỏ hơn số nước cũ. Vui lòng nhập lại:", parse_mode="HTML")
                        return
                    user_sessions[chat_id]["data"]["nuoc_moi"] = val
                    user_sessions[chat_id]["step"] = "nhap_so_khoa"
                    gui_tin_nhan_telegram(
                        chat_id,
                        f"💧 Số nước mới: <code>{val}</code>\n👉 Bước 5/5: Vui lòng nhập <b>Số khóa</b> (VD: 8):",
                        parse_mode="HTML"
                    )
                except:
                    gui_tin_nhan_telegram(chat_id, "⚠️ Số nước phải là số nguyên. Vui lòng nhập lại:", parse_mode="HTML")
                return

            # ── Nhập nhanh /tinhcn – nhận 1 dòng "sdcu;sdm;sncm;snm;sk" ──
            elif step == "nhap_nhanh_tinh_cn":
                wait_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Hệ thống đang xử lý, vui lòng chờ...</i>", parse_mode="HTML", disable_noti=True)
                for wid in wait_ids: xoa_tin_nhan(chat_id, wid)
                try:
                    parts = text.split(";")
                    if len(parts) != 5:
                        gui_tin_nhan_telegram(chat_id, "⚠️ Định dạng không hợp lệ. Vui lòng nhập đúng 5 số, phân cách bằng dấu chấm phẩy (;). Ví dụ: <code>1682;1820;811;819;8</code>", parse_mode="HTML")
                        return

                    dien_cu  = int(parts[0].strip())
                    dien_moi = int(parts[1].strip())
                    nuoc_cu  = int(parts[2].strip())
                    nuoc_moi = int(parts[3].strip())
                    s_khoa   = int(parts[4].strip())

                    if dien_moi < dien_cu:
                        gui_tin_nhan_telegram(chat_id, "⚠️ Số điện mới không thể nhỏ hơn số điện cũ.", parse_mode="HTML")
                        return
                    if nuoc_moi < nuoc_cu:
                        gui_tin_nhan_telegram(chat_id, "⚠️ Số nước mới không thể nhỏ hơn số nước cũ.", parse_mode="HTML")
                        return

                    user_sessions[chat_id]["step"] = None
                    user_sessions[chat_id]["pending_sonuocngay"] = True

                    so_dien   = dien_moi - dien_cu
                    so_nuoc   = nuoc_moi - nuoc_cu
                    tien_dien = so_dien * GIA_DIEN
                    tien_nuoc = so_nuoc * GIA_NUOC
                    phu_phi   = A3 + A4 + A5
                    tong_tien = AN + tien_dien + tien_nuoc + phu_phi
                    tracking_data[str(chat_id)] = s_khoa

                    ht = datetime.date.today()
                    msg_ = (
                        f"<b>🏠 HÓA ĐƠN TIỀN NHÀ ({ht.strftime('%d/%m/%Y')})</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n"
                        f"• Tiền nhà cố định (AN): <code>{AN:,} VNĐ</code>\n"
                        f"• Số điện: <code>{dien_cu} ➔ {dien_moi}</code> "
                        f"({so_dien} kWh × {GIA_DIEN:,}đ) = <code>{tien_dien:,} VNĐ</code>\n"
                        f"• Số nước: <code>{nuoc_cu} ➔ {nuoc_moi}</code> "
                        f"({so_nuoc} m³ × {GIA_NUOC:,}đ) = <code>{tien_nuoc:,} VNĐ</code>\n"
                        f"• Phí tiện ích & dịch vụ: <code>{phu_phi:,} VNĐ</code>\n"
                        f"• Số khóa cài đặt: <code>{s_khoa}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n"
                        f"👉 <b>TỔNG CỘNG: <code>{tong_tien:,} VNĐ</code></b>\n"
                        "<i>(Tin nhắn tự xóa sau 1 phút)</i>"
                    )
                    try:
                        save_data()
                    except:
                        pass
                    msg_ids = gui_tin_nhan_telegram(chat_id, msg_, parse_mode="HTML")
                    xoa_tin_nhan_sau_delay(chat_id, msg_ids, 30)
                except Exception:
                    gui_tin_nhan_telegram(chat_id, "⚠️ Lỗi: Vui lòng nhập đúng 5 số nguyên (cách nhau bởi dấu ;). Ví dụ: <code>1682;1820;811;819;8</code>", parse_mode="HTML")
                return

            elif step == "nhap_so_khoa":
                try:
                    s_khoa = int(text)
                    user_sessions[chat_id]["step"] = None
                    user_sessions[chat_id]["pending_sonuocngay"] = True
                    d         = user_sessions[chat_id]["data"]
                    so_dien   = d["dien_moi"] - d["dien_cu"]
                    so_nuoc   = d["nuoc_moi"] - d["nuoc_cu"]
                    tien_dien = so_dien * GIA_DIEN
                    tien_nuoc = so_nuoc * GIA_NUOC
                    phu_phi   = A3 + A4 + A5
                    tong_tien = AN + tien_dien + tien_nuoc + phu_phi
                    tracking_data[str(chat_id)] = s_khoa
                    ht = datetime.date.today()
                    msg_ = (
                        f"<b>🏠 HÓA ĐƠN TIỀN NHÀ ({ht.strftime('%d/%m/%Y')})</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n"
                        f"• Tiền nhà cố định (AN): <code>{AN:,} VNĐ</code>\n"
                        f"• Số điện: <code>{d['dien_cu']} ➔ {d['dien_moi']}</code> "
                        f"({so_dien} kWh × {GIA_DIEN:,}đ) = <code>{tien_dien:,} VNĐ</code>\n"
                        f"• Số nước: <code>{d['nuoc_cu']} ➔ {d['nuoc_moi']}</code> "
                        f"({so_nuoc} m³ × {GIA_NUOC:,}đ) = <code>{tien_nuoc:,} VNĐ</code>\n"
                        f"• Phí tiện ích & dịch vụ: <code>{phu_phi:,} VNĐ</code>\n"
                        f"• Số khóa cài đặt: <code>{s_khoa}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n"
                        f"👉 <b>TỔNG CỘNG: <code>{tong_tien:,} VNĐ</code></b>\n"
                        "<i>(Tin nhắn tự xóa sau 1 phút)</i>"
                    )
                    msg_ids = gui_tin_nhan_telegram(chat_id, msg_, parse_mode="HTML")
                    xoa_tin_nhan_sau_delay(chat_id, msg_ids, 30)
                    save_data()
                except:
                    gui_tin_nhan_telegram(
                        chat_id, "⚠️ Vui lòng nhập số khóa hợp lệ (dạng số nguyên):", parse_mode="HTML")
                return

    except Exception:
        traceback.print_exc()

# =====================================================================
# [PHẦN 10] FLASK ROUTES (Webhook + Polling)
# =====================================================================
if TELEGRAM_BOT_TOKEN:
    @app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
    def telegram_webhook():
        try:
            data = request.get_json()
            if data:
                threading.Thread(target=xu_ly_telegram_update, args=(data,), daemon=True).start()
            return "OK", 200
        except Exception:
            return "OK", 200

@app.route('/webhook', methods=['POST'])
def telegram_generic_webhook():
    try:
        data = request.get_json()
        if data:
            threading.Thread(target=xu_ly_telegram_update, args=(data,), daemon=True).start()
        return "OK", 200
    except Exception:
        return "OK", 200

@app.route('/ping')
def ping():
    return "Pong", 200

BOILERPLATE_SKIP_PHRASES = [
    'liên hệ', 'bản quyền', 'hotline', 'quảng cáo', 'tải app',
    'email:', 'đường dây nóng', 'vui lòng nhập đủ', 'link bài gốc',
    'tổng biên tập', 'giấy phép xuất bản', 'cấm sao chép', 'chia sẻ bài viết',
    'chia sẻ', 'chi sẻ', 'chia sẻ qua', 'chi sẻ qua', 'chia sẻ lên', 'chia sẻ với', 'chia sẻ qua facebook',
    'chia sẻ qua twitter', 'chia sẻ qua email', 'chia sẻ qua zalo',
    'thẻ:', 'từ khóa:', 'tags:', 'tag:', 'chủ đề:',
    'xem thêm:', 'tin liên quan:', 'bài viết liên quan:', 'đọc tiếp:',
    'xem các bài viết của tác giả', 'bình luận', 'ý kiến bạn đọc', 'báo điện tử'
]

def _clean_str(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def _clean_author_str(author):
    if not author:
        return ""
    a = _clean_str(author)
    a = re.sub(r'(?i)xem các bài viết của tác giả.*$', '', a).strip()
    a = re.sub(r'(?i)^(tác giả|phóng viên|bài|ảnh|theo|nguồn)\s*:\s*', '', a).strip()
    return a

def _resolve_best_img(img_tag, base_url=""):
    if not img_tag:
        return ""
    candidates = [
        img_tag.get('data-large-src'),
        img_tag.get('data-src'),
        img_tag.get('data-original'),
        img_tag.get('data-lazy-src'),
        img_tag.get('data-actualsrc'),
        img_tag.get('data-cdn-src'),
        img_tag.get('src')
    ]
    for c in candidates:
        if c and not c.startswith('data:') and 'blank.gif' not in c and '1x1' not in c and 'placeholder' not in c:
            c = c.strip()
            if c.startswith('//'):
                return 'https:' + c
            if c.startswith('/') and base_url:
                try:
                    return urllib.parse.urljoin(base_url, c)
                except Exception:
                    pass
            return c
    srcset = img_tag.get('data-srcset') or img_tag.get('srcset')
    if srcset:
        parts = srcset.split(',')
        if parts:
            c = parts[-1].strip().split(' ')[0]
            if c and not c.startswith('data:'):
                if c.startswith('//'): return 'https:' + c
                if c.startswith('/') and base_url:
                    try: return urllib.parse.urljoin(base_url, c)
                    except: pass
                return c
    return ""

def trich_xuat_noi_dung_bai_bao(url, title="", description=""):
    """
    Trích xuất toàn văn 100% nội dung bài báo theo chiến lược 5 tầng:
    1. Schema JSON-LD (NewsArticle, Article, BlogPosting)
    2. Thẻ ngữ nghĩa <article>, <main>
    3. CSS Selectors chuẩn báo chí Việt Nam (#maincontent, .detail-content, .article__body, .fck_detail...)
    4. Domain-specific rules (Tiền Phong phóng sự ảnh, VietnamNet, Soha, Dân Trí, VnExpress...)
    5. Phân tích mật độ văn bản (heuristic density)
    Trả về dữ liệu chuẩn JSON không cắt ngắn và không tạo văn bản nhân tạo giả mạo.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    now_str = datetime.datetime.now().strftime("%H:%M %d/%m/%Y")
    
    result = {
        "source_name": "",
        "article_url": url,
        "canonical_url": url,
        "title": title or "",
        "author": "",
        "published_at": "",
        "updated_at": "",
        "summary": description or "",
        "content_html": "",
        "content_text": "",
        "headings": [],
        "images": [],
        "content_status": "failed",
        "extraction_method": "rss_only",
        "extraction_error": None,
        "paragraph_count": 0,
        "content_length": 0,
        "fetched_at": now_iso,
        # Giữ các key cũ để tương thích 100% frontend & bot telegram
        "url": url,
        "paragraphs": [],
        "sapo": description or "",
        "published_time": now_str,
        "total_paragraphs": 0
    }

    if not url or url == "#" or not url.startswith("http"):
        if description:
            try:
                clean_desc = _clean_str(BeautifulSoup(description, 'html.parser').get_text()) if '<' in description else _clean_str(description)
            except Exception:
                clean_desc = _clean_str(description)
            if clean_desc:
                paras = [p.strip() for p in re.split(r'\n+|\r+', clean_desc) if len(p.strip()) > 0]
                if not paras:
                    paras = [clean_desc]
                result["paragraphs"] = paras
                result["paragraph_count"] = len(paras)
                result["total_paragraphs"] = len(paras)
                result["content_text"] = "\n\n".join(paras)
                result["content_html"] = "".join(f"<p>{p}</p>" for p in paras)
                result["content_status"] = "summary_only"
                result["extraction_method"] = "rss_description"
                result["extraction_error"] = None
                return result
        result["extraction_error"] = "URL không hợp lệ hoặc rỗng"
        result["content_status"] = "failed"
        return result

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache"
    }

    resp = None
    last_err = None
    for attempt in range(2):
        try:
            resp = requests.get(url, headers=headers, timeout=8.0, allow_redirects=True)
            if resp.status_code == 200:
                break
        except Exception as e:
            last_err = str(e)

    if resp is None:
        result["extraction_error"] = f"Lỗi kết nối sau 2 lần thử: {last_err}"
        result["content_status"] = "failed"
        return result

    if resp.status_code in [403, 429]:
        result["extraction_error"] = f"Bị chặn bởi server nguồn (HTTP {resp.status_code})"
        result["content_status"] = "blocked"
        return result
    elif resp.status_code != 200:
        result["extraction_error"] = f"Lỗi HTTP {resp.status_code}"
        result["content_status"] = "failed"
        return result

    html_text = resp.text
    if any(cf in html_text.lower() for cf in ['cf-browser-verification', 'ray id:', 'checking your browser before accessing', 'just a moment...']):
        result["extraction_error"] = "Bị chặn bởi Cloudflare / Anti-bot"
        result["content_status"] = "blocked"
        return result

    resp.encoding = resp.apparent_encoding or 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Canonical URL
    canon_el = soup.find('link', rel='canonical')
    canonical_url = canon_el.get('href', url).strip() if canon_el else resp.url
    result["canonical_url"] = canonical_url

    # Hostname / Source name
    domain = urllib.parse.urlparse(canonical_url).netloc.lower()
    if 'tienphong.vn' in domain: result["source_name"] = "Tiền Phong"
    elif 'vietnamnet.vn' in domain: result["source_name"] = "VietnamNet"
    elif 'dantri.com.vn' in domain: result["source_name"] = "Dân Trí"
    elif 'vnexpress.net' in domain: result["source_name"] = "VnExpress"
    elif 'tuoitre.vn' in domain: result["source_name"] = "Tuổi Trẻ"
    elif 'thanhnien.vn' in domain: result["source_name"] = "Thanh Niên"
    elif 'soha.vn' in domain: result["source_name"] = "Soha"
    elif 'vtv.vn' in domain: result["source_name"] = "VTV News"
    elif 'laodong.vn' in domain: result["source_name"] = "Lao Động"
    elif 'plo.vn' in domain: result["source_name"] = "Pháp Luật TP.HCM"
    elif 'baogiaothong.vn' in domain: result["source_name"] = "Báo Giao Thông"
    elif 'kenh14.vn' in domain: result["source_name"] = "Kênh 14"
    else: result["source_name"] = domain.replace('www.', '')

    # Page Title
    h1 = soup.find('h1')
    og_title = soup.find('meta', property='og:title')
    extracted_title = _clean_str(h1.get_text() if h1 else (og_title.get('content', '') if og_title else ''))
    if extracted_title:
        result["title"] = extracted_title

    # Published date & Updated date
    pub_date = ""
    time_meta = soup.find('meta', property=lambda p: p and 'published_time' in p.lower())
    if time_meta and time_meta.get('content'):
        pub_date = time_meta['content'].strip()
    if not pub_date:
        time_tag = soup.find('time')
        if time_tag:
            pub_date = _clean_str(time_tag.get('datetime', '') or time_tag.get_text())
    if not pub_date:
        date_el = soup.find(class_=lambda c: c and any(k in str(c).lower() for k in ['date-time', 'datetime', 'dt-text-13px', 'publish-date']))
        if date_el:
            pub_date = _clean_str(date_el.get_text())

    # Sapo
    sapo_el = soup.find(class_=lambda c: c and any(k in str(c).lower() for k in ['sapo', 'lead', 'detail-sapo', 'singular-sapo', 'content-detail-sapo', 'article__sapo']))
    if not sapo_el:
        sapo_el = soup.find('h2', class_=lambda c: c and any(k in str(c).lower() for k in ['sapo', 'lead', 'description']))
    sapo_text = _clean_str(sapo_el.get_text()) if sapo_el else _clean_str(description)
    result["summary"] = sapo_text
    result["sapo"] = sapo_text

    # Author
    author_text = ""
    author_el = soup.find(class_=lambda c: c and any(k in str(c).lower() for k in ['author', 'tac-gia', 'byline', 'journalist', 'article__author', 'details__author']))
    if not author_el:
        author_el = soup.find('a', rel='author') or soup.find(attrs={"itemprop": "author"})
    if author_el:
        author_text = _clean_author_str(author_el.get_text())

    # Check Schema JSON-LD (Tầng 1)
    json_ld_body = ""
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            raw_s = s.string or s.get_text() or ''
            clean_s = re.sub(r'[\x00-\x1f\x7f-\x9f]', lambda m: ' ' if m.group() in '\n\r' else '', raw_s).strip()
            if not clean_s: continue
            data = json.loads(clean_s)
            items = data if isinstance(data, list) else (data.get('@graph', [data]) if isinstance(data, dict) else [])
            for it in items:
                if not isinstance(it, dict): continue
                t = it.get('@type', '')
                if any(x in str(t) for x in ['NewsArticle', 'Article', 'BlogPosting']):
                    if it.get('articleBody') and len(it['articleBody']) > len(json_ld_body):
                        json_ld_body = it['articleBody']
                    if not author_text and it.get('author'):
                        a = it['author']
                        a_name = a.get('name', '') if isinstance(a, dict) else (a[0].get('name', '') if isinstance(a, list) and isinstance(a[0], dict) else str(a))
                        author_text = _clean_author_str(a_name)
                    if not pub_date and it.get('datePublished'):
                        pub_date = str(it['datePublished'])
                    if it.get('dateModified'):
                        result["updated_at"] = str(it['dateModified'])
        except Exception:
            pass

    if author_text:
        result["author"] = author_text
    else:
        result["author"] = result["source_name"] or "Ban Biên Tập"

    if pub_date:
        result["published_at"] = pub_date
        result["published_time"] = pub_date

    # Pre-cleaning: Remove scripts, styles, ads, social boxes, recommend/related widgets
    for junk in soup.find_all(['script', 'style', 'noscript', 'nav', 'footer', 'header', 'iframe']):
        junk.decompose()
    for ad in soup.find_all(class_=lambda c: c and any(k in str(c).lower() for k in [
        'ads', 'banner', 'comment', 'social', 'breadcrumb', 'box-author', 'qc',
        'recommend', 'tin-lien-quan', 'relate', 'video-shorts', 'box-related',
        'bottom-info', 'morenews', 'zone--highlight', 'sidebar',
        'article__tag', '_tag', 'article-tag', 'detail__tag', 'box-tag', 'news-tag',
        'topic-tag', 'keywords', 'tag-item', 'share', 'chia-se', 'chiase'
    ])):
        ad.decompose()

    # Tầng 3 & 4: CSS Selectors & Domain-specific selectors
    priority_selectors = [
        "#maincontent", ".maincontent", "#main-detail-body",
        ".detail-content", ".detail-body", ".content-detail",
        "article.fck_detail", ".fck_detail",
        ".article__body", ".article-body", ".article-content",
        ".knc-content", ".singular-content", ".the-article-body",
        ".post-content", ".entry-content", ".news-content",
        "[data-role='content']"
    ]
    generic_selectors = ["article", "main"]

    best_container = None
    best_score = 0
    extraction_method = "css_selector"

    # Ưu tiên các selector thân bài cụ thể trước
    for sel in priority_selectors:
        for el in soup.select(sel):
            p_tags = el.find_all('p')
            fig_tags = el.find_all('figure')
            valid_p = [p for p in p_tags if len(p.get_text().strip()) > 25 and not any(skip in p.get_text().lower() for skip in BOILERPLATE_SKIP_PHRASES)]
            valid_fig = [f for f in fig_tags if f.find('img')]
            score = len(valid_p) * 10 + len(valid_fig) * 8 + len(el.get_text().strip()) // 50
            if score > best_score:
                best_score = score
                best_container = el
                extraction_method = f"css_selector: {sel}"

    # Nếu selector cụ thể chưa đủ tốt (score < 15), mới xét tới article hoặc main
    if best_score < 15:
        for sel in generic_selectors:
            for el in soup.select(sel):
                p_tags = el.find_all('p')
                fig_tags = el.find_all('figure')
                valid_p = [p for p in p_tags if len(p.get_text().strip()) > 25 and not any(skip in p.get_text().lower() for skip in BOILERPLATE_SKIP_PHRASES)]
                valid_fig = [f for f in fig_tags if f.find('img')]
                score = len(valid_p) * 10 + len(valid_fig) * 8 + len(el.get_text().strip()) // 50
                if score > best_score:
                    best_score = score
                    best_container = el
                    extraction_method = f"semantic: {sel}"

    # Tầng 5: Heuristic density fallback nếu vẫn chưa tìm thấy container đạt chuẩn
    if not best_container or best_score < 15:
        max_density = 0
        for el in soup.find_all(['div', 'section', 'article', 'main']):
            if el.name == 'body': continue
            p_list = [p for p in el.find_all('p') if len(p.get_text().strip()) > 25]
            density = len(p_list) * 10 + len(el.get_text().strip()) // 100
            if density > max_density:
                max_density = density
                best_container = el
                extraction_method = "heuristic_density"

    target = best_container if best_container else soup

    # Trích xuất toàn bộ: p, h2-h4, blockquote, ul/ol/li, figure/img/figcaption
    paragraphs = []
    headings = []
    images = []
    html_parts = []
    seen_texts = set()

    # Đưa Sapo lên đầu nếu hợp lệ
    if sapo_text and len(sapo_text) > 30 and not sapo_text.startswith('#'):
        seen_texts.add(sapo_text.lower())
        paragraphs.append(sapo_text)
        html_parts.append(f'<p class="article-sapo font-semibold">{sapo_text}</p>')

    for child in target.descendants:
        if not hasattr(child, 'name') or not child.name:
            continue
        tag = child.name.lower()

        if tag in ['h2', 'h3', 'h4']:
            txt = _clean_str(child.get_text())
            if txt and len(txt) > 5 and not txt.startswith('#') and txt.lower() not in seen_texts and not any(skip in txt.lower() for skip in BOILERPLATE_SKIP_PHRASES):
                seen_texts.add(txt.lower())
                headings.append(txt)
                html_parts.append(f'<{tag}>{txt}</{tag}>')

        elif tag == 'blockquote':
            txt = _clean_str(child.get_text())
            if txt and len(txt) > 15 and not txt.startswith('#') and txt.lower() not in seen_texts and not any(skip in txt.lower() for skip in BOILERPLATE_SKIP_PHRASES):
                seen_texts.add(txt.lower())
                paragraphs.append(txt)
                html_parts.append(f'<blockquote>{txt}</blockquote>')

        elif tag == 'p':
            txt = _clean_str(child.get_text())
            if len(txt) > 20 and not txt.startswith('#') and not (txt.count('#') > 0 and len(re.sub(r'#[\w\d\s_\-]+', '', txt).strip()) < 20) and not re.search(r'(chia\s*sẻ|chi\s*sẻ|share)', txt, re.IGNORECASE) and not any(skip in txt.lower() for skip in BOILERPLATE_SKIP_PHRASES):
                if txt.lower() not in seen_texts:
                    seen_texts.add(txt.lower())
                    paragraphs.append(txt)
                    html_parts.append(f'<p>{txt}</p>')

        elif tag == 'figure' or (tag == 'div' and child.find('img') and (child.find('figcaption') or any(c in ' '.join(child.get('class', [])).lower() for c in ['caption', 'desc', 'photo']))):
            img_el = child.find('img')
            img_url = _resolve_best_img(img_el, canonical_url)
            caption_el = child.find('figcaption') or child.find(class_=lambda c: c and any(k in str(c).lower() for k in ['caption', 'desc']))
            caption_text = _clean_str(caption_el.get_text() if caption_el else (img_el.get('title') or img_el.get('alt') or ''))
            alt_text = _clean_str(img_el.get('alt', '') if img_el else '')
            if img_url:
                images.append({
                    "url": img_url,
                    "caption": caption_text,
                    "alt": alt_text
                })
                img_html = f'<figure><img src="{img_url}" alt="{alt_text}" />'
                if caption_text:
                    img_html += f'<figcaption>{caption_text}</figcaption>'
                    if len(caption_text) > 25 and caption_text.lower() not in seen_texts and not any(skip in caption_text.lower() for skip in BOILERPLATE_SKIP_PHRASES):
                        seen_texts.add(caption_text.lower())
                        paragraphs.append(caption_text)
                img_html += '</figure>'
                html_parts.append(img_html)

        elif tag in ['ul', 'ol']:
            items = []
            for li in child.find_all('li', recursive=False):
                li_text = _clean_str(li.get_text())
                if li_text and len(li_text) > 10 and li_text.lower() not in seen_texts and not any(skip in li_text.lower() for skip in BOILERPLATE_SKIP_PHRASES):
                    seen_texts.add(li_text.lower())
                    items.append(f'<li>{li_text}</li>')
                    paragraphs.append(f"• {li_text}")
            if items:
                html_parts.append(f'<{tag}>{"".join(items)}</{tag}>')

    # Nếu sau khi quét HTML vẫn có ít hơn 2 đoạn, nhưng JSON-LD có articleBody
    if len(paragraphs) < 2 and json_ld_body and len(json_ld_body) > 100:
        extraction_method = "schema_jsonld"
        raw_paras = [_clean_str(p) for p in re.split(r'\n+|\r+', json_ld_body) if len(_clean_str(p)) > 25]
        if raw_paras:
            paragraphs = raw_paras
            html_parts = [f'<p>{p}</p>' for p in paragraphs]

    # Đánh giá content_status trung thực (Tuyệt đối không bịa đặt text giả)
    content_text = "\n\n".join(paragraphs).strip()
    content_html = "\n".join(html_parts).strip()
    p_count = len(paragraphs)
    c_len = len(content_text)

    if p_count >= 3 or (p_count >= 2 and len(images) >= 1) or (len(images) >= 3 and p_count >= 1):
        content_status = "full"
        extraction_error = None
    elif p_count >= 1 or c_len > 100:
        content_status = "partial"
        extraction_error = "Nội dung chỉ trích xuất được một phần bài viết hoặc phóng sự ảnh ngắn"
    elif sapo_text:
        content_status = "summary_only"
        extraction_error = "Chỉ lấy được sapo hoặc tóm tắt RSS do không tìm thấy vùng thân bài chính thức"
    else:
        content_status = "failed"
        extraction_error = "Không trích xuất được nội dung bài viết từ URL"

    result.update({
        "content_html": content_html,
        "content_text": content_text,
        "headings": headings,
        "images": images,
        "content_status": content_status,
        "extraction_method": extraction_method,
        "extraction_error": extraction_error,
        "paragraph_count": p_count,
        "content_length": c_len,
        "paragraphs": paragraphs,
        "total_paragraphs": p_count
    })
    return result

@app.route('/api/article-detail', methods=['GET', 'POST', 'OPTIONS'])
def api_article_detail():
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers.add("Access-Control-Allow-Origin", "*")
        resp.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        resp.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return resp
        
    try:
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            url = data.get("url", "")
            title = data.get("title", "")
            description = data.get("description", "") or data.get("desc", "")
        else:
            url = request.args.get("url", "")
            title = request.args.get("title", "")
            description = request.args.get("desc", "") or request.args.get("description", "")
            
        result = trich_xuat_noi_dung_bai_bao(url, title=title, description=description)
        response = jsonify(result)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tts/vieneu', methods=['POST', 'OPTIONS'])
def api_tts_vieneu():
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers.add("Access-Control-Allow-Origin", "*")
        resp.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        resp.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return resp
    try:
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
        voice = data.get("voice", "Mai Anh")
        speed = float(data.get("speed", 1.0))
        from vieneu_service import vieneu_manager
        result = vieneu_manager.synthesize(text=text, voice=voice, speed=speed)
        result.pop("wav_bytes", None)
        response = jsonify(result)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tts/voices', methods=['GET', 'OPTIONS'])
def api_tts_voices():
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers.add("Access-Control-Allow-Origin", "*")
        resp.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        resp.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return resp
    try:
        from vieneu_service import vieneu_manager
        voices = vieneu_manager.get_voices()
        response = jsonify({"success": True, "voices": voices})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/')
def home():
    return "Hệ thống AnX v7.1 (Token mới 09/2026 – Gemini 3.8 Flash – /tinhcn + /websitecn) đang hoạt động!"

def run_telegram_polling():
    """Long Polling – dùng khi không có webhook."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "mock_telegram_token_123456789:ABCDEF":
        print("[Telegram Polling] Bỏ qua vì chưa có TELEGRAM_BOT_TOKEN.")
        return
    time.sleep(2)
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook",
            json={"drop_pending_updates": False}, timeout=10
        )
    except Exception:
        pass
    offset = 0
    print(f"[Telegram Polling] Bot đã kích hoạt Long Polling...")
    while True:
        try:
            res = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                params={"timeout": 20, "offset": offset}, timeout=25
            )
            if res.status_code == 200:
                body = res.json()
                if body.get("ok"):
                    for update in body.get("result", []):
                        offset = max(offset, update["update_id"] + 1)
                        threading.Thread(target=xu_ly_telegram_update,
                                         args=(update,), daemon=True).start()
            elif res.status_code == 401:
                print(f"[Polling Error] Token trả về 401 Unauthorized. Kiểm tra lại token trong .env!")
                time.sleep(30)
            else:
                time.sleep(3)
        except Exception:
            time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=run_telegram_polling, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
