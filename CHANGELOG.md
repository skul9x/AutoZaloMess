# Changelog

## [2026-03-08] - v2.1.0 (RPA Safety Update)
### Added
- **Anti-Duplicate Check**: App tự động bỏ qua (skip) các số điện thoại đã có trạng thái "Thành công" trong cùng phiên chạy, giúp ngăn chặn việc gửi trùng tin nhắn khi khởi động lại kịch bản.
- **Enhanced Search Cleanup**: Thêm phím nóng "Backspace" sau lệnh `Ctrl + A` trong các trường hợp lỗi (Failed) hoặc Timeout. Đảm bảo ô tìm kiếm Zalo luôn được xóa trắng tuyệt đối trước khi xử lý SĐT tiếp theo.
- **Success Delay (300ms)**: Thêm khoảng thời gian chờ 300ms ngay sau khi nhận diện ảnh Thành công. Giúp UI Zalo ổn định hơn trước khi app thực hiện cú click vào tọa độ người dùng.

### Changed
- Cập nhật phiên bản bộ nhớ dự án (.brain) lên trạng thái v2.1.
- Tối ưu hóa thời gian phản hồi giữa các thao tác phím nóng để tránh hiện tượng kẹt phím mô phỏng.

---

## [2026-03-01] - v2.0.0 (Release)
### Added
- **Official v2.0 Upgrade**: Toàn bộ hệ thống được đồng bộ hóa lên phiên bản 2.0.
- **Auto Cleanup UI**: Thêm logic `click(friend_coords)` và `Ctrl+A` để dọn dẹp màn hình Zalo khi gặp SĐT không tồn tại hoặc Timeout, ngăn ngừa lỗi click loạn lượt tiếp theo.
- **Smart Wait 10s**: Nâng cấp hệ thống nhận diện 3 trạng thái ảnh (Success, Failed, RateLimit) với thời gian chờ tối ưu.

### Changed
- Cập nhật tiêu đề ứng dụng (MainWindow) thành v2.0.
- Cập nhật README.md với phân mục "Có gì mới trong bản v2.0?".
- Cấu trúc `.brain/` (brain.json, session.json) phản ánh trạng thái v2.0.

### Fixed
- **Critical Logic Fix**: Sửa lỗi "ấn loạn cả lên" khi gặp số điện thoại không tồn tại (do thiếu bước dọn dẹp focus cũ).
- Sửa lỗi không tìm thấy text trong ô search khi gõ số tiếp theo.

---

## [2026-03-01] - v1.3.0 (Alpha)
### Added
- Giao diện (UI) thêm ô chọn "Ảnh báo thành công" cho cả App và Web.
- Hàm `wait_for_any_image` trong `automation_logic.py`, cho phép quét màn hình tìm 3 trạng thái cùng lúc (Success, Failed, RateLimit).
- Khởi tạo thư mục `.brain/` (brain.json, session.json) để AI giữ ngữ cảnh.
- Tự động hóa cài đặt các dependencies mới.

### Changed
- Refactor logic Bước 3 & Bước 4: Loại bỏ `time.sleep(2.5)` cố định, thay bằng Smart Wait thời gian chờ tối đa 10s.
- Cập nhật luồng xử lý `AppController` để truyền đủ 3 file ảnh điều kiện.

### Fixed
- Lỗi thiếu thư viện `pyautogui`, `pyperclip`, `tkcalendar`.
- Lỗi mạng lag dẫn đến click sai (nay được xử lý bằng ảnh Thành công cố định).

---
*Tạo bởi Antigravity Librarian*
