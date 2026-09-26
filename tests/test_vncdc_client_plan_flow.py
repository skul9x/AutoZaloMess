import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Ensure app module can be found when running pytest directly on this file
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.services.vncdc_client import VncdcClient


class TestVncdcClientPlanFlow:
    """
    Comprehensive test suite for Phase 01: VNCDC Client API Expansion.
    Covers:
      1. nhap_bo_sung_doi_tuong (injection of target children into vaccination plan)
      2. get_danh_sach_hen_tiem (retrieval of appointments and unmasked phone numbers)
      3. xoa_doi_tuong_hen_tiem (safe deletion of injected target children)
    """

    # -------------------------------------------------------------------------
    # 1. nhap_bo_sung_doi_tuong tests
    # -------------------------------------------------------------------------
    def test_nhap_bo_sung_doi_tuong_success(self):
        client = VncdcClient()
        client.session.cookies.set("__RequestVerificationToken", "csrf_token_abc")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "Status": 2,
            "Message": "Bổ sung đối tượng vào buổi tiêm thành công"
        }

        with patch.object(client.session, "post", return_value=mock_resp) as mock_post:
            doi_tuong_ids = [81126724, "81123344", {"DOI_TUONG_ID": 81118298, "DANH_SACH_VACXIN": []}]
            res = client.nhap_bo_sung_doi_tuong(
                ke_hoach_id=9403580,
                doi_tuong_ids=doi_tuong_ids,
                buoi_tiem=1,
                force_save=0
            )

            # Check return structure and status
            assert isinstance(res, dict)
            assert res.get("Status") == 2
            assert res.get("success") is True
            assert res.get("Message") == "Bổ sung đối tượng vào buổi tiêm thành công"

            # Check post call arguments
            mock_post.assert_called_once()
            call_args, call_kwargs = mock_post.call_args
            assert call_args[0] == "/KeHoachTiemPhatSinhArea/NhapBoSung/NhapBoSungDoiTuong/"

            # Verify JSON payload structure
            payload = call_kwargs["json"]
            assert payload["KE_HOACH_TIEM_ID"] == "9403580"
            assert payload["BUOI_TIEM"] == "1"
            assert payload["FORCE_SAVE"] == 0
            assert len(payload["DU_LIEU_DA_CHON"]) == 3
            assert payload["DU_LIEU_DA_CHON"][0] == {"DOI_TUONG_ID": 81126724, "DANH_SACH_VACXIN": []}
            assert payload["DU_LIEU_DA_CHON"][1] == {"DOI_TUONG_ID": 81123344, "DANH_SACH_VACXIN": []}
            assert payload["DU_LIEU_DA_CHON"][2] == {"DOI_TUONG_ID": 81118298, "DANH_SACH_VACXIN": []}

            # Verify headers
            headers = call_kwargs["headers"]
            assert headers["Content-Type"] == "application/json; charset=UTF-8"
            assert headers["X-Requested-With"] == "XMLHttpRequest"
            assert headers["Accept"] == "application/json, text/javascript, */*; q=0.01"
            assert headers["__RequestVerificationToken"] == "csrf_token_abc"

    def test_nhap_bo_sung_doi_tuong_single_id_and_errors(self):
        client = VncdcClient()

        # Test single id (int)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"Status": 1, "Message": "Đã tồn tại trong danh sách"}

        with patch.object(client.session, "post", return_value=mock_resp) as mock_post:
            res = client.nhap_bo_sung_doi_tuong(ke_hoach_id="9403580", doi_tuong_ids=81126724)
            assert res.get("Status") == 1
            assert res.get("success") is False
            payload = mock_post.call_args[1]["json"]
            assert len(payload["DU_LIEU_DA_CHON"]) == 1
            assert payload["DU_LIEU_DA_CHON"][0]["DOI_TUONG_ID"] == 81126724

        # Test network/exception handling
        with patch.object(client.session, "post", side_effect=Exception("Connection reset")):
            res_err = client.nhap_bo_sung_doi_tuong(ke_hoach_id=9403580, doi_tuong_ids=[81126724])
            assert res_err["Status"] == -1
            assert res_err["success"] is False
            assert "Connection reset" in res_err["Message"]

    # -------------------------------------------------------------------------
    # 2. get_danh_sach_hen_tiem tests
    # -------------------------------------------------------------------------
    def test_get_danh_sach_hen_tiem_success(self):
        client = VncdcClient()
        client.session.cookies.set("__RequestVerificationToken", "csrf_token_xyz")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "ThongTinHenTiem": [
                {
                    "DOI_TUONG_ID": 81015981,
                    "MA_DOI_TUONG": "106290120260263",
                    "HO_TEN": "ĐẶNG ĐÌNH NGUYÊN",
                    "TEN_ME": "(Mẹ) SẦM THỊ HOÀI",
                    "DIEN_THOAI": "0374441067",
                    "DIA_CHI": "TDP BẰNG AN, Phường Quế Võ, Bắc Ninh",
                    "KE_HOACH_TIEM_CHI_TIET_ID": 84020986,
                    "THOI_GIAN_TIEM": 1,
                    "KE_HOACH_TIEM_ID": 9403580,
                },
                {
                    "DOI_TUONG_ID": 81015662,
                    "MA_DOI_TUONG": "106290120260264",
                    "HO_TEN": "NGUYỄN VĂN A",
                    "TEN_ME": "LÊ THỊ B",
                    "DIEN_THOAI": "0987654321",
                    "DIA_CHI": "Hà Nội",
                    "KE_HOACH_TIEM_CHI_TIET_ID": 84020987,
                    "THOI_GIAN_TIEM": 0,
                    "KE_HOACH_TIEM_ID": 9403580,
                }
            ]
        }

        with patch.object(client.session, "post", return_value=mock_resp) as mock_post:
            items = client.get_danh_sach_hen_tiem(ke_hoach_id="9403580", buoi_tiem=0, trang_thai=-1)

            assert isinstance(items, list)
            assert len(items) == 2

            # Verify unmasked phone numbers and required fields
            assert items[0]["DOI_TUONG_ID"] == 81015981
            assert items[0]["DIEN_THOAI"] == "0374441067"
            assert items[0]["KE_HOACH_TIEM_CHI_TIET_ID"] == 84020986
            assert items[0]["HO_TEN"] == "ĐẶNG ĐÌNH NGUYÊN"
            assert items[0]["TEN_ME"] == "(Mẹ) SẦM THỊ HOÀI"

            assert items[1]["DOI_TUONG_ID"] == 81015662
            assert items[1]["DIEN_THOAI"] == "0987654321"
            assert items[1]["KE_HOACH_TIEM_CHI_TIET_ID"] == 84020987

            # Verify request
            mock_post.assert_called_once()
            call_args, call_kwargs = mock_post.call_args
            assert call_args[0] == "/KeHoachTiemPhatSinhArea/KeHoachTiemPhatSinh/GetDanhSachHenTiemByParams"

            payload = call_kwargs["json"]
            assert payload == {
                "KE_HOACH_TIEM_ID": 9403580,
                "BUOI_TIEM": "0",
                "TRANG_THAI_TIEM": "-1"
            }

            headers = call_kwargs["headers"]
            assert headers["Content-Type"] == "application/json; charset=UTF-8"
            assert headers["X-Requested-With"] == "XMLHttpRequest"
            assert headers["__RequestVerificationToken"] == "csrf_token_xyz"

    def test_get_danh_sach_hen_tiem_empty_and_exception(self):
        client = VncdcClient()

        # Server returns empty or None ThongTinHenTiem
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ThongTinHenTiem": None}

        with patch.object(client.session, "post", return_value=mock_resp):
            items = client.get_danh_sach_hen_tiem(ke_hoach_id=9403580)
            assert items == []

        # Server returns exception
        with patch.object(client.session, "post", side_effect=Exception("Timeout")):
            items = client.get_danh_sach_hen_tiem(ke_hoach_id=9403580)
            assert items == []

    # -------------------------------------------------------------------------
    # 3. xoa_doi_tuong_hen_tiem tests
    # -------------------------------------------------------------------------
    def test_xoa_doi_tuong_hen_tiem_success(self):
        client = VncdcClient()
        client.session.cookies.set("__RequestVerificationToken", "csrf_token_del")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "1"
        mock_resp.json.return_value = 1

        with patch.object(client.session, "post", return_value=mock_resp) as mock_post:
            success = client.xoa_doi_tuong_hen_tiem(
                ke_hoach_id="9403580",
                doi_tuong_id="81015981",
                ke_hoach_tiem_ct_id="84020986",
                thoi_gian_tiem=0
            )

            assert success is True

            # Verify endpoint and payload
            mock_post.assert_called_once()
            call_args, call_kwargs = mock_post.call_args
            assert call_args[0] == "/KeHoachTiemPhatSinhArea/KeHoachTiemPhatSinh/XoaDoiTuongDSHenTiem"

            payload = call_kwargs["json"]
            assert payload == {
                "KE_HOACH_TIEM_CT_ID": 84020986,
                "DOI_TUONG_ID": 81015981,
                "THOI_GIAN_TIEM": 0,
                "KE_HOACH_TIEM_ID": 9403580
            }

            headers = call_kwargs["headers"]
            assert headers["Content-Type"] == "application/json; charset=UTF-8"
            assert headers["X-Requested-With"] == "XMLHttpRequest"
            assert headers["__RequestVerificationToken"] == "csrf_token_del"

    def test_xoa_doi_tuong_hen_tiem_failure_and_exception(self):
        client = VncdcClient()

        # Server returns 0 (failure)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "0"
        mock_resp.json.return_value = 0

        with patch.object(client.session, "post", return_value=mock_resp):
            success = client.xoa_doi_tuong_hen_tiem(
                ke_hoach_id=9403580,
                doi_tuong_id=81015981,
                ke_hoach_tiem_ct_id=84020986
            )
            assert success is False

        # Server raises HTTP/connection error
        with patch.object(client.session, "post", side_effect=Exception("Server Error 500")):
            success = client.xoa_doi_tuong_hen_tiem(
                ke_hoach_id=9403580,
                doi_tuong_id=81015981,
                ke_hoach_tiem_ct_id=84020986
            )
            assert success is False
