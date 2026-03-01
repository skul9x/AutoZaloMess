# Phase 01: Setup Configuration & Assets
Status: ⬜ Pending
Dependencies: None

## Objective
Tích hợp cấu hình nhận diện ảnh thứ 3 (ảnh chứa text "Số điện thoại:") vào hệ thống thông qua `image_config.json` và code base.

## Requirements
### Functional
- [ ] Bổ sung key `success_image_path` vào config của hệ thống.
- [ ] User cần tự tạo 2 file `ThanhCong_app.png` và `ThanhCong_web.png` lưu ở thư mục gốc.

## Implementation Steps
1. [ ] Đọc và sửa file `image_config.json`.
2. [ ] Thêm biến config mặc định vào file constants (nếu có tồn tại file này)
3. [ ] Viết hướng dẫn nhỏ trong log/terminal để nhắc user tự tạo file ảnh nếu file chưa tổn tại.

## Files to Modify
- `image_config.json` - Nạp file path cho ảnh báo thành công.

---
Next Phase: [Phase 02 (Logic Engine Refactoring)](./phase-02-logic.md)
