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

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8502160323:AAGC19pmi7bd1RLKu89nH9jOyS7Qr833zp0")
ZALO_WEBHOOK_URL = os.environ.get("ZALO_WEBHOOK_URL", "https://hook.eu1.make.com/9ruvgdciavfa1k6xf2vzpkn6zk2umnc7")
CALENDAR_ID = os.environ.get("CALENDAR_ID", "mrkun28@gmail.com") 

AUTHORIZED_USERNAME = os.environ.get("AUTHORIZED_USERNAME", "anaa2700") 
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "a201c471567522a7d0b7a0567ad245fe")
POWERPOINT_FOLDER_ID = os.environ.get("POWERPOINT_FOLDER_ID", "1BwFCLX0Fjag9xM13mHIJTOYvZ6dYW5Ox")
DOC_LOGIC_ID = os.environ.get("DOC_LOGIC_ID", "1a9_qNqFEpbmuIoKuEvT3cExHzpszov4THOfm1ztCZc8")
DOC_NEWS_ID = os.environ.get("DOC_NEWS_ID", "NHẬP_ID_FILE_DOCS_TIN_TỨC_VÀO_ĐÂY") 

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

user_sessions = {}
active_tracking_chats = set()
active_auto_news_chats = set()
tracking_data = {} 
sent_articles_history = {}
sent_articles_set = {}
pinned_weather_msgs = {}
last_weather_alerts = {} 
last_report_msgs = {}
user_last_news_sent = {}

ai_chat_sessions = set()

admin_location = {"lat": 20.9716, "lon": 105.7725, "name": "Hà Nội, VN"}
TRANG_THAI_THOI_TIET = "BINH_THUONG"

DANH_SACH_TRANG = {
    "1": {"ten": "📰 Dân Trí", "muc": ["https://dantri.com.vn/rss/home.rss", "https://dantri.com.vn/rss/xa-hoi.rss", "https://dantri.com.vn/rss/the-gioi.rss"]},
    "2": {"ten": "🇻🇳 VnExpress", "muc": ["https://vnexpress.net/rss/tin-moi-nhat.rss", "https://vnexpress.net/rss/kinh-doanh.rss", "https://vnexpress.net/rss/thoi-su.rss"]},
    "3": {"ten": "🌸 Kênh 14", "muc": ["https://kenh14.vn/home.rss", "https://kenh14.vn/star.rss", "https://kenh14.vn/xa-hoi.rss"]},
    "4": {"ten": "📜 Tuổi Trẻ", "muc": ["https://tuoitre.vn/rss/tin-moi-nhat.rss", "https://tuoitre.vn/rss/thoi-su.rss", "https://tuoitre.vn/rss/the-gioi.rss"]},
    "5": {"ten": "🍀 Thanh Niên", "muc": ["https://thanhnien.vn/rss/home.rss", "https://thanhnien.vn/rss/thoi-su.rss", "https://thanhnien.vn/rss/the-gioi.rss"]},
    "6": {"ten": "🌐 VietnamNet", "muc": ["https://vietnamnet.vn/rss/tin-moi-nhat.rss", "https://vietnamnet.vn/rss/thoi-su.rss"]},
    "7": {"ten": "⚡ Lao Động", "muc": ["https://laodong.vn/rss/home.rss", "https://laodong.vn/rss/thoi-su.rss"]},
    "8": {"ten": "📺 VTV News", "muc": ["https://vtv.vn/trong-nuoc.rss", "https://vtv.vn/the-gioi.rss"]},
    "9": {"ten": "⚖️ Pháp Luật", "muc": ["https://plo.vn/rss/thoi-su-c2.rss"]},
    "10": {"ten": "🚗 Giao Thông", "muc": ["https://www.baogiaothong.vn/rss/thoi-su.rss"]}
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
                    tracking_data = data.get("tracking_data", {})
                    active_tracking_chats = set(data.get("active_tracking_chats", []))
                    pinned_weather_msgs = data.get("pinned_weather_msgs", {})
                    last_weather_alerts = data.get("last_weather_alerts", {})
                    raw_sent_set = data.get("sent_articles_set", {})
                    sent_articles_set = {k: set(v) for k, v in raw_sent_set.items()}
                    saved_loc = data.get("admin_location")
                    if saved_loc: admin_location = saved_loc
                    last_report_msgs = data.get("last_report_msgs", {})
                    ai_chat_sessions = set(data.get("ai_chat_sessions", []))
            except Exception: pass

def save_data():
    with json_lock:
        try:
            serializable_sent_set = {k: list(v) for k, v in sent_articles_set.items()}
            with open(FILE_DATA, "w", encoding="utf-8") as f:
                json.dump({
                    "active_auto_news_chats": list(active_auto_news_chats),
                    "tracking_data": tracking_data,
                    "active_tracking_chats": list(active_tracking_chats),
                    "pinned_weather_msgs": pinned_weather_msgs,
                    "last_weather_alerts": last_weather_alerts,
                    "sent_articles_set": serializable_sent_set,
                    "admin_location": admin_location,
                    "last_report_msgs": last_report_msgs,
                    "ai_chat_sessions": list(ai_chat_sessions)
                }, f, ensure_ascii=False)
        except Exception: pass

load_data()

def dong_bo_bo_nho_he_thong():
    if not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json'): return
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)
        request = drive_service.files().export_media(fileId=DOC_LOGIC_ID, mimeType='text/plain')
        content = request.execute().decode('utf-8', errors='ignore')
        with open("core_logic_memory.txt", "w", encoding="utf-8") as f:
            f.write(content)
    except Exception: pass

threading.Thread(target=dong_bo_bo_nho_he_thong).start()

def ghi_logic_moi_vao_docs(noi_dung_moi):
    if not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json'): return False
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
        docs_service = build('docs', 'v1', credentials=creds)
        doc = docs_service.documents().get(documentId=DOC_LOGIC_ID).execute()
        content = doc.get('body').get('content')
        end_index = content[-1]['endIndex'] - 1 
        ht = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        text_to_insert = f"\n\n[NEW_LOGIC_UPDATE - {ht.strftime('%H:%M %d/%m/%Y')}]\n{noi_dung_moi}\n"
        requests_payload = [{'insertText': {'location': {'index': end_index}, 'text': text_to_insert}}]
        docs_service.documents().batchUpdate(documentId=DOC_LOGIC_ID, body={'requests': requests_payload}).execute()
        with open("core_logic_memory.txt", "a", encoding="utf-8") as f:
            f.write(text_to_insert)
        return True
    except Exception: return False

def kiem_tra_quyen_admin(chat_id, user_id, username):
    if username and username.lower() == AUTHORIZED_USERNAME.lower(): return True
    if str(chat_id) == str(user_id): return True
    if str(chat_id).startswith('-'):
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChatMember"
        try:
            res = requests.get(url, params={"chat_id": chat_id, "user_id": user_id}, timeout=5).json()
            if res.get("ok") and res["result"]["status"] in ["creator", "administrator"]: return True
        except: pass
    return False

# =====================================================================
# [PHẦN 3] MODULE TELEGRAM & CƠ CHẾ BATCH DELETE 30S
# =====================================================================
def escape_html(text): return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def xoa_tin_nhan(chat_id, message_id):
    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage", json={"chat_id": chat_id, "message_id": message_id}, timeout=5)
    except: pass

def xoa_tin_nhan_sau_delay(chat_id, msg_ids, delay=10):
    if not msg_ids: return
    def task():
        time.sleep(delay)
        for mid in msg_ids: xoa_tin_nhan(chat_id, mid)
    t = threading.Thread(target=task, daemon=True)
    t.start()


def send_warning(chat_id, text, delay_seconds=3):
    """Send a warning message that auto‑deletes after *delay_seconds* seconds."""
    msg_ids = gui_tin_nhan_telegram(chat_id, text, parse_mode="HTML")
    if msg_ids:
        xoa_tin_nhan_sau_delay(chat_id, msg_ids, delay_seconds)

user_msg_queue = {}
queue_lock = threading.Lock()

def xoa_tin_nhan_nguoi_dung_cung_luc(chat_id):
    if str(chat_id) in ai_chat_sessions:
        with queue_lock: 
            if chat_id in user_msg_queue: user_msg_queue[chat_id].clear()
        return

    with queue_lock:
        if chat_id in user_msg_queue:
            m_ids = list(user_msg_queue[chat_id])
            user_msg_queue[chat_id].clear()
        else:
            m_ids = []
    for mid in m_ids: xoa_tin_nhan(chat_id, mid)

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
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    lines = noi_dung.split('\n')
    current_msg = ""
    msg_ids = []
    for line in lines:
        if len(current_msg) + len(line) + 1 > 4000:
            payload = {"chat_id": chat_id, "text": current_msg, "parse_mode": parse_mode, "disable_web_page_preview": True, "disable_notification": disable_noti}
            if reply_markup: payload["reply_markup"] = reply_markup
            try: 
                res = requests.post(url, json=payload, timeout=10).json()
                if res.get('ok'): msg_ids.append(res['result']['message_id'])
            except: pass
            current_msg = line + "\n"; time.sleep(0.3)
        else: current_msg += line + "\n"
    if current_msg.strip():
        payload = {"chat_id": chat_id, "text": current_msg, "parse_mode": parse_mode, "disable_web_page_preview": True, "disable_notification": disable_noti}
        if reply_markup: payload["reply_markup"] = reply_markup
        try: 
            res = requests.post(url, json=payload, timeout=10).json()
            if res.get('ok'): msg_ids.append(res['result']['message_id'])
        except: pass
    return msg_ids

def gui_anh_telegram(chat_id, photo_url, caption):
    url_send_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        res = requests.post(url_send_photo, json={"chat_id": chat_id, "photo": photo_url, "caption": caption, "parse_mode": "HTML"}, timeout=10)
        if res.status_code != 200:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            res_img = requests.get(photo_url, headers=headers, timeout=10)
            if res_img.status_code == 200:
                files = {"photo": ("image.jpg", res_img.content)}
                data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
                requests.post(url_send_photo, data=data, files=files, timeout=15)
    except Exception: pass

# =====================================================================
# [PHẦN 4] MODULE GEMINI CHAT
# =====================================================================
def sua_loi_mojibake(text):
    if not isinstance(text, str) or not text: return text
    dau_hieu = ("Ã", "Â", "áº", "á»", "Ä", "Å", "Æ", "Ð", "Ñ", "â€™", "â€œ", "â€")
    if not any(x in text for x in dau_hieu): return text
    try: return text.encode("latin1").decode("utf-8")
    except: return text

def goi_gemini_api(cau_hoi):
    models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-2.0-flash", "gemini-1.5-pro"]
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    payload = {"contents": [{"parts": [{"text": f"Bạn là trợ lý AI thông minh trên Telegram. Trả lời chính xác, mạch lạc.\n\nNgười dùng hỏi: {cau_hoi}"}]}]}
    last_error = "Không thể kết nối đến Gemini."
    
    for model in models:
        api_version = "v1beta" if "2.0" in model or "latest" in model else "v1"
        url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent"
        
        for attempt in range(2):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=50)
                res_json = response.json()
                if response.status_code == 200:
                    try:
                        text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                        return True, sua_loi_mojibake(text)
                    except:
                        last_error = "Gemini trả về dữ liệu không đúng định dạng."
                        continue
                else:
                    err_msg = res_json.get('error', {}).get('message', f'HTTP {response.status_code}')
                    last_error = err_msg
                    if any(x in err_msg.lower() for x in ["high demand", "temporarily", "spikes", "overloaded", "not found"]): break
                    break
            except requests.exceptions.Timeout:
                last_error = "Hết thời gian chờ (timeout)."
                if attempt == 0: time.sleep(1.5); continue
                break
            except Exception as e:
                last_error = str(e)
                break
    return False, last_error

def xu_ly_gemini_chat(chat_id, cau_hoi):
    wait_msg = gui_tin_nhan_telegram(chat_id, "🤖 <i>Đang trả lời...</i>", parse_mode="HTML")
    try:
        success, result = goi_gemini_api(cau_hoi)
        for mid in wait_msg: xoa_tin_nhan(chat_id, mid)
        if success:
            ket_qua = f"🤖 <b>Gemini AI:</b>\n\n{escape_html(result)}"
            gui_tin_nhan_telegram(chat_id, ket_qua, parse_mode="HTML")
        else:
            if any(x in result.lower() for x in ["high demand", "temporarily", "spikes", "overloaded", "timeout"]):
                result = "Model đang quá tải hoặc chậm. Vui lòng thử lại sau ít phút."
            gui_tin_nhan_telegram(chat_id, f"⚠️ <b>Lỗi Gemini:</b> {escape_html(result)}", parse_mode="HTML")
    except Exception as e:
        for mid in wait_msg: xoa_tin_nhan(chat_id, mid)
        gui_tin_nhan_telegram(chat_id, f"⚠️ <b>Lỗi hệ thống:</b> {escape_html(str(e))}", parse_mode="HTML")

# =====================================================================
# [PHẦN 5] BÁO CÁO DRIVE (THUẬT TOÁN ĐỐI CHIẾU CHÉO HOÀN TOÀN MỚI)
# =====================================================================
def trich_xuat_so_tuan(ten_thu_muc):
    match = re.search(r'(?i)tuan\s*(\d+)', ten_thu_muc)
    if match: return int(match.group(1))
    return 999

def chuan_hoa_tien_to_tuan(ten_thu_muc):
    match = re.search(r'(?i)tuan\s*(\d+)', ten_thu_muc)
    if match:
        so_tuan = match.group(1)
        return f"Tuan{so_tuan}_"
    return ""

def tao_bao_cao_powerpoint():
    if not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json'): 
        return "⚠️ Lỗi hệ thống: Không tìm thấy file <code>credentials.json</code>."
    
    msg = f"📊 <b>BÁO CÁO TIẾN ĐỘ POWERPOINT</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)

        query_main = f"'{POWERPOINT_FOLDER_ID}' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'"
        results = drive_service.files().list(q=query_main, fields="files(id, name)", pageSize=1000).execute()
        raw_folders = results.get('files', [])
        
        main_folders = sorted(raw_folders, key=lambda x: (trich_xuat_so_tuan(x['name']), x['name']))
        co_du_lieu = False

        for main_folder in main_folders:
            folder_name = main_folder['name']
            folder_id = main_folder['id']
            
            if not (folder_name.upper().startswith("TUAN") or folder_name.upper().startswith("KNTT") or "TUAN" in folder_name.upper()): 
                continue
            
            co_du_lieu = True
            msg += f"📁 <b>{escape_html(folder_name)}</b>\n"
            
            tien_to_chuan = chuan_hoa_tien_to_tuan(folder_name)

            query_sub = f"'{folder_id}' in parents and trashed=false"
            sub_results = drive_service.files().list(q=query_sub, fields="files(id, name, mimeType)", pageSize=1000).execute()
            
            all_pptx = []
            sub_folders = []

            # 1. Thu thập TẤT CẢ các file .pptx và các folder con
            for item in sub_results.get('files', []):
                if item['mimeType'] == 'application/vnd.google-apps.folder': 
                    sub_folders.append(item['id'])
                elif item['name'].lower().endswith('.pptx'):
                    all_pptx.append(item['name'])

            # 2. Quét sâu vào các folder con (Bypass hoàn toàn việc tìm tên folder gốc - hay --)
            for sub_id in sub_folders:
                query_ss = f"'{sub_id}' in parents and trashed=false"
                ss_results = drive_service.files().list(q=query_ss, fields="files(id, name, mimeType)", pageSize=1000).execute()
                for item in ss_results.get('files', []):
                    if item['mimeType'] == 'application/vnd.google-apps.folder': 
                        query_sss = f"'{item['id']}' in parents and trashed=false"
                        sss_results = drive_service.files().list(q=query_sss, fields="files(name, mimeType)", pageSize=1000).execute()
                        for item_sss in sss_results.get('files', []):
                            if item_sss['name'].lower().endswith('.pptx'):
                                all_pptx.append(item_sss['name'])
                    elif item['name'].lower().endswith('.pptx'):
                        all_pptx.append(item['name'])

            all_pptx = list(set(all_pptx))
            # Sắp xếp theo độ dài (ngắn đến dài) để dễ coi file ngắn là bản gốc
            all_pptx.sort(key=len)
            
            matched_indices = set()
            file_list = []

            # 3. THUẬT TOÁN SO KHỚP CHÉO (Tự động nhận diện bản gốc vs bản đã xử lý)
            for i in range(len(all_pptx)):
                if i in matched_indices: continue
                
                clean_i = re.sub(r'(?i)\.pptx$', '', all_pptx[i]).strip().lower()
                clean_i = re.sub(r'\s+', '', clean_i)
                
                for j in range(i+1, len(all_pptx)):
                    if j in matched_indices: continue
                    
                    clean_j = re.sub(r'(?i)\.pptx$', '', all_pptx[j]).strip().lower()
                    clean_j = re.sub(r'\s+', '', clean_j)
                    
                    if clean_i in clean_j:
                        file_list.append(f"+ {escape_html(all_pptx[j])}(hoàn thành);")
                        matched_indices.add(i)
                        matched_indices.add(j)
                        break
            
            # Những file không có cặp (Chưa hoàn thành hoặc Thừa) -> Nối tiền tố nếu thiếu
            for i in range(len(all_pptx)):
                if i not in matched_indices:
                    d_name = all_pptx[i]
                    if tien_to_chuan and not d_name.lower().startswith(tien_to_chuan.lower()):
                        d_name = tien_to_chuan + d_name
                    file_list.append(f"+ {escape_html(d_name)};")

            if not file_list:
                file_list.append("+ <i>Thư mục rỗng, chưa có file nào</i>;")
                
            file_list.sort() 
            
            block_msg = "\n".join(file_list)
            if block_msg.endswith(";"):
                block_msg = block_msg[:-1] + "."
            
            msg += block_msg + "\n\n"

        if not co_du_lieu:
            msg += "<i>Không tìm thấy thư mục nào chứa TUAN hoặc KNTT.</i>"

        return msg.strip()
                
    except Exception as e: 
        return f"⚠️ Quá trình quét Drive gặp lỗi: {escape_html(str(e))}"

# =====================================================================
# [PHẦN 6] THỜI TIẾT THÔNG MINH, ĐÔ THỊ & BÁO CHÍ 
# =====================================================================
def get_owm_icon(icon_code):
    mapping = {"01d": "☀️", "01n": "🌑", "02d": "⛅", "02n": "☁️", "03d": "☁️", "03n": "☁️", "04d": "☁️", "04n": "☁️", "09d": "🌧️", "09n": "🌧️", "10d": "🌦️", "10n": "🌧️", "11d": "⛈️", "11n": "⛈️", "13d": "❄️", "13n": "❄️", "50d": "🌫️", "50n": "🌫️"}
    return mapping.get(icon_code, "🌤️")

def xac_dinh_trang_thai_thoi_tiet(c_temp, feels_like, c_desc, n_pop, humidity):
    desc_lower = c_desc.lower()
    la_mua_hien_tai = any(x in desc_lower for x in ["mưa", "dông", "giông", "bão", "lất phất", "rào"])
    la_mua_to = la_mua_hien_tai and (any(x in desc_lower for x in ["to", "vừa", "nặng", "dông", "giông", "rào"]) or n_pop >= 80)
    sap_mua = (not la_mua_hien_tai) and (n_pop >= 60)
    la_nang_gat = c_temp >= 35 or feels_like >= 38
    
    if la_mua_to: return "RONG_BAO"
    elif la_mua_hien_tai: return "MUA_NHE"
    elif sap_mua: return "SAP_MUA"
    elif la_nang_gat: return "NANG_GAT"
    else: return "NANG_DEP"

def lay_bang_diem_ngap(ten_vung, muc_do="NHE"):
    he_so = 1.3 if muc_do == "TO" else 1.0
    ds = [
        ("Vạn Phúc", 15, 25, "Ngã tư Vạn Phúc, Tố Hữu, phố Lụa", "Trũng mép đường, cẩn thận trượt ngã."),
        ("Phúc La", 20, 40, "Khu Viện K, KĐT Xa La, Phùng Hưng", "Nước xiết, sóng nước mạnh dễ gây chết máy."),
        ("Mộ Lao", 15, 30, "Nguyễn Văn Lộc, Làng Việt Kiều", "Nước ngập nửa bánh xe, khuyến cáo đi sát tim đường."),
        ("Hà Cầu", 15, 25, "Chợ Hà Đông, Lê Lợi, Tô Hiệu", "Nước dâng nhanh cục bộ, dễ gây ùn tắc kéo dài."),
        ("Văn Quán", 25, 45, "Hồ Văn Quán, Chiến Thắng, 19/5", "Nguy cơ thủy kích, chết máy hàng loạt."),
        ("Quang Trung", 20, 40, "Ngã ba Ba La, ga La Khê, bến xe", "Ngập sâu mất vỉa hè, kẹt xe cục bộ."),
        ("La Khê", 20, 35, "Lê Trọng Tấn, Park City", "Nguy cơ sụp cống ngầm, nắp hố ga trào ngược."),
        ("Đại Mỗ", 25, 45, "Cầu Đôi, Sa Đôi, ngã ba Hữu Hưng", "Ùn tắc nghiêm trọng, ngập lút bô xe máy."),
        ("Tân Triều", 30, 50, "Triều Khúc, ngõ 66, ngõ 111", "Ngập lút bánh xe, tuyệt đối không rẽ vào ngõ nhỏ.")
    ]
    txt = f"🌊 <b>BẢNG ĐIỂM ĐEN NGẬP ÚNG ({escape_html(ten_vung)}):</b>\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    if muc_do == "NHE":
        for phuong, mn, mx, tuyen, hau_qua in ds:
            txt += f"📍 <b>{phuong}</b>\n └ ⚠️ <i>{tuyen}.</i>\n"
        txt += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        txt += "🛡️ <b>LỘ TRÌNH ĐƯỜNG TRÁNH & KHUYẾN CÁO:</b>\n"
        txt += " ├ <b>Giao thông công cộng:</b> Có thể ưu tiên tàu điện Cát Linh - Hà Đông nếu mưa kéo dài.\n"
    else:
        for phuong, mn, mx, tuyen, hau_qua in ds:
            min_v, max_v = int(mn * he_so), int(mx * he_so)
            canh_bao = "⛔ <b>CẤM XE GẦM THẤP</b>" if max_v >= 50 else ("⚠️ <b>GẦM THẤP NGUY HIỂM</b>" if max_v >= 35 else "⚠️ <b>ĐI CHẬM ĐỀU GA</b>")
            txt += f"📍 <b>{phuong}</b> | 🌊 <code>{min_v}-{max_v} cm</code> | {canh_bao}\n"
            txt += f" └ ⚠️ <i>{tuyen}. {hau_qua}</i>\n"
        txt += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        txt += "🛡️ <b>LỘ TRÌNH ĐƯỜNG TRÁNH & KHUYẾN CÁO:</b>\n"
        txt += " ├ <b>Đường tránh ngập:</b> Ưu tiên đi trục Xa La - Nguyễn Xiển, đường Vành đai 3 trên cao, hoặc bám sát tim đường trục BRT.\n"
        txt += " ├ <b>Giao thông công cộng:</b> Ưu tiên sử dụng tàu điện Cát Linh - Hà Đông để tránh kẹt xe diện rộng.\n"
        txt += " └ <b>Khuyến cáo:</b> Tuyệt đối không bám đuôi ô tô lớn qua vũng ngập để tránh sóng nước cuộn vào ống xả làm chết máy.\n"
    return txt

def lay_bang_nang_gat(ten_vung, temp):
    txt = f"☀️ <b>ĐIỂM CẦN LƯU Ý DO NẮNG GẮT ({escape_html(ten_vung)}):</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    diem = [
        ("Vạn Phúc", "Hạn chế ngoài trời", "Khu vực đường rộng, ít bóng râm có thể nóng nhanh."),
        ("Phúc La", "Bổ sung nước", "Hạn chế hoạt động ngoài trời vào thời điểm nắng mạnh."),
        ("Mộ Lao", "Che nắng", "Ưu tiên di chuyển tại khu vực có mái che."),
        ("Hà Cầu", "Hạn chế di chuyển", "Nhiệt độ mặt đường có thể cao hơn đáng kể so với nhiệt độ không khí."),
        ("Văn Quán", "Tránh nắng gắt", "Hạn chế đứng ngoài trời trong thời gian dài."),
        ("Quang Trung", "Bổ sung nước", "Khu vực đông phương tiện, nhiệt tích tụ cao."),
        ("La Khê", "Che nắng", "Nên sử dụng mũ, kính và áo chống nắng."),
        ("Đại Mỗ", "Hạn chế ngoài trời", "Tránh hoạt động ngoài trời trong thời gian nắng mạnh."),
        ("Tân Triều", "Cảnh báo nhiệt", "Ưu tiên nơi có bóng mát hoặc không gian điều hòa.")
    ]
    for ten, cb, mt in diem:
        txt += f"📍 <b>{ten}</b> | 🔥 <code>{temp}°C</code> | ⚠️ <b>{cb.upper()}</b>\n └ ⚠️ <i>{mt}</i>\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━\n🛡️ <b>LỘ TRÌNH ĐƯỜNG TRÁNH & KHUYẾN CÁO:</b>\n"
    txt += " ├ <b>Đường tránh nắng:</b> Ưu tiên các tuyến đường có nhiều cây xanh, mái che hoặc công trình có bóng mát.\n"
    txt += " ├ <b>Giao thông công cộng:</b> Có thể ưu tiên tàu điện hoặc phương tiện có điều hòa khi di chuyển vào thời điểm nắng mạnh.\n"
    txt += " └ <b>Khuyến cáo:</b> Hạn chế hoạt động ngoài trời vào khoảng <code>11:00-15:00</code>, uống đủ nước và chủ động nghỉ ngơi.\n"
    return txt

def lay_bang_nang_dep(ten_vung):
    txt = f"☀️ <b>ĐIỂM ĐIỀU KIỆN NGOÀI TRỜI ({escape_html(ten_vung)}):</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    diem = [
        ("Khu vực trung tâm", "Nắng đẹp", "THUẬN LỢI", "Tầm nhìn tốt, thời tiết phù hợp cho di chuyển."),
        ("Hà Đông", "Nắng", "THUẬN LỢI", "Đường khô ráo, khả năng mưa thấp."),
        ("Cầu Giấy", "Nắng", "THUẬN LỢI", "Điều kiện giao thông thời tiết ổn định."),
        ("Thanh Xuân", "Ít mây", "BÌNH THƯỜNG", "Nhiệt độ tăng nhẹ vào buổi trưa."),
        ("Tân Triều", "Nắng", "THUẬN LỢI", "Không ghi nhận nguy cơ ngập do mưa tại thời điểm hiện tại.")
    ]
    for ten, tt, trang_thai, mo_ta in diem:
        icon = "✅" if trang_thai == "THUẬN LỢI" else "🌤️"
        txt += f"📍 <b>{ten}</b> | ☀️ <code>{tt}</code> | {icon} <b>{trang_thai}</b>\n └ <i>{mo_ta}</i>\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━\n🛡️ <b>LỘ TRÌNH ĐƯỜNG TRÁNH & KHUYẾN CÁO:</b>\n"
    txt += " ├ <b>Đường di chuyển:</b> Có thể lựa chọn các tuyến đường thông thường, ưu tiên tuyến đường rộng và ít ùn tắc.\n"
    txt += " ├ <b>Giao thông công cộng:</b> Có thể sử dụng tàu điện, xe buýt hoặc phương tiện cá nhân bình thường.\n"
    txt += " └ <b>Khuyến cáo:</b> Nên bổ sung nước nếu di chuyển hoặc hoạt động ngoài trời trong thời gian dài.\n"
    return txt

def cap_nhat_trang_thai_thoi_tiet():
    global TRANG_THAI_THOI_TIET
    try:
        lat, lon = admin_location["lat"], admin_location["lon"]
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi"
        res = requests.get(url, timeout=10).json()
        list_data = res.get("list", [])[:8] 
        so_ca_mua = sum(1 for i in list_data if i.get('pop', 0) >= 0.5 or 'mưa' in i['weather'][0]['description'].lower())
        so_ca_nang = sum(1 for i in list_data if i['main']['temp_max'] >= 34 and i.get('pop', 0) < 0.2)
        if so_ca_mua >= 4: TRANG_THAI_THOI_TIET = "MUA_CA_NGAY"
        elif so_ca_nang >= 4: TRANG_THAI_THOI_TIET = "NANG_CA_NGAY"
        else: TRANG_THAI_THOI_TIET = "BINH_THUONG"
    except: pass

def tim_toa_do_theo_ten(ten_vung):
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={urllib.parse.quote(ten_vung)}&limit=1&appid={OPENWEATHER_API_KEY}"
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        response = res.json()
        if len(response) > 0:
            ket_qua = response[0]
            loc_name = ket_qua.get('local_names', {}).get('vi', ket_qua['name'])
            return {"thanh_cong": True, "lat": ket_qua["lat"], "lon": ket_qua["lon"], "name": f"{loc_name}, {ket_qua.get('country', '')}"}
        return {"thanh_cong": False}
    except: return {"thanh_cong": False}

def lay_thoi_tiet_hom_nay_de_ghim():
    try:
        lat, lon, ten_vi_tri = admin_location["lat"], admin_location["lon"], admin_location["name"]
        url_forecast = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi"
        res = requests.get(url_forecast, timeout=10)
        res.encoding = 'utf-8'
        res_json = res.json()
        if str(res_json.get("cod")) != "200": return f"⚠️ Lỗi máy chủ thời tiết."
        list_data = res_json.get("list", [])
        
        frames_sang, frames_chieu = [], []
        t_min_list, t_max_list, pop_list = [], [], []
        
        for item in list_data[:8]:
            dt_val = datetime.datetime.fromtimestamp(item['dt'] + 7*3600, tz=datetime.timezone.utc)
            h = dt_val.hour
            t_min_list.append(item['main']['temp_min'])
            t_max_list.append(item['main']['temp_max'])
            pop_list.append(item.get('pop', 0) * 100)
            
            line = f"<code>{dt_val.strftime('%H:%M')}</code>: <code>{round(item['main']['temp'], 1)}°C</code> | Mưa <code>{int(item.get('pop', 0)*100)}%</code> | {get_owm_icon(item['weather'][0]['icon'])} {item['weather'][0]['description'].capitalize()}"
            if 0 <= h < 13: frames_sang.append(line)
            else: frames_chieu.append(line)
                
        ht = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        
        msg = f"🌤 <b>BẢN TIN THỜI TIẾT TỔNG QUAN HÔM NAY</b> 🌤\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📍 <b>Khu vực:</b> <code>{escape_html(ten_vi_tri)}</code>\n"
        msg += f"⏱ <b>Cập nhật:</b> <code>{ht.strftime('%H:%M - %d/%m/%Y')}</code>\n\n"
        
        msg += f"📊 <b>TỔNG KẾT TRONG NGÀY</b>\n"
        msg += f" ├ Nhiệt độ: <code>{round(min(t_min_list),1)}°C</code> - <code>{round(max(t_max_list),1)}°C</code>\n"
        msg += f" ├ Khả năng mưa cao nhất: <code>{int(max(pop_list))}%</code>\n"
        msg += f" └ Trạng thái: {get_owm_icon(list_data[0]['weather'][0]['icon'])} <b>{list_data[0]['weather'][0]['description'].capitalize()}</b>\n\n"
        
        if frames_sang:
            msg += f"🌅 <b>DIỄN BIẾN BUỔI SÁNG</b>\n"
            for i, line in enumerate(frames_sang):
                prefix = " └ " if i == len(frames_sang)-1 else " ├ "
                msg += f"{prefix}{line}\n"
            msg += "\n"
            
        if frames_chieu:
            msg += f"🌇 <b>DIỄN BIẾN BUỔI CHIỀU TỐI</b>\n"
            for i, line in enumerate(frames_chieu):
                prefix = " └ " if i == len(frames_chieu)-1 else " ├ "
                msg += f"{prefix}{line}\n"

        msg += f"\n📌 <i>Bản tin tổng này tự động ghim lúc 00:00 đầu ngày.</i>"
        return msg
    except Exception as e: return f"⚠️ Lỗi dữ liệu thời tiết: {escape_html(str(e))}"

def lay_thoi_tiet_va_tin_tuc_hien_tai(include_news=True):
    try:
        lat, lon, ten_vi_tri = admin_location["lat"], admin_location["lon"], admin_location["name"]
        ten_ngan = ten_vi_tri.split(',')[0].strip()

        url_curr = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi"
        req_curr = requests.get(url_curr, timeout=10)
        req_curr.encoding = 'utf-8'
        res_curr = req_curr.json()
        c_temp = round(res_curr['main']['temp'], 1)
        feels_like = round(res_curr['main']['feels_like'], 1)
        humidity = res_curr['main']['humidity']
        c_desc = res_curr['weather'][0]['description'].capitalize()
        c_icon = get_owm_icon(res_curr['weather'][0]['icon'])

        url_fore = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi"
        req_fore = requests.get(url_fore, timeout=10)
        req_fore.encoding = 'utf-8'
        res_fore = req_fore.json()
        forecast_list = res_fore.get('list', [])
        
        n_item = forecast_list[0] if forecast_list else {}
        n_temp = round(n_item.get('main', {}).get('temp', c_temp), 1)
        n_pop = int(n_item.get('pop', 0) * 100)
        n_desc = n_item.get('weather', [{}])[0].get('description', c_desc).capitalize()

        url_aqi = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
        req_aqi = requests.get(url_aqi, timeout=5)
        res_aqi = req_aqi.json()
        aqi_level = res_aqi['list'][0]['main']['aqi']
        pm25 = res_aqi['list'][0]['components'].get('pm2_5', 0)

        trang_thai = xac_dinh_trang_thai_thoi_tiet(c_temp, feels_like, c_desc, n_pop, humidity)

        img_url = None
        img_caption = None
        tu_khoa = f"thời tiết {ten_ngan}"
        
        ht = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        msg = f"⏱ <b>THỜI TIẾT HIỆN TẠI ({ht.strftime('%H:%M')})</b>\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📍 <b>Khu vực:</b> <code>{escape_html(ten_vi_tri)}</code>\n\n"
        msg += f"🌡 <b>THÔNG SỐ HIỆN TẠI</b>\n"
        msg += f" ├ Nhiệt độ: <code>{c_temp}°C</code> (Cảm nhận: <code>{feels_like}°C</code>)\n"
        msg += f" ├ Trạng thái: {c_icon} <b>{c_desc}</b> (Độ ẩm: <code>{humidity}%</code>)\n"
        msg += f" └ Bụi mịn PM2.5: <code>{pm25} µg/m³</code> {'😷' if aqi_level >= 4 else '✅'}\n\n"
        msg += f"🔮 <b>DỰ BÁO 3 GIỜ TỚI</b>\n"
        msg += f" └ ~<code>{n_temp}°C</code> | {n_desc} | Mưa: <code>{n_pop}%</code>\n\n"

        if trang_thai == "MUA_NHE":
            msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
            msg += f" └ Mưa nhẹ đang diễn ra trên diện rộng, mặt đường có thể trơn trượt và tầm nhìn giảm. Một số khu vực trũng thấp có khả năng xuất hiện ngập cục bộ nếu mưa kéo dài.\n"
            msg += f" └ <b>Dự báo ngắn:</b> Xác suất mưa trong 3h tới vẫn ở mức <code>{n_pop}%</code>, khả năng mưa giảm dần nhưng chưa tạnh hoàn toàn.\n\n"
            msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
            msg += f" ├ <b>Điều khiển phương tiện:</b> Giảm tốc độ, giữ khoảng cách an toàn và hạn chế phanh gấp. Bật đèn chiếu gần khi tầm nhìn giảm.\n"
            msg += f" └ <b>Trang bị:</b> Mang áo mưa, bảo vệ điện thoại và các thiết bị điện tử khỏi nước.\n\n"
            msg += lay_bang_diem_ngap(ten_ngan, muc_do="NHE")
            img_url = URL_ANH_NGAP
            img_caption = "🌦️ <b>CẢNH BÁO MƯA NHẸ TỪ BÀI VIẾT</b>"
            tu_khoa = f"mưa {ten_ngan}"

        elif trang_thai == "RONG_BAO":
            msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
            msg += f" └ Mưa diện rộng & Cản trở tầm nhìn (Độ ẩm <code>{humidity}%</code>). Lượng mưa trút xuống nhanh đang gây quá tải tức thì cho hệ thống cống ngầm. Mặt đường sũng nước làm giảm tới 40% ma sát phanh. Cực kỳ cảnh giác với hố ga bị bung nắp do áp lực nước trào ngược.\n"
            msg += f" └ <b>Dự báo ngắn:</b> Xác suất mưa trong 3h tới vẫn ở mức <code>{n_pop}%</code>, chưa có dấu hiệu tạnh ráo hẳn.\n\n"
            msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
            msg += f" ├ <b>Điều khiển phương tiện:</b> Tuyệt đối không phanh gấp bằng phanh trước. Giảm tốc độ xuống dưới 30km/h khi qua vũng đọng. Bật đèn cos (đèn chiếu gần) để các xe khác dễ nhận diện trong màn mưa.\n"
            msg += f" └ <b>Trang bị:</b> Khuyến cáo dùng áo mưa bộ rời (áo mưa dơi rất dễ quất vào bánh xe hoặc che khuất gương chiếu hậu). Bọc kỹ thiết bị điện tử.\n\n"
            msg += lay_bang_diem_ngap(ten_ngan, muc_do="TO")
            img_url = URL_ANH_NGAP
            img_caption = "⛈️ <b>CẢNH BÁO RÔNG BÃO / MƯA TO TỪ BÀI VIẾT</b>"
            tu_khoa = f"ngập lụt OR mưa ngập {ten_ngan}"
            
        elif trang_thai == "SAP_MUA":
            msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
            msg += f" └ Hiện tại trời đang <b>tạnh ráo ({c_desc})</b>, nhưng mây dông đang tích tụ. Dự báo vài giờ tới có khả năng đổ mưa (Xác suất: <code>{n_pop}%</code>).\n\n"
            msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
            msg += f" └ <b>Lộ trình:</b> Trời chưa mưa nhưng cần mang sẵn áo mưa dự phòng. Ưu tiên hoàn thành sớm các việc ngoài trời trước khi mưa đổ xuống.\n\n"
            tu_khoa = f"thời tiết {ten_ngan}"

        elif trang_thai == "NANG_GAT":
            msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
            msg += f" └ 🔥 <b>Nắng nóng gay gắt:</b> Nhiệt độ cao, nhiệt độ cảm nhận tăng mạnh và chỉ số UV ở mức cao. Nguy cơ mất nước và kiệt sức do nóng tăng khi ở ngoài trời lâu.\n"
            msg += f" └ <b>Dự báo ngắn:</b> Nhiệt độ tiếp tục duy trì mức cao trong 3h tới. Hạn chế ra đường.\n\n"
            msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
            msg += f" ├ <b>Điều khiển phương tiện:</b> Hạn chế di chuyển ngoài trời vào thời điểm nắng mạnh. Nếu phải di chuyển, nên nghỉ tại nơi có bóng mát và bổ sung nước thường xuyên.\n"
            msg += f" └ <b>Trang bị:</b> Sử dụng áo chống nắng, mũ, kính râm và kem chống nắng. Không để thiết bị điện tử hoặc vật dễ cháy trong xe dưới trời nắng.\n\n"
            msg += lay_bang_nang_gat(ten_ngan, int(c_temp))
            img_url = URL_ANH_NANG
            img_caption = "🔥☀️ <b>CẢNH BÁO NẮNG GẮT TỪ BÀI VIẾT</b>"
            tu_khoa = f"nắng nóng gay gắt {ten_ngan}"

        else:
            msg += f"🚨 <b>CẢNH BÁO TRỌNG TÂM</b>\n"
            msg += f" └ ☀️ <b>Thời tiết ổn định:</b> Trời quang, ít mây, khả năng mưa thấp. Điều kiện thuận lợi cho việc di chuyển và các hoạt động ngoài trời.\n"
            msg += f" └ <b>Dự báo ngắn:</b> Chưa ghi nhận nguy cơ mưa hay biến đổi đáng kể trong 3h tới.\n\n"
            msg += f"💡 <b>GỢI Ý LỊCH TRÌNH THỰC TẾ</b>\n"
            msg += f" ├ <b>Điều khiển phương tiện:</b> Điều kiện đường sá thuận lợi. Có thể di chuyển bình thường, vẫn cần chú ý tốc độ và giao thông.\n"
            msg += f" └ <b>Trang bị:</b> Có thể mang kính râm, mũ và nước uống nếu hoạt động ngoài trời trong thời gian dài.\n\n"
            msg += lay_bang_nang_dep(ten_ngan)
            tu_khoa = f"thời tiết {ten_ngan}"

        if not include_news:
            return msg, img_url, img_caption

        msg += f"\n🌍 <b>TIN TỨC MỚI NHẤT ({escape_html(ten_ngan)}):</b>\n"
        url_news = f"https://news.google.com/rss/search?q={urllib.parse.quote(tu_khoa)}&hl=vi&gl=VN&ceid=VN:vi"
        
        try:
            res_news = requests.get(url_news, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            res_news.encoding = 'utf-8'
            items_found = False
            if res_news.status_code == 200:
                try: soup = BeautifulSoup(res_news.text, 'xml')
                except: soup = BeautifulSoup(res_news.text, 'html.parser')
                items = soup.find_all('item')
                count = 0
                chat_id_str = "broadcast_weather"
                if chat_id_str not in sent_articles_set: sent_articles_set[chat_id_str] = set()
                
                for item in items:
                    link = item.link.text.strip()
                    if link in sent_articles_set[chat_id_str]: continue
                    raw_title = item.title.text.strip() if item.title else ""
                    title = escape_html(html.unescape(raw_title))
                    
                    if img_caption and not img_url:
                        enc = item.find('enclosure')
                        if enc and 'url' in enc.attrs: img_url = enc['url']
                        else:
                            try:
                                raw_desc = item.description.text if item.description else ""
                                desc_soup = BeautifulSoup(html.unescape(raw_desc), 'html.parser')
                                img_tag = desc_soup.find('img')
                                if img_tag and 'src' in img_tag.attrs: img_url = img_tag['src']
                            except: pass

                    if count < 3:
                        msg += f" ├ <a href='{link}'>{title}</a>\n"
                        sent_articles_set[chat_id_str].add(link)
                        items_found = True
                        count += 1
                if len(sent_articles_set[chat_id_str]) > 400: sent_articles_set[chat_id_str].clear()
            if not items_found:
                msg += " └ <i>Chưa ghi nhận biến động giao thông khẩn cấp.</i>\n"
            else:
                msg = msg.rsplit(' ├ ', 1)
                msg = msg[0] + ' └ ' + msg[1] if len(msg) == 2 else msg[0]
        except:
            msg += " └ <i>Tạm thời không thể tải tin tức nóng.</i>\n"

        try:
            url_yt = "https://www.youtube.com/feeds/videos.xml?channel_id=UCabsTV34JwALXKGMqHpvUiA" 
            res_yt = requests.get(url_yt, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            res_yt.encoding = 'utf-8'
            if res_yt.status_code == 200:
                try: soup_yt = BeautifulSoup(res_yt.text, 'xml')
                except: soup_yt = BeautifulSoup(res_yt.text, 'html.parser')
                entries = soup_yt.find_all('entry')
                if entries:
                    kws = ['mưa', 'lũ', 'ngập', 'bão'] if trang_thai in ["MUA_NHE", "RONG_BAO"] else ['nắng', 'hạn hán', 'nhiệt độ']
                    found_vid = False
                    for entry in entries:
                        title = html.unescape(entry.title.text if entry.title else "")
                        link = entry.find('link')['href'] if entry.find('link') and 'href' in entry.find('link').attrs else ""
                        if any(kw in title.lower() for kw in kws):
                            msg += f"\n📺 <b>VIDEO CẢNH BÁO (VTV24):</b>\n └ <a href='{link}'>{escape_html(title)}</a>\n"
                            found_vid = True
                            break
                    if not found_vid:
                        title = html.unescape(entries[0].title.text if entries[0].title else "Tin tức VTV24")
                        link = entries[0].find('link')['href'] if entries[0].find('link') and 'href' in entries[0].find('link').attrs else ""
                        if link: msg += f"\n📺 <b>TIN TỨC VIDEO (VTV24):</b>\n └ <a href='{link}'>{escape_html(title)}</a>\n"
        except: pass

        return msg, img_url, img_caption
    except Exception as e: return f"⚠️ Lỗi dữ liệu: {escape_html(str(e))}", None, None

def lay_video_thoi_su_youtube(kieu_thoi_tiet=""):
    return ""

def lay_tat_ca_bai_viet_ngau_nhien():
    danh_sach_tong = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    nguon_rss_hien_tai = [val for key, val in DANH_SACH_TRANG.items()]
        
    if TRANG_THAI_THOI_TIET == "MUA_CA_NGAY":
        nguon_rss_hien_tai.append({"ten": "⚠️ CẢNH BÁO MƯA LŨ", "muc": ["https://news.google.com/rss/search?q=ngập+lụt+OR+mưa+lớn+OR+lũ+quét&hl=vi&gl=VN&ceid=VN:vi"]})
    elif TRANG_THAI_THOI_TIET == "NANG_CA_NGAY":
        nguon_rss_hien_tai.append({"ten": "⚠️ CẢNH BÁO NẮNG NÓNG", "muc": ["https://news.google.com/rss/search?q=hạn+hán+OR+nắng+nóng+gay+gắt&hl=vi&gl=VN&ceid=VN:vi"]})
        
    nguon_rss_hien_tai.append({"ten": "🌐 Tin Nổi Bật", "muc": ["https://news.google.com/rss?hl=vi&gl=VN&ceid=VN:vi"]})
    
    for t_info in nguon_rss_hien_tai:
        for url in t_info["muc"]:
            try:
                res = requests.get(url, headers=headers, timeout=10)
                res.encoding = 'utf-8'
                if res.status_code != 200: continue
                try: soup = BeautifulSoup(res.text, 'xml')
                except: soup = BeautifulSoup(res.text, 'html.parser')
                    
                items = soup.find_all('item')
                for item in items[:5]: 
                    raw_title = item.title.text.strip() if item.title else "News"
                    title = html.unescape(raw_title)
                    raw_desc = item.description.text.strip() if item.description else ""
                    desc = html.unescape(raw_desc)
                    link = item.link.text.strip() if item.link else ""
                    img_url = None
                    enc = item.find('enclosure')
                    if enc and 'url' in enc.attrs: img_url = enc['url']
                    else:
                        try:
                            img_tag = BeautifulSoup(desc, 'html.parser').find('img')
                            if img_tag and 'src' in img_tag.attrs: img_url = img_tag['src']
                        except: pass
                    try: c_desc = BeautifulSoup(desc, 'html.parser').get_text().strip()
                    except: c_desc = desc
                    c_desc = html.unescape(c_desc)
                    if len(c_desc) > 240: c_desc = c_desc[:240] + "..."
                    if link: danh_sach_tong.append({"title": title, "description": c_desc, "link": link, "image": img_url, "author": t_info["ten"], "source": t_info["ten"]})
            except: continue
    random.shuffle(danh_sach_tong)
    return danh_sach_tong

def lay_bai_viet_5_trang_khac_nhau(chat_id_str=None, so_luong=5):
    tat_ca_tin = lay_tat_ca_bai_viet_ngau_nhien()
    if not tat_ca_tin: return []

    chua_gui = tat_ca_tin
    if chat_id_str:
        if chat_id_str not in sent_articles_set:
            sent_articles_set[chat_id_str] = set()
        chua_gui = [b for b in tat_ca_tin if b['link'] not in sent_articles_set[chat_id_str]]
        if len(chua_gui) < so_luong:
            sent_articles_set[chat_id_str].clear()
            chua_gui = tat_ca_tin

    # Chọn 5 bài từ 5 trang báo khác nhau
    selected = []
    seen_sources = set()
    for bai in chua_gui:
        src = bai.get("source", "")
        if src not in seen_sources:
            selected.append(bai)
            seen_sources.add(src)
            if chat_id_str:
                sent_articles_set[chat_id_str].add(bai['link'])
            if len(selected) >= so_luong:
                break

    # Nếu số trang khác nhau chưa đủ, lấy thêm từ các bài còn lại
    if len(selected) < so_luong:
        for bai in chua_gui:
            if bai not in selected:
                selected.append(bai)
                if chat_id_str:
                    sent_articles_set[chat_id_str].add(bai['link'])
                if len(selected) >= so_luong:
                    break

    if chat_id_str:
        save_data()
    return selected

def lay_bai_viet_moi_chua_gui(chat_id_str, so_luong=5):
    return lay_bai_viet_5_trang_khac_nhau(chat_id_str, so_luong)

# =====================================================================
# [PHẦN 7] SCHEDULER CHẠY NGẦM THÔNG MINH & GOOGLE DOCS NEWS
# =====================================================================
def job_cap_nhat_docs_tin_tuc():
    if not GOOGLE_API_AVAILABLE or not os.path.exists('credentials.json') or DOC_NEWS_ID == "NHẬP_ID_FILE_DOCS_TIN_TỨC_VÀO_ĐÂY":
        return
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
        docs_service = build('docs', 'v1', credentials=creds)

        ht = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        ngay_thang = ht.strftime('%d/%m/%Y')
        
        noi_dung = f"📅 BẢN TIN TỔNG HỢP ANX NGÀY {ngay_thang}\n"
        noi_dung += f"⏱ Cập nhật lúc: 00:01\n"
        noi_dung += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
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

        doc = docs_service.documents().get(documentId=DOC_NEWS_ID).execute()
        content = doc.get('body').get('content')
        end_index = content[-1]['endIndex'] - 1

        requests_payload = []
        if end_index > 1:
            requests_payload.append({
                'deleteContentRange': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': end_index
                    }
                }
            })
        
        requests_payload.append({
            'insertText': {
                'location': {
                    'index': 1
                },
                'text': noi_dung
            }
        })

        docs_service.documents().batchUpdate(documentId=DOC_NEWS_ID, body={'requests': requests_payload}).execute()
    except Exception: pass

def job_tu_dong_day_tin():
    try:
        ht_time = time.time()
        with json_lock: chats_to_send = list(active_auto_news_chats)
        
        valid_chats = [c for c in chats_to_send if ht_time - user_last_news_sent.get(str(c), 0) >= 3500]
        if not valid_chats: return

        for chat_id in valid_chats:
            chat_str = str(chat_id)
            ds_bai = lay_bai_viet_5_trang_khac_nhau(chat_str, so_luong=5)
            if not ds_bai: continue

            gui_tin_nhan_telegram(chat_id, "🌟 <b>BẢN TIN ĐỊNH KỲ 1 GIỜ (5 BÁO NÓNG NHẤT)</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n🌐 <i>Hệ thống tự động tổng hợp tin tức nóng nhất 1 giờ qua.</i>", parse_mode="HTML", disable_noti=True)
            for bai in ds_bai:
                caption = f"📌 <b>{escape_html(bai['title'])}</b>\n\n📝 <i>{escape_html(bai['description'])}</i>\n\n📰 Nguồn: <code>{escape_html(bai['source'])}</code>\n🔗 <a href='{bai['link']}'>[Đọc bài viết đầy đủ tại đây]</a>"
                if bai['image']: gui_anh_telegram(chat_id, bai['image'], caption)
                else: gui_tin_nhan_telegram(chat_id, caption, parse_mode="HTML", disable_noti=True)
            user_last_news_sent[chat_str] = time.time()
        save_data()
    except: pass

def job_thoi_tiet_hang_gio():
    try:
        ht = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        hour = ht.hour
        cap_nhat_trang_thai_thoi_tiet()

        with json_lock: chats = list(active_auto_news_chats)
        for chat_id in chats:
            chat_str = str(chat_id)
            if hour == 0:
                noi_dung = lay_thoi_tiet_hom_nay_de_ghim()
                img_url, img_caption = None, None
            else:
                noi_dung, img_url, img_caption = lay_thoi_tiet_va_tin_tuc_hien_tai(include_news=True)

            old_pin = pinned_weather_msgs.get(chat_str)
            if old_pin:
                try: 
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/unpinChatMessage", json={"chat_id": chat_id, "message_id": old_pin}, timeout=5)
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage", json={"chat_id": chat_id, "message_id": old_pin}, timeout=5)
                except: pass

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": noi_dung, "parse_mode": "HTML", "disable_web_page_preview": True, "disable_notification": True}
            try: 
                res = requests.post(url, json=payload, timeout=5)
                if res.status_code == 200:
                    new_msg_id = res.json()['result']['message_id']
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/pinChatMessage", json={"chat_id": chat_id, "message_id": new_msg_id, "disable_notification": True}, timeout=5)
                    pinned_weather_msgs[chat_str] = new_msg_id
            except: pass
            
            if img_url:
                gui_anh_telegram(chat_id, img_url, img_caption)
        save_data()
    except Exception as e: pass

scheduler = BackgroundScheduler()
scheduler.add_job(func=job_tu_dong_day_tin, trigger="cron", minute=0)
scheduler.add_job(func=job_thoi_tiet_hang_gio, trigger="cron", minute=0) 
scheduler.add_job(func=job_cap_nhat_docs_tin_tuc, trigger="cron", hour=0, minute=1) 
scheduler.start()

# =====================================================================
# [PHẦN 8] KHỐI TƯƠNG TÁC (WEBHOOK & API)
# =====================================================================
@app.route('/api/daily-news', methods=['GET'])
def api_daily_news():
    try:
        lat, lon, ten_vi_tri = admin_location["lat"], admin_location["lon"], admin_location["name"]
        url_curr = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi"
        res_curr = requests.get(url_curr, timeout=10).json()
        c_temp = round(res_curr['main']['temp'], 1)
        feels_like = round(res_curr['main']['feels_like'], 1)
        humidity = res_curr['main']['humidity']
        c_desc = res_curr['weather'][0]['description'].capitalize()
        c_icon = get_owm_icon(res_curr['weather'][0]['icon'])

        url_fore = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi"
        res_fore = requests.get(url_fore, timeout=10).json()
        forecast_list = res_fore.get('list', [])
        
        n_item = forecast_list[0] if forecast_list else {}
        n_temp = round(n_item.get('main', {}).get('temp', c_temp), 1)
        n_pop = int(n_item.get('pop', 0) * 100)
        n_desc = n_item.get('weather', [{}])[0].get('description', c_desc).capitalize()

        url_aqi = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
        res_aqi = requests.get(url_aqi, timeout=5).json()
        aqi_level = res_aqi['list'][0]['main']['aqi']
        pm25 = res_aqi['list'][0]['components'].get('pm2_5', 0)

        trang_thai = xac_dinh_trang_thai_thoi_tiet(c_temp, feels_like, c_desc, n_pop, humidity)

        tin_tuc = lay_tat_ca_bai_viet_ngau_nhien()[:15]
        
        data_response = {
            "timestamp": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime('%H:%M %d/%m/%Y'),
            "location": ten_vi_tri,
            "weather": {
                "current": {
                    "temp": c_temp,
                    "feels_like": feels_like,
                    "humidity": humidity,
                    "desc": c_desc,
                    "icon": c_icon,
                    "pm25": pm25,
                    "aqi_level": aqi_level
                },
                "forecast_3h": {
                    "temp": n_temp,
                    "pop": n_pop,
                    "desc": n_desc
                },
                "status": trang_thai
            },
            "news": tin_tuc
        }
        
        response = jsonify(data_response)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def thread_xu_ly_tin_tuc(chat_id, user_id, username):
    try:
        wait_msg = gui_tin_nhan_telegram(chat_id, "⏳ <i>Đang tổng hợp 5 bài báo nóng nhất từ các trang khác nhau...</i>", parse_mode="HTML")
        ds_bai = lay_bai_viet_5_trang_khac_nhau(str(chat_id), so_luong=5)
        for w_id in wait_msg: xoa_tin_nhan(chat_id, w_id)
        if not ds_bai:
            m_ids = gui_tin_nhan_telegram(chat_id, "⚠️ Không thể lấy dữ liệu tin tức lúc này. Vui lòng thử lại sau.", parse_mode="HTML")
            xoa_tin_nhan_sau_delay(chat_id, m_ids, 10)
            return
        
        threading.Thread(target=job_cap_nhat_docs_tin_tuc).start()
        
        gui_tin_nhan_telegram(chat_id, "📰 <b>BẢN TIN TIÊU ĐIỂM (5 BÁO NÓNG NHẤT)</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n🌐 <i>Tổng hợp tin thời sự, đời sống & chính trị nổi bật:</i>", parse_mode="HTML")
        for bai in ds_bai:
            caption = f"📌 <b>{escape_html(bai['title'])}</b>\n\n📝 <i>{escape_html(bai['description'])}</i>\n\n📰 Nguồn: <code>{escape_html(bai['source'])}</code>\n🔗 <a href='{bai['link']}'>👉 Đọc tại đây</a>"
            if bai.get('image'): gui_anh_telegram(chat_id, bai['image'], caption)
            else: gui_tin_nhan_telegram(chat_id, caption, parse_mode="HTML")
    except Exception: traceback.print_exc()

def lay_ma_shopee_moi_nhat():
    ngay = datetime.date.today().strftime('%d/%m/%Y')
    return f"<b>🛍️ KHO MÃ SHOPEE HÔM NAY</b>\n━━━━━━━━━━━━━━━━━━━━━\n📅 Cập nhật: <code>{ngay}</code>\n\n• 🎟️ <a href='https://shopee.vn/m/ma-giam-gia'>Kho Tổng Hợp Mã Giảm Giá</a>\n• ⚡ <a href='https://shopee.vn/m/voucher-hot'>Săn Voucher Khung Giờ Hot</a>\n• 🚚 <a href='https://shopee.vn/m/mien-phi-van-chuyen'>Nhận Mã Freeship 0Đ</a>"

def lay_ma_shopeefood_moi_nhat():
    ngay = datetime.date.today().strftime('%d/%m/%Y')
    return f"<b>🍕 DEAL SHOPEEFOOD</b>\n━━━━━━━━━━━━━━━━━━━━━\n📅 Cập nhật: <code>{ngay}</code>\n\n• 🍔 <a href='https://shopeefood.vn/'>Trang Chủ Săn Deal</a>\n• 🎟️ <a href='https://shopee.vn/m/shopeefood'>Kho Voucher Độc Quyền</a>"

def xu_ly_telegram_update(data):
    try:
        if not data: return

        chat_id, user_id, username, text, message_id = None, "", "", "", None

        if "message" in data:
            msg = data["message"]
            chat_id = str(msg.get("chat", {}).get("id", ""))
            message_id = msg.get("message_id")
            user_id = str(msg.get("from", {}).get("id", ""))
            username = msg.get("from", {}).get("username", "").lower()
            text = msg.get("text", "").strip()
            
            if chat_id and message_id:
                add_user_msg_to_queue(chat_id, message_id)
                
        elif "callback_query" in data:
            cb = data["callback_query"]
            chat_id = str(cb["message"]["chat"]["id"])
            user_id = str(cb.get("from", {}).get("id", ""))
            username = cb.get("from", {}).get("username", "").lower()
            text = cb["data"] 
            try:
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": cb.get("id")}, timeout=5)
            except: pass

        if not chat_id: return
        active_auto_news_chats.add(chat_id)
        save_data()
        
        cmd = text.split('@')[0].strip() if text else ""

        if cmd.startswith("/startgemini") or cmd.startswith("/geminichat") or cmd == "menu_startgemini":
            cau_hoi = text.replace("/startgemini", "").replace("/geminichat", "").replace(f"@{AUTHORIZED_USERNAME}", "").strip() if text else ""
            if cmd == "menu_startgemini": cau_hoi = ""
            ai_chat_sessions.add(str(chat_id))
            gui_tin_nhan_telegram(chat_id, "🟢 <b>PHIÊN AI ĐÃ MỞ:</b> Chế độ tự động xóa tin nhắn tạm thời bị tắt. Bạn có thể chat thoải mái.\nGõ <code>/endgemini</code> để thoát.", parse_mode="HTML")
            if cau_hoi: threading.Thread(target=xu_ly_gemini_chat, args=(chat_id, cau_hoi)).start()
            return
            
        if cmd.startswith("/endgemini") or cmd == "menu_endgemini":
            if str(chat_id) in ai_chat_sessions:
                ai_chat_sessions.remove(str(chat_id))
                gui_tin_nhan_telegram(chat_id, "🔴 <b>PHIÊN AI KẾT THÚC:</b> Chế độ tự dọn rác nhóm sau 30s đã kích hoạt lại.", parse_mode="HTML")
            return
            
        if str(chat_id) in ai_chat_sessions and not cmd.startswith("/"):
            threading.Thread(target=xu_ly_gemini_chat, args=(chat_id, text)).start()
            return

        if cmd.startswith("/logicondinh"):
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                gui_tin_nhan_telegram(chat_id, "⚠️ <i>Lệnh này chỉ dành cho Quản trị viên (Admin).</i>", parse_mode="HTML")
                return
            noi_dung_logic = text.replace("/logicondinh", "").strip()
            if not noi_dung_logic: return
            wait_msg_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Đang lưu logic mới...</i>", parse_mode="HTML")
            def xu_ly_ghi_docs():
                thanh_cong = ghi_logic_moi_vao_docs(noi_dung_logic)
                for w_id in wait_msg_ids: xoa_tin_nhan(chat_id, w_id)
                if thanh_cong:
                    m_ids = gui_tin_nhan_telegram(chat_id, "✅ <b>Cập nhật bộ nhớ thành công!</b>", parse_mode="HTML")
                else:
                    m_ids = gui_tin_nhan_telegram(chat_id, "❌ <b>Ghi nhớ thất bại!</b>", parse_mode="HTML")
                xoa_tin_nhan_sau_delay(chat_id, m_ids, 10)
            threading.Thread(target=xu_ly_ghi_docs).start()
            return

        if cmd in ["/tintuc", "menu_docbao", "Báo trong ngày"]:
            threading.Thread(target=thread_xu_ly_tin_tuc, args=(chat_id, user_id, username)).start()
            return

        if cmd in ["/thoitiethientai", "Thời tiết hiện tại", "menu_thoitiet"]:
            def xu_ly_tt_hientai_rieng():
                noi_dung, img_url, img_caption = lay_thoi_tiet_va_tin_tuc_hien_tai(include_news=True)
                
                chat_str = str(chat_id)
                old_pin = pinned_weather_msgs.get(chat_str)
                if old_pin:
                    try: 
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/unpinChatMessage", json={"chat_id": chat_id, "message_id": old_pin}, timeout=5)
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage", json={"chat_id": chat_id, "message_id": old_pin}, timeout=5)
                    except: pass
                
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = {"chat_id": chat_id, "text": noi_dung, "parse_mode": "HTML", "disable_web_page_preview": True}
                try: 
                    res = requests.post(url, json=payload, timeout=5)
                    if res.status_code == 200:
                        new_msg_id = res.json()['result']['message_id']
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/pinChatMessage", json={"chat_id": chat_id, "message_id": new_msg_id, "disable_notification": True}, timeout=5)
                        pinned_weather_msgs[chat_str] = new_msg_id
                        save_data()
                except: pass

                if img_url: gui_anh_telegram(chat_id, img_url, img_caption)

            threading.Thread(target=xu_ly_tt_hientai_rieng).start()
            return

        if cmd.startswith("/thoitiet"):
            dia_diem = text.replace("/thoitiet", "").strip()
            if not dia_diem:
                def xu_ly_tt_nhanh():
                    noi_dung, img_url, img_caption = lay_thoi_tiet_va_tin_tuc_hien_tai(include_news=False)
                    gui_tin_nhan_telegram(chat_id, noi_dung, parse_mode="HTML")
                    if img_url: gui_anh_telegram(chat_id, img_url, img_caption)
                threading.Thread(target=xu_ly_tt_nhanh).start()
                return
            else:
                def xu_ly_tt_theo_vung():
                    ket_qua = tim_toa_do_theo_ten(dia_diem)
                    if not ket_qua.get("thanh_cong"):
                        gui_tin_nhan_telegram(chat_id, f"⚠️ Không tìm thấy tọa độ cho địa điểm: <b>{escape_html(dia_diem)}</b>", parse_mode="HTML")
                        return
                    lat, lon, ten_vung = ket_qua["lat"], ket_qua["lon"], ket_qua["name"]
                    try:
                        url_curr = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi"
                        res_curr = requests.get(url_curr, timeout=10).json()
                        temp = round(res_curr['main']['temp'], 1)
                        feels = round(res_curr['main']['feels_like'], 1)
                        hum = res_curr['main']['humidity']
                        desc = res_curr['weather'][0]['description'].capitalize()
                        icon = get_owm_icon(res_curr['weather'][0]['icon'])
                        msg = (
                            f"🌤️ <b>THỜI TIẾT TẠI {escape_html(ten_vung.upper())}</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━\n"
                            f"🌡️ Nhiệt độ: <code>{temp}°C</code> (Cảm nhận: <code>{feels}°C</code>)\n"
                            f"💧 Độ ẩm: <code>{hum}%</code>\n"
                            f"Trạng thái: {icon} <b>{desc}</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━\n"
                            f"<i>Gõ <code>/vung {escape_html(dia_diem)}</code> để đặt làm khu vực mặc định.</i>"
                        )
                        gui_tin_nhan_telegram(chat_id, msg, parse_mode="HTML")
                    except Exception as e:
                        gui_tin_nhan_telegram(chat_id, f"⚠️ Lỗi tra cứu thời tiết: {escape_html(str(e))}", parse_mode="HTML")
                threading.Thread(target=xu_ly_tt_theo_vung).start()
                return

        if cmd in ["/baocao", "menu_baocao"]:
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                gui_tin_nhan_telegram(chat_id, "⚠️ <i>Lệnh này chỉ dành cho Quản trị viên (Admin).</i>", parse_mode="HTML")
                return
            
            if message_id: xoa_tin_nhan(chat_id, message_id)
            if chat_id in last_report_msgs:
                for old_id in last_report_msgs[chat_id]: xoa_tin_nhan(chat_id, old_id)
                
            wait_msg_ids = gui_tin_nhan_telegram(chat_id, "⏳ <i>Đang quét hệ thống Google Drive...\n(Báo cáo tự xóa sau 2 phút)</i>", parse_mode="HTML", disable_noti=True)
            def tien_trinh_baocao_va_huy():
                try:
                    bao_cao_html = tao_bao_cao_powerpoint()
                    for w_id in wait_msg_ids: xoa_tin_nhan(chat_id, w_id)
                    new_ids = gui_tin_nhan_telegram(chat_id, bao_cao_html, parse_mode="HTML", disable_noti=True)
                    last_report_msgs[chat_id] = new_ids
                    save_data()
                    
                    time.sleep(120) 
                    for m_id in new_ids: xoa_tin_nhan(chat_id, m_id)
                    last_report_msgs[chat_id] = []
                    save_data()
                except: pass
            threading.Thread(target=tien_trinh_baocao_va_huy).start()
            return

        if cmd.startswith("/vung"):
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                gui_tin_nhan_telegram(chat_id, "⚠️ <i>Lệnh này chỉ dành cho Quản trị viên (Admin).</i>", parse_mode="HTML")
                return
            if chat_id in user_sessions: user_sessions[chat_id]["step"] = None
            ten_vung = text.replace("/vung", "").strip()
            if not ten_vung: return
            ket_qua = tim_toa_do_theo_ten(ten_vung)
            if ket_qua.get("thanh_cong"):
                admin_location["lat"] = ket_qua["lat"]
                admin_location["lon"] = ket_qua["lon"]
                admin_location["name"] = ket_qua["name"]
                save_data()
                m_ids = gui_tin_nhan_telegram(chat_id, f"✅ Đã chuyển vùng mặc định: <b>{escape_html(ket_qua['name'])}</b>", parse_mode="HTML")
                xoa_tin_nhan_sau_delay(chat_id, m_ids, 10)
            return

        if cmd in ["/start", "/menu", "Menu", "/help"]:
            keyboard = [
                [{"text": "⚡ Tính Điện Nước", "callback_data": "menu_tinhtien"}, {"text": "📊 Báo Cáo PPT", "callback_data": "menu_baocao"}],
                [{"text": "📰 Bản Tin 5 Báo", "callback_data": "menu_docbao"}, {"text": "⛅ Thời Tiết Hiện Tại", "callback_data": "menu_thoitiet"}],
                [{"text": "🌐 Website Cá Nhân", "callback_data": "menu_websitecn"}, {"text": "🤖 AI Gemini", "callback_data": "menu_startgemini"}]
            ]
            is_admin = kiem_tra_quyen_admin(chat_id, user_id, username)
            quyen = "Quản trị viên (Admin)" if is_admin else "Người dùng"
            txt_menu = (
                f"<b>🤖 HỆ THỐNG ANX - QUẢN LÝ TIỀN PHÒNG & THÔNG TIN</b>\n"
                f"👤 Quyền truy cập: <b>{quyen}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>Danh sách các lệnh hỗ trợ:</b>\n"
                f"• <code>/tinh</code> : Nhập số điện nước & tính hóa đơn tiền phòng\n"
                f"• <code>/baocao</code> : Báo cáo tiến độ PowerPoint tự động\n"
                f"• <code>/tintuc</code> : Bản tin tổng hợp 5 báo nóng nhất (1h/lần)\n"
                f"• <code>/thoitiethientai</code> : Thời tiết & cảnh báo giao thông chi tiết\n"
                f"• <code>/thoitiet [địa điểm]</code> : Tra cứu thời tiết theo vùng\n"
                f"• <code>/websitecn</code> : Cổng thông tin Website Cá Nhân\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<i>Vui lòng chọn nút bấm bên dưới hoặc gõ lệnh trực tiếp:</i>"
            )
            gui_tin_nhan_telegram(chat_id, txt_menu, {"inline_keyboard": keyboard}, parse_mode="HTML")
            return

        if cmd in ["/tinh", "Tính số điện nước AnX", "menu_tinhtien"]:
            if chat_id not in user_sessions: user_sessions[chat_id] = {"step": None, "data": {}}
            user_sessions[chat_id]["step"] = "nhap_dien_cu"
            user_sessions[chat_id]["data"] = {}
            msg = (
                "<b>⚡ QUẢN LÝ TÍNH TIỀN PHÒNG & ĐIỆN NƯỚC</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "👉 Bước 1/5: Vui lòng nhập <b>Số điện cũ</b> (đầu tháng):"
            )
            gui_tin_nhan_telegram(chat_id, msg, parse_mode="HTML")
            return

        if cmd in ["/websitecn", "menu_websitecn"]:
            msg = (
                "<b>🌐 WEBSITE CÁ NHÂN (INFORMATION & NEWS DASHBOARD)</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 <b>Trạng thái:</b> <i>Đang phát triển (In Development)</i> ⏳\n"
                "🎨 <b>Giao diện:</b> Modern Dark Navy Theme (Responsive Desktop & Mobile)\n"
                "🔗 <b>API Kết nối:</b> Endpoint <code>/api/daily-news</code>\n"
                "✨ <b>Tính năng chính dự kiến:</b>\n"
                " • Dashboard theo dõi thời tiết thực tế & cảnh báo ngập/nắng\n"
                " • Tích hợp luồng tin tức tổng hợp tự động từ 10+ đầu báo\n"
                " • Xem lịch trình, video thời sự VTV24 trực tiếp\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 <i>Giao diện web đang được hoàn thiện và sẽ sớm cập nhật trong thời gian tới!</i>"
            )
            gui_tin_nhan_telegram(chat_id, msg, parse_mode="HTML")
            return

        if cmd in ["/shoppe", "/shopee", "Mã Shopee", "menu_shopee"]:
            gui_tin_nhan_telegram(chat_id, lay_ma_shopee_moi_nhat(), parse_mode="HTML")
            return
            
        if cmd in ["/shopeefd", "Mã ShopeeFood", "menu_shopeefd"]:
            gui_tin_nhan_telegram(chat_id, lay_ma_shopeefood_moi_nhat(), parse_mode="HTML")
            return

        if cmd == ".sonuocngay":
            if not kiem_tra_quyen_admin(chat_id, user_id, username):
                gui_tin_nhan_telegram(chat_id, "⚠️ <i>Lệnh này chỉ dành cho Quản trị viên (Admin).</i>", parse_mode="HTML")
                return
            if chat_id not in user_sessions: user_sessions[chat_id] = {"step": None, "data": {}}
            user_sessions[chat_id]["step"] = "nhap_nuoc_thuc_te_hang_ngay"
            gui_tin_nhan_telegram(chat_id, "<b>💧 BÁO CÁO NƯỚC NGÀY</b>\n━━━━━━━━━━━━━━━━━━━━━\nNhập số khối nước tiêu thụ thực tế trong ngày:", parse_mode="HTML")
            return

        # Xử lý các bước nhập liệu tương tác (Session Workflow)
        if chat_id in user_sessions and user_sessions[chat_id].get("step"):
            step = user_sessions[chat_id]["step"]
            
            if step == "nhap_nuoc_thuc_te_hang_ngay":
                try:
                    sn = float(text)
                    if sn <= 0: return
                    user_sessions[chat_id]["step"] = None
                    s_khoa = tracking_data.get(str(chat_id), 0)
                    if s_khoa > 0:
                        so_ngay = math.ceil(s_khoa / sn)
                        nk = datetime.date.today() + datetime.timedelta(days=so_ngay)
                        gui_tin_nhan_telegram(chat_id, f"<b>📅 LỊCH CHỐT NƯỚC:</b> <code>{nk.strftime('%d/%m/%Y')}</code>", parse_mode="HTML")
                except: pass
                return
                
            elif step == "nhap_dien_cu":
                try:
                    val = int(text)
                    user_sessions[chat_id]["data"]["dien_cu"] = val
                    user_sessions[chat_id]["step"] = "nhap_dien_moi"
                    gui_tin_nhan_telegram(chat_id, f"⚡ Số điện cũ: <code>{val}</code>\n👉 Bước 2/5: Vui lòng nhập <b>Số điện mới</b>:", parse_mode="HTML")
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
                    gui_tin_nhan_telegram(chat_id, f"⚡ Số điện mới: <code>{val}</code>\n👉 Bước 3/5: Vui lòng nhập <b>Số nước cũ</b> (đầu tháng):", parse_mode="HTML")
                except:
                    gui_tin_nhan_telegram(chat_id, "⚠️ Số điện phải là số nguyên. Vui lòng nhập lại:", parse_mode="HTML")
                return

            elif step == "nhap_nuoc_cu":
                try:
                    val = int(text)
                    user_sessions[chat_id]["data"]["nuoc_cu"] = val
                    user_sessions[chat_id]["step"] = "nhap_nuoc_moi"
                    gui_tin_nhan_telegram(chat_id, f"💧 Số nước cũ: <code>{val}</code>\n👉 Bước 4/5: Vui lòng nhập <b>Số nước mới</b>:", parse_mode="HTML")
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
                    gui_tin_nhan_telegram(chat_id, f"💧 Số nước mới: <code>{val}</code>\n👉 Bước 5/5: Vui lòng nhập <b>Số khóa</b> (VD: 8):", parse_mode="HTML")
                except:
                    gui_tin_nhan_telegram(chat_id, "⚠️ Số nước phải là số nguyên. Vui lòng nhập lại:", parse_mode="HTML")
                return

            elif step == "nhap_so_khoa":
                try:
                    s_khoa = int(text)
                    user_sessions[chat_id]["step"] = None
                    d = user_sessions[chat_id]["data"]
                    so_dien = d["dien_moi"] - d["dien_cu"]
                    so_nuoc = d["nuoc_moi"] - d["nuoc_cu"]
                    tien_dien = so_dien * GIA_DIEN
                    tien_nuoc = so_nuoc * GIA_NUOC
                    phu_phi = A3 + A4 + A5
                    tong_tien = AN + tien_dien + tien_nuoc + phu_phi
                    tracking_data[str(chat_id)] = s_khoa
                    ht = datetime.date.today()
                    msg = (
                        f"<b>🏠 HÓA ĐƠN TIỀN NHÀ ({ht.strftime('%d/%m/%Y')})</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                        f"• Tiền nhà cố định (AN): <code>{AN:,} VNĐ</code>\n"
                        f"• Số điện: <code>{d['dien_cu']} ➔ {d['dien_moi']}</code> ({so_dien} kWh x {GIA_DIEN:,}đ) = <code>{tien_dien:,} VNĐ</code>\n"
                        f"• Số nước: <code>{d['nuoc_cu']} ➔ {d['nuoc_moi']}</code> ({so_nuoc} m³ x {GIA_NUOC:,}đ) = <code>{tien_nuoc:,} VNĐ</code>\n"
                        f"• Phí tiện ích & dịch vụ: <code>{phu_phi:,} VNĐ</code>\n"
                        f"• Số khóa cài đặt: <code>{s_khoa}</code>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                        f"👉 <b>TỔNG CỘNG: {tong_tien:,} VNĐ</b>"
                    )
                    gui_tin_nhan_telegram(chat_id, msg, parse_mode="HTML")
                    save_data()
                except:
                    gui_tin_nhan_telegram(chat_id, "⚠️ Vui lòng nhập số khóa hợp lệ (dạng số nguyên):", parse_mode="HTML")
                return

    except Exception:
        traceback.print_exc()

def run_telegram_polling():
    """Vòng lặp Long Polling nhận tin nhắn Telegram tự động không cần mở port hay Webhook"""
    time.sleep(2)
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook", json={"drop_pending_updates": False}, timeout=10)
    except Exception:
        pass

    offset = 0
    print(f"[Telegram Polling] Đã kích hoạt Long Polling cho Bot...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"timeout": 20, "offset": offset}
            res = requests.get(url, params=params, timeout=25)
            if res.status_code == 200:
                body = res.json()
                if body.get("ok"):
                    for update in body.get("result", []):
                        offset = max(offset, update["update_id"] + 1)
                        threading.Thread(target=xu_ly_telegram_update, args=(update,)).start()
            elif res.status_code == 401:
                print(f"[Telegram Polling Error] Bot Token trả về 401 Unauthorized ({TELEGRAM_BOT_TOKEN[:10]}...). Vui lòng cập nhật token hợp lệ từ @BotFather trong file .env!")
                time.sleep(15)
            else:
                time.sleep(3)
        except Exception:
            time.sleep(3)

@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def telegram_webhook():
    try:
        data = request.get_json()
        if data:
            threading.Thread(target=xu_ly_telegram_update, args=(data,)).start()
        return "OK", 200
    except Exception:
        return "OK", 200

@app.route('/webhook', methods=['POST'])
def telegram_generic_webhook():
    try:
        data = request.get_json()
        if data:
            threading.Thread(target=xu_ly_telegram_update, args=(data,)).start()
        return "OK", 200
    except Exception:
        return "OK", 200

@app.route('/ping')
def ping():
    return "Pong", 200

@app.route('/')
def home():
    return "Hệ thống AnX v6.48 (Toàn vẹn tính năng & Phân quyền) đang hoạt động!"

if __name__ == "__main__":
    threading.Thread(target=run_telegram_polling, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
