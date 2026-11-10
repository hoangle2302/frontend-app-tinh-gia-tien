"""Mobile content information architecture, independent of Flet.

The 10 item names come from the user's desktop screenshot. Their grouping and
short descriptions are NEW UX conventions, not database facts.
"""
from __future__ import annotations
from dataclasses import dataclass
import unicodedata
from form_schema import LEGACY_TABS

@dataclass(frozen=True)
class ContentGroup:
    label: str
    items: tuple[str, ...]

@dataclass(frozen=True)
class ContentMeta:
    group: str
    description: str

CONTENT_GROUPS = (
    ContentGroup('Thông tin', ('Thông tin chung', 'Thông tin Pro', 'Chi tiết', 'Thông tin card')),
    ContentGroup('Vật tư', ('Vật tư điện', 'Vật tư cơ khí', 'Vật tư tủ điện')),
    ContentGroup('Bổ sung', ('Manual', 'Tệp đính kèm', 'Ghi chú')),
)
CONTENT_META = {
    'Thông tin chung': ContentMeta('Thông tin', 'Khách hàng, nguồn, khung và hệ thống điện'),
    'Thông tin Pro': ContentMeta('Thông tin', 'Chưa có chi tiết biểu mẫu từ phần mềm gốc'),
    'Chi tiết': ContentMeta('Thông tin', 'Chưa có chi tiết biểu mẫu từ phần mềm gốc'),
    'Thông tin card': ContentMeta('Thông tin', 'Chưa có chi tiết biểu mẫu từ phần mềm gốc'),
    'Vật tư điện': ContentMeta('Vật tư', 'Các dòng chi phí vật tư điện đã khai báo'),
    'Vật tư cơ khí': ContentMeta('Vật tư', 'Các dòng chi phí vật tư cơ khí đã khai báo'),
    'Vật tư tủ điện': ContentMeta('Vật tư', 'Các dòng chi phí vật tư tủ điện đã khai báo'),
    'Manual': ContentMeta('Bổ sung', 'Nhập các dòng chi phí thủ công'),
    'Tệp đính kèm': ContentMeta('Bổ sung', 'Chọn tệp liên quan đến bản nháp'),
    'Ghi chú': ContentMeta('Bổ sung', 'Lưu ý và diễn giải cho chứng từ'),
}


def ordered_content() -> tuple[str, ...]:
    """Logical step order for sequential next/previous navigation."""
    return tuple(name for group in CONTENT_GROUPS for name in group.items)


def fold(text: str) -> str:
    """Accent-insensitive, case-insensitive filtering for Vietnamese."""
    value = unicodedata.normalize('NFD', text.casefold().replace('đ', 'd'))
    return ''.join(c for c in value if unicodedata.category(c) != 'Mn')


def search_content(query: str) -> tuple[str, ...]:
    term = fold(query.strip())
    return tuple(name for name in ordered_content()
                 if term in fold(name) or term in fold(CONTENT_META[name].description))


def adjacent_content(name: str) -> tuple[str | None, str | None]:
    options = ordered_content()
    index = options.index(name)
    return (options[index - 1] if index > 0 else None,
            options[index + 1] if index < len(options) - 1 else None)


assert len(ordered_content()) == len(LEGACY_TABS) == 10
assert set(ordered_content()) == set(LEGACY_TABS) == set(CONTENT_META)
