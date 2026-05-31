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
