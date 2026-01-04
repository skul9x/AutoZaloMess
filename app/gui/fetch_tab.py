import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import date, timedelta

class FetchTab(ttk.Frame):
    def __init__(self, master, state, callbacks):
        super().__init__(master, padding="15")
        self.state = state
        self.callbacks = callbacks
        self._build()

    def _build(self):
        # --- Login Section ---
        login_frame = ttk.LabelFrame(self, text="1. Đăng nhập hệ thống VNCDC", padding=15)
        login_frame.pack(fill="x", pady=(0, 15))
        login_frame.columnconfigure(1, weight=1)

        ttk.Label(login_frame, text="Tên đăng nhập:").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)

        ttk.Label(login_frame, text="Mật khẩu:").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(login_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)

        self.remember_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(login_frame, text="Ghi nhớ và Lưu mật khẩu", variable=self.remember_var).grid(row=2, column=1, sticky="w", padx=(10, 0))

        self.login_btn = ttk.Button(login_frame, text="Đăng nhập", command=self._on_login_click)
        self.login_btn.grid(row=3, column=1, sticky="e", pady=(10, 0))

        self.login_status_label = ttk.Label(login_frame, text="Chưa đăng nhập", foreground="grey")
        self.login_status_label.grid(row=3, column=0, sticky="w", pady=(10, 0))

        # --- Search Section ---
        search_frame = ttk.LabelFrame(self, text="2. Lấy dữ liệu tiêm chủng", padding=15)
        search_frame.pack(fill="x", pady=10)
        search_frame.columnconfigure(1, weight=1)
        search_frame.columnconfigure(3, weight=1)

        # Calculate default dates
        today = date.today()
        week_ago = today - timedelta(days=7)

        ttk.Label(search_frame, text="Ngày sinh từ:").grid(row=0, column=0, sticky="w", pady=5)
        self.date_from_entry = DateEntry(search_frame, width=12, background='darkblue',
                                         foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.date_from_entry.set_date(week_ago)
        self.date_from_entry.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ttk.Label(search_frame, text="đến ngày:").grid(row=0, column=2, sticky="w", pady=5)
        self.date_to_entry = DateEntry(search_frame, width=12, background='darkblue',
                                       foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.date_to_entry.set_date(today)
        self.date_to_entry.grid(row=0, column=3, sticky="w", padx=10, pady=5)

        self.fetch_btn = ttk.Button(search_frame, text="Lấy dữ liệu & Chuyển sang AutoZalo", command=self._on_fetch_click, state=tk.DISABLED)
        self.fetch_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(15, 0), ipady=5, padx=(0, 5))
        
        self.config_xa_btn = ttk.Button(search_frame, text="Cấu hình Xã (XA_ID)", command=self._on_config_xa_click)
        self.config_xa_btn.grid(row=2, column=2, columnspan=2, sticky="ew", pady=(15, 0), ipady=5, padx=(5, 0))

        self.fetch_status_label = ttk.Label(search_frame, text="", foreground="#005a9e")
        self.fetch_status_label.grid(row=3, column=0, columnspan=4, pady=(10, 0))

        # --- Info Section ---
        info_frame = ttk.Frame(self)
        info_frame.pack(fill="both", expand=True, pady=10)
        info_text = "Lưu ý: \n- Cần đăng nhập thành công trước khi lấy dữ liệu.\n- Dữ liệu sau khi lấy sẽ tự động được điền vào tab 'Tự động hóa'."
        lbl_info = ttk.Label(info_frame, text=info_text, foreground="grey", justify=tk.LEFT)
        lbl_info.pack(anchor="w")

    def _on_login_click(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get().strip()
        remember = self.remember_var.get()
        if self.callbacks.get("on_login"):
            self.callbacks["on_login"](u, p, remember)

    def _on_fetch_click(self):
        d_from = self.date_from_entry.get()
        d_to = self.date_to_entry.get()
        if self.callbacks.get("on_fetch"):
            self.callbacks["on_fetch"](d_from, d_to)
            
    def _on_config_xa_click(self):
        if self.callbacks.get("on_configure_xa"):
            self.callbacks["on_configure_xa"]()

    def set_login_status(self, status, color="black", is_success=False):
        self.login_status_label.config(text=status, foreground=color)
        if is_success:
            self.fetch_btn.config(state=tk.NORMAL)
            self.login_btn.config(state=tk.DISABLED)
            self.username_entry.config(state=tk.DISABLED)
            self.password_entry.config(state=tk.DISABLED)
            
    def set_credentials(self, username, password):
        """Feature 3: Pre-fill credentials"""
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, username)
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, password)

    def set_fetch_status(self, text):
        self.fetch_status_label.config(text=text)

    def get_login_info(self):
        return self.username_entry.get(), self.password_entry.get(), self.remember_var.get()

    def show_xa_settings_dialog(self, load_callback, save_callback):
        dialog = tk.Toplevel(self)
        dialog.title("Cấu hình danh sách Xã (XA_ID)")
        dialog.geometry("500x450")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_screenwidth() // 2 - 250
        y = self.winfo_screenheight() // 2 - 225
        dialog.geometry(f"+{x}+{y}")

        # Main layout container
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill="both", expand=True)

        # 1. Bottom Frame (Save button) - Pack this first (or use side=bottom) to ensure visibility
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        ttk.Separator(bottom_frame, orient="horizontal").pack(fill="x", pady=(0, 10))
        
        def save_and_close():
            # Need to access lb from here. lb will be defined in top_frame
            new_ids = list(lb.get(0, tk.END))
            save_callback(new_ids)
            dialog.destroy()
            tk.messagebox.showinfo("Đã lưu", f"Đã lưu {len(new_ids)} mã xã.", parent=self)

        ttk.Button(bottom_frame, text="Lưu & Đóng", command=save_and_close).pack(side="right")
        ttk.Button(bottom_frame, text="Hủy", command=dialog.destroy).pack(side="right", padx=5)

        # 2. Top Content Frame (Label, Listbox, Add/Import inputs)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(side="top", fill="both", expand=True)

        ttk.Label(top_frame, text="Danh sách Mã Xã (XA_ID) cần lấy dữ liệu:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))

        list_frame = ttk.Frame(top_frame)
        list_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        lb = tk.Listbox(list_frame, height=10, yscrollcommand=scrollbar.set)
        lb.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=lb.yview)

        # Load existing IDs
        current_ids = load_callback()
        for xid in current_ids:
            lb.insert(tk.END, xid)

        # Controls under listbox
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(fill="x", pady=10)

        entry_var = tk.StringVar()
        entry = ttk.Entry(btn_frame, textvariable=entry_var)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def add_id():
            val = entry_var.get().strip()
            if val:
                if val not in lb.get(0, tk.END):
                    lb.insert(tk.END, val)
                    entry_var.set("")
                else:
                    tk.messagebox.showwarning("Trùng lặp", "Mã xã này đã tồn tại.", parent=dialog)
        
        entry.bind("<Return>", lambda e: add_id())

        def delete_id():
            sel = lb.curselection()
            if sel:
                lb.delete(sel)
        
        def import_from_file():
            file_path = tk.filedialog.askopenfilename(
                title="Chọn file TXT chứa danh sách Xã",
                filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
                parent=dialog
            )
            if not file_path:
                return
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Handle formatted like: 1060501; \n 1060511;
                normalized = content.replace(";", " ")
                ids = normalized.split()
                
                added_count = 0
                existing = lb.get(0, tk.END)
                
                for xid in ids:
                    xid = xid.strip()
                    if xid.isdigit() and xid not in existing:
                        lb.insert(tk.END, xid)
                        added_count += 1
                        existing = lb.get(0, tk.END) 
                
                tk.messagebox.showinfo("Import hoàn tất", f"Đã thêm {added_count} mã xã mới.", parent=dialog)
                
            except Exception as e:
                tk.messagebox.showerror("Lỗi Import", f"Không thể đọc file: {e}", parent=dialog)

        ttk.Button(btn_frame, text="Thêm", command=add_id).pack(side="left")
        ttk.Button(btn_frame, text="Import từ file .txt", command=import_from_file).pack(side="left", padx=5)
        
        ttk.Button(top_frame, text="Xóa dòng chọn", command=delete_id).pack(anchor="w", pady=(0, 0))