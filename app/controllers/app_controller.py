import tkinter as tk
import threading
import queue
import time
import os
import re
from tkinter import filedialog, messagebox
from ..services.vncdc_client import VncdcClient
from ..utils import extract_phone_from_string, normalize_name, save_json, load_json
from ..gui.otp_dialog import OtpDialog

class AppController:
    def __init__(self, window, services, automation_logic):
        self.window = window
        self.storage = services["storage"]
        self.contacts_service = services["contacts"]
        self.report_service = services["report"]
        self.automation_logic = automation_logic

        self.contacts = []
        self.success_count = 0
        self.fail_count = 0
        self.stopped_reason = None

        self.sent_phones = self.storage.load_sent_database()

        self.comm_queue = window.comm_queue
        
        self.vncdc_client = None
        self.vncdc_profile = {}
        self.vncdc_ke_hoach_id = None
        self.is_fetching = False

    def load_initial_data(self):
        """Called after UI is built to load saved data."""
        # Feature 3: Load saved credentials
        saved_user, saved_pass = self.storage.load_credentials()
        if saved_user:
            self.window.fetch_tab.set_credentials(saved_user, saved_pass)

    def handle_vncdc_login(self, username, password, remember):
        if not username or not password:
            self.window.fetch_tab.set_login_status("Vui lòng nhập đầy đủ thông tin", "red")
            return

        self.window.fetch_tab.set_login_status("Đang đăng nhập...", "blue")
        
        def login_task():
            try:
                client = VncdcClient()
                success, status, data = client.login(username, password, remember)
                if status == "2fa_required":
                    self.comm_queue.put(("otp_required", client, data))
                    return
                elif success:
                    profile, ke_hoach_id = client.fetch_profile_and_plan()
                    self.vncdc_client = client
                    self.vncdc_profile = profile or {}
                    self.vncdc_ke_hoach_id = ke_hoach_id
                    
                    # Feature 3: Save credentials if successful
                    self.storage.save_credentials(username, password)
                    
                    msg = f"Đăng nhập thành công. KH_ID: {ke_hoach_id}"
                    self.comm_queue.put(("login_result", True, msg))
                else:
                    client.close()
                    self.comm_queue.put(("login_result", False, data or "Sai tài khoản hoặc mật khẩu"))
            except Exception as e:
                self.comm_queue.put(("login_result", False, f"Lỗi: {str(e)}"))

        threading.Thread(target=login_task, daemon=True).start()
        self._schedule_queue_check()

    def show_otp_and_verify(self, client, message):
        def on_confirm(otp):
            self.otp_dialog.set_loading(True)
            self.otp_dialog.hide_error()
            
            def verify_task():
                try:
                    success, err = client.verify_2fa(otp)
                    if success:
                        profile, ke_hoach_id = client.fetch_profile_and_plan()
                        self.comm_queue.put(("otp_verify_result", True, (client, profile, ke_hoach_id)))
                    else:
                        self.comm_queue.put(("otp_verify_result", False, err or "Mã OTP không chính xác"))
                except Exception as e:
                    self.comm_queue.put(("otp_verify_result", False, f"Lỗi: {str(e)}"))
            
            threading.Thread(target=verify_task, daemon=True).start()
            
        self.otp_dialog = OtpDialog(self.window, error_message=message, on_confirm_callback=on_confirm)

    def handle_vncdc_fetch(self, date_from, date_to):
        # Feature: Batch processing by XA_ID
        xa_ids = self.storage.load_xa_ids()
        
        if not xa_ids:
            self.window.fetch_tab.set_fetch_status("Chưa cấu hình danh sách Xã (XA_ID).")
            self.window.automation_tab.show_warning("Chưa cấu hình", "Vui lòng vào 'Cấu hình Xã' để thêm danh sách mã xã cần lấy dữ liệu.")
            return

        if not self.vncdc_client or not self.vncdc_ke_hoach_id:
            self.window.fetch_tab.set_fetch_status("Chưa có thông tin Kế hoạch tiêm. Hãy đăng nhập lại.")
            return

        if self.is_fetching:
            return

        self.is_fetching = True
        self.window.fetch_tab.set_fetch_status("Đang lấy dữ liệu... Vui lòng chờ.")
        self.window.fetch_tab.fetch_btn.config(state=tk.DISABLED)

        def fetch_task():
            try:
                all_items = []
                total_xas = len(xa_ids)
                
                tinh_id = self.vncdc_profile.get("tinh_id") or 106
                huyen_id = self.vncdc_profile.get("huyen_id") or 10605
                # xa_id will be dynamic
                thon_id = self.vncdc_profile.get("thon_id") or -1
                
                self.comm_queue.put(("fetch_progress", f"Bắt đầu lấy dữ liệu cho {total_xas} xã..."))

                for idx, xa_id_str in enumerate(xa_ids, 1):
                    xa_id = xa_id_str.strip()
                    if not xa_id: continue
                    
                    self.comm_queue.put(("fetch_progress", f"[{idx}/{total_xas}] Đang tải dữ liệu xã {xa_id}..."))
                    
                    base_payload = {
                        "KE_HOACH_TIEM_ID": str(self.vncdc_ke_hoach_id),
                        "MA_TRE": "",
                        "TEN_TRE": "",
                        "TINH_ID": str(tinh_id),
                        "HUYEN_ID": str(huyen_id),
                        "XA_ID": str(xa_id),
                        "THON_ID": str(thon_id),
                        "NGAY_SINH_TU_NGAY": date_from,
                        "NGAY_SINH_TOI_NGAY": date_to,
                        "TEN_NGUOI_THAN": "",
                        "SO_DIEN_THOAI": "",
                        "SESSION_KEY": "BO_SUNG_APP",
                    }

                    # Fetch page 1
                    base_payload["PageNumber"] = "1"
                    try:
                        first_res = self.vncdc_client.search_doi_tuong(base_payload)
                        items_p1 = first_res.get("items", [])
                        all_items.extend(items_p1)
                        
                        total_page = first_res.get("total_page", 1)
                        # total_item = first_res.get("total_item", 0)
                        
                        if total_page > 1:
                            self.comm_queue.put(("fetch_progress", f"[{idx}/{total_xas}] Xã {xa_id}: Đang tải trang 1/{total_page}..."))

                        # Fetch subsequent pages
                        for p in range(2, total_page + 1):
                            self.comm_queue.put(("fetch_progress", f"[{idx}/{total_xas}] Xã {xa_id}: Đang tải trang {p}/{total_page}..."))
                            base_payload["PageNumber"] = str(p)
                            res = self.vncdc_client.search_doi_tuong(base_payload)
                            all_items.extend(res.get("items", []))
                            time.sleep(0.1)
                            
                    except Exception as e:
                        print(f"Error fetching XA {xa_id}: {e}")
                        # self.comm_queue.put(("fetch_progress", f"Lỗi xã {xa_id}: {e}"))
                        # Continue to next XA
                        pass
                    
                    # Small delay between XAs
                    time.sleep(0.5)

                # Process all items (deduplication logic)
                new_contacts = []
                count_added = 0
                count_skipped = 0
                
                seen_phones = set()

                for it in all_items:
                    raw_info = it.get("nguoi_cham_soc", "")
                    phone = extract_phone_from_string(raw_info)
                    
                    if not phone:
                        continue
                    
                    if phone in seen_phones:
                        continue
                    seen_phones.add(phone)
                        
                    name_temp = raw_info.replace(phone, "").strip(" -:.")
                    name_clean = re.sub(r'^M_|^M- ?|^M - ', '', name_temp).strip()

                    if not name_clean or len(name_clean) < 2:
                        child_name = it.get("ho_ten", "")
                        name_clean = f"PH bé {child_name}"

                    # Feature 1: Auto format name to Title Case
                    name_final = normalize_name(name_clean)

                    status = "Đã gửi trước đó" if phone in self.sent_phones else "Chờ gửi"
                    if status == "Đã gửi trước đó":
                        count_skipped += 1
                    else:
                        count_added += 1
                    
                    new_contacts.append({"name": name_final, "phone": phone, "status": status})

                self.comm_queue.put(("fetch_success", new_contacts, count_added, count_skipped))

            except Exception as e:
                self.comm_queue.put(("fetch_error", str(e)))
            finally:
                self.is_fetching = False

        threading.Thread(target=fetch_task, daemon=True).start()
        self._schedule_queue_check()

    def _schedule_queue_check(self):
        pass

    def handle_configure_xa(self):
        """Feature: Open dialog to configure XA_IDs"""
        self.window.fetch_tab.show_xa_settings_dialog(
            self.storage.load_xa_ids,
            self.storage.save_xa_ids
        )

    def on_selection_change(self):
        tab = self.window.automation_tab
        tab.set_contact_status_label(f"Tổng số: {len(self.contacts)} | Đã chọn: {len(tab.get_selected_indices())}")

    def update_contact_list(self):
        tab = self.window.automation_tab
        tab.clear_tree()
        for i, contact in enumerate(self.contacts, 1):
            tab.insert_contact_row(i, contact)
        self.on_selection_change()

    def update_ui_state(self, state=None):
        tab = self.window.automation_tab
        if state is None:
            if self.automation_logic.running:
                state = "paused" if not self.automation_logic.pause_event.is_set() else "running"
            else:
                state = "loaded" if self.contacts else "initial"

        coords_ready = all("Chưa thiết lập" not in v.get() for v in self.window.coord_vars.values())
        mode = self.window.zalo_mode.get()
        fail_image_key = "web_fail_path" if mode == "web" else "app_fail_path"
        ratelimit_image_key = "web_ratelimit_path" if mode == "web" else "app_ratelimit_path"
        success_img_key = "web_success_path" if mode == "web" else "app_success_path"

        images_ready = (
            "Chưa thiết lập" not in self.window.image_path_vars[fail_image_key].get() and 
            "Chưa thiết lập" not in self.window.image_path_vars[ratelimit_image_key].get() and
            "Chưa thiết lập" not in self.window.image_path_vars[success_img_key].get()
        )
        is_ready_to_run = coords_ready and images_ready

        if state == "initial":
            tab.set_status_label("Trạng thái: Sẵn sàng lấy dữ liệu", "#0078D7")
            tab.set_buttons_state(tk.DISABLED, tk.DISABLED, False, False, tk.NORMAL, tk.NORMAL, tk.DISABLED, tk.NORMAL)
            tab.set_message_state(True)
        elif state == "loaded":
            tab.set_buttons_state(tk.NORMAL if is_ready_to_run else tk.DISABLED, tk.NORMAL, False, False, tk.NORMAL, tk.NORMAL, tk.NORMAL, tk.NORMAL)
            tab.set_status_label("Vui lòng thiết lập Tọa độ và Ảnh lỗi!" if not is_ready_to_run else f"Trạng thái: Sẵn sàng gửi ({len(self.contacts)} liên hệ)", "orange" if not is_ready_to_run else "green")
            tab.set_message_state(True)
        elif state == "running":
            tab.set_status_label("Trạng thái: Đang chạy...", "red")
            tab.set_buttons_state(tk.DISABLED, tk.NORMAL, True, False, tk.NORMAL, tk.NORMAL, tk.DISABLED, tk.DISABLED)
            tab.set_message_state(False)
        elif state == "paused":
            tab.set_status_label("Trạng thái: Đã tạm dừng", "orange")
            tab.set_buttons_state(tk.DISABLED, tk.NORMAL, False, True, tk.NORMAL, tk.NORMAL, tk.DISABLED, tk.DISABLED)
            tab.set_message_state(False)
        elif state == "stopping":
            tab.set_status_label("Trạng thái: Đang dừng...", "grey")
            tab.set_buttons_state(tk.DISABLED, tk.DISABLED, True, False, tk.DISABLED, tk.NORMAL, tk.DISABLED, tk.DISABLED)
            tab.set_message_state(False)

    def handle_start(self):
        tab = self.window.automation_tab
        if not self.contacts:
            tab.show_error("Lỗi", "Danh sách liên hệ trống.")
            return

        user_message = tab.get_message_text()
        if not user_message:
            tab.show_error("Lỗi", "Nội dung tin nhắn không được để trống.")
            return

        self.storage.save_message(user_message)
        self.stopped_reason = None

        try:
            params = {key: eval(var.get()) for key, var in self.window.coord_vars.items()}
            mode = self.window.zalo_mode.get()
            fail_image_key = "web_fail_path" if mode == "web" else "app_fail_path"
            ratelimit_image_key = "web_ratelimit_path" if mode == "web" else "app_ratelimit_path"
            success_img_key = "web_success_path" if mode == "web" else "app_success_path"
            
            params["fail_image_path"] = self.window.image_path_vars[fail_image_key].get()
            params["ratelimit_image_path"] = self.window.image_path_vars[ratelimit_image_key].get()
            # Ảnh rate limit thứ 2 cho cùng mode
            ratelimit_image_key_2 = "web_ratelimit_path_2" if mode == "web" else "app_ratelimit_path_2"
            params["ratelimit_image_path_2"] = self.window.image_path_vars[ratelimit_image_key_2].get()
            params["success_image_path"] = self.window.image_path_vars[success_img_key].get()

            if not os.path.exists(params["fail_image_path"]) or \
               not os.path.exists(params["ratelimit_image_path"]) or \
               not os.path.exists(params["success_image_path"]):
                tab.show_error("Lỗi", f"Chưa thiết lập hoặc không tìm thấy đủ 3 file ảnh điều kiện cho chế độ {mode.upper()}.")
                return
        except Exception as e:
            tab.show_error("Lỗi tọa độ", f"Một hoặc nhiều tọa độ không hợp lệ. Lỗi: {e}")
            return

        self.success_count = 0
        self.fail_count = 0
        self.update_ui_state("running")
        self.window.automation_thread = threading.Thread(target=self.automation_logic.run, args=(list(self.contacts), user_message, params), daemon=True)
        self.window.automation_thread.start()

    def handle_pause(self):
        self.automation_logic.pause()
        self.update_ui_state("paused")

    def handle_resume(self):
        self.automation_logic.resume()
        self.update_ui_state("running")

    def handle_cancel(self):
        tab = self.window.automation_tab
        if self.automation_logic.running:
            if not tab.ask_yesno("Xác nhận", "Bạn có chắc chắn muốn hủy bỏ tác vụ đang chạy?"):
                return
        self.automation_logic.stop()
        self.update_ui_state("stopping")

    def delete_selected_contacts(self):
        tab = self.window.automation_tab
        if self.automation_logic.running:
            tab.show_warning("Không thể xóa", "Không thể xóa danh sách khi tác vụ đang chạy.")
            return
        selected = tab.get_selected_indices()
        if not selected:
            tab.show_warning("Chưa chọn", "Vui lòng chọn các liên hệ cần xóa.")
            return
        if tab.ask_yesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa {len(selected)} liên hệ đã chọn?"):
            for index in sorted(selected, reverse=True):
                del self.contacts[index]
            self.update_contact_list()
            self.update_ui_state()

    def export_report(self):
        tab = self.window.automation_tab
        if not self.contacts:
            tab.show_warning("Không có dữ liệu", "Không có dữ liệu liên hệ để xuất.")
            return
        file_path = tab.ask_save_csv()
        if not file_path:
            return
        try:
            self.report_service.export_csv(file_path, self.contacts)
            tab.show_info("Thành công", f"Báo cáo đã được lưu tại:\n{file_path}")
        except Exception as e:
            tab.show_error("Lỗi", f"Không thể lưu file báo cáo:\n{e}")

    def handle_load_fail_image(self, image_key):
        tab = self.window.automation_tab
        file_path = tab.show_open_image()
        if file_path:
            self.window.image_path_vars[image_key].set(file_path)
            self.storage.save_image_config({key: var.get() for key, var in self.window.image_path_vars.items()})
            self.update_ui_state()

    def capture_coordinate(self, coord_key):
        tab = self.window.automation_tab
        tab.withdraw_root()
        time.sleep(0.2)

        def on_click(event):
            coords = (event.x_root, event.y_root)
            self.window.coord_vars[coord_key].set(str(coords))
            self.storage.save_coords({key: var.get() for key, var in self.window.coord_vars.items()})
            overlay.destroy()
            tab.deiconify_root()
            self.update_ui_state()

        def on_escape(event):
            overlay.destroy()
            tab.deiconify_root()

        overlay = tab.fullscreen_overlay(on_click, on_escape)

    def process_comm_queue(self):
        tab = self.window.automation_tab
        fetch_tab = self.window.fetch_tab
        
        was_running = any(s in tab.status_label.cget("text") for s in ["Đang chạy", "Đang dừng", "Đã tạm dừng"])
        
        while not self.comm_queue.empty():
            try:
                message = self.comm_queue.get_nowait()
                msg_type = message[0]
                
                if msg_type == "log":
                    tab.log_text.config(state=tk.NORMAL)
                    tab.log_text.insert(tk.END, message[1] + "\n")
                    tab.log_text.see(tk.END)
                    tab.log_text.config(state=tk.DISABLED)
                elif msg_type == "status":
                    index, status_text = message[1], message[2]
                    if 0 <= index < len(self.contacts):
                        self.contacts[index]["status"] = status_text
                        try:
                            item_id = tab.tree.get_children()[index]
                            current_tags = tab.tree.item(item_id, "tags")
                            is_already_processed = "success" in current_tags or "failure" in current_tags
                            
                            tag = ""
                            if "Thành công" in status_text:
                                tag = "success"
                                if not is_already_processed:
                                    self.success_count += 1
                                    self.storage.add_phone_to_database(self.sent_phones, self.contacts[index]["phone"])
                            elif "Thất bại" in status_text:
                                tag = "failure"
                                if not is_already_processed:
                                    self.fail_count += 1
                            elif "Đang xử lý" in status_text:
                                tag = "processing"
                            
                            tab.set_row_status(index, status_text, tag)
                        except IndexError:
                            pass
                elif msg_type == "stopped_due_to_ratelimit":
                    self.stopped_reason = "ratelimit"
                
                elif msg_type == "login_result":
                    success, msg = message[1], message[2]
                    color = "green" if success else "red"
                    fetch_tab.set_login_status(msg, color, success)
                    
                elif msg_type == "otp_required":
                    client, data = message[1], message[2]
                    fetch_tab.set_login_status("Yêu cầu nhập OTP", "orange")
                    self.show_otp_and_verify(client, data)
                    
                elif msg_type == "otp_verify_result":
                    success, data = message[1], message[2]
                    if success:
                        client, profile, ke_hoach_id = data
                        self.vncdc_client = client
                        self.vncdc_profile = profile or {}
                        self.vncdc_ke_hoach_id = ke_hoach_id
                        
                        username, password, _ = fetch_tab.get_login_info()
                        self.storage.save_credentials(username, password)
                        
                        if hasattr(self, "otp_dialog") and self.otp_dialog.winfo_exists():
                            self.otp_dialog._close()
                            
                        msg = f"Đăng nhập thành công. KH_ID: {ke_hoach_id}"
                        fetch_tab.set_login_status(msg, "green", True)
                    else:
                        if hasattr(self, "otp_dialog") and self.otp_dialog.winfo_exists():
                            self.otp_dialog.set_loading(False)
                            self.otp_dialog.show_error(data)
                    
                elif msg_type == "fetch_progress":
                    fetch_tab.set_fetch_status(message[1])
                    
                elif msg_type == "fetch_success":
                    new_contacts, added, skipped = message[1], message[2], message[3]
                    self.contacts = new_contacts
                    self.update_contact_list()
                    self.update_ui_state("loaded")
                    
                    fetch_tab.set_fetch_status(f"Hoàn tất! Đã lấy {len(new_contacts)} liên hệ.")
                    fetch_tab.fetch_btn.config(state=tk.NORMAL)
                    
                    self.window.notebook.select(1)
                    tab.show_info("Lấy dữ liệu thành công", f"Đã tải {len(new_contacts)} liên hệ từ VNCDC.\n(Thêm mới: {added}, Đã gửi trước đó: {skipped})")
                    
                elif msg_type == "fetch_error":
                    fetch_tab.set_fetch_status(f"Lỗi: {message[1]}")
                    fetch_tab.fetch_btn.config(state=tk.NORMAL)
                    tab.show_error("Lỗi lấy dữ liệu", message[1])

            except (queue.Empty, IndexError):
                break

        is_running_now = self.automation_logic.running
        if was_running and not is_running_now:
            tab.topmost(True)
            if self.stopped_reason == "ratelimit":
                tab.show_warning("Bị giới hạn", "Đã gửi quá nhiều tin nhắn! Zalo đã tạm thời giới hạn tính năng tìm kiếm của bạn.\n\nVui lòng chờ một thời gian trước khi thử lại.")
            else:
                tab.show_info("Hoàn thành", f"Đã hoàn thành xong gửi tin nhắn.\n\nThành công: {self.success_count}\nThất bại: {self.fail_count}")
            tab.topmost(False)
            self.update_ui_state()

        self.window.after(100, self.process_comm_queue)

    def on_f9_press(self, event=None):
        tab = self.window.automation_tab
        if tab.start_button["state"] == tk.NORMAL:
            self.comm_queue.put(("log", "--- Phím nóng F9 được nhấn: Bắt đầu ---"))
            tab.start_button.invoke()

    def on_f10_press(self, event=None):
        tab = self.window.automation_tab
        if tab.pause_button.winfo_ismapped() and tab.pause_button["state"] == tk.NORMAL:
            self.comm_queue.put(("log", "--- Phím nóng F10 được nhấn: Tạm dừng ---"))
            tab.pause_button.invoke()
        elif tab.resume_button.winfo_ismapped() and tab.resume_button["state"] == tk.NORMAL:
            self.comm_queue.put(("log", "--- Phím nóng F10 được nhấn: Tiếp tục ---"))
            tab.resume_button.invoke()

    def on_f11_press(self, event=None):
        tab = self.window.automation_tab
        if tab.cancel_button["state"] == tk.NORMAL:
            self.comm_queue.put(("log", "--- Phím nóng F11 được nhấn: Hủy bỏ ---"))
            self.handle_cancel()

    def backup_contacts(self):
        """Sao lưu danh sách liên hệ hiện tại ra file JSON."""
        if not self.contacts:
            messagebox.showwarning("Cảnh báo", "Không có liên hệ nào để sao lưu.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Chọn nơi lưu file sao lưu"
        )
        if file_path:
            try:
                save_json(file_path, self.contacts)
                messagebox.showinfo("Thành công", f"Đã sao lưu {len(self.contacts)} liên hệ thành công.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu file sao lưu:\n{e}")

    def restore_contacts(self):
        """Khôi phục danh sách liên hệ từ file JSON sao lưu."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Chọn file sao lưu để khôi phục"
        )
        if not file_path:
            return
            
        data = load_json(file_path, None)
        if data is None or not isinstance(data, list):
            messagebox.showerror("Lỗi", "File không hợp lệ hoặc không đúng định dạng danh sách JSON.")
            return
            
        valid_contacts = []
        for item in data:
            if not isinstance(item, dict) or "phone" not in item or "name" not in item:
                messagebox.showerror("Lỗi", "Cấu trúc dữ liệu liên hệ trong file không hợp lệ (mỗi liên hệ cần có 'phone' và 'name').")
                return
            
            phone = str(item["phone"]).strip()
            name = str(item["name"]).strip()
            status = item.get("status", "Chờ gửi")
            valid_contacts.append({"phone": phone, "name": name, "status": status})
            
        if not valid_contacts:
            messagebox.showwarning("Cảnh báo", "File sao lưu trống hoặc không chứa liên hệ hợp lệ.")
            return
            
        choice = messagebox.askyesnocancel(
            "Xác nhận khôi phục",
            "Bạn muốn khôi phục dữ liệu bằng cách nào?\n\n"
            "- Chọn 'Yes' (Ghi đè): Thay thế hoàn toàn danh sách hiện có.\n"
            "- Chọn 'No' (Thêm tiếp): Ghép thêm liên hệ mới vào danh sách (không trùng SĐT).\n"
            "- Chọn 'Cancel': Hủy thao tác."
        )
        
        if choice is None:
            # Cancel
            return
        elif choice is True:
            # Overwrite
            self.contacts = valid_contacts
            messagebox.showinfo("Thành công", f"Đã ghi đè thành công {len(valid_contacts)} liên hệ.")
        else:
            # Merge
            existing_phones = {c["phone"] for c in self.contacts}
            added_count = 0
            for item in valid_contacts:
                if item["phone"] not in existing_phones:
                    self.contacts.append(item)
                    existing_phones.add(item["phone"])
                    added_count += 1
            messagebox.showinfo("Thành công", f"Đã thêm nối tiếp thành công {added_count} liên hệ mới.")
            
        self.update_contact_list()
        self.update_ui_state()