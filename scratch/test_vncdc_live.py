"""
Interactive Live Test Script for VNCDC 2FA login
This script runs in terminal, lets you input username and password, 
and handles OTP prompt interactively if the server requests 2FA.
"""
import sys
import os

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_live_test():
    print("====================================================")
    print("     VNCDC 2FA LIVE LOGIN INTERACTIVE TEST SCRIPT   ")
    print("====================================================")
    
    # 1. Ask credentials
    username = input("Username [bn_dv_tcdvquevo]: ").strip() or "bn_dv_tcdvquevo"
    password = input("Password [Tinh@2027]: ").strip() or "Tinh@2027"
    
    print(f"\n[+] Khởi tạo kết nối tới VNCDC với user '{username}'...")
    
    try:
        from app.services.vncdc_client import VncdcClient
    except ImportError:
        print("[!] Không tìm thấy VncdcClient thực tế. Đang chạy ở chế độ giả lập (Mock Mode)...")
        # Define mock client class for visual preview
        class MockVncdcClient:
            def __init__(self):
                self.cookies = {}
            def login(self, username, password, remember=True):
                print(f"[*] Gửi request POST AJAX đăng nhập cho {username}...")
                print("[*] Gọi GET /DonViHanhChinh/LayThongBao...")
                return True, "2fa_required", "Vui lòng mở Google Authenticator và nhập mã OTP."
            def verify_2fa(self, code):
                print(f"[*] Gửi POST AJAX tới /Account/VerifyTwoFactor với OTP '{code}'...")
                if code == "123456":
                    self.cookies[".ASPXAUTH"] = "mock_aspxauth_cookie_token_123456"
                    return True, None
                return False, "Mã xác thực OTP không chính xác hoặc đã hết hạn!"
            def fetch_profile_and_plan(self):
                print("[+] Đăng nhập thành công! Đang tải thông tin cá nhân và kế hoạch...")
                return "1060501" # Mock KeHoachId
        VncdcClient = MockVncdcClient
        
    client = VncdcClient()
    success, status, data = client.login(username, password)
    
    if not success:
        print(f"[-] Đăng nhập thất bại: {data}")
        return
        
    if status == "2fa_required":
        print(f"\n[!] VNCDC Yêu cầu Xác thực 2 lớp (2FA)!")
        print(f"--> Hướng dẫn: {data}")
        
        while True:
            otp_code = input("\n🔐 Nhập mã OTP 6 số (hoặc gõ 'exit' để hủy): ").strip()
            if otp_code.lower() == 'exit':
                print("[*] Đã hủy kiểm thử.")
                break
                
            if len(otp_code) != 6 or not otp_code.isdigit():
                print("[!] Vui lòng nhập đúng 6 chữ số!")
                continue
                
            otp_success, err_msg = client.verify_2fa(otp_code)
            if otp_success:
                print("\n[+] XÁC THỰC OTP THÀNH CÔNG!")
                ke_hoach_id = client.fetch_profile_and_plan()
                print(f"[+] Lấy thành công ID Kế hoạch tiêm chủng: {ke_hoach_id}")
                print("[+] Kiểm thử kết nối LIVE Hoàn tất thành công tốt đẹp!")
                break
            else:
                print(f"[-] Lỗi xác thực OTP: {err_msg}. Vui lòng thử lại!")
                
    elif status == "success":
        print("\n[+] ĐĂNG NHẬP THÀNH CÔNG THẲNG (Không cần 2FA)!")
        ke_hoach_id = client.fetch_profile_and_plan()
        print(f"[+] Lấy thành công ID Kế hoạch tiêm chủng: {ke_hoach_id}")
        print("[+] Kiểm thử kết nối LIVE Hoàn tất thành công!")
        
if __name__ == "__main__":
    run_live_test()
