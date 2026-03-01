# Phase 02: Logic Engine Refactoring (Flow 3)
Status: ⬜ Pending
Dependencies: Phase 01

## Objective
Thay đổi hoàn toàn Core `class AutomationLogic` trong file `app/automation_logic.py` để sử dụng cấu trúc phân nhánh Event-driven bằng việc wait hình ảnh.

## Requirements
### Functional
- [ ] Xoá đoạn code fixed wait `time.sleep(2.5)` sau đoạn code gõ số điện thoại.
- [ ] Viết hàm `wait_for_any_image` dùng vòng lặp thời gian kết hợp Check Image liên tục, có hỗ trợ pause_event. Thang đo confidence có thể giảm nhẹ.
- [ ] Tuỳ biến `process_contact`: Đạt được logic ngã 3 (Limit, Failed, Success, và Timeout Timeout > 10s).
- [ ] Trả về status rõ ràng để UI cập nhật lên listbox.

## Files to Modify
- `app/automation_logic.py`

---
Next Phase: [Phase 03 (UI & Controller Integration)](./phase-03-controller.md)
