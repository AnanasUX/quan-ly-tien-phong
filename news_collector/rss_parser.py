"""
Module RSS Parser: Bộ phân tích RSS 2.0, RSS 1.0 và Atom feeds chuẩn hóa dữ liệu tin tức Việt Nam.
Tuân thủ Mục 2 và Mục 3.1 trong tài liệu yêu cầu kỹ thuật.
"""

import re
import html
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from news_collector.url_normalizer import clean_cdata, normalize_url

VN_TZ = timezone(timedelta(hours=7))

def parse_vietnamese_or_rfc_date(date_str: str) -> str:
    """
    Phân tích chuỗi ngày tháng từ RSS (RFC 822, RFC 2822, ISO 8601 hoặc tiếng Việt)
    và trả về chuỗi ISO 8601 chuẩn hóa (+07:00).
    """
    if not date_str:
        return datetime.now(VN_TZ).isoformat()
    
    clean_str = clean_cdata(date_str).strip()
    clean_str = re.sub(r'\s+', ' ', clean_str)

    # Thử phân tích RFC 822 / RFC 2822 (ví dụ: Sun, 18 Oct 2026 00:05:00 +0700)
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%a, %d %b %Y %H:%M:%S",
        "%d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M:%S"
    ):
        try:
            dt = datetime.strptime(clean_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=VN_TZ)
            else:
                dt = dt.astimezone(VN_TZ)
            return dt.isoformat()
        except Exception:
            continue

    # Fallback trích xuất regex ngày giờ tiếng Việt
    match = re.search(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})(?:\s+[àa]?[t]?\s*(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?', clean_str)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        hour = int(match.group(4)) if match.group(4) else 0
        minute = int(match.group(5)) if match.group(5) else 0
        second = int(match.group(6)) if match.group(6) else 0
        try:
            dt = datetime(year, month, day, hour, minute, second, tzinfo=VN_TZ)
            return dt.isoformat()
        except Exception:
            pass

    return datetime.now(VN_TZ).isoformat()

def extract_image_from_html(html_text: str) -> Optional[str]:
    """Trích xuất URL ảnh chất lượng cao từ đoạn mã HTML trong description/summary."""
    if not html_text:
        return None
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        img = soup.find('img')
        if img:
            src = (
                img.get('data-original') or
                img.get('data-src') or
                img.get('data-lazy-src') or
                img.get('src')
            )
            if src and not src.startswith('data:') and not '1x1' in src and not 'blank.gif' in src:
                return normalize_url(src.strip())
    except Exception:
        pass
    
    # Fallback regex
    match = re.search(r'<img[^>]+(?:src|data-src|data-original)=["\'](https?://[^"\']+)["\']', html_text, re.IGNORECASE)
    if match:
        return normalize_url(match.group(1))
    return None

def extract_clean_text(html_text: str) -> str:
    """Loại bỏ thẻ HTML và trả về văn bản thuần gọn gàng."""
    if not html_text:
        return ""
    text = clean_cdata(html_text)
    try:
        soup = BeautifulSoup(text, 'html.parser')
        raw = soup.get_text(separator=' ').strip()
        raw = html.unescape(raw)
        return re.sub(r'\s+', ' ', raw).strip()
    except Exception:
        raw = re.sub(r'<[^>]*>', ' ', text)
        return re.sub(r'\s+', ' ', raw).strip()

class RSSFeedParser:
    """Bộ phân tích RSS/Atom đa năng hỗ trợ mọi định dạng báo chí Việt Nam."""

    @staticmethod
    def parse_feed(xml_content: str, feed_url: str = "", source_meta: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Phân tích nội dung XML của RSS hoặc Atom và trả về danh sách bài viết chuẩn hóa.
        """
        if not xml_content or not xml_content.strip():
            return []

        source_meta = source_meta or {}
        source_name = source_meta.get("source_name", "Báo điện tử")
        category = source_meta.get("category", "thoi_su_xa_hoi")

        # Thử parse XML qua BeautifulSoup lxml-xml hoặc xml hoặc html.parser
        soup = None
        for parser in ('lxml-xml', 'xml', 'html.parser'):
            try:
                soup = BeautifulSoup(xml_content, parser)
                break
            except Exception:
                continue

        if not soup:
            return []

        articles: List[Dict[str, Any]] = []

        # 1. Định dạng RSS 2.0 / RSS 0.9x: thẻ <item>
        items = soup.find_all('item')
        is_atom = False

        # 2. Định dạng Atom 1.0: thẻ <entry>
        if not items:
            items = soup.find_all('entry')
            is_atom = True

        for item in items:
            try:
                parsed_article = RSSFeedParser._parse_single_item(item, is_atom, feed_url, source_name, category)
                if parsed_article and parsed_article.get("title") and parsed_article.get("article_url"):
                    articles.append(parsed_article)
            except Exception:
                continue

        return articles

    @staticmethod
    def _parse_single_item(item: Any, is_atom: bool, feed_url: str, source_name: str, category: str) -> Optional[Dict[str, Any]]:
        # 1. Tiêu đề
        title_el = item.find('title')
        raw_title = clean_cdata(title_el.get_text() if title_el else '')
        title = html.unescape(raw_title).strip()
        if not title:
            return None

        # 2. Link bài viết gốc
        article_url = ""
        if is_atom:
            link_el = item.find('link', rel='alternate') or item.find('link')
            if link_el:
                article_url = link_el.get('href', '') or link_el.get_text()
        else:
            link_el = item.find('link')
            if link_el:
                article_url = link_el.get_text().strip()
            if not article_url:
                guid_el = item.find('guid', isPermaLink=lambda v: v is None or str(v).lower() != 'false')
                if guid_el and (guid_el.get_text().startswith('http://') or guid_el.get_text().startswith('https://')):
                    article_url = guid_el.get_text().strip()

        article_url = normalize_url(article_url)
        if not article_url:
            return None

        # 3. GUID / ID
        guid = ""
        guid_el = item.find('id') if is_atom else item.find('guid')
        if guid_el:
            guid = clean_cdata(guid_el.get_text()).strip()
        if not guid:
            guid = article_url

        # 4. Thời gian xuất bản & cập nhật
        pub_date_raw = ""
        up_date_raw = ""
        if is_atom:
            pub_date_el = item.find('published') or item.find('issued') or item.find('updated')
            up_date_el = item.find('updated')
            pub_date_raw = pub_date_el.get_text() if pub_date_el else ""
            up_date_raw = up_date_el.get_text() if up_date_el else ""
        else:
            pub_date_el = item.find('pubDate') or item.find('dc:date') or item.find('date')
            pub_date_raw = pub_date_el.get_text() if pub_date_el else ""

        published_at = parse_vietnamese_or_rfc_date(pub_date_raw)
        updated_at = parse_vietnamese_or_rfc_date(up_date_raw) if up_date_raw else published_at

        # 5. Tác giả
        author = ""
        author_el = item.find('author') or item.find('dc:creator') or item.find('creator')
        if author_el:
            # Nếu trong thẻ <author> có <name>
            name_el = author_el.find('name') if hasattr(author_el, 'find') else None
            author = clean_cdata(name_el.get_text() if name_el else author_el.get_text()).strip()
            # Bỏ email rác nếu có
            author = re.sub(r'\(.*?\)|<.*?>', '', author).strip()

        # 6. Tóm tắt (Summary / Description) & Ảnh đại diện
        desc_el = item.find('summary') if is_atom else (item.find('description') or item.find('summary'))
        raw_desc = desc_el.get_text() if desc_el else ""
        
        # Bóc tách ảnh đại diện:
        # Thử enclosure
        image_url = None
        enclosure = item.find('enclosure', type=lambda t: t and t.startswith('image/'))
        if enclosure and enclosure.get('url'):
            image_url = normalize_url(enclosure.get('url'))

        # Thử media:content / media:thumbnail
        if not image_url:
            media_content = item.find(['media:content', 'media:thumbnail'])
            if media_content and media_content.get('url'):
                image_url = normalize_url(media_content.get('url'))

        # Thử bóc tách từ HTML của description
        if not image_url and raw_desc:
            image_url = extract_image_from_html(raw_desc)

        # Lấy tóm tắt văn bản sạch
        summary = extract_clean_text(raw_desc)

        # 7. Nội dung đầy đủ trực tiếp trong RSS/Atom nếu có (content:encoded hoặc content)
        content_direct = ""
        content_el = item.find(['content:encoded', 'content'])
        if content_el:
            raw_c = content_el.get_text().strip()
            if len(raw_c) > 200:
                content_direct = raw_c

        # 8. Thẻ phân loại Tags / Categories
        tags = []
        for cat in item.find_all('category'):
            c_text = clean_cdata(cat.get_text()).strip()
            if c_text and c_text not in tags:
                tags.append(c_text)

        # Xác định sơ bộ content_status
        content_status = "summary_only"
        if content_direct and len(extract_clean_text(content_direct)) > 300:
            content_status = "full"

        return {
            "source_name": source_name,
            "category": category,
            "feed_url": feed_url,
            "article_url": article_url,
            "title": title,
            "author": author,
            "published_at": published_at,
            "updated_at": updated_at,
            "summary": summary,
            "content": content_direct,
            "image_url": image_url or "",
            "tags": tags,
            "content_status": content_status,
            "fetched_at": datetime.now(VN_TZ).isoformat(),
            "guid": guid
        }
