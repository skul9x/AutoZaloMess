# Phase 01: Bỏ qua SĐT "Thất bại" khi gửi tin

Status: ✅ Done
Dependencies: None

## Objective
Khi thực hiện gửi tin nhắn hàng loạt bằng RPA, ứng dụng cần bỏ qua các số điện thoại có trạng thái là `"Thất bại"` (bên cạnh `"Thành công"` và `"Đã gửi trước đó"`) nhằm tránh gửi lại nhiều lần cho các số không tồn tại hoặc bị lỗi.

## Requirements
### Functional
- [x] Trong file `app/automation_logic.py`, cập nhật bộ lọc trạng thái bỏ qua trong hàm `run`.
- [x] Đảm bảo rằng khi bắt đầu hoặc tiếp tục tác vụ gửi tin, các liên hệ có trạng thái là `"Thất bại"` sẽ lập tức được bỏ qua mà không thực hiện bất kỳ thao tác RPA nào.

## Implementation Steps
1. [x] Sửa file [automation_logic.py](file:///d:/skul9x/AutoZaloMess-main/app/automation_logic.py) ở dòng 157:
   ```python
   # Trước:
   if contact["status"] in ("Đã gửi trước đó", "Thành công"):
       continue

   # Sau:
   if contact["status"] in ("Đã gửi trước đó", "Thành công", "Thất bại"):
       continue
   ```

## Test Criteria
- [x] Chạy file test `tests/test_skip_failed.py` thành công.
- [x] Đảm bảo số lượng liên hệ được gửi tin là chính xác, không bao gồm các số "Thất bại".

---

## Test File Content (`tests/test_skip_failed.py`)

Dưới đây là mã nguồn của file test chuẩn chỉ cho tác vụ của phase này, sử dụng cơ chế mock `pyautogui` để có thể chạy kiểm thử tự động trực tiếp thông qua terminal mà không ảnh hưởng tới chuột và bàn phím thật của người dùng.

```python
import unittest
from unittest.mock import MagicMock, patch
import queue
import sys
import os

# Đảm bảo import được thư mục app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.automation_logic import AutomationLogic

class TestSkipFailedContacts(unittest.TestCase):
    def setUp(self):
        self.comm_queue = queue.Queue()
        self.logic = AutomationLogic(self.comm_queue)
        
    @patch('app.automation_logic.pyautogui')
    @patch('app.automation_logic.pyperclip')
    def test_run_skips_failed_contacts(self, mock_pyperclip, mock_pyautogui):
        # Thiết lập danh sách liên hệ thử nghiệm
        contacts = [
            {"phone": "0987654321", "name": "Nguyễn Văn A", "status": "Chờ gửi"},
            {"phone": "0912345678", "name": "Trần Thị B", "status": "Thành công"},
            {"phone": "0909090909", "name": "Lê Văn C", "status": "Thất bại"},
            {"phone": "0888888888", "name": "Phạm Văn D", "status": "Đã gửi trước đó"}
        ]
        
        # Mock hàm process_contact để kiểm tra số lần được gọi thực sự
        self.logic.process_contact = MagicMock(return_value="success")
        
        # Rút ngắn thời gian sleep trong test xuống 0 để chạy nhanh
        self.logic.controlled_sleep = MagicMock()
        
        # Chạy logic gửi tin
        params = {
            "search_coords": (100, 200),
            "friend_coords": (150, 250),
            "messagebox_coords": (200, 300),
            "fail_image_path": "dummy_fail.png",
            "ratelimit_image_path": "dummy_ratelimit.png",
            "success_image_path": "dummy_success.png"
        }
        
        self.logic.run(contacts, "Xin chào {name}", params)
        
        # Kiểm tra: process_contact chỉ được gọi đúng 1 lần cho "Nguyễn Văn A" (Chờ gửi)
        # Các số "Thành công", "Thất bại" và "Đã gửi trước đó" phải bị bỏ qua (skip)
        self.assertEqual(self.logic.process_contact.call_count, 1)
        self.logic.process_contact.assert_called_once_with("0987654321", "Nguyễn Văn A", "Xin chào {name}", params)
        
        # Đọc hàng đợi queue để xác nhận trạng thái log
        logs = []
        statuses = []
        while not self.comm_queue.empty():
            msg = self.comm_queue.get()
            if msg[0] == "log":
                logs.append(msg[1])
            elif msg[0] == "status":
                statuses.append(msg)
                
        # Xác nhận status của liên hệ đầu tiên được cập nhật là "Thành công" do mock trả về "success"
        self.assertIn(("status", 0, "Thành công"), statuses)
        
        print("\n[OK] Test Skip Failed Contacts chạy thành công!")

if __name__ == '__main__':
    unittest.main()
```

---
Next Phase: [Phase 02: Thiết kế UI Sao lưu & Khôi phục](file:///d:/skul9x/AutoZaloMess-main/plans/260531-1050-backup-skipfailed/phase-02-backup-restore-ui.md)
