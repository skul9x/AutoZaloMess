import pytest
from unittest.mock import MagicMock, patch
from app.services.vncdc_client import VncdcClient

def test_get_doi_tuong_phone_success():
    client = VncdcClient()
    mock_response = MagicMock()
    mock_response.text = """
    <html>
    <body>
    <script type="text/javascript">
        var TiemChung$DoiTuong$EditModel = {"DienThoaiMe": "0365240748"};
    </script>
    </body>
    </html>
    """
    mock_response.status_code = 200
    
    with patch.object(client.session, "get", return_value=mock_response) as mock_get:
        phone = client.get_doi_tuong_phone("78875959")
        assert phone == "0365240748"
        mock_get.assert_called_once_with(
            "/TiemChung/DoiTuong/Edit?doiTuongId=78875959",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://tiemchung.vncdc.gov.vn/TiemChung/DoiTuong/Index",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

def test_get_doi_tuong_phone_failure():
    client = VncdcClient()
    with patch.object(client.session, "get", side_effect=Exception("HTTP Error")) as mock_get:
        phone = client.get_doi_tuong_phone("78875959")
        assert phone == ""
