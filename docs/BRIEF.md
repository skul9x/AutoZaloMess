# 💡 BRIEF: Cập Nhật Luồng Đăng Nhập & Xác Thực 2FA VNCDC (Mới Nhất)

**Ngày tạo:** 2026-11-08  
**Brainstorm cùng:** User  
**Nguồn dữ liệu:** `curl_capture_20261108_151208`

---

## 1. VẤN ĐỀ CẦN GIẢI QUYẾT
- Hệ thống Tiêm chủng Quốc gia (VNCDC) gần đây đã cập nhật cơ chế bảo mật cho luồng **VerifyTwoFactor (Xác thực 2 lớp - 2FA)**.
- Trước đây, sau khi nhập mã OTP, client chỉ gửi `code` dạng form payload thông thường lên `/Account/VerifyTwoFactor`.
- Hiện tại, VNCDC yêu cầu thêm header bảo mật **`RequestVerificationToken`** khi submit mã OTP lên endpoint `/Account/VerifyTwoFactor`.
- Nếu thiếu token này trong header, request OTP sẽ bị từ chối hoặc trả về mã lỗi bảo mật (Anti-Forgery Token validation failed), khiến việc đăng nhập VNCDC trong app thất bại.

---

## 2. PHÂN TÍCH TỪ DỮ LIỆU THỰC TẾ (CURL CAPTURE)

Dựa trên gói cURL capture ngày 08/11/2026:

### Bước 1: Yêu cầu lấy Token trước khi verify OTP
- **File:** `20261108_151205_GET_Account_AntiForgeryToken.txt`
- **Request:**
  - Method: `GET`
  - URL: `https://tiemchung.vncdc.gov.vn/Account/AntiForgeryToken?_={timestamp_ms}`
  - Headers:
    - `Referer: https://tiemchung.vncdc.gov.vn/Account/VerifyTwoFactor`
    - `X-Requested-With: XMLHttpRequest`
    - `Accept: */*`
- **Response Body:**
  ```json
  {
    "token": "2fzw8VdbcJYYLYKjS8x4TV1LlmwY1_-wHW0KFpAOg33FmYQLiqRNwrwta5WKKA4SWUO_p2eYfrkDcNKp9B6JsXgM4JbZ3oXV1Yi1YCBru4QyfyJpRaDbgie46o0a6tHdGgdHybELMS6zu5kdPnFGDA2"
  }
  ```

### Bước 2: Submit OTP kèm theo Header `RequestVerificationToken`
- **File:** `20261108_151205_POST_Account_VerifyTwoFactor.txt`
- **Request:**
  - Method: `POST`
  - URL: `https://tiemchung.vncdc.gov.vn/Account/VerifyTwoFactor`
  - Headers:
    - `RequestVerificationToken: <token_vừa_lấy_ở_bước_1>`
    - `Origin: https://tiemchung.vncdc.gov.vn`
    - `Referer: https://tiemchung.vncdc.gov.vn/Account/VerifyTwoFactor`
    - `X-Requested-With: XMLHttpRequest`
    - `Content-Type: application/x-www-form-urlencoded; charset=UTF-8`
  - Form Data:
    - `code=<mã_otp>`
- **Response Body:**
  ```json
  {
    "Success": true,
    "Redirect": "/TiemChung/DoiTuong/Index"
  }
  ```

### Bước 3: Kiểm tra session & hoàn tất xác thực (Verification check)
- **File:** `20261108_151206_GET_Home_GetNumberOfNewMessage.txt`
- Sau khi `VerifyTwoFactor` trả về `"Success": true`, server thiết lập cookie `.ASPXAUTH` xác thực phiên làm việc.
- Gọi GET `/Home/GetNumberOfNewMessage` hoặc `/KeHoachTiemPhatSinhArea/KeHoachTiemPhatSinh` để load kế hoạch tiêm.

---

## 3. ĐIỂM KHÁC BIỆT SO VỚI CODE HIỆN TẠI TRONG APP

| Tiêu chí | Code hiện tại (`app/services/vncdc_client.py`) | Luồng thực tế mới (CURL Capture) |
|---|---|---|
| **Lấy Token 2FA** | ❌ Không gọi endpoint lấy token | ✅ Phải gọi `GET /Account/AntiForgeryToken?_={timestamp}` để lấy `json["token"]` |
| **Header khi POST OTP** | ❌ Chỉ có header thông thường, thiếu `RequestVerificationToken` | ✅ Bắt buộc gửi header: `RequestVerificationToken: <token>` |
| **Referer của OTP** | `Referer: https://tiemchung.vncdc.gov.vn/Account/Login` | `Referer: https://tiemchung.vncdc.gov.vn/Account/VerifyTwoFactor` |
| **Fallback Token (nếu có)** | Không có | Nếu `AntiForgeryToken` lỗi, có thể fallback parse từ cookie hoặc DOM `/Account/VerifyTwoFactor` |

---

## 4. GIẢI PHÁP ĐỀ XUẤT

1. **Bổ sung helper method `get_anti_forgery_token()` trong `VncdcClient`**:
   - Gửi GET đến `/Account/AntiForgeryToken?_={current_timestamp_ms}`.
   - Headers chuẩn: `X-Requested-With: XMLHttpRequest`, `Referer: .../Account/VerifyTwoFactor`.
   - Bóc tách `token = resp.json().get("token")`.
2. **Cập nhật phương thức `verify_2fa(self, code)`**:
   - Tự động gọi `get_anti_forgery_token()`.
   - Đưa token vào header `RequestVerificationToken: token`.
   - Cập nhật đúng `Referer: .../Account/VerifyTwoFactor`.
   - Giữ nguyên logic fallback kiểm tra response JSON / cookie `.ASPXAUTH`.
3. **Cập nhật Test Suites**:
   - Viết mock test cho `get_anti_forgery_token()` và luồng `verify_2fa` mới trong `tests/test_vncdc_client_2fa.py`.
   - Đảm bảo 100% test case pass.

---

## 5. PHẠM VI CÔNG VIỆC (MVP SCOPE)

### 🚀 MVP (Bắt buộc):
- [ ] Cập nhật `VncdcClient.get_anti_forgery_token()` trong [app/services/vncdc_client.py](file:///d:/skul9x/AutoZaloMess-main/app/services/vncdc_client.py).
- [ ] Cập nhật `VncdcClient.verify_2fa()` kèm header `RequestVerificationToken`.
- [ ] Cập nhật toàn bộ unit tests trong [tests/test_vncdc_client_2fa.py](file:///d:/skul9x/AutoZaloMess-main/tests/test_vncdc_client_2fa.py) để phản ánh đúng flow mới.
- [ ] Chạy test tự động xác nhận tương thích hoàn toàn.

### 🎁 Nice-to-have:
- Thêm cơ chế retry hoặc fallback nếu endpoint `/Account/AntiForgeryToken` gặp timeout/lỗi 500 mạng chập chờn.

---

## 6. ĐÁNH GIÁ KỸ THUẬT & RỦI RO
- **Độ phức tạp:** 🟢 Thấp (Dễ làm - phạm vi nằm gọn trong `app/services/vncdc_client.py`).
- **Tác động:** Không ảnh hưởng giao diện hay database, chỉ cập nhật network request trong service client.
- **Rủi ro:** Cực kỳ thấp vì payload và headers đã được trích xuất chính xác 100% từ request thực tế người dùng vừa bắt được.

---

## 7. BƯỚC TIẾP THEO
→ Chuyển sang `/plan` để lên chi tiết checklist và tiến hành implement code ngay lập tức.
