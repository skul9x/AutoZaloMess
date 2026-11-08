# Plan: VNCDC Updated 2FA AntiForgeryToken Flow
Created: 2026-11-08T15:18:00+07:00
Status: ✅ Completed

## Overview
Update the VNCDC client authentication and two-factor verification (2FA) mechanisms to comply with the updated VNCDC security requirements observed in November 2026 network captures (`curl_capture_20261108_151208`):
1. **AntiForgeryToken Retrieval**: Before submitting OTP verification, client must fetch an anti-forgery token via `GET /Account/AntiForgeryToken?_={timestamp_ms}`.
2. **2FA Header Verification**: When posting OTP to `POST /Account/VerifyTwoFactor`, client must attach the header `RequestVerificationToken: {token}` and proper `Referer` (`https://tiemchung.vncdc.gov.vn/Account/VerifyTwoFactor`).
3. **Session Verification & Integration**: Ensure successful OTP verification sets `.ASPXAUTH` session cookie, updates controller state seamlessly, and remains resilient with appropriate fallbacks.

## Tech Stack
- Python 3.11+
- HTTPX (`httpx.Client`)
- Pytest (Comprehensive unit & integration tests)

## Phases

| Phase | Name | Description | Status | Test File |
|---|---|---|---|---|
| 01 | AntiForgeryToken & 2FA Header Integration | Implement token retrieval helper and attach `RequestVerificationToken` header to `VerifyTwoFactor` in `VncdcClient` | ✅ Completed | `tests/test_vncdc_client_2fa_antiforgery.py` |
| 02 | Controller State Verification & Error Handling | Verify controller flow integration, OTP error propagation, and session recovery in `AppController` | ✅ Completed | `tests/test_vncdc_2fa_controller_integration.py` |

## Quick Commands
- Verify Phase 01: `python -m pytest tests/test_vncdc_client_2fa_antiforgery.py`
- Verify Phase 02: `python -m pytest tests/test_vncdc_2fa_controller_integration.py`
- Run All 2FA Tests: `python -m pytest tests/test_vncdc_client_2fa.py tests/test_vncdc_client_2fa_antiforgery.py tests/test_vncdc_2fa_controller_integration.py`

