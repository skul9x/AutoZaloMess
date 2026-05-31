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
        
        print("\n[OK] Test Skip Failed Contacts completed successfully!")

if __name__ == '__main__':
    unittest.main()
