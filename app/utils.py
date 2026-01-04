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