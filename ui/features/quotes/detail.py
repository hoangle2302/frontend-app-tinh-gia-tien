"""QuoteDetailMixin: isolated UI responsibilities; inherited by the screen coordinator.

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

class QuoteDetailMixin:
    def _open_quote_detail_view(self, history_id: int):
        item = self.db.get_quote_history(history_id)
        if not item:
            return
        self.detail_mode = True
        self.active_detail_item = item
        if hasattr(self, "list_wrapper"):
            self.list_wrapper.content = self._build_detail_view(item)
        if hasattr(self, "page") and getattr(self.page, "_Control__page", None):
            self.page.update()

    def _close_detail_view(self):
        self.detail_mode = False
        self.active_detail_item = None
        if hasattr(self, "list_wrapper") and hasattr(self, "list_scroll_container"):
            self.list_wrapper.content = self.list_scroll_container
        self._refresh_list_view()

    def _edit_quote_from_detail(self, history_id: int):
        self.detail_mode = False
        self.active_detail_item = None
        if hasattr(self, "list_wrapper") and hasattr(self, "list_scroll_container"):
            self.list_wrapper.content = self.list_scroll_container
        self._load_history(history_id)

    def _build_detail_view(self, item: Dict[str, Any]) -> ft.Control:
        item_id = item["id"]
        q_num = item.get("quote_number") or f"DT-{item_id:03d}"
        status_val = item.get("status") or "Nháp"
        date_str = str(item.get("created_at") or "")[:19]
        payload = item.get("payload") or {}
        total_val = float(item.get("total", 0))

        cust_name = item.get("customer_name") or payload.get("customer_name") or "Khách lẻ"
        proj_name = item.get("project_name") or payload.get("project_name") or "Màn hình LED"
        phone = payload.get("customer_phone") or "—"
        address = payload.get("customer_address") or "—"

        w = item.get("width_m") or payload.get("width_m") or 0
        h = item.get("height_m") or payload.get("height_m") or 0
        try:
            area = float(w) * float(h)
        except Exception:
            area = 0.0
        m_code = item.get("module_code") or payload.get("module_code") or "—"
        screen_qty = payload.get("screen_quantity") or 1
        display_mode = payload.get("display_mode") or "Online"
        vat_pct = payload.get("vat_percent", 10)
        profit_pct = payload.get("profit_percent", 0)

        # Tính toán lại chi tiết bảng linh kiện từ engine
        calc_items = []
        try:
            form = payload
            module = self._get_selected(form.get("module_code"), "module")
            power = self._get_selected(form.get("power_code"), "power")
            card = self._get_selected(form.get("card_code"), "card")
            frame = self._get_selected(form.get("frame_code"), "frame")
            processors = self.db.list_products(category="processor")
            if module and power and card and frame and processors:
                discount = float(form.get("discount_percent") or 0)
                calc_res = self.calculator.calculate(
                    CalculationInput(
                        width_m=self._to_float(form.get("width_m")),
                        height_m=self._to_float(form.get("height_m")),
                        environment=form.get("environment", "indoor"),
                        module=module, power=power, card=card, frame=frame,
                        processors=processors,
                        discount_percent=discount,
                        include_install=form.get("include_install", True),
                        include_transport=form.get("include_transport", True),
                        install_unit_price=self._to_float(form.get("install_price", 0)),
                        transport_price=self._to_float(form.get("transport_price", 0)),
                        profit_percent=self._to_float(form.get("profit_percent", 0)),
                        vat_percent=self._to_float(form.get("vat_percent", 10)),
                        reserve_percent=self._to_float(form.get("reserve_percent", 0)),
                        screen_quantity=int(self._to_float(form.get("screen_quantity", 1))),
                        additional_items=[
                            {
                                **it,
                                "qty": self._to_float(it.get("qty", 0)),
                                "unit_price": self._to_float(it.get("unit_price", 0)),
                            }
                            for it in form.get("additional_items", [])
                        ],
                    )
                )
                calc_items = calc_res.get("items", [])
        except Exception:
            calc_items = []

        def _info_cell(label: str, val: str, icon=None):
            return ft.Container(
                expand=True,
                padding=ft.Padding(10, 8, 10, 8),
                bgcolor=UIColors.SURFACE_SUBTLE,
                border_radius=8,
                content=ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(
                            spacing=4,
                            controls=[
                                ft.Icon(icon, size=13, color=UIColors.TEXT_SECONDARY) if icon else ft.Container(width=0),
                                ft.Text(label, size=11, color=UIColors.TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                            ],
                        ),
                        ft.Text(str(val), size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                ),
            )

        # Header bar của giao diện chỉ xem
        header_bar = ft.Container(
            padding=ft.Padding(0, 0, 0, 4),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                wrap=True,
                spacing=8,
                controls=[
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                tooltip="Quay lại danh sách",
                                style=ft.ButtonStyle(bgcolor="#EFF6FF"),
                                icon_color=UIColors.PRIMARY,
                                on_click=lambda e: self._close_detail_view(),
                            ),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text(f"Chi tiết {q_num}", size=18, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
                                            ft.Container(
                                                padding=ft.Padding(6, 2, 6, 2),
                                                bgcolor="#ECFDF5",
                                                border_radius=6,
                                                border=ft.Border.all(1, "#A7F3D0"),
                                                content=ft.Text("CHỈ XEM", size=10, weight=ft.FontWeight.BOLD, color="#059669"),
                                            ),
                                        ],
                                    ),
                                    ft.Text(f"Ngày tạo: {date_str} • Trạng thái: {status_val}", size=11, color=UIColors.TEXT_SECONDARY),
                                ],
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.OutlinedButton(
                                "Sao chép",
                                icon=ft.Icons.CONTENT_COPY,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                                on_click=lambda e: self._clone_history(item_id),
                            ),
                            ft.FilledButton(
                                "Chỉnh sửa",
                                icon=ft.Icons.EDIT,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), bgcolor=UIColors.PRIMARY),
                                on_click=lambda e: self._edit_quote_from_detail(item_id),
                            ),
                        ],
                    ),
                ],
            ),
        )

        card_customer = ft.Container(
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, UIColors.BORDER),
            border_radius=12,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row([ft.Icon(ft.Icons.BUSINESS, size=16, color=UIColors.PRIMARY), ft.Text("Thông tin khách hàng & dự án", size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY)]),
                    ft.Row([_info_cell("Dự án", proj_name), _info_cell("Khách hàng", cust_name)]),
                    ft.Row([_info_cell("Số điện thoại", phone), _info_cell("Địa chỉ", address)]),
                ],
            ),
        )

        card_specs = ft.Container(
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, UIColors.BORDER),
            border_radius=12,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row([ft.Icon(ft.Icons.SETTINGS, size=16, color=UIColors.PRIMARY), ft.Text("Thông số kỹ thuật màn hình", size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY)]),
                    ft.Row([_info_cell("Mã Module", m_code), _info_cell("Kích thước", f"{w}m × {h}m ({area:.2f} m²)")], spacing=8),
                    ft.Row([_info_cell("Số lượng bộ", f"{screen_qty} màn hình"), _info_cell("Điều khiển", display_mode)], spacing=8),
                ],
            ),
        )

        bom_rows = []
        if calc_items:
            for idx, cit in enumerate(calc_items, 1):
                qty_val = cit.get("quantity", cit.get("qty", 1))
                price_val = cit.get("unit_price", 0)
                sub_val = cit.get("total", qty_val * price_val)
                bom_rows.append(
                    ft.Container(
                        padding=ft.Padding(8, 6, 8, 6),
                        bgcolor=UIColors.SURFACE_SUBTLE if idx % 2 == 1 else ft.Colors.WHITE,
                        border_radius=6,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(f"{idx}. {cit.get('name')}", size=12, weight=ft.FontWeight.W_600, color=UIColors.TEXT_PRIMARY, expand=True),
                                ft.Text(f"{qty_val:g} {cit.get('unit', '')}", size=12, color=UIColors.TEXT_SECONDARY, width=70, text_align=ft.TextAlign.RIGHT),
                                ft.Text(f"{price_val:,.0f} đ".replace(",", "."), size=12, color="#475569", width=95, text_align=ft.TextAlign.RIGHT),
                                ft.Text(f"{sub_val:,.0f} đ".replace(",", "."), size=12, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY, width=105, text_align=ft.TextAlign.RIGHT),
                            ],
                        ),
                    )
                )
        else:
            bom_rows.append(
                ft.Container(
                    padding=12,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text("Dữ liệu linh kiện lưu trữ theo cấu hình tổng thể.", size=12, color=UIColors.TEXT_SECONDARY),
                )
            )

        card_bom = ft.Container(
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, UIColors.BORDER),
            border_radius=12,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row([ft.Icon(ft.Icons.LIST_ALT, size=16, color=UIColors.PRIMARY), ft.Text("Bảng kê linh kiện dự toán (BOM)", size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY)]),
                    ft.Container(
                        padding=ft.Padding(8, 4, 8, 4),
                        bgcolor=UIColors.BORDER,
                        border_radius=6,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Hạng mục", size=11, weight=ft.FontWeight.BOLD, color="#475569", expand=True),
                                ft.Text("Số lượng", size=11, weight=ft.FontWeight.BOLD, color="#475569", width=70, text_align=ft.TextAlign.RIGHT),
                                ft.Text("Đơn giá", size=11, weight=ft.FontWeight.BOLD, color="#475569", width=95, text_align=ft.TextAlign.RIGHT),
                                ft.Text("Thành tiền", size=11, weight=ft.FontWeight.BOLD, color="#475569", width=105, text_align=ft.TextAlign.RIGHT),
                            ],
                        ),
                    ),
                    *bom_rows,
                ],
            ),
        )

        card_total = ft.Container(
            padding=16,
            bgcolor="#EFF6FF",
            border=ft.Border.all(1.5, "#BFDBFE"),
            border_radius=12,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Tổng dự toán báo giá (đã gồm VAT)", size=12, color="#1E40AF", weight=ft.FontWeight.W_600),
                            ft.Text(f"Thuế VAT: {vat_pct}% • Lợi nhuận: {profit_pct}%", size=11, color=UIColors.TEXT_SECONDARY),
                        ],
                    ),
                    ft.Text(f"{total_val:,.0f} đ".replace(",", "."), size=22, weight=ft.FontWeight.W_900, color=UIColors.PRIMARY),
                ],
            ),
        )

        return ft.Container(
            expand=True,
            padding=ft.Padding(16, 12, 16, 16),
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=12,
                controls=[
                    header_bar,
                    card_customer,
                    card_specs,
                    card_bom,
                    card_total,
                ],
            ),
        )
