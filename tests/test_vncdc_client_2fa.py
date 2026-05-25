import pytest
import queue
from unittest.mock import MagicMock, patch
from app.services.vncdc_client import VncdcClient
from app.controllers.app_controller import AppController

class TestVncdcClient2FA:
    
    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_login_success_without_2fa(self, mock_post, mock_get):
        """
        Test Case 1: Đăng nhập thành công thẳng mà không cần mã 2FA.
        Server trả về cookie .ASPXAUTH ngay lập tức.
        """
        # Setup mock for GET /Account/Login
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.text = '<input name="__RequestVerificationToken" type="hidden" value="token_123" />'
        mock_get.return_value = mock_get_resp
        
        # Setup mock for POST /Account/Login
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {"TwoFactorRequired": False, "Success": True}
        mock_post.return_value = mock_post_resp
        
        client = VncdcClient()
        # Mock cookies
        client.session.cookies.set(".ASPXAUTH", "auth_cookie_value")
        
        success, status, err = client.login("username", "password")
        
        assert success is True
        assert status == "success"
        assert err is None
        
        # Verify calls
        mock_get.assert_called_once_with("/Account/Login")
        mock_post.assert_called_once()
        
    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_login_requires_2fa(self, mock_post, mock_get):
        """
        Test Case 2: Đăng nhập yêu cầu mã xác thực 2 lớp (2FA).
        Server trả về JSON chỉ ra TwoFactorRequired == True.
        """
        # Setup mock for GET /Account/Login
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.text = '<input name="__RequestVerificationToken" type="hidden" value="token_123" />'
        
        # Dùng side_effect để xử lý cho cả 2 cuộc gọi GET: /Account/Login và /DonViHanhChinh/LayThongBao
        mock_policy_resp = MagicMock()
        mock_policy_resp.status_code = 200
        mock_get.side_effect = [mock_get_resp, mock_policy_resp]
        
        # Setup mock for POST /Account/Login
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {"TwoFactorRequired": True, "Message": "Yêu cầu xác thực 2 lớp"}
        mock_post.return_value = mock_post_resp
        
        client = VncdcClient()
        
        success, status, msg = client.login("username", "password")
        
        assert success is True
        assert status == "2fa_required"
        assert msg == "Yêu cầu xác thực 2 lớp"
        
        # Check that GET /DonViHanhChinh/LayThongBao was called
        assert mock_get.call_count == 2
        mock_get.assert_any_call("/DonViHanhChinh/LayThongBao", headers={
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://tiemchung.vncdc.gov.vn/Account/Login",
            "Accept": "*/*"
        })

    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_login_failed(self, mock_post, mock_get):
        """
        Test Case 3: Đăng nhập thất bại do sai mật khẩu.
        """
        # Setup mock for GET /Account/Login
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.text = '<input name="__RequestVerificationToken" type="hidden" value="token_123" />'
        mock_get.return_value = mock_get_resp
        
        # Setup mock for POST /Account/Login (failed login)
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {"TwoFactorRequired": False, "Success": False, "Message": "Sai tài khoản hoặc mật khẩu"}
        mock_post.return_value = mock_post_resp
        
        client = VncdcClient()
        
        success, status, err = client.login("username", "wrong_password")
        
        assert success is False
        assert status == "failed"
        assert err == "Sai tài khoản hoặc mật khẩu"

    @patch("httpx.Client.post")
    def test_verify_2fa_success_with_json_response(self, mock_post):
        """
        Test Case 4: Gửi mã OTP chính xác và server trả về JSON báo Success == True.
        """
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {"Success": True}
        mock_post.return_value = mock_post_resp
        
        client = VncdcClient()
        
        success, err = client.verify_2fa("123456")
        
        assert success is True
        assert err is None

    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_verify_2fa_success_with_empty_response(self, mock_post, mock_get):
        """
        Test Case 5: Gửi mã OTP chính xác nhưng server VNCDC trả về Empty Response (HTTP 200 nhưng text rỗng).
        Client tự động gọi gián tiếp GET /Home/GetNumberOfNewMessage và xác thực thành công nhờ có cookie .ASPXAUTH.
        """
        # Mock POST to VerifyTwoFactor (returns empty response)
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.text = ""
        mock_post.return_value = mock_post_resp
        
        # Mock GET to GetNumberOfNewMessage (returns 200 OK)
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get.return_value = mock_get_resp
        
        client = VncdcClient()
        
        # Giả lập khi gọi GetNumberOfNewMessage, cookie .ASPXAUTH được tự động set bởi server
        def fake_get(url, **kwargs):
            if url == "/Home/GetNumberOfNewMessage":
                client.session.cookies.set(".ASPXAUTH", "auth_cookie_value")
            return mock_get_resp
            
        mock_get.side_effect = fake_get
        
        success, err = client.verify_2fa("123456")
        
        assert success is True
        assert err is None
        mock_get.assert_called_once_with(
            "/Home/GetNumberOfNewMessage",
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://tiemchung.vncdc.gov.vn/TiemChung/DoiTuong/Index"
            },
            timeout=5.0
        )

    @patch("httpx.Client.post")
    def test_verify_2fa_failed_wrong_otp(self, mock_post):
        """
        Test Case 6: Gửi sai mã OTP. Server trả về JSON chứa Success == False và thông báo lỗi.
        """
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.text = '{"Success": false, "Message": "Mã xác thực không hợp lệ hoặc đã hết hạn."}'
        mock_post_resp.json.return_value = {"Success": False, "Message": "Mã xác thực không hợp lệ hoặc đã hết hạn."}
        mock_post.return_value = mock_post_resp
        
        client = VncdcClient()
        
        success, err = client.verify_2fa("999999")
        
        assert success is False
        assert "không hợp lệ" in err


class TestAppControllerIntegration:
    
    @patch("app.controllers.app_controller.VncdcClient")
    @patch("app.controllers.app_controller.OtpDialog")
    @patch("threading.Thread")
    def test_handle_vncdc_login_requires_2fa(self, mock_thread, mock_otp_dialog_class, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.login.return_value = (True, "2fa_required", "Yêu cầu xác thực 2 lớp")
        
        mock_window = MagicMock()
        mock_queue = queue.Queue()
        mock_window.comm_queue = mock_queue
        
        mock_services = {
            "storage": MagicMock(),
            "contacts": MagicMock(),
            "report": MagicMock()
        }
        
        controller = AppController(mock_window, mock_services, MagicMock())
        controller.handle_vncdc_login("username", "password", True)
        
        assert mock_thread.called
        target_fn = mock_thread.call_args[1]["target"]
        target_fn()
        
        assert not mock_queue.empty()
        msg = mock_queue.get()
        assert msg[0] == "otp_required"
        assert msg[1] == mock_client
        assert msg[2] == "Yêu cầu xác thực 2 lớp"

    @patch("app.controllers.app_controller.OtpDialog")
    def test_process_comm_queue_handles_otp_required(self, mock_otp_dialog_class):
        mock_window = MagicMock()
        mock_queue = queue.Queue()
        mock_window.comm_queue = mock_queue
        
        mock_services = {
            "storage": MagicMock(),
            "contacts": MagicMock(),
            "report": MagicMock()
        }
        
        controller = AppController(mock_window, mock_services, MagicMock())
        mock_client = MagicMock()
        mock_queue.put(("otp_required", mock_client, "Yêu cầu xác thực"))
        
        controller.show_otp_and_verify = MagicMock()
        controller.process_comm_queue()
        
        mock_window.fetch_tab.set_login_status.assert_called_once_with("Yêu cầu nhập OTP", "orange")
        controller.show_otp_and_verify.assert_called_once_with(mock_client, "Yêu cầu xác thực")

    @patch("app.controllers.app_controller.OtpDialog")
    @patch("threading.Thread")
    def test_show_otp_and_verify_success(self, mock_thread, mock_otp_dialog_class):
        mock_window = MagicMock()
        mock_queue = queue.Queue()
        mock_window.comm_queue = mock_queue
        
        mock_services = {
            "storage": MagicMock(),
            "contacts": MagicMock(),
            "report": MagicMock()
        }
        
        controller = AppController(mock_window, mock_services, MagicMock())
        mock_client = MagicMock()
        mock_client.verify_2fa.return_value = (True, None)
        mock_client.fetch_profile_and_plan.return_value = ({"name": "test"}, 123)
        
        controller.show_otp_and_verify(mock_client, "Nhập OTP")
        
        mock_otp_dialog_class.assert_called_once()
        args, kwargs = mock_otp_dialog_class.call_args
        assert args[0] == mock_window
        assert kwargs["error_message"] == "Nhập OTP"
        
        on_confirm = kwargs["on_confirm_callback"]
        mock_dialog = mock_otp_dialog_class.return_value
        
        on_confirm("123456")
        mock_dialog.set_loading.assert_called_once_with(True)
        mock_dialog.hide_error.assert_called_once()
        
        assert mock_thread.called
        verify_task = mock_thread.call_args[1]["target"]
        verify_task()
        
        mock_client.verify_2fa.assert_called_once_with("123456")
        mock_client.fetch_profile_and_plan.assert_called_once()
        
        assert not mock_queue.empty()
        msg = mock_queue.get()
        assert msg[0] == "otp_verify_result"
        assert msg[1] is True
        assert msg[2] == (mock_client, {"name": "test"}, 123)

    @patch("app.controllers.app_controller.OtpDialog")
    @patch("threading.Thread")
    def test_show_otp_and_verify_failure(self, mock_thread, mock_otp_dialog_class):
        mock_window = MagicMock()
        mock_queue = queue.Queue()
        mock_window.comm_queue = mock_queue
        
        mock_services = {
            "storage": MagicMock(),
            "contacts": MagicMock(),
            "report": MagicMock()
        }
        
        controller = AppController(mock_window, mock_services, MagicMock())
        mock_client = MagicMock()
        mock_client.verify_2fa.return_value = (False, "Mã sai rồi")
        
        controller.show_otp_and_verify(mock_client, "Nhập OTP")
        
        args, kwargs = mock_otp_dialog_class.call_args
        on_confirm = kwargs["on_confirm_callback"]
        
        on_confirm("123456")
        
        assert mock_thread.called
        verify_task = mock_thread.call_args[1]["target"]
        verify_task()
        
        assert not mock_queue.empty()
        msg = mock_queue.get()
        assert msg[0] == "otp_verify_result"
        assert msg[1] is False
        assert msg[2] == "Mã sai rồi"

    def test_process_comm_queue_otp_verify_result_success(self):
        mock_window = MagicMock()
        mock_queue = queue.Queue()
        mock_window.comm_queue = mock_queue
        
        mock_services = {
            "storage": MagicMock(),
            "contacts": MagicMock(),
            "report": MagicMock()
        }
        
        controller = AppController(mock_window, mock_services, MagicMock())
        
        mock_dialog = MagicMock()
        mock_dialog.winfo_exists.return_value = True
        controller.otp_dialog = mock_dialog
        
        mock_window.fetch_tab.get_login_info.return_value = ("user123", "pass123", True)
        mock_client = MagicMock()
        mock_queue.put(("otp_verify_result", True, (mock_client, {"name": "test"}, 123)))
        
        controller.process_comm_queue()
        
        assert controller.vncdc_client == mock_client
        assert controller.vncdc_profile == {"name": "test"}
        assert controller.vncdc_ke_hoach_id == 123
        
        mock_services["storage"].save_credentials.assert_called_once_with("user123", "pass123")
        mock_dialog._close.assert_called_once()
        mock_window.fetch_tab.set_login_status.assert_called_once_with("Đăng nhập thành công. KH_ID: 123", "green", True)

    def test_process_comm_queue_otp_verify_result_failure(self):
        mock_window = MagicMock()
        mock_queue = queue.Queue()
        mock_window.comm_queue = mock_queue
        
        mock_services = {
            "storage": MagicMock(),
            "contacts": MagicMock(),
            "report": MagicMock()
        }
        
        controller = AppController(mock_window, mock_services, MagicMock())
        
        mock_dialog = MagicMock()
        mock_dialog.winfo_exists.return_value = True
        controller.otp_dialog = mock_dialog
        
        mock_queue.put(("otp_verify_result", False, "Mã OTP sai"))
        
        controller.process_comm_queue()
        
        mock_dialog.set_loading.assert_called_once_with(False)
        mock_dialog.show_error.assert_called_once_with("Mã OTP sai")

