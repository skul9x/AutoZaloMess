import tkinter as tk
from tkinter import ttk, scrolledtext

class GuideTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding="15")
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        guide_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Segoe UI", 11), relief=tk.FLAT)
        guide_text.pack(fill="both", expand=True)
        guide_text.tag_configure("title", font=("Segoe UI", 16, "bold"), spacing3=10)
        guide_text.tag_configure("heading", font=("Segoe UI", 12, "bold"), spacing1=15, spacing3=5)
        guide_text.tag_configure("bullet", lmargin1=20, lmargin2=20, font=("Segoe UI", 11))

        guide_text.insert(tk.END, "Hướng Dẫn Sử Dụng Ứng Dụng\n", "title")
        guide_text.insert(tk.END, "Bước 1: Thiết lập Ảnh báo lỗi (Làm 1 lần)\n", "heading")
        guide_text.insert(tk.END, "• Tìm kiếm một SĐT không tồn tại trên Zalo để Zalo hiển thị thông báo lỗi 'Không tìm thấy'.\n", "bullet")
        guide_text.insert(tk.END, "• Tìm kiếm SĐT liên tục cho đến khi Zalo hiển thị cảnh báo 'Tìm số điện thoại quá nhiều lần...'.\n", "bullet")
        guide_text.insert(tk.END, "• Chụp ảnh màn hình riêng phần thông báo cho từng trường hợp và lưu lại.\n", "bullet")
        guide_text.insert(tk.END, "• Trong tab 'Tự động hóa', nhấn 'Tải ảnh...' và chọn file ảnh bạn vừa chụp cho từng mục tương ứng.\n", "bullet")

        guide_text.insert(tk.END, "Bước 2: Thiết lập Tọa độ\n", "heading")
        guide_text.insert(tk.END, "• Nhấn 'Chọn' cho từng mục và click vào vị trí tương ứng trên Zalo như mô tả.\n", "bullet")

        guide_text.insert(tk.END, "Bước 3: Nhập danh sách và Gửi tin\n", "heading")
        guide_text.insert(tk.END, "• Nhấn 'Nhập file HTML'.\n", "bullet")
        guide_text.insert(tk.END, "• Soạn tin nhắn, sử dụng `{name}` để cá nhân hóa.\n", "bullet")
        guide_text.insert(tk.END, "• Chọn đúng 'Chế độ Zalo' (App hoặc Web) bạn đang dùng.\n", "bullet")
        guide_text.insert(tk.END, "• Nhấn 'Bắt đầu' để chạy.\n", "bullet")

        guide_text.config(state=tk.DISABLED)