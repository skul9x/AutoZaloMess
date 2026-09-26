# Phase 02: Controller Integration & Safe Cleanup
Status: ✅ Completed
Dependencies: Phase 01

## Objective
Refactor `handle_vncdc_fetch` / `fetch_task` in `app/controllers/app_controller.py` to coordinate the new flow:
1. Search targets by date range and communes.
2. Temporarily inject targets into the plan.
3. Retrieve full contact details with unmasked phone numbers directly from the appointment list.
4. Guarantee immediate and complete removal of all added targets via `try ... finally`.

## Requirements
### Functional
- Target Search:
  - Query each commune (`XA_ID`) across all pages for the configured birth date range (`date_from` to `date_to`).
  - Extract unique `doi_tuong_id` integers.
- Temporary Injection & Extraction:
  - Batch target IDs and invoke `client.nhap_bo_sung_doi_tuong(...)`.
  - Query `client.get_danh_sach_hen_tiem(...)` to receive JSON appointments.
  - Extract `DIEN_THOAI`, `TEN_ME`, `HO_TEN`, `DIA_CHI`, `DOI_TUONG_ID`, and `KE_HOACH_TIEM_CHI_TIET_ID`.
  - Filter out records where phone number is missing or empty.
- Strict Cleanup Guarantee:
  - Execute deletion in a `try ... finally` block.
  - Only delete target IDs that were injected during this session (`added_doi_tuong_ids`), ensuring pre-existing plan data is untouched.
  - For each injected target, invoke `client.xoa_doi_tuong_hen_tiem(ke_hoach_id, doi_tuong_id, ke_hoach_tiem_ct_id)`.
- UI & Storage Synchronization:
  - Format contact names (`TEN_ME` or fallback `PH bé {HO_TEN}`).
  - Deduplicate phone numbers and skip numbers already in `sent_database.json`.
  - Push contacts to automation tab and update UI progress counter.

### Non-Functional
- Resilience: If network drops during fetching, the finally block still executes cleanup for all injected items.
- Maintain UI responsiveness via existing queue/threading pattern.

## Files to Create/Modify
- `app/controllers/app_controller.py`: Implement the temporary injection, appointment retrieval, and safe cleanup in `fetch_task`.
- `tests/test_app_controller_fetch_cleanup.py`: Comprehensive test file verifying the entire orchestration and cleanup guarantee.

## Test Verification
- Exactly one comprehensive test file:
  `pytest tests/test_app_controller_fetch_cleanup.py`
  - Verifies targets are searched, temporarily added, appointments fetched, and deleted.
  - Verifies cleanup is invoked even if an exception occurs during contact parsing.
