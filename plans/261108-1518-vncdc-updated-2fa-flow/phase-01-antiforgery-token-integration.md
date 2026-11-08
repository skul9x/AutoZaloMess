# Phase 01: AntiForgeryToken & 2FA Header Integration
Status: ✅ Completed
Dependencies: None

## Objective
Update `VncdcClient` in `app/services/vncdc_client.py` to support dynamic Anti-Forgery Token retrieval and supply the mandatory `RequestVerificationToken` HTTP header when verifying two-factor authentication (2FA).

## Scope
- Modify `VncdcClient` service in `app/services/vncdc_client.py`.
- Implement `get_anti_forgery_token()` method that requests `/Account/AntiForgeryToken`.
- Update `verify_2fa(code)` method to acquire the token and include it in request headers.
- Provide a single comprehensive file-based test in `tests/test_vncdc_client_2fa_antiforgery.py`.

## Requirements
### Functional
1. **Token Fetching (`get_anti_forgery_token`):**
   - Must issue `GET` to `/Account/AntiForgeryToken` with a cache-busting timestamp parameter (`_={timestamp_ms}`).
   - Must include standard AJAX headers:
     - `X-Requested-With: XMLHttpRequest`
     - `Referer: {base_url}/Account/VerifyTwoFactor`
     - `Accept: */*`
   - Must parse JSON response `{"token": "..."}` and return the token string.
   - If network request fails or token key is missing, return `None` or raise handled exception without crashing.

2. **2FA Verification Header Update (`verify_2fa`):**
   - Automatically retrieve AntiForgeryToken prior to posting the verification code.
   - Post payload `{"code": code}` to `/Account/VerifyTwoFactor`.
   - Include required headers:
     - `RequestVerificationToken: {token}` (if token is available)
     - `Referer: {base_url}/Account/VerifyTwoFactor`
     - `Origin: {base_url}`
     - `Content-Type: application/x-www-form-urlencoded; charset=UTF-8`
     - `X-Requested-With: XMLHttpRequest`
     - `Accept: application/json, text/javascript, */*; q=0.01`
   - Maintain compatibility with server response formats (JSON `{"Success": true, "Redirect": "..."}` or empty body fallback with `.ASPXAUTH` cookie check).

### Non-Functional & Quality
- Maintain resilient timeout (e.g. 10s timeout for token request).
- Log or handle token retrieval failures gracefully so the client can still attempt OTP verification if the token endpoint is bypassed.

## Constraints
- Do not modify existing public interface signatures of `VncdcClient.verify_2fa(self, code)` so callers (`AppController`) remain unaffected.
- Maintain existing session cookie handling in `httpx.Client`.

## Dependencies
- `app/services/vncdc_client.py`
- `curl_capture_20261108_151208` reference specifications

## Acceptance Criteria
- [x] `VncdcClient` has `get_anti_forgery_token()` returning token string on HTTP 200 JSON response.
- [x] Calling `verify_2fa(code)` sends `POST /Account/VerifyTwoFactor` with header `RequestVerificationToken: {token}` and `Referer: https://tiemchung.vncdc.gov.vn/Account/VerifyTwoFactor`.
- [x] If `VerifyTwoFactor` succeeds (`Success: true` and/or `.ASPXAUTH` present), `verify_2fa` returns `(True, None)`.
- [x] If `VerifyTwoFactor` returns an invalid OTP error, `verify_2fa` returns `(False, "error message")`.
- [x] Exactly one comprehensive test file `tests/test_vncdc_client_2fa_antiforgery.py` tests all token retrieval and header verification scenarios.

## Test Specification
- **Test File:** `tests/test_vncdc_client_2fa_antiforgery.py`
- **Coverage Requirements:**
  - Mocked GET `/Account/AntiForgeryToken` returns valid token JSON -> token parsed correctly.
  - Mocked GET `/Account/AntiForgeryToken` fails -> handled gracefully without crash.
  - Verify `POST /Account/VerifyTwoFactor` receives `RequestVerificationToken` and `Referer` headers.
  - Successful 2FA scenario (with token + correct code) -> returns `(True, None)`.
  - Failed 2FA scenario (wrong code) -> returns `(False, error_msg)`.

---
Next Phase: [Phase 02: Controller State Verification & Error Handling](file:///d:/skul9x/AutoZaloMess-main/plans/261108-1518-vncdc-updated-2fa-flow/phase-02-controller-and-logic-integration.md)

