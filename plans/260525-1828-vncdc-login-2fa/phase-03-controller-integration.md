# Phase 03: Tích Hợp Controller & Xử Lý Bất Đồng Bộ
Status: ✅ Completed
Dependencies: [Phase 02](./phase-02-ui-otp-dialog.md)

## Objective
Tích hợp `OtpDialog` vào luồng điều phối của `AppController` (`app/controllers/app_controller.py`) thông qua cơ chế Queue bất đồng bộ của Tkinter để đảm bảo app không bị crash, đơ (Not Responding) khi giao tiếp mạng chạy ngầm:
1. Sửa hàm `handle_vncdc_login` để nhận dạng trạng thái `"2fa_required"`.
2. Truyền mã OTP từ giao diện Tkinter main thread xuống luồng background để tiếp tục quy trình xác thực.
3. Đồng bộ hóa việc cập nhật trạng thái UI (`FetchTab`) sau khi đăng nhập thành công hoặc thất bại.

## Requirements
### Functional
- [x] Khi server báo cần OTP, mở `OtpDialog` trên main thread của Tkinter một cách an toàn.
- [x] Chạy task xác thực OTP ngầm trên background thread.
- [x] Nếu OTP sai, giữ dialog mở và hiển thị thông báo lỗi trực tiếp trên dialog để user nhập lại mã mới.
- [x] Khi OTP đúng, đóng dialog, hoàn tất đăng nhập và load dữ liệu Kế hoạch tiêm chủng (`fetch_profile_and_plan`).

### Non-Functional
- [x] Giao diện chính của app không bị đơ hoặc treo khi đang chờ mạng xác thực OTP.
- [x] Tách biệt logic luồng UI (main thread) và luồng mạng (worker thread).

## Implementation Steps
1. [x] Cập nhật hàm `handle_vncdc_login` trong `app/controllers/app_controller.py`:
   - Định nghĩa lại `login_task`:
     - Khởi tạo `client = VncdcClient()`.
     - Gọi `success, status, data = client.login(username, password, remember)`.
     - Nếu `status == "2fa_required"`:
       - Đưa message `("otp_required", client, data)` vào `comm_queue`.
       - Giữ kết nối client mở để chờ xác thực OTP.
     - Nếu đăng nhập thẳng thành công:
       - Load plan/profile, lưu credentials và đưa `("login_result", True, ...)` vào `comm_queue`.
     - Nếu thất bại ngay:
       - Đóng client và đưa `("login_result", False, error_msg)` vào `comm_queue`.
2. [x] Cập nhật hàm `process_comm_queue` trong `app_controller.py` để xử lý các tín hiệu mới:
   - Thêm case `msg_type == "otp_required"`:
     - Đọc `client` và `message` (thông báo lỗi/hướng dẫn từ server).
     - Khởi chạy một hàm `show_otp_and_verify(client, message)` trên main thread.
3. [x] Viết hàm `show_otp_and_verify(self, client, message)`:
   - Khởi tạo `dialog = OtpDialog(self.window, error_message=message)`.
   - Lắng nghe sự kiện click nút Xác thực của dialog:
     - Khi user submit mã OTP, thay vì tắt dialog ngay, chạy một background thread mới gọi `client.verify_2fa(code)`.
     - Nếu `verify_2fa` trả về `(True, None)` (thành công):
       - Gọi `client.fetch_profile_and_plan()` ngầm.
       - Gửi tín hiệu thành công về main thread để đóng dialog, lưu credentials và cập nhật UI thành công.
     - Nếu trả về `(False, error_msg)` (thất bại):
       - Gửi tín hiệu lỗi về main thread để cập nhật label lỗi trên dialog và cho phép user nhập lại.

## Files to Create/Modify
- `app/controllers/app_controller.py` - Cập nhật logic `handle_vncdc_login`, `process_comm_queue` và tích hợp dialog OTP.

## Test Criteria
- [x] Thực hiện chạy mock test tích hợp của Phase 3 trong `tests/test_vncdc_client_2fa.py` để verify luồng controller + client hoạt động trơn tru.

---
Next Phase: [Phase 04: Viết suite test & Xác minh trực tiếp](./phase-04-testing.md)
