"""FloatingActionsMixin: isolated UI responsibilities; inherited by the screen coordinator.

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

class FloatingActionsMixin:
    def _build_action_menu_button(self):
        action_btn = ft.IconButton(
            icon=ft.Icons.APPS_ROUNDED,
            icon_color=ft.Colors.WHITE,
            icon_size=20,
            tooltip="Xem các mục đã chọn & Tạo bảng báo giá",
            on_click=self._on_fab_clicked,
            style=ft.ButtonStyle(padding=0),
        )

        # Nút nổi Floating Action Button ở góc dưới phải sát trên NavigationBar
        return ft.Container(
            right=12,
            bottom=72,
            visible=True,
            animate_opacity=300,
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            content=ft.Container(
                width=42,
                height=42,
                border_radius=21,
                bgcolor=UIColors.PRIMARY,
                shadow=ft.BoxShadow(blur_radius=8, color="#502563EB", offset=ft.Offset(0, 3)),
                alignment=ft.Alignment(0, 0),
                content=action_btn,
            ),
        )

    def _on_fab_clicked(self, e=None):
        """Khi bấm nút tròn FAB: nếu thanh bottom card đang ẩn thì mở rộng lên; nếu đã mở thì mở modal chi tiết."""
        if not getattr(self, "_apply_card_expanded", False):
            self._toggle_bottom_card(force_expand=True)
        else:
            self._open_selected_summary_sheet()

    def _toggle_bottom_card(self, force_expand: Optional[bool] = None):
        """Mở rộng hoặc thu nhỏ thanh bottom card tóm tắt."""
        if force_expand is not None:
            self._apply_card_expanded = force_expand
        else:
            self._apply_card_expanded = not getattr(self, "_apply_card_expanded", False)
        self._update_fab_visibility()

    def _update_fab_visibility(self):
        """Cập nhật trạng thái hiển thị của thanh áp dụng cấu hình, thanh linh kiện và nút nổi FAB."""
        current_tab = getattr(self.nav_bar, "selected_index", 0) if hasattr(self, "nav_bar") else 0
        is_expanded = bool(getattr(self, "_apply_card_expanded", False))

        # FAB luôn hiển thị ở tab 0 (Lập dự toán) và tab 1 (Linh kiện)
        show_fab = current_tab in (0, 1)
        show_estimate_bar = (current_tab == 0) and is_expanded
        show_inventory_bar = (current_tab == 1) and is_expanded

        needs_page_update = False
        if hasattr(self, "quote_apply_bar") and self.quote_apply_bar:
            if self.quote_apply_bar.visible != show_estimate_bar:
                self.quote_apply_bar.visible = show_estimate_bar
                self.quote_apply_bar.opacity = 1.0 if show_estimate_bar else 0.0
                needs_page_update = True

        if hasattr(self, "inventory_total_bar") and self.inventory_total_bar:
            if self.inventory_total_bar.visible != show_inventory_bar:
                self.inventory_total_bar.visible = show_inventory_bar
                self.inventory_total_bar.opacity = 1.0 if show_inventory_bar else 0.0
                needs_page_update = True

        if hasattr(self, "action_menu_btn") and self.action_menu_btn:
            if self.action_menu_btn.visible != show_fab:
                self.action_menu_btn.visible = show_fab
                needs_page_update = True

        if needs_page_update and hasattr(self, "page") and self.page:
            try:
                self.page.update()
            except Exception:
                pass
