"""FormDataMixin: isolated UI responsibilities; inherited by the screen coordinator.

Preserves original control construction and callbacks for migration safety.
"""
import math
from typing import Any, Callable, Dict, List
import flet as ft


class FormDataMixin:
    def add_additional(self, name: str, qty, unit_price):
        self._add_additional_item()
        name_field, qty_field, price_field, _ = self.additional_items[-1]
        name_field.value = name
        qty_field.value = str(qty)
        price_field.value = str(int(unit_price))
        self.on_change(None)

    def additional_qty_by_name(self, name: str) -> float:
        total = 0.0
        for name_field, qty_field, _, _ in self.additional_items:
            if (name_field.value or "").strip() == name:
                try:
                    total += float(str(qty_field.value).replace(",", "."))
                except ValueError:
                    pass
        return total

    def _add_additional_item(self, e=None):
        name = ft.TextField(label="Tên vật tư", expand=True, **self._field_style())
        quantity = ft.TextField(label="SL", value="1", width=58, keyboard_type=ft.KeyboardType.NUMBER, **self._field_style())
        price = ft.TextField(label="Đơn giá", value="0", width=100, keyboard_type=ft.KeyboardType.NUMBER, **self._field_style())
        row = ft.Row(spacing=5, controls=[name, quantity, price])
        self.additional_items.append((name, quantity, price, row))
        row.controls.append(
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                tooltip="Xóa hạng mục",
                on_click=lambda event, item=(name, quantity, price, row): self._remove_additional_item(item),
            )
        )
        self.additional_rows.controls.append(row)

    def _remove_additional_item(self, item):
        self.additional_items.remove(item)
        self.additional_rows.controls.remove(item[3])
        self.on_change(None)

    def set_values(self, values: Dict):
        for control, key in (
            (self.customer_name, "customer_name"),
            (self.project_name, "project_name"),
            (self.customer_phone, "customer_phone"),
            (self.screen_quantity, "screen_quantity"),
            (self.profit_input, "profit_percent"),
            (self.vat_input, "vat_percent"),
        ):
            if key in values:
                control.value = str(values[key])

        if "config_mode" in values:
            self._set_mode(values["config_mode"])

        if "module_code" in values:
            self.module_code_dropdown.value = values["module_code"]
            self.pitch_dropdown.value = values["module_code"]
        # New quotes persist the ERP key; older quotes may only store environment.
        screen_type_code = values.get("screen_type_code")
        if not screen_type_code and values.get("environment"):
            screen_type_code = self.screen_type_code_for_environment(values["environment"])
        if screen_type_code:
            self.select_screen_type(str(screen_type_code))
        if "power_code" in values:
            self.power_dropdown.value = values["power_code"]
        if "card_code" in values:
            self.card_dropdown.value = values["card_code"]
        if "frame_code" in values:
            self.frame_dropdown.value = values["frame_code"]

        # Restore manual fields
        for attr, key in [
            (self.m_sl_module, "m_sl_module"),
            (self.m_sl_nguon, "m_sl_nguon"),
            (self.m_sl_bxl, "m_sl_bxl"),
            (self.m_sl_card, "m_sl_card"),
            (self.m_sl_cbn1, "m_sl_cbn1"),
            (self.m_sl_cbn2, "m_sl_cbn2"),
            (self.m_sl_cbn3, "m_sl_cbn3"),
            (self.m_sl_cbn4, "m_sl_cbn4"),
            (self.m_dien_tich, "m_dien_tich"),
            (self.module_brand_dropdown, "m_hang_module"),
            (self.power_brand_dropdown, "m_hang_nguon"),
            (self.processor_brand_dropdown, "m_hang_bxl"),
            (self.m_ma_bxl, "m_ma_bxl"),
            (self.m_ma_card, "m_ma_card"),
            (self.m_quy_cach, "m_quy_cach"),
            (self.m_ma_cbn1, "m_ma_cbn1"),
            (self.m_ma_cbn2, "m_ma_cbn2"),
            (self.m_ma_cbn3, "m_ma_cbn3"),
            (self.m_ma_cbn4, "m_ma_cbn4"),
            (self.m_ma_alu, "m_ma_alu"),
            (self.m_ma_alu_dt, "m_ma_alu_dt"),
            (self.m_ma_quat5v, "m_ma_quat5v"),
            (self.m_loai_tu_dien, "m_loai_tu_dien"),
            (self.cb_dropdown, "m_loai_cb"),
            (self.m_tiet_dien, "m_tiet_dien"),
        ]:
            if key in values and hasattr(attr, "value"):
                attr.value = str(values[key])

        if "m_check_tu_dien" in values:
            self.m_check_tu_dien.value = bool(values["m_check_tu_dien"])
        if "m_check_1pha" in values and values["m_check_1pha"]:
            self._set_power_phase("1pha")
        elif "m_check_3pha" in values and values["m_check_3pha"]:
            self._set_power_phase("3pha")

        # Kích thước W / H (m) -> suy ra số module
        mod = self._get_current_module()
        w_mm = float(mod.get("spec_json", {}).get("width_mm", 320))
        h_mm = float(mod.get("spec_json", {}).get("height_mm", 160))
        if "width_m" in values and w_mm > 0:
            self.num_modules_w = max(1, round(float(values["width_m"]) * 1000 / w_mm))
            self.txt_modules_w.value = str(self.num_modules_w)
        if "height_m" in values and h_mm > 0:
            self.num_modules_h = max(1, round(float(values["height_m"]) * 1000 / h_mm))
            self.txt_modules_h.value = str(self.num_modules_h)

        self._sync_calc_display()

    def get_values(self) -> Dict:
        mod = self._get_current_module()
        code = mod.get("code") or self.module_code_dropdown.value
        screen_type_code = self.erp_screen_types_dropdown.value
        selected_type = self._find_screen_type(screen_type_code)
        return {
            "config_mode": self.config_mode,
            "screen_type_code": screen_type_code,
            "screen_type_name": selected_type.name if selected_type else None,
            "environment": self.environment.value if selected_type else None,
            "module_code": code,
            "display_mode": self.display_mode_val,
            "card_code": self.m_ma_card.value or self.card_dropdown.value,
            "power_code": self.power_dropdown.value,
            "frame_code": self.frame_dropdown.value,
            "width_m": self.width_input.value,
            "height_m": self.height_input.value,
            "discount_percent": self.discount_slider.value,
            "include_install": bool(self.include_install.value),
            "include_transport": bool(self.include_transport.value),
            "install_price": self.install_price_input.value if self.include_install.value else "0",
            "transport_price": self.transport_price_input.value if self.include_transport.value else "0",
            "customer_name": (self.customer_name.value or "").strip(),
            "project_name": (self.project_name.value or "").strip(),
            "customer_phone": (self.customer_phone.value or "").strip(),
            "screen_quantity": self.screen_quantity.value or "1",
            "profit_percent": self.profit_input.value or "20",
            "vat_percent": self.vat_input.value or "8",
            "reserve_percent": self.reserve_input.value or "3",
            "m_hang_module": self.module_brand_dropdown.value,
            "m_ma_module": self.module_code_dropdown.value,
            "m_sl_module": self.m_sl_module.value,
            "m_hang_nguon": self.power_brand_dropdown.value,
            "m_ma_nguon": self.power_dropdown.value,
            "m_sl_nguon": self.m_sl_nguon.value,
            "m_hang_bxl": self.processor_brand_dropdown.value,
            "m_ma_bxl": self.m_ma_bxl.value,
            "m_sl_bxl": self.m_sl_bxl.value,
            "m_ma_card": self.m_ma_card.value,
            "m_quy_cach": self.m_quy_cach.value,
            "m_sl_card": self.m_sl_card.value,
            "m_ma_cbn1": self.m_ma_cbn1.value,
            "m_sl_cbn1": self.m_sl_cbn1.value,
            "m_ma_cbn2": self.m_ma_cbn2.value,
            "m_sl_cbn2": self.m_sl_cbn2.value,
            "m_ma_cbn3": self.m_ma_cbn3.value,
            "m_sl_cbn3": self.m_sl_cbn3.value,
            "m_ma_cbn4": self.m_ma_cbn4.value,
            "m_sl_cbn4": self.m_sl_cbn4.value,
            "m_ma_alu": self.m_ma_alu.value,
            "m_dien_tich": self.m_dien_tich.value,
            "m_ma_alu_dt": self.m_ma_alu_dt.value,
            "m_ma_quat5v": self.m_ma_quat5v.value,
            "m_loai_tu_dien": self.m_loai_tu_dien.value,
            "m_loai_cb": self.cb_dropdown.value,
            "m_tiet_dien": self.m_tiet_dien.value,
            "m_check_tu_dien": bool(self.m_check_tu_dien.value),
            "m_check_1pha": bool(self.m_check_1pha.value),
            "m_check_3pha": bool(self.m_check_3pha.value),
            "additional_items": [
                {
                    "name": name.value.strip(),
                    "qty": quantity.value,
                    "unit_price": price.value,
                    "unit": "item",
                }
                for name, quantity, price, _ in self.additional_items
                if name.value and name.value.strip()
            ],
        }
