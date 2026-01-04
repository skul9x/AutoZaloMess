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
        self.controlled_sleep(2.5)

        if self.check_image(params["ratelimit_image_path"]):
            self.log("!!! PHÁT HIỆN LỖI GIỚI HẠN TÌM KIẾM TỪ ZALO !!!")
            return "rate_limited"

        if self.check_image(params["fail_image_path"]):
            self.log("=> Lỗi: Số điện thoại không tìm thấy. Bỏ qua...")
            return "failed"
        else:
            self.log("=> Thành công: Bắt đầu gửi tin nhắn.")
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
        
        self.log(f"Hoàn thành xử lý cho {name}.")
        return "success"

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
            if contact["status"] == "Đã gửi trước đó":
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