# Phase 01: Nâng Cấp VncdcClient
Status: ✅ Completed
Dependencies: None
Completed At: 2026-05-25T18:35:00+07:00

## Objective
Nâng cấp thư viện client `VncdcClient` (`app/services/vncdc_client.py`) để tích hợp đầy đủ các API và cơ chế bảo mật mới của hệ thống VNCDC dựa trên code thực tế từ dự án `VaccineAnalyzer-Pro-main`:
1. Sử dụng phương thức AJAX POST khi đăng nhập để bắt được yêu cầu xác thực 2 lớp (`TwoFactorRequired`).
2. Gửi request `GET /DonViHanhChinh/LayThongBao` để chấp nhận điều khoản bảo mật của Viettel.
3. Thêm phương thức `verify_2fa(code)` để gửi mã OTP.
4. Xử lý trường hợp server VNCDC trả về Empty Response (HTTP 200 nhưng text trống) khi gửi mã OTP đúng bằng cách kiểm tra gián tiếp cookie `.ASPXAUTH` thông qua request test nhỏ `GET /Home/GetNumberOfNewMessage`.

## Requirements
### Functional
- [x] Gửi thành công request đăng nhập AJAX và phân tích kết quả trả về (`TwoFactorRequired`).
- [x] Tự động gửi request xác nhận bảo mật `/DonViHanhChinh/LayThongBao` khi 2FA được yêu cầu.
- [x] Hỗ trợ xác thực mã OTP qua API `/Account/VerifyTwoFactor`.
- [x] Vượt qua lỗi crash do parse JSON rỗng bằng cơ chế xác thực gián tiếp.

### Non-Functional
- [x] Tương thích 100% với `httpx` hiện có trong `AutoZaloMess` để không gây lỗi import hay xung đột thư viện.
- [x] Log đầy đủ các bước HTTP request phục vụ cho việc debug.

## Implementation Steps
1. [x] Cập nhật định nghĩa class `VncdcClient` trong `app/services/vncdc_client.py`.
2. [x] Sửa đổi hàm `login(self, username, password, remember=True)`:
   - Thực hiện GET `/Account/Login` để bóc tách CSRF token `__RequestVerificationToken`.
   - Thực hiện AJAX POST tới `/Account/Login` với header `X-Requested-With: XMLHttpRequest` và `Content-Type: application/x-www-form-urlencoded; charset=UTF-8`.
   - Phân tích phản hồi:
     - Nếu redirect 302 đến `VerifyTwoFactor` hoặc JSON trả về có `"TwoFactorRequired": true`:
       - Thực hiện request phụ `GET /DonViHanhChinh/LayThongBao` kèm header AJAX để ký chấp nhận chính sách.
       - Trả về tuple `(True, "2fa_required", message)`.
     - Nếu đăng nhập thẳng thành công (không có 2FA):
       - Kiểm tra sự tồn tại của cookie `.ASPXAUTH`.
       - Trả về `(True, "success", None)`.
     - Nếu thất bại:
       - Trả về `(False, "failed", error_message)`.
3. [x] Thêm hàm `verify_2fa(self, code)`:
   - Thực hiện AJAX POST tới `/Account/VerifyTwoFactor` with payload `{"code": code}`.
   - Nếu cookie `.ASPXAUTH` lập tức xuất hiện -> Trả về `(True, None)`.
   - Nếu phản hồi trống (HTTP 200, empty text):
     - Gửi request kiểm tra gián tiếp đến `GET /Home/GetNumberOfNewMessage` với header AJAX.
     - Nếu status 200 và `.ASPXAUTH` có trong cookies -> Trả về `(True, None)`.
   - Nếu phản hồi không trống:
     - Parse JSON và kiểm tra `json_resp.get("Success")`. Nếu True -> Trả về `(True, None)`. Ngược lại trả về `(False, error_message)`.

## Files to Create/Modify
- `app/services/vncdc_client.py` - Cập nhật logic `login` và thêm `verify_2fa`.

## Test Criteria
- [x] Viết suite test mock `tests/test_vncdc_client_2fa.py` mô phỏng các phản hồi từ server VNCDC (Thành công thẳng, Yêu cầu 2FA, Gửi OTP thành công với phản hồi trống, Gửi OTP sai).
- [x] Chạy suite test và đảm bảo 100% test cases đều PASS trước khi sang Phase 2.

---
Next Phase: [Phase 02: Xây dựng giao diện nhập mã OTP](./phase-02-ui-otp-dialog.md)
