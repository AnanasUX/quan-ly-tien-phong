"""
Module CLI: Giao diện dòng lệnh (Command Line Interface) điều khiển hệ thống thu thập tin tức.
"""

import argparse
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from news_collector.database import NewsDatabase
from news_collector.collector_engine import NewsCollectorEngine
from news_collector.web_app import start_server

def main():
    parser = argparse.ArgumentParser(
        description="VietNews: Hệ thống thu thập tin tức RSS và trích xuất nội dung toàn văn báo chí Việt Nam"
    )

    parser.add_argument("--crawl", action="store_true", help="Kích hoạt thu thập tin tức ngay")
    parser.add_argument("--category", type=str, default=None, help="Lọc chuyên mục thu thập (ví dụ: thoi_su_xa_hoi, cong_nghe_ai...)")
    parser.add_argument("--source", type=str, default=None, help="Lọc theo ID nguồn cụ thể (ví dụ: vnn_thoi_su, vne_so_hoa...)")
    parser.add_argument("--no-full-text", action="store_true", help="Chỉ thu thập RSS mà không cào toàn văn bài viết gốc")
    parser.add_argument("--workers", type=int, default=4, help="Số luồng đồng thời kiểm soát (mặc định: 4)")
    parser.add_argument("--timeout", type=int, default=10, help="Thời gian chờ tối đa cho mỗi request (giây, mặc định: 10)")
    parser.add_argument("--stats", action="store_true", help="Hiển thị thống kê dữ liệu hiện tại trong DB")
    parser.add_argument("--export-json", type=str, default=None, help="Xuất dữ liệu ra file JSON")
    parser.add_argument("--export-csv", type=str, default=None, help="Xuất dữ liệu ra file CSV")
    parser.add_argument("--export-excel", type=str, default=None, help="Xuất dữ liệu ra file Excel (.xlsx)")
    parser.add_argument("--serve", action="store_true", help="Khởi động máy chủ Web UI Dashboard")
    parser.add_argument("--port", type=int, default=5050, help="Cổng máy chủ Web Dashboard (mặc định: 5050)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host máy chủ Web (mặc định: 127.0.0.1)")
    parser.add_argument("--schedule", type=int, default=0, help="Khoảng thời gian tự động thu thập định kỳ (phút, ví dụ: 30)")

    args = parser.parse_args()

    db = NewsDatabase()
    engine = NewsCollectorEngine(db=db, max_workers=args.workers, request_timeout=args.timeout)

    if args.stats:
        stats = db.get_statistics()
        print("\n" + "="*50)
        print("          THỐNG KÊ CƠ SỞ DỮ LIỆU TIN TỨC")
        print("="*50)
        print(f"Tổng số bài viết:       {stats['total_articles']:,}")
        print(f"- Toàn văn (full):      {stats['full_count']:,}")
        print(f"- Một phần (partial):   {stats['partial_count']:,}")
        print(f"- Chỉ tóm tắt (summary):{stats['summary_only_count']:,}")
        print(f"- Lỗi/Chặn (failed):    {stats['failed_count']:,}")
        print("\nPhân loại theo chuyên mục:")
        for cat, cnt in stats.get("by_category", {}).items():
            print(f"  • {cat}: {cnt:,} bài")
        print("\nNguồn tin hàng đầu:")
        for src, cnt in stats.get("top_sources", {}).items():
            print(f"  • {src}: {cnt:,} bài")
        print("="*50 + "\n")

    if args.export_json:
        path = db.export_json(args.export_json)
        print(f"✅ Đã xuất dữ liệu JSON thành công: {path}")

    if args.export_csv:
        path = db.export_csv(args.export_csv)
        print(f"✅ Đã xuất dữ liệu CSV thành công: {path}")

    if args.export_excel:
        path = db.export_excel(args.export_excel)
        print(f"✅ Đã xuất dữ liệu Excel thành công: {path}")

    if args.crawl:
        fetch_full = not args.no_full_text
        print(f"\n🚀 Đang tiến hành thu thập tin tức (fetch_full={fetch_full}, category={args.category}, source={args.source})...")
        report = engine.run_crawl(
            category=args.category,
            source_id=args.source,
            fetch_full_content=fetch_full
        )
        print("\n" + "="*50)
        print("             BÁO CÁO KẾT QUẢ THU THẬP")
        print("="*50)
        print(f"Thời gian thực thi:      {report['duration_seconds']} giây")
        print(f"Số nguồn đã quét:        {report['total_sources_scanned']}")
        print(f"Tổng số bài tìm thấy:    {report['total_found']}")
        print(f"Bài viết mới thêm:       {report['new_inserted']}")
        print(f"Bài trùng cập nhật full: {report['duplicates_updated']}")
        print(f"Bài trùng lặp bỏ qua:    {report['duplicates_skipped']}")
        print(f"Bài lấy được toàn văn:   {report['full_count']}")
        print(f"Bài lấy được một phần:   {report['partial_count']}")
        print(f"Bài chỉ có tóm tắt:      {report['summary_only_count']}")
        print(f"Bài lỗi:                 {report['failed_count']}")
        print("="*50 + "\n")

    if args.schedule > 0:
        print(f"⏰ Chế độ tự động: Thu thập định kỳ mỗi {args.schedule} phút...")
        while True:
            try:
                time.sleep(args.schedule * 60)
                print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Kích hoạt thu thập định kỳ...")
                engine.run_crawl(category=args.category, fetch_full_content=not args.no_full_text)
            except KeyboardInterrupt:
                print("\nĐã dừng chế độ tự động.")
                break

    if args.serve:
        start_server(host=args.host, port=args.port)

    if not any([args.crawl, args.stats, args.export_json, args.export_csv, args.export_excel, args.serve, args.schedule]):
        parser.print_help()

if __name__ == "__main__":
    main()
