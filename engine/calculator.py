import math
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


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
    discount_percent: float = 0.0
    include_install: bool = True
    include_transport: bool = True
    install_unit_price: float = 350000
    transport_price: float = 1500000


class Calculators:
    @staticmethod
    def _safe_round_to_int(value: float, minimum: int = 1) -> int:
        return max(int(round(value)), minimum)

    @staticmethod
    def _format_currency(value: float) -> str:
        return f"{value:,.0f}".replace(",", ".")

    def _select_processor(self, pixels: int, processors: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not processors:
            raise ValueError("Chua co bo xu ly trong danh muc linh kien.")

        processors_sorted = sorted(
            processors,
            key=lambda p: (
                p.get("spec_json", {}).get("min_pixels", 0),
                p.get("spec_json", {}).get("max_pixels", 10**12),
            ),
        )

        # Prefer a processor whose supported pixel range covers the actual project size.
        for item in processors_sorted:
            spec = item.get("spec_json", {})
            min_pixels = int(spec.get("min_pixels", 0))
            max_pixels = int(spec.get("max_pixels", 10**12))
            if min_pixels <= pixels <= max_pixels:
                return item

        if pixels < 1300000:
            return processors_sorted[0]

        return processors_sorted[-1]

    def calculate(self, inp: CalculationInput) -> Dict[str, Any]:
        if inp.width_m <= 0 or inp.height_m <= 0:
            raise ValueError("Kich thuoc W va H phai lon hon 0.")

        module_spec = inp.module["spec_json"]
        module_w_m = float(module_spec["width_mm"]) / 1000.0
        module_h_m = float(module_spec["height_mm"]) / 1000.0

        n_ngang = self._safe_round_to_int(inp.width_m / module_w_m)
        n_doc = self._safe_round_to_int(inp.height_m / module_h_m)
        n_total = n_ngang * n_doc

        w_real = n_ngang * module_w_m
        h_real = n_doc * module_h_m

        i_module_max = float(module_spec["max_current_a"])
        i_max = n_total * i_module_max

        power_spec = inp.power["spec_json"]
        i_source_max = float(power_spec["max_current_a"])
        i_safe = i_source_max * 0.8
        n_power = max(math.ceil(i_max / i_safe), 1)

        res_w = n_ngang * int(module_spec["pixel_w"])
        res_h = n_doc * int(module_spec["pixel_h"])
        pixels = res_w * res_h

        card_spec = inp.card["spec_json"]
        card_capacity = int(card_spec["capacity_pixels"])
        if card_capacity <= 0:
            raise ValueError("Suc chua card thu phai lon hon 0 pixel.")
        cards_base = math.ceil(pixels / card_capacity)

        # Extra wiring-aware card count rule:
        # guarantee enough cards for practical horizontal split (about 4 modules/card).
        cards_by_layout = max(1, math.ceil(n_ngang / 4))
        n_cards = max(cards_base, cards_by_layout)

        processor = self._select_processor(pixels, inp.processors)
        area_m2 = w_real * h_real

        bom_rows: List[Dict[str, Any]] = [
            {
                "name": inp.module["name"],
                "spec": f"{module_spec['pitch']} - {module_spec['width_mm']}x{module_spec['height_mm']}mm",
                "qty": n_total,
                "unit": inp.module["unit"],
                "unit_price": float(inp.module["unit_price"]),
            },
            {
                "name": inp.power["name"],
                "spec": f"{i_source_max:.0f}A (80% safe)",
                "qty": n_power,
                "unit": inp.power["unit"],
                "unit_price": float(inp.power["unit_price"]),
            },
            {
                "name": inp.card["name"],
                "spec": f"Capacity {card_capacity:,} px",
                "qty": n_cards,
                "unit": inp.card["unit"],
                "unit_price": float(inp.card["unit_price"]),
            },
            {
                "name": processor["name"],
                "spec": f"Suggested by {pixels:,} px",
                "qty": 1,
                "unit": processor["unit"],
                "unit_price": float(processor["unit_price"]),
            },
            {
                "name": inp.frame["name"],
                "spec": "Frame/structure",
                "qty": round(area_m2, 2),
                "unit": inp.frame["unit"],
                "unit_price": float(inp.frame["unit_price"]),
            },
        ]

        if inp.include_install:
            bom_rows.append(
                {
                    "name": "Thi cong lap dat",
                    "spec": "Labor",
                    "qty": round(area_m2, 2),
                    "unit": "m2",
                    "unit_price": float(inp.install_unit_price),
                }
            )

        if inp.include_transport:
            bom_rows.append(
                {
                    "name": "Van chuyen",
                    "spec": "Transport",
                    "qty": 1,
                    "unit": "job",
                    "unit_price": float(inp.transport_price),
                }
            )

        sub_total = 0.0
        for row in bom_rows:
            row_total = float(row["qty"]) * float(row["unit_price"])
            row["line_total"] = row_total
            sub_total += row_total

        discount_value = sub_total * (inp.discount_percent / 100.0)
        final_total = max(sub_total - discount_value, 0.0)

        width_diff_pct = abs((w_real - inp.width_m) / max(inp.width_m, 1e-6)) * 100
        height_diff_pct = abs((h_real - inp.height_m) / max(inp.height_m, 1e-6)) * 100
        max_deviation_pct = max(width_diff_pct, height_diff_pct)

        return {
            "input": {
                "width_m": inp.width_m,
                "height_m": inp.height_m,
                "environment": inp.environment,
                "discount_percent": inp.discount_percent,
            },
            "summary": {
                "n_ngang": n_ngang,
                "n_doc": n_doc,
                "n_total": n_total,
                "w_real": w_real,
                "h_real": h_real,
                "res_w": res_w,
                "res_h": res_h,
                "pixels": pixels,
                "refresh_rate_hz": int(module_spec.get("refresh_rate_hz", 1920)),
                "deviation_pct": max_deviation_pct,
                "i_max": i_max,
                "i_safe": i_safe,
                "processor_name": processor["name"],
            },
            "bom": bom_rows,
            "pricing": {
                "sub_total": sub_total,
                "discount_percent": inp.discount_percent,
                "discount_value": discount_value,
                "final_total": final_total,
                "final_total_fmt": self._format_currency(final_total),
            },
        }
