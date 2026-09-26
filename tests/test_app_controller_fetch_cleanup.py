import sys
from pathlib import Path
import queue
from unittest.mock import MagicMock, patch, call
import pytest

# Ensure app module can be found when running pytest directly on this file
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.controllers.app_controller import AppController


class TestAppControllerFetchCleanup:
    """
    Comprehensive test suite for Phase 02: Controller Integration & Safe Cleanup.
    Covers:
      1. Target search across communes and multiple pages with unique integer ID extraction.
      2. Temporary injection into active plan (nhap_bo_sung_doi_tuong).
      3. Contact extraction from appointment list (get_danh_sach_hen_tiem):
         - Unmasked phone extraction.
         - Name normalization (TEN_ME or fallback PH bé {HO_TEN}).
         - Skipping missing phones and deduplicating phone numbers.
         - Sent status synchronization with sent_database.
      4. Strict cleanup guarantee via try ... finally:
         - Only injected targets are deleted via xoa_doi_tuong_hen_tiem.
         - Pre-existing plan appointments are strictly preserved.
         - Cleanup is guaranteed even if an unexpected exception occurs during parsing.
         - Cleanup resilience when network/error occurs before contact extraction.
      5. Graceful handling of empty search results.
    """

    def _setup_controller(self, xa_ids=None, sent_phones=None):
        mock_window = MagicMock()
        mock_queue = queue.Queue()
        mock_window.comm_queue = mock_queue

        mock_storage = MagicMock()
        mock_storage.load_xa_ids.return_value = xa_ids or ["1062901"]
        mock_storage.load_sent_database.return_value = sent_phones or set()

        mock_services = {
            "storage": mock_storage,
            "contacts": MagicMock(),
            "report": MagicMock()
        }

        mock_vncdc_client = MagicMock()
        controller = AppController(mock_window, mock_services, MagicMock())
        controller.vncdc_client = mock_vncdc_client
        controller.vncdc_ke_hoach_id = 9403580
        controller.vncdc_profile = {"tinh_id": 106, "huyen_id": 10605, "thon_id": -1}

        return controller, mock_vncdc_client, mock_queue

    @patch("time.sleep", return_value=None)
    @patch("threading.Thread")
    def test_full_fetch_and_cleanup_orchestration(self, mock_thread, mock_sleep):
        controller, mock_client, mock_queue = self._setup_controller(
            xa_ids=["1062901", "1062902"],
            sent_phones={"0374441067"}
        )

        # Mock multi-commune and multi-page search results
        def mock_search_doi_tuong(payload):
            xa_id = payload.get("XA_ID")
            page = payload.get("PageNumber")
            if xa_id == "1062901" and page == "1":
                return {
                    "total_page": 2,
                    "items": [
                        {"doi_tuong_id": "81126724,0", "ho_ten": "ĐẶNG ĐÌNH NGUYÊN"},
                        {"doi_tuong_id": "81123344", "ho_ten": "NGUYỄN VĂN A"},
                    ]
                }
            elif xa_id == "1062901" and page == "2":
                return {
                    "total_page": 2,
                    "items": [
                        {"doi_tuong_id": 81118298, "ho_ten": "TRẦN VĂN B"},
                    ]
                }
            elif xa_id == "1062902" and page == "1":
                return {
                    "total_page": 1,
                    "items": [
                        # Duplicate of 81126724 from commune 1
                        {"doi_tuong_id": "81126724", "ho_ten": "ĐẶNG ĐÌNH NGUYÊN"},
                        {"doi_tuong_id": "81105557", "ho_ten": "HOÀNG THỊ C"},
                    ]
                }
            return {"total_page": 1, "items": []}

        mock_client.search_doi_tuong.side_effect = mock_search_doi_tuong
        mock_client.nhap_bo_sung_doi_tuong.return_value = {"Status": 2, "success": True}

        # Appointments in plan: 4 injected targets + 1 pre-existing target
        mock_client.get_danh_sach_hen_tiem.return_value = [
            {
                "DOI_TUONG_ID": 81126724,
                "DIEN_THOAI": "0374441067",
                "TEN_ME": "(Mẹ) SẦM THỊ HOÀI",
                "HO_TEN": "ĐẶNG ĐÌNH NGUYÊN",
                "KE_HOACH_TIEM_CHI_TIET_ID": 84020986,
                "THOI_GIAN_TIEM": 0,
            },
            {
                "DOI_TUONG_ID": 81123344,
                "DIEN_THOAI": "0987654321",
                "TEN_ME": "",  # Empty mother name -> fallback to PH bé HO_TEN
                "HO_TEN": "NGUYỄN VĂN A",
                "KE_HOACH_TIEM_CHI_TIET_ID": 84020987,
                "THOI_GIAN_TIEM": 0,
            },
            {
                "DOI_TUONG_ID": 81118298,
                "DIEN_THOAI": "",  # Missing phone -> must be filtered out
                "TEN_ME": "LÊ THỊ C",
                "HO_TEN": "TRẦN VĂN B",
                "KE_HOACH_TIEM_CHI_TIET_ID": 84020988,
                "THOI_GIAN_TIEM": 0,
            },
            {
                "DOI_TUONG_ID": 81105557,
                "DIEN_THOAI": "0987654321",  # Duplicate phone (same as 81123344) -> deduplicated
                "TEN_ME": "PHẠM THỊ D",
                "HO_TEN": "HOÀNG THỊ C",
                "KE_HOACH_TIEM_CHI_TIET_ID": 84020989,
                "THOI_GIAN_TIEM": 0,
            },
            {
                "DOI_TUONG_ID": 99999999,  # PRE-EXISTING target in plan, not injected during this session
                "DIEN_THOAI": "0911222333",
                "TEN_ME": "ĐỖ THỊ PRE",
                "HO_TEN": "BÉ PRE",
                "KE_HOACH_TIEM_CHI_TIET_ID": 84099999,
                "THOI_GIAN_TIEM": 0,
            },
        ]
        mock_client.xoa_doi_tuong_hen_tiem.return_value = True

        # Trigger fetch
        controller.handle_vncdc_fetch("01/01/2026", "31/01/2026")

        # Execute thread body synchronously
        assert mock_thread.called
        fetch_task_fn = mock_thread.call_args[1]["target"]
        fetch_task_fn()

        # 1. Verify target injection
        mock_client.nhap_bo_sung_doi_tuong.assert_called_once()
        inj_call = mock_client.nhap_bo_sung_doi_tuong.call_args
        assert inj_call.kwargs.get("ke_hoach_id") == 9403580
        # Unique integer IDs only
        assert inj_call.kwargs.get("doi_tuong_ids") == [81126724, 81123344, 81118298, 81105557]

        # 2. Verify appointment retrieval
        mock_client.get_danh_sach_hen_tiem.assert_called_once_with(9403580)

        # 3. Verify strict cleanup guarantee
        # Injected targets must all be deleted
        expected_cleanup_calls = [
            call(9403580, 81126724, 84020986),
            call(9403580, 81123344, 84020987),
            call(9403580, 81118298, 84020988),
            call(9403580, 81105557, 84020989),
        ]
        mock_client.xoa_doi_tuong_hen_tiem.assert_has_calls(expected_cleanup_calls, any_order=True)
        assert mock_client.xoa_doi_tuong_hen_tiem.call_count == 4

        # Pre-existing target 99999999 must NEVER have been deleted
        for c in mock_client.xoa_doi_tuong_hen_tiem.call_args_list:
            assert c.args[1] != 99999999
            assert c.args[2] != 84099999

        # 4. Verify state and queue output
        assert controller.is_fetching is False
        msgs = []
        while not mock_queue.empty():
            msgs.append(mock_queue.get())

        success_msgs = [m for m in msgs if m[0] == "fetch_success"]
        assert len(success_msgs) == 1
        _, new_contacts, added, skipped = success_msgs[0]

        # 2 unique contacts extracted (1 skipped because in sent_database, 1 added)
        assert len(new_contacts) == 2
        assert added == 1
        assert skipped == 1

        # Check contact 1: mother name formatted properly, status is "Đã gửi trước đó"
        assert new_contacts[0]["phone"] == "0374441067"
        assert new_contacts[0]["name"] == "Sầm Thị Hoài"
        assert new_contacts[0]["status"] == "Đã gửi trước đó"

        # Check contact 2: fallback to child name formatted as "Ph Bé Nguyễn Văn A", status "Chờ gửi"
        assert new_contacts[1]["phone"] == "0987654321"
        assert new_contacts[1]["name"] == "Ph Bé Nguyễn Văn A"
        assert new_contacts[1]["status"] == "Chờ gửi"

    @patch("time.sleep", return_value=None)
    @patch("threading.Thread")
    def test_cleanup_guarantee_on_exception_during_parsing(self, mock_thread, mock_sleep):
        controller, mock_client, mock_queue = self._setup_controller(
            xa_ids=["1062901"]
        )

        mock_client.search_doi_tuong.return_value = {
            "total_page": 1,
            "items": [{"doi_tuong_id": "81126724", "ho_ten": "BÉ LỖI"}]
        }
        mock_client.nhap_bo_sung_doi_tuong.return_value = {"Status": 2, "success": True}
        mock_client.get_danh_sach_hen_tiem.return_value = [
            {
                "DOI_TUONG_ID": 81126724,
                "DIEN_THOAI": "0374441067",
                "TEN_ME": "Mẹ Lỗi",
                "KE_HOACH_TIEM_CHI_TIET_ID": 84020986,
            }
        ]
        mock_client.xoa_doi_tuong_hen_tiem.return_value = True

        # Simulate unexpected crash during contact parsing (e.g. clean_contact_name_and_role raises Exception)
        with patch("app.controllers.app_controller.clean_contact_name_and_role", side_effect=ValueError("Simulated parsing crash")):
            controller.handle_vncdc_fetch("01/01/2026", "31/01/2026")
            fetch_task_fn = mock_thread.call_args[1]["target"]
            fetch_task_fn()

        # Strict cleanup guarantee: xoa_doi_tuong_hen_tiem MUST still be invoked in finally block
        mock_client.xoa_doi_tuong_hen_tiem.assert_called_once_with(9403580, 81126724, 84020986)
        assert controller.is_fetching is False

        # Queue must receive fetch_error
        msgs = []
        while not mock_queue.empty():
            msgs.append(mock_queue.get())

        error_msgs = [m for m in msgs if m[0] == "fetch_error"]
        assert len(error_msgs) == 1
        assert "Simulated parsing crash" in error_msgs[0][1]

    @patch("time.sleep", return_value=None)
    @patch("threading.Thread")
    def test_cleanup_resilience_when_error_occurs_before_appointment_query(self, mock_thread, mock_sleep):
        controller, mock_client, mock_queue = self._setup_controller(
            xa_ids=["1062901"]
        )

        mock_client.search_doi_tuong.return_value = {
            "total_page": 1,
            "items": [{"doi_tuong_id": "81126724", "ho_ten": "BÉ TEST"}]
        }
        mock_client.nhap_bo_sung_doi_tuong.return_value = {"Status": 2, "success": True}

        # First call inside try block raises Network Error
        # Second call inside finally block resolves appointment CT_ID for cleanup
        mock_client.get_danh_sach_hen_tiem.side_effect = [
            ConnectionResetError("Connection dropped while fetching appointments"),
            [{"DOI_TUONG_ID": 81126724, "KE_HOACH_TIEM_CHI_TIET_ID": 84020986, "THOI_GIAN_TIEM": 0}]
        ]
        mock_client.xoa_doi_tuong_hen_tiem.return_value = True

        controller.handle_vncdc_fetch("01/01/2026", "31/01/2026")
        fetch_task_fn = mock_thread.call_args[1]["target"]
        fetch_task_fn()

        # Injected target must still be cleaned up via resolution in finally block
        mock_client.xoa_doi_tuong_hen_tiem.assert_called_once_with(9403580, 81126724, 84020986)
        assert controller.is_fetching is False

        msgs = []
        while not mock_queue.empty():
            msgs.append(mock_queue.get())
        error_msgs = [m for m in msgs if m[0] == "fetch_error"]
        assert len(error_msgs) == 1
        assert "Connection dropped" in error_msgs[0][1]

    @patch("time.sleep", return_value=None)
    @patch("threading.Thread")
    def test_empty_search_results_no_injection_or_cleanup(self, mock_thread, mock_sleep):
        controller, mock_client, mock_queue = self._setup_controller(
            xa_ids=["1062901"]
        )

        mock_client.search_doi_tuong.return_value = {"total_page": 1, "items": []}

        controller.handle_vncdc_fetch("01/01/2026", "31/01/2026")
        fetch_task_fn = mock_thread.call_args[1]["target"]
        fetch_task_fn()

        # Neither injection nor cleanup should be called
        mock_client.nhap_bo_sung_doi_tuong.assert_not_called()
        mock_client.get_danh_sach_hen_tiem.assert_not_called()
        mock_client.xoa_doi_tuong_hen_tiem.assert_not_called()

        assert controller.is_fetching is False
        msgs = []
        while not mock_queue.empty():
            msgs.append(mock_queue.get())

        success_msgs = [m for m in msgs if m[0] == "fetch_success"]
        assert len(success_msgs) == 1
        assert success_msgs[0][1] == []
        assert success_msgs[0][2] == 0
        assert success_msgs[0][3] == 0
