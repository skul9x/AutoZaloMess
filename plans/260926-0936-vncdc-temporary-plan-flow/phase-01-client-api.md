# Phase 01: VNCDC Client API Expansion
Status: ✅ Completed
Dependencies: None

## Objective
Extend `VncdcClient` in `app/services/vncdc_client.py` to support the new VNCDC endpoints captured from network traffic:
1. Adding target children into a vaccination plan session (`NhapBoSungDoiTuong`).
2. Querying appointment list from the vaccination plan (`GetDanhSachHenTiemByParams`) to extract unmasked phone numbers.
3. Deleting target children from the appointment list (`XoaDoiTuongDSHenTiem`).

## Requirements
### Functional
- `nhap_bo_sung_doi_tuong(ke_hoach_id, doi_tuong_ids, buoi_tiem=1, force_save=0)`:
  - Formats JSON payload with `DU_LIEU_DA_CHON` list containing `{"DOI_TUONG_ID": id, "DANH_SACH_VACXIN": []}`.
  - Sends `POST /KeHoachTiemPhatSinhArea/NhapBoSung/NhapBoSungDoiTuong/`.
  - Handles response `{"Status": 2, "Message": ...}`.
- `get_danh_sach_hen_tiem(ke_hoach_id, buoi_tiem=0, trang_thai=-1)`:
  - Sends `POST /KeHoachTiemPhatSinhArea/KeHoachTiemPhatSinh/GetDanhSachHenTiemByParams`.
  - Parses JSON response and returns `ThongTinHenTiem` list.
- `xoa_doi_tuong_hen_tiem(ke_hoach_id, doi_tuong_id, ke_hoach_tiem_ct_id, thoi_gian_tiem=0)`:
  - Sends `POST /KeHoachTiemPhatSinhArea/KeHoachTiemPhatSinh/XoaDoiTuongDSHenTiem` with required JSON body.
  - Returns `True` if server responds with `1`.

### Non-Functional
- Correct request headers: `Content-Type: application/json; charset=UTF-8`, `X-Requested-With: XMLHttpRequest`, and anti-forgery headers.
- Safe error handling and timeout configuration.

## Files to Create/Modify
- `app/services/vncdc_client.py`: Add API methods for add, get appointments, and delete.
- `tests/test_vncdc_client_plan_flow.py`: Comprehensive test file for all 3 endpoints.

## Test Verification
- Exactly one comprehensive test file:
  `pytest tests/test_vncdc_client_plan_flow.py`
  - Validates payload structure and serialization for `nhap_bo_sung_doi_tuong`.
  - Validates JSON extraction of unmasked phone numbers in `get_danh_sach_hen_tiem`.
  - Validates payload structure and response code for `xoa_doi_tuong_hen_tiem`.
