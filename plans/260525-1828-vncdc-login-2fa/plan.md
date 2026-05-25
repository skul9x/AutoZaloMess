# Plan: Nâng Cấp VNCDC Login 2FA Flow
Created: 2026-05-25 18:28
Status: 🟡 In Progress

## Overview
Nâng cấp cơ chế đăng nhập VNCDC của dự án **AutoZaloMess** để hỗ trợ xác thực 2 lớp (2FA / OTP) và tuân thủ các chính sách bảo mật mới (Nghị định 13/2023/NĐ-CP - LayThongBao), tránh tình trạng không đăng nhập được do hệ thống VNCDC đã cập nhật từ ngày 20/05/2026. Quá trình này được thực hiện bằng cách chuyển đổi và tích hợp flow đăng nhập ổn định nhất từ dự án **VaccineAnalyzer-Pro-main** sang nền tảng Tkinter của **AutoZaloMess**.

## Tech Stack
- Backend: Python 3
- Libraries: `httpx` (hoặc `requests`), `BeautifulSoup` (bs4), `unittest` hoặc `pytest`
- UI Framework: Tkinter (giao tiếp thông qua `queue.Queue` trong background thread)

## Phases

| Phase | Name | Status | Progress |
|-------|------|--------|----------|
| 01 | [Nâng cấp VncdcClient (`vncdc_client.py`)](./phase-01-client-upgrade.md) | ⬜ Pending | 0% |
| 02 | [Xây dựng giao diện nhập mã OTP (`otp_dialog.py`)](./phase-02-ui-otp-dialog.md) | ⬜ Pending | 0% |
| 03 | [Tích hợp controller & Xử lý bất đồng bộ (`app_controller.py`)](./phase-03-controller-integration.md) | ⬜ Pending | 0% |
| 04 | [Viết suite test & Xác minh trực tiếp (`phase-04-testing.md`)](./phase-04-testing.md) | ⬜ Pending | 0% |

## Quick Commands
- Chạy Test Giả lập Phase 1 & 3: `pytest tests/test_vncdc_client_2fa.py -v`
- Xem tiến độ: `/next`
- Lưu context: `/save-brain`

---
Next Phase: [Phase 01: Nâng cấp VncdcClient](./phase-01-client-upgrade.md)
