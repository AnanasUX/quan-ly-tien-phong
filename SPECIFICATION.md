# TÀI LIỆU ĐẶC TẢ HỆ THỐNG ANX
**(Bao gồm Bot Telegram Quản lý & Website Thời tiết - Tin tức)**

---

## 1. TỔNG QUAN HỆ THỐNG
Hệ thống AnX là một hệ sinh thái tiện ích cá nhân bao gồm 2 thành phần cốt lõi:
1. **Telegram Bot (Backend - Python):** Xử lý các nghiệp vụ tự động hóa quản lý tiền phòng, điện nước, lưu trữ Google Calendar và tạo payload dữ liệu thời tiết.
2. **Website Frontend (ReactJS - Vite):** Giao diện hiển thị thời tiết, cảnh báo và tin tức nóng. Hoạt động song song thông qua payload của Bot hoặc chạy độc lập (Standalone) hoàn toàn theo thời gian thực.

---

## 2. ĐẶC TẢ TÍNH NĂNG: TELEGRAM BOT

### 2.1. Nghiệp vụ Tính hóa đơn Điện / Nước (`/tinh`, `/tinhcn`)
- **Mô tả:** Hỗ trợ người dùng nhập liệu số điện, số nước (theo từng bước hoặc nhập nhanh 1 dòng phân cách bởi dấu `;`) để tính toán hóa đơn.
- **Ràng buộc toàn vẹn (State Locked):** 
  - Sau khi tính xong hóa đơn, hệ thống sẽ đưa người dùng vào trạng thái **"Chờ chốt nước"**.
  - Không cho phép người dùng chạy lệnh `/tinh` hoặc `/tinhcn` mới nếu chưa hoàn tất lệnh `.sonuocngay` của chu kỳ trước (Báo lỗi cảnh báo).
- **Cơ chế Timeout (Chống treo hệ thống):**
  - Nếu đang trong quy trình nhập liệu mà người dùng không phản hồi quá **120 giây (2 phút)**, Bot tự động hủy phiên làm việc, xóa các câu hỏi đang lửng lơ trên khung chat và thông báo hủy.

### 2.2. Nghiệp vụ Chốt số nước hằng ngày (`.sonuocngay`)
- **Tích hợp Google Calendar:**
  - Nhận số khối nước tiêu thụ thực tế để ước tính số ngày sử dụng còn lại.
  - Tự động ghim lịch "💧 Lịch chốt số nước" vào Google Calendar vào đúng **19:00 đến 19:30 (7:00 PM)** của ngày dự kiến.
  - **Chống trùng lặp:** Tự động rà soát và xóa các sự kiện "Lịch chốt số nước" cũ trong tương lai trước khi ghim sự kiện mới.

### 2.3. Cơ chế Xóa dấu vết (Auto-Cleanup / Self-Destruct)
- Toàn bộ các tin nhắn sinh ra trong quy trình giao dịch (Bao gồm: Lệnh của người dùng, số liệu người dùng nhập, câu hỏi của Bot, Hóa đơn trả về, Câu lệnh `.sonuocngay` và thông báo ghim lịch thành công) đều được đưa vào hàng đợi.
- Sau khi quy trình hoàn tất, hệ thống sẽ đếm ngược **đúng 30 giây** và thu hồi/xóa sạch toàn bộ đoạn hội thoại này.
- Ngay cả tin nhắn gọi website (`/websitecn`) và link website Bot trả về cũng sẽ tự động bốc hơi sau 30 giây.

---

## 3. ĐẶC TẢ TÍNH NĂNG: WEBSITE FRONTEND

### 3.1. Chế độ hoạt động Độc lập (Standalone Real-time)
- Website (`https://ananasux.github.io/Website_thoitiet_design/`) có khả năng vận hành độc lập mà không cần bất kỳ tham số url (`?cdata=`) nào từ Bot.
- **Luồng xử lý:** Tự động kết nối trực tiếp đến **OpenWeatherMap API** để lấy thông tin nhiệt độ, sức gió, PM2.5 và dự báo 3 giờ tới.
- **Đồng hồ động:** Tích hợp bộ đếm JavaScript thời gian thực (Cập nhật giao diện mỗi 60 giây). Định dạng hiển thị chuẩn: `Thứ Bảy, 26 tháng 9 · 10:57`.

### 3.2. Bóc tách Tin tức và Xử lý Ảnh (CORS Proxy Scraper)
- **Cơ chế lấy tin:** Fetch dữ liệu từ Google News RSS thông qua `rss2json.com`. Các tin tức được trộn ngẫu nhiên (Shuffle) mỗi lần F5 trang.
- **Trích xuất OpenGraph Image (OG:Image):**
  - Giải quyết nhược điểm không có ảnh từ RSS bằng cách quét DOM client-side.
  - Tự động gọi qua Proxy `allorigins.win` để bẻ khóa CORS, đọc mã HTML gốc của tờ báo, tìm thẻ `<meta property="og:image">` và gắn ngược lại vào UI.
  - Giúp giao diện luôn có hình ảnh trực quan mà không cần backend xử lý hộ.

### 3.3. Tối ưu Giao diện (UI/UX)
- Gỡ bỏ các yếu tố tĩnh thừa (Nút "Mới nhất", "Xem thêm tin tức", Nút Dev ẩn).
- Chỉnh sửa nhận diện thương hiệu nhất quán với text logo: **Anx.**
- Giao diện Responsive toàn diện (chuyển đổi linh hoạt giữa Mobile & Desktop layout).

---

## 4. CÔNG NGHỆ SỬ DỤNG (TECH STACK)
- **Backend Bot:** `Python 3`, `python-telegram-bot`, `Flask` (cho Webhook & API nội bộ), `google-api-python-client` (Calendar API).
- **Frontend Web:** `React 19`, `Vite`, `Tailwind CSS v4`.
- **Triển khai (Deployment):** Frontend host trực tiếp dưới dạng tĩnh trên GitHub Pages, Backend chạy môi trường Server/VPS (hỗ trợ cả Polling và Webhook).
