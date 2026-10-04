# Phase 02: Controller & Automation Logic Integration
Status: ✅ Completed
Dependencies: Phase 01

## Objective
Integrate role-based salutation and short-name formatting into `app/controllers/app_controller.py` and `app/automation_logic.py`, ensuring contact lists maintain full names while outgoing messages use short names and appropriate honorifics.

## Requirements
### Functional
1. **Controller Contacts Storage (`app/controllers/app_controller.py`):**
   - Store full name in `contact["name"]` so the GUI table displays the complete name (e.g., "Nguyễn Thị Linh", "Trần Thị Mai").
   - Store `contact["role"]` (e.g., "mẹ", "bà", "bố", "phụ huynh") alongside `contact["is_mother"]`.
   - Ensure deduplication, backup/restore, and table view continue functioning seamlessly without schema mismatch.

2. **Automation Logic Execution (`app/automation_logic.py`):**
   - Pass `role=contact.get("role", "")` to `format_message_for_contact`.
   - Logging in terminal / UI displays both full contact name and the formatted outgoing greeting.
   - Maintain safety in `try...except` block for formatting errors.

## Files to Modify/Create
- `app/controllers/app_controller.py` - Store `role` in contact dict and update unpack calls.
- `app/automation_logic.py` - Pass `role` through `process_contact` and `run` methods.
- `tests/test_automation_message_formatting.py` - Integration tests verifying end-to-end message generation from contact dictionary.

## Test Criteria
- [x] Controller stores `contact["role"]` correctly from VNCDC raw appointment data.
- [x] Table displays full name ("Nguyễn Thị Linh"), while `format_message_for_contact` invoked during automation generates message with "mẹ Linh".
- [x] End-to-end automation logic verifies correct messages for mother ("mẹ Linh"), grandmother ("bà Mai"), father ("bố Tuấn"), and child fallback ("phụ huynh bé Nguyễn Văn An").
- [x] All existing test suites continue to pass without regression.
