from tkinter import ttk
from app.gui.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    style = ttk.Style(app)
    style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), foreground="white")
    style.map("Accent.TButton", background=[("active", "#005a9e"), ("!disabled", "#0078D7")])
    app.mainloop()