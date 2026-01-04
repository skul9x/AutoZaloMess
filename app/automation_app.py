import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import queue
import time
import csv

from .automation_logic import AutomationLogic
from .constants import DEFAULT_MESSAGE, CONFIG_FILE, COORDS_FILE, SENT_DB_FILE, IMAGE_CONFIG_FILE
from .utils import load_json, save_json, parse_contacts_from_html

class AutomationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ứng dụng tự động gửi tin Zalo v1.1")
        self.geometry("1200x800")

        self.comm_queue = queue.Queue()
        self.automation_logic = AutomationLogic(self.comm_queue)
        self.automation_thread = None
        self.contacts = []
        self.stopped_reason = None

        self.zalo_mode = tk.StringVar(value="web")

        self.coord_vars = {
            "search_coords": tk.StringVar(value="Chưa thiết lập"),
            "friend_coords": tk.StringVar(value="Chưa thiết lập"),
            "messagebox_coords": tk.StringVar(value="Chưa thiết lập")
        }
        self.image_path_vars = {
            "web_fail_path": tk.StringVar(value="Chưa thiết lập"),
            "app_fail_path": tk.StringVar(value="Chưa thiết lập"),
            "web_ratelimit_path": tk.StringVar(value="Chưa thiết lập"),
            "app_ratelimit_path": tk.StringVar(value="Chưa thiết lập")
        }

        self.success_count = 0
        self.fail_count = 0
        self.sent_phones = self.load_sent_database()

        self.load_coords()
        self.load_image_config()
        self.create_widgets()
        self.setup_hotkeys()
        self.update_ui_state("initial")
        self.process_comm_queue()
        self.center_window()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def load_message(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return f.read()
        return DEFAULT_MESSAGE

    def save_message(self, message):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(message)

    def load_coords(self):
        coords = load_json(COORDS_FILE, {})
        if not coords:
            return
        for key, value in coords.items():
            if key in self.coord_vars:
                self.coord_vars[key].set(str(value))

    def save_coords(self):
        data_to_save = {key: var.get() for key, var in self.coord_vars.items()}
        save_json(COORDS_FILE, data_to_save)

    def load_image_config(self):
        paths = load_json(IMAGE_CONFIG_FILE, {})
        for key, value in paths.items():
            if key in self.image_path_vars and os.path.exists(value):
                self.image_path_vars[key].set(value)

    def save_image_config(self):
        data_to_save = {key: var.get() for key, var in self.image_path_vars.items()}
        save_json(IMAGE_CONFIG_FILE, data_to_save)

    def load_sent_database(self):
        data = load_json(SENT_DB_FILE, [])
        try:
            return set(data)
        except Exception:
            return set()

    def add_phone_to_database(self, phone_number):
        self.sent_phones.add(phone_number)
        save_json(SENT_DB_FILE, list(self.sent_phones))

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=10, fill="both", expand=True)
        automation_tab = ttk.Frame(notebook)
        guide_tab = ttk.Frame(notebook)
        notebook.add(automation_tab, text="Tự động hóa")
        notebook.add(guide_tab, text="Hướng dẫn sử dụng")
        self.create_automation_tab(automation_tab)
        self.create_guide_tab(guide_tab)

    def create_automation_tab(self, parent_tab):
        main_frame = ttk.Frame(parent_tab, padding="10")
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
        self.message_text_area.insert(tk.INSERT, self.load_message())

        list_frame = ttk.LabelFrame(left_frame, text="Danh sách liên hệ", padding=5)
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
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)
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
        ttk.Button(list_manage_frame, text="Xóa đã chọn", command=self.delete_selected_contacts).pack(side="right")
        self.export_button = ttk.Button(list_manage_frame, text="Xuất báo cáo CSV", command=self.export_report)
        self.export_button.pack(side="right", padx=5)

        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.rowconfigure(3, weight=1)

        control_frame = ttk.LabelFrame(right_frame, text="Điều khiển", padding=10)
        control_frame.pack(fill="x")

        mode_frame = ttk.Frame(control_frame)
        mode_frame.pack(pady=5, anchor="w", fill="x")
        ttk.Label(mode_frame, text="Chế độ Zalo:").pack(side="left")
        self.radio_app = ttk.Radiobutton(mode_frame, text="Zalo App", variable=self.zalo_mode, value="app", command=self.update_ui_state)
        self.radio_app.pack(side="left", padx=10)
        self.radio_web = ttk.Radiobutton(mode_frame, text="Zalo Web", variable=self.zalo_mode, value="web", command=self.update_ui_state)
        self.radio_web.pack(side="left")

        self.import_button = ttk.Button(control_frame, text="Nhập file HTML", command=self.handle_import)
        self.import_button.pack(fill="x", ipady=5, pady=(10, 5))

        self.start_button = ttk.Button(control_frame, text="Bắt đầu (F9)", style="Accent.TButton", command=self.handle_start)
        self.start_button.pack(fill="x", ipady=8, pady=5)

        self.pause_resume_frame = ttk.Frame(control_frame)
        self.pause_resume_frame.pack(fill="x", pady=5)
        self.pause_button = ttk.Button(self.pause_resume_frame, text="Tạm dừng (F10)", command=self.handle_pause)
        self.resume_button = ttk.Button(self.pause_resume_frame, text="Tiếp tục (F10)", command=self.handle_resume)

        self.cancel_button = ttk.Button(control_frame, text="Hủy bỏ (F11)", command=self.handle_cancel)
        self.cancel_button.pack(fill="x", ipady=5, pady=5)
        self.status_label = ttk.Label(control_frame, text="", font=("Segoe UI", 10, "bold"), foreground="#0078D7")
        self.status_label.pack(pady=(10, 0))

        coords_frame = ttk.LabelFrame(right_frame, text="Thiết lập Tọa độ", padding=10)
        coords_frame.pack(fill="x", pady=10)
        coords_frame.columnconfigure(1, weight=1)

        ttk.Label(coords_frame, text="Ô tìm kiếm Zalo:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(coords_frame, textvariable=self.coord_vars["search_coords"], state="readonly").grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(coords_frame, text="Chọn", command=lambda: self.capture_coordinate("search_coords")).grid(row=0, column=2)

        ttk.Label(coords_frame, text="Tọa độ hiển thị tên khi tìm kiếm:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(coords_frame, textvariable=self.coord_vars["friend_coords"], state="readonly").grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(coords_frame, text="Chọn", command=lambda: self.capture_coordinate("friend_coords")).grid(row=1, column=2)

        ttk.Label(coords_frame, text="Ô soạn tin nhắn:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(coords_frame, textvariable=self.coord_vars["messagebox_coords"], state="readonly").grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Button(coords_frame, text="Chọn", command=lambda: self.capture_coordinate("messagebox_coords")).grid(row=2, column=2)

        image_frame = ttk.LabelFrame(right_frame, text="Thiết lập ảnh báo lỗi", padding=10)
        image_frame.pack(fill="x", pady=10)
        image_frame.columnconfigure(1, weight=1)

        ttk.Label(image_frame, text="Ảnh SĐT không tồn tại (App):").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(image_frame, textvariable=self.image_path_vars["app_fail_path"], state="readonly").grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(image_frame, text="Tải ảnh...", command=lambda: self.handle_load_fail_image("app_fail_path")).grid(row=0, column=2)

        ttk.Label(image_frame, text="Ảnh SĐT không tồn tại (Web):").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(image_frame, textvariable=self.image_path_vars["web_fail_path"], state="readonly").grid(row=1, column=1, padx=5, sticky="ew")
        ttk.Button(image_frame, text="Tải ảnh...", command=lambda: self.handle_load_fail_image("web_fail_path")).grid(row=1, column=2)

        ttk.Label(image_frame, text="Ảnh bị giới hạn tìm kiếm (App):").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(image_frame, textvariable=self.image_path_vars["app_ratelimit_path"], state="readonly").grid(row=2, column=1, padx=5, sticky="ew")
        ttk.Button(image_frame, text="Tải ảnh...", command=lambda: self.handle_load_fail_image("app_ratelimit_path")).grid(row=2, column=2)

        ttk.Label(image_frame, text="Ảnh bị giới hạn tìm kiếm (Web):").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(image_frame, textvariable=self.image_path_vars["web_ratelimit_path"], state="readonly").grid(row=3, column=1, padx=5, sticky="ew")
        ttk.Button(image_frame, text="Tải ảnh...", command=lambda: self.handle_load_fail_image("web_ratelimit_path")).grid(row=3, column=2)

        log_frame = ttk.LabelFrame(right_frame, text="Nhật ký", padding=10)
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.log_text = tk.Text(log_frame, state=tk.DISABLED, wrap=tk.WORD, bg="#f0f0f0", font=("Segoe UI", 8))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar_log = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar_log.set)
        log_scrollbar_log.pack(side=tk.RIGHT, fill=tk.Y)

    def create_guide_tab(self, parent_tab):
        guide_frame = ttk.Frame(parent_tab, padding="15")
        guide_frame.pack(fill="both", expand=True)
        guide_text = scrolledtext.ScrolledText(guide_frame, wrap=tk.WORD, font=("Segoe UI", 11), relief=tk.FLAT)
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

    def handle_load_fail_image(self, image_key):
        file_path = filedialog.askopenfilename(title="Chọn file ảnh báo lỗi", filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if file_path:
            self.image_path_vars[image_key].set(file_path)
            self.save_image_config()
            self.update_ui_state()

    def capture_coordinate(self, coord_key):
        self.withdraw()
        time.sleep(0.2)
        capture_window = tk.Toplevel(self)
        capture_window.attributes("-fullscreen", True)
        capture_window.attributes("-alpha", 0.1)
        capture_window.attributes("-topmost", True)
        capture_window.config(cursor="crosshair")

        def on_coord_captured(event):
            coords = (event.x_root, event.y_root)
            self.coord_vars[coord_key].set(str(coords))
            self.save_coords()
            capture_window.destroy()
            self.deiconify()
            self.update_ui_state()

        capture_window.bind("<Button-1>", on_coord_captured)
        capture_window.bind("<Escape>", lambda e: (capture_window.destroy(), self.deiconify()))

    def setup_hotkeys(self):
        self.bind("<F9>", self.on_f9_press)
        self.bind("<F10>", self.on_f10_press)
        self.bind("<F11>", self.on_f11_press)

    def update_ui_state(self, state=None):
        if state is None:
            if self.automation_logic.running:
                state = "paused" if not self.automation_logic.pause_event.is_set() else "running"
            else:
                state = "loaded" if self.contacts else "initial"

        self.pause_button.pack_forget()
        self.resume_button.pack_forget()

        coords_ready = all("Chưa thiết lập" not in v.get() for v in self.coord_vars.values())
        mode = self.zalo_mode.get()
        fail_image_key = "web_fail_path" if mode == "web" else "app_fail_path"
        ratelimit_image_key = "web_ratelimit_path" if mode == "web" else "app_ratelimit_path"
        images_ready = "Chưa thiết lập" not in self.image_path_vars[fail_image_key].get() and "Chưa thiết lập" not in self.image_path_vars[ratelimit_image_key].get()
        is_ready_to_run = coords_ready and images_ready

        if state == "initial":
            self.status_label.config(text="Trạng thái: Sẵn sàng nhập file", foreground="#0078D7")
            self.import_button.config(state=tk.NORMAL)
            self.start_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.DISABLED)
        elif state == "loaded":
            self.import_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.NORMAL)
            self.start_button.config(state=tk.NORMAL if is_ready_to_run else tk.DISABLED)
            self.status_label.config(
                text="Vui lòng thiết lập Tọa độ và Ảnh lỗi!" if not is_ready_to_run else f"Trạng thái: Sẵn sàng gửi ({len(self.contacts)} liên hệ)",
                foreground="orange" if not is_ready_to_run else "green"
            )
        elif state == "running":
            self.status_label.config(text="Trạng thái: Đang chạy...", foreground="red")
            self.import_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.pack(fill="x")
            self.pause_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.NORMAL)
        elif state == "paused":
            self.status_label.config(text="Trạng thái: Đã tạm dừng", foreground="orange")
            self.resume_button.pack(fill="x")
            self.resume_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.NORMAL)
        elif state == "stopping":
            self.status_label.config(text="Trạng thái: Đang dừng...", foreground="grey")
            self.import_button.config(state=tk.NORMAL)
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.pack(fill="x")
            self.pause_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.DISABLED)

        if state in ["running", "paused", "stopping"]:
            self.message_text_area.config(state=tk.DISABLED)
            self.export_button.config(state=tk.DISABLED)
            self.radio_app.config(state=tk.DISABLED)
            self.radio_web.config(state=tk.DISABLED)
        else:
            self.message_text_area.config(state=tk.NORMAL)
            self.export_button.config(state=tk.NORMAL if self.contacts else tk.DISABLED)
            self.radio_app.config(state=tk.NORMAL)
            self.radio_web.config(state=tk.NORMAL)

    def handle_import(self):
        if self.contacts and not messagebox.askyesnocancel("Xác nhận", "Đã có danh sách. Bạn muốn THAY THẾ danh sách cũ (Yes) hay THÊM VÀO danh sách hiện tại (No)?"):
            return
        file_paths = filedialog.askopenfilenames(title="Chọn file HTML", filetypes=(("HTML files", "*.html"),))
        if not file_paths:
            return

        replace_existing = True
        if self.contacts and not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn thay thế danh sách hiện tại?"):
            replace_existing = False

        html_content = "".join(f.read() for path in file_paths for f in [open(path, "r", encoding="utf-8")])
        parsed, added_count, skipped_count = parse_contacts_from_html(html_content, self.sent_phones)

        if not parsed:
            messagebox.showwarning("Không tìm thấy", "Không tìm thấy dữ liệu tên và SĐT trong file đã chọn.")
            return

        if replace_existing:
            self.contacts = parsed
        else:
            self.contacts.extend(parsed)

        self.update_contact_list()
        self.update_ui_state("loaded")
        messagebox.showinfo("Hoàn tất nhập file", f"Đã thêm mới {added_count} liên hệ.\nBỏ qua {skipped_count} liên hệ đã gửi trước đó.\nTổng số hiện tại: {len(self.contacts)}.")

    def handle_start(self):
        if not self.contacts:
            messagebox.showerror("Lỗi", "Danh sách liên hệ trống.")
            return
        user_message = self.message_text_area.get("1.0", tk.END).strip()
        if not user_message:
            messagebox.showerror("Lỗi", "Nội dung tin nhắn không được để trống.")
            return

        self.save_message(user_message)
        self.stopped_reason = None

        try:
            params = {key: eval(var.get()) for key, var in self.coord_vars.items()}
            mode = self.zalo_mode.get()
            fail_image_key = "web_fail_path" if mode == "web" else "app_fail_path"
            ratelimit_image_key = "web_ratelimit_path" if mode == "web" else "app_ratelimit_path"
            params["fail_image_path"] = self.image_path_vars[fail_image_key].get()
            params["ratelimit_image_path"] = self.image_path_vars[ratelimit_image_key].get()
            if not os.path.exists(params["fail_image_path"]) or not os.path.exists(params["ratelimit_image_path"]):
                messagebox.showerror("Lỗi", f"Chưa thiết lập hoặc không tìm thấy file ảnh lỗi cho chế độ {mode.upper()}.")
                return
        except Exception as e:
            messagebox.showerror("Lỗi tọa độ", f"Một hoặc nhiều tọa độ không hợp lệ. Lỗi: {e}")
            return

        self.success_count = 0
        self.fail_count = 0
        self.update_ui_state("running")
        self.automation_thread = threading.Thread(target=self.automation_logic.run, args=(list(self.contacts), user_message, params), daemon=True)
        self.automation_thread.start()

    def handle_pause(self):
        self.automation_logic.pause()
        self.update_ui_state("paused")

    def handle_resume(self):
        self.automation_logic.resume()
        self.update_ui_state("running")

    def handle_cancel(self):
        if self.automation_logic.running and not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn hủy bỏ tác vụ đang chạy?"):
            return
        self.automation_logic.stop()
        self.update_ui_state("stopping")

    def _update_ui_from_queue(self):
        while not self.comm_queue.empty():
            try:
                message = self.comm_queue.get_nowait()
                msg_type = message[0]

                if msg_type == "log":
                    self.log_text.config(state=tk.NORMAL)
                    self.log_text.insert(tk.END, message[1] + "\n")
                    self.log_text.see(tk.END)
                    self.log_text.config(state=tk.DISABLED)

                elif msg_type == "status":
                    index, status_text = message[1], message[2]
                    item_id = self.tree.get_children()[index]
                    current_tags = self.tree.item(item_id, "tags")
                    is_already_processed = "success" in current_tags or "failure" in current_tags
                    self.tree.set(item_id, "status", status_text)
                    self.contacts[index]["status"] = status_text
                    tag = ""
                    if "Thành công" in status_text:
                        tag = "success"
                        self.success_count += 0 if is_already_processed else 1
                        if not is_already_processed:
                            self.add_phone_to_database(self.contacts[index]["phone"])
                    elif "Thất bại" in status_text:
                        tag = "failure"
                        self.fail_count += 0 if is_already_processed else 1
                    elif "Đang xử lý" in status_text:
                        tag = "processing"
                    self.tree.item(item_id, tags=(tag,))

                elif msg_type == "stopped_due_to_ratelimit":
                    self.stopped_reason = "ratelimit"

            except (queue.Empty, IndexError):
                break

    def process_comm_queue(self):
        was_running = "Đang chạy" in self.status_label.cget("text") or "Đang dừng" in self.status_label.cget("text") or "Đã tạm dừng" in self.status_label.cget("text")
        self._update_ui_from_queue()
        is_running_now = self.automation_logic.running

        if was_running and not is_running_now:
            self._update_ui_from_queue()
            self.attributes("-topmost", True)
            if self.stopped_reason == "ratelimit":
                messagebox.showwarning("Bị giới hạn", "Đã gửi quá nhiều tin nhắn! Zalo đã tạm thời giới hạn tính năng tìm kiếm của bạn.\n\nVui lòng chờ một thời gian trước khi thử lại.")
            else:
                summary_message = f"Đã hoàn thành xong gửi tin nhắn.\n\nThành công: {self.success_count}\nThất bại: {self.fail_count}"
                messagebox.showinfo("Hoàn thành", summary_message)
            self.attributes("-topmost", False)
            self.update_ui_state()

        self.after(100, self.process_comm_queue)

    def update_contact_list(self):
        self.tree.delete(*self.tree.get_children())
        for i, contact in enumerate(self.contacts, 1):
            tags = ("sent_before",) if contact["status"] == "Đã gửi trước đó" else ()
            self.tree.insert("", tk.END, values=(i, contact["phone"], contact["name"], contact.get("status", "Chờ gửi")), tags=tags)
        self.on_selection_change()

    def on_selection_change(self, event=None):
        self.contact_status_label.config(text=f"Tổng số: {len(self.contacts)} | Đã chọn: {len(self.tree.selection())}")

    def delete_selected_contacts(self):
        if self.automation_logic.running:
            messagebox.showwarning("Không thể xóa", "Không thể xóa danh sách khi tác vụ đang chạy.")
            return
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn các liên hệ cần xóa.")
            return
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa {len(selected_items)} liên hệ đã chọn?"):
            indices_to_delete = sorted([self.tree.index(item) for item in selected_items], reverse=True)
            for index in indices_to_delete:
                del self.contacts[index]
            self.update_contact_list()
            self.update_ui_state()

    def export_report(self):
        if not self.contacts:
            messagebox.showwarning("Không có dữ liệu", "Không có dữ liệu liên hệ để xuất.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Lưu file báo cáo")
        if not file_path:
            return
        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["STT", "Số điện thoại", "Tên khách hàng", "Trạng thái"])
                for i, contact in enumerate(self.contacts, 1):
                    writer.writerow([i, contact["phone"], contact["name"], contact.get("status", "N/A")])
            messagebox.showinfo("Thành công", f"Báo cáo đã được lưu tại:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu file báo cáo:\n{e}")

    def on_closing(self):
        if self.automation_logic.running and messagebox.askokcancel("Thoát", "Tác vụ đang chạy, bạn có chắc chắn muốn thoát?"):
            self.automation_logic.stop()
            self.destroy()
        elif not self.automation_logic.running:
            self.destroy()

    def on_f9_press(self, event=None):
        if self.start_button["state"] == tk.NORMAL:
            self.log("--- Phím nóng F9 được nhấn: Bắt đầu ---")
            self.start_button.invoke()

    def on_f10_press(self, event=None):
        if self.pause_button.winfo_ismapped() and self.pause_button["state"] == tk.NORMAL:
            self.log("--- Phím nóng F10 được nhấn: Tạm dừng ---")
            self.pause_button.invoke()
        elif self.resume_button.winfo_ismapped() and self.resume_button["state"] == tk.NORMAL:
            self.log("--- Phím nóng F10 được nhấn: Tiếp tục ---")
            self.resume_button.invoke()

    def on_f11_press(self, event=None):
        if self.cancel_button["state"] == tk.NORMAL:
            self.log("--- Phím nóng F11 được nhấn: Hủy bỏ ---")
            self.handle_cancel()

    def log(self, message):
        self.comm_queue.put(("log", message))