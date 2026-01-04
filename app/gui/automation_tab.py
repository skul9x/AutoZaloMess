import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

class AutomationTab(ttk.Frame):
    def __init__(self, master, state, callbacks):
        super().__init__(master)
        self.state = state
        self.callbacks = callbacks
        self._build()

    def _build(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.rowconfigure(1, weight=1)

        msg_frame = ttk.LabelFrame(left_frame, text="Nội dung tin nhắn", padding=5)
        msg_frame.pack(fill="x", pady=(0, 10))
        self.message_text_area = scrolledtext.ScrolledText(msg_frame, wrap=tk.WORD, height=8, font=("Segoe UI", 10))
        self.message_text_area.pack(fill="x", expand=True)
        self.message_text_area.insert(tk.INSERT, self.state["initial_message"])

        list_frame = ttk.LabelFrame(left_frame, text="Danh sách liên hệ (Double Click để copy)", padding=5)
        list_frame.pack(fill="both", expand=True)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(list_frame, columns=("stt", "phone", "name", "status"), show="headings", selectmode="extended")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.heading("stt", text="STT")
        self.tree.column("stt", width=40, anchor="center")
        self.tree.heading("phone", text="Số điện thoại")
        self.tree.column("phone", width=120)
        self.tree.heading("name", text="Tên khách hàng")
        self.tree.column("name", width=150)
        self.tree.heading("status", text="Trạng thái")
        self.tree.column("status", width=120)
        
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.callbacks["on_selection_change"]())
        # Feature 2: Double click to copy
        self.tree.bind("<Double-1>", self._on_double_click)

        self.tree.tag_configure("success", foreground="green")
        self.tree.tag_configure("failure", foreground="red")
        self.tree.tag_configure("processing", foreground="#0078D7")
        self.tree.tag_configure("sent_before", foreground="grey")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscroll=scrollbar.set)

        list_manage_frame = ttk.Frame(list_frame)
        list_manage_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        self.contact_status_label = ttk.Label(list_manage_frame, text="Tổng số: 0 | Đã chọn: 0")
        self.contact_status_label.pack(side="left")
        ttk.Button(list_manage_frame, text="Xóa đã chọn", command=self.callbacks["delete_selected_contacts"]).pack(side="right")
        self.export_button = ttk.Button(list_manage_frame, text="Xuất báo cáo CSV", command=self.callbacks["export_report"])
        self.export_button.pack(side="right", padx=5)

        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.rowconfigure(3, weight=1)

        control_frame = ttk.LabelFrame(right_frame, text="Điều khiển", padding=10)
        control_frame.pack(fill="x")

        mode_frame = ttk.Frame(control_frame)
        mode_frame.pack(pady=5, anchor="w", fill="x")
        ttk.Label(mode_frame, text="Chế độ Zalo:").pack(side="left")
        self.radio_app = ttk.Radiobutton(mode_frame, text="Zalo App", variable=self.state["zalo_mode"], value="app", command=self.callbacks["update_ui_state"])
        self.radio_app.pack(side="left", padx=10)
        self.radio_web = ttk.Radiobutton(mode_frame, text="Zalo Web", variable=self.state["zalo_mode"], value="web", command=self.callbacks["update_ui_state"])
        self.radio_web.pack(side="left")

        self.start_button = ttk.Button(control_frame, text="Bắt đầu (F9)", style="Accent.TButton", command=self.callbacks["handle_start"])
        self.start_button.pack(fill="x", ipady=8, pady=5)

        self.pause_resume_frame = ttk.Frame(control_frame)
        self.pause_resume_frame.pack(fill="x", pady=5)
        self.pause_button = ttk.Button(self.pause_resume_frame, text="Tạm dừng (F10)", command=self.callbacks["handle_pause"])
        self.resume_button = ttk.Button(self.pause_resume_frame, text="Tiếp tục (F10)", command=self.callbacks["handle_resume"])

        self.cancel_button = ttk.Button(control_frame, text="Hủy bỏ (F11)", command=self.callbacks["handle_cancel"])
        self.cancel_button.pack(fill="x", ipady=5, pady=5)
        self.status_label = ttk.Label(control_frame, text="", font=("Segoe UI", 10, "bold"), foreground="#0078D7")
        self.status_label.pack(pady=(10, 0))

        coords_frame = ttk.LabelFrame(right_frame, text="Thiết lập Tọa độ", padding=10)
        coords_frame.pack(fill="x", pady=10)
        coords_frame.columnconfigure(1, weight=1)

        ttk.Label(coords_frame, text="Ô tìm kiếm Zalo:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(coords_frame, textvariable=self.state["coord_vars"]["search_coords"], state="readonly").grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(coords_frame, text="Chọn", command=lambda: self.callbacks["capture_coordinate"]("search_coords")).grid(row=0, column=2)

        ttk.Label(coords_frame, text="Tọa độ hiển thị tên khi tìm kiếm:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(coords_frame, textvariable=self.state["coord_vars"]["friend_coords"], state="readonly").grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(coords_frame, text="Chọn", command=lambda: self.callbacks["capture_coordinate"]("friend_coords")).grid(row=1, column=2)

        ttk.Label(coords_frame, text="Ô soạn tin nhắn:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(coords_frame, textvariable=self.state["coord_vars"]["messagebox_coords"], state="readonly").grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Button(coords_frame, text="Chọn", command=lambda: self.callbacks["capture_coordinate"]("messagebox_coords")).grid(row=2, column=2)

        image_frame = ttk.LabelFrame(right_frame, text="Thiết lập ảnh báo lỗi", padding=10)
        image_frame.pack(fill="x", pady=10)
        image_frame.columnconfigure(1, weight=1)

        ttk.Label(image_frame, text="Ảnh SĐT không tồn tại (App):").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(image_frame, textvariable=self.state["image_path_vars"]["app_fail_path"], state="readonly").grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(image_frame, text="Tải ảnh...", command=lambda: self.callbacks["handle_load_fail_image"]("app_fail_path")).grid(row=0, column=2)

        ttk.Label(image_frame, text="Ảnh SĐT không tồn tại (Web):").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(image_frame, textvariable=self.state["image_path_vars"]["web_fail_path"], state="readonly").grid(row=1, column=1, padx=5, sticky="ew")
        ttk.Button(image_frame, text="Tải ảnh...", command=lambda: self.callbacks["handle_load_fail_image"]("web_fail_path")).grid(row=1, column=2)

        ttk.Label(image_frame, text="Ảnh bị giới hạn tìm kiếm (App):").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(image_frame, textvariable=self.state["image_path_vars"]["app_ratelimit_path"], state="readonly").grid(row=2, column=1, padx=5, sticky="ew")
        ttk.Button(image_frame, text="Tải ảnh...", command=lambda: self.callbacks["handle_load_fail_image"]("app_ratelimit_path")).grid(row=2, column=2)

        ttk.Label(image_frame, text="Ảnh bị giới hạn tìm kiếm (Web):").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(image_frame, textvariable=self.state["image_path_vars"]["web_ratelimit_path"], state="readonly").grid(row=3, column=1, padx=5, sticky="ew")
        ttk.Button(image_frame, text="Tải ảnh...", command=lambda: self.callbacks["handle_load_fail_image"]("web_ratelimit_path")).grid(row=3, column=2)

        log_frame = ttk.LabelFrame(right_frame, text="Nhật ký", padding=10)
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.log_text = tk.Text(log_frame, state=tk.DISABLED, wrap=tk.WORD, bg="#f0f0f0", font=("Segoe UI", 8))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar_log = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar_log.set)
        log_scrollbar_log.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        values = self.tree.item(item_id, "values")
        if values:
            # Format: Phone - Name
            text_to_copy = f"{values[1]} - {values[2]}"
            self.clipboard_clear()
            self.clipboard_append(text_to_copy)
            self.update()
            messagebox.showinfo("Đã copy", f"Đã copy: {text_to_copy}")

    def get_message_text(self):
        return self.message_text_area.get("1.0", tk.END).strip()

    def set_message_state(self, enabled):
        self.message_text_area.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def clear_tree(self):
        self.tree.delete(*self.tree.get_children())

    def insert_contact_row(self, i, contact):
        tags = ("sent_before",) if contact["status"] == "Đã gửi trước đó" else ()
        self.tree.insert("", tk.END, values=(i, contact["phone"], contact["name"], contact.get("status", "Chờ gửi")), tags=tags)

    def set_row_status(self, index, status_text, tag):
        item_id = self.tree.get_children()[index]
        self.tree.set(item_id, "status", status_text)
        self.tree.item(item_id, tags=(tag,))

    def get_selected_indices(self):
        return [self.tree.index(item) for item in self.tree.selection()]

    def set_contact_status_label(self, text):
        self.contact_status_label.config(text=text)

    def set_status_label(self, text, color):
        self.status_label.config(text=text, foreground=color)

    def set_buttons_state(self, start_state, cancel_state, pause_visible, resume_visible, pause_state, resume_state, export_state, radio_state):
        self.start_button.config(state=start_state)
        self.cancel_button.config(state=cancel_state)
        self.export_button.config(state=export_state)
        self.radio_app.config(state=radio_state)
        self.radio_web.config(state=radio_state)
        if pause_visible:
            self.resume_button.pack_forget()
            self.pause_button.pack(fill="x")
            self.pause_button.config(state=pause_state)
        elif resume_visible:
            self.pause_button.pack_forget()
            self.resume_button.pack(fill="x")
            self.resume_button.config(state=resume_state)
        else:
            self.pause_button.pack_forget()
            self.resume_button.pack_forget()

    def ask_open_files(self):
        return filedialog.askopenfilenames(title="Chọn file HTML", filetypes=(("HTML files", "*.html"),))

    def show_open_image(self):
        return filedialog.askopenfilename(title="Chọn file ảnh báo lỗi", filetypes=[("Image Files", "*.png *.jpg *.jpeg")])

    def ask_save_csv(self):
        return filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Lưu file báo cáo")

    def ask_yesnocancel(self, title, msg):
        return messagebox.askyesnocancel(title, msg)

    def ask_yesno(self, title, msg):
        return messagebox.askyesno(title, msg)

    def show_info(self, title, msg):
        messagebox.showinfo(title, msg)

    def show_warning(self, title, msg):
        messagebox.showwarning(title, msg)

    def show_error(self, title, msg):
        messagebox.showerror(title, msg)

    def topmost(self, enabled):
        self.winfo_toplevel().attributes("-topmost", enabled)

    def withdraw_root(self):
        self.winfo_toplevel().withdraw()

    def deiconify_root(self):
        self.winfo_toplevel().deiconify()

    def fullscreen_overlay(self, on_click, on_escape):
        root = self.winfo_toplevel()
        overlay = tk.Toplevel(root)
        overlay.attributes("-fullscreen", True)
        overlay.attributes("-alpha", 0.1)
        overlay.attributes("-topmost", True)
        overlay.config(cursor="crosshair")
        overlay.bind("<Button-1>", on_click)
        overlay.bind("<Escape>", on_escape)
        return overlay