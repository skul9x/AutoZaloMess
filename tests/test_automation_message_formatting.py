import queue
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.automation_logic import AutomationLogic
from app.controllers.app_controller import AppController


class TestAutomationMessageFormatting(unittest.TestCase):
    def setUp(self):
        self.comm_queue = queue.Queue()
        self.logic = AutomationLogic(self.comm_queue)
        # Disable sleep delays in automation for fast test execution
        self.logic.controlled_sleep = MagicMock()

    @patch("app.automation_logic.pyperclip")
    @patch("app.automation_logic.pyautogui")
    def test_automation_logic_end_to_end_formatting(self, mock_pyautogui, mock_pyperclip):
        """Verify process_contact and run formatting for mother, grandmother, father, and child fallback."""
        template = "Phòng tiêm Vắc Xin Quế Võ mời mẹ {name} đưa bé đi tiêm phòng."
        params = {
            "search_coords": (10, 20),
            "friend_coords": (30, 40),
            "messagebox_coords": (50, 60),
            "fail_image_path": "fail.png",
            "ratelimit_image_path": "limit.png",
            "success_image_path": "success.png",
        }

        # Mock wait_for_any_image to succeed
        self.logic.wait_for_any_image = MagicMock(return_value=("success", (100, 100)))

        copied_messages = []
        mock_pyperclip.copy.side_effect = lambda msg: copied_messages.append(msg)

        contacts = [
            {"name": "Nguyễn Thị Linh", "phone": "0912345678", "status": "Chờ gửi", "is_mother": True, "role": "mẹ"},
            {"name": "Trần Thị Mai", "phone": "0987654321", "status": "Chờ gửi", "is_mother": False, "role": "bà"},
            {"name": "Nguyễn Văn Tuấn", "phone": "0901234567", "status": "Chờ gửi", "is_mother": False, "role": "bố"},
            {"name": "phụ huynh bé Nguyễn Văn An", "phone": "0934567890", "status": "Chờ gửi", "is_mother": False, "role": "phụ huynh"},
        ]

        # Execute run with full contact list
        self.logic.run(contacts, template, params)

        # 1. Verify all 4 messages were generated and copied to clipboard
        self.assertEqual(len(copied_messages), 4)

        # 2. Verify mother greeting uses short name "Linh" with "mẹ"
        self.assertIn("mời mẹ Linh", copied_messages[0])
        self.assertNotIn("Nguyễn Thị Linh", copied_messages[0])

        # 3. Verify grandmother greeting uses short name "Mai" with "bà"
        self.assertIn("mời bà Mai", copied_messages[1])
        self.assertNotIn("Trần Thị Mai", copied_messages[1])
        self.assertNotIn("mẹ Mai", copied_messages[1])

        # 4. Verify father greeting uses short name "Tuấn" with "bố"
        self.assertIn("mời bố Tuấn", copied_messages[2])
        self.assertNotIn("Nguyễn Văn Tuấn", copied_messages[2])
        self.assertNotIn("mẹ Tuấn", copied_messages[2])

        # 5. Verify child fallback preserves full phrase "mời phụ huynh bé Nguyễn Văn An"
        self.assertIn("mời phụ huynh bé Nguyễn Văn An", copied_messages[3])
        self.assertNotIn("mẹ", copied_messages[3])

        # 6. Verify logging displays both full contact name and the formatted outgoing greeting
        logs = []
        while not self.comm_queue.empty():
            item = self.comm_queue.get()
            if item[0] == "log":
                logs.append(item[1])

        # Mother: full name in log, greeting in log
        self.assertTrue(any("Nguyễn Thị Linh" in log for log in logs))
        self.assertTrue(any("mời mẹ Linh" in log for log in logs))

        # Grandmother: full name in log, greeting in log
        self.assertTrue(any("Trần Thị Mai" in log for log in logs))
        self.assertTrue(any("mời bà Mai" in log for log in logs))

        # Father: full name in log, greeting in log
        self.assertTrue(any("Nguyễn Văn Tuấn" in log for log in logs))
        self.assertTrue(any("mời bố Tuấn" in log for log in logs))

        # Child fallback: full phrase in log
        self.assertTrue(any("phụ huynh bé Nguyễn Văn An" in log for log in logs))

    @patch("app.automation_logic.pyautogui")
    def test_automation_logic_error_safety(self, mock_pyautogui):
        """Verify error safety in try...except block for invalid templates."""
        invalid_template = "Xin chào {invalid_variable}"
        params = {"search_coords": (10, 20)}
        self.logic.running = True

        result = self.logic.process_contact("0912345678", "Nguyễn Thị Linh", invalid_template, params)
        self.assertEqual(result, "error")

    @patch("threading.Thread")
    def test_controller_stores_contact_role_and_full_name(self, mock_thread):
        """Verify AppController correctly parses role and stores full name from VNCDC appointment list."""
        mock_window = MagicMock()
        mock_queue = queue.Queue()
        mock_window.comm_queue = mock_queue

        mock_storage = MagicMock()
        mock_storage.load_xa_ids.return_value = ["1062901"]
        mock_storage.load_sent_database.return_value = set()

        mock_services = {
            "storage": mock_storage,
            "contacts": MagicMock(),
            "report": MagicMock()
        }

        mock_vncdc_client = MagicMock()
        # Mock search returning target objects
        mock_vncdc_client.search_doi_tuong.return_value = {
            "page_size": 10,
            "total_page": 1,
            "items": [
                {"doi_tuong_id": "1001,0"},
                {"doi_tuong_id": "1002,0"},
                {"doi_tuong_id": "1003,0"},
                {"doi_tuong_id": "1004,0"},
            ]
        }
        mock_vncdc_client.nhap_bo_sung_doi_tuong.return_value = True

        # Mock appointment response with diverse family relationships
        mock_vncdc_client.get_danh_sach_hen_tiem.return_value = [
            {
                "DOI_TUONG_ID": "1001",
                "KE_HOACH_TIEM_CHI_TIET_ID": 201,
                "DIEN_THOAI": "0912345678",
                "TEN_ME": "Nguyễn Thị Linh",
                "HO_TEN": "Nguyễn Văn B",
            },
            {
                "DOI_TUONG_ID": "1002",
                "KE_HOACH_TIEM_CHI_TIET_ID": 202,
                "DIEN_THOAI": "0987654321",
                "TEN_ME": "(Bà) Trần Thị Mai",
                "HO_TEN": "Trần Văn C",
            },
            {
                "DOI_TUONG_ID": "1003",
                "KE_HOACH_TIEM_CHI_TIET_ID": 203,
                "DIEN_THOAI": "0901234567",
                "TEN_ME": "(Bố) Nguyễn Văn Tuấn",
                "HO_TEN": "Nguyễn Văn D",
            },
            {
                "DOI_TUONG_ID": "1004",
                "KE_HOACH_TIEM_CHI_TIET_ID": 204,
                "DIEN_THOAI": "0934567890",
                "TEN_ME": "",
                "HO_TEN": "Nguyễn Văn An",
            },
        ]
        mock_vncdc_client.xoa_doi_tuong_khoi_ke_hoach.return_value = True

        controller = AppController(mock_window, mock_services, MagicMock())
        controller.vncdc_client = mock_vncdc_client
        controller.vncdc_ke_hoach_id = 9999

        # Trigger fetch task
        controller.handle_vncdc_fetch("01/01/2026", "02/01/2026")
        self.assertTrue(mock_thread.called)
        fetch_fn = mock_thread.call_args[1]["target"]
        fetch_fn()

        # Check fetch_success message in queue
        success_msg = None
        while not mock_queue.empty():
            msg = mock_queue.get()
            if msg[0] == "fetch_success":
                success_msg = msg
                break

        self.assertIsNotNone(success_msg, "fetch_success was not emitted")
        new_contacts = success_msg[1]
        self.assertEqual(len(new_contacts), 4)

        # 1. Mother check: Full name stored, role is 'mẹ', is_mother is True
        c0 = new_contacts[0]
        self.assertEqual(c0["name"], "Nguyễn Thị Linh")
        self.assertEqual(c0["role"], "mẹ")
        self.assertTrue(c0["is_mother"])

        # 2. Grandmother check: Full name stored, role is 'bà', is_mother is False
        c1 = new_contacts[1]
        self.assertEqual(c1["name"], "Trần Thị Mai")
        self.assertEqual(c1["role"], "bà")
        self.assertFalse(c1["is_mother"])

        # 3. Father check: Full name stored, role is 'bố', is_mother is False
        c2 = new_contacts[2]
        self.assertEqual(c2["name"], "Nguyễn Văn Tuấn")
        self.assertEqual(c2["role"], "bố")
        self.assertFalse(c2["is_mother"])

        # 4. Child fallback check: Full phrase stored, role is 'phụ huynh', is_mother is False
        c3 = new_contacts[3]
        self.assertEqual(c3["name"], "phụ huynh bé Nguyễn Văn An")
        self.assertEqual(c3["role"], "phụ huynh")
        self.assertFalse(c3["is_mother"])

    def test_table_row_and_restore_data_integrity(self):
        """Verify GUI table row receives full name and restore contacts retains role."""
        mock_window = MagicMock()
        mock_tab = MagicMock()
        mock_window.automation_tab = mock_tab

        controller = AppController(mock_window, {"storage": MagicMock(), "contacts": MagicMock(), "report": MagicMock()}, MagicMock())
        controller.contacts = [
            {"name": "Nguyễn Thị Linh", "phone": "0912345678", "status": "Chờ gửi", "is_mother": True, "role": "mẹ"},
            {"name": "Trần Thị Mai", "phone": "0987654321", "status": "Chờ gửi", "is_mother": False, "role": "bà"},
        ]

        # Update contact list in GUI
        controller.update_contact_list()

        # Verify insert_contact_row was called with full names
        call_args_list = mock_tab.insert_contact_row.call_args_list
        self.assertEqual(len(call_args_list), 2)
        self.assertEqual(call_args_list[0][0][1]["name"], "Nguyễn Thị Linh")
        self.assertEqual(call_args_list[1][0][1]["name"], "Trần Thị Mai")

        # Test restore data integrity
        backup_data = [
            {"name": "Nguyễn Văn Tuấn", "phone": "0901234567", "status": "Chờ gửi", "is_mother": False, "role": "bố"}
        ]
        with patch("app.controllers.app_controller.filedialog.askopenfilename", return_value="dummy.json"), \
             patch("app.controllers.app_controller.load_json", return_value=backup_data), \
             patch("app.controllers.app_controller.messagebox.askyesnocancel", return_value=True), \
             patch("app.controllers.app_controller.messagebox.showinfo"):
            controller.restore_contacts()

        self.assertEqual(len(controller.contacts), 1)
        restored = controller.contacts[0]
        self.assertEqual(restored["name"], "Nguyễn Văn Tuấn")
        self.assertEqual(restored["role"], "bố")
        self.assertFalse(restored["is_mother"])


if __name__ == "__main__":
    unittest.main()
