import os
import base64
import json
from . import __init__
from ..constants import DEFAULT_MESSAGE, CONFIG_FILE, COORDS_FILE, SENT_DB_FILE, IMAGE_CONFIG_FILE
from ..utils import load_json, save_json

CREDENTIALS_FILE = "config.json"

class StorageService:
    def load_message(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return DEFAULT_MESSAGE
        return DEFAULT_MESSAGE

    def save_message(self, message):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(message)

    def load_coords(self):
        return load_json(COORDS_FILE, {})

    def save_coords(self, coords_dict):
        save_json(COORDS_FILE, coords_dict)

    def load_image_config(self):
        return load_json(IMAGE_CONFIG_FILE, {})

    def save_image_config(self, image_dict):
        save_json(IMAGE_CONFIG_FILE, image_dict)

    def load_sent_database(self):
        data = load_json(SENT_DB_FILE, [])
        try:
            return set(data)
        except Exception:
            return set()

    def add_phone_to_database(self, sent_phones, phone_number):
        sent_phones.add(phone_number)
        save_json(SENT_DB_FILE, list(sent_phones))

    def load_xa_ids(self):
        """Feature: Load list of XA_IDs."""
        # Assuming xa_settings.json is in the same directory as other config files
        # or a default data directory if self.data_dir were initialized.
        # For now, using a direct file name similar to CREDENTIALS_FILE.
        return load_json("xa_settings.json", [])

    def save_xa_ids(self, xa_ids):
        """Feature: Save list of XA_IDs."""
        # Assuming xa_settings.json is in the same directory as other config files
        # or a default data directory if self.data_dir were initialized.
        save_json("xa_settings.json", xa_ids)

    # --- Credentials Management (Feature 3) ---
    def _obfuscate(self, text):
        """Simple Base64 encoding to hide plain text."""
        return base64.b64encode(text.encode("utf-8")).decode("utf-8")

    def _deobfuscate(self, encoded_text):
        """Decode Base64."""
        try:
            return base64.b64decode(encoded_text).decode("utf-8")
        except Exception:
            return ""

    def save_credentials(self, username, password):
        data = {
            "username": self._obfuscate(username),
            "password": self._obfuscate(password)
        }
        save_json(CREDENTIALS_FILE, data)

    def load_credentials(self):
        data = load_json(CREDENTIALS_FILE, {})
        if not data:
            return "", ""
        
        u = self._deobfuscate(data.get("username", ""))
        p = self._deobfuscate(data.get("password", ""))
        return u, p