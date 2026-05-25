import sys
from unittest.mock import MagicMock, patch

# Định nghĩa dummy classes để tránh lỗi khi kế thừa từ MagicMock và tránh yêu cầu Display của Tkinter
class DummyToplevel:
    def __init__(self, *args, **kwargs):
        # Tạo mock cho các widget hoặc thuộc tính cơ bản nếu cần
        pass
    def title(self, *args): pass
    def geometry(self, *args): pass
    def resizable(self, *args): pass
    def transient(self, *args): pass
    def grab_set(self, *args): pass
    def grab_release(self, *args): pass
    def destroy(self, *args): pass
    def after(self, *args): return "after_id"
    def after_cancel(self, *args): pass
    def bind(self, *args): pass
    def protocol(self, *args): pass
    def update_idletasks(self): pass
    def winfo_screenwidth(self): return 1920
    def winfo_screenheight(self): return 1080
    def register(self, func): return func

# Thay thế mô-đun tkinter bằng mock và dummy classes trước khi import OtpDialog
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter'].Toplevel = DummyToplevel
sys.modules['tkinter.font'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()

from app.gui.otp_dialog import OtpDialog

def test_otp_validation():
    parent = MagicMock()
    
    # Không patch các hàm khởi tạo, để tkinter mock lo phần tạo thuộc tính
    dialog = OtpDialog(parent)
    
    # Test hàm _validate_otp
    # Test hợp lệ: chuỗi rỗng
    assert dialog._validate_otp("") is True
    
    # Test hợp lệ: chuỗi số dài <= 6
    assert dialog._validate_otp("1") is True
    assert dialog._validate_otp("123456") is True
    
    # Test không hợp lệ: chứa chữ
    assert dialog._validate_otp("12a") is False
    
    # Test không hợp lệ: dài hơn 6 chữ số
    assert dialog._validate_otp("1234567") is False

def test_otp_confirm_valid():
    parent = MagicMock()
    dialog = OtpDialog(parent)
    dialog.otp_entry = MagicMock()
    dialog.otp_entry.get.return_value = "123456"
    
    with patch.object(dialog, "_close") as mock_close:
        dialog._on_confirm()
        assert dialog.result == "123456"
        mock_close.assert_called_once()

def test_otp_confirm_valid_with_callback():
    parent = MagicMock()
    mock_callback = MagicMock()
    dialog = OtpDialog(parent, on_confirm_callback=mock_callback)
    dialog.otp_entry = MagicMock()
    dialog.otp_entry.get.return_value = "123456"
    
    dialog._on_confirm()
    assert dialog.result == "123456"
    mock_callback.assert_called_once_with("123456")

def test_otp_confirm_invalid():
    parent = MagicMock()
    dialog = OtpDialog(parent)
    dialog.otp_entry = MagicMock()
    dialog.otp_entry.get.return_value = "123"
    
    with patch.object(dialog, "show_error") as mock_show_error:
        dialog._on_confirm()
        assert dialog.result is None
        mock_show_error.assert_called_once_with("Mã OTP phải có đúng 6 chữ số")

def test_otp_cancel():
    parent = MagicMock()
    dialog = OtpDialog(parent)
    
    with patch.object(dialog, "_close") as mock_close:
        dialog._on_cancel()
        assert dialog.result is None
        mock_close.assert_called_once()

def test_set_loading():
    parent = MagicMock()
    dialog = OtpDialog(parent)
    dialog.btn_confirm = MagicMock()
    dialog.btn_cancel = MagicMock()
    dialog.otp_entry = MagicMock()
    
    dialog.set_loading(True)
    dialog.btn_confirm.config.assert_called_once_with(state="disabled")
    dialog.btn_cancel.config.assert_called_once_with(state="disabled")
    dialog.otp_entry.config.assert_called_once_with(state="disabled")
    
    dialog.set_loading(False)
    dialog.btn_confirm.config.assert_called_with(state="normal")
    dialog.btn_cancel.config.assert_called_with(state="normal")
    dialog.otp_entry.config.assert_called_with(state="normal")
