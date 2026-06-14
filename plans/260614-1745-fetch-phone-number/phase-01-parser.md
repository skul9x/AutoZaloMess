# Phase 01: Upgrade Parser (`vncdc_parser.py`)
Status: ✅ Complete
Dependencies: None

## Objective
Implement a parser function to extract the unmasked phone number from the Edit page's HTML structure.

## Requirements
### Functional
- Parse the `TiemChung$DoiTuong$EditModel` Javascript object from the page.
- Safely parse the JSON structure and read phone numbers (`DienThoai`, `DienThoaiMe`, `DienThoaiBo`, `DienThoaiNguoiGiamHo`).
- Filter out masked values (`********`).
- Provide a BeautifulSoup fallback to parse form input values (`txtDienThoai_Sua`, `txtDienThoaiMe_Sua`, etc.).

## Implementation Steps
1. [x] Add `parse_doi_tuong_phone_from_edit_page(html)` to `app/services/vncdc_parser.py`.
2. [x] Write unit test file `tests/test_phone_parser.py` using captured HTML samples.

## Files to Create/Modify
- `app/services/vncdc_parser.py` - [Modify] Add parsing logic.
- `tests/test_phone_parser.py` - [New] Unit test for the parser.

## Test Criteria
- Verify that a valid unmasked phone number is correctly extracted.
- Verify that if all values are masked (`********`), it returns an empty string or handles it gracefully.
- Run `pytest tests/test_phone_parser.py`.
