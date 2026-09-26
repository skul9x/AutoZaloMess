import os
import re
import json

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

def clean_contact_name_and_role(raw_name: str, child_name: str = "") -> tuple[str, bool]:
    """
    Cleans raw parent/contact name and detects if the person is a mother.

    Rules:
    - If raw_name contains '/', split by '/' and pick the segment containing '(Mẹ)' / 'Mẹ'.
      If mother segment found -> is_mother = True.
    - If no segment contains '(Mẹ)', check for other roles: '(Bà)', '(Bác)', '(Bố)', '(Ông)', etc.
      If non-mother role found -> is_mother = False.
      Otherwise default to True.
    - Strips role markers like (Mẹ), (Bố), (Bà), (Bác), (Ông), (Cô), (Chú), M_, M-, M - .
    - Normalizes the clean name with normalize_name.
    - If clean name is empty or < 2 chars, fallbacks to 'PH bé {child_name}' and is_mother = False.
    """
    if not raw_name:
        raw_name = ""
    raw_name = raw_name.strip()

    is_mother = True
    target_part = raw_name

    if "/" in raw_name:
        parts = [p.strip() for p in raw_name.split("/") if p.strip()]
        mother_part = None
        for part in parts:
            if re.search(r'\b(?:mẹ|me)\b', part, flags=re.IGNORECASE):
                mother_part = part
                break
        if mother_part:
            target_part = mother_part
            is_mother = True
        else:
            target_part = parts[-1]
            if re.search(r'\b(?:bà|ba|bác|bac|bố|bo|ông|ong|cô|co|chú|chu)\b', target_part, flags=re.IGNORECASE):
                is_mother = False
    else:
        if re.search(r'\b(?:mẹ|me)\b', target_part, flags=re.IGNORECASE):
            is_mother = True
        elif re.search(r'\b(?:bà|ba|bác|bac|bố|bo|ông|ong|cô|co|chú|chu)\b', target_part, flags=re.IGNORECASE):
            is_mother = False
        else:
            is_mother = True

    # Strip relationship prefixes: (Mẹ), (Bố), (Bà), Mẹ:, Bà:, etc.
    cleaned = re.sub(
        r'^\s*[\(\[]?\s*(?:Mẹ|Bố|Bà|Ông|Bác|Chú|Cô|Me|Bo|Ba|Ong|Bac|Chu|Co)\s*[\)\]]?\s*[:\-\.]?\s*',
        '',
        target_part,
        flags=re.IGNORECASE
    ).strip()

    # Also clean if any role prefix in parentheses remains anywhere at the start
    cleaned = re.sub(r'^\s*\((?:Mẹ|Bố|Bà|Ông|Bác|Chú|Cô|Me|Bo|Ba|Ong|Bac|Chu|Co)\)\s*', '', cleaned, flags=re.IGNORECASE).strip()

    # Strip vaccination prefix codes: M_, M- , M-, etc.
    cleaned = re.sub(r'^[Mm][_\-]\s*|^[Mm]\s+-\s*', '', cleaned).strip()

    # Fallback if empty or too short
    if not cleaned or len(cleaned) < 2:
        if child_name:
            cleaned = f"PH bé {child_name}".strip()
            is_mother = False
        else:
            cleaned = raw_name
            is_mother = False

    name_final = normalize_name(cleaned)
    return name_final, is_mother

def format_message_for_contact(message_template: str, name: str, phone: str = "", is_mother: bool = True) -> str:
    """Formats message template with contact info, adjusting salutation if not mother."""
    if not is_mother:
        # Remove 'mẹ ' before {name} e.g., 'mời mẹ {name}' -> 'mời {name}'
        tpl = re.sub(r'(mời\s+)mẹ\s+(\{name\})', r'\1\2', message_template, flags=re.IGNORECASE)
        if tpl == message_template:
            tpl = re.sub(r'\bmẹ\s+(\{name\})', r'\1', message_template, flags=re.IGNORECASE)
    else:
        tpl = message_template
    return tpl.format(name=name, phone=phone)