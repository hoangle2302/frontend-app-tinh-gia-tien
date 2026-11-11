"""SummaryScreenMixin: isolated UI responsibilities; inherited by the screen coordinator.

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

class SummaryScreenMixin:
    @staticmethod
    def _summary_row(label: str, value_text: ft.Text, bold: bool = False):
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(label, size=13, weight=ft.FontWeight.W_700 if bold else ft.FontWeight.W_400, color=UIColors.TEXT_PRIMARY),
                value_text,
            ],
        )

    def _build_summary_view(self):
        def money_text(size=13, bold=False, color=UIColors.TEXT_PRIMARY):
            return ft.Text("0 đ", size=size, weight=ft.FontWeight.W_800 if bold else ft.FontWeight.W_600, color=color)

        self.sum_code = ft.Text("DT-MỚI", size=12, color=UIColors.TEXT_SECONDARY)
        self.sum_name = ft.Text("Chưa đặt tên dự án", size=18, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY)
        self.sum_total = ft.Text("0 đ", size=30, weight=ft.FontWeight.W_800, color=UIColors.PRIMARY)
        self.sum_total_note = ft.Text("", size=12, color=UIColors.TEXT_SECONDARY)
        self.sum_subtotal = money_text(bold=True)
        self.sum_subtotal_note = ft.Text("", size=12, color=UIColors.TEXT_SECONDARY)
        self.sum_profit = money_text()
        self.sum_transport = money_text()
        self.sum_discount_value = money_text()
        self.sum_before_vat = money_text(bold=True)
        self.sum_vat_value = money_text(bold=True)
        self.sum_grand = money_text(size=20, bold=True, color=UIColors.PRIMARY)

        field_kwargs = InputPanel._field_style()
        self.sum_install = ft.TextField(
            label="Chi phí thi công (đ/m²)",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.CONSTRUCTION,
            on_change=self._on_summary_edit,
            **field_kwargs,
        )
        self.sum_discount = ft.TextField(
            label="Chiết khấu (%)",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.SELL_OUTLINED,
            on_change=self._on_summary_edit,
            **field_kwargs,
        )
        self.sum_vat = ft.TextField(
            label="Thuế GTGT (%)",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=130,
            on_change=self._on_summary_edit,
            **field_kwargs,
        )
        self.sum_notes = ft.TextField(
            label="Ghi chú báo giá",
            hint_text="Cần khảo sát vị trí lắp đặt và xác nhận phương án điều khiển trước khi chốt.",
            multiline=True,
            min_lines=2,
            max_lines=5,
            on_change=lambda e: self.recalculate(),
            **field_kwargs,
        )
        self.sum_format = ft.Dropdown(
            value="pdf",
            width=130,
            options=[ft.dropdown.Option("pdf", "PDF"), ft.dropdown.Option("excel", "Excel")],
            **InputPanel._dropdown_style(),
        )
        self.sum_message = ft.Text("", size=12, color=ft.Colors.GREEN_700)

        def card(controls, bgcolor=ft.Colors.WHITE, border=UIColors.BORDER):
            return ft.Container(
                padding=16,
                bgcolor=bgcolor,
                border=ft.Border.all(1, border),
                border_radius=14,
                content=ft.Column(spacing=12, controls=controls),
            )

        header_card = card([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    self.sum_code,
                    ft.Container(
                        padding=ft.Padding(8, 2, 8, 2),
                        border_radius=6,
                        bgcolor="#F1F5F9",
                        content=ft.Text("Nháp", size=11, color=UIColors.TEXT_SECONDARY),
                    ),
                ],
            ),
            self.sum_name,
        ])
        total_card = card(
            [
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("TỔNG DỰ TOÁN", size=11, weight=ft.FontWeight.W_700, color=UIColors.PRIMARY),
                        ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, color=UIColors.PRIMARY, size=18),
                    ],
                ),
                self.sum_total,
                self.sum_total_note,
            ],
            bgcolor=UIColors.PRIMARY_SOFT,
            border="#C7D6FE",
        )
        cost_card = card([
            ft.Text("Các khoản chi phí", size=17, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
            self._summary_row("Tạm tính linh kiện", self.sum_subtotal, bold=True),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    self.sum_subtotal_note,
                    ft.TextButton("Chỉnh linh kiện ›", on_click=lambda e: self._go_tab(1)),
                ],
            ),
            ft.Divider(color=UIColors.BORDER, height=1),
            self.sum_install,
            self.sum_discount,
            self._summary_row("Lợi nhuận", self.sum_profit),
            self._summary_row("Vận chuyển", self.sum_transport),
            self._summary_row("Chiết khấu", self.sum_discount_value),
            ft.Divider(color=UIColors.BORDER, height=1),
            self._summary_row("Trước thuế", self.sum_before_vat, bold=True),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.sum_vat, self.sum_vat_value],
            ),
            ft.Divider(color=UIColors.BORDER, height=1),
            self._summary_row("Tổng cộng", self.sum_grand, bold=True),
        ])
        notes_card = card([self.sum_notes])
        export_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[ft.Text("Định dạng báo giá", size=13, color=UIColors.TEXT_SECONDARY), self.sum_format],
        )
        export_button = ft.FilledButton(
            "Xuất báo giá",
            icon=ft.Icons.DOWNLOAD,
            height=48,
            expand=True,
            style=InputPanel._primary_button_style(),
            on_click=self._on_summary_export,
        )
        return ft.Container(
            expand=True,
            padding=ft.Padding(16, 12, 16, 16),
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Tổng hợp dự toán", size=22, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
                                    ft.Text("Rà soát và tùy chỉnh chi phí trước khi xuất báo giá.", size=12, color=UIColors.TEXT_SECONDARY),
                                ],
                            ),
                        ],
                    ),
                    header_card,
                    total_card,
                    cost_card,
                    notes_card,
                    ft.Text(
                        "Dữ liệu minh họa • Chưa phải báo giá chính thức",
                        size=11,
                        color="#B45309",
                    ),
                    export_row,
                    ft.Row([export_button]),
                    self.sum_message,
                    ft.Text("Chi tiết báo giá", size=17, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
                    self.preview_panel,
                ],
            ),
        )

    def _sync_summary_fields(self):
        """Đồng bộ các ô nhập ở tab Tổng hợp từ form Lập dự toán."""
        panel = self.input_panel
        self.sum_install.value = panel.install_price_input.value
        self.sum_discount.value = f"{panel.discount_slider.value:g}"
        self.sum_vat.value = panel.vat_input.value

    def _on_summary_edit(self, e):
        panel = self.input_panel
        install = (self.sum_install.value or "0").strip()
        panel.install_price_input.value = install or "0"
        try:
            panel.include_install.value = float(install.replace(",", ".")) > 0
        except ValueError:
            pass
        panel.install_price_input.disabled = not panel.include_install.value
        try:
            panel.discount_slider.value = min(100.0, max(0.0, float((self.sum_discount.value or "0").replace(",", "."))))
        except ValueError:
            pass
        panel.vat_input.value = (self.sum_vat.value or "0").strip()
        self.recalculate()

    def _on_summary_export(self, e):
        if self.sum_format.value == "excel":
            self.on_export_excel(e)
        else:
            self.on_export_pdf(e)
        self.sum_message.value = self.message.value

    def _refresh_summary(self):
        data = self.quote_data or {}
        pricing = data.get("pricing")
        form = self.input_panel.get_values()
        self.sum_name.value = form.get("project_name") or "Chưa đặt tên dự án"
        self.sum_code.value = data.get("quote_number") or "DT-MỚI"
        if not pricing:
            self.sum_message.value = self.message.value
            return
        money = lambda v: f"{self._money(v)} đ"
        vat_percent = pricing["vat_percent"]
        self.sum_total.value = money(pricing["final_total"])
        self.sum_total_note.value = f"Đã gồm thuế GTGT {vat_percent:g}%"
        self.sum_subtotal.value = money(pricing["cost_total"])
        bom_count = len(data.get("bom", []))
        self.sum_subtotal_note.value = f"{bom_count} dòng linh kiện"
        self.sum_profit.value = money(pricing["profit_value"])
        self.sum_transport.value = money(pricing["transport_value"])
        self.sum_discount_value.value = "-" + money(pricing["discount_value"])
        self.sum_before_vat.value = money(pricing["before_vat"])
        self.sum_vat_value.value = money(pricing["vat_value"])
        self.sum_grand.value = money(pricing["final_total"])
        self.sum_message.value = self.message.value
