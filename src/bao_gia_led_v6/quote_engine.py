"""Calculations for the screenshot-faithful LED quote prototype.

All dimensions, resolutions, material quantities and prices are user-supplied.
No product specifications, supplier prices, BOM auto-sizing or VAT rules are
assumed. The legacy 'Tổng số lượng' field has no established formula and is
NOT used as a screen multiplier.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional

D = Decimal


def number(raw: object, label: str, *, integer=False, positive=False, optional=True) -> Optional[Decimal]:
    value = '' if raw is None else str(raw).strip().replace(' ', '')
    if not value:
        if optional:
            return None
        raise ValueError(f'{label}: cần nhập giá trị.')
    # Accept decimal comma for a decimal fraction. Avoid guessing thousands format.
    if value.count('.') + value.count(',') > 1:
        raise ValueError(f'{label}: không dùng dấu phân tách hàng nghìn.')
    try:
        result = D(value.replace(',', '.'))
    except InvalidOperation as exc:
        raise ValueError(f'{label}: giá trị số không hợp lệ.') from exc
    if not result.is_finite():
        raise ValueError(f'{label}: giá trị không hữu hạn.')
    if result < 0 or (positive and result == 0):
        raise ValueError(f'{label}: phải là số {"lớn hơn 0" if positive else "không âm"}.')
    if integer and result != result.to_integral_value():
        raise ValueError(f'{label}: phải là số nguyên.')
    return result


def fmt_number(value: object, places=2) -> str:
    if value is None:
        return '—'
    txt = f'{D(value):,.{places}f}'
    return txt.replace(',', '_').replace('.', ',').replace('_', '.')


def fmt_int(value: object) -> str:
    if value is None:
        return '—'
    return f'{int(value):,}'.replace(',', '.')


def fmt_money(value: object) -> str:
    if value is None:
        return 'Chưa đủ dữ liệu'
    rounded = D(value).quantize(D('1'), rounding=ROUND_HALF_UP)
    return f'{rounded:,.0f}'.replace(',', '.') + ' đ'


@dataclass(frozen=True)
class TechnicalResult:
    module_count: Optional[int]
    screen_width_mm: Optional[Decimal]
    screen_height_mm: Optional[Decimal]
    area_m2: Optional[Decimal]
    resolution_w: Optional[int]
    resolution_h: Optional[int]
    total_pixels: Optional[int]


def technical_result(data: dict[str, object]) -> TechnicalResult:
    w = number(data.get('so_module_w'), 'Số module (W)', integer=True, positive=True)
    h = number(data.get('so_module_h'), 'Số module (H)', integer=True, positive=True)
    spare = number(data.get('so_module_du_phong'), 'Số module dự phòng', integer=True)
    mm_w = number(data.get('module_rong_mm'), 'Rộng module (mm)', positive=True)
    mm_h = number(data.get('module_cao_mm'), 'Cao module (mm)', positive=True)
    px_w = number(data.get('module_pixel_w'), 'Pixel module (W)', integer=True, positive=True)
    px_h = number(data.get('module_pixel_h'), 'Pixel module (H)', integer=True, positive=True)
    available = (w is not None and h is not None)
    disp_w = w * mm_w if available and mm_w is not None else None
    disp_h = h * mm_h if available and mm_h is not None else None
    res_w = int(w * px_w) if available and px_w is not None else None
    res_h = int(h * px_h) if available and px_h is not None else None
    # Spare is treated as extra MODULES for one display, consistent with top labels.
    total_mods = int(w * h + (spare or D(0))) if available else None
    return TechnicalResult(
        module_count=total_mods,
        screen_width_mm=disp_w,
        screen_height_mm=disp_h,
        area_m2=(disp_w * disp_h / D(1_000_000) if disp_w is not None and disp_h is not None else None),
        resolution_w=res_w,
        resolution_h=res_h,
        total_pixels=(res_w * res_h if res_w is not None and res_h is not None else None),
    )


@dataclass(frozen=True)
class CostLine:
    category: str
    name: str
    quantity: object
    unit_price: object


@dataclass(frozen=True)
class PriceResult:
    cost: Optional[Decimal]
    selling: Optional[Decimal]
    cost_per_m2: Optional[Decimal]
    selling_per_m2: Optional[Decimal]
    gross_margin_percent: Optional[Decimal]
    issues: tuple[str, ...]
    completed_lines: int


def price_result(
    lines: list[CostLine], area_m2: Optional[Decimal], margin: object,
    manual_sell: object = None,
) -> PriceResult:
    total = D(0)
    issues: list[str] = []
    completed = 0
    for idx, line in enumerate(lines, 1):
        name = line.name.strip()
        qty_str = str(line.quantity or '').strip()
        cost_str = str(line.unit_price or '').strip()
        if not any((name, qty_str, cost_str)):
            continue
        if not name:
            issues.append(f'Dòng {idx}: thiếu tên vật tư/chi phí')
            continue
        try:
            qty = number(line.quantity, f'Số lượng {name}', positive=True, optional=False)
            unit = number(line.unit_price, f'Đơn giá {name}', optional=False)
        except ValueError as exc:
            issues.append(str(exc))
            continue
        total += qty * unit
        completed += 1
    cost = total if completed and not issues else None
    margin_percent = number(margin, 'Biên độ lợi nhuận (%)')
    manual_amount = number(manual_sell, 'Giá bán thủ công', positive=True)
    if margin_percent is not None and margin_percent >= 100:
        raise ValueError('Biên độ lợi nhuận gộp phải nhỏ hơn 100%.')
    sell = None
    if cost is not None:
        if manual_amount is not None:
            sell = manual_amount
        elif margin_percent is not None:
            sell = (cost / (D(1) - margin_percent / D(100))).quantize(D('1'), rounding=ROUND_HALF_UP)
    gross = ((sell - cost) / sell * D(100)) if sell is not None and cost is not None and sell > 0 else None
    return PriceResult(
        cost=cost, selling=sell,
        cost_per_m2=(cost / area_m2 if cost is not None and area_m2 is not None and area_m2 > 0 else None),
        selling_per_m2=(sell / area_m2 if sell is not None and area_m2 is not None and area_m2 > 0 else None),
        gross_margin_percent=gross,
        issues=tuple(issues),
        completed_lines=completed,
    )
