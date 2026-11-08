import sys
import queue
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest
import httpx

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.controllers.app_controller import AppController
from app.services.vncdc_client import VncdcClient


class TestVncdc2FAControllerIntegration:
    """
    Comprehensive test suite for Phase 02: Controller State Verification & Error Handling.
    Verifies:
      1. Login dispatch -> 2fa_required detection -> queue notification -> OtpDialog trigger.
      2. End-to-end 2FA verification flow with AntiForgeryToken and post-login plan extraction.
      3. Integration with real VncdcClient service methods and mocked HTTP responses.
      4. Invalid OTP rejection, error propagation, loading state resets, and retry capability.
      5. Resilient exception handling during verify_2fa (network timeout, HTTP error).
      6. Resilient exception handling during fetch_profile_and_plan.
      7. Graceful fallback when OtpDialog is closed/destroyed before background worker finishes.
      8. Thread safety via comm_queue and daemon thread configuration.
    """

    def _setup_controller(self):
        mock_window = MagicMock()
        mock_queue = queue.Queue()
        mock_window.comm_queue = mock_queue

        mock_storage = MagicMock()
        mock_storage.load_sent_database.return_value = set()
        mock_storage.load_credentials.return_value = ("testuser", "testpass")

        mock_services = {
            "storage": mock_storage,
            "contacts": MagicMock(),
            "report": MagicMock()
        }

        mock_fetch_tab = MagicMock()
        mock_fetch_tab.get_login_info.return_value = ("testuser", "testpass", True)
        mock_window.fetch_tab = mock_fetch_tab

        mock_automation_tab = MagicMock()
        mock_automation_tab.status_label.cget.return_value = "Trạng thái: Sẵn sàng"
        mock_window.automation_tab = mock_automation_tab

        controller = AppController(mock_window, mock_services, MagicMock())
        return controller, mock_window, mock_services, mock_queue

    # --------------------------------------------------------------------------
    # 1. Login flow dispatch -> 2fa_required detection
    # --------------------------------------------------------------------------
    @patch("threading.Thread")
    @patch("app.controllers.app_controller.VncdcClient")
    def test_handle_vncdc_login_triggers_otp_required(self, mock_client_cls, mock_thread_cls):
        """
        Verify that handle_vncdc_login invokes VncdcClient.login.
        When status == '2fa_required', it pushes ('otp_required', client, data) to comm_queue.
        """
        controller, mock_window, _, mock_queue = self._setup_controller()
        mock_client = MagicMock()
        mock_client.login.return_value = (True, "2fa_required", "Yêu cầu xác thực 2 lớp")
        mock_client_cls.return_value = mock_client

        controller.handle_vncdc_login("admin_cdc", "secret_pass", True)

        # Confirm thread created as daemon
        assert mock_thread_cls.called
        thread_kwargs = mock_thread_cls.call_args[1]
        assert thread_kwargs.get("daemon") is True
        login_task = thread_kwargs["target"]

        # Run worker task synchronously
        login_task()

        # Check queue
        assert not mock_queue.empty()
        event = mock_queue.get()
        assert event[0] == "otp_required"
        assert event[1] == mock_client
        assert event[2] == "Yêu cầu xác thực 2 lớp"

    # --------------------------------------------------------------------------
    # 2. Queue processing -> show_otp_and_verify dialog trigger
    # --------------------------------------------------------------------------
    @patch("app.controllers.app_controller.OtpDialog")
    def test_process_comm_queue_handles_otp_required_and_shows_dialog(self, mock_dialog_cls):
        """
        Verify process_comm_queue consumes 'otp_required', updates login status to orange,
        and instantiates OtpDialog.
        """
        controller, mock_window, _, mock_queue = self._setup_controller()
        mock_client = MagicMock()
        mock_queue.put(("otp_required", mock_client, "Vui lòng nhập OTP"))

        controller.process_comm_queue()

        mock_window.fetch_tab.set_login_status.assert_called_once_with("Yêu cầu nhập OTP", "orange")
        mock_dialog_cls.assert_called_once()
        dialog_args, dialog_kwargs = mock_dialog_cls.call_args
        assert dialog_args[0] == mock_window
        assert dialog_kwargs["error_message"] == "Vui lòng nhập OTP"
        assert callable(dialog_kwargs["on_confirm_callback"])

    # --------------------------------------------------------------------------
    # 3. Full 2FA success flow: submit OTP -> verify -> fetch plan -> UI update
    # --------------------------------------------------------------------------
    @patch("app.controllers.app_controller.OtpDialog")
    @patch("threading.Thread")
    def test_otp_verification_success_flow(self, mock_thread_cls, mock_dialog_cls):
        """
        Verify the successful 2FA confirmation:
        - OtpDialog sets loading state and hides prior error.
        - Worker calls verify_2fa(otp) -> (True, None).
        - Worker calls fetch_profile_and_plan() -> (profile, ke_hoach_id).
        - Worker puts ('otp_verify_result', True, (client, profile, ke_hoach_id)).
        - process_comm_queue stores state, saves credentials, closes dialog, sets UI to green.
        """
        controller, mock_window, mock_services, mock_queue = self._setup_controller()
        mock_client = MagicMock()
        mock_client.verify_2fa.return_value = (True, None)
        mock_client.fetch_profile_and_plan.return_value = ({"tinh_id": 106, "huyen_id": 10605}, 9403580)

        mock_dialog_instance = MagicMock()
        mock_dialog_instance.winfo_exists.return_value = True
        mock_dialog_cls.return_value = mock_dialog_instance

        # 1. Trigger dialog display
        controller.show_otp_and_verify(mock_client, "Yêu cầu OTP")
        assert controller.otp_dialog == mock_dialog_instance

        # 2. Extract and invoke on_confirm callback
        _, dialog_kwargs = mock_dialog_cls.call_args
        on_confirm = dialog_kwargs["on_confirm_callback"]
        on_confirm("654321")

        mock_dialog_instance.set_loading.assert_called_once_with(True)
        mock_dialog_instance.hide_error.assert_called_once()

        # 3. Execute background verify_task
        assert mock_thread_cls.called
        assert mock_thread_cls.call_args[1].get("daemon") is True
        verify_task = mock_thread_cls.call_args[1]["target"]
        verify_task()

        mock_client.verify_2fa.assert_called_once_with("654321")
        mock_client.fetch_profile_and_plan.assert_called_once()

        # 4. Check worker result in queue
        assert not mock_queue.empty()
        event = mock_queue.get()
        assert event[0] == "otp_verify_result"
        assert event[1] is True
        client_res, profile_res, kh_id_res = event[2]
        assert client_res == mock_client
        assert profile_res == {"tinh_id": 106, "huyen_id": 10605}
        assert kh_id_res == 9403580

        # 5. Process queue on main thread
        mock_queue.put(event)
        controller.process_comm_queue()

        # Verify controller updated state
        assert controller.vncdc_client == mock_client
        assert controller.vncdc_profile == {"tinh_id": 106, "huyen_id": 10605}
        assert controller.vncdc_ke_hoach_id == 9403580

        # Verify credentials saved
        mock_services["storage"].save_credentials.assert_called_once_with("testuser", "testpass")

        # Verify dialog closed and UI updated
        mock_dialog_instance._close.assert_called_once()
        mock_window.fetch_tab.set_login_status.assert_called_once_with(
            "Đăng nhập thành công. KH_ID: 9403580", "green", True
        )

    # --------------------------------------------------------------------------
    # 4. End-to-end integration with real VncdcClient instance + mocked HTTP
    # --------------------------------------------------------------------------
    @patch("app.controllers.app_controller.OtpDialog")
    @patch("threading.Thread")
    @patch("httpx.Client.post")
    @patch("httpx.Client.get")
    def test_e2e_flow_with_real_client_antiforgery_header_and_plan(
        self, mock_get, mock_post, mock_thread_cls, mock_dialog_cls
    ):
        """
        End-to-end integration test with the real VncdcClient service:
        - Verifies that AntiForgeryToken is retrieved via GET /Account/AntiForgeryToken.
        - Verifies that VerifyTwoFactor receives RequestVerificationToken header.
        - Verifies profile/plan retrieval and final controller state.
        """
        controller, mock_window, mock_services, mock_queue = self._setup_controller()

        real_client = VncdcClient(base_url="https://tiemchung.vncdc.gov.vn")

        # Mock GET /Account/AntiForgeryToken
        def fake_get(url, **kwargs):
            mock_r = MagicMock()
            if "/Account/AntiForgeryToken" in url:
                mock_r.status_code = 200
                mock_r.json.return_value = {"token": "AF_TOKEN_123456789"}
            elif "/TiemChung/DoiTuong/Index" in url:
                mock_r.status_code = 200
                mock_r.text = '<input id="KE_HOACH_TIEM_ID" value="888001" />'
            else:
                mock_r.status_code = 200
                mock_r.text = ""
            return mock_r

        mock_get.side_effect = fake_get

        # Mock POST /Account/VerifyTwoFactor
        def fake_post(url, **kwargs):
            mock_r = MagicMock()
            if "/Account/VerifyTwoFactor" in url:
                mock_r.status_code = 200
                # Simulate setting .ASPXAUTH session cookie
                real_client.session.cookies.set(".ASPXAUTH", "session_auth_token_val")
                mock_r.text = '{"Success": true, "Redirect": "/Home/Index"}'
            return mock_r

        mock_post.side_effect = fake_post

        # Mock fetch_profile_and_plan on the client
        real_client.fetch_profile_and_plan = MagicMock(return_value=({"tinh_id": 106}, 888001))

        mock_dialog_instance = MagicMock()
        mock_dialog_instance.winfo_exists.return_value = True
        mock_dialog_cls.return_value = mock_dialog_instance

        # Controller displays OTP dialog
        controller.show_otp_and_verify(real_client, "Nhập OTP")

        # User submits OTP
        _, dialog_kwargs = mock_dialog_cls.call_args
        on_confirm = dialog_kwargs["on_confirm_callback"]
        on_confirm("999888")

        # Run verify_task
        verify_task = mock_thread_cls.call_args[1]["target"]
        verify_task()

        # Check HTTP POST headers for RequestVerificationToken
        verify_post_calls = [c for c in mock_post.call_args_list if "/Account/VerifyTwoFactor" in c[0][0]]
        assert len(verify_post_calls) == 1
        post_url, post_kwargs = verify_post_calls[0][0][0], verify_post_calls[0][1]
        assert post_kwargs["headers"].get("RequestVerificationToken") == "AF_TOKEN_123456789"
        assert post_kwargs["headers"].get("Referer") == "https://tiemchung.vncdc.gov.vn/Account/VerifyTwoFactor"
        assert post_kwargs["data"] == {"code": "999888"}

        # Process queue
        controller.process_comm_queue()

        assert controller.vncdc_client == real_client
        assert controller.vncdc_ke_hoach_id == 888001
        assert controller.vncdc_profile == {"tinh_id": 106}
        mock_dialog_instance._close.assert_called_once()
        mock_window.fetch_tab.set_login_status.assert_called_once_with(
            "Đăng nhập thành công. KH_ID: 888001", "green", True
        )

    # --------------------------------------------------------------------------
    # 5. OTP verification failure (wrong OTP code)
    # --------------------------------------------------------------------------
    @patch("app.controllers.app_controller.OtpDialog")
    @patch("threading.Thread")
    def test_otp_verification_failure_wrong_code(self, mock_thread_cls, mock_dialog_cls):
        """
        Verify that an invalid OTP code:
        - Worker puts ('otp_verify_result', False, error_msg).
        - process_comm_queue keeps dialog open, re-enables buttons (set_loading(False)),
          and displays error message via show_error.
        - Credentials and plan id are not saved.
        """
        controller, mock_window, mock_services, mock_queue = self._setup_controller()
        mock_client = MagicMock()
        mock_client.verify_2fa.return_value = (False, "Mã OTP không chính xác hoặc đã hết hạn")

        mock_dialog_instance = MagicMock()
        mock_dialog_instance.winfo_exists.return_value = True
        mock_dialog_cls.return_value = mock_dialog_instance

        controller.show_otp_and_verify(mock_client, "Nhập OTP")

        _, dialog_kwargs = mock_dialog_cls.call_args
        on_confirm = dialog_kwargs["on_confirm_callback"]
        on_confirm("000000")

        verify_task = mock_thread_cls.call_args[1]["target"]
        verify_task()

        # Queue receives failure
        assert not mock_queue.empty()
        event = mock_queue.get()
        assert event[0] == "otp_verify_result"
        assert event[1] is False
        assert event[2] == "Mã OTP không chính xác hoặc đã hết hạn"

        # Main thread consumes failure
        mock_queue.put(event)
        controller.process_comm_queue()

        # Dialog was NOT closed, error was shown, loading state reset
        mock_dialog_instance._close.assert_not_called()
        mock_dialog_instance.set_loading.assert_has_calls([call(True), call(False)])
        mock_dialog_instance.show_error.assert_called_once_with("Mã OTP không chính xác hoặc đã hết hạn")

        # Credentials NOT saved
        mock_services["storage"].save_credentials.assert_not_called()
        assert controller.vncdc_ke_hoach_id is None

    # --------------------------------------------------------------------------
    # 6. Fallback error message when err is None
    # --------------------------------------------------------------------------
    @patch("app.controllers.app_controller.OtpDialog")
    @patch("threading.Thread")
    def test_otp_verification_failure_fallback_message(self, mock_thread_cls, mock_dialog_cls):
        """
        Verify fallback to default 'Mã OTP không chính xác' when err is None or empty.
        """
        controller, mock_window, _, mock_queue = self._setup_controller()
        mock_client = MagicMock()
        mock_client.verify_2fa.return_value = (False, None)

        mock_dialog_instance = MagicMock()
        mock_dialog_instance.winfo_exists.return_value = True
        mock_dialog_cls.return_value = mock_dialog_instance

        controller.show_otp_and_verify(mock_client, "Nhập OTP")

        on_confirm = mock_dialog_cls.call_args[1]["on_confirm_callback"]
        on_confirm("111222")

        verify_task = mock_thread_cls.call_args[1]["target"]
        verify_task()

        event = mock_queue.get()
        assert event[0] == "otp_verify_result"
        assert event[1] is False
        assert event[2] == "Mã OTP không chính xác"

    # --------------------------------------------------------------------------
    # 7. Network / unexpected exception in verify_2fa
    # --------------------------------------------------------------------------
    @patch("app.controllers.app_controller.OtpDialog")
    @patch("threading.Thread")
    def test_verify_task_catches_network_timeout(self, mock_thread_cls, mock_dialog_cls):
        """
        Verify unhandled network exception during verify_2fa is caught and posted as
        ('otp_verify_result', False, 'Lỗi: ...').
        """
        controller, mock_window, _, mock_queue = self._setup_controller()
        mock_client = MagicMock()
        mock_client.verify_2fa.side_effect = httpx.ConnectTimeout("Không thể kết nối đến máy chủ VNCDC")

        mock_dialog_instance = MagicMock()
        mock_dialog_instance.winfo_exists.return_value = True
        mock_dialog_cls.return_value = mock_dialog_instance

        controller.show_otp_and_verify(mock_client, "Nhập OTP")

        on_confirm = mock_dialog_cls.call_args[1]["on_confirm_callback"]
        on_confirm("123456")

        verify_task = mock_thread_cls.call_args[1]["target"]
        # Must not raise
        verify_task()

        event = mock_queue.get()
        assert event[0] == "otp_verify_result"
        assert event[1] is False
        assert "Lỗi: Không thể kết nối đến máy chủ VNCDC" in event[2]

        mock_queue.put(event)
        controller.process_comm_queue()

        mock_dialog_instance.set_loading.assert_called_with(False)
        mock_dialog_instance.show_error.assert_called_with(event[2])

    # --------------------------------------------------------------------------
    # 8. Exception during fetch_profile_and_plan
    # --------------------------------------------------------------------------
    @patch("app.controllers.app_controller.OtpDialog")
    @patch("threading.Thread")
    def test_verify_task_catches_exception_in_post_auth_fetch(self, mock_thread_cls, mock_dialog_cls):
        """
        Verify that if verify_2fa succeeds but fetch_profile_and_plan raises an exception,
        the worker captures it gracefully without crashing.
        """
        controller, mock_window, _, mock_queue = self._setup_controller()
        mock_client = MagicMock()
        mock_client.verify_2fa.return_value = (True, None)
        mock_client.fetch_profile_and_plan.side_effect = RuntimeError("Failed to parse plan table HTML")

        mock_dialog_instance = MagicMock()
        mock_dialog_instance.winfo_exists.return_value = True
        mock_dialog_cls.return_value = mock_dialog_instance

        controller.show_otp_and_verify(mock_client, "Nhập OTP")

        on_confirm = mock_dialog_cls.call_args[1]["on_confirm_callback"]
        on_confirm("123456")

        verify_task = mock_thread_cls.call_args[1]["target"]
        verify_task()

        event = mock_queue.get()
        assert event[0] == "otp_verify_result"
        assert event[1] is False
        assert "Lỗi: Failed to parse plan table HTML" in event[2]

        mock_queue.put(event)
        controller.process_comm_queue()

        mock_dialog_instance.show_error.assert_called_with("Lỗi: Failed to parse plan table HTML")

    # --------------------------------------------------------------------------
    # 9. Dialog lifecycle edge case: dialog destroyed before result arrives
    # --------------------------------------------------------------------------
    def test_otp_verify_failure_when_dialog_is_destroyed_or_none(self):
        """
        Verify that if the user closes the OtpDialog while verification is in-flight,
        process_comm_queue gracefully updates fetch_tab status instead of crashing.
        """
        controller, mock_window, _, mock_queue = self._setup_controller()

        # Dialog exists = False
        mock_dialog = MagicMock()
        mock_dialog.winfo_exists.return_value = False
        controller.otp_dialog = mock_dialog

        mock_queue.put(("otp_verify_result", False, "Mã xác thực đã hết hạn"))

        # Must not raise AttributeError or crash
        controller.process_comm_queue()

        mock_window.fetch_tab.set_login_status.assert_called_once_with(
            "Xác thực thất bại: Mã xác thực đã hết hạn", "red"
        )
        mock_dialog.show_error.assert_not_called()

    def test_otp_verify_success_when_dialog_is_none(self):
        """
        Verify that if otp_dialog is None on success, controller still saves credentials
        and updates fetch status without error.
        """
        controller, mock_window, mock_services, mock_queue = self._setup_controller()
        controller.otp_dialog = None

        mock_client = MagicMock()
        mock_queue.put(("otp_verify_result", True, (mock_client, {"tinh_id": 106}, 999123)))

        controller.process_comm_queue()

        assert controller.vncdc_client == mock_client
        assert controller.vncdc_ke_hoach_id == 999123
        mock_services["storage"].save_credentials.assert_called_once_with("testuser", "testpass")
        mock_window.fetch_tab.set_login_status.assert_called_once_with(
            "Đăng nhập thành công. KH_ID: 999123", "green", True
        )
