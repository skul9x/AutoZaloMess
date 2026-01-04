import re
from bs4 import BeautifulSoup

def parse_login_token(html):
    m = re.search(r'name="__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"', html)
    if not m:
        m = re.search(r'__RequestVerificationToken[^>]*value="([^"]+)"', html)
    return m.group(1) if m else ""

def parse_ke_hoach_tiem_id(html):
    patterns = [
        r'id="HF_KE_HOACH_TIEM_ID_SEARCH_BOX"[^>]*value="([^"]+)"',
        r'id="KE_HOACH_TIEM_BS"[^>]*value="([^"]+)"',
        r'KE_HOACH_TIEM_ID\s*=\s*(\d+)',
    ]
    for p in patterns:
        m = re.search(p, html)
        if m:
            v = m.group(1).strip()
            if v.isdigit():
                return int(v)
    return None

def parse_search_response(html):
    soup = BeautifulSoup(html, "html.parser")
    def get_hidden_int(id_):
        el = soup.find("input", {"id": id_})
        if not el or not el.get("value"):
            return None
        v = el["value"].strip()
        return int(v) if v.isdigit() else None

    page_size = get_hidden_int("pageSize") or 10
    page_number = get_hidden_int("pageNumber") or 1
    total_item = get_hidden_int("totalItem") or 0
    page_data_count = get_hidden_int("pageDataListBS") or 0

    items = []
    table = soup.find("table", {"id": "DanhSachTreBoSung"})
    if table:
        tbody = table.find("tbody")
        if tbody:
            trs = tbody.find_all("tr", recursive=False)
            for tr in trs:
                doi_tuong_id = tr.get("doituongid") or tr.get("doiTuongID") or tr.get("doituongId")
                tds = tr.find_all("td", recursive=False)
                stt = tds[1].get_text(strip=True) if len(tds) > 1 else ""
                name_label = tr.find("label", id=re.compile(r"^NAME-"))
                ho_ten = name_label.get_text(strip=True) if name_label else ""
                ma_span = tr.find("span", class_=re.compile(r"color-warning"))
                ma_doi_tuong = ma_span.get_text(strip=True) if ma_span else ""
                ngay_sinh = tds[4].get_text(strip=True) if len(tds) > 4 else ""
                nguoi_cs = tds[5].get_text(separator=" ", strip=True) if len(tds) > 5 else ""
                dia_chi = tds[6].get_text(strip=True) if len(tds) > 6 else ""
                items.append({
                    "doi_tuong_id": doi_tuong_id or "",
                    "stt": stt,
                    "ho_ten": ho_ten,
                    "ma_doi_tuong": ma_doi_tuong,
                    "ngay_sinh": ngay_sinh,
                    "nguoi_cham_soc": nguoi_cs,
                    "dia_chi": dia_chi,
                })

    total_page = (total_item + page_size - 1) // page_size if page_size else 1
    return {
        "page_size": page_size,
        "page_number": page_number,
        "total_item": total_item,
        "total_page": total_page,
        "page_data_count": page_data_count,
        "items": items,
        "raw_html": html,
    }