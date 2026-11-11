"""EstimateScreenMixin: isolated UI responsibilities; inherited by the screen coordinator.

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

class EstimateScreenMixin:
    def _build_apply_bar(self):
        self.apply_mode_text = ft.Text("Chế độ tự động", size=11, color=UIColors.TEXT_SECONDARY)
        self.apply_size_text = ft.Text("Chưa có kích thước", size=12, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY)
        collapse_btn = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN,
            icon_size=18,
            icon_color=UIColors.TEXT_SECONDARY,
            tooltip="Thu nhỏ thanh điều khiển",
            width=28,
            height=28,
            style=ft.ButtonStyle(padding=0),
            on_click=lambda e: self._toggle_bottom_card(force_expand=False),
        )
        self.quote_apply_bar = ft.Container(
            padding=ft.Padding(14, 10, 14, 10),
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, UIColors.BORDER),
            border_radius=14,
            visible=False,
            animate_opacity=300,
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(blur_radius=10, color="#15000000", offset=ft.Offset(0, -3)),
            ink=True,
            on_click=self._open_selected_summary_sheet,
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.apply_mode_text,
                            ft.Row(
                                spacing=4,
                                controls=[
                                    self.apply_size_text,
                                    collapse_btn,
                                ],
                            ),
                        ],
                    ),
                    ft.FilledButton(
                        "Áp dụng cấu hình",
                        icon=ft.Icons.ARROW_FORWARD,
                        height=46,
                        expand=True,
                        on_click=self._open_selected_summary_sheet,
                        style=InputPanel._primary_button_style(),
                    ),
                    ft.Text(
                        "Rà soát các mục chưa thiết lập trước khi chuyển sang bảng dự toán.",
                        size=10,
                        color=UIColors.TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )
        return self.quote_apply_bar

    def _build_total_bar(self, button_text: str, button_icon, on_click, outlined: bool = False):
        total_text = ft.Text("0 đ", size=22, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY)
        count_text = ft.Text("", size=12, color=UIColors.TEXT_SECONDARY)
        self._total_texts.append((total_text, count_text))
        if outlined:
            button = ft.OutlinedButton(
                button_text,
                icon=button_icon,
                height=44,
                expand=True,
                on_click=on_click,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=12),
                    side=ft.BorderSide(1, UIColors.BORDER_STRONG),
                    color=UIColors.PRIMARY,
                ),
            )
        else:
            button = ft.FilledButton(
                button_text,
                icon=button_icon,
                height=44,
                expand=True,
                on_click=on_click,
                style=InputPanel._primary_button_style(),
            )
        return ft.Container(
            padding=ft.Padding(14, 10, 14, 10),
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, UIColors.BORDER),
            border_radius=14,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            ft.Column(
                                spacing=0,
                                controls=[
                                    ft.Text("Tổng dự toán tạm tính", size=12, color=UIColors.TEXT_SECONDARY),
                                    total_text,
                                ],
                            ),
                            count_text,
                        ],
                    ),
                    ft.Row([button]),
                ],
            ),
        )

    def _refresh_total_bars(self):
        pricing = (self.quote_data or {}).get("pricing") or {}
        total = pricing.get("final_total", 0)
        count = len(self.input_panel.additional_items) if hasattr(self, "input_panel") else 0
        for total_text, count_text in self._total_texts:
            total_text.value = f"{total:,.0f} đ".replace(",", ".")
            count_text.value = f"{count} hạng mục thêm"
        if hasattr(self, "apply_size_text") and hasattr(self, "input_panel"):
            form = self.input_panel.get_values()
            w_m = float(form.get("width_m", 0) or 0)
            h_m = float(form.get("height_m", 0) or 0)
            self.apply_size_text.value = f"{int(w_m*1000):,} × {int(h_m*1000):,} mm".replace(",", ".")
            if hasattr(self, "apply_mode_text"):
                mode_str = "Chế độ thủ công" if form.get("config_mode") == "manual" else "Chế độ tự động"
                self.apply_mode_text.value = mode_str

    @staticmethod
    def _money(value) -> str:
        return f"{value:,.0f}".replace(",", ".")
