# Phase 03: UI & Controller Update
Status: ⬜ Pending
Dependencies: Phase 02

## Objective
Luồng UI và luồng Thread gửi tin hiện tại nhận tham số ảnh từ `params`. Cần bổ sung việc đọc "Ảnh thứ 3" từ file cấu hình và truyền xuống cho logic xử lý. 

## Requirements
### Functional
- [ ] Khi khởi tạo `AppController` -> `start_automation`, phải lấy thêm key `success_image_path` truyền xuống class con.
- [ ] Đảm bảo giao diện ở `automation_tab.py` cho phép người dùng Load thêm hoặc Verify rằng ảnh "Thành công" đã được cài đặt (nếu App cũ đã thiết kế UI chọn ảnh lỗi, ta cần thêm ô chọn ảnh Success).

## Files to Modify
- `app/controllers/app_controller.py` - Chỗ trigger nút Bắt đầu.
- `app/gui/automation_tab.py` - Cập nhật Frame chứa config hình ảnh.

---
Next Phase: [Phase 04 (Testing and Tuning)](./phase-04-testing.md)
