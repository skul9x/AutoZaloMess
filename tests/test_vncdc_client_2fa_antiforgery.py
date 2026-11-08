import pytest
import time
from unittest.mock import MagicMock, patch
import httpx
from app.services.vncdc_client import VncdcClient


class TestVncdcClient2FAAntiForgeryToken:

    @patch("httpx.Client.get")
    def test_get_anti_forgery_token_success(self, mock_get):
        """
        Verify that get_anti_forgery_token sends a GET request to /Account/AntiForgeryToken
        with cache-busting timestamp, appropriate headers, and parses the returned JSON token.
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "token": "2fzw8VdbcJYYLYKjS8x4TV1LlmwY1_-wHW0KFpAOg33FmYQLiqRNwrwta5WKKA4SWUO"
        }
        mock_get.return_value = mock_resp

        client = VncdcClient()
        token = client.get_anti_forgery_token()

        assert token == "2fzw8VdbcJYYLYKjS8x4TV1LlmwY1_-wHW0KFpAOg33FmYQLiqRNwrwta5WKKA4SWUO"
        mock_get.assert_called_once()
        call_args, call_kwargs = mock_get.call_args

        # Verify URL starts with /Account/AntiForgeryToken?_=
        assert call_args[0].startswith("/Account/AntiForgeryToken?_=")
        param_ts = call_args[0].split("?_=")[1]
        assert param_ts.isdigit()

        # Verify required headers
        headers = call_kwargs.get("headers", {})
        assert headers.get("X-Requested-With") == "XMLHttpRequest"
        assert headers.get("Referer") == "https://tiemchung.vncdc.gov.vn/Account/VerifyTwoFactor"
        assert headers.get("Accept") == "*/*"

        # Verify timeout
        assert call_kwargs.get("timeout") == 10.0

    @patch("httpx.Client.get")
    def test_get_anti_forgery_token_http_error(self, mock_get):
        """
        Verify that if the token request returns an HTTP error (e.g. 500),
        get_anti_forgery_token handles it gracefully and returns None.
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=MagicMock(),
            response=mock_resp,
        )
        mock_get.return_value = mock_resp

        client = VncdcClient()
        token = client.get_anti_forgery_token()

        assert token is None

    @patch("httpx.Client.get")
    def test_get_anti_forgery_token_network_timeout(self, mock_get):
        """
        Verify that network timeouts return None without raising unhandled exceptions.
        """
        mock_get.side_effect = httpx.TimeoutException("Connection timed out")

        client = VncdcClient()
        token = client.get_anti_forgery_token()

        assert token is None

    @patch("httpx.Client.get")
    def test_get_anti_forgery_token_missing_key_or_invalid_json(self, mock_get):
        """
        Verify that missing token key or non-dict/invalid JSON responses return None.
        """
        # Case A: Dictionary without 'token' key
        mock_resp_no_key = MagicMock()
        mock_resp_no_key.status_code = 200
        mock_resp_no_key.json.return_value = {"other": "value"}
        mock_get.return_value = mock_resp_no_key

        client = VncdcClient()
        assert client.get_anti_forgery_token() is None

        # Case B: Response is not a dict
        mock_resp_list = MagicMock()
        mock_resp_list.status_code = 200
        mock_resp_list.json.return_value = ["not_a_dict"]
        mock_get.return_value = mock_resp_list

        assert client.get_anti_forgery_token() is None

        # Case C: JSON decode error
        mock_resp_invalid_json = MagicMock()
        mock_resp_invalid_json.status_code = 200
        mock_resp_invalid_json.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_resp_invalid_json

        assert client.get_anti_forgery_token() is None

    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_verify_2fa_success_with_token_and_headers(self, mock_post, mock_get):
        """
        Verify that verify_2fa acquires the AntiForgeryToken and sends it along with
        all required headers (Origin, Referer, RequestVerificationToken) in POST /Account/VerifyTwoFactor.
        """
        # Mock AntiForgeryToken response
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"token": "secret_token_123"}
        mock_get.return_value = mock_token_resp

        # Mock VerifyTwoFactor response
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.text = '{"Success": true, "Redirect": "/TiemChung/DoiTuong/Index"}'
        mock_post_resp.json.return_value = {
            "Success": True,
            "Redirect": "/TiemChung/DoiTuong/Index",
        }
        mock_post.return_value = mock_post_resp

        client = VncdcClient()
        success, err = client.verify_2fa("648938")

        assert success is True
        assert err is None

        # Verify POST arguments
        mock_post.assert_called_once()
        post_args, post_kwargs = mock_post.call_args
        assert post_args[0] == "/Account/VerifyTwoFactor"
        assert post_kwargs.get("data") == {"code": "648938"}

        headers = post_kwargs.get("headers", {})
        assert headers.get("RequestVerificationToken") == "secret_token_123"
        assert headers.get("Referer") == "https://tiemchung.vncdc.gov.vn/Account/VerifyTwoFactor"
        assert headers.get("Origin") == "https://tiemchung.vncdc.gov.vn"
        assert headers.get("Content-Type") == "application/x-www-form-urlencoded; charset=UTF-8"
        assert headers.get("X-Requested-With") == "XMLHttpRequest"
        assert headers.get("Accept") == "application/json, text/javascript, */*; q=0.01"

    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_verify_2fa_graceful_when_token_endpoint_fails(self, mock_post, mock_get):
        """
        Verify that if AntiForgeryToken endpoint fails (returns None),
        verify_2fa still proceeds without crashing, omitting RequestVerificationToken header.
        """
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.text = '{"Success": true}'
        mock_post_resp.json.return_value = {"Success": True}
        mock_post.return_value = mock_post_resp

        client = VncdcClient()
        success, err = client.verify_2fa("648938")

        assert success is True
        assert err is None

        # Verify RequestVerificationToken is not in headers
        post_args, post_kwargs = mock_post.call_args
        headers = post_kwargs.get("headers", {})
        assert "RequestVerificationToken" not in headers
        assert headers.get("Referer") == "https://tiemchung.vncdc.gov.vn/Account/VerifyTwoFactor"

    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_verify_2fa_success_via_aspxauth_cookie(self, mock_post, mock_get):
        """
        Verify that if the response sets the .ASPXAUTH cookie, verify_2fa returns (True, None).
        """
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"token": "valid_token"}
        mock_get.return_value = mock_token_resp

        client = VncdcClient()

        def fake_post(url, **kwargs):
            client.session.cookies.set(".ASPXAUTH", "auth_cookie_val")
            resp = MagicMock()
            resp.status_code = 200
            resp.text = ""
            return resp

        mock_post.side_effect = fake_post

        success, err = client.verify_2fa("112233")
        assert success is True
        assert err is None

    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_verify_2fa_success_empty_body_fallback(self, mock_post, mock_get):
        """
        Verify fallback behavior when VerifyTwoFactor returns empty body (HTTP 200)
        and subsequent /Home/GetNumberOfNewMessage check sets .ASPXAUTH.
        """
        # Mock GET to return token first, then respond to GetNumberOfNewMessage
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"token": "valid_token"}

        mock_msg_resp = MagicMock()
        mock_msg_resp.status_code = 200

        client = VncdcClient()

        def fake_get(url, **kwargs):
            if "/Account/AntiForgeryToken" in url:
                return mock_token_resp
            elif url == "/Home/GetNumberOfNewMessage":
                client.session.cookies.set(".ASPXAUTH", "cookie_from_msg_endpoint")
                return mock_msg_resp
            return MagicMock()

        mock_get.side_effect = fake_get

        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.text = ""
        mock_post.return_value = mock_post_resp

        success, err = client.verify_2fa("112233")
        assert success is True
        assert err is None

    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_verify_2fa_failed_wrong_code(self, mock_post, mock_get):
        """
        Verify that an invalid OTP response returns (False, error_message).
        """
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"token": "valid_token"}
        mock_get.return_value = mock_token_resp

        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.text = '{"Success": false, "Message": "Mã xác thực không hợp lệ hoặc đã hết hạn."}'
        mock_post_resp.json.return_value = {
            "Success": False,
            "Message": "Mã xác thực không hợp lệ hoặc đã hết hạn.",
        }
        mock_post.return_value = mock_post_resp

        client = VncdcClient()
        success, err = client.verify_2fa("000000")

        assert success is False
        assert err == "Mã xác thực không hợp lệ hoặc đã hết hạn."

    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_verify_2fa_network_post_failure(self, mock_post, mock_get):
        """
        Verify that if POST /Account/VerifyTwoFactor raises a network error,
        it returns (False, failure_message).
        """
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"token": "valid_token"}
        mock_get.return_value = mock_token_resp

        mock_post.side_effect = httpx.ConnectError("Connection dropped")

        client = VncdcClient()
        success, err = client.verify_2fa("123456")

        assert success is False
        assert "Gửi mã OTP thất bại: Connection dropped" in err

    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_verify_2fa_server_error_html_response(self, mock_post, mock_get):
        """
        Verify that if POST returns non-empty HTML / invalid JSON, it handles it gracefully.
        """
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"token": "valid_token"}
        mock_get.return_value = mock_token_resp

        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 500
        mock_post_resp.text = "<html>500 Internal Server Error</html>"
        mock_post_resp.json.side_effect = ValueError("JSON decode error")
        mock_post.return_value = mock_post_resp

        client = VncdcClient()
        success, err = client.verify_2fa("123456")

        assert success is False
        assert "Lỗi xử lý phản hồi từ server" in err

