# Phase 01: Core Parsing & Formatting Utilities
Status: ✅ Completed
Dependencies: None

## Objective
Implement robust Vietnamese short name extraction and role-aware salutation formatting in `app/utils.py`.

## Requirements
### Functional
1. **Given Name Extraction (`extract_short_name`):**
   - Extract the last word of a Vietnamese full name (e.g., "Nguyễn Thị Linh" -> "Linh", "Trần Duy Vũ" -> "Vũ").
   - Handle single-word names ("Linh" -> "Linh").
   - Detect and preserve child fallback phrases (e.g., "phụ huynh bé Nguyễn Văn An" or "Phụ huynh bé Nguyễn Văn An" -> keep as is, do NOT cut to "An").
   - Strip leading/trailing whitespaces and normalize casing properly.

2. **Role Detection Enhancement (`clean_contact_name_and_role`):**
   - Identify the exact role/honorific (e.g. `role: str = "mẹ"`, `"bà"`, `"bố"`, `"bác"`, `"ông"`, `"cô"`, `"chú"`).
   - If child fallback is used when no parent name is provided, format fallback string as `"phụ huynh bé {child_name}"` (replacing `"PH"` with `"phụ huynh"`), setting role to `"phụ huynh"` and `is_mother` to `False`.
   - Ensure backward compatibility: return `(name_final, is_mother, role)`.

3. **Message Formatting (`format_message_for_contact`):**
   - Accept `role: str = ""` alongside `is_mother: bool`.
   - If `role` is "mẹ" (or default mother): keep "mời mẹ {name}" and format `{name}` with short name (e.g., "mời mẹ Linh").
   - If `role` is a non-mother relative ("bà", "bố", "bác", "ông", "cô", "chú"):
     Substitute "mẹ {name}" with "{role} {name}" (e.g., "mời bà Mai", "mời bố Tuấn", "mời bác Hùng").
   - If `role` is "phụ huynh" or starts with "phụ huynh bé":
     Substitute "mời mẹ {name}" with "mời {name}" (resulting in "mời phụ huynh bé Nguyễn Văn An").

## Files to Modify/Create
- `app/utils.py` - Add `extract_short_name`, update `clean_contact_name_and_role` and `format_message_for_contact`.
- `tests/test_short_name_formatting.py` - Create unit tests for given name extraction, role detection, and message formatting.

## Test Criteria
- [x] `extract_short_name("Nguyễn Thị Linh") == "Linh"`
- [x] `extract_short_name("Linh") == "Linh"`
- [x] `extract_short_name("phụ huynh bé Nguyễn Văn An") == "phụ huynh bé Nguyễn Văn An"`
- [x] `format_message_for_contact(template, name="Nguyễn Thị Linh", is_mother=True, role="mẹ")` generates `"mời mẹ Linh"`
- [x] `format_message_for_contact(template, name="Trần Thị Mai", is_mother=False, role="bà")` generates `"mời bà Mai"`
- [x] `format_message_for_contact(template, name="Nguyễn Văn Tuấn", is_mother=False, role="bố")` generates `"mời bố Tuấn"`
- [x] `format_message_for_contact(template, name="phụ huynh bé Nguyễn Văn An", is_mother=False, role="phụ huynh")` generates `"mời phụ huynh bé Nguyễn Văn An"`

---
Next Phase: [Phase 02: Controller & Automation Logic Integration](file:///d:/skul9x/AutoZaloMess-main/plans/261004-0909-short-name-salutation-formatting/phase-02-controller-and-logic-integration.md)
