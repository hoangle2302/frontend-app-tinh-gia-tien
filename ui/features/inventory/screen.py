"""InventoryScreenMixin: isolated UI responsibilities; inherited by the screen coordinator.

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

class InventoryScreenMixin:
    def _build_inventory_view(self):
        self.inventory_search = ft.TextField(
            hint_text="Tên linh kiện hoặc thông số...",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=self._refresh_inventory,
            **InputPanel._field_style(),
        )
        self.inventory_search.bgcolor = ft.Colors.WHITE
        self.inventory_chips = ft.Row(wrap=True, spacing=8, run_spacing=8)
        self.inventory_count = ft.Text("", size=12, weight=ft.FontWeight.W_600, color=UIColors.TEXT_PRIMARY)
        self.inventory_rows = ft.Column(spacing=10)
        self.inventory_project = ft.Text("Chưa đặt tên dự án", size=13, weight=ft.FontWeight.W_600, color=UIColors.TEXT_PRIMARY)
        self.inventory_project_sub = ft.Text("", size=11, color=UIColors.TEXT_SECONDARY)
        add_button = ft.IconButton(
            icon=ft.Icons.ADD,
            tooltip="Thêm vật tư mới vào danh mục",
            icon_color=ft.Colors.WHITE,
            bgcolor=UIColors.PRIMARY,
            width=36,
            height=36,
            style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0),
            on_click=self._open_add_product,
        )
        project_banner = ft.Container(
            padding=ft.Padding(12, 10, 12, 10),
            bgcolor=UIColors.PRIMARY_SOFT,
            border=ft.Border.all(1, "#C7D6FE"),
            border_radius=12,
            ink=True,
            on_click=lambda e: self._go_tab(2),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, color=UIColors.PRIMARY, size=20),
                    ft.Column(
                        spacing=0,
                        expand=True,
                        controls=[self.inventory_project, self.inventory_project_sub],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=UIColors.PRIMARY),
                ],
            ),
        )
        inv_total_text = ft.Text("0 đ", size=22, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY)
        inv_count_text = ft.Text("", size=12, color=UIColors.TEXT_SECONDARY)
        self._total_texts.append((inv_total_text, inv_count_text))
        inv_collapse_btn = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN,
            icon_size=18,
            icon_color=UIColors.TEXT_SECONDARY,
            tooltip="Thu nhỏ thanh điều khiển",
            width=28,
            height=28,
            style=ft.ButtonStyle(padding=0),
            on_click=lambda e: self._toggle_bottom_card(force_expand=False),
        )
        self.inventory_total_bar = ft.Container(
            padding=ft.Padding(14, 10, 14, 10),
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, UIColors.BORDER),
            border_radius=14,
            visible=False,
            animate_opacity=300,
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(blur_radius=10, color="#15000000", offset=ft.Offset(0, -3)),
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
                                    inv_total_text,
                                ],
                            ),
                            ft.Row(
                                spacing=4,
                                controls=[
                                    inv_count_text,
                                    inv_collapse_btn,
                                ],
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.OutlinedButton(
                                "Quay lại dự toán",
                                icon=ft.Icons.ARROW_BACK,
                                height=44,
                                expand=True,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                    side=ft.BorderSide(1, UIColors.BORDER_STRONG),
                                    color=UIColors.PRIMARY,
                                ),
                                on_click=lambda e: self._go_tab(0),
                            ),
                            ft.FilledButton(
                                "Xem & Điều chỉnh",
                                icon=ft.Icons.TUNE,
                                height=44,
                                expand=True,
                                style=InputPanel._primary_button_style(),
                                on_click=self._open_selected_summary_sheet,
                            ),
                        ],
                    ),
                ],
            ),
        )
        view = ft.Container(
            expand=True,
            padding=ft.Padding(16, 12, 16, 8),
            content=ft.Column(
                expand=True,
                spacing=10,
                controls=[
                    ft.Column(
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
                                        expand=True,
                                        controls=[
                                            ft.Text("Danh mục linh kiện", size=22, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
                                            ft.Text("Tìm đúng linh kiện, thêm nhanh vào dự toán.", size=12, color=UIColors.TEXT_SECONDARY),
                                        ],
                                    ),
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            add_button,
                                        ],
                                    ),
                                ],
                            ),
                            project_banner,
                            self.inventory_search,
                            self.inventory_chips,
                            self.inventory_count,
                            self.inventory_rows,
                        ],
                    ),
                    self.inventory_total_bar,
                ],
            ),
        )
        self._refresh_inventory()
        return view

    def _set_inventory_filter(self, key: str):
        self._inv_filter = key
        self._inv_selected = None
        self._inv_qty = 1
        self._interacted_inventory = True
        self._apply_card_expanded = True
        self._update_fab_visibility()
        self._refresh_inventory()

    def _toggle_inventory_item(self, code: str):
        if self._inv_selected == code:
            self._inv_selected = None
        else:
            self._inv_selected = code
            self._inv_qty = 1
        self._interacted_inventory = True
        self._apply_card_expanded = True
        self._update_fab_visibility()
        self._refresh_inventory()

    def _change_inventory_qty(self, delta: int):
        self._inv_qty = max(1, self._inv_qty + delta)
        self._interacted_inventory = True
        self._apply_card_expanded = True
        self._update_fab_visibility()
        self._refresh_inventory()

    def _add_to_estimate(self, product: Dict[str, Any]):
        self.input_panel.add_additional(product["name"], self._inv_qty, product["unit_price"])
        self.message.value = f"Đã thêm {self._inv_qty} × {product['name']} vào dự toán."
        self.message.color = ft.Colors.GREEN_700
        self._inv_selected = None
        self._inv_qty = 1
        self._interacted_inventory = True
        self._apply_card_expanded = True
        self._update_fab_visibility()
        self.recalculate()
        self._refresh_inventory()
        self.page.snack_bar = ft.SnackBar(ft.Text(self.message.value), bgcolor=UIColors.PRIMARY)
        self.page.snack_bar.open = True
        self.page.update()

    def _product_spec_line(self, product: Dict[str, Any]) -> str:
        spec = product.get("spec_json") or {}
        parts = []
        if isinstance(spec, dict):
            if spec.get("pitch"):
                parts.append(str(spec["pitch"]))
            if spec.get("power_w"):
                parts.append(f"{spec['power_w']} W")
        parts.append(product["code"])
        if product.get("supplier"):
            parts.append(product["supplier"])
        return " • ".join(parts)

    def _refresh_inventory(self, e=None):
        search = (self.inventory_search.value or "").strip().lower()
        all_products = self.db.list_products(category=None)
        counts = {"all": len(all_products)}
        for product in all_products:
            counts[product["category"]] = counts.get(product["category"], 0) + 1

        # Chip nhóm
        chips = [("all", "Tất cả")] + [c for c in self.CATEGORY_LABELS if counts.get(c[0])]
        self.inventory_chips.controls = [
            ft.Container(
                padding=ft.Padding(14, 8, 14, 8),
                border_radius=10,
                ink=True,
                bgcolor=UIColors.PRIMARY if self._inv_filter == key else ft.Colors.WHITE,
                border=ft.Border.all(1, UIColors.PRIMARY if self._inv_filter == key else UIColors.BORDER),
                on_click=lambda e, k=key: self._set_inventory_filter(k),
                content=ft.Text(
                    f"{label} · {counts.get(key, 0)}",
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE if self._inv_filter == key else UIColors.TEXT_PRIMARY,
                ),
            )
            for key, label in chips
        ]

        products = [p for p in all_products if self._inv_filter in ("all", p["category"])]
        if search:
            self._interacted_inventory = True
            products = [
                p for p in products
                if search in p["name"].lower()
                or search in p["code"].lower()
                or search in (p.get("supplier") or "").lower()
                or search in str(p.get("spec_json") or "").lower()
            ]
        self.inventory_count.value = f"{len(products)} linh kiện hiển thị"

        form = self.input_panel.get_values() if hasattr(self, "input_panel") else {}
        self.inventory_project.value = form.get("project_name") or "Chưa đặt tên dự án"
        self.inventory_project_sub.value = (
            f"{form.get('width_m', '-')}m × {form.get('height_m', '-')}m • "
            f"{len(self.input_panel.additional_items)} hạng mục thêm"
        ) if form else ""

        self.inventory_rows.controls = []
        if not products:
            self.inventory_rows.controls.append(
                ft.Container(
                    padding=24,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.SEARCH_OFF, size=36, color=UIColors.TEXT_SECONDARY),
                            ft.Text("Không tìm thấy vật tư phù hợp", color=UIColors.TEXT_SECONDARY, size=14),
                        ],
                    ),
                )
            )
        for product in products:
            self.inventory_rows.controls.append(self._build_product_card(product))
        self._refresh_total_bars()
        self._update_fab_visibility()
        self.page.update()

    def _build_product_card(self, product: Dict[str, Any]):
        selected = self._inv_selected == product["code"]
        in_estimate = self.input_panel.additional_qty_by_name(product["name"])
        icon = self.CATEGORY_ICONS.get(product["category"], ft.Icons.INVENTORY_2_OUTLINED)

        if in_estimate:
            status = ft.Text(f"✓ Đã có {in_estimate:g}", size=11, weight=ft.FontWeight.W_600, color=UIColors.SUCCESS)
        else:
            status = ft.Container()
        action = ft.FilledTonalButton(
            "Đang chọn" if selected else "Chọn",
            icon=ft.Icons.CHECK if selected else ft.Icons.ADD,
            height=34,
            style=ft.ButtonStyle(
                bgcolor=UIColors.PRIMARY_SOFT,
                color=UIColors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(10, 0, 10, 0),
            ),
            on_click=lambda e, c=product["code"]: self._toggle_inventory_item(c),
        )

        header = ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    width=40,
                    height=40,
                    border_radius=10,
                    bgcolor="#F1F5F9",
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(icon, size=20, color="#334155"),
                ),
                ft.Column(
                    spacing=2,
                    expand=True,
                    controls=[
                        ft.Text(product["name"], size=15, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY),
                        ft.Text(self._product_spec_line(product), size=11, color=UIColors.TEXT_SECONDARY),
                    ],
                ),
            ],
        )
        price_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    f"{self._money(product['unit_price'])} đ/{product['unit']}",
                    size=16,
                    weight=ft.FontWeight.W_800,
                    color=UIColors.TEXT_PRIMARY,
                ),
                ft.Row(spacing=8, controls=[status, action]),
            ],
        )
        controls = [header, price_row]

        if selected:
            line_total = self._inv_qty * product["unit_price"]
            price_field = ft.TextField(
                value=str(int(product["unit_price"])),
                label="Đơn giá (đ)",
                width=130,
                keyboard_type=ft.KeyboardType.NUMBER,
                **InputPanel._field_style(),
            )
            controls += [
                ft.Divider(color=UIColors.BORDER, height=1),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Số lượng thêm", size=13, color=UIColors.TEXT_PRIMARY),
                        ft.Container(
                            border=ft.Border.all(1, UIColors.BORDER_STRONG),
                            border_radius=10,
                            content=ft.Row(
                                spacing=0,
                                controls=[
                                    ft.IconButton(ft.Icons.REMOVE, icon_size=18, on_click=lambda e: self._change_inventory_qty(-1)),
                                    ft.Text(str(self._inv_qty), size=15, weight=ft.FontWeight.W_700, width=36, text_align=ft.TextAlign.CENTER),
                                    ft.IconButton(ft.Icons.ADD, icon_size=18, on_click=lambda e: self._change_inventory_qty(1)),
                                ],
                            ),
                        ),
                    ],
                ),
                ft.FilledButton(
                    f"Thêm vào dự toán · {self._money(line_total)} đ",
                    icon=ft.Icons.ADD,
                    height=44,
                    expand=True,
                    style=InputPanel._primary_button_style(),
                    on_click=lambda e, p=product: self._add_to_estimate(p),
                ),
                ft.Text(
                    "Linh kiện được thêm vào mục Hạng mục bổ sung của dự toán.",
                    size=11,
                    color="#B45309",
                ),
                ft.Divider(color=UIColors.BORDER, height=1),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        price_field,
                        ft.Row(
                            spacing=4,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.CHECK,
                                    icon_color=UIColors.PRIMARY,
                                    tooltip="Cập nhật giá nhanh",
                                    style=ft.ButtonStyle(bgcolor=UIColors.PRIMARY_SOFT, shape=ft.CircleBorder()),
                                    on_click=lambda e, code=product["code"], field=price_field: self._update_price(code, field),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT_OUTLINED,
                                    icon_color="#00687A",
                                    tooltip="Chỉnh sửa thông tin",
                                    style=ft.ButtonStyle(bgcolor=UIColors.PRIMARY_SOFT, shape=ft.CircleBorder()),
                                    on_click=lambda e, p=product: self._open_edit_product(p),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color="#BA1A1A",
                                    tooltip="Xóa vật tư",
                                    style=ft.ButtonStyle(bgcolor="#FFDAD6", shape=ft.CircleBorder()),
                                    on_click=lambda e, code=product["code"]: self._delete_product(code),
                                ),
                            ],
                        ),
                    ],
                ),
            ]

        return ft.Container(
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border_radius=14,
            border=ft.Border.all(1.5 if selected else 1, UIColors.PRIMARY if selected else UIColors.BORDER),
            content=ft.Column(spacing=10, controls=controls),
        )
