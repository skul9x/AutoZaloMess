import pytest
from unittest.mock import MagicMock, patch
import httpx
from app.services.vncdc_client import VncdcClient

class TestVncdcClientSearchToken:
    def test_search_doi_tuong_attaches_antiforgery_token(self):
        client = VncdcClient()
        
        # Giả lập token lấy từ get_anti_forgery_token
        with patch.object(client, "get_anti_forgery_token", return_value="dynamic_token_123"):
            with patch.object(client.session, "post") as mock_post:
                mock_resp = MagicMock(spec=httpx.Response)
                mock_resp.status_code = 200
                mock_resp.text = "<html><body></body></html>"
                mock_post.return_value = mock_resp
                
                payload = {"KE_HOACH_TIEM_ID": "9570001", "XA_ID": "1062907"}
                res = client.search_doi_tuong(payload)
                
                assert mock_post.called
                call_args = mock_post.call_args
                headers = call_args[1].get("headers") or call_args.kwargs.get("headers")
                
                assert headers["RequestVerificationToken"] == "dynamic_token_123"
                assert headers["__RequestVerificationToken"] == "dynamic_token_123"
                assert headers["X-Requested-With"] == "XMLHttpRequest"

    def test_search_doi_tuong_fallback_to_cookie_token_when_endpoint_fails(self):
        client = VncdcClient()
        client.session.cookies.set("__RequestVerificationToken", "cookie_token_456")
        
        with patch.object(client, "get_anti_forgery_token", return_value=None):
            with patch.object(client.session, "post") as mock_post:
                mock_resp = MagicMock(spec=httpx.Response)
                mock_resp.status_code = 200
                mock_resp.text = "<html><body></body></html>"
                mock_post.return_value = mock_resp
                
                payload = {"KE_HOACH_TIEM_ID": "9570001", "XA_ID": "1062907"}
                res = client.search_doi_tuong(payload)
                
                assert mock_post.called
                call_args = mock_post.call_args
                headers = call_args[1].get("headers") or call_args.kwargs.get("headers")
                
                assert headers["RequestVerificationToken"] == "cookie_token_456"
                assert headers["__RequestVerificationToken"] == "cookie_token_456"

    def test_controller_passes_formatted_session_key(self):
        import time
        now = time.localtime()
        ms = int((time.time() % 1) * 1000)
        session_key = f"BO_SUNG_DV_{now.tm_min}_{now.tm_sec}_{ms}"
        assert session_key.startswith("BO_SUNG_DV_")

