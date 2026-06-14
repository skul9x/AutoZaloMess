# Phase 03: Upgrade Controller (`app_controller.py`)
Status: ✅ Complete
Dependencies: Phase 02

## Objective
Integrate the phone-fetching mechanism into the `AppController.fetch_task` method to obtain phone numbers for each record in the search results.

## Requirements
### Functional
- In `fetch_task`, check if `doi_tuong_id` is present for each item.
- Extract the numeric ID part (splitting by comma `,` if necessary).
- Query `vncdc_client.get_doi_tuong_phone` for the unmasked phone number.
- Add a tiny delay (e.g. 0.1s - 0.2s) between requests to respect VNCDC server resources and avoid rate limiting.
- Map the retrieved phone number into the contact's payload.

## Implementation Steps
1. [x] Modify the batch fetching loop in `fetch_task` inside `app/controllers/app_controller.py`.
2. [x] Write unit/mock tests in `tests/test_app_controller_phone.py` to verify that `fetch_task` fetches individual phones and processes them correctly.

## Files to Create/Modify
- `app/controllers/app_controller.py` - [Modify] Retrieve phone from edit pages.
- `tests/test_app_controller_phone.py` - [New] Test cases for controller fetching logic.

## Test Criteria
- Verify that individual Edit requests are triggered for each item in the search list.
- Verify that final contacts are correctly populated with unmasked phone numbers.
- Run `pytest tests/test_app_controller_phone.py`.
