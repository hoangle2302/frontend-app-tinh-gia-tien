"""Exact names transcribed from the screenshot; other tab field lists unknown.

'lookup' means the screenshot shows a picker button. It is an editable code/name
input plus a picker placeholder until the real master data is supplied.
"""
from dataclasses import dataclass

LEGACY_TABS = (
    'Thông tin chung', 'Thông tin Pro', 'Chi tiết',
    'Vật tư điện', 'Vật tư cơ khí', 'Vật tư tủ điện',
    'Thông tin card', 'Manual', 'Tệp đính kèm', 'Ghi chú',
)

@dataclass(frozen=True)
class Field:
    key: str
    label: str
    kind: str = 'text'
    required: bool = False  # Explicit user-defined finalization requirement

@dataclass(frozen=True)
class Section:
    label: str
    fields: tuple[Field, ...]

# Four presentation groups are a NEW MOBILE LAYOUT, not separate legacy tabs.
COMMON_SECTIONS = (
    Section('Khách hàng & hợp đồng', (
        Field('ma_khach_hang', 'Mã khách hàng', 'lookup'),
        Field('so_hop_dong', 'Số hợp đồng'),
    )),
    Section('Nguồn & xử lý', (
        Field('hang_nguon', 'Hãng nguồn', 'lookup', required=True),
        Field('ma_nguon', 'Mã nguồn', 'lookup', required=True),
        Field('cong_suat', 'Công suất', 'decimal'),
        Field('hang_bo_xu_ly', 'Hãng bộ xử lý', 'lookup'),
    )),
    Section('Khung, Alu & phụ kiện', (
        Field('loai_khung', 'Loại khung', 'lookup', required=True),
        Field('alu_theo_khung', 'Alu theo khung', 'lookup'),
        Field('alu_theo_dien_tich', 'Alu theo diện tích', 'number_lookup'),
        Field('quat_5v', 'Quạt 5v', 'lookup'),
    )),
    Section('Tủ điện & nguồn điện', (
        Field('loai_tu_dien', 'Loại tủ điện', 'lookup'),
        Field('loai_cb', 'Loại CB', 'lookup'),
        Field('tiet_dien_day', 'Tiết diện dây', 'lookup'),
        Field('nguon_dien_1pha', '1 Pha', 'checkbox'),
        Field('nguon_dien_3pha', '3 Pha', 'checkbox'),
        Field('tu_dien', 'Tủ điện', 'checkbox'),
    )),
)

HEADER_FIELDS = (
    Field('loai_man_hinh', 'Loại màn hình', 'lookup', required=True),
    Field('loai_trinh_chieu', 'Loại trình chiếu', 'lookup', required=True),
    Field('hang_module', 'Hãng module', 'lookup', required=True),
    Field('ma_module', 'Mã module', 'lookup', required=True),
    Field('so_module_w', 'Số module (W)', 'integer'),
    Field('so_module_h', 'Số module (H)', 'integer'),
    Field('so_module_du_phong', 'Số module dự phòng', 'integer'),
    Field('dien_giai', 'Diễn giải'),
)

# Additional input required to calculate mm and pixels WITHOUT guessing a SKU.
MODULE_DETAILS = (
    Field('module_rong_mm', 'Rộng 1 module (mm)', 'decimal'),
    Field('module_cao_mm', 'Cao 1 module (mm)', 'decimal'),
    Field('module_pixel_w', 'Pixel ngang của 1 module', 'integer'),
    Field('module_pixel_h', 'Pixel dọc của 1 module', 'integer'),
)

ALL_FIELDS = HEADER_FIELDS + MODULE_DETAILS + tuple(f for sec in COMMON_SECTIONS for f in sec.fields)
assert len(COMMON_SECTIONS) == 4
assert len(LEGACY_TABS) == 10
assert len({f.key for f in ALL_FIELDS}) == len(ALL_FIELDS)

# Requirements explicitly requested for completion; no other fields implied.
REQUIRED_FIELDS = tuple(field for field in ALL_FIELDS if field.required)
assert len(REQUIRED_FIELDS) == 7
