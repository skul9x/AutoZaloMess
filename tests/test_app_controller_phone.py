import pytest
import queue
import time
from unittest.mock import MagicMock, patch
from app.controllers.app_controller import AppController

class TestAppControllerPhone:
    @patch("threading.Thread")
    def test_handle_vncdc_fetch_obtains_phone_numbers(self, mock_thread):
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
        
        # Mock search result containing 1 target without phone number
        search_res = {
            "page_size": 10,
            "page_number": 1,
            "total_item": 1,
            "total_page": 1,
            "page_data_count": 1,
            "items": [
                {
                    "doi_tuong_id": "78875959,0",
                    "stt": "1",
                    "ho_ten": "M - Nguyễn Thị Tuyết Mai",
                    "ma_doi_tuong": "106290120260115",
                    "ngay_sinh": "12/06/2026",
                    "nguoi_cham_soc": "Nguyễn Thị Tuyết Mai",
                    "dia_chi": "Can Vũ, Phường Quế Võ, Bắc Ninh",
                }
            ],
            "raw_html": "<html></html>"
        }
        mock_vncdc_client.search_doi_tuong.return_value = search_res
        mock_vncdc_client.get_doi_tuong_phone.return_value = "0365240748"

        controller = AppController(mock_window, mock_services, MagicMock())
        controller.vncdc_client = mock_vncdc_client
        controller.vncdc_ke_hoach_id = 9023889

        # Trigger fetch
        controller.handle_vncdc_fetch("07/06/2026", "14/06/2026")

        # Verify that thread was started
        assert mock_thread.called
        fetch_task_fn = mock_thread.call_args[1]["target"]
        
        # Run the thread target function synchronously in the test
        fetch_task_fn()

        # Check client calls
        mock_vncdc_client.search_doi_tuong.assert_called_once()
        mock_vncdc_client.get_doi_tuong_phone.assert_called_once_with("78875959")

        # Check queue results
        assert not mock_queue.empty()
        msgs = []
        while not mock_queue.empty():
            msgs.append(mock_queue.get())

        # The last message should be fetch_success
        success_msg = msgs[-1]
        assert success_msg[0] == "fetch_success"
        contacts = success_msg[1]
        assert len(contacts) == 1
        assert contacts[0]["phone"] == "0365240748"
        assert contacts[0]["name"] == "Nguyễn Thị Tuyết Mai"
