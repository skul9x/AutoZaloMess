# Plan: Short Name Extraction and Role Salutation Formatting
Created: 2026-10-04T09:09:10+07:00
Status: 🟡 In Progress

## Overview
Improve message personalization in Zalo notifications:
1. Contact table in GUI continues to display full names (e.g., "Nguyễn Thị Linh", "Trần Thị Mai") for easy staff search and verification.
2. In outgoing message bodies, `{name}` is automatically replaced with the contact's given name (last word, e.g., "Linh", "Mai").
3. Preserve relationship titles/honorifics for non-mother contacts (e.g. `(Bà) Trần Thị Mai` -> "mời bà Mai", `(Bố) Nguyễn Văn Tuấn` -> "mời bố Tuấn", `(Bác) Lê Văn Hùng` -> "mời bác Hùng").
4. If no parent name exists and child fallback is used, format as "phụ huynh bé [Tên Bé]" (e.g., "mời phụ huynh bé Nguyễn Văn An"), preserving the entire phrase without truncating to just the child's last name.

## Tech Stack
- Python 3.11+
- Regular Expressions (`re`)
- Pytest (File-based unit & integration tests)

## Phases

| Phase | Name | Description | Status | Test File |
|---|---|---|---|---|
| 01 | Core Parsing & Formatting Utilities | Implement `extract_short_name`, enhanced `clean_contact_name_and_role`, and updated `format_message_for_contact` | ✅ Completed | `tests/test_short_name_formatting.py` |
| 02 | Controller & Automation Logic Integration | Integrate role metadata and short name formatting across `app_controller.py` and `automation_logic.py` | ✅ Completed | `tests/test_automation_message_formatting.py` |

## Quick Commands
- Verify Phase 01: `pytest tests/test_short_name_formatting.py`
- Verify Phase 02: `pytest tests/test_automation_message_formatting.py`
- Run All Tests: `pytest`
