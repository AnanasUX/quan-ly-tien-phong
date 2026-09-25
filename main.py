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
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
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
    raise RuntimeError("❌ TELEGRAM_BOT_TOKEN chưa được cấu hình trong biến môi trường!")

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
    with json_lock:
        if os.path.exists(FILE_DATA):
            try:
                with open(FILE_DATA, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    active_auto_news_chats = set(data.get("active_auto_news_chats", []))
                    tracking_data          = data.get("tracking_data", {})
                    active_tracking_chats  = set(data.get("active_tracking_chats", []))
                    pinned_weather_msgs    = data.get("pinned_weather_msgs", {})
                    last_weather_alerts    = data.get("last_weather_alerts", {})
                    raw_sent_set           = data.get("sent_articles_set", {})
                    sent_articles_set      = {k: set(v) for k, v in raw_sent_set.items()}
                    saved_loc              = data.get("admin_location")
                    if saved_loc: admin_location = saved_loc
                    last_report_msgs  = data.get("last_report_msgs", {})
                    ai_chat_sessions  = set(data.get("ai_chat_sessions", []))
            except Exception:
                pass

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
    return msg_ids

def gui_anh_telegram(chat_id, photo_url, caption):
    url_send_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        res = requests.post(url_send_photo,
                            json={"chat_id": chat_id, "photo": photo_url,
                                  "caption": caption, "parse_mode": "HTML"}, timeout=10)
        if res.status_code != 200:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            res_img = requests.get(photo_url, headers=headers, timeout=10)
            if res_img.status_code == 200:
                files = {"photo": ("image.jpg", res_img.content)}
                data  = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
                requests.post(url_send_photo, data=data, files=files, timeout=15)
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
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
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
                    if any(x in err_msg.lower() for x in ["not found", "is not found", "not supported"]):
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

def xu_ly_gemini_chat(chat_id, cau_hoi):
    wait_msg = gui_tin_nhan_telegram(chat_id, "🤖 <i>Đang trả lời...</i>", parse_mode="HTML")
    try:
        success, result = goi_gemini_api(cau_hoi)
        for mid in wait_msg:
            xoa_tin_nhan(chat_id, mid)
        if success:
            gui_tin_nhan_telegram(chat_id, f"🤖 <b>Gemini AI:</b>\n\n{escape_html(result)}", parse_mode="HTML")
        else:
            if any(x in result.lower() for x in ["high demand", "temporarily", "spikes", "overloaded", "timeout"]):
                result = "Model đang quá tải hoặc chậm. Vui lòng thử lại sau ít phút."
            gui_tin_nhan_telegram(chat_id, f"⚠️ <b>Lỗi Gemini:</b> {escape_html(result)}", parse_mode="HTML")
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
        event = {
            'summary': '💧 Lịch chốt số nước',
            'description': f'Hệ thống AnX nhắc nhở chốt nước.\n- Tiêu thụ thực tế: {so_khoi} khối/ngày\n- Số ngày dùng: {so_ngay} ngày.',
            'start': {
                'date': ngay_chot.strftime('%Y-%m-%d'),
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
            'end': {
                'date': (ngay_chot + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
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

def day_du_lieu_google_sheets():
    """Quét Drive rồi ghi vào Google Sheets theo cấu trúc A(STT) B(Thư mục cha) C(File gốc) D(File đã làm) E(Trạng thái).
    Mỗi lần gọi sẽ xóa dữ liệu cũ rồi ghi mới từ hàng 3.
    """
    if not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json'):
        return False, "Không tìm thấy credentials.json"

    try:
        creds         = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)

        # ── 1. Quét Drive (logic giống tao_bao_cao_powerpoint) ──────────────
        query_main = (f"'{POWERPOINT_FOLDER_ID}' in parents and trashed=false "
                      f"and mimeType='application/vnd.google-apps.folder'")
        results     = drive_service.files().list(q=query_main, fields="files(id, name)", pageSize=1000).execute()
        raw_folders = results.get('files', [])
        main_folders = sorted(raw_folders, key=lambda x: (trich_xuat_so_tuan(x['name']), x['name']))

        rows = []   # Mỗi phần tử: (folder_name, orig_file, processed_file_or_none)
        stt  = 1

        for main_folder in main_folders:
            folder_name = main_folder['name']
            folder_id   = main_folder['id']

            if not ("TUAN" in folder_name.upper() or "KNTT" in folder_name.upper()):
                continue

            match_tuan = re.search(r'(?i)tuan\s*(\d+)', folder_name)
            tien_to    = f"Tuan{match_tuan.group(1)}_" if match_tuan else ""

            query_sub   = f"'{folder_id}' in parents and trashed=false"
            sub_results = drive_service.files().list(
                q=query_sub, fields="files(id, name, mimeType)", pageSize=1000
            ).execute()

            thu_muc_goc_id  = None
            processed_files = []

            for item in sub_results.get('files', []):
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    if item['name'].strip().lower() == "thu_muc_goc":
                        thu_muc_goc_id = item['id']
                elif item['name'].lower().endswith('.pptx'):
                    processed_files.append(item['name'])

            if thu_muc_goc_id:
                orig_results = drive_service.files().list(
                    q=(f"'{thu_muc_goc_id}' in parents and trashed=false "
                       f"and mimeType!='application/vnd.google-apps.folder'"),
                    fields="files(name)", pageSize=1000
                ).execute()
                original_files  = sorted([f['name'] for f in orig_results.get('files', [])
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
                    # C = file gốc (thu_muc_goc), D = file đã xử lý
                    if found:
                        rows.append([stt, folder_name, orig, found, "hoàn thành"])
                        matched_processed.add(found)
                    else:
                        # D = tên dự kiến (chưa tồn tại)
                        expected = (tien_to + orig) if (tien_to and not orig.lower().startswith(tien_to.lower())) else orig
                        rows.append([stt, folder_name, orig, expected, "chưa làm"])
                    stt += 1

                # File processed không khớp gốc nào (thừa)
                for proc in processed_files:
                    if proc not in matched_processed:
                        expected_orig = re.sub(r'(?i)^tuan\d+_', '', proc) if tien_to else proc
                        rows.append([stt, folder_name, expected_orig, proc, "hoàn thành"])
                        stt += 1
            else:
                # Không có thu_muc_goc → liệt kê processed_files trực tiếp
                for proc in sorted(processed_files):
                    rows.append([stt, folder_name, "", proc, "hoàn thành"])
                    stt += 1

        # ── 2. Ghi vào Google Sheets ─────────────────────────────────────────
        sheet = sheets_service.spreadsheets()

        # Lấy tên của Sheet đầu tiên để ghi dữ liệu
        spreadsheet_info = sheets_service.spreadsheets().get(spreadsheetId=SHEETS_ID).execute()
        sheet_name = spreadsheet_info['sheets'][0]['properties']['title']

        # Xóa toàn bộ dữ liệu cũ từ hàng 2
        sheet.values().clear(
            spreadsheetId=SHEETS_ID,
            range=f"'{sheet_name}'!A2:E"
        ).execute()

        # Ghi dữ liệu từ hàng 2, viết hoa trạng thái để khớp dropdown
        if rows:
            for r in rows:
                if r[4] == "hoàn thành":
                    r[4] = "Hoàn thành"
                elif r[4] == "chưa làm":
                    r[4] = "Chưa làm"

            sheet.values().update(
                spreadsheetId=SHEETS_ID,
                range=f"'{sheet_name}'!A2:E{1 + len(rows)}",
                valueInputOption="USER_ENTERED",
                body={"values": rows}
            ).execute()

        return True, f"Đã ghi {len(rows)} dòng vào Google Sheets."

    except Exception as e:
        return False, str(e)


def tao_bao_cao_powerpoint():
    if not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json'):
        return "⚠️ Lỗi hệ thống: Không tìm thấy file <code>credentials.json</code>. Vui lòng thêm file này vào thư mục chứa code."

    msg = "📊 <b>BÁO CÁO TIẾN ĐỘ POWERPOINT</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"

    try:
        creds         = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)

        query_main = (f"'{POWERPOINT_FOLDER_ID}' in parents and trashed=false "
                      f"and mimeType='application/vnd.google-apps.folder'")
        results     = drive_service.files().list(q=query_main, fields="files(id, name)", pageSize=1000).execute()
        raw_folders = results.get('files', [])

        main_folders = sorted(raw_folders, key=lambda x: (trich_xuat_so_tuan(x['name']), x['name']))
        co_du_lieu   = False

        for main_folder in main_folders:
            folder_name = main_folder['name']
            folder_id   = main_folder['id']

            if not (folder_name.upper().startswith("TUAN") or
                    folder_name.upper().startswith("KNTT") or
                    "TUAN" in folder_name.upper()):
                continue

            co_du_lieu = True
            msg += f"📁 <b>{escape_html(folder_name)}</b>\n  + Thư mục con: thu_muc_goc\n"

            tien_to = ""
            match_tuan = re.search(r'(?i)tuan\s*(\d+)', folder_name)
            if match_tuan:
                tien_to = f"Tuan{match_tuan.group(1)}_"

            query_sub   = f"'{folder_id}' in parents and trashed=false"
            sub_results = drive_service.files().list(
                q=query_sub, fields="files(id, name, mimeType)", pageSize=1000
            ).execute()

            thu_muc_goc_id  = None
            processed_files = []

            for item in sub_results.get('files', []):
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    if item['name'].strip().lower() == "thu_muc_goc":
                        thu_muc_goc_id = item['id']
                elif item['name'].lower().endswith('.pptx'):
                    processed_files.append(item['name'])

            file_list = []

            if thu_muc_goc_id:
                orig_results = drive_service.files().list(
                    q=(f"'{thu_muc_goc_id}' in parents and trashed=false "
                       f"and mimeType!='application/vnd.google-apps.folder'"),
                    fields="files(name)", pageSize=1000
                ).execute()
                original_files  = sorted([f['name'] for f in orig_results.get('files', [])
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
                        file_list.append(f"    - {escape_html(found)}(hoàn thành);")
                        matched_processed.add(found)
                    else:
                        display_name = orig
                        if tien_to and not orig.lower().startswith(tien_to.lower()):
                            display_name = tien_to + orig
                        file_list.append(f"    - {escape_html(display_name)};")

                for proc in processed_files:
                    if proc not in matched_processed:
                        display_name = proc
                        if tien_to and not proc.lower().startswith(tien_to.lower()):
                            display_name = tien_to + proc
                        file_list.append(f"    - {escape_html(display_name)};")

                if not original_files and not processed_files:
                    file_list.append("    - <i>Thư mục gốc trống, chưa có file nào</i>;")

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
                            file_list.append(f"    - {escape_html(all_pptx[j])}(hoàn thành);")
                            matched_indices.add(i)
                            matched_indices.add(j)
                            break

                for i in range(len(all_pptx)):
                    if i not in matched_indices:
                        d_name = all_pptx[i]
                        if tien_to and not d_name.lower().startswith(tien_to.lower()):
                            d_name = tien_to + d_name
                        file_list.append(f"    - {escape_html(d_name)};")

                if not all_pptx:
                    file_list.append("    - <i>Thư mục rỗng, chưa có file nào</i>;")

            if file_list:
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

    random.seed(datetime.now().strftime("%Y%m%d%H"))
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
                    kws = (['mưa', 'lũ', 'ngập', 'bão'] if trang_thai in ["MUA_NHE", "RONG_BAO"]
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
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(ten_dia_diem)}&format=json&limit=1"
        res = requests.get(url, headers={"User-Agent": "AnXBot/1.0"}, timeout=10).json()
        if res:
            return {"thanh_cong": True, "lat": float(res[0]["lat"]), "lon": float(res[0]["lon"]), "name": res[0].get("display_name", ten_dia_diem)}
    except:
        pass
    return {"thanh_cong": False}

def lay_tat_ca_bai_viet_ngau_nhien():
    danh_sach_tong  = []
    headers         = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    nguon_rss       = [val for val in DANH_SACH_TRANG.values()]

    if TRANG_THAI_THOI_TIET == "MUA_CA_NGAY":
        nguon_rss.append({"ten": "⚠️ CẢNH BÁO MƯA LŨ",
                          "muc": ["https://news.google.com/rss/search?q=ngập+lụt+OR+mưa+lớn+OR+lũ+quét&hl=vi&gl=VN&ceid=VN:vi"]})
    elif TRANG_THAI_THOI_TIET == "NANG_CA_NGAY":
        nguon_rss.append({"ten": "⚠️ CẢNH BÁO NẮNG NÓNG",
                          "muc": ["https://news.google.com/rss/search?q=hạn+hán+OR+nắng+nóng+gay+gắt&hl=vi&gl=VN&ceid=VN:vi"]})
    nguon_rss.append({"ten": "🌐 Tin Nổi Bật",
                      "muc": ["https://news.google.com/rss?hl=vi&gl=VN&ceid=VN:vi"]})

    for t_info in nguon_rss:
        for url in t_info["muc"]:
            try:
                res = requests.get(url, headers=headers, timeout=10)
                res.encoding = 'utf-8'
                if res.status_code != 200:
                    continue
                try:    soup = BeautifulSoup(res.text, 'xml')
                except: soup = BeautifulSoup(res.text, 'html.parser')
                for item in soup.find_all('item')[:5]:
                    raw_title = item.title.text.strip() if item.title else "News"
                    title     = html.unescape(raw_title)
                    raw_desc  = item.description.text.strip() if item.description else ""
                    desc      = html.unescape(raw_desc)
                    link      = item.link.text.strip() if item.link else ""
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
                    try:    c_desc = BeautifulSoup(desc, 'html.parser').get_text().strip()
                    except: c_desc = desc
                    c_desc = html.unescape(c_desc)
                    if len(c_desc) > 240:
                        c_desc = c_desc[:240] + "..."
                    if link:
                        danh_sach_tong.append({
                            "title": title, "description": c_desc,
                            "link": link,   "image": img_url,
                            "author": t_info["ten"], "source": t_info["ten"]
                        })
            except:
                continue
    random.shuffle(danh_sach_tong)
    return danh_sach_tong

def lay_bai_viet_moi_chua_gui(chat_id_str, so_luong=5):
    if chat_id_str not in sent_articles_set:
        sent_articles_set[chat_id_str] = set()
    tat_ca_tin = lay_tat_ca_bai_viet_ngau_nhien()
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

        tin_tuc = lay_tat_ca_bai_viet_ngau_nhien()[:15]
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
                       if ht_time - user_last_news_sent.get(str(c), 0) >= 3600]
        if not valid_chats:
            return

        tat_ca_tin = lay_tat_ca_bai_viet_ngau_nhien()
        if not tat_ca_tin:
            return

        for chat_id in valid_chats:
            chat_str = str(chat_id)
            if chat_str not in sent_articles_set:
                sent_articles_set[chat_str] = set()
            chua_gui = [b for b in tat_ca_tin if b['link'] not in sent_articles_set[chat_str]]
            if len(chua_gui) < 5:
                sent_articles_set[chat_str].clear()
                chua_gui = tat_ca_tin
            ds_bai = chua_gui[:5]
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
                if bai['image']:
                    gui_anh_telegram(chat_id, bai['image'], caption)
                else:
                    gui_tin_nhan_telegram(chat_id, caption, parse_mode="HTML", disable_noti=True)
            user_last_news_sent[chat_str] = time.time()
        save_data()
    except:
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
        tin_tuc   = lay_tat_ca_bai_viet_ngau_nhien()[:15]
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
            threading.Thread(target=thread_xu_ly_tin_tuc, daemon=True).start()
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
            threading.Thread(target=xu_ly_tt_hientai_rieng, daemon=True).start()
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
                threading.Thread(target=xu_ly_tt_nhanh, daemon=True).start()
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
                threading.Thread(target=xu_ly_tt_theo_vung, daemon=True).start()
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
                "⏳ <i>Đang quét hệ thống Google Drive...\n(Báo cáo tự xóa sau 2 phút)</i>",
                parse_mode="HTML", disable_noti=True
            )
            def tien_trinh_baocao_va_huy():
                try:
                    bao_cao_html = tao_bao_cao_powerpoint()
                    
                    # Gọi hàm đồng bộ Google Sheets
                    sheets_success, sheets_msg = day_du_lieu_google_sheets()
                    if sheets_success:
                        bao_cao_html += f"\n\n✅ <b>Đồng bộ Google Sheets:</b> Thành công ({escape_html(sheets_msg)})"
                    else:
                        bao_cao_html += f"\n\n⚠️ <b>Đồng bộ Google Sheets:</b> Thất bại ({escape_html(sheets_msg)})"
                        
                    for w_id in wait_msg_ids:
                        xoa_tin_nhan(chat_id, w_id)
                    new_ids = gui_tin_nhan_telegram(chat_id, bao_cao_html, parse_mode="HTML", disable_noti=True)
                    last_report_msgs[chat_id] = new_ids
                    save_data()
                    time.sleep(120)
                    for m_id in new_ids:
                        xoa_tin_nhan(chat_id, m_id)
                    last_report_msgs[chat_id] = []
                    save_data()
                except Exception as e:
                    print("Lỗi khi chạy báo cáo:", e)
                    pass
            threading.Thread(target=tien_trinh_baocao_va_huy, daemon=True).start()
            return

        # ── Đổi vùng thời tiết ──
        if cmd.startswith("/vung"):
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                return
            if chat_id in user_sessions:
                user_sessions[chat_id]["step"] = None
            ten_vung = text.replace("/vung", "").strip()
            if not ten_vung:
                return
            kq = tim_toa_do_theo_ten(ten_vung)
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

                    # ── 2. Lấy tin tức (giảm còn 5 bài để URL không vượt quá 4000 ký tự của Telegram) ──
                    tin_tuc = lay_tat_ca_bai_viet_ngau_nhien()[:5]

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
                        "news": tin_tuc
                    }

                    # ── 4. Base64 encode → ghép vào URL ──
                    encoded = _b64.urlsafe_b64encode(
                        _json.dumps(data_payload, ensure_ascii=False).encode('utf-8')
                    ).decode('ascii')
                    
                    website_base = WEBSITE_URL.strip()
                    if not website_base:
                        website_base = "https://ananasux.github.io/Website_thoitiet_design/"
                    
                    raw_url = f"{website_base.rstrip('/')}/?data={encoded}"
                    url_to_send = raw_url

                    # Gọi API rút gọn link (TinyURL) để lách luật độ dài của Telegram
                    try:
                        import requests
                        tiny_res = requests.get(f"http://tinyurl.com/api-create.php?url={raw_url}", timeout=5)
                        if tiny_res.status_code == 200 and tiny_res.text.startswith("http"):
                            url_to_send = tiny_res.text
                    except Exception:
                        pass

                    gui_tin_nhan_telegram(
                        chat_id,
                        f"✅ <b>Giao Diện Web Thời Tiết – Dữ Liệu Thực Tế</b>\n\n"
                        f"📍 {ten} | 🌡️ {c_temp}°C | {c_icon}\n\n"
                        f"🌐 <b>Mở website:</b>\n{url_to_send}",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    gui_tin_nhan_telegram(chat_id, f"⚠️ <b>Lỗi:</b> {escape_html(str(e))}", parse_mode="HTML")
            threading.Thread(target=xu_ly_websitecn, daemon=True).start()
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
                        xoa_tin_nhan_sau_delay(chat_id, msg_ids, 60)
                except:
                    pass
                return

            elif step == "nhap_dien_cu":
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
                    xoa_tin_nhan_sau_delay(chat_id, msg_ids, 60)
                except Exception:
                    gui_tin_nhan_telegram(chat_id, "⚠️ Lỗi: Vui lòng nhập đúng 5 số nguyên (cách nhau bởi dấu ;). Ví dụ: <code>1682;1820;811;819;8</code>", parse_mode="HTML")
                return

            elif step == "nhap_so_khoa":
                try:
                    s_khoa = int(text)
                    user_sessions[chat_id]["step"] = None
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
                    xoa_tin_nhan_sau_delay(chat_id, msg_ids, 60)
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

@app.route('/')
def home():
    return "Hệ thống AnX v7.1 (Token mới 09/2026 – Gemini 2.5 Flash – /tinhcn + /websitecn) đang hoạt động!"

def run_telegram_polling():
    """Long Polling – dùng khi không có webhook."""
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
