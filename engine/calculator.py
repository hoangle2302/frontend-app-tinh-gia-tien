"""Bộ tính BOM và giá báo thuần, không phụ thuộc giao diện hoặc database."""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List

from engine.config import (
    DEFAULT_DISCOUNT_PERCENT,
    DEFAULT_PROFIT_PERCENT,
    DEFAULT_RESERVE_PERCENT,
    DEFAULT_VAT_PERCENT,
    MEDIUM_PROCESSOR_MAX_PIXELS,
    PIXELS_PER_MODULE,
    POWER_SAFE_LOAD_RATIO,
    POWER_SUPPLY_WATTS,
    RECEIVING_CARD_CAPACITY_PIXELS,
    SMALL_PROCESSOR_MAX_PIXELS,
    STANDARD_MODULE_HEIGHT_M,
    STANDARD_MODULE_WIDTH_M,
)


@dataclass
class CalculationInput:
    width_m: float
    height_m: float
    environment: str
    module: Dict[str, Any]
    power: Dict[str, Any]
    card: Dict[str, Any]
    frame: Dict[str, Any]
    processors: List[Dict[str, Any]]
    discount_percent: float = DEFAULT_DISCOUNT_PERCENT
    include_install: bool = True
    include_transport: bool = True
    install_unit_price: float = 350000
    transport_price: float = 1500000
    profit_percent: float = DEFAULT_PROFIT_PERCENT
    vat_percent: float = DEFAULT_VAT_PERCENT
    reserve_percent: float = DEFAULT_RESERVE_PERCENT
    screen_quantity: int = 1
    additional_items: List[Dict[str, Any]] = field(default_factory=list)


class Calculators:
    """Tính thông số màn hình, BOM và các lớp giá báo khách."""

    @staticmethod
    def _format_currency(value: float) -> str:
        return f"{value:,.0f}".replace(",", ".")

    @staticmethod
    def _positive(value: Any, label: str) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} phải là số hợp lệ.") from exc
        if number < 0:
            raise ValueError(f"{label} không được nhỏ hơn 0.")
        return number

    @staticmethod
    def _round_count(value: float) -> int:
        return max(int(math.floor(value + 0.5)), 1)

    @staticmethod
    def _select_processor(pixels: int, processors: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not processors:
            raise ValueError("Chưa có bộ xử lý trong danh mục linh kiện.")
        for processor in sorted(
            processors,
            key=lambda item: item.get("spec_json", {}).get("min_pixels", 0),
        ):
            spec = processor.get("spec_json", {})
            min_pixels = int(spec.get("min_pixels", 0))
            max_pixels = int(spec.get("max_pixels", 10**12))
            if min_pixels <= pixels <= max_pixels:
                return processor
        return (
            processors[0]
            if pixels < SMALL_PROCESSOR_MAX_PIXELS
            else processors[-1]
        )

    @staticmethod
    def _module_power_watts(module_spec: Dict[str, Any]) -> float:
        explicit_power = module_spec.get("power_w")
        if explicit_power is not None:
            return max(float(explicit_power), 0.01)
        voltage = float(module_spec.get("voltage", 5))
        current = float(module_spec.get("max_current_a", 0))
        return max(voltage * current, 0.01)

    @staticmethod
    def _validate_percent(value: float, label: str) -> None:
        if not 0 <= value <= 100:
            raise ValueError(f"{label} phải nằm trong khoảng 0% đến 100%.")

    def calculate(self, inp: CalculationInput) -> Dict[str, Any]:
        width_m = self._positive(inp.width_m, "Chiều rộng W")
        height_m = self._positive(inp.height_m, "Chiều cao H")
        if width_m == 0 or height_m == 0:
            raise ValueError("Chiều rộng W và chiều cao H phải lớn hơn 0.")
        if inp.environment not in {"indoor", "outdoor"}:
            raise ValueError("Môi trường phải là indoor hoặc outdoor.")

        quantity = int(inp.screen_quantity)
        if quantity < 1:
            raise ValueError("Số lượng màn hình phải lớn hơn 0.")

        profit = self._positive(inp.profit_percent, "Lợi nhuận")
        vat = self._positive(inp.vat_percent, "VAT")
        discount = self._positive(inp.discount_percent, "Chiết khấu")
        reserve = self._positive(inp.reserve_percent, "Module dự phòng")
        for value, label in (
            (profit, "Lợi nhuận"),
            (vat, "VAT"),
            (discount, "Chiết khấu"),
            (reserve, "Module dự phòng"),
        ):
            self._validate_percent(value, label)

        module_spec = inp.module.get("spec_json", {})
        module_width = float(module_spec.get("width_mm", 320)) / 1000
        module_height = float(module_spec.get("height_mm", 160)) / 1000
        cols = self._round_count(width_m / module_width)
        rows = self._round_count(height_m / module_height)
        base_modules = cols * rows
        reserve_modules = math.ceil(base_modules * reserve / 100)
        total_modules = base_modules + reserve_modules

        real_width = cols * module_width
        real_height = rows * module_height
        pitch = str(module_spec.get("pitch", ""))
        pixel_width, pixel_height = PIXELS_PER_MODULE.get(
            pitch,
            (
                int(module_spec.get("pixel_w", 0)),
                int(module_spec.get("pixel_h", 0)),
            ),
        )
        if pixel_width <= 0 or pixel_height <= 0:
            raise ValueError("Module chưa có thông tin pixel/module hợp lệ.")
        resolution_width = cols * pixel_width
        resolution_height = rows * pixel_height
        total_pixels = resolution_width * resolution_height

        power_watts = self._module_power_watts(module_spec)
        modules_per_power = max(
            int((POWER_SUPPLY_WATTS * POWER_SAFE_LOAD_RATIO) // power_watts),
            1,
        )
        power_count = math.ceil(total_modules / modules_per_power)
        receiving_cards = math.ceil(total_pixels / RECEIVING_CARD_CAPACITY_PIXELS)
        processor = self._select_processor(total_pixels, inp.processors)
        area_m2 = real_width * real_height

        bom_rows: List[Dict[str, Any]] = [
            self._bom_row(
                inp.module["name"],
                f"{pitch} - {module_spec.get('width_mm', 320)}x{module_spec.get('height_mm', 160)}mm",
                total_modules,
                inp.module["unit"],
                inp.module["unit_price"],
            ),
            self._bom_row(
                inp.power["name"],
                f"{power_watts:.0f}W/module, tải an toàn 80%",
                power_count,
                inp.power["unit"],
                inp.power["unit_price"],
            ),
            self._bom_row(
                inp.card["name"],
                f"Capacity {RECEIVING_CARD_CAPACITY_PIXELS:,} px",
                receiving_cards,
                inp.card["unit"],
                inp.card["unit_price"],
            ),
            self._bom_row(
                processor["name"],
                f"Đề xuất cho {total_pixels:,} px",
                1,
                processor["unit"],
                processor["unit_price"],
            ),
            self._bom_row(
                inp.frame["name"],
                "Frame/structure",
                round(area_m2, 2),
                inp.frame["unit"],
                inp.frame["unit_price"],
            ),
        ]
        if inp.include_install:
            bom_rows.append(
                self._bom_row("Thi công lắp đặt", "Labor", round(area_m2, 2), "m2", inp.install_unit_price)
            )
        if inp.include_transport:
            bom_rows.append(
                self._bom_row("Vận chuyển", "Transport", 1, "job", inp.transport_price)
            )
        for item in inp.additional_items:
            bom_rows.append(
                self._bom_row(
                    item.get("name", "Hạng mục bổ sung"),
                    item.get("spec", "Additional"),
                    item.get("qty", 0),
                    item.get("unit", "item"),
                    item.get("unit_price", 0),
                )
            )

        cost_per_screen = sum(row["line_total"] for row in bom_rows)
        cost_total = cost_per_screen * quantity
        profit_value = cost_total * profit / 100
        before_discount = cost_total + profit_value
        discount_value = before_discount * discount / 100
        transport = 0 if inp.include_transport else self._positive(inp.transport_price, "Vận chuyển")
        taxable_total = max(before_discount - discount_value + transport, 0)
        vat_value = taxable_total * vat / 100
        final_total = taxable_total + vat_value

        width_deviation = abs(real_width - width_m) / width_m * 100
        height_deviation = abs(real_height - height_m) / height_m * 100
        deviation = max(width_deviation, height_deviation)

        return {
            "input": {
                "width_m": width_m,
                "height_m": height_m,
                "environment": inp.environment,
                "screen_quantity": quantity,
                "profit_percent": profit,
                "vat_percent": vat,
                "discount_percent": discount,
                "reserve_percent": reserve,
            },
            "summary": {
                "n_ngang": cols,
                "n_doc": rows,
                "n_base": base_modules,
                "n_reserve": reserve_modules,
                "n_total": total_modules,
                "w_real": real_width,
                "h_real": real_height,
                "area_m2": area_m2,
                "res_w": resolution_width,
                "res_h": resolution_height,
                "pixels": total_pixels,
                "refresh_rate_hz": int(module_spec.get("refresh_rate_hz", 1920)),
                "power_count": power_count,
                "receiving_card_count": receiving_cards,
                "power_kw": total_modules * power_watts / 1000,
                "processor_name": processor["name"],
                "deviation_pct": deviation,
            },
            "bom": bom_rows,
            "pricing": {
                "cost_per_screen": cost_per_screen,
                "cost_total": cost_total,
                "sub_total": cost_total,
                "profit_value": profit_value,
                "discount_percent": discount,
                "discount_value": discount_value,
                "transport_value": transport,
                "vat_percent": vat,
                "vat_value": vat_value,
                "before_vat": taxable_total,
                "final_total": final_total,
                "unit_price_m2_before_vat": taxable_total / area_m2 if area_m2 else 0,
                "final_total_fmt": self._format_currency(final_total),
            },
        }

    @staticmethod
    def _bom_row(name: str, spec: str, qty: Any, unit: str, unit_price: Any) -> Dict[str, Any]:
        quantity = float(qty)
        price = float(unit_price)
        return {
            "name": name,
            "spec": spec,
            "qty": quantity,
            "unit": unit,
            "unit_price": price,
            "line_total": quantity * price,
        }
