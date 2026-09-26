# Plan: VNCDC Temporary Plan Injection and Safe Cleanup Flow
Created: 2026-09-26T09:36:00+07:00
Status: ✅ Completed

## Overview
Adapt the contact fetching algorithm to the latest VNCDC workflow:
1. Search targets by date of birth and commune (XA_ID) as before.
2. Temporarily inject target IDs into the active vaccination plan (`NhapBoSungDoiTuong`).
3. Fetch appointment targets via JSON (`GetDanhSachHenTiemByParams`) to retrieve unmasked phone numbers, parent names, child names, and addresses.
4. Guaranteed cleanup: Immediately remove all newly injected targets from the vaccination plan (`XoaDoiTuongDSHenTiem`), restoring the plan to its pristine state without leaving any residual entries.

## Tech Stack
- Python 3.11+
- HTTPX (HTTP client)
- Tkinter & Threading (UI & Queue)
- Pytest (Unit & Integration tests)

## Phases

| Phase | Name | Status | Test File |
|-------|------|--------|-----------|
| 01 | VNCDC Client API Expansion | ✅ Completed | `tests/test_vncdc_client_plan_flow.py` |
| 02 | Controller Integration & Safe Cleanup | ✅ Completed | `tests/test_app_controller_fetch_cleanup.py` |

## Quick Commands
- Verify Phase 01: `pytest tests/test_vncdc_client_plan_flow.py`
- Verify Phase 02: `pytest tests/test_app_controller_fetch_cleanup.py`
