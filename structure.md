# Cấu trúc tệp tin và mã nguồn (Project Structure)

Dự án **AutoZaloMess** (Tự động gửi tin nhắn Zalo tích hợp lấy dữ liệu từ VNCDC) được tổ chức theo mô hình MVC (Model-View-Controller) kết hợp với kiến trúc các Service rõ ràng, giúp dễ dàng mở rộng và bảo trì.

Dưới đây là cấu trúc chi tiết của dự án:

```text
AutoZaloMess_1.3_SourceCode/
├── main.py                     # Entry point chính của ứng dụng. Khởi tạo MainWindow và giao diện Tkinter.
├── AnhgioihanTimKiem_app.png   # Ảnh mẫu: Cảnh báo giới hạn tìm kiếm (trên Zalo App)
├── AnhgioihanTimKiem_web.png   # Ảnh mẫu: Cảnh báo giới hạn tìm kiếm (trên Zalo Web)
├── KhongChoTimKiem_app.png     # Ảnh mẫu: Không tìm thấy số điện thoại (trên Zalo App)
├── KhongChoTimKiem_web.png     # Ảnh mẫu: Không tìm thấy số điện thoại (trên Zalo Web)
├── config.json                 # Tệp cấu hình lưu trữ tài khoản, mật khẩu đăng nhập VNCDC
├── coords_config.json          # Tệp lưu trữ tọa độ click chuột (Search, Friend, Message_box)
├── image_config.json           # Tệp lưu trữ đường dẫn cấu hình nhận diện hình ảnh lỗi báo từ Zalo
├── message_config.txt          # Tệp lưu trữ nội dung tin nhắn mẫu
├── sent_database.json          # Cơ sở dữ liệu lưu các số điện thoại đã gửi tin nhắn thành công
├── xa_settings.json            # Tệp cấu hình lưu danh sách mã xã/phường dùng để filter dữ liệu VNCDC
├── .brain/                     # Thư mục lưu trữ kiến thức dự án (AI Context)
│   ├── brain.json              # Kiến thức tĩnh (Cấu trúc, Tech Stack)
│   └── session.json            # Trạng thái phiên làm việc (Task hiện tại)
├── app/                        # Thư mục chứa toàn bộ mã nguồn lõi của ứng dụng
│   ├── __init__.py             # Đánh dấu thư mục `app` là một package Python
│   ├── automation_app.py       # Tập tin cũ/dự phòng lưu trữ code giao diện và logic Automation (Bản cũ gộp chung)
│   ├── automation_logic.py     # Chứa Class `AutomationLogic` xử lý lõi RPA: pyautogui click, copy/paste, tìm ảnh báo lỗi
│   ├── constants.py            # Chứa các biến hằng số, đường dẫn mặc định và Text mặc định của hệ thống
│   ├── utils.py                # Các hàm tiện ích (đọc/ghi file JSON, parse phone/text, Regex)
│   ├── controllers/            # Lớp Controller điều phối tác vụ giữa UI và logic
│   │   ├── __init__.py         
│   │   └── app_controller.py   # Nhận sự kiện từ UI, gọi Service lấy API hoặc bắt đầu quy trình Authomation gửi tin
│   ├── data/                   # Thư mục rỗng (chứa các file export/report sinh ra nếu có)
│   ├── gui/                    # Lớp View (Giao diện người dùng bằng Tkinter)
│   │   ├── __init__.py
│   │   ├── main_window.py      # Cửa sổ chính, tích hợp cả 3 Tabs bên dưới
│   │   ├── fetch_tab.py        # Tab 1: Giao diện Khai báo tài khoản, Chọn ngày, Lấy dữ liệu từ VNCDC
│   │   ├── automation_tab.py   # Tab 2: Quản lý danh sách gửi tin, setup text/tọa độ, điều khiển Gửi/Dừng/Hủy
│   │   └── guide_tab.py        # Tab 3: Giao diện Hướng dẫn sử dụng trực quan cho user
│   └── services/               # Lớp Model (Xử lý Data, API, File Storage)
│       ├── __init__.py
│       ├── contact_service.py  # Quản lý danh sách đối tượng (Thêm, Xóa, Cập nhật trạng thái)
│       ├── report_service.py   # Dịch vụ xuất báo cáo (vd ra file CSV)
│       ├── storage_service.py  # Xử lý đọc/ghi các file config.json, coords_config.json, sent_database.json...
│       ├── vncdc_client.py     # HTTP Client (dùng httpx) mô phỏng Request Đăng nhập và Fetch dữ liệu từ API tiêm chủng
│       └── vncdc_parser.py     # Extract HTML/JSON data trả về từ vncdc_client, bóc tách sđt, tên tuổi
```

## Các module chính và vai trò

### 1. Cấu trúc UI (`app/gui/`):
- Toàn bộ giao diện được xây dựng bằng viện thư viện `tkinter` chuẩn của Python.
- Module UI được chia nhỏ ra thành các file `Tab` riêng biệt. Mỗi file chịu trách nhiệm xây dựng Layout, Buttons thay vì nhồi nhét vào 1 file `main.py` khổng lồ.

### 2. Bộ phận Auto Gửi Zalo (`app/automation_logic.py`):
- Ứng dụng công nghệ **RPA (Robotic Process Automation)** mức cơ bản thông qua thư viện `pyautogui` và `pyperclip`.
- Khi gọi `.run()`, phần mềm sẽ tự đưa chuột đến thanh tìm kiếm của Zalo, dán (Ctrl+V) SĐT, chờ load, kiểm tra màn hình xem có **hình ảnh cảnh báo lỗi rate-limit** hay **lỗi không tìm thấy bạn bè** không. 
- Nếu tìm thấy, nhấp vào bạn bè -> paste (Ctrl+V) Message -> Gửi (Enter).

### 3. Tương tác với hệ thống tiêm chủng VNCDC (`app/services/vncdc_client.py`):
- Sử dụng `httpx` xây dựng một Client có khả năng giữ session (Cookie `.ASPXAUTH`) sau khi Login vào trang CMS Tiêm chủng.
- Có khả năng gọi API để lấy ra danh sách các đối tượng cần gửi tin nhắn, bóc tách token chặn CSRF từ form HTML.
