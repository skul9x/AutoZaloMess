import sys
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.utils import clean_contact_name_and_role, format_message_for_contact

class TestContactNameAndRole:
    @pytest.mark.parametrize("raw_name, expected_name, expected_is_mother", [
        ("Nguyễn Đình Tuấn / (mẹ) Nguyễn Thị Hoàn", "Nguyễn Thị Hoàn", True),
        ("Ngô Viết Xuân / (mẹ) Nguyễn Thị Kim Dung", "Nguyễn Thị Kim Dung", True),
        ("(Bố) Nguyễn Văn Bá / (Mẹ) Nguyễn Thị Thanh", "Nguyễn Thị Thanh", True),
        ("(Mẹ) Nguyễn Thị Hoàn / (Bố) Nguyễn Đình Tuấn", "Nguyễn Thị Hoàn", True),
        ("Trần Duy Vũ / (mẹ) Đỗ Thị Ngân", "Đỗ Thị Ngân", True),
        ("Nguyễn Đức Chỉnh / (mẹ) Nguyễn Thị Hằng", "Nguyễn Thị Hằng", True),
        ("Phạm Xuân Cơ / (mẹ) Nguyễn Thị Hoa", "Nguyễn Thị Hoa", True),
        ("Nguyễn Văn Chính / (mẹ) Nguyễn Thị Minh", "Nguyễn Thị Minh", True),
        ("Nguyễn Văn Đức / (mẹ) Trịnh Thị Phương", "Trịnh Thị Phương", True),
        ("(Mẹ) SẦM THỊ HOÀI", "Sầm Thị Hoài", True),
        ("(Mẹ) M_Bùi Diệu Linh", "Bùi Diệu Linh", True),
        ("(Mẹ) M-Hoàng Ngọc Anh", "Hoàng Ngọc Anh", True),
        ("(Mẹ) M - Nguyễn Thị Hường", "Nguyễn Thị Hường", True),
        ("Phạm Thị Lương", "Phạm Thị Lương", True),
        ("(Bà) Trần Thị Mai", "Trần Thị Mai", False),
        ("(Bác) Nguyễn Văn C", "Nguyễn Văn C", False),
        ("(Bố) Nguyễn Văn C", "Nguyễn Văn C", False),
        ("(Cô) Hoàng Thị Mai", "Hoàng Thị Mai", False),
    ])
    def test_clean_contact_name_and_role(self, raw_name, expected_name, expected_is_mother):
        name, is_mother = clean_contact_name_and_role(raw_name)
        assert name == expected_name
        assert is_mother is expected_is_mother

    def test_clean_contact_name_empty_with_child_fallback(self):
        name, is_mother = clean_contact_name_and_role("", child_name="Nguyễn Văn A")
        assert name == "Ph Bé Nguyễn Văn A"
        assert is_mother is False

    def test_format_message_for_mother(self):
        template = "Phòng tiêm Vắc Xin Dịch Vụ Quế Võ mời mẹ {name} đưa bé đến tiêm phòng và nhận ngay 3 ưu đãi lớn:\nBảo vệ con, an tâm cho mẹ!"
        formatted = format_message_for_contact(template, name="Nguyễn Thị Hoàn", is_mother=True)
        assert "mời mẹ Nguyễn Thị Hoàn đưa bé" in formatted
        assert "Bảo vệ con, an tâm cho mẹ!" in formatted

    def test_format_message_for_non_mother_ba(self):
        template = "Phòng tiêm Vắc Xin Dịch Vụ Quế Võ mời mẹ {name} đưa bé đến tiêm phòng và nhận ngay 3 ưu đãi lớn:\nBảo vệ con, an tâm cho mẹ!"
        formatted = format_message_for_contact(template, name="Trần Thị Mai", is_mother=False)
        assert "mời Trần Thị Mai đưa bé" in formatted
        assert "mời mẹ Trần Thị Mai" not in formatted

    def test_format_message_for_non_mother_bac(self):
        template = "Phòng tiêm Vắc Xin Dịch Vụ Quế Võ mời mẹ {name} đưa bé đến tiêm phòng và nhận ngay 3 ưu đãi lớn:\nBảo vệ con, an tâm cho mẹ!"
        formatted = format_message_for_contact(template, name="Nguyễn Văn C", is_mother=False)
        assert "mời Nguyễn Văn C đưa bé" in formatted
        assert "mời mẹ Nguyễn Văn C" not in formatted
