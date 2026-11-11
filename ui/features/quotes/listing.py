"""QuoteListingMixin: isolated UI responsibilities; inherited by the screen coordinator.

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

class QuoteListingMixin:
    @staticmethod
    def _strip_vn_accents(text: str) -> str:
        if not text:
            return ""
        s1 = unicodedata.normalize("NFD", text)
        s2 = "".join(c for c in s1 if unicodedata.category(c) != "Mn")
        return s2.replace("đ", "d").replace("Đ", "D").lower().strip()

    def _get_filtered_list_history(self):
        query = (self.list_search.value or "").strip() if hasattr(self, "list_search") else ""
        history = self.db.list_quote_history()
        if not query:
            return history

        query_clean = self._strip_vn_accents(query)
        query_tokens = query_clean.split()

        matched = []
        for h in history:
            payload = h.get("payload") or {}
            item_id = str(h.get("id", ""))
            q_num = str(h.get("quote_number") or f"DT-{item_id}")
            m_code = str(h.get("module_code") or payload.get("module_code") or "")
            c_name = str(h.get("customer_name") or payload.get("customer_name") or "")
            p_name = str(h.get("project_name") or payload.get("project_name") or "")
            status = str(h.get("status") or "")
            date_str = str(h.get("created_at") or "")[:10]
            total_val = h.get("total", 0)
            total_formatted = f"{total_val:,.0f}".replace(",", ".")
            raw_total = str(int(total_val))
            phone = str(payload.get("customer_phone") or "")
            w = str(h.get("width_m") or payload.get("width_m") or "")
            h_val = str(h.get("height_m") or payload.get("height_m") or "")
            dim_str = f"{w}x{h_val} {w} x {h_val} {w}m"

            combined_raw = f"{q_num} {item_id} {m_code} {c_name} {p_name} {status} {date_str} {total_formatted} {raw_total} {dim_str} {phone}".lower()
            combined_clean = self._strip_vn_accents(combined_raw)

            # Khớp nếu TẤT CẢ các từ tìm kiếm đều xuất hiện (hỗ trợ cả có dấu và không dấu)
            all_match = True
            for token in query_tokens:
                if token not in combined_clean and token not in combined_raw:
                    all_match = False
                    break

            if all_match:
                matched.append(h)

        return matched

    def _build_list_view(self):
        self.list_search = ft.TextField(
            label="Tìm kiếm theo số, module, khách hàng...",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=lambda e: self._refresh_list_view(),
            **InputPanel._field_style(),
        )
        self.list_count_text = ft.Text("", size=12, weight=ft.FontWeight.W_600, color=UIColors.TEXT_SECONDARY)
        self.list_subtitle_text = ft.Text("Bảng tổng hợp hồ sơ dự toán và thông số kỹ thuật", size=12, color=UIColors.TEXT_SECONDARY)
        self.select_all_cb = ft.Checkbox(
            label="Chọn tất cả",
            value=False,
            active_color=UIColors.PRIMARY,
            on_change=self._toggle_select_all,
        )
        self.select_count_text = ft.Text("Đã chọn: 0", size=12, color=UIColors.PRIMARY, weight=ft.FontWeight.BOLD)

        # Hàng hiển thị khi ở chế độ chọn
        self.select_header_row = ft.Row(
            visible=False,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self.select_all_cb,
                        ft.TextButton(
                            "Bỏ chọn",
                            icon=ft.Icons.DESELECT_OUTLINED,
                            style=ft.ButtonStyle(
                                color=UIColors.ERROR,
                                padding=ft.Padding(4, 0, 8, 0),
                            ),
                            on_click=lambda e: self._action_deselect_all(),
                        ),
                    ],
                ),
                self.select_count_text,
            ],
        )

        # Hàng hiển thị khi ở chế độ bình thường
        self.normal_header_row = ft.Row(
            visible=True,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.list_count_text,
                ft.TextButton(
                    "Chọn",
                    icon=ft.Icons.CHECKLIST_OUTLINED,
                    style=ft.ButtonStyle(
                        color=UIColors.PRIMARY,
                        padding=ft.Padding(4, 0, 8, 0),
                    ),
                    on_click=lambda e: self._enable_select_mode(),
                ),
            ],
        )

        # Thanh công cụ thao tác khi đã chọn 1 hoặc nhiều dự toán
        self.selection_bar = ft.Container(
            visible=False,
            padding=ft.Padding(12, 8, 12, 8),
            bgcolor="#EFF6FF",
            border_radius=10,
            border=ft.Border.all(1, "#BFDBFE"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                wrap=True,
                spacing=6,
                controls=[
                    self.select_count_text,
                    ft.Row(
                        spacing=4,
                        controls=[
                            ft.OutlinedButton(
                                "Sửa",
                                icon=ft.Icons.EDIT_OUTLINED,
                                height=34,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    padding=ft.Padding(8, 0, 10, 0),
                                ),
                                on_click=lambda e: self._action_edit_selected(),
                            ),
                            ft.OutlinedButton(
                                "Xem",
                                icon=ft.Icons.VISIBILITY_OUTLINED,
                                height=34,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    padding=ft.Padding(8, 0, 10, 0),
                                ),
                                on_click=lambda e: self._action_view_selected(),
                            ),
                            ft.OutlinedButton(
                                "Sao chép",
                                icon=ft.Icons.CONTENT_COPY_OUTLINED,
                                height=34,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    padding=ft.Padding(8, 0, 10, 0),
                                ),
                                on_click=lambda e: self._action_clone_selected(),
                            ),
                            ft.FilledButton(
                                "Xóa",
                                icon=ft.Icons.DELETE_OUTLINE,
                                height=34,
                                style=ft.ButtonStyle(
                                    bgcolor=UIColors.ERROR,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    padding=ft.Padding(8, 0, 10, 0),
                                ),
                                on_click=lambda e: self._action_delete_selected(),
                            ),
                            ft.OutlinedButton(
                                "Bỏ chọn",
                                icon=ft.Icons.DESELECT_OUTLINED,
                                height=34,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    side=ft.BorderSide(1, UIColors.BORDER_STRONG),
                                    color=UIColors.TEXT_SECONDARY,
                                    padding=ft.Padding(8, 0, 10, 0),
                                ),
                                on_click=lambda e: self._action_deselect_all(),
                            ),
                        ],
                    ),
                ],
            ),
        )

        self.list_table_column = ft.Column(spacing=8)

        self.list_scroll_container = ft.Container(
            expand=True,
            padding=ft.Padding(16, 12, 16, 12),
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Danh sách dự toán", size=22, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
                                    self.list_subtitle_text,
                                ],
                            ),
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                tooltip="Tải lại danh sách",
                                on_click=lambda e: self._refresh_list_view(),
                            ),
                        ],
                    ),
                    ft.Row([self.list_search]),
                    self.normal_header_row,
                    self.select_header_row,
                    self.selection_bar,
                    self.list_table_column,
                ],
            ),
        )

        self.list_wrapper = ft.Container(
            expand=True,
            content=self.list_scroll_container,
        )
        return self.list_wrapper

    def _refresh_list_view(self):
        if self.detail_mode and self.active_detail_item:
            if hasattr(self, "list_wrapper"):
                self.list_wrapper.content = self._build_detail_view(self.active_detail_item)
            if hasattr(self, "page") and getattr(self.page, "_Control__page", None):
                self.page.update()
            return

        if hasattr(self, "list_wrapper") and hasattr(self, "list_scroll_container"):
            self.list_wrapper.content = self.list_scroll_container

        history = self._get_filtered_list_history()
        total_records = len(history)
        selected_count = len(self.selected_quote_ids)

        self.list_count_text.value = f"Tổng: {total_records} bản ghi"
        self.select_all_cb.value = (total_records > 0 and selected_count == total_records)
        self.select_count_text.value = f"Đã chọn: {selected_count}/{total_records}"
        self.select_header_row.visible = self.select_mode
        self.normal_header_row.visible = not self.select_mode
        self.selection_bar.visible = (self.select_mode and selected_count > 0)
        self.list_subtitle_text.value = (
            "Tích chọn từng mục hoặc chọn tất cả để thao tác"
            if self.select_mode
            else "Bảng tổng hợp hồ sơ dự toán và thông số kỹ thuật"
        )
        self.list_table_column.controls.clear()

        if not history:
            self.list_table_column.controls.append(
                ft.Container(
                    padding=24,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.INBOX_OUTLINED, size=40, color=UIColors.TEXT_SUBTLE),
                            ft.Text("Chưa có dự toán nào phù hợp", color=UIColors.TEXT_SECONDARY, size=14),
                            ft.FilledButton("Tạo dự toán ngay", icon=ft.Icons.ADD, on_click=lambda e: self._go_tab(0)),
                        ],
                    ),
                )
            )
        else:
            for item in history:
                card = self._build_list_item_card(item)
                self.list_table_column.controls.append(card)

        if hasattr(self, "page") and getattr(self.page, "_Control__page", None):
            self.page.update()

    def _build_list_item_card(self, item: Dict):
        item_id = item["id"]
        is_selected = item_id in self.selected_quote_ids
        payload = item.get("payload") or {}
        unit_str = "Hệ thống"
        date_str = str(item.get("created_at") or "")[:10]
        number_str = item.get("quote_number") or f"DT-{item_id:03d}"
        module_str = item.get("module_code") or payload.get("module_code") or "P10"
        cust_name = item.get("customer_name") or payload.get("customer_name") or "Khách lẻ"
        proj_name = item.get("project_name") or payload.get("project_name") or "Màn hình LED"
        w = item.get("width_m") or payload.get("width_m") or 0
        h = item.get("height_m") or payload.get("height_m") or 0
        explanation = f"{proj_name} - KH: {cust_name} ({w}m × {h}m)"
        total_val = item.get("total", 0)

        # Đổi viền và nền khi được chọn trong select_mode
        if self.select_mode and is_selected:
            bg_card = "#EFF6FF"
            border_card = ft.Border.all(2, UIColors.PRIMARY)
        else:
            bg_card = ft.Colors.WHITE
            border_card = ft.Border.all(1, UIColors.BORDER)

        # Hàng 1 bên trái: Có checkbox chỉ khi đang ở select_mode
        h1_left_controls = []
        if self.select_mode:
            h1_left_controls.append(
                ft.Checkbox(
                    value=is_selected,
                    active_color=UIColors.PRIMARY,
                    on_change=lambda e, i_id=item_id: self._toggle_select_item(i_id, e.control.value),
                )
            )
        h1_left_controls.extend([
            ft.Container(
                padding=ft.Padding(8, 2, 8, 2),
                bgcolor=UIColors.PRIMARY_SOFT if not (self.select_mode and is_selected) else "#DBEAFE",
                border_radius=6,
                content=ft.Text(number_str, size=12, weight=ft.FontWeight.W_700, color=UIColors.PRIMARY),
            ),
            ft.Text(f"Đơn vị: {unit_str}", size=11, color=UIColors.TEXT_SECONDARY),
        ])

        return ft.Container(
            padding=12,
            bgcolor=bg_card,
            border_radius=12,
            border=border_card,
            content=ft.Column(
                spacing=8,
                controls=[
                    # Hàng 1: Số & Ngày (+ Checkbox khi bật chế độ chọn)
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=h1_left_controls,
                            ),
                            ft.Text(f"Ngày: {date_str}", size=11, color=UIColors.TEXT_SECONDARY),
                        ],
                    ),
                    # Hàng 2: Tên module & Giá
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Icon(ft.Icons.GRID_VIEW, size=16, color=UIColors.PRIMARY),
                                    ft.Text(f"Tên module: {module_str}", size=14, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY),
                                ],
                            ),
                            ft.Text(f"{total_val:,.0f} đ".replace(",", "."), size=14, weight=ft.FontWeight.W_800, color=UIColors.PRIMARY),
                        ],
                    ),
                    # Hàng 3: Diễn giải
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=15, color=UIColors.TEXT_SECONDARY),
                            ft.Text(f"Diễn giải: {explanation}", size=12, color="#475569", expand=True),
                        ],
                    ),
                    # Hàng 4: Nút Xem / Sửa nhanh
                    ft.Divider(height=1, color=UIColors.BORDER if not (self.select_mode and is_selected) else "#BFDBFE"),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        spacing=6,
                        controls=[
                            ft.TextButton(
                                "Xem chi tiết",
                                icon=ft.Icons.VISIBILITY_OUTLINED,
                                on_click=lambda e, i_id=item_id: self._open_quote_detail_view(i_id),
                            ),
                            ft.TextButton(
                                "Sao chép",
                                icon=ft.Icons.CONTENT_COPY_OUTLINED,
                                on_click=lambda e, i_id=item_id: self._clone_history(i_id),
                            ),
                        ],
                    ),
                ],
            ),
        )
