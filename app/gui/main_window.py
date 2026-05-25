import tkinter as tk
from tkinter import ttk
import queue

from ..constants import DEFAULT_MESSAGE
from ..automation_logic import AutomationLogic
from ..services.storage_service import StorageService
from ..services.contact_service import ContactService
from ..services.report_service import ReportService
from ..controllers.app_controller import AppController
from .automation_tab import AutomationTab
from .guide_tab import GuideTab
from .fetch_tab import FetchTab

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ứng dụng tự động gửi tin Zalo v2.0 - Tích hợp VNCDC")
        self.geometry("1200x800")

        self.comm_queue = queue.Queue()
        self.automation_logic = AutomationLogic(self.comm_queue)
        self.automation_thread = None

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
            "app_ratelimit_path": tk.StringVar(value="Chưa thiết lập"),
            "web_ratelimit_path_2": tk.StringVar(value="Chưa thiết lập"),
            "app_ratelimit_path_2": tk.StringVar(value="Chưa thiết lập"),
            "web_success_path": tk.StringVar(value="Chưa thiết lập"),
            "app_success_path": tk.StringVar(value="Chưa thiết lập")
        }

        self.storage = StorageService()
        self.contacts_service = ContactService()
        self.report_service = ReportService()

        coords = self.storage.load_coords()
        for k, v in coords.items():
            if k in self.coord_vars:
                self.coord_vars[k].set(str(v))

        img_cfg = self.storage.load_image_config()
        for k, v in img_cfg.items():
            if k in self.image_path_vars:
                self.image_path_vars[k].set(v)

        services = {
            "storage": self.storage,
            "contacts": self.contacts_service,
            "report": self.report_service
        }

        self.controller = AppController(self, services, self.automation_logic)

        self._build_ui()
        self._setup_hotkeys()
        
        # Fix: Load data after UI is built to avoid AttributeError
        self.controller.load_initial_data()
        
        self.controller.update_ui_state("initial")
        self.controller.process_comm_queue()
        self._center_window()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        fetch_tab_frame = ttk.Frame(self.notebook)
        automation_tab_frame = ttk.Frame(self.notebook)
        guide_tab_frame = ttk.Frame(self.notebook)

        self.notebook.add(fetch_tab_frame, text="1. Lấy dữ liệu Online")
        self.notebook.add(automation_tab_frame, text="2. Gửi tin tự động")
        self.notebook.add(guide_tab_frame, text="Hướng dẫn sử dụng")

        auto_callbacks = {
            "handle_start": self.controller.handle_start,
            "handle_pause": self.controller.handle_pause,
            "handle_resume": self.controller.handle_resume,
            "handle_cancel": self.controller.handle_cancel,
            "update_ui_state": self.controller.update_ui_state,
            "on_selection_change": self.controller.on_selection_change,
            "delete_selected_contacts": self.controller.delete_selected_contacts,
            "export_report": self.controller.export_report,
            "capture_coordinate": self.controller.capture_coordinate,
            "handle_load_fail_image": self.controller.handle_load_fail_image
        }

        fetch_callbacks = {
            "on_login": getattr(self.controller, "handle_vncdc_login", lambda u, p, r: print("Login logic pending...")),
            "on_fetch": getattr(self.controller, "handle_vncdc_fetch", lambda f, t: print("Fetch logic pending...")),
            "on_configure_xa": getattr(self.controller, "handle_configure_xa", lambda: print("Config XA pending..."))
        }

        state = {
            "zalo_mode": self.zalo_mode,
            "coord_vars": self.coord_vars,
            "image_path_vars": self.image_path_vars,
            "initial_message": self.storage.load_message()
        }

        self.fetch_tab = FetchTab(fetch_tab_frame, {}, fetch_callbacks)
        self.fetch_tab.pack(fill="both", expand=True)

        self.automation_tab = AutomationTab(automation_tab_frame, state, auto_callbacks)
        self.automation_tab.pack(fill="both", expand=True)

        self.guide_tab = GuideTab(guide_tab_frame)
        self.guide_tab.pack(fill="both", expand=True)

    def _setup_hotkeys(self):
        self.bind("<F9>", self.controller.on_f9_press)
        self.bind("<F10>", self.controller.on_f10_press)
        self.bind("<F11>", self.controller.on_f11_press)

    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _on_closing(self):
        if self.automation_logic.running:
            if tk.messagebox.askokcancel("Thoát", "Tác vụ đang chạy, bạn có chắc chắn muốn thoát?"):
                self.automation_logic.stop()
                self.destroy()
        else:
            self.destroy()