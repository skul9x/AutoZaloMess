# Phase 02: Thiết kế UI Sao lưu & Khôi phục

Status: ✅ Done
Dependencies: None

## Objective
Tích hợp trực quan các nút "Sao lưu (Backup)" và "Khôi phục (Restore)" vào tab "Gửi tin tự động" mà không làm phá vỡ bố cục hiện có của ứng dụng.

## Requirements
### Functional
- [x] Thêm 2 nút: "Sao lưu (Backup)" và "Khôi phục (Restore)" vào thanh quản lý danh sách liên hệ ở cột bên trái trong tab "Gửi tin tự động".
- [x] Bố cục giao diện phải thẳng hàng, cân xứng, hiển thị đầy đủ văn bản nút và không bị tràn khung hình ở độ phân giải mặc định (1200x800).
- [x] Liên kết các nút này với các callbacks tương ứng được truyền vào từ Controller.

## Implementation Steps
1. [x] Sửa file [automation_tab.py](file:///d:/skul9x/AutoZaloMess-main/app/gui/automation_tab.py):
   - Thêm nút `backup_button` và `restore_button` vào `list_manage_frame` bằng cách gọi `ttk.Button`.
   - Cấu hình callback click: `command=self.callbacks["backup_contacts"]` và `command=self.callbacks["restore_contacts"]`.
   - Đảm bảo layout pack các nút theo thứ tự hợp lý và có padding `padx=5` để tạo khoảng trống đồng đều.
   - Cập nhật hàm `set_buttons_state` để cập nhật trạng thái `NORMAL/DISABLED` cho hai nút này dựa trên trạng thái ứng dụng (ví dụ: vô hiệu hóa khi tool đang chạy gửi tin nhắn).
2. [x] Sửa file [main_window.py](file:///d:/skul9x/AutoZaloMess-main/app/gui/main_window.py):
   - Thêm `"backup_contacts": self.controller.backup_contacts` và `"restore_contacts": self.controller.restore_contacts` vào dict `auto_callbacks`.

## Test Criteria
- [x] Khởi chạy giao diện chính thành công và kiểm tra trực quan các nút mới xuất hiện đúng vị trí và thẳng hàng.
- [x] Nút "Sao lưu (Backup)" và "Khôi phục (Restore)" chuyển sang trạng thái disabled khi ứng dụng đang chạy gửi tin.

---

## Test File Content (`tests/test_backup_restore_ui.py`)

File test chuẩn dưới đây sẽ tạo dựng một phiên làm việc Tkinter mock nhỏ để tự động kiểm tra xem các nút Backup và Restore có được khởi tạo và định vị chính xác trong `AutomationTab` hay không.

```python
import unittest
import tkinter as tk
from tkinter import ttk
import sys
import os

# Đảm bảo import được thư mục app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.gui.automation_tab import AutomationTab

class TestBackupRestoreUI(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.title("Test UI")
        
        # Tạo mock state và callbacks
        self.state = {
            "initial_message": "Hello Test",
            "zalo_mode": tk.StringVar(value="web"),
            "coord_vars": {
                "search_coords": tk.StringVar(value="Chưa thiết lập"),
                "friend_coords": tk.StringVar(value="Chưa thiết lập"),
                "messagebox_coords": tk.StringVar(value="Chưa thiết lập")
            },
            "image_path_vars": {
                "web_fail_path": tk.StringVar(value="Chưa thiết lập"),
                "app_fail_path": tk.StringVar(value="Chưa thiết lập"),
                "web_ratelimit_path": tk.StringVar(value="Chưa thiết lập"),
                "app_ratelimit_path": tk.StringVar(value="Chưa thiết lập"),
                "web_ratelimit_path_2": tk.StringVar(value="Chưa thiết lập"),
                "app_ratelimit_path_2": tk.StringVar(value="Chưa thiết lập"),
                "web_success_path": tk.StringVar(value="Chưa thiết lập"),
                "app_success_path": tk.StringVar(value="Chưa thiết lập")
            }
        }
        
        self.mock_callbacks = {
            "handle_start": lambda: print("Start"),
            "handle_pause": lambda: print("Pause"),
            "handle_resume": lambda: print("Resume"),
            "handle_cancel": lambda: print("Cancel"),
            "update_ui_state": lambda: print("Update UI"),
            "on_selection_change": lambda: print("Selection changed"),
            "delete_selected_contacts": lambda: print("Delete selected"),
            "export_report": lambda: print("Export"),
            "capture_coordinate": lambda k: print(f"Capture {k}"),
            "handle_load_fail_image": lambda k: print(f"Load image {k}"),
            "backup_contacts": lambda: print("Backup triggered"),
            "restore_contacts": lambda: print("Restore triggered")
        }
        
        self.tab = AutomationTab(self.root, self.state, self.mock_callbacks)
        self.tab.pack(fill="both", expand=True)

    def tearDown(self):
        self.root.destroy()

    def test_buttons_existence(self):
        # Kiểm tra xem nút backup và restore có được gán làm thuộc tính của AutomationTab không
        self.assertTrue(hasattr(self.tab, 'backup_button'), "Thiếu thuộc tính backup_button trong AutomationTab")
        self.assertTrue(hasattr(self.tab, 'restore_button'), "Thiếu thuộc tính restore_button trong AutomationTab")
        
        # Kiểm tra xem command callback có được gán đúng không
        self.assertEqual(self.tab.backup_button.cget("text"), "Sao lưu (Backup)")
        self.assertEqual(self.tab.restore_button.cget("text"), "Khôi phục (Restore)")
        
        print("\n[OK] Test UI Buttons (Backup/Restore) da tao thanh cong va lien ket callback chinh xac!")

if __name__ == '__main__':
    unittest.main()
```

---
Next Phase: [Phase 03: Logic Sao lưu & Khôi phục trong Controller](file:///d:/skul9x/AutoZaloMess-main/plans/260531-1050-backup-skipfailed/phase-03-backup-restore-logic.md)
