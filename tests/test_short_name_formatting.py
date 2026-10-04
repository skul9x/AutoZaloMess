import sys
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.utils import extract_short_name, clean_contact_name_and_role, format_message_for_contact

class TestShortNameFormatting:
    """Comprehensive test suite for Phase 01: Core Parsing & Formatting Utilities."""

    # 1. Given Name Extraction Tests
    @pytest.mark.parametrize("input_name, expected_short_name", [
        ("Nguyễn Thị Linh", "Linh"),
        ("Trần Duy Vũ", "Vũ"),
        ("Linh", "Linh"),
        ("linh", "Linh"),
        ("  Nguyễn   Thị   Linh  ", "Linh"),
        ("phụ huynh bé Nguyễn Văn An", "phụ huynh bé Nguyễn Văn An"),
        ("Phụ huynh bé Nguyễn Văn An", "phụ huynh bé Nguyễn Văn An"),
        ("PH bé Nguyễn Văn An", "phụ huynh bé Nguyễn Văn An"),
        ("ph bé nguyễn văn an", "phụ huynh bé Nguyễn Văn An"),
        ("phụ huynh", "phụ huynh"),
        ("", ""),
        ("   ", ""),
    ])
    def test_extract_short_name(self, input_name, expected_short_name):
        assert extract_short_name(input_name) == expected_short_name

    # 2. Enhanced clean_contact_name_and_role Tests
    @pytest.mark.parametrize("raw_name, child_name, expected_name, expected_is_mother, expected_role", [
        ("Nguyễn Thị Linh", "", "Nguyễn Thị Linh", True, "mẹ"),
        ("(Mẹ) Nguyễn Thị Hoàn", "", "Nguyễn Thị Hoàn", True, "mẹ"),
        ("(Mẹ) SẦM THỊ HOÀI", "", "Sầm Thị Hoài", True, "mẹ"),
        ("Nguyễn Đình Tuấn / (mẹ) Nguyễn Thị Hoàn", "", "Nguyễn Thị Hoàn", True, "mẹ"),
        ("(Bố) Nguyễn Văn Bá / (Mẹ) Nguyễn Thị Thanh", "", "Nguyễn Thị Thanh", True, "mẹ"),
        ("(Bà) Trần Thị Mai", "", "Trần Thị Mai", False, "bà"),
        ("(Bố) Nguyễn Văn Tuấn", "", "Nguyễn Văn Tuấn", False, "bố"),
        ("(Bác) Lê Văn Hùng", "", "Lê Văn Hùng", False, "bác"),
        ("(Ông) Đỗ Văn Nam", "", "Đỗ Văn Nam", False, "ông"),
        ("(Cô) Hoàng Thị Mai", "", "Hoàng Thị Mai", False, "cô"),
        ("(Chú) Vũ Văn Long", "", "Vũ Văn Long", False, "chú"),
        ("", "Nguyễn Văn An", "phụ huynh bé Nguyễn Văn An", False, "phụ huynh"),
        ("PH bé Nguyễn Văn An", "", "phụ huynh bé Nguyễn Văn An", False, "phụ huynh"),
        ("Phụ huynh bé Nguyễn Văn An", "", "phụ huynh bé Nguyễn Văn An", False, "phụ huynh"),
    ])
    def test_clean_contact_name_and_role_3_unpack(self, raw_name, child_name, expected_name, expected_is_mother, expected_role):
        name, is_mother, role = clean_contact_name_and_role(raw_name, child_name=child_name)
        assert name == expected_name
        assert is_mother is expected_is_mother
        assert role == expected_role

    def test_clean_contact_name_and_role_backward_compatible_2_unpack(self):
        # Verify legacy 2-variable unpack works seamlessly
        name, is_mother = clean_contact_name_and_role("(Bà) Trần Thị Mai")
        assert name == "Trần Thị Mai"
        assert is_mother is False

        name_mom, is_mother_mom = clean_contact_name_and_role("Nguyễn Thị Linh")
        assert name_mom == "Nguyễn Thị Linh"
        assert is_mother_mom is True

    def test_clean_contact_result_attributes_and_equality(self):
        res = clean_contact_name_and_role("(Bố) Nguyễn Văn Tuấn")
        assert res.name == "Nguyễn Văn Tuấn"
        assert res.is_mother is False
        assert res.role == "bố"
        assert res == ("Nguyễn Văn Tuấn", False, "bố")
        assert len(res) == 3
        assert tuple(res) == ("Nguyễn Văn Tuấn", False, "bố")

    # 3. Message Formatting Tests
    def test_format_message_mother(self):
        template = "mời mẹ {name}"
        formatted = format_message_for_contact(template, name="Nguyễn Thị Linh", is_mother=True, role="mẹ")
        assert formatted == "mời mẹ Linh"

    def test_format_message_non_mother_ba(self):
        template = "mời mẹ {name}"
        formatted = format_message_for_contact(template, name="Trần Thị Mai", is_mother=False, role="bà")
        assert formatted == "mời bà Mai"

    def test_format_message_non_mother_bo(self):
        template = "mời mẹ {name}"
        formatted = format_message_for_contact(template, name="Nguyễn Văn Tuấn", is_mother=False, role="bố")
        assert formatted == "mời bố Tuấn"

    def test_format_message_non_mother_bac(self):
        template = "mời mẹ {name}"
        formatted = format_message_for_contact(template, name="Lê Văn Hùng", is_mother=False, role="bác")
        assert formatted == "mời bác Hùng"

    def test_format_message_child_fallback(self):
        template = "mời mẹ {name}"
        formatted = format_message_for_contact(template, name="phụ huynh bé Nguyễn Văn An", is_mother=False, role="phụ huynh")
        assert formatted == "mời phụ huynh bé Nguyễn Văn An"

    def test_format_message_realistic_template_with_phone(self):
        template = (
            "Phòng tiêm Vắc Xin Dịch Vụ Quế Võ mời mẹ {name} đưa bé đến tiêm phòng "
            "(SĐT: {phone}) và nhận ngay 3 ưu đãi lớn:\nBảo vệ con, an tâm cho mẹ!"
        )
        formatted = format_message_for_contact(
            template,
            name="Nguyễn Thị Linh",
            phone="0987654321",
            is_mother=True,
            role="mẹ"
        )
        assert "mời mẹ Linh đưa bé" in formatted
        assert "(SĐT: 0987654321)" in formatted
        assert "an tâm cho mẹ!" in formatted
