import tkinter as tk
from tkinter import ttk
import sys
import os

# Thêm thư mục gốc vào PYTHONPATH để có thể import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.gui.otp_dialog import OtpDialog

def run_test():
    root = tk.Tk()
    root.title("Test OTP Dialog UI")
    root.geometry("300x200")
    
    # Căn giữa cửa sổ chính
    width = 300
    height = 200
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    label_status = ttk.Label(root, text="Chưa mở Dialog", font=("Helvetica", 12))
    label_status.pack(pady=30)
    
    def open_dialog():
        dialog = OtpDialog(root)
        result = dialog.show()
        if result:
            label_status.config(text=f"Mã OTP đã nhập: {result}")
        else:
            label_status.config(text="Đã hủy hoặc đóng Dialog")
            
    btn_open = ttk.Button(root, text="Mở Dialog OTP", command=open_dialog)
    btn_open.pack()
    
    root.mainloop()

if __name__ == "__main__":
    run_test()
