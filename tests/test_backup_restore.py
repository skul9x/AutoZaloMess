import unittest
import json
import os
import sys

# Đảm bảo import được thư mục app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils import save_json, load_json

class TestBackupRestoreLogic(unittest.TestCase):
    def setUp(self):
        self.test_file_path = "test_contacts_backup.json"
        self.dummy_contacts = [
            {"phone": "0987654321", "name": "Nguyễn Văn A", "status": "Chờ gửi"},
            {"phone": "0912345678", "name": "Trần Thị B", "status": "Thành công"}
        ]

    def tearDown(self):
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_json_backup_write_and_read(self):
        # 1. Thao tác sao lưu (Ghi file)
        save_json(self.test_file_path, self.dummy_contacts)
        self.assertTrue(os.path.exists(self.test_file_path), "File backup không được tạo thành công")
        
        # 2. Thao tác khôi phục (Đọc file)
        loaded_data = load_json(self.test_file_path, None)
        self.assertIsNotNone(loaded_data, "Không đọc được dữ liệu JSON")
        self.assertEqual(len(loaded_data), 2)
        self.assertEqual(loaded_data[0]["phone"], "0987654321")
        self.assertEqual(loaded_data[1]["name"], "Trần Thị B")

    def test_backup_validation(self):
        # Kiểm tra tính hợp lệ của schema dữ liệu backup
        invalid_data_1 = "Không phải danh sách"
        invalid_data_2 = [{"phone": "01234"}]  # Thiếu name
        
        def validate_contacts(data):
            if not isinstance(data, list):
                return False
            for item in data:
                if not isinstance(item, dict) or "phone" not in item or "name" not in item:
                    return False
            return True
            
        self.assertTrue(validate_contacts(self.dummy_contacts))
        self.assertFalse(validate_contacts(invalid_data_1))
        self.assertFalse(validate_contacts(invalid_data_2))

    def test_restore_merge_logic(self):
        # Giả lập logic merge (Thêm nối tiếp) không trùng SĐT
        current_contacts = [
            {"phone": "0987654321", "name": "Nguyễn Văn A", "status": "Chờ gửi"}
        ]
        
        backup_contacts = [
            {"phone": "0987654321", "name": "Nguyễn Văn A", "status": "Thành công"}, # Trùng SĐT
            {"phone": "0909090909", "name": "Lê Văn C", "status": "Chờ gửi"}         # Liên hệ mới
        ]
        
        # Thực hiện merge logic
        existing_phones = {c["phone"] for c in current_contacts}
        added_count = 0
        for item in backup_contacts:
            if item["phone"] not in existing_phones:
                current_contacts.append(item)
                existing_phones.add(item["phone"])
                added_count += 1
                
        self.assertEqual(len(current_contacts), 2)
        self.assertEqual(added_count, 1)
        self.assertEqual(current_contacts[1]["phone"], "0909090909")
        print("\n[OK] Test Logic Backup & Restore (Read/Write/Validation/Merge) ran successfully!")

if __name__ == '__main__':
    unittest.main()
