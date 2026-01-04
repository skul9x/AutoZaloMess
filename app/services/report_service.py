import csv

class ReportService:
    def export_csv(self, file_path, contacts):
        with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["STT", "Số điện thoại", "Tên khách hàng", "Trạng thái"])
            for i, contact in enumerate(contacts, 1):
                writer.writerow([i, contact["phone"], contact["name"], contact.get("status", "N/A")])