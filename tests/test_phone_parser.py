import pytest
from app.services.vncdc_parser import parse_doi_tuong_phone_from_edit_page

def test_parse_phone_from_js_model():
    html = """
    <html>
    <body>
    <script type="text/javascript">
        var TiemChung$DoiTuong$EditModel = {"DienThoai": null, "DienThoaiMe": "0365240748", "DienThoaiBo": "********", "DienThoaiNguoiGiamHo": null};
    </script>
    </body>
    </html>
    """
    phone = parse_doi_tuong_phone_from_edit_page(html)
    assert phone == "0365240748"

def test_parse_phone_from_js_model_target():
    html = """
    <html>
    <body>
    <script type="text/javascript">
        var TiemChung$DoiTuong$EditModel = {"DienThoai": "0987654321", "DienThoaiMe": "0365240748", "DienThoaiBo": "********"};
    </script>
    </body>
    </html>
    """
    phone = parse_doi_tuong_phone_from_edit_page(html)
    assert phone == "0987654321"

def test_parse_phone_from_js_model_masked():
    html = """
    <html>
    <body>
    <script type="text/javascript">
        var TiemChung$DoiTuong$EditModel = {"DienThoai": "********", "DienThoaiMe": "********", "DienThoaiBo": "********"};
    </script>
    </body>
    </html>
    """
    phone = parse_doi_tuong_phone_from_edit_page(html)
    assert phone == ""

def test_parse_phone_from_inputs_fallback():
    html = """
    <html>
    <body>
    <input type="text" id="txtDienThoaiMe_Sua" value="0365240748" />
    <input type="text" id="txtDienThoaiBo_Sua" value="********" />
    </body>
    </html>
    """
    phone = parse_doi_tuong_phone_from_edit_page(html)
    assert phone == "0365240748"

def test_parse_phone_no_data():
    html = "<html><body>No phone here</body></html>"
    phone = parse_doi_tuong_phone_from_edit_page(html)
    assert phone == ""
