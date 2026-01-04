from ..utils import parse_contacts_from_html

class ContactService:
    def import_from_html(self, html_content, sent_phones):
        return parse_contacts_from_html(html_content, sent_phones)

    def import_from_files(self, file_paths, sent_phones):
        html_content = ""
        for path in file_paths:
            with open(path, "r", encoding="utf-8") as f:
                html_content += f.read()
        return self.import_from_html(html_content, sent_phones)