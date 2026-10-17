"""
Module Article Extractor: Trích xuất nội dung toàn văn bài viết từ URL bài viết gốc.
Tuân thủ Mục 3 (Lấy nội dung chi tiết) và Mục 4 (Chuẩn hóa dữ liệu) trong yêu cầu kỹ thuật:
- Trích xuất tiêu đề, sapo, thân bài, các đoạn văn, đề mục, ảnh minh họa, chú thích ảnh, tác giả và thời gian đăng.
- Loại bỏ menu, quảng cáo, điều hướng, footer và rác.
- Giữ nguyên dấu tiếng Việt, thứ tự đoạn văn và ngữ cảnh.
- Đánh dấu trạng thái chính xác: 'full', 'partial', 'summary_only', 'failed'.
- TUYỆT ĐỐI không tự tạo hoặc suy đoán những đoạn nội dung bị thiếu.
"""

import re
import html
import json
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from news_collector.url_normalizer import normalize_url
from news_collector.rss_parser import parse_vietnamese_or_rfc_date

DEFAULT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
}

# Các bộ chọn vùng nội dung chính của các báo điện tử Việt Nam
PRIMARY_CONTENT_SELECTORS = [
    '#maincontent', '.maincontent', '#main-content', '.main-content',
    'article.fck_detail', '.fck_detail', '[data-role="content"]', '.detail-cmain',
    '#main-detail-body', '.detail-content [data-role="content"]', '#articleContent',
    '.singular-content', '.e-magazine__body', '.the-article-body', '.knc-content',
    '.post-content', '.entry-content', '.article-content',
    '.article__body', '.zce-content-body', '.cms-body',
    '.content-detail', '.detail-content-body', '.content-body', '.post-detail',
    '.noidung', '.news-content', '.detail-content', 'article'
]

# Các bộ chọn Sapo mở đầu
SAPO_SELECTORS = [
    '.content-detail-sapo', '.singular-sapo', '.article__sapo', '.sapo',
    '.lead', 'h2.description', 'h2.sapo', '.detail-sapo', '.content-sapo',
    '.summary', '.post-summary', '[itemprop="description"]'
]

# Các selector rác cần gỡ bỏ trước khi bóc tách
UNWANTED_SELECTORS = [
    'script', 'style', 'nav', 'footer', 'header', '.ads', '.ad', '.advertisement',
    '.qc', '.banner', '.banner-ads', 'ins.adsbygoogle', '.google-auto-placed',
    '[class*="ad-"]', '[id*="ad-"]', '[class*="banner"]', '.social', '.comment',
    'iframe:not([data-keep-video="true"])', '.return-thread-body-btn',
    '.readmore-body-btn', '.box-author-detail', '.author-info', '.bread-crumb',
    '.breadcrumb', '.share', '.like-fb', '.content-detail-top', '.back-to-top',
    '[data-content-name="article-author"]', '[data-content-piece*="author"]',
    'a[rel="author"]', 'a[href*="/tac-gia/"]', '.author-avatar', '.article-author',
    '.dt-author', '.box-author', '.details__author', '.article__author',
    '[data-module="article-audio-new"]', '[data-module="article-audio"]', 'time',
    '.ck-cms-insert-neww-group', '.vnn-template-noneditable', '.box-tinlienquan',
    '.article-relate', '.detail-relate', '.insert-wiki-group', '.vnn-content-related'
]

def create_robust_session() -> requests.Session:
    """Tạo HTTP Session có retry kiểm soát và connection pooling."""
    session = requests.Session()
    retries = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=20)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

GLOBAL_SESSION = create_robust_session()

def clean_inline_boilerplate(text: str) -> bool:
    """Kiểm tra văn bản có phải boilerplate điều hướng / quảng cáo rác không."""
    if not text:
        return True
    t = text.lower().strip()
    if len(t) < 3:
        return True
    if re.search(r'^(đọc tiếp|về trang chủ đề|trở lại chủ đề|chủ đề:|từ khóa:|xem thêm|tin liên quan|bài viết liên quan|nguồn:)', t):
        return True
    if re.search(r'^theo\s+(nguồn|dân trí|tiền phong|vnexpress|thanh niên|tuổi trẻ|vtv|lao động|báo)', t):
        return True
    if re.search(r'BEGIN COMPONENT|END COMPONENT|Bấm để xem|Theo dõi chúng tôi', t, re.IGNORECASE):
        return True
    return False

def extract_metadata_from_html(soup: BeautifulSoup, html_str: str, base_url: str) -> Tuple[str, str, str, str]:
    """
    Trích xuất: (title, author, published_at, sapo) từ DOM, Schema JSON-LD và dataLayer.
    """
    # 1. Tiêu đề
    title = ""
    h1_el = soup.find('h1')
    if h1_el:
        title = h1_el.get_text().strip()
    if not title:
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content', '').strip()
    if not title and soup.title:
        title = soup.title.get_text().strip()
    title = re.sub(r'\s+', ' ', title).strip()

    # 2. Sapo
    sapo = ""
    for sel in SAPO_SELECTORS:
        el = soup.select_one(sel)
        if el:
            txt = el.get_text().strip()
            if txt and len(txt) > 20:
                sapo = re.sub(r'\s+', ' ', txt).strip()
                break

    # 3. Tác giả & Thời gian xuất bản
    author = ""
    published_at = ""

    # Schema JSON-LD
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            raw_ld = script.string
            if not raw_ld:
                continue
            clean_ld = re.sub(r'[\x00-\x1f\x7f-\x9f]', lambda m: ' ' if m.group(0) in '\r\n' else '', raw_ld.strip())
            data = json.loads(clean_ld)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not author and item.get('author'):
                    auth = item['author']
                    a = auth[0] if isinstance(auth, list) else auth
                    author = a if isinstance(a, str) else a.get('name', '')
                if not published_at and item.get('datePublished'):
                    published_at = parse_vietnamese_or_rfc_date(item['datePublished'])
        except Exception:
            continue

    # dataLayer scanning (cho VietnamNet và các trang tin dùng GTM)
    if not author:
        m_auth = re.search(r"['\"]ArticleAuthor['\"]\s*:\s*['\"]([^'\"]+)['\"]", html_str)
        if m_auth:
            author = m_auth.group(1).strip()
    if not published_at:
        m_date = re.search(r"['\"]ArticlePublishDate['\"]\s*:\s*['\"]([^'\"]+)['\"]", html_str)
        if m_date:
            published_at = parse_vietnamese_or_rfc_date(m_date.group(1).strip())

    # DOM Fallback cho tác giả
    if not author:
        author_el = soup.select_one(
            '[data-content-piece*="author-position_1-name"], a[rel="author"], a[href*="/tac-gia/"], '
            '.author-name, .author_name, .details__author, .article__author, [itemprop="author"], .box-author .name, .author'
        )
        if author_el:
            author = author_el.get_text().strip()

    # DOM Fallback cho thời gian
    if not published_at:
        time_el = soup.select_one('time, [data-slot="date"], .date-time, .datetime, meta[property="article:published_time"]')
        if time_el:
            raw_t = time_el.get('content') or time_el.get_text().strip()
            published_at = parse_vietnamese_or_rfc_date(raw_t)

    return title, author, published_at, sapo

class ArticleExtractor:
    """Bộ trích xuất nội dung toàn văn trang bài viết gốc."""

    @staticmethod
    def extract_article(article_url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Truy cập URL bài viết gốc và trích xuất nội dung toàn văn:
        - Đảm bảo giữ nguyên tiếng Việt, thứ tự đoạn văn, tiêu đề phụ và ảnh minh họa.
        - Đánh dấu chính xác content_status ('full', 'partial', 'summary_only', 'failed').
        - Tuyệt đối không tự suy đoán hoặc tạo nội dung giả định.
        """
        norm_url = normalize_url(article_url)
        if not norm_url:
            return {
                "article_url": article_url,
                "content": "",
                "sapo": "",
                "title": "",
                "author": "",
                "published_at": "",
                "images": [],
                "content_status": "failed",
                "error": "URL không hợp lệ"
            }

        try:
            resp = GLOBAL_SESSION.get(norm_url, headers=DEFAULT_HEADERS, timeout=timeout)
            if resp.status_code != 200:
                return {
                    "article_url": norm_url,
                    "content": "",
                    "sapo": "",
                    "title": "",
                    "author": "",
                    "published_at": "",
                    "images": [],
                    "content_status": "failed",
                    "error": f"HTTP status code: {resp.status_code}"
                }

            # Tự động phát hiện encoding đúng của tiếng Việt (UTF-8)
            resp.encoding = resp.apparent_encoding or 'utf-8'
            html_text = resp.text

            return ArticleExtractor.parse_html_content(html_text, norm_url)

        except requests.exceptions.Timeout:
            return {
                "article_url": norm_url,
                "content": "",
                "sapo": "",
                "title": "",
                "author": "",
                "published_at": "",
                "images": [],
                "content_status": "failed",
                "error": "Quá thời gian kết nối (Timeout)"
            }
        except Exception as e:
            return {
                "article_url": norm_url,
                "content": "",
                "sapo": "",
                "title": "",
                "author": "",
                "published_at": "",
                "images": [],
                "content_status": "failed",
                "error": str(e)
            }

    @staticmethod
    def parse_html_content(html_text: str, base_url: str) -> Dict[str, Any]:
        """Phân tích HTML nội bộ để bóc tách cấu trúc bài viết chuẩn hóa."""
        if not html_text or len(html_text.strip()) < 100:
            return {
                "article_url": base_url,
                "content": "",
                "sapo": "",
                "title": "",
                "author": "",
                "published_at": "",
                "images": [],
                "content_status": "failed",
                "error": "Nội dung HTML rỗng hoặc quá ngắn"
            }

        soup = BeautifulSoup(html_text, 'html.parser')

        # 1. Trích xuất metadata trước khi pre-cleaning
        title, author, published_at, sapo = extract_metadata_from_html(soup, html_text, base_url)

        # 2. Pre-cleaning các thành phần rác
        for sel in UNWANTED_SELECTORS:
            for el in soup.select(sel):
                el.decompose()

        # 3. Tìm container nội dung chính
        main_content = None
        for sel in PRIMARY_CONTENT_SELECTORS:
            candidate = soup.select_one(sel)
            if candidate and (
                len(candidate.find_all('p')) >= 2 or
                len(candidate.find_all('img')) >= 2 or
                len(candidate.get_text().strip()) > 200
            ):
                main_content = candidate
                break

        # Fallback Heuristic dựa trên mật độ thẻ <p>
        if not main_content:
            max_p = 0
            for el in soup.find_all(['div', 'article', 'section']):
                p_count = len(el.find_all('p'))
                if p_count > max_p:
                    max_p = p_count
                    main_content = el

        if not main_content:
            main_content = soup.body

        # 4. Trích xuất tuần tự các đoạn văn, tiêu đề phụ và ảnh minh họa
        content_paragraphs: List[str] = []
        structured_images: List[Dict[str, str]] = []

        def process_element(node: Any):
            if not node or isinstance(node, str):
                return
            
            tag = node.name
            if not tag:
                return

            # Xử lý hình ảnh / figure
            if tag in ['figure', 'picture']:
                img = node.find('img')
                if img:
                    cap_el = node.find(['figcaption', 'div'])
                    cap = cap_el.get_text().strip() if cap_el else (img.get('alt') or '')
                    src = (
                        img.get('data-original') or
                        img.get('data-src') or
                        img.get('data-srcset', '').split(',')[0].strip().split(' ')[0] or
                        img.get('src')
                    )
                    if src and not src.startswith('data:') and not src.endswith('.svg') and not 'icon' in src:
                        full_img_url = urljoin(base_url, src.strip())
                        structured_images.append({"url": full_img_url, "caption": cap})
                return

            if tag == 'img':
                src = (
                    node.get('data-original') or
                    node.get('data-src') or
                    node.get('data-srcset', '').split(',')[0].strip().split(' ')[0] or
                    node.get('src')
                )
                cap = node.get('alt') or ''
                if src and not src.startswith('data:') and not src.endswith('.svg') and not 'icon' in src:
                    full_img_url = urljoin(base_url, src.strip())
                    structured_images.append({"url": full_img_url, "caption": cap})
                return

            # Xử lý đoạn văn bản, tiêu đề phụ, trích dẫn
            if tag in ['p', 'h2', 'h3', 'h4', 'blockquote']:
                # Nếu bên trong chứa ảnh thì duyệt con để bóc tách ảnh đúng thứ tự
                if node.find('img'):
                    for child in node.children:
                        process_element(child)
                else:
                    text = node.get_text().strip()
                    if text and not clean_inline_boilerplate(text):
                        # Bỏ nếu trùng tiêu đề chính hoặc sapo
                        if text == title or text == sapo:
                            return
                        # Bỏ nếu là tên tác giả đứng riêng một dòng
                        if author and text.lower() == author.lower():
                            return

                        # Đánh dấu tiêu đề phụ
                        children = [c for c in node.children if hasattr(c, 'name') and c.name]
                        is_only_strong = len(children) == 1 and children[0].name in ['strong', 'b'] and children[0].get_text().strip() == text
                        is_subheading = tag.startswith('h') or (tag == 'p' and is_only_strong and len(text) < 120 and not text.endswith('.'))

                        if is_subheading:
                            content_paragraphs.append(f"### {text}")
                        elif tag == 'blockquote':
                            content_paragraphs.append(f"> {text}")
                        else:
                            content_paragraphs.append(text)
                return

            for child in node.children:
                process_element(child)

        if main_content:
            process_element(main_content)

        # 5. Phóng sự ảnh (Photo Story): nếu ít hơn 2 đoạn văn nhưng có nhiều ảnh và chú thích
        if len(content_paragraphs) < 2 and len(structured_images) >= 2:
            for img_info in structured_images:
                if img_info.get("caption") and len(img_info["caption"]) > 25:
                    if img_info["caption"] not in content_paragraphs:
                        content_paragraphs.append(img_info["caption"])

        # 6. Ghép toàn văn nội dung bài viết
        full_text = "\n\n".join(content_paragraphs).strip()

        # 7. Đánh giá content_status chính xác theo quy chuẩn
        # - full: Bài viết có ít nhất 3 đoạn văn hoặc phóng sự ảnh hoàn chỉnh (> 400 ký tự)
        # - partial: Có 1-2 đoạn văn nhưng chưa đủ toàn văn (> 100 ký tự)
        # - summary_only: Chỉ có sapo hoặc tóm tắt, không bóc tách được thân bài
        # - failed: Không có bất kỳ nội dung nào
        if len(content_paragraphs) >= 3 or (len(structured_images) >= 2 and len(full_text) > 300):
            status = "full"
        elif len(content_paragraphs) >= 1 or len(full_text) > 100:
            status = "partial"
        elif sapo:
            status = "summary_only"
            full_text = sapo
        else:
            status = "failed"

        primary_image = structured_images[0]["url"] if structured_images else ""

        return {
            "article_url": base_url,
            "title": title,
            "author": author,
            "published_at": published_at,
            "sapo": sapo,
            "content": full_text,
            "images": structured_images,
            "primary_image": primary_image,
            "paragraph_count": len(content_paragraphs),
            "content_status": status
        }
