# Phase 02: Xây Dựng Giao Diện Nhập Mã OTP
Status: ✅ Completed
Dependencies: [Phase 01](./phase-01-client-upgrade.md)

## Objective
Xây dựng một Dialog Tkinter đẹp mắt và thân thiện (`app/gui/otp_dialog.py`) kế thừa giao diện của `OTPDialog` trong PySide từ `VaccineAnalyzer-Pro-main`:
1. Hiển thị thông báo hướng dẫn người dùng lấy mã xác thực 2 lớp qua Google Authenticator.
2. Cung cấp một ô nhập mã OTP lớn, giới hạn nhập 6 chữ số, chỉ cho nhập số.
3. Đồng hồ đếm ngược 30 giây giả lập để hướng dẫn chu kỳ thay đổi mã OTP của Google Authenticator.
4. Nút "🔐 Xác thực" và "Hủy" có trạng thái Disable khi đang gửi xác thực để tránh click đúp.
5. Hiển thị thông báo lỗi trực tiếp trên giao diện nếu nhập sai mã.

## Requirements
### Functional
- [x] Chặn nhập ký tự không phải số, giới hạn đúng 6 chữ số.
- [x] Tự động đếm ngược từ 30s về 0s và lặp lại để biểu thị chu kỳ mã OTP. Đổi màu chữ sang đỏ khi countdown dưới 5s.
- [x] Tự động Focus vào ô nhập OTP ngay khi dialog mở ra.
- [x] Hỗ trợ phím nóng `Enter` để gửi mã và `Escape` để đóng dialog.
- [x] Trả về mã OTP khi người dùng bấm "Xác thực" hoặc `None` nếu bấm "Hủy" / đóng cửa sổ.

### Non-Functional
- [x] Thiết kế hiện đại, premium, sử dụng font chữ lớn và khoảng cách hợp lý.
- [x] Hoạt động mượt mà không làm đơ giao diện chính của Tkinter.

## Implementation Steps
1. [x] Tạo file mới `app/gui/otp_dialog.py`.
2. [x] Xây dựng class `OtpDialog` kế thừa từ `tk.Toplevel`:
   - Set các thuộc tính: `title("Xác thực 2 lớp")`, `transient(parent)`, `grab_set()`.
   - Căn giữa dialog so với màn hình hoặc cửa sổ chính.
3. [x] Tạo layout widget:
   - Một label tiêu đề lớn: "Xác thực 2 lớp" (font cỡ 16, bold).
   - Khung hướng dẫn màu nền nhẹ: Hướng dẫn mở ứng dụng Authenticator, đọc mã và điền vào ô dưới.
   - Một `tk.Entry` lớn để nhập mã (font chữ cỡ 20, căn giữa).
   - Ràng buộc nhập số bằng hàm validate Tkinter (`validate="key"`).
   - Một label đếm ngược: "⏱ Mã sẽ đổi sau: 30s".
   - Label báo lỗi màu đỏ (ẩn mặc định).
   - Frame chứa 2 nút: "Xác thực" (primary button) và "Hủy".
4. [x] Viết hàm countdown đệ quy bằng `self.after(1000, self._tick_countdown)` để cập nhật đồng hồ mỗi giây.
5. [x] Tạo phương thức `show(self)` để block tiến trình bằng `self.wait_window()` và trả về kết quả mã OTP khi đóng.

## Files to Create/Modify
- `app/gui/otp_dialog.py` - Tạo mới file chứa class `OtpDialog`.

## Test Criteria
- [x] Viết script test thủ công độc lập `tests/test_otp_dialog_ui.py` để khởi chạy riêng dialog Tkinter và xác minh các tương tác: chặn ký tự chữ, countdown đếm ngược, submit mã OTP, tắt dialog.

---
Next Phase: [Phase 03: Tích hợp controller & Xử lý bất đồng bộ](./phase-03-controller-integration.md)
