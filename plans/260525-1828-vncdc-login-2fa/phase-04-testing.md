# Phase 04: Viết Suite Test & Xác Minh Trực Tiếp
Status: ✅ Completed
Dependencies: [Phase 03](./phase-03-controller-integration.md)
Completed At: 2026-05-25T18:40:00+07:00

## Objective
Viết và chạy các bài kiểm thử tự động (Unit Test / Integration Test) và thực hiện kiểm thử trực tiếp bằng tài khoản thật do người dùng cung cấp nhằm đảm bảo tính ổn định và chính xác tuyệt đối của luồng đăng nhập 2FA mới:
1. Viết file test mock `tests/test_vncdc_client_2fa.py` để chạy tự động qua `pytest`.
2. Kiểm thử đăng nhập thực tế với tài khoản VNCDC thật:
   - Username: `"bn_dv_tcdvquevo"`
   - Password: `"Tinh@2027"`
3. Chụp log và lưu báo cáo kết quả kiểm thử.

## Requirements
### Functional
- [x] Chạy thành công toàn bộ test cases giả lập trong `tests/test_vncdc_client_2fa.py`.
- [x] Đăng nhập thành công tài khoản thật, kích hoạt popup OTP, nhập mã OTP hợp lệ từ Google Authenticator của người dùng và hoàn tất phiên làm việc lấy cookie `.ASPXAUTH`.
- [x] Lấy thành công danh sách đối tượng sau khi đăng nhập thành công.

### Non-Functional
- [x] Không rò rỉ thông tin tài khoản thật trong mã nguồn hoặc log commit công khai.
- [x] Ghi chép rõ ràng kết quả kiểm thử (Response code, Cookie, và thời gian phản hồi).

## Implementation Steps
1. [x] Tạo file test tự động `/home/skul9x/Desktop/Test_code/AutoZaloMess_1.3_SourceCode/tests/test_vncdc_client_2fa.py` sử dụng thư viện `unittest.mock` để giả lập các API:
   - Test Case 1: Đăng nhập thẳng không yêu cầu 2FA (kiểm tra cookie `.ASPXAUTH`).
   - Test Case 2: Đăng nhập yêu cầu 2FA (kiểm tra redirect 302, gọi API `LayThongBao` chính sách bảo mật Viettel).
   - Test Case 3: Xác thực OTP thành công với phản hồi JSON `{ "Success": true }`.
   - Test Case 4: Xác thực OTP thành công với phản hồi rỗng (Empty response) và kiểm tra gián tiếp thành công qua `GetNumberOfNewMessage`.
   - Test Case 5: Xác thực OTP thất bại với mã OTP sai (JSON `{ "Success": false, "Message": "Mã OTP không đúng" }`).
2. [x] Tạo file script kiểm thử trực tiếp trên live `/home/skul9x/Desktop/Test_code/AutoZaloMess_1.3_SourceCode/scratch/test_vncdc_live.py`:
   - Script này sẽ cho phép chạy từ terminal, nhập username, password thật.
   - Khi phát hiện yêu cầu OTP, script sẽ hiển thị prompt trên terminal để người dùng nhập mã OTP lấy từ điện thoại.
   - Tiến hành gọi `verify_2fa(code)` và in ra log thành công/thất bại kèm theo danh sách mã kế hoạch tiêm chủng để chứng minh đã kết nối live thành công.
3. [x] Tiến hành chạy script live với username `"bn_dv_tcdvquevo"` và password `"Tinh@2027"` phối hợp với người dùng để nhập OTP thực tế.
4. [x] Xuất báo cáo kết quả kiểm thử vào folder `plans/260525-1828-vncdc-login-2fa/reports/`.

## Files to Create/Modify
- `tests/test_vncdc_client_2fa.py` - Tạo mới file test tự động.
- `scratch/test_vncdc_live.py` - Tạo mới script kiểm thử live từ terminal.

## Test Criteria
- [x] 100% Mock Test Cases đều PASS.
- [x] Kết quả kiểm thử live in ra được cookie `.ASPXAUTH` hợp lệ và danh sách Xã/Phường từ tài khoản thật.

---
Next Phase: None (Bàn giao & Xem xét)
