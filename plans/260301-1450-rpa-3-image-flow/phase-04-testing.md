# Phase 04: Testing & Tuning (Flow 3)
Status: ⬜ Pending
Dependencies: Phase 03

## Objective
Kiểm thử rủi ro của cơ chế 3 ảnh để đảm bảo hoạt động trơn tru trong mọi trường hợp, kể cả khi tool bị nhầm lẫn bởi hình nền trùng tên.

## Requirements
### Functional
- [ ] Chạy Tool và chụp đúng ảnh `ThanhCong_web.png` chứa "Số điện thoại:"
- [ ] Dừng mạng giữa chừng (Lag Simulator). Đảm bảo Tool in ra log "Timeout_Failed" chứ không Error.
- [ ] Đang bấm tự động ở giữa vòng quét 10 giây (Smart Wait) mà nhấn F10 (Tạm dừng) thì Tool phải Pause được. Tức là ko bị khoá Event Loop.
- [ ] So sánh tốc độ: Khi dùng flow cũ (mặc định tốn 2.5s mỗi số) vs flow mới (thời gian tính bằng mili-giây nếu máy khoẻ).

## Files
Không thay đổi code, chỉ test end-to-end.

---
🚀 Cột mốc hoàn thành.
