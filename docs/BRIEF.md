# 💡 BRIEF: Nâng cấp AutoZaloMess_1.3 (Flow 3 Ảnh)

**Ngày tạo:** 2026-03-01
**Brainstorm cùng:** User

---

## 1. VẤN ĐỀ CẦN GIẢI QUYẾT
- Hiện tại tool Zalo Mess sử dụng `time.sleep(2.5)` (fixed sleep) sau khi gõ số điện thoại, sau đó kiểm tra 2 ảnh lỗi (Rate Limit và Không tìm thấy). 
- Cách này gây ra 2 nhược điểm:
  1. Thiếu ổn định khi mạng lag (nếu sau 2.5s ảnh lỗi mới hiện ra thì tool sẽ bỏ qua và click nhầm).
  2. Lãng phí thời gian nếu mạng nhanh (ảnh hiện ra ngay lập tức nhưng tool vẫn phải đợi đủ 2.5s).
- Không có cơ chế xác nhận 100% người dùng tiêm đã được tìm thấy (mới chỉ dùng phương pháp loại trừ).

## 2. GIẢI PHÁP ĐỀ XUẤT (Flow 3 Ảnh)
- **Thêm ảnh thứ 3:** Ảnh có chứa đoạn text `"Số điện thoại:"`. Đoạn text này xuất hiện cố định khi Zalo trả về kết quả tìm kiếm thành công cho một số điện thoại lạ. Khoanh vùng thật chuẩn chỉ dòng text này để đảm bảo độ chính xác (không lấy cả ảnh avatar hay số đuôi).
- **Thay đổi Logic:** Bỏ hoàn toàn `sleep(2.5)`. Thay vào đó, tạo một vòng lặp (Smart Wait) liên tục quét màn hình tìm **1 trong 3 trạng thái**:
  1. `[Ảnh Lỗi 1]` - Giới hạn tìm kiếm -> DỪNG TOOL.
  2. `[Ảnh Lỗi 2]` - Không tìm thấy số -> SKIP.
  3. `[Ảnh Thứ 3]` - Chữ "Số điện thoại:" -> CLICK GỬI TIN.
- Nếu sau một thời gian tối đa (Timeout, ví dụ 10s) mà cả 3 ảnh đều không xuất hiện (có thể rớt mạng), đánh dấu lỗi Timeout và Skip.

## 3. TÍNH NĂNG & THAY ĐỔI CẦN THIẾT

### 🚀 MVP (Bắt buộc có):
- [ ] Bổ sung cơ chế Load `Ảnh Thứ 3` (thành công) vào code. `coords_config.json` hoặc `image_config.json` cần được cập nhật.
- [ ] Viết lại hàm `wait_for_any_image` trong `automation_logic.py`, có khả năng nhận array ảnh và trả về kết quả ảnh nào xuất hiện đầu tiên.
- [ ] Sửa lại luồng `process_contact` ở Bước 3 và Bước 4 theo kết quả của hàm mới.

## 4. BƯỚC TIẾP THEO
→ Chạy `/plan` để lên thiết kế chi tiết (kiến trúc hàm mới và cách thức đọc cấu hình ảnh thứ 3).
