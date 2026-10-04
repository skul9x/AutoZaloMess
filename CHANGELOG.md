# Changelog

## [2026-10-04] - v2.4.0 (Short Name Extraction & Role Salutation Formatting)
### Added
- **Given/Short Name Extraction**: Tự động trích xuất tên gọi ngắn (tên chính/last word) cho danh xưng tiếng Việt qua hàm `extract_short_name` (ví dụ: "Nguyễn Thị Linh" -> "Linh").
- **Role Detection & Salutation Personalization**: Nhận diện chính xác quan hệ/vai trò (`mẹ`, `bà`, `bố`, `bác`, `ông`, `cô`, `chú`, `phụ huynh`) từ dữ liệu VNCDC và tùy biến lời chào tin nhắn tự động (ví dụ: "mời mẹ Linh", "mời bà Mai", "mời bố Tuấn").
- **Child Fallback Preservation**: Trong trường hợp không có tên phụ huynh, tự động gán `"phụ huynh bé [Tên Bé]"` và bảo toàn nguyên cụm từ không bị cắt ngắn (ví dụ: "mời phụ huynh bé Nguyễn Văn An").
- **Table & Controller Data Integrity**: Lưu trữ đầy đủ họ tên trong bảng danh sách GUI và file sao lưu/khôi phục, đồng thời bổ sung trường `role` phục vụ định dạng tin nhắn gửi đi.
- **Unit & Integration Test Suites**: Bổ sung bộ kiểm thử `tests/test_short_name_formatting.py` và `tests/test_automation_message_formatting.py`.

### Changed
- Cập nhật `app/utils.py`, `app/controllers/app_controller.py`, và `app/automation_logic.py` để đồng bộ truyền nhận `role` và ghi log lời chào/tin nhắn gửi đi rõ ràng trên giao diện.

---

## [2026-09-26] - v2.3.0 (VNCDC Temporary Plan Injection & Safe Cleanup Flow)
### Added
- **VNCDC Temporary Plan Injection**: Tích hợp API `nhap_bo_sung_doi_tuong` (bổ sung đối tượng vào kế hoạch) để trích xuất số điện thoại unmasked qua `GetDanhSachHenTiemByParams`.
- **Safe Cleanup Guarantee**: Bổ sung cơ chế dọn dẹp đối tượng tự động trong khối `try ... finally` qua API `XoaDoiTuongDSHenTiem`, đảm bảo khôi phục nguyên trạng kế hoạch tiêm mà không ảnh hưởng tới dữ liệu có sẵn từ trước.
- **Unit Tests Suite**: Viết bộ unit test toàn diện cho luồng API client (`test_vncdc_client_plan_flow.py`) và bộ điều khiển (`test_app_controller_fetch_cleanup.py`).

### Changed
- Cập nhật luồng lấy danh sách trong `AppController` (`fetch_task`) để tìm kiếm qua các xã (`XA_ID`), gom nhóm batch injection và parse thông tin phụ huynh/SĐT trực tiếp từ lịch hẹn.
- Đồng bộ bộ nhớ kiến thức dự án `.brain/` (brain.json, session.json).

---

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
