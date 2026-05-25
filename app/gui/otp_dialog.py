import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

class OtpDialog(tk.Toplevel):
    def __init__(self, parent, error_message=None, on_confirm_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.on_confirm_callback = on_confirm_callback
        self.result = None
        
        self.title("Xác thực 2 lớp")
        self.resizable(False, False)
        
        # Make transient and grab focus
        self.transient(parent)
        self.grab_set()
        
        # Configure styles
        self.style = ttk.Style(self)
        
        self._build_ui(error_message)
        
        # Center dialog relative to parent or screen
        self._center_dialog()
        
        # Countdown state
        self.countdown_val = 30
        self._tick_countdown()
        
        # Bind events
        self.bind("<Return>", lambda e: self._on_confirm())
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Focus on OTP Entry
        self.otp_entry.focus_set()
        
    def _center_dialog(self):
        self.update_idletasks()
        width = 400
        height = 365
        
        if self.parent:
            try:
                parent_x = self.parent.winfo_rootx()
                parent_y = self.parent.winfo_rooty()
                parent_w = self.parent.winfo_width()
                parent_h = self.parent.winfo_height()
                x = parent_x + (parent_w - width) // 2
                y = parent_y + (parent_h - height) // 2
            except Exception:
                x = (self.winfo_screenwidth() - width) // 2
                y = (self.winfo_screenheight() - height) // 2
        else:
            x = (self.winfo_screenwidth() - width) // 2
            y = (self.winfo_screenheight() - height) // 2
            
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def _validate_otp(self, P):
        # Allow empty string (deleting) or digits only up to 6 characters
        if P == "":
            return True
        if P.isdigit() and len(P) <= 6:
            return True
        return False
        
    def _build_ui(self, error_message):
        # Outer padding frame
        main_frame = ttk.Frame(self, padding="20 20 20 20")
        main_frame.pack(fill="both", expand=True)
        
        # Title Label
        title_font = tkfont.Font(family="Helvetica", size=16, weight="bold")
        title_label = ttk.Label(main_frame, text="Xác thực 2 lớp", font=title_font)
        title_label.pack(pady=(0, 10))
        
        # Instruction Frame with light background
        instr_frame = tk.Frame(main_frame, bg="#eef2f7", bd=1, relief="solid")
        instr_frame.pack(fill="x", pady=(0, 15))
        
        instr_text = (
            "Vui lòng mở ứng dụng Google Authenticator trên\n"
            "thiết bị của bạn để lấy mã OTP và điền vào ô bên dưới."
        )
        instr_label = tk.Label(
            instr_frame, 
            text=instr_text, 
            bg="#eef2f7", 
            fg="#4a5568", 
            font=("Helvetica", 10),
            justify="center",
            pady=8
        )
        instr_label.pack(fill="both", expand=True)
        
        # OTP Entry Field (Large, centered text)
        entry_font = tkfont.Font(family="Helvetica", size=20, weight="bold")
        
        # Validate command
        vcmd = (self.register(self._validate_otp), "%P")
        
        self.otp_entry = tk.Entry(
            main_frame,
            font=entry_font,
            justify="center",
            width=10,
            validate="key",
            validatecommand=vcmd,
            bd=2,
            relief="groove"
        )
        self.otp_entry.pack(pady=(0, 10))
        
        # Countdown Label
        self.countdown_label = ttk.Label(
            main_frame, 
            text="⏱ Mã sẽ đổi sau: 30s", 
            font=("Helvetica", 10, "italic")
        )
        self.countdown_label.pack(pady=(0, 5))
        
        # Error Label (red, hidden by default unless error_message is provided)
        self.error_label = tk.Label(
            main_frame,
            text=error_message or "",
            fg="#e53e3e",
            font=("Helvetica", 10, "bold"),
            wraplength=350
        )
        if error_message:
            self.error_label.pack(pady=(5, 5))
        else:
            self.error_label.pack(pady=(5, 5))
            self.error_label.pack_forget()
            
        # Buttons Frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(15, 0))
        
        # Cancel Button
        self.btn_cancel = ttk.Button(btn_frame, text="Hủy", command=self._on_cancel)
        self.btn_cancel.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        # Confirm Button
        self.btn_confirm = ttk.Button(btn_frame, text="🔐 Xác thực", command=self._on_confirm)
        self.btn_confirm.pack(side="right", expand=True, fill="x", padx=(5, 0))
        
    def _tick_countdown(self):
        # Update UI countdown label
        self.countdown_label.config(text=f"⏱ Mã sẽ đổi sau: {self.countdown_val}s")
        
        # Change text color to red if countdown < 5s
        if self.countdown_val < 5:
            self.countdown_label.config(foreground="red")
        else:
            self.countdown_label.config(foreground="black")
            
        # Decrement or reset
        self.countdown_val -= 1
        if self.countdown_val < 0:
            self.countdown_val = 30
            
        # Register next tick
        self._timer_id = self.after(1000, self._tick_countdown)
        
    def _on_confirm(self):
        otp = self.otp_entry.get().strip()
        if len(otp) != 6:
            self.show_error("Mã OTP phải có đúng 6 chữ số")
            return
            
        self.result = otp
        if self.on_confirm_callback:
            self.on_confirm_callback(otp)
        else:
            self._close()
        
    def _on_cancel(self):
        self.result = None
        self._close()
        
    def _close(self):
        # Cancel timers to prevent memory leaks or running after destroy
        try:
            self.after_cancel(self._timer_id)
        except Exception:
            pass
        self.grab_release()
        self.destroy()
        
    def show_error(self, message):
        self.error_label.config(text=message)
        self.error_label.pack(pady=(5, 5))
        
    def hide_error(self):
        self.error_label.pack_forget()
        
    def set_loading(self, is_loading: bool):
        if is_loading:
            self.btn_confirm.config(state="disabled")
            self.btn_cancel.config(state="disabled")
            self.otp_entry.config(state="disabled")
        else:
            self.btn_confirm.config(state="normal")
            self.btn_cancel.config(state="normal")
            self.otp_entry.config(state="normal")
            
    def show(self):
        self.wait_window()
        return self.result
