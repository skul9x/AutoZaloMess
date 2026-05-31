import random
import threading
import time
import pyautogui
import pyperclip

class AutomationLogic:
    def __init__(self, comm_queue):
        self.comm_queue = comm_queue
        self.running = False
        self.pause_event = threading.Event()

    def log(self, message):
        self.comm_queue.put(("log", message))

    def stop(self):
        self.running = False
        self.pause_event.set()

    def pause(self):
        self.pause_event.clear()
        self.log("--- Tác vụ đã tạm dừng ---")

    def resume(self):
        self.pause_event.set()
        self.log("--- Tác vụ đã tiếp tục ---")

    def check_image(self, image_path, confidence=0.8):
        try:
            location = pyautogui.locateOnScreen(image_path, region=(0, 0, 1000, 600), confidence=confidence)
            return bool(location)
        except Exception as e:
            self.log(f"Lỗi khi tìm ảnh '{image_path}': {e}")
            return False

    def wait_for_any_image(self, images_dict, timeout=10, confidence=0.8):
        start_time = time.time()
        while self.running and time.time() - start_time < timeout:
            self.pause_event.wait()
            if not self.running: return None, None
            
            for state, image_path in images_dict.items():
                if image_path and 'Chưa thiết lập' not in image_path:
                    try:
                        location = pyautogui.locateOnScreen(image_path, region=(0, 0, 1000, 600), confidence=confidence)
                        if location:
                            return state, location
                    except Exception:
                        pass
            time.sleep(0.3)
        return None, None

    def process_contact(self, phone, name, message_template, params):
        if not self.running:
            return "stopped"
        self.log("-" * 30)
        self.log(f"Đang xử lý SĐT: {phone} | Tên: {name}")

        try:
            formatted_message = message_template.format(name=name, phone=phone)
        except KeyError as e:
            self.log(f"LỖI: Nội dung tin nhắn có chứa biến không hợp lệ {e}.")
            self.stop()
            return "error"

        pyautogui.click(params["search_coords"])
        self.controlled_sleep(1)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.typewrite(phone)
        self.controlled_sleep(1)
        
        images_to_check = {
            "rate_limited": params.get("ratelimit_image_path"),
            "rate_limited_2": params.get("ratelimit_image_path_2"),
            "failed": params.get("fail_image_path"),
            "success": params.get("success_image_path")
        }
        
        self.log("Đang tìm kết quả...")
        found_state, location = self.wait_for_any_image(images_to_check, timeout=10)

        if found_state in ("rate_limited", "rate_limited_2"):
            self.log("!!! PHÁT HIỆN LỖI GIỚI HẠN TÌM KIẾM TỪ ZALO !!!")
            return "rate_limited"

        elif found_state == "failed":
            self.log("=> Lỗi: Số điện thoại không tìm thấy hoặc bị chặn. Bỏ qua...")
            pyautogui.click(params["search_coords"])
            self.controlled_sleep(0.5)
            pyautogui.hotkey("ctrl", "a")
            self.controlled_sleep(0.1)
            pyautogui.press("backspace")
            self.controlled_sleep(0.3)
            
            # Chờ ảnh "Không tìm thấy" biến mất khỏi màn hình để tránh kẹt cho số sau
            fail_img = params.get("fail_image_path")
            if fail_img and 'Chưa thiết lập' not in fail_img:
                for _ in range(10):  # Tối đa ~2 giây
                    if not self.check_image(fail_img):
                        break
                    self.controlled_sleep(0.2)
                    
            return "failed"
            
        elif found_state == "success":
            self.log("=> Thành công: Đã tìm thấy người dùng. Bắt đầu gửi tin nhắn.")
            self.controlled_sleep(0.3)
            pyautogui.click(params["friend_coords"])
            self.controlled_sleep(0.5)
            pyautogui.click(params["messagebox_coords"])
            self.controlled_sleep(0.1)
            pyautogui.hotkey("ctrl", "a")
            self.controlled_sleep(0.1)
            pyperclip.copy(formatted_message)
            pyautogui.hotkey("ctrl", "v")
            self.controlled_sleep(0.5)
            pyautogui.press("enter")
            self.log("Đã gửi tin nhắn thành công.")
            return "success"
            
        else:
            self.log("=> Lỗi Timeout: Mạng quá lag hoặc không nhận diện được kết quả trả về sau 10s. Bỏ qua...")
            pyautogui.click(params["search_coords"])
            self.controlled_sleep(0.5)
            pyautogui.hotkey("ctrl", "a")
            self.controlled_sleep(0.1)
            pyautogui.press("backspace")
            self.controlled_sleep(0.3)

            # Chờ ảnh "Không tìm thấy" hoặc kết quả cũ biến mất
            fail_img = params.get("fail_image_path")
            if fail_img and 'Chưa thiết lập' not in fail_img:
                for _ in range(10):
                    if not self.check_image(fail_img):
                        break
                    self.controlled_sleep(0.2)
                    
            return "failed"

    def controlled_sleep(self, duration):
        end_time = time.time() + duration
        while self.running and time.time() < end_time:
            self.pause_event.wait()
            if not self.running:
                break
            time.sleep(0.1)

    def run(self, contacts, message_template, params):
        self.running = True
        self.pause_event.set()
        
        self.log("=== BẮT ĐẦU KỊCH BẢN ===")
        self.log("Vui lòng không sử dụng chuột và bàn phím trong 5 giây tới...")
        self.controlled_sleep(5)

        for i, contact in enumerate(contacts):
            if contact["status"] in ("Đã gửi trước đó", "Thành công", "Thất bại"):
                continue

            self.comm_queue.put(("status", i, "Đang xử lý..."))
            self.pause_event.wait()
            if not self.running:
                self.log("Tác vụ đã bị hủy bởi người dùng.")
                break
            
            status = self.process_contact(contact["phone"], contact["name"], message_template, params)
            
            if status == "rate_limited":
                self.comm_queue.put(("stopped_due_to_ratelimit",))
                self.stop()
                break
            elif status == "success":
                self.comm_queue.put(("status", i, "Thành công"))
            elif status == "failed":
                self.comm_queue.put(("status", i, "Thất bại"))
            
            random_sleep = random.randint(300, 500) / 1000.0
            self.controlled_sleep(random_sleep)
            
        if self.running:
            self.log("=== KỊCH BẢN HOÀN TẤT ===")
        
        self.running = False
        self.log("--- Luồng xử lý ngầm đã kết thúc ---")