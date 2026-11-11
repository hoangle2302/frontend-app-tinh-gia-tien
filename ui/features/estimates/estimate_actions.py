"""EstimateActionsMixin: isolated UI responsibilities; inherited by the screen coordinator.

Preserves original control construction and callbacks for migration safety.
"""
import copy
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

class EstimateActionsMixin:
    def _create_quote_and_go_list(self, e=None):
        """Tạo báo giá từ cấu hình hiện tại, lưu vào DB và chuyển thẳng sang tab Danh sách."""
        if not self.quote_data:
            self.recalculate()
        if not self.quote_data:
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Chưa có dữ liệu dự toán để tạo!"), bgcolor=UIColors.ERROR)
                self.page.snack_bar.open = True
                self.page.update()
            return

        form = self.input_panel.get_values()
        name = form.get("project_name") or f"Báo giá {form.get('module_code') or 'LED'}"
        customer = form.get("customer_name") or "Khách lẻ"
        total_val = self.quote_data.get("pricing", {}).get("final_total", 0)

        history_id = self.db.save_quote_history(
            quote_name=name,
            customer_name=customer,
            payload=form,
            total=total_val,
            status="Nháp",
        )
        saved = self.db.get_quote_history(history_id)
        if saved:
            self.quote_data["quote_number"] = saved.get("quote_number")

        self._interacted_estimate = False
        self._interacted_inventory = False
        self.selected_quote_ids.clear()
        self.select_mode = False
        self._refresh_history()
        self._refresh_list_view()
        self._go_tab(3)

        if hasattr(self, "page") and self.page:
            q_num = saved.get("quote_number") if saved else f"DT-{history_id:03d}"
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Đã tạo báo giá {q_num} thành công và lưu vào Danh sách!"),
                bgcolor=UIColors.SUCCESS,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _to_float(self, value: Any) -> float:
        try:
            number = float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            raise ValueError("Vui lòng nhập số hợp lệ cho kích thước và chi phí.")
        if number < 0:
            raise ValueError("Giá trị không được nhỏ hơn 0.")
        return number

    def _get_selected(self, code: str, category: str) -> Dict[str, Any]:
        product = self.db.get_product_by_code(code) if code else None
        return product if product and product.get("category") == category else {}

    def recalculate(self):
        form = self.input_panel.get_values()
        module = self._get_selected(form["module_code"], "module")
        power = self._get_selected(form["power_code"], "power")
        card = self._get_selected(form["card_code"], "card")
        frame = self._get_selected(form["frame_code"], "frame")
        processors = self.db.list_products(category="processor")
        try:
            if not form.get("screen_type_code") or not form.get("environment"):
                raise ValueError("Vui lòng chọn Loại màn hình từ danh mục FastBusiness.")
            if not all([module, power, card, frame, processors]):
                raise ValueError("Chưa đủ dữ liệu danh mục để tính toán.")
            discount = float(form["discount_percent"] or 0)
            self.quote_data = self.calculator.calculate(
                CalculationInput(
                    width_m=self._to_float(form["width_m"]),
                    height_m=self._to_float(form["height_m"]),
                    environment=form["environment"],
                    module=module, power=power, card=card, frame=frame,
                    processors=processors,
                    discount_percent=discount,
                    include_install=form["include_install"],
                    include_transport=form["include_transport"],
                    install_unit_price=self._to_float(form["install_price"]),
                    transport_price=self._to_float(form["transport_price"]),
                    profit_percent=self._to_float(form["profit_percent"]),
                    vat_percent=self._to_float(form["vat_percent"]),
                    reserve_percent=self._to_float(form["reserve_percent"]),
                    screen_quantity=int(self._to_float(form["screen_quantity"])),
                    additional_items=[
                        {
                            **item,
                            "qty": self._to_float(item["qty"]),
                            "unit_price": self._to_float(item["unit_price"]),
                        }
                        for item in form["additional_items"]
                    ],
                )
            )
            self.quote_data["customer"] = {
                "name": form["customer_name"],
                "project": form["project_name"],
                "phone": form["customer_phone"],
            }
            self.quote_data["display_mode"] = form["display_mode"]
            self.quote_data["notes"] = self.sum_notes.value or ""
            self.preview_panel.update_quote(self.quote_data)
            self.input_panel.update_layout_preview(self.quote_data["summary"])
            self.message.value = ""
        except ValueError as exc:
            self.quote_data = {}
            self.input_panel.update_layout_preview({}, str(exc))
            self.message.value = str(exc)
            self.message.color = ft.Colors.RED_700
        self.preview_panel.message.value = self.message.value
        self._refresh_total_bars()
        self._refresh_summary()
        self.page.update()

    def on_input_change(self, e):
        self._interacted_estimate = True
        self._apply_card_expanded = True
        self._update_fab_visibility()
        self.recalculate()

    def on_load_preset(self, name: str):
        self._interacted_estimate = True
        self._apply_card_expanded = True
        self._update_fab_visibility()
        if name and name.startswith("saved:"):
            saved = self.db.get_configuration(int(name.split(":", 1)[1]))
            if saved:
                self.input_panel.set_values(saved["payload"])
                self.recalculate()

    def on_export_excel(self, e):
        if not self.quote_data:
            self.recalculate()
        if self.quote_data:
            self.message.value = f"Đã xuất Excel: {self.exporter.export_excel(self.quote_data)}"
            self.preview_panel.message.value = self.message.value
            self.page.update()

    def on_export_pdf(self, e):
        if not self.quote_data:
            self.recalculate()
        if self.quote_data:
            self.message.value = f"Đã xuất PDF: {self.exporter.export_pdf(self.quote_data)}"
            self.preview_panel.message.value = self.message.value
            self.page.update()

    def on_save_config(self, e):
        form = self.input_panel.get_values()
        name = self.input_panel.preset_dropdown.value or f"Cấu hình {form['module_code']}"
        self.db.save_configuration(name=name, payload=form)
        self._refresh_preset_options()
        self.message.value = "Đã lưu cấu hình vào SQLite cục bộ."
        self.preview_panel.message.value = self.message.value
        self.page.update()

    def on_save_quote(self, e=None):
        if not self.quote_data:
            self.recalculate()
        if not self.quote_data:
            return
        form = self.input_panel.get_values()
        name = form["project_name"] or f"Báo giá {form['module_code']}"
        history_id = self.db.save_quote_history(
            quote_name=name,
            customer_name=form["customer_name"],
            payload=form,
            total=self.quote_data["pricing"]["final_total"],
        )
        saved = self.db.get_quote_history(history_id)
        if saved:
            self.quote_data["quote_number"] = saved.get("quote_number")
        self._refresh_history()
        self.message.value = "Đã lưu báo giá vào lịch sử."
        self.message.color = ft.Colors.GREEN_700
        self.preview_panel.message.value = self.message.value
        self.page.update()

    def on_share_quote(self, e=None):
        if not self.quote_data:
            self.recalculate()
        if self.quote_data:
            path = self.exporter.export_pdf(self.quote_data)
            self.message.value = f"Đã tạo PDF để in/chia sẻ: {path}"
            self.message.color = ft.Colors.GREEN_700
            self.preview_panel.message.value = self.message.value
            self.page.update()
