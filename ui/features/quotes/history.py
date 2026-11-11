"""QuoteHistoryMixin: isolated UI responsibilities; inherited by the screen coordinator.

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

class QuoteHistoryMixin:
    def _build_history_view(self):
        self.history_rows = ft.Column(spacing=10)
        self.history_search = ft.TextField(
            label="Tìm khách hàng, dự án hoặc số báo giá",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=self._refresh_history,
            **InputPanel._field_style(),
        )
        self.history_status = ft.Dropdown(
            label="Trạng thái",
            value="all",
            width=140,
            options=[
                ft.dropdown.Option("all", "Tất cả"),
                ft.dropdown.Option("Nháp"),
                ft.dropdown.Option("Đã gửi"),
                ft.dropdown.Option("Chốt"),
                ft.dropdown.Option("Hủy"),
            ],
            on_select=self._refresh_history,
            **InputPanel._dropdown_style(),
        )
        self.history_stats = ft.Row(wrap=True, spacing=8)
        view = ft.Container(
            expand=True,
            padding=ft.Padding(16, 12, 16, 16),
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=12,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=4,
                                height=24,
                                bgcolor=UIColors.PRIMARY,
                                border_radius=2,
                            ),
                            ft.Column(
                                spacing=1,
                                controls=[
                                    ft.Text("Lịch sử báo giá", size=20, weight=ft.FontWeight.BOLD, color=UIColors.TEXT_PRIMARY),
                                    ft.Text("Theo dõi trạng thái, mở lại hoặc xuất lại các báo giá đã tạo", size=12, color=UIColors.TEXT_SECONDARY),
                                ],
                            ),
                        ],
                    ),
                    self.history_stats,
                    ft.Row([self.history_search, self.history_status], spacing=8, wrap=True),
                    self.history_rows,
                ],
            ),
        )
        self._refresh_history()
        return view

    def _refresh_history(self, e=None):
        self.history_rows.controls = []
        history = self.db.list_quote_history(
            search=self.history_search.value if hasattr(self, "history_search") else "",
            status=self.history_status.value if hasattr(self, "history_status") else "all",
        )
        total_count = len(history)
        chot_count = sum(1 for h in history if h.get("status") == "Chốt")
        total_sum = sum(h.get("total", 0) for h in history)

        if hasattr(self, "history_stats"):
            self.history_stats.controls = [
                ft.Container(
                    expand=True,
                    padding=ft.Padding(12, 8, 12, 8),
                    border_radius=12,
                    bgcolor="#F1F5F9",
                    content=ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Tổng báo giá", size=11, color=UIColors.TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                            ft.Text(f"{total_count} bản ghi", size=14, weight=ft.FontWeight.BOLD, color=UIColors.TEXT_PRIMARY),
                        ],
                    ),
                ),
                ft.Container(
                    expand=True,
                    padding=ft.Padding(12, 8, 12, 8),
                    border_radius=12,
                    bgcolor="#DFFFE2",
                    content=ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Đã chốt", size=11, color="#1B5E20", weight=ft.FontWeight.W_500),
                            ft.Text(f"{chot_count} đơn", size=14, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                        ],
                    ),
                ),
                ft.Container(
                    expand=True,
                    padding=ft.Padding(12, 8, 12, 8),
                    border_radius=12,
                    bgcolor=UIColors.PRIMARY_SOFT,
                    content=ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Tổng giá trị", size=11, color="#004B70", weight=ft.FontWeight.W_500),
                            ft.Text(f"{total_sum:,.0f} đ", size=14, weight=ft.FontWeight.BOLD, color="#001E30"),
                        ],
                    ),
                ),
            ]

        if not history:
            self.history_rows.controls.append(
                ft.Card(
                    elevation=0,
                    bgcolor=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(
                        radius=14,
                        side=ft.BorderSide(width=1, color=UIColors.BORDER),
                    ),
                    content=ft.Container(
                        padding=24,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.HISTORY_TOGGLE_OFF, size=36, color=UIColors.TEXT_SECONDARY),
                                ft.Text("Chưa có báo giá nào trong danh sách", color=UIColors.TEXT_SECONDARY, size=14),
                                ft.FilledButton(
                                    "Tạo báo giá mới ngay",
                                    icon=ft.Icons.ADD,
                                    style=InputPanel._primary_button_style(),
                                    on_click=self._open_quote_tab,
                                ),
                            ],
                        ),
                    ),
                )
            )
        else:
            status_colors = {
                "Nháp": ("#F1F5F9", "#42474E"),
                "Đã gửi": (UIColors.PRIMARY_SOFT, "#004B70"),
                "Chốt": ("#DFFFE2", "#1B5E20"),
                "Hủy": ("#FFDAD6", "#BA1A1A"),
            }
            for item in history:
                curr_status = item.get("status", "Nháp")
                bg_chip, text_chip = status_colors.get(curr_status, ("#F1F5F9", "#42474E"))
                self.history_rows.controls.append(
                    ft.Card(
                        elevation=0,
                        bgcolor=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(
                            radius=14,
                            side=ft.BorderSide(width=1, color=UIColors.BORDER),
                        ),
                        content=ft.Container(
                            padding=14,
                            content=ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Row(
                                                spacing=8,
                                                controls=[
                                                    ft.Container(
                                                        padding=ft.Padding(8, 4, 8, 4),
                                                        border_radius=8,
                                                        bgcolor=bg_chip,
                                                        content=ft.Text(curr_status, size=11, weight=ft.FontWeight.BOLD, color=text_chip),
                                                    ),
                                                    ft.Text(
                                                        item.get("quote_number") or f"BG-ID-{item['id']}",
                                                        weight=ft.FontWeight.BOLD,
                                                        size=13,
                                                        color=UIColors.PRIMARY,
                                                    ),
                                                ],
                                            ),
                                            ft.Text(
                                                f"{item['total']:,.0f} đ",
                                                weight=ft.FontWeight.BOLD,
                                                size=15,
                                                color=UIColors.PRIMARY,
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        f"Khách hàng: {item.get('customer_name') or 'Chưa cập nhật'}"
                                        + (f" • Dự án: {item.get('project_name')}" if item.get('project_name') else ""),
                                        size=13,
                                        color=UIColors.TEXT_PRIMARY,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Row(
                                        wrap=True,
                                        spacing=8,
                                        controls=[
                                            ft.Text(
                                                f"Kích thước: {item.get('width_m', 0)}m × {item.get('height_m', 0)}m"
                                                + (f" • Mod: {item.get('module_code')}" if item.get('module_code') else ""),
                                                size=11,
                                                color=UIColors.TEXT_SECONDARY,
                                            ),
                                            ft.Text(
                                                f"Ngày: {str(item.get('created_at', ''))[:16]}",
                                                size=11,
                                                color=UIColors.TEXT_SECONDARY,
                                            ),
                                        ],
                                    ),
                                    ft.Divider(color=UIColors.BORDER, height=1),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        wrap=True,
                                        spacing=6,
                                        controls=[
                                            ft.Dropdown(
                                                value=curr_status,
                                                width=115,
                                                options=[
                                                    ft.dropdown.Option("Nháp"),
                                                    ft.dropdown.Option("Đã gửi"),
                                                    ft.dropdown.Option("Chốt"),
                                                    ft.dropdown.Option("Hủy"),
                                                ],
                                                on_select=lambda e, item_id=item["id"]: self._update_history_status(item_id, e.control.value),
                                                **InputPanel._dropdown_style(),
                                            ),
                                            ft.Row(
                                                spacing=4,
                                                controls=[
                                                    ft.FilledTonalButton(
                                                        "Mở",
                                                        icon=ft.Icons.FOLDER_OPEN_OUTLINED,
                                                        height=36,
                                                        style=ft.ButtonStyle(
                                                            shape=ft.RoundedRectangleBorder(radius=12),
                                                            padding=ft.Padding(8, 0, 10, 0),
                                                        ),
                                                        on_click=lambda e, item_id=item["id"]: self._load_history(item_id),
                                                    ),
                                                    ft.OutlinedButton(
                                                        "Nhân bản",
                                                        icon=ft.Icons.CONTENT_COPY_OUTLINED,
                                                        height=36,
                                                        style=ft.ButtonStyle(
                                                            shape=ft.RoundedRectangleBorder(radius=12),
                                                            padding=ft.Padding(8, 0, 10, 0),
                                                        ),
                                                        on_click=lambda e, item_id=item["id"]: self._clone_history(item_id),
                                                    ),
                                                    ft.IconButton(
                                                        icon=ft.Icons.DELETE_OUTLINE,
                                                        icon_color="#BA1A1A",
                                                        tooltip="Xóa báo giá",
                                                        width=36,
                                                        height=36,
                                                        on_click=lambda e, item_id=item["id"]: self._delete_history(item_id),
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    )
                )
        if hasattr(self, "page"):
            self.page.update()

    def _load_history(self, history_id: int):
        item = self.db.get_quote_history(history_id)
        if item:
            self.input_panel.set_values(item["payload"])
            self.nav_bar.selected_index = 0
            self.view_container.content = self.quote_view
            self.recalculate()

    def _delete_history(self, history_id: int):
        self.db.delete_quote_history(history_id)
        self._refresh_history()
        self.message.value = "Đã xóa báo giá khỏi lịch sử."
        self.message.color = ft.Colors.GREEN_700

    def _update_history_status(self, history_id: int, status: str):
        self.db.update_quote_status(history_id, status)
        self._refresh_history()
        self.message.value = "Đã cập nhật trạng thái báo giá."
        self.message.color = ft.Colors.GREEN_700

    def _clone_history(self, history_id: int):
        item = self.db.get_quote_history(history_id)
        if not item:
            return
        payload = copy.deepcopy(item.get("payload") or {})
        orig_name = item.get("quote_name") or item.get("project_name") or "Dự toán"
        new_name = f"{orig_name} (Bản sao)"
        new_id = self.db.save_quote_history(
            quote_name=new_name,
            customer_name=item.get("customer_name") or "",
            payload=payload,
            total=item.get("total", 0),
            status="Nháp",
        )
        new_item = self.db.get_quote_history(new_id)
        new_num = new_item.get("quote_number") if new_item else f"DT-{new_id:03d}"

        self.detail_mode = False
        self.active_detail_item = None
        if hasattr(self, "list_wrapper") and hasattr(self, "list_scroll_container"):
            self.list_wrapper.content = self.list_scroll_container
        self._refresh_history()
        self._refresh_list_view()

        if hasattr(self, "page") and self.page:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Đã sao chép thành công và tạo mới dự toán: {new_num}!"),
                bgcolor=UIColors.SUCCESS,
            )
            self.page.snack_bar.open = True
            self.page.update()
