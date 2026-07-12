import httpx
from .vncdc_parser import parse_login_token, parse_ke_hoach_tiem_id, parse_search_response

class VncdcClient:
    def __init__(self, base_url="https://tiemchung.vncdc.gov.vn"):
        self.base_url = base_url.rstrip("/")
        self.session = httpx.Client(base_url=self.base_url, follow_redirects=True, timeout=30.0, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def close(self):
        self.session.close()

    def get_login_page(self):
        r = self.session.get("/Account/Login")
        r.raise_for_status()
        token = parse_login_token(r.text)
        return token

    def login(self, username, password, remember=True):
        try:
            r_get = self.session.get("/Account/Login")
            r_get.raise_for_status()
            token = parse_login_token(r_get.text)
        except Exception as e:
            return False, "failed", f"Không thể tải trang đăng nhập: {str(e)}"

        data = {
            "__RequestVerificationToken": token,
            "UserName": username,
            "password": password,
            "remember_me_check": "true" if remember else "false",
            "remember_me": "true" if remember else "false",
        }

        try:
            r_post = self.session.post(
                "/Account/Login",
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Origin": self.base_url,
                    "Referer": f"{self.base_url}/Account/Login",
                },
                follow_redirects=False
            )
        except Exception as e:
            return False, "failed", f"Gửi yêu cầu đăng nhập thất bại: {str(e)}"

        is_2fa_required = False
        message = "Yêu cầu xác thực 2 lớp"

        # Check redirect 302 đến VerifyTwoFactor
        if r_post.status_code == 302 and "VerifyTwoFactor" in r_post.headers.get("Location", ""):
            is_2fa_required = True
        else:
            try:
                json_resp = r_post.json()
                if json_resp.get("TwoFactorRequired"):
                    is_2fa_required = True
                    message = json_resp.get("Message", "Yêu cầu xác thực 2 lớp")
            except Exception:
                if ".ASPXAUTH" not in self.session.cookies:
                    return False, "failed", "Server không trả về phản hồi hợp lệ."

        if is_2fa_required:
            try:
                self.session.get(
                    "/DonViHanhChinh/LayThongBao",
                    headers={
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": f"{self.base_url}/Account/Login",
                        "Accept": "*/*"
                    }
                )
            except Exception:
                pass
            return True, "2fa_required", message
        else:
            if ".ASPXAUTH" in self.session.cookies:
                return True, "success", None
            else:
                error_message = "Sai tài khoản hoặc mật khẩu"
                try:
                    json_resp = r_post.json()
                    if json_resp.get("Message"):
                        error_message = json_resp.get("Message")
                except Exception:
                    pass
                return False, "failed", error_message

    def verify_2fa(self, code):
        data = {
            "code": code
        }
        try:
            r = self.session.post(
                "/Account/VerifyTwoFactor",
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Origin": self.base_url,
                    "Referer": f"{self.base_url}/Account/Login",
                }
            )
        except Exception as e:
            return False, f"Gửi mã OTP thất bại: {str(e)}"

        if ".ASPXAUTH" in self.session.cookies:
            return True, None

        response_text = r.text.strip()
        if r.status_code == 200 and not response_text:
            try:
                test_resp = self.session.get(
                    "/Home/GetNumberOfNewMessage",
                    headers={
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": f"{self.base_url}/TiemChung/DoiTuong/Index"
                    },
                    timeout=5.0
                )
                if test_resp.status_code == 200 and ".ASPXAUTH" in self.session.cookies:
                    return True, None
            except Exception:
                pass

        if response_text:
            try:
                json_resp = r.json()
                if json_resp.get("Success"):
                    return True, None
                else:
                    return False, json_resp.get("Message", "Mã OTP không đúng.")
            except Exception as e:
                return False, f"Lỗi xử lý phản hồi từ server: {str(e)}"

        return False, "Mã OTP không đúng hoặc đã hết hạn."

    def fetch_profile_and_plan(self):
        r = self.session.get("/KeHoachTiemPhatSinhArea/KeHoachTiemPhatSinh")
        r.raise_for_status()
        ke_hoach_id = parse_ke_hoach_tiem_id(r.text)
        profile = {}
        return profile, ke_hoach_id

    def search_doi_tuong(self, payload):
        r = self.session.post(
            "/KeHoachTiemPhatSinhArea/NhapBoSung/GetDanhSachDoiTuongTiem/",
            data=payload,
            headers={
                "Accept": "text/html, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/KeHoachTiemPhatSinhArea/KeHoachTiemPhatSinh",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        r.raise_for_status()
        return parse_search_response(r.text)

    def execute_curl_cmd(self, curl_cmd: str):
        """
        Parses a raw curl command string and executes it using the existing session.
        This is a basic parser tailored for the specific format provided by the user.
        """
        import shlex

        # Clean up the command
        cmd = curl_cmd.replace("\\\n", " ").replace("\\", "").strip()
        if not cmd.startswith("curl"):
            return None

        try:
            tokens = shlex.split(cmd)
        except:
            # Fallback for simple splitting if shlex fails on complex chars
            tokens = cmd.split()

        url = None
        method = "GET"
        headers = {}
        data = None

        i = 1
        while i < len(tokens):
            token = tokens[i]
            
            if token.startswith("http"):
                url = token
            elif token in ("-H", "--header"):
                i += 1
                if i < len(tokens):
                    header_str = tokens[i]
                    if ":" in header_str:
                        key, value = header_str.split(":", 1)
                        headers[key.strip()] = value.strip()
            elif token == "--data-raw" or token == "--data" or token == "-d":
                i += 1
                if i < len(tokens):
                    data = tokens[i]
                    method = "POST"
            
            i += 1

        if not url:
            return None

        # Update specific headers but keep session defaults where appropriate
        # Note: We don't want to override the session cookies blindly if the curl has specific cookies,
        # but usually we want to use the CURL's cookies if provided, or the session's if not.
        # For this specific task, the curl command likely contains the valid session cookie.
        
        # We will create a request using the parsed info.
        # If 'Content-Type' is in headers, let it decide the encoding.
        
        # 'data' string from curl is usually x-www-form-urlencoded. 
        # We pass it directly as 'content' or parse it to 'data' dict/list?
        # httpx 'data' arg accepts dict (form-encoded) or str (raw body).
        
        req_headers = self.session.headers.copy()
        req_headers.update(headers)
        
        # Remove Accept-Encoding to avoid decompression issues if handled manually (httpx handles it)
        if "cmp" in req_headers.get("Accept-Encoding", ""):
            del req_headers["Accept-Encoding"]

        r = self.session.request(method, url, headers=req_headers, content=data)
        r.raise_for_status()
        
        # We assume the response format is the same as the search result
        return parse_search_response(r.text)

    def get_doi_tuong_phone(self, doi_tuong_id, ho_ten=None):
        try:
            url = f"/TiemChung/DoiTuong/Edit?doiTuongId={doi_tuong_id}"
            if ho_ten:
                import urllib.parse
                url += f"&hoTen={urllib.parse.quote_plus(ho_ten)}"
            r = self.session.get(
                url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": f"{self.base_url}/TiemChung/DoiTuong/Index",
                    "X-Requested-With": "XMLHttpRequest",
                }
            )
            r.raise_for_status()
            from .vncdc_parser import parse_doi_tuong_phone_from_edit_page
            return parse_doi_tuong_phone_from_edit_page(r.text)
        except Exception as e:
            print(f"Error fetching phone for object {doi_tuong_id}: {e}")
            return ""