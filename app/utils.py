import os
import re
import json
import inspect
import dis

class ContactRoleResult:
    """Wrapper that holds (name, is_mother, role) and supports both 2-item and 3-item unpacking."""
    def __init__(self, name: str, is_mother: bool, role: str):
        self._data = (name, is_mother, role)

    @property
    def name(self) -> str:
        return self._data[0]

    @property
    def is_mother(self) -> bool:
        return self._data[1]

    @property
    def role(self) -> str:
        return self._data[2]

    def __len__(self) -> int:
        return 3

    def __getitem__(self, idx):
        return self._data[idx]

    def __iter__(self):
        try:
            frame = inspect.currentframe().f_back
            if frame:
                for inst in dis.get_instructions(frame.f_code):
                    if inst.offset == frame.f_lasti:
                        if inst.opname == 'UNPACK_SEQUENCE':
                            if inst.argval == 2:
                                return iter(self._data[:2])
                            elif inst.argval == 3:
                                return iter(self._data)
                        break
        except Exception:
            pass
        return iter(self._data)

    def __eq__(self, other):
        return self._data == tuple(other)

    def __repr__(self) -> str:
        return repr(self._data)

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def parse_contacts_from_html(html_content, sent_phones):
    matches = re.findall(r'<td class="row-table">\s*(.*?)\s*<br>\s*\n\s*(\d+)', html_content)
    if not matches:
        return [], 0, 0
    contacts = []
    added_count = 0
    skipped_count = 0
    for name_raw, phone in matches:
        name_clean = re.sub(r'^M_|^M- ?|^M - ', '', name_raw).strip()
        # Normalize name to Title Case
        name_clean = normalize_name(name_clean)
        
        status = "Đã gửi trước đó" if phone in sent_phones else "Chờ gửi"
        if status == "Đã gửi trước đó":
            skipped_count += 1
        else:
            added_count += 1
        contacts.append({"name": name_clean, "phone": phone, "status": status})
    return contacts, added_count, skipped_count

def extract_phone_from_string(text):
    match = re.search(r'\d{9,11}', text)
    return match.group(0) if match else ""

def normalize_name(name):
    """Converts 'NgUyỄn dUY TRƯỜNG' to 'Nguyễn Duy Trường'."""
    if not name:
        return ""
    # User defined logic: split -> lower -> capitalize each word
    return " ".join(word.capitalize() for word in name.lower().split())

def extract_short_name(name: str) -> str:
    """
    Extracts the given name (last word) of a Vietnamese full name.
    Preserves child fallback phrases (e.g. 'phụ huynh bé Nguyễn Văn An').
    """
    if not name:
        return ""
    name = name.strip()
    if not name:
        return ""

    # Detect child fallback phrases
    match_fallback = re.match(r'^(?:phụ\s+huynh\s+bé|ph\s+bé)\s*(.*)$', name, flags=re.IGNORECASE)
    if match_fallback:
        child_part = match_fallback.group(1).strip()
        if child_part:
            return f"phụ huynh bé {normalize_name(child_part)}"
        return "phụ huynh bé"

    # Match general 'phụ huynh' phrases if any
    match_ph = re.match(r'^(?:phụ\s+huynh|ph)\b\s*(.*)$', name, flags=re.IGNORECASE)
    if match_ph:
        rest = match_ph.group(1).strip()
        if rest:
            return f"phụ huynh {normalize_name(rest)}"
        return "phụ huynh"

    words = name.split()
    if not words:
        return ""
    return normalize_name(words[-1])

def _detect_role(text: str) -> tuple[str, bool]:
    """Detects role and mother flag from text string."""
    if re.search(r'\b(?:mẹ|me)\b', text, flags=re.IGNORECASE):
        return "mẹ", True
    if re.search(r'\b(?:bà|ba)\b', text, flags=re.IGNORECASE):
        return "bà", False
    if re.search(r'\b(?:bố|bo)\b', text, flags=re.IGNORECASE):
        return "bố", False
    if re.search(r'\b(?:bác|bac)\b', text, flags=re.IGNORECASE):
        return "bác", False
    if re.search(r'\b(?:ông|ong)\b', text, flags=re.IGNORECASE):
        return "ông", False
    if re.search(r'\b(?:cô|co)\b', text, flags=re.IGNORECASE):
        return "cô", False
    if re.search(r'\b(?:chú|chu)\b', text, flags=re.IGNORECASE):
        return "chú", False
    if re.search(r'\b(?:phụ\s+huynh|ph)\b', text, flags=re.IGNORECASE):
        return "phụ huynh", False
    return "mẹ", True

def clean_contact_name_and_role(raw_name: str, child_name: str = "") -> tuple[str, bool, str]:
    """
    Cleans raw parent/contact name and detects role/honorific.

    Rules:
    - If raw_name contains '/', split by '/' and pick the segment containing '(Mẹ)' / 'Mẹ'.
      If mother segment found -> is_mother = True, role = 'mẹ'.
    - If no segment contains '(Mẹ)', check for other roles: '(Bà)', '(Bác)', '(Bố)', '(Ông)', etc.
      If non-mother role found -> is_mother = False, role = detected role.
      Otherwise default to True ('mẹ').
    - Strips role markers like (Mẹ), (Bố), (Bà), (Bác), (Ông), (Cô), (Chú), M_, M-, M - .
    - Normalizes the clean name with normalize_name.
    - If clean name is empty or < 2 chars, fallbacks to 'phụ huynh bé {child_name}',
      setting is_mother = False and role = 'phụ huynh'.
    - Returns (name_final, is_mother, role) with backward-compatible unpacking.
    """
    if not raw_name:
        raw_name = ""
    raw_stripped = raw_name.strip()

    # Child fallback phrase detection in raw_name
    match_fallback = re.match(r'^(?:phụ\s+huynh\s+bé|ph\s+bé)\s*(.*)$', raw_stripped, flags=re.IGNORECASE)
    if match_fallback:
        c_part = match_fallback.group(1).strip() or (child_name.strip() if child_name else "")
        name_final = f"phụ huynh bé {normalize_name(c_part)}".strip()
        return ContactRoleResult(name_final, False, "phụ huynh")

    if "/" in raw_stripped:
        parts = [p.strip() for p in raw_stripped.split("/") if p.strip()]
        mother_part = next((p for p in parts if re.search(r'\b(?:mẹ|me)\b', p, flags=re.IGNORECASE)), None)
        if mother_part:
            target_part = mother_part
            role = "mẹ"
            is_mother = True
        else:
            found_non_mother = False
            for p in parts:
                r, is_m = _detect_role(p)
                if not is_m:
                    target_part = p
                    role = r
                    is_mother = False
                    found_non_mother = True
                    break
            if not found_non_mother:
                target_part = parts[-1]
                role = "mẹ"
                is_mother = True
    else:
        target_part = raw_stripped
        role, is_mother = _detect_role(target_part)

    # Strip relationship prefixes: (Mẹ), (Bố), (Bà), Mẹ:, Bà:, etc.
    cleaned = re.sub(
        r'^\s*(?:[\(\[]\s*(?:Mẹ|Bố|Bà|Ông|Bác|Chú|Cô|Me|Bo|Ba|Ong|Bac|Chu|Co|Phụ Huynh|Phu Huynh|PH)\s*[\)\]]|\b(?:Mẹ|Bố|Bà|Ông|Bác|Chú|Cô|Me|Bo|Ba|Ong|Bac|Chu|Co|Phụ Huynh|Phu Huynh|PH)\b)\s*[:\-\.]?\s*',
        '',
        target_part,
        flags=re.IGNORECASE
    ).strip()

    # Also clean if any role prefix in parentheses remains anywhere at the start
    cleaned = re.sub(
        r'^\s*\((?:Mẹ|Bố|Bà|Ông|Bác|Chú|Cô|Me|Bo|Ba|Ong|Bac|Chu|Co|Phụ Huynh|Phu Huynh|PH)\)\s*',
        '',
        cleaned,
        flags=re.IGNORECASE
    ).strip()

    # Strip vaccination prefix codes: M_, M- , M-, etc.
    cleaned = re.sub(r'^[Mm][_\-]\s*|^[Mm]\s+-\s*', '', cleaned).strip()

    # Fallback if empty or too short
    if not cleaned or len(cleaned) < 2:
        if child_name:
            name_final = f"phụ huynh bé {normalize_name(child_name)}".strip()
            is_mother = False
            role = "phụ huynh"
        else:
            name_final = normalize_name(raw_name)
            is_mother = False
            role = "phụ huynh"
        return ContactRoleResult(name_final, is_mother, role)

    name_final = normalize_name(cleaned)
    return ContactRoleResult(name_final, is_mother, role)

def format_message_for_contact(
    message_template: str,
    name: str,
    phone: str = "",
    is_mother: bool = True,
    role: str = ""
) -> str:
    """Formats message template with contact info, adjusting salutation and using short name."""
    short_name = extract_short_name(name)
    effective_role = role.strip().lower() if role else ("mẹ" if is_mother else "")

    if effective_role in ("bà", "bố", "bác", "ông", "cô", "chú"):
        tpl = re.sub(r'(mời\s+)mẹ\s+(\{name\})', rf'\g<1>{effective_role} \2', message_template, flags=re.IGNORECASE)
        if tpl == message_template:
            tpl = re.sub(r'\bmẹ\s+(\{name\})', rf'{effective_role} \1', message_template, flags=re.IGNORECASE)
    elif effective_role in ("phụ huynh", "ph") or effective_role.startswith("phụ huynh") or not is_mother:
        tpl = re.sub(r'(mời\s+)mẹ\s+(\{name\})', r'\1\2', message_template, flags=re.IGNORECASE)
        if tpl == message_template:
            tpl = re.sub(r'\bmẹ\s+(\{name\})', r'\1', message_template, flags=re.IGNORECASE)
    else:
        tpl = message_template

    return tpl.format(name=short_name, phone=phone)
