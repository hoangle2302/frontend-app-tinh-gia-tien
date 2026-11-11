"""InventoryProductActionsMixin: isolated UI responsibilities; inherited by the screen coordinator.

Preserves original control construction and callbacks for migration safety.
"""
import copy
import json
import sqlite3
import unicodedata
from typing import Any, Callable, Dict, List, Optional
import flet as ft
from database.db_manager import DBManager
from engine.calculator import CalculationInput, Calculators
from engine.exporter import QuoteExporter
from ui.components.input_panel import InputPanel
from ui.components.preview_panel import PreviewPanel
from ui.views.profile_view import ProfileView


from ui.theme.tokens import UIColors

class InventoryProductActionsMixin:
    @staticmethod
    def _product_environment_dropdown(default: str):
        return ft.Dropdown(
            label="Môi trường sử dụng",
            value=default if default in {"indoor", "outdoor", "both"} else "both",
            options=[
                ft.dropdown.Option(key="indoor", text="Trong nhà"),
                ft.dropdown.Option(key="outdoor", text="Ngoài trời"),
                ft.dropdown.Option(key="both", text="Cả hai"),
            ],
            **InputPanel._dropdown_style(),
        )

    @staticmethod
    def _product_specs_field(value=None):
        return ft.TextField(
            label="Thông số kỹ thuật JSON",
            hint_text='Module: cần pitch, width_mm, height_mm, pixel_w, pixel_h',
            value=json.dumps(value or {}, ensure_ascii=False),
            multiline=True,
            min_lines=3,
            max_lines=6,
            **InputPanel._field_style(),
        )

    @staticmethod
    def _parse_product_specs(raw, category: str) -> dict:
        try:
            technical = json.loads(raw or "{}")
        except (ValueError, TypeError) as exc:
            raise ValueError("Thông số kỹ thuật phải là JSON hợp lệ") from exc
        if not isinstance(technical, dict):
            raise ValueError("Thông số kỹ thuật phải là một object JSON")
        if category == "module":
            for key in ("width_mm", "height_mm", "pixel_w", "pixel_h"):
                try:
                    if float(technical[key]) <= 0:
                        raise ValueError
                except (ValueError, KeyError, TypeError):
                    raise ValueError(f"Module cần giá trị dương cho '{key}'") from None
        return technical

    def _open_edit_product(self, product: Dict[str, Any]):
        cat_group, cat_ui = self._build_category_selector(default_value=product["category"])
        code = ft.TextField(label="Mã vật tư", value=product["code"], disabled=True, **InputPanel._field_style())
        name = ft.TextField(label="Tên vật tư", value=product["name"], **InputPanel._field_style())
        price = ft.TextField(label="Đơn giá (VNĐ)", value=str(int(product["unit_price"])), keyboard_type=ft.KeyboardType.NUMBER, **InputPanel._field_style())
        unit = ft.TextField(label="Đơn vị tính", value=product.get("unit", "pcs"), **InputPanel._field_style())
        supplier = ft.TextField(label="Nhà cung cấp", value=product.get("supplier", ""), **InputPanel._field_style())
        environment = self._product_environment_dropdown(product.get("environment", "both"))
        specifications = self._product_specs_field(product.get("spec_json", {}))

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.EDIT_NOTE, color=UIColors.PRIMARY),
                    ft.Text("Chỉnh sửa vật tư", weight=ft.FontWeight.BOLD),
                ],
            ),
            content=ft.Column(
                [cat_ui, code, name, price, unit, supplier, environment, specifications],
                tight=True,
                spacing=10,
                width=340,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Lưu thay đổi",
                    style=InputPanel._primary_button_style(),
                    on_click=lambda e: self._save_edit_product(
                        dialog, product["code"], cat_group, name, price, unit, supplier, environment, specifications
                    ),
                ),
            ],
        )
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _save_edit_product(self, dialog, code, category, name, price, unit, supplier, environment, specifications):
        try:
            technical = self._parse_product_specs(specifications.value, category.value)
            self.db.update_product(code, {
                "name": name.value.strip(),
                "category": category.value,
                "unit": unit.value.strip() or "pcs",
                "unit_price": float(price.value.replace(",", ".")),
                "supplier": supplier.value.strip(),
                "environment": environment.value,
                "spec_json": technical,
            })
            self._close_dialog(dialog)
            self._refresh_options()
            self._refresh_inventory()
            self.message.value = f"Đã cập nhật thông tin vật tư {code}."
            self.message.color = ft.Colors.GREEN_700
            self.recalculate()
        except (ValueError, KeyError, sqlite3.IntegrityError) as exc:
            self.message.value = f"Không thể cập nhật vật tư: {exc}"
            self.message.color = ft.Colors.RED_700
            self.page.update()

    def _update_price(self, code: str, field: ft.TextField):
        try:
            self.db.update_product_price(code, float(field.value.replace(",", ".")))
            self._refresh_options()
            self.message.value = "Đã cập nhật đơn giá."
            self.message.color = ft.Colors.GREEN_700
        except ValueError:
            self.message.value = "Đơn giá không hợp lệ."
            self.message.color = ft.Colors.RED_700
        self._refresh_inventory()
        self.recalculate()

    def _delete_product(self, code: str):
        self.db.delete_product(code)
        self._refresh_options()
        self._refresh_inventory()
        self.message.value = "Đã xóa vật tư khỏi danh mục."
        self.message.color = ft.Colors.GREEN_700
        self.page.update()

    def _open_add_product(self, e):
        cat_group, cat_ui = self._build_category_selector(default_value="module")
        code = ft.TextField(label="Mã vật tư (duy nhất)", **InputPanel._field_style())
        name = ft.TextField(label="Tên vật tư", **InputPanel._field_style())
        price = ft.TextField(label="Đơn giá (VNĐ)", value="0", keyboard_type=ft.KeyboardType.NUMBER, **InputPanel._field_style())
        unit = ft.TextField(label="Đơn vị tính", value="pcs", **InputPanel._field_style())
        supplier = ft.TextField(label="Nhà cung cấp", **InputPanel._field_style())
        environment = self._product_environment_dropdown("both")
        specifications = self._product_specs_field()
        err_msg = ft.Text("", color=ft.Colors.RED_700, size=12, visible=False)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.ADD_BOX_OUTLINED, color=UIColors.PRIMARY),
                    ft.Text("Thêm vật tư mới", weight=ft.FontWeight.BOLD),
                ],
            ),
            content=ft.Column(
                [cat_ui, code, name, price, unit, supplier, environment, specifications, err_msg],
                tight=True,
                spacing=10,
                width=340,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Thêm vật tư",
                    style=InputPanel._primary_button_style(),
                    on_click=lambda e: self._create_product(
                        dialog, cat_group, code, name, price, unit, supplier, environment, specifications, err_msg
                    ),
                ),
            ],
        )
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _close_dialog(self, dialog):
        if hasattr(self.page, "pop_dialog"):
            self.page.pop_dialog()
        else:
            dialog.open = False
            self.page.update()

    def _create_product(self, dialog, category, code, name, price, unit, supplier, environment, specifications, err_msg=None):
        c_code = (code.value or "").strip()
        c_name = (name.value or "").strip()
        if not c_code or not c_name:
            if err_msg:
                err_msg.value = "Vui lòng nhập Mã và Tên vật tư!"
                err_msg.visible = True
                self.page.update()
            return

        try:
            p_val = float((price.value or "0").replace(",", "."))
            technical = self._parse_product_specs(specifications.value, category.value)
        except ValueError as exc:
            if err_msg:
                err_msg.value = f"Dữ liệu không hợp lệ: {exc}"
                err_msg.visible = True
                self.page.update()
            return

        try:
            self.db.create_product({
                "category": category.value,
                "code": c_code,
                "name": c_name,
                "unit_price": p_val,
                "unit": (unit.value or "pcs").strip() or "pcs",
                "environment": environment.value,
                "spec_json": technical,
                "supplier": (supplier.value or "").strip(),
            })
            self._close_dialog(dialog)
            self._refresh_options()
            self._refresh_inventory()
            self.message.value = f"Đã thêm vật tư '{c_name}' thành công."
            self.message.color = ft.Colors.GREEN_700
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Đã thêm {c_code} thành công!"), bgcolor=ft.Colors.GREEN_700)
            self.page.snack_bar.open = True
            self.page.update()
        except sqlite3.IntegrityError:
            if err_msg:
                err_msg.value = f"Mã vật tư '{c_code}' đã tồn tại! Vui lòng chọn mã khác."
                err_msg.visible = True
                self.page.update()
        except Exception as exc:
            if err_msg:
                err_msg.value = f"Lỗi: {exc}"
                err_msg.visible = True
                self.page.update()
