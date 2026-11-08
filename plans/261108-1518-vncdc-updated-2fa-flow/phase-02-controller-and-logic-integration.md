# Phase 02: Controller State Verification & Error Handling
Status: ✅ Completed
Dependencies: Phase 01: AntiForgeryToken & 2FA Header Integration

## Objective
Verify and validate the end-to-end integration between `AppController`, the UI dialog triggers, and the updated `VncdcClient.verify_2fa` implementation, ensuring proper UI callback messaging, error propagation, and post-authentication state updates.

## Scope
- Ensure `AppController.handle_vncdc_login` and its OTP verification worker handle the new 2FA verification responses correctly.
- Ensure post-login workflow (`fetch_profile_and_plan`) executes smoothly upon successful 2FA verification.
- Ensure proper error message rendering in `OtpDialog` when 2FA verification fails or when network issues prevent token retrieval.
- Provide a single comprehensive file-based test in `tests/test_vncdc_2fa_controller_integration.py`.

## Requirements
### Functional
1. **Controller OTP Worker Verification:**
   - When OTP verification is triggered from the UI, `verify_task` in `app_controller.py` must invoke `client.verify_2fa(otp)`.
   - On success (`True, None`):
     - Trigger `client.fetch_profile_and_plan()`.
     - Push `("otp_verify_result", True, (client, profile, ke_hoach_id))` to `comm_queue`.
     - Store client instance and update UI fetch status to logged in.
   - On failure (`False, err`):
     - Push `("otp_verify_result", False, err)` to `comm_queue`.
     - Allow user to re-enter OTP or re-trigger verification.

2. **Network/Exception Resiliency:**
   - Any unhandled exceptions during token retrieval or 2FA request execution inside the background worker must be captured and pushed as `("otp_verify_result", False, f"Lỗi: {e}")`.

### Non-Functional & Quality
- Ensure asynchronous worker thread does not block Tkinter UI main loop.
- Guarantee thread safety via `comm_queue`.

## Constraints
- Do not introduce breaking changes to `AppController.comm_queue` event types.
- Preserve UI lifecycle for `OtpDialog` and parent window.

## Dependencies
- `app/controllers/app_controller.py`
- `app/services/vncdc_client.py` (updated in Phase 01)
- `Phase 01` implementation

## Acceptance Criteria
- [x] End-to-end simulation of 2FA flow through `AppController` succeeds when valid token and OTP are provided.
- [x] Controller correctly triggers profile/plan retrieval on successful 2FA.
- [x] Controller properly signals verification failure on invalid OTP or network error.
- [x] Exactly one comprehensive test file `tests/test_vncdc_2fa_controller_integration.py` verifies the controller flow and worker queue messages.

## Test Specification
- **Test File:** `tests/test_vncdc_2fa_controller_integration.py`
- **Coverage Requirements:**
  - Mock full sequence: Login -> `2fa_required` -> OTP submit -> `verify_2fa` with AntiForgeryToken -> `fetch_profile_and_plan` -> Queue receives success event.
  - Mock OTP failure sequence: OTP submit -> `verify_2fa` failure -> Queue receives error event.
  - Mock unexpected exception: Worker catches exception and posts formatted error to Queue.

---
Phase Complete.

