"""View state helpers without Flet; easily unit tested."""
from __future__ import annotations
from dataclasses import dataclass
from form_schema import ALL_FIELDS, COMMON_SECTIONS
from content_navigation import CONTENT_GROUPS

STEPS = ("Cấu hình", "Nội dung", "Chi phí", "Rà soát")
COST_TABS = ("Vật tư điện", "Vật tư cơ khí", "Vật tư tủ điện", "Manual")


def next_step(current: int, direction: int) -> int:
    return max(0, min(len(STEPS) - 1, current + direction))


def has_data(data: object) -> bool:
    if isinstance(data, bool):
        return data
    return str(data or "").strip() not in ("", "0", "0.00")


def common_status(fields: dict) -> str:
    count = sum(has_data(fields.get(spec.key)) for group in COMMON_SECTIONS for spec in group.fields)
    return f"{count} trường đã nhập" if count else "Chưa nhập dữ liệu"


def section_status(name: str, snapshot: dict) -> str:
    if name == "Thông tin chung":
        return common_status(snapshot.get("fields", {}))
    if name in COST_TABS:
        count = len(snapshot.get("lines", {}).get(name, []))
        return f"{count} dòng chi phí" if count else "Chưa có dòng chi phí"
    if name == "Ghi chú":
        return "Đã nhập" if has_data(snapshot.get("note")) else "Chưa có ghi chú"
    if name == "Tệp đính kèm":
        count = len(snapshot.get("attachment_names", []))
        return f"{count} tệp đã chọn" if count else "Chưa chọn tệp"
    return "Chưa có biểu mẫu thực tế"


def quote_label(snapshot: dict) -> str:
    fields = snapshot.get("fields", {})
    return fields.get("ma_khach_hang") or fields.get("ma_module") or "Chưa đặt tên báo giá"


def validate_draft(snapshot: dict) -> None:
    """Only reject malformed numbers; do not require a complete BOM to save a draft."""
    from quote_engine import number, technical_result
    values = snapshot.get("fields", {})
    technical_result(values)
    for key, label in (("cong_suat", "Công suất"), ("alu_theo_dien_tich", "Alu theo diện tích")):
        number(values.get(key), label)
    number(snapshot.get("total_quantity"), "Tổng số lượng")
    margin = number(snapshot.get("margin"), "Biên lợi nhuận (%)")
    if margin is not None and margin >= 100:
        raise ValueError("Biên lợi nhuận gộp cần nhỏ hơn 100%.")
    if snapshot.get("manual_enabled"):
        number(snapshot.get("manual_sell"), "Giá bán thủ công", positive=True)
    for cat, entries in snapshot.get("lines", {}).items():
        for row in entries:
            if not any(str(row.get(k, "")).strip() for k in ("name", "qty", "price")):
                continue
            # Empty partial rows are allowed in drafts. Numeric values, when
            # provided, still need to be valid. The pricing engine will mark
            # incomplete rows and withhold the calculated total.
            number(row.get("qty"), f"Số lượng / {cat}", positive=True)
            number(row.get("price"), f"Đơn giá / {cat}")
