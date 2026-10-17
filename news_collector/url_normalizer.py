"""
Module URL Normalizer: Chuẩn hóa URL, loại bỏ tham số tracking và tạo chữ ký nhận diện chống trùng lặp.
Tuân thủ Mục 5 - Chống trùng lặp theo yêu cầu kỹ thuật.
"""

import re
import hashlib
from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode

TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'utm_id',
    'fbclid', 'gclid', 'ref', 'from', 'gidzl', '_ga', 'spm', '_hsenc', '_hsmi',
    'mc_cid', 'mc_eid', 'campaign', 'zanpid', 'igshid', 'mibextid', 'ns_source',
    'ns_mchannel', 'ns_campaign', 'ns_linkname', 'ns_fee'
}

def clean_cdata(text: str) -> str:
    """Loại bỏ thẻ bọc CDATA của XML nếu có."""
    if not text:
        return ""
    text = str(text).strip()
    return re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL).strip()

def normalize_url(raw_url: str) -> str:
    """
    Chuẩn hóa URL:
    - Loại bỏ CDATA, khoảng trắng đầu cuối
    - Chuẩn hóa scheme (http/https) và domain chữ thường
    - Loại bỏ các tham số tracking / quảng cáo / phân tích (utm, fbclid, ref, gidzl...)
    - Giữ nguyên các tham số query quan trọng của bài viết (ví dụ id, post_id nếu có)
    - Loại bỏ hash fragment (#...)
    - Chuẩn hóa dấu gạch chéo cuối trang
    """
    if not raw_url:
        return ""
    
    url = clean_cdata(raw_url).strip()
    if not url:
        return ""
    
    # Chuẩn hóa protocol tương đối //
    if url.startswith("//"):
        url = "https:" + url
    elif not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url.lstrip("/")

    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        # Bỏ port mặc định nếu có
        if netloc.endswith(":80") and scheme == "http":
            netloc = netloc[:-3]
        elif netloc.endswith(":443") and scheme == "https":
            netloc = netloc[:-4]

        path = parsed.path or "/"
        # Chuẩn hóa nhiều dấu gạch chéo liền kề trong path
        path = re.sub(r'/+', '/', path)
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        # Lọc query parameters loại bỏ tracking
        query_items = parse_qsl(parsed.query, keep_blank_values=False)
        clean_items = []
        for k, v in query_items:
            k_lower = k.lower()
            if k_lower in TRACKING_PARAMS or k_lower.startswith("utm_"):
                continue
            clean_items.append((k, v))
        
        # Sắp xếp query params để so sánh nhất quán
        clean_items.sort(key=lambda x: x[0])
        clean_query = urlencode(clean_items)

        # Bỏ fragment (#)
        normalized = urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))
        return normalized
    except Exception:
        return url.strip()

def generate_article_hash(normalized_url: str, title: str = "", domain: str = "") -> str:
    """
    Tạo mã SHA-256 đối chiếu độc nhất cho bài viết:
    - Ưu tiên URL chuẩn hóa.
    - Kết hợp tiêu đề chuẩn hóa và domain để đối chiếu chéo khi URL có thay đổi nhỏ.
    """
    norm_url = normalize_url(normalized_url)
    clean_title = re.sub(r'\s+', ' ', (title or '').lower().strip())
    # Bỏ dấu câu cơ bản khỏi tiêu đề khi băm để đối chiếu bài viết trùng
    simplified_title = re.sub(r'[\W_]+', '', clean_title)
    
    seed = f"{norm_url}::{domain.lower().strip()}::{simplified_title}"
    return hashlib.sha256(seed.encode('utf-8')).hexdigest()

def generate_title_signature(title: str, domain: str = "") -> str:
    """Tạo chữ ký tiêu đề để phát hiện trùng lặp tiêu đề trong cùng một tờ báo."""
    clean_title = re.sub(r'[\W_]+', '', (title or '').lower().strip())
    seed = f"{domain.lower().strip()}::{clean_title}"
    return hashlib.md5(seed.encode('utf-8')).hexdigest()
