# Phase 02: Upgrade Client (`vncdc_client.py`)
Status: ✅ Complete
Dependencies: Phase 01

## Objective
Extend `VncdcClient` to support fetching the Edit page of a specific vaccination target and returning the parsed phone number.

## Requirements
### Functional
- Add a new method `get_doi_tuong_phone(self, doi_tuong_id)` to `VncdcClient`.
- Send an HTTP GET request to `/TiemChung/DoiTuong/Edit?doiTuongId={doi_tuong_id}`.
- Use `parse_doi_tuong_phone_from_edit_page` to retrieve the unmasked phone number.

## Implementation Steps
1. [x] Add `get_doi_tuong_phone(self, doi_tuong_id)` to `app/services/vncdc_client.py`.
2. [x] Write integration test file `tests/test_vncdc_client_phone.py` using `unittest.mock` to mock `httpx.Client` HTTP responses.

## Files to Create/Modify
- `app/services/vncdc_client.py` - [Modify] Add method to fetch Edit page.
- `tests/test_vncdc_client_phone.py` - [New] Mocked tests for the client request logic.

## Test Criteria
- Verify that the client sends the correct GET request with headers.
- Verify that it correctly returns the parsed phone number from the mock response.
- Run `pytest tests/test_vncdc_client_phone.py`.
