# Tự động gửi tin Zalo (AutoZaloMess v2.0)

![AutoZaloMess](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.x-green)

**AutoZaloMess** là một công cụ phần mềm tự động hóa (RPA) kết hợp giao diện đồ họa (GUI). Nó hỗ trợ thu thập dữ liệu về số điện thoại và thông tin cá nhân từ trang thông tin cổng Hệ thống quản lý tiêm chủng quốc gia (VNCDC), sau đó tự động điều khiển chuột và bàn phím máy tính để tự động tìm kiếm và gửi hàng loạt tin nhắn thông báo (Nhắc lịch) trên ứng dụng Zalo (Web & App) mà không cần thao tác tay.

## Chức năng chính

1. **Kết nối API VNCDC (Lấy dữ liệu trực tiếp):** 
   - Hỗ trợ đăng nhập tự động vào hệ thống tiêm chủng (HTTP Session).
   - Truy vấn danh sách đối tượng tiêm, phụ huynh, SĐT theo lịch hẹn, khoảng khoảng thời gian lọc và mã Xã/Phường cấu hình sẵn.
2. **Auto Gửi tin Zalo (Tự động hóa chuỗi thao tác):** 
   - Sử dụng thư viện `pyautogui` điều khiển chuột dán số điện thoại, chọn kết quả, dán tin nhắn, và nhấn Gửi.
   - Cơ chế Sleep Random (độ trễ ngẫu nhiên) mô phỏng người thật giúp làm giảm nguy cơ bị khóa tài khoản (Rate Limited).
   - Nội dung tin nhắn có thể chứa các biến cá nhân hóa `{name}` và `{phone}`.
3. **Phát hiện lỗi bằng Xử lý hình ảnh (Computer Vision):**
   - Zalo thường sẽ khóa "Tìm kiếm" nếu tìm kiếm quá nhanh, phần mềm tự động chụp hoặc tải các ảnh mẫu (`.png`) để nhận biết trường hợp lỗi: `Hình báo Không Tìm Thấy Bạn Bè` hoặc `Hình báo Zalo Phạt Giới hạn Tìm kiếm`.
4. **Hệ thống Quản lý trực quan (GUI Tkinter):** 
   - Chia thành 3 Tabs dễ sử dụng: 
     - **Tab 1: Lấy dữ liệu Online** (Login VNCDC, chọn Date, Xã/Phường).
     - **Tab 2: Gửi tin tự động** (Danh sách KH, set tọa độ màn hình Zalo, Edit tin nhắn, Dừng/Tiếp tục auto).
     - **Tab 3: Hướng dẫn sử dụng**.

---

## Yêu cầu môi trường (Requirements)

Cài đặt Python 3.x và các gói phụ thuộc (Dependencies). Mở Terminal/Command Prompt lên và gõ:

```bash
pip install httpx pyautogui pyperclip tkcalendar
```
*(Giao diện ứng dụng sử dụng module `tkinter` chuẩn, thường được cài sẵn với Python)*

---

## Cài đặt hệ thống (Configuration)

Project lưu trữ trạng thái người dùng tại các file sau dưới định dạng JSON & Text:
- `config.json`: Cấu hình lưu trữ thông tin Đăng nhập VNCDC
- `coords_config.json`: Vị trí Click chuột (Search Box, Vị trí Bạn Bè đầu tiên, Box Gõ tin nhắn). Hệ thống có chức năng tự bắt tọa độ khi sử dụng.
- `image_config.json`: Khai báo vị trí các file ảnh lỗi của Zalo (ví dụ: `KhongChoTimKiem_web.png`) để tool tự skip nếu Zalo báo lỗi SĐT chưa dùng Zalo.
- `message_config.txt`: Format tin nhắn sẽ gửi đi.
- `xa_settings.json`: Danh sách ID Xã/Phường do VNCDC cung cấp. 
- `sent_database.json`: File database "Blacklist" để ghi nhớ phần mềm đã gửi thành công những số nào, tự động Skip trong lần chạy tiếp theo.

---

## Cách chạy dự án (How to run)

1. Mở Terminal / CMD / PowerShell tại thư mục thư mục gốc dự án.
2. Khởi chạy file App chính (main).
```shell
python main.py
```
3. Màn hình GUI sẽ hiện lên với 3 tabs chính.

## Hướng dẫn sử dụng (User Guide)

- **Bước 1 (Lấy số điện thoại):** Cấu hình Tên đăng nhập & Mật khẩu VNCDC, tick tải danh sách tiêm trong giới hạn ngày. Nhất Nút [Đăng nhập & Lấy danh sách]. Kết quả các số điện thoại sẽ xuất hiện ở hệ thống.
- **Bước 2 (Set tọa độ Màn hình Zalo):** Chuyển sang Tab 2, chia nửa màn hình máy tính của App và App Zalo (hoặc Web) song song. 
  - Click vào chữ **`(Thiết lập Cấu Hình)`** ở phần Tọa độ điểm nhấn. Di chuột sang ô Tìm kiếm của Zalo, ấn phím **`ESC`** trên bàn phím để Tool lưu lại tọa độ. Làm tương tự cho ô "Bạn bè Zalo" và ô "Nhập tin nhắn".
- **Bước 3 (Thiết lập Ảnh nhận dạng lỗi):** Load các file ảnh (`Anhgioihan...png`, `KhongChoTimKiem...png`) để tool có dữ kiện nhận diện lỗi tìm kiếm.
- **Bước 4 (Start):** Nhấn **Bắt Đầu Gửi Tin (F9)**. Rời tay khỏi chuột/bàn phím để theo dõi con trỏ tự động di chuyển. Nhấn phím  **Tạm dừng (F10)** hoặc **Hủy (F11)** để kết thúc kịch bản sớm.

---
---
**CẢNH BÁO BẢO MẬT & VẬN HÀNH:** 
- Đây là Tool tự động (RPA) điều khiển chuột máy tính. Tuyệt đối **KHÔNG thao tác chuột, gõ bàn phím** trong lúc Tool đang hiển thị thông báo "Đang Gửi". Mọi thao tác tranh giành chuột có thể dán nhầm tin nhắn vào các cửa sổ khác.
- Tuyệt đối tự chịu trách nhiệm nếu việc gửi tin nhắn spam quá lạm dụng gây ra việc tài khoản Zalo bị cấm (Banned). Tool tích hợp thuật toán "Delay ngẫu nhiên" và "Fail Skip" giúp tỷ lệ sống sót cao hơn nhưng Zalo vẫn có các policy ngầm ẩn.

---
### Có gì mới trong bản v2.0?
- **Smart Wait 10s**: Thay thế hoàn toàn cơ chế chờ cố định (Hard Sleep) bằng cơ chế nhận diện ảnh thông minh.
- **Auto Cleanup UI**: Tự động dọn dẹp (Click + Ctrl+A) khi gặp số điện thoại không tồn tại, tránh lỗi click nhầm.
- **Hỗ trợ 3 trạng thái**: Thành công, Thất bại, Bị giới hạn (Rate Limit).

