"""NavigationMixin: isolated UI responsibilities; inherited by the screen coordinator.

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

class NavigationMixin:
    def _on_profile_updated(self, data: dict):
        # Tự động cập nhật default VAT / Lợi nhuận vào form Báo giá nếu người dùng muốn
        if hasattr(self, "input_panel"):
            if "default_vat" in data and not self.input_panel.vat_input.value:
                self.input_panel.vat_input.value = str(data["default_vat"])
            if "default_profit" in data and not self.input_panel.profit_input.value:
                self.input_panel.profit_input.value = str(data["default_profit"])
            self.recalculate()

    def _on_nav_change(self, e):
        self._go_tab(self.nav_bar.selected_index)

    def reset(self):
        """Khôi phục trạng thái ban đầu của MainView về Tab 0 (Lập dự toán) và đóng mọi màn hình phụ."""
        self.detail_mode = False
        self.active_detail_item = None
        self.selected_quote_ids.clear()
        self.select_mode = False
        self._inv_filter = "all"
        self._inv_selected = None
        self._apply_card_expanded = False
        self._interacted_estimate = False
        self._interacted_inventory = False
        self._go_tab(0)

    def _open_quote_tab(self, e=None):
        """Mở tab Lập dự toán (tab 0)."""
        self._go_tab(0)

    def _go_tab(self, idx: int):
        views = [self.quote_view, self.inventory_view, self.summary_view, self.list_view]
        self.nav_bar.selected_index = idx
        self.view_container.content = views[idx]
        if idx == 1:
            self._refresh_inventory()
        elif idx == 2:
            self._sync_summary_fields()
            self._refresh_summary()
        elif idx == 3:
            self._refresh_list_view()
        self._update_fab_visibility()
        self.page.update()

    def _open_aux(self, title: str, view):
        """Mở Lịch sử / Hồ sơ (từ nút trên thanh tiêu đề) kèm nút quay lại."""
        self.view_container.content = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.Padding(8, 4, 8, 0),
                    content=ft.Row(
                        spacing=4,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                tooltip="Quay lại",
                                on_click=lambda e: self._go_tab(self.nav_bar.selected_index or 0),
                            ),
                            ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=UIColors.TEXT_SECONDARY),
                        ],
                    ),
                ),
                ft.Container(expand=True, content=view),
            ],
        )
        self.page.update()

    def open_history(self, e=None):
        self._refresh_history()
        self._open_aux("Lịch sử báo giá", self.history_view)

    def open_profile(self, e=None):
        self._open_aux("Hồ sơ", self.profile_view)

    def mount(self):
        self._mounted = True
        self._on_resize()

    def _on_resize(self, e=None):
        page_w = self.page.width or 400

        if hasattr(self, "profile_view") and hasattr(self.profile_view, "on_resize"):
            self.profile_view.on_resize(page_w)

        if self._mounted:
            self.page.update()

    def on_resize(self, e=None):
        self._on_resize(e)

    def apply_theme(self, is_dark: bool):
        if hasattr(self, "input_panel") and hasattr(self.input_panel, "apply_theme"):
            self.input_panel.apply_theme(is_dark)

        palette = {
            "surface": UIColors.DARK_SURFACE if is_dark else ft.Colors.WHITE,
            "surface_card": UIColors.DARK_SURFACE if is_dark else ft.Colors.WHITE,
            "field": ft.Colors.TRANSPARENT,
            "primary_text": "#E0E2E8" if is_dark else UIColors.TEXT_PRIMARY,
            "secondary_text": "#8C9199" if is_dark else UIColors.TEXT_SECONDARY,
            "border": "#42474E" if is_dark else UIColors.BORDER,
            "card_chip": "#272A2E" if is_dark else "#F1F5F9",
            "icon": "#8C9199" if is_dark else UIColors.TEXT_SECONDARY,
        }

        if hasattr(self, "nav_bar"):
            self.nav_bar.bgcolor = "#111827" if is_dark else "#FFFFFF"
            self.nav_bar.indicator_color = "#004B70" if is_dark else UIColors.PRIMARY_SOFT

        def visit(control):
            if isinstance(control, ft.Card):
                control.bgcolor = palette["surface_card"]
                if control.shape and isinstance(control.shape, ft.RoundedRectangleBorder):
                    control.shape.side = ft.BorderSide(width=1, color=palette["border"])
            elif isinstance(control, ft.Container):
                # Đổi màu nền cho các container card trong theme tối
                bg = getattr(control, "bgcolor", None)
                if bg in [ft.Colors.WHITE, UIColors.SURFACE_SUBTLE, "#EFF6FF", "#F0F5FF"]:
                    if is_dark:
                        control.bgcolor = "#2A2E33" if bg in [UIColors.SURFACE_SUBTLE, "#EFF6FF", "#F0F5FF"] else palette["surface_card"]
                elif bg in [UIColors.DARK_SURFACE, "#2A2E33"] and not is_dark:
                    control.bgcolor = ft.Colors.WHITE
                if getattr(control, "border", None):
                    control.border = ft.Border.all(1, palette["border"])
            if isinstance(control, ft.Text):
                if getattr(control, "color", None) not in {"#BA1A1A", UIColors.PRIMARY, "#8FCDFF"}:
                    control.color = palette["primary_text"]
            elif isinstance(control, ft.Dropdown):
                control.bgcolor = palette["surface"]
                control.border = {
                    ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                        border_radius=12,
                        side=ft.BorderSide(width=1, color=palette["border"]),
                    ),
                    ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                        border_radius=12,
                        side=ft.BorderSide(width=2, color="#8FCDFF" if is_dark else UIColors.PRIMARY),
                    ),
                }
                control.label_style = ft.TextStyle(size=13, color=palette["secondary_text"])
                if hasattr(control, "menu_style") and control.menu_style:
                    control.menu_style.bgcolor = palette["surface"]
            elif isinstance(control, ft.TextField):
                control.bgcolor = palette["field"]
                control.border = {
                    ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                        border_radius=12,
                        side=ft.BorderSide(width=1, color=palette["border"]),
                    ),
                    ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                        border_radius=12,
                        side=ft.BorderSide(width=2, color="#8FCDFF" if is_dark else UIColors.PRIMARY),
                    ),
                }
                control.label_style = ft.TextStyle(size=13, color=palette["secondary_text"])
            elif isinstance(control, ft.Divider):
                control.color = palette["border"]

            children = getattr(control, "controls", None)
            if children:
                for child in children:
                    visit(child)
            content = getattr(control, "content", None)
            if content is not None:
                visit(content)

        visit(self.tabs)
