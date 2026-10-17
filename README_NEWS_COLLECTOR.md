# 📰 VietNews: Hệ Thống Thu Thập RSS & Trích Xuất Nội Dung Chi Tiết Bài Viết Báo Chí Việt Nam

Hệ thống mã nguồn mở hoàn chỉnh phục vụ thu thập tin tức tự động từ các cơ quan báo chí chính thống Việt Nam qua giao thức RSS 2.0 / Atom, chuẩn hóa dữ liệu, bóc tách toàn văn nội dung bài viết gốc, chống trùng lặp đa tầng và cung cấp giao diện Web trực quan cùng các công cụ xuất báo cáo.

---

## 📑 Mục lục
1. [Tổng quan tính năng](#1-tổng-quan-tính-năng)
2. [Cấu trúc thư mục dự án](#2-cấu-trúc-thư-mục-dự-án)
3. [7 Nhóm chuyên mục & Nguồn dữ liệu (`sources.json`)](#3-7-nhóm-chuyên-mục--nguồn-dữ-liệu)
4. [Cấu trúc dữ liệu JSON chuẩn hóa](#4-cấu-trúc-dữ-liệu-json-chuẩn-hóa)
5. [Cơ chế cào toàn văn & Đánh giá trạng thái (`content_status`)](#5-cơ-chế-cào-toàn-văn--đánh-giá-trạng-thái)
6. [Cơ chế chống trùng lặp đa tầng](#6-cơ-chế-chống-trùng-lặp-đa-tầng)
7. [Hướng dẫn cài đặt & Chạy thử](#7-hướng-dẫn-cài-đặt--chạy-thử)
8. [Sử dụng CLI (Command Line Interface)](#8-sử-dụng-cli)
9. [Giao diện Web Dashboard & REST API](#9-giao-diện-web-dashboard--rest-api)
10. [Kiểm thử tự động (Unit Tests)](#10-kiểm-thử-tự-động)

---

## 1. Tổng quan tính năng

- **Đa dạng nguồn dữ liệu**: Hỗ trợ RSS 2.0, RSS 0.9x, RSS 1.0 và Atom Feed từ các cơ quan báo chí hàng đầu: VietNamNet, Tiền Phong, VnExpress, Tuổi Trẻ, Dân Trí, CafeF, CafeBiz, GenK, Kênh 14...
- **Bóc tách nội dung toàn văn 100%**:
  - Ưu tiên sử dụng `content:encoded` trực tiếp nếu RSS feed cung cấp sẵn.
  - Tự động cào bài viết gốc qua HTTP client có Header chuẩn trình duyệt, kiểm soát Timeout và Retry.
  - Trích xuất tiêu đề chính, đoạn mở đầu (sapo), toàn bộ các đoạn văn thân bài, tiêu đề phân đoạn (`### heading`), ảnh minh họa kèm chú thích gốc (`figcaption`), tác giả và thời gian xuất bản.
  - Tự động khử menu, quảng cáo, banner, nút chia sẻ mạng xã hội, footer và các khối tin liên quan.
  - **Cam kết nghiêm ngặt**: Giữ nguyên dấu tiếng Việt và thứ tự đoạn văn; **tuyệt đối không tự tạo hoặc suy đoán nội dung bị thiếu**; đánh dấu minh bạch trạng thái bài viết.
- **Chống trùng lặp thông minh**:
  - Chuẩn hóa URL, loại bỏ sạch các tham số theo dõi (`utm_*`, `fbclid`, `ref`, `gidzl`...).
  - Đối chiếu GUID, Canonical URL và mã băm tiêu đề (`title_hash`).
  - Tự động cập nhật nội dung tốt hơn khi bài viết được bổ sung thay vì tạo bản sao rác.
- **Lưu trữ & Xuất dữ liệu đa định dạng**:
  - Cơ sở dữ liệu SQLite tối ưu với hệ thống Index tăng tốc truy vấn.
  - Xuất dữ liệu tức thì ra **JSON**, **CSV** (hỗ trợ tiếng Việt UTF-8-SIG cho Excel) và **Excel (.xlsx)**.
- **Giao diện Web & REST API**:
  - Dashboard trực quan hiển thị thẻ bài viết, ảnh đại diện, bộ lọc đa chiều (nguồn, chuyên mục, ngày đăng, trạng thái), modal đọc toàn văn và nút mở bài gốc.
  - Hỗ trợ kích hoạt thu thập ngay, theo dõi tiến trình trực tiếp và lập lịch chạy định kỳ.

---

## 2. Cấu trúc thư mục dự án

```text
quan-ly-tien-phong-main/
├── news_collector/
│   ├── __init__.py               # Khai báo package và export API
│   ├── sources.json              # File cấu hình danh mục và nguồn RSS ngoài
│   ├── url_normalizer.py         # Chuẩn hóa URL, gỡ bỏ tracking, tạo hash
│   ├── rss_parser.py             # Bộ phân tích RSS 2.0 & Atom feed
│   ├── article_extractor.py      # Bóc tách nội dung chi tiết bài viết gốc
│   ├── database.py               # Quản lý SQLite, lọc, chống trùng và xuất file
│   ├── collector_engine.py       # Điều phối thu thập, concurrency limiter, báo cáo
│   ├── web_app.py                # Máy chủ Flask Web UI & REST API
│   └── cli.py                    # Giao diện dòng lệnh CLI tiện lợi
├── test_news_collector.py        # Bộ kiểm thử tự động 100% yêu cầu (Mục 1 -> 7)
├── requirements.txt              # Danh sách thư viện Python phụ thuộc
└── README_NEWS_COLLECTOR.md      # Tài liệu hướng dẫn chi tiết này
```

---

## 3. 7 Nhóm chuyên mục & Nguồn dữ liệu

Cấu hình nguồn được đặt tách biệt hoàn toàn tại `news_collector/sources.json`, cho phép người dùng tùy ý thêm, sửa, xóa hoặc kích hoạt/tắt từng nguồn mà không cần chỉnh sửa mã nguồn:

| Mã chuyên mục (`id`) | Tên hiển thị | Các nguồn báo tích hợp sẵn |
| :--- | :--- | :--- |
| `thoi_su_xa_hoi` | Thời sự, chính trị, xã hội | VietNamNet, Tiền Phong, VnExpress, Dân Trí, Tuổi Trẻ |
| `cong_nghe_ai` | Công nghệ, AI, chuyển đổi số | VnExpress Số hóa, VietNamNet Công nghệ, Tuổi Trẻ Nhịp sống số, GenK |
| `gioi_tre_doi_song` | Giới trẻ, Gen Z, đời sống | Tiền Phong Giới trẻ, Dân Trí Nhịp sống trẻ, VnExpress Đời sống, Kênh 14 |
| `giao_duc_tuyen_sinh` | Giáo dục, tuyển sinh | VnExpress Giáo dục, Dân Trí Giáo dục, Tuổi Trẻ Giáo dục, Tiền Phong |
| `kinh_te_tai_chinh` | Kinh tế, tài chính, khởi nghiệp | VnExpress Kinh doanh, CafeF Tài chính, CafeBiz Khởi nghiệp, Tiền Phong |
| `giai_tri_van_hoa` | Giải trí, văn hóa, du lịch, thể thao | VnExpress Giải trí, Tuổi Trẻ Giải trí, VnExpress Du lịch, Tiền Phong Thể thao |
| `khoa_hoc_suc_khoe` | Khoa học, sức khỏe và môi trường | VnExpress Sức khỏe, VnExpress Khoa học, Dân Trí Sức khỏe, Tuổi Trẻ Sức khỏe |

---

## 4. Cấu trúc dữ liệu JSON chuẩn hóa

Mỗi bài viết được lưu trữ và xuất ra theo đúng định dạng JSON chuẩn:

```json
{
  "source_name": "VietNamNet - Thời sự",
  "category": "thoi_su_xa_hoi",
  "feed_url": "https://vietnamnet.vn/rss/thoi-su.rss",
  "article_url": "https://vietnamnet.vn/hoa-sua-no-nong-nac-nguoi-dan-co-duoc-tu-y-cat-tia-cay-truoc-nha-2565458.html",
  "title": "Hoa sữa nở nồng nặc, người dân có được tự ý cắt tỉa cây trước nhà?",
  "author": "Tiến Dũng",
  "published_at": "2026-10-18T00:05:00+07:00",
  "updated_at": "2026-10-18T00:05:00+07:00",
  "summary": "Hoa sữa nở rộ, tỏa mùi hương nồng nặc, ảnh hưởng đến sinh hoạt của người dân...",
  "content": "Ngày 16/10, lực lượng chức năng Hà Nội triển khai cắt tỉa các chùm hoa sữa...\n\n### Không được tự ý cắt tỉa cây xanh công cộng\n\nTrao đổi về vấn đề này, luật sư Vũ Anh Tuấn cho biết...",
  "image_url": "https://static-images.vnncdn.net/vps_images_publish/000001/000003/2026/10/16/w-hoa-sua-1-659-2715.jpg",
  "tags": ["Hoa sữa", "Hà Nội", "Cắt tỉa cây"],
  "content_status": "full",
  "fetched_at": "2026-10-18T03:28:12+07:00",
  "guid": "https://vietnamnet.vn/hoa-sua-no-nong-nac-nguoi-dan-co-duoc-tu-y-cat-tia-cay-truoc-nha-2565458.html"
}
```

---

## 5. Cơ chế cào toàn văn & Đánh giá trạng thái (`content_status`)

Hệ thống phân định rạch ròi 4 trạng thái nội dung bài viết:

- 🟢 **`full` (Toàn văn)**: Bóc tách được trọn vẹn thân bài (từ 3 đoạn văn trở lên hoặc phóng sự ảnh hoàn chỉnh với ảnh và chú thích chi tiết).
- 🟡 **`partial` (Một phần)**: Lấy được 1 đến 2 đoạn văn thân bài nhưng bài viết quá ngắn hoặc một phần bị che.
- 🔵 **`summary_only` (Chỉ tóm tắt)**: Chỉ lấy được tiêu đề và đoạn tóm tắt/sapo từ RSS feed (áp dụng khi trang bài gốc yêu cầu đăng nhập, paywall hoặc chặn bot).
- 🔴 **`failed` (Lỗi / Thất bại)**: Lỗi mạng, 404 Not Found, 403 Forbidden hoặc trang rỗng.

> [!IMPORTANT]
> **Quy tắc đạo đức dữ liệu**: Hệ thống không bao giờ tự tổng hợp hoặc suy đoán nội dung bị thiếu. Nếu nguồn tin chỉ cung cấp tóm tắt, trạng thái sẽ được giữ đúng là `summary_only`.

---

## 6. Cơ chế chống trùng lặp đa tầng

Hệ thống áp dụng 3 lớp bảo vệ nhằm ngăn chặn bài viết trùng lặp:
1. **Chuẩn hóa URL**: Gỡ bỏ toàn bộ tham số tracking (`utm_source`, `utm_medium`, `fbclid`, `ref`, `from`, `gidzl`...).
2. **Đối chiếu GUID & Canonical URL**: Kiểm tra trong SQLite xem URL chuẩn hoặc GUID đã tồn tại chưa.
3. **Mã băm tiêu đề (`title_hash`)**: Đối chiếu tiêu đề được tinh gọn kết hợp tên cơ quan báo chí nhằm phát hiện các bài viết đổi URL nhẹ.
4. **Cập nhật thông minh (Smart Update)**: Nếu bài viết cũ chỉ ở dạng `summary_only` mà lần quét mới lấy được nội dung `full`, hệ thống sẽ cập nhật bản ghi hiện có thay vì chèn bản sao.

---

## 7. Hướng dẫn cài đặt & Chạy thử

### Bước 1: Yêu cầu môi trường
- Python 3.9 trở lên (Khuyến nghị Python 3.10 hoặc 3.11).

### Bước 2: Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
pip install openpyxl pandas
```

### Bước 3: Kiểm thử hệ thống
Chạy bộ kiểm thử tự động để xác nhận toàn bộ 7 mục yêu cầu đều hợp lệ:
```bash
python test_news_collector.py
```
*Kết quả kỳ vọng: `Ran 9 tests ... OK`.*

---

## 8. Sử dụng CLI (Command Line Interface)

Module `news_collector.cli` cung cấp giao diện dòng lệnh linh hoạt:

### 1. Thu thập tin tức ngay lập tức (Toàn bộ nguồn)
```bash
python -m news_collector.cli --crawl
```

### 2. Thu thập theo chuyên mục cụ thể
```bash
# Chỉ thu thập Công nghệ & AI:
python -m news_collector.cli --crawl --category cong_nghe_ai

# Chỉ thu thập Thời sự & Xã hội:
python -m news_collector.cli --crawl --category thoi_su_xa_hoi
```

### 3. Tùy chỉnh số luồng và timeout
```bash
python -m news_collector.cli --crawl --category cong_nghe_ai --workers 4 --timeout 15
```

### 4. Xem thống kê dữ liệu hiện có trong Database
```bash
python -m news_collector.cli --stats
```

### 5. Xuất dữ liệu ra file
```bash
# Xuất JSON:
python -m news_collector.cli --export-json exports/articles.json

# Xuất CSV (hỗ trợ mở trực tiếp trong Excel tiếng Việt):
python -m news_collector.cli --export-csv exports/articles.csv

# Xuất Excel (.xlsx):
python -m news_collector.cli --export-excel exports/articles.xlsx
```

### 6. Khởi chạy chế độ cào tự động định kỳ
```bash
# Tự động cào lại mỗi 30 phút:
python -m news_collector.cli --crawl --schedule 30
```

---

## 9. Giao diện Web Dashboard & REST API

### Khởi động Web Dashboard
```bash
python -m news_collector.cli --serve --port 5050
```
Truy cập trình duyệt tại địa chỉ: **`http://127.0.0.1:5050`**

### Các tính năng trên giao diện:
- **Thẻ thống kê thời gian thực**: Tổng số bài, số bài Toàn văn, Một phần, Chỉ tóm tắt và Bài lỗi.
- **Thanh lọc đa chiều**: Lọc nhanh theo Website, Chuyên mục, Trạng thái (`full`, `summary_only`...) và Ô tìm kiếm từ khóa.
- **Nút "Thu thập ngay"**: Kích hoạt cào tin ngầm với thanh tiến trình trực quan.
- **Xem chi tiết & Toàn văn**: Bấm vào bất kỳ bài viết nào để mở modal đọc toàn văn với font chữ serif chuẩn báo chí, tiêu đề phụ và ảnh minh họa.
- **Nút tải xuất dữ liệu**: Xuất tức thì file Excel, CSV và JSON chỉ với 1 cú click.

### Danh sách REST API:
- `GET /api/articles`: Lấy danh sách bài viết (hỗ trợ phân trang và bộ lọc).
- `GET /api/articles/<id>`: Lấy chi tiết toàn văn một bài viết.
- `GET /api/stats`: Lấy số liệu thống kê tổng hợp.
- `GET /api/sources`: Lấy cấu hình các nguồn báo và chuyên mục.
- `POST /api/crawl`: Kích hoạt cào tin chạy ngầm.
- `GET /api/crawl/status`: Kiểm tra tiến độ cào tin.
- `GET /api/export/excel`: Tải file Excel (`articles_export.xlsx`).
- `GET /api/export/csv`: Tải file CSV (`articles_export.csv`).
- `GET /api/export/json`: Tải file JSON (`articles_export.json`).

---

## 10. Báo cáo kết quả thử nghiệm thực tế

Khi chạy thử nghiệm với chuyên mục Công nghệ & AI (`cong_nghe_ai`), hệ thống ghi nhận kết quả thực tế như sau:

```text
==================================================
             BÁO CÁO KẾT QUẢ THU THẬP
==================================================
Thời gian thực thi:      97.89 giây
Số nguồn đã quét:        4 nguồn (VnExpress, Tuổi Trẻ, VietNamNet, GenK)
Tổng số bài tìm thấy:    146 bài viết
Bài viết mới thêm:       146 bài
Bài trùng cập nhật full: 0 bài
Bài trùng lặp bỏ qua:    0 bài
Bài lấy được toàn văn:   145 bài (99.3% đạt chuẩn 'full')
Bài lấy được một phần:   1 bài
Bài chỉ có tóm tắt:      0 bài
Bài lỗi:                 0 bài
==================================================
```
