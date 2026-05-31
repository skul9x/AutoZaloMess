# Plan: AutoZaloMess - Skip Failed Status & Backup/Restore Contacts
Created: 2026-05-31
Status: 🟡 In Progress

## Overview
Dự án bổ sung 2 tính năng quan trọng:
1. **Skip Failed Contacts**: Bỏ qua không gửi tin đối với các số điện thoại đã có trạng thái "Thất bại".
2. **Backup/Restore Contacts**: Cho phép sao lưu danh sách SĐT hiện tại sang file JSON (có dialog hỏi đường dẫn) và khôi phục lại với tùy chọn Ghi đè (Replace) hoặc Thêm nối tiếp (Append).

## Tech Stack
- **Language**: Python 3.x
- **Framework**: Tkinter (Standard GUI)
- **Libs**: json, os, tkinter.filedialog

## Phases

| Phase | Name | Status | Progress |
|-------|------|--------|----------|
| 01 | Bỏ qua SĐT "Thất bại" khi gửi tin | ⬜ Pending | 0% |
| 02 | Thiết kế UI Sao lưu & Khôi phục | ⬜ Pending | 0% |
| 03 | Logic Sao lưu & Khôi phục trong Controller | ⬜ Pending | 0% |

## Quick Commands
- Chạy thử ứng dụng: `python main.py`
- Chạy unit test Phase 1: `python -m unittest tests/test_skip_failed.py`
- Chạy unit test Phase 3: `python -m unittest tests/test_backup_restore.py`
