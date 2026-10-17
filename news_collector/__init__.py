"""
VietNews Collector Package: Hệ thống thu thập tin tức RSS và trích xuất nội dung toàn văn chuẩn hóa.
"""

from news_collector.url_normalizer import normalize_url, generate_article_hash, generate_title_signature
from news_collector.rss_parser import RSSFeedParser
from news_collector.article_extractor import ArticleExtractor
from news_collector.database import NewsDatabase
from news_collector.collector_engine import NewsCollectorEngine

__all__ = [
    "normalize_url",
    "generate_article_hash",
    "generate_title_signature",
    "RSSFeedParser",
    "ArticleExtractor",
    "NewsDatabase",
    "NewsCollectorEngine"
]
