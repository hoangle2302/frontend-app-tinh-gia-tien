import sqlite3
from typing import Any, Dict

import flet as ft

from database.db_manager import DBManager
from engine.calculator import CalculationInput, Calculators
from engine.exporter import QuoteExporter
from ui.components.input_panel import InputPanel
from ui.components.preview_panel import PreviewPanel


class MainView:
    def __init__(self, page: ft.Page, db: DBManager):
        self.page = page
        self.db = db
        self.calculator = Calculators()
        self.exporter = QuoteExporter()
        self.quote_data: Dict[str, Any] = {}
        self.message = ft.Text("", color=ft.Colors.GREEN_700)
        self._refresh_options()

        self.input_panel = InputPanel(
            options=self.options,
            on_change=self.on_input_change,
            on_save=self.on_save_config,
            on_export_excel=self.on_export_excel,
            on_export_pdf=self.on_export_pdf,
            on_load_preset=self.on_load_preset,
        )
        self._refresh_preset_options()
        self.preview_panel = PreviewPanel(
            self.on_export_excel,
            self.on_export_pdf,
            self.on_save_quote,
            self.on_share_quote,
        )
        self.left_container = ft.Container(
            content=self.input_panel,
            expand=True,
        )
        self.quote_view = ft.Container(
            padding=ft.Padding(8, 4, 8, 8),
            content=None,
        )
        self.inventory_view = self._build_inventory_view()
        self.history_view = self._build_history_view()
        self.tabs = ft.Tabs(
            selected_index=0,
            length=3,
            expand=1,
            animation_duration=250,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        divider_color="#E0E2EC",
                        indicator_color="#006494",
                        indicator_thickness=3,
                        scrollable=False,
                        label_padding=ft.Padding(16, 0, 16, 0),
                        label_text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
                        unselected_label_text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_500),
                        tabs=[
                            ft.Tab(label="Báo giá", icon=ft.Icons.CALCULATE_OUTLINED),
                            ft.Tab(label="Danh mục", icon=ft.Icons.INVENTORY_2_OUTLINED),
                            ft.Tab(label="Lịch sử", icon=ft.Icons.HISTORY_ROUNDED),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[self.quote_view, self.inventory_view, self.history_view],
                    ),
                ],
            ),
        )
        self._mounted = False
        self.page.on_resize = self._on_resize
        self._on_resize()
        self.recalculate()

    def mount(self):
        self.page.add(
            self.tabs,
        )
        self._mounted = True
        self._on_resize()

    def _on_resize(self, e=None):
        self.quote_view.content = ft.Column(
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            controls=[self.left_container, self.preview_panel],
        )
        if self._mounted:
            self.page.update()

    def on_resize(self, e=None):
        self._on_resize(e)

    def apply_theme(self, is_dark: bool):
        palette = {
            "surface": "#1D2024" if is_dark else ft.Colors.WHITE,
            "surface_card": "#1D2024" if is_dark else ft.Colors.WHITE,
            "field": ft.Colors.TRANSPARENT,
            "primary_text": "#E0E2E8" if is_dark else "#191C1E",
            "secondary_text": "#8C9199" if is_dark else "#72777F",
            "border": "#42474E" if is_dark else "#E0E2EC",
            "card_chip": "#272A2E" if is_dark else "#F0F4F8",
            "icon": "#8C9199" if is_dark else "#72777F",
        }

        def visit(control):
            if isinstance(control, ft.Card):
                control.bgcolor = palette["surface_card"]
                if control.shape and isinstance(control.shape, ft.RoundedRectangleBorder):
                    control.shape.side = ft.BorderSide(width=1, color=palette["border"])
            if isinstance(control, ft.Text):
                if getattr(control, "color", None) not in {"#BA1A1A", "#006494", "#8FCDFF"}:
                    control.color = palette["primary_text"]
            elif isinstance(control, (ft.TextField, ft.Dropdown)):
                control.bgcolor = palette["field"]
                control.border = {
                    ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                        border_radius=12,
                        side=ft.BorderSide(width=1, color=palette["border"]),
                    ),
                    ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                        border_radius=12,
                        side=ft.BorderSide(width=2, color="#8FCDFF" if is_dark else "#006494"),
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

    def _refresh_options(self):
        self.options = {
            "modules": self.db.list_products(category="module"),
            "powers": self.db.list_products(category="power"),
            "cards": self.db.list_products(category="card"),
            "frames": self.db.list_products(category="frame"),
            "processors": self.db.list_products(category="processor"),
        }

    def _refresh_preset_options(self):
        options = [
            ft.dropdown.Option("Màn hình Hội trường P2.5"),
            ft.dropdown.Option("Màn hình Outdoor P4"),
        ]
        options.extend(
            ft.dropdown.Option(
                key=f"saved:{item['id']}",
                text=f"{item['name']} (đã lưu)",
            )
            for item in self.db.list_configurations()
        )
        self.input_panel.preset_dropdown.options = options

    def _build_category_selector(self, default_value: str = "module"):
        options = [
            ("module", "Module LED"),
            ("power", "Nguồn"),
            ("card", "Card thu"),
            ("processor", "Bộ xử lý"),
            ("frame", "Khung"),
            ("service", "Dịch vụ"),
        ]
        radio_group = ft.RadioGroup(
            value=default_value,
            content=ft.Row(
                wrap=True,
                spacing=6,
                run_spacing=4,
                controls=[
                    ft.Radio(
                        value=val,
                        label=lbl,
                        fill_color="#006494",
                    )
                    for val, lbl in options
                ],
            ),
        )
        container = ft.Container(
            padding=ft.Padding(10, 8, 10, 8),
            border=ft.Border.all(1, "#C2C7CF"),
            border_radius=12,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Text("Nhóm vật tư *", size=12, color="#72777F", weight=ft.FontWeight.W_500),
                    radio_group,
                ],
            ),
        )
        return radio_group, container

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
                                bgcolor="#006494",
                                border_radius=2,
                            ),
                            ft.Column(
                                spacing=1,
                                controls=[
                                    ft.Text("Lịch sử báo giá", size=20, weight=ft.FontWeight.BOLD, color="#191C1E"),
                                    ft.Text("Theo dõi trạng thái, mở lại hoặc xuất lại các báo giá đã tạo", size=12, color="#72777F"),
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
                    bgcolor="#F0F4F8",
                    content=ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Tổng báo giá", size=11, color="#72777F", weight=ft.FontWeight.W_500),
                            ft.Text(f"{total_count} bản ghi", size=14, weight=ft.FontWeight.BOLD, color="#191C1E"),
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
                    bgcolor="#CBE6FF",
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
                        radius=16,
                        side=ft.BorderSide(width=1, color="#E0E2EC"),
                    ),
                    content=ft.Container(
                        padding=24,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.HISTORY_TOGGLE_OFF, size=36, color="#72777F"),
                                ft.Text("Chưa có báo giá nào trong danh sách", color="#72777F", size=14),
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
                "Nháp": ("#F0F4F8", "#42474E"),
                "Đã gửi": ("#CBE6FF", "#004B70"),
                "Chốt": ("#DFFFE2", "#1B5E20"),
                "Hủy": ("#FFDAD6", "#BA1A1A"),
            }
            for item in history:
                curr_status = item.get("status", "Nháp")
                bg_chip, text_chip = status_colors.get(curr_status, ("#F0F4F8", "#42474E"))
                self.history_rows.controls.append(
                    ft.Card(
                        elevation=0,
                        bgcolor=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(
                            radius=16,
                            side=ft.BorderSide(width=1, color="#E0E2EC"),
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
                                                        color="#006494",
                                                    ),
                                                ],
                                            ),
                                            ft.Text(
                                                f"{item['total']:,.0f} đ",
                                                weight=ft.FontWeight.BOLD,
                                                size=15,
                                                color="#006494",
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        f"Khách hàng: {item.get('customer_name') or 'Chưa cập nhật'}"
                                        + (f" • Dự án: {item.get('project_name')}" if item.get('project_name') else ""),
                                        size=13,
                                        color="#191C1E",
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
                                                color="#72777F",
                                            ),
                                            ft.Text(
                                                f"Ngày: {str(item.get('created_at', ''))[:16]}",
                                                size=11,
                                                color="#72777F",
                                            ),
                                        ],
                                    ),
                                    ft.Divider(color="#E0E2EC", height=1),
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

    def _open_quote_tab(self, e=None):
        self.tabs.selected_index = 0
        self.page.update()

    def _load_history(self, history_id: int):
        item = self.db.get_quote_history(history_id)
        if item:
            self.input_panel.set_values(item["payload"])
            self.tabs.selected_index = 0
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
        payload = item["payload"]
        self.input_panel.set_values(payload)
        self.tabs.selected_index = 0
        self.recalculate()
        self.message.value = "Đã nhân bản báo giá. Bạn có thể chỉnh sửa rồi lưu thành báo giá mới."
        self.message.color = ft.Colors.GREEN_700

    def _build_inventory_view(self):
        self.inventory_category = ft.Dropdown(
            label="Lọc theo nhóm",
            value="all",
            width=150,
            options=[
                ft.dropdown.Option("all", "Tất cả"),
                ft.dropdown.Option("module", "Module LED"),
                ft.dropdown.Option("power", "Nguồn"),
                ft.dropdown.Option("card", "Card thu"),
                ft.dropdown.Option("processor", "Bộ xử lý"),
                ft.dropdown.Option("frame", "Khung"),
                ft.dropdown.Option("service", "Dịch vụ"),
            ],
            on_select=lambda e: self._refresh_inventory(),
            **InputPanel._dropdown_style(),
        )
        self.inventory_search = ft.TextField(
            label="Tìm kiếm vật tư",
            hint_text="Nhập tên, mã vật tư hoặc NCC",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=self._refresh_inventory,
            **InputPanel._field_style(),
        )
        self.inventory_rows = ft.Column(spacing=10)
        add_button = ft.IconButton(
            icon=ft.Icons.ADD,
            tooltip="Thêm vật tư mới",
            icon_color=ft.Colors.WHITE,
            bgcolor="#006494",
            width=40,
            height=40,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=0,
            ),
            on_click=self._open_add_product,
        )
        view = ft.Container(
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
                            ft.Row(
                                expand=True,
                                controls=[
                                    ft.Container(
                                        width=4,
                                        height=24,
                                        bgcolor="#006494",
                                        border_radius=2,
                                    ),
                                    ft.Column(
                                        spacing=1,
                                        expand=True,
                                        controls=[
                                            ft.Text("Danh mục vật tư & Đơn giá", size=18, weight=ft.FontWeight.BOLD, color="#191C1E", no_wrap=True),
                                            ft.Text("Quản lý bảng giá linh kiện LED", size=12, color="#72777F", no_wrap=True),
                                        ],
                                    ),
                                ],
                            ),
                            add_button,
                        ],
                    ),
                    ft.Row([self.inventory_search, self.inventory_category], spacing=8, wrap=True),
                    self.inventory_rows,
                ],
            ),
        )
        self._refresh_inventory()
        return view

    def _refresh_inventory(self, e=None):
        category = self.inventory_category.value
        search = (self.inventory_search.value or "").strip().lower()
        products = self.db.list_products(category=None if category == "all" else category)
        if search:
            products = [
                product for product in products
                if search in product["name"].lower()
                or search in product["code"].lower()
                or search in (product.get("supplier") or "").lower()
            ]
        self.inventory_rows.controls = []

        if not products:
            self.inventory_rows.controls.append(
                ft.Card(
                    elevation=0,
                    bgcolor=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(
                        radius=16,
                        side=ft.BorderSide(width=1, color="#E0E2EC"),
                    ),
                    content=ft.Container(
                        padding=24,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.SEARCH_OFF, size=36, color="#72777F"),
                                ft.Text("Không tìm thấy vật tư phù hợp", color="#72777F", size=14),
                            ],
                        ),
                    ),
                )
            )
        else:
            cat_labels = {
                "module": "Module LED",
                "power": "Nguồn",
                "card": "Card thu",
                "processor": "Bộ xử lý",
                "frame": "Khung",
                "service": "Dịch vụ",
            }
            for product in products:
                price_field = ft.TextField(
                    value=str(int(product["unit_price"])),
                    label="Đơn giá (đ)",
                    width=130,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    **InputPanel._field_style(),
                )
                cat_name = cat_labels.get(product["category"], product["category"])
                self.inventory_rows.controls.append(
                    ft.Card(
                        elevation=0,
                        bgcolor=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(
                            radius=16,
                            side=ft.BorderSide(width=1, color="#E0E2EC"),
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
                                                        bgcolor="#EDF0F5",
                                                        content=ft.Text(cat_name, size=11, weight=ft.FontWeight.BOLD, color="#006494"),
                                                    ),
                                                    ft.Text(product["code"], weight=ft.FontWeight.BOLD, size=13, color="#006494"),
                                                ],
                                            ),
                                            ft.Text(
                                                f"{product['unit_price']:,.0f} đ / {product['unit']}",
                                                weight=ft.FontWeight.BOLD,
                                                size=14,
                                                color="#191C1E",
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        product["name"],
                                        weight=ft.FontWeight.BOLD,
                                        size=14,
                                        color="#191C1E",
                                    ),
                                    ft.Row(
                                        wrap=True,
                                        spacing=12,
                                        controls=[
                                            ft.Row(
                                                spacing=4,
                                                controls=[
                                                    ft.Icon(ft.Icons.STOREFRONT_OUTLINED, size=14, color="#72777F"),
                                                    ft.Text(f"NCC: {product.get('supplier') or 'Chưa rõ'}", size=12, color="#72777F"),
                                                ],
                                            ),
                                            ft.Row(
                                                spacing=4,
                                                controls=[
                                                    ft.Icon(ft.Icons.ACCESS_TIME, size=14, color="#72777F"),
                                                    ft.Text(f"Cập nhật: {str(product.get('updated_at', '-'))[:10]}", size=12, color="#72777F"),
                                                ],
                                            ),
                                        ],
                                    ),
                                    ft.Divider(color="#E0E2EC", height=1),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            price_field,
                                            ft.Row(
                                                spacing=4,
                                                controls=[
                                                    ft.IconButton(
                                                        icon=ft.Icons.CHECK,
                                                        icon_color="#006494",
                                                        tooltip="Cập nhật giá nhanh",
                                                        width=36,
                                                        height=36,
                                                        style=ft.ButtonStyle(
                                                            bgcolor="#EDF0F5",
                                                            shape=ft.CircleBorder(),
                                                        ),
                                                        on_click=lambda e, code=product["code"], field=price_field: self._update_price(code, field),
                                                    ),
                                                    ft.IconButton(
                                                        icon=ft.Icons.EDIT_OUTLINED,
                                                        icon_color="#00687A",
                                                        tooltip="Chỉnh sửa thông tin",
                                                        width=36,
                                                        height=36,
                                                        style=ft.ButtonStyle(
                                                            bgcolor="#EDF0F5",
                                                            shape=ft.CircleBorder(),
                                                        ),
                                                        on_click=lambda e, p=product: self._open_edit_product(p),
                                                    ),
                                                    ft.IconButton(
                                                        icon=ft.Icons.DELETE_OUTLINE,
                                                        icon_color="#BA1A1A",
                                                        tooltip="Xóa vật tư",
                                                        width=36,
                                                        height=36,
                                                        style=ft.ButtonStyle(
                                                            bgcolor="#FFDAD6",
                                                            shape=ft.CircleBorder(),
                                                        ),
                                                        on_click=lambda e, code=product["code"]: self._delete_product(code),
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
        self.page.update()

    def _open_edit_product(self, product: Dict[str, Any]):
        cat_group, cat_ui = self._build_category_selector(default_value=product["category"])
        code = ft.TextField(label="Mã vật tư", value=product["code"], disabled=True, **InputPanel._field_style())
        name = ft.TextField(label="Tên vật tư", value=product["name"], **InputPanel._field_style())
        price = ft.TextField(label="Đơn giá (VNĐ)", value=str(int(product["unit_price"])), keyboard_type=ft.KeyboardType.NUMBER, **InputPanel._field_style())
        unit = ft.TextField(label="Đơn vị tính", value=product.get("unit", "pcs"), **InputPanel._field_style())
        supplier = ft.TextField(label="Nhà cung cấp", value=product.get("supplier", ""), **InputPanel._field_style())

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.EDIT_NOTE, color="#006494"),
                    ft.Text("Chỉnh sửa vật tư", weight=ft.FontWeight.BOLD),
                ],
            ),
            content=ft.Column(
                [cat_ui, code, name, price, unit, supplier],
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
                        dialog, product["code"], cat_group, name, price, unit, supplier
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

    def _save_edit_product(self, dialog, code, category, name, price, unit, supplier):
        try:
            self.db.update_product(code, {
                "name": name.value.strip(),
                "category": category.value,
                "unit": unit.value.strip() or "pcs",
                "unit_price": float(price.value.replace(",", ".")),
                "supplier": supplier.value.strip(),
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
        err_msg = ft.Text("", color=ft.Colors.RED_700, size=12, visible=False)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.ADD_BOX_OUTLINED, color="#006494"),
                    ft.Text("Thêm vật tư mới", weight=ft.FontWeight.BOLD),
                ],
            ),
            content=ft.Column(
                [cat_ui, code, name, price, unit, supplier, err_msg],
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
                        dialog, cat_group, code, name, price, unit, supplier, err_msg
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

    def _create_product(self, dialog, category, code, name, price, unit, supplier, err_msg=None):
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
        except ValueError:
            if err_msg:
                err_msg.value = "Đơn giá không hợp lệ!"
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
                "environment": "both",
                "spec_json": {},
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

    def _to_float(self, value: Any) -> float:
        try:
            number = float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            raise ValueError("Vui lòng nhập số hợp lệ cho kích thước và chi phí.")
        if number < 0:
            raise ValueError("Giá trị không được nhỏ hơn 0.")
        return number

    def _get_selected(self, code: str, category: str) -> Dict[str, Any]:
        return self.db.get_product_by_code(code) or (
            self.db.list_products(category=category) or [{}]
        )[0]

    def recalculate(self):
        form = self.input_panel.get_values()
        module = self._get_selected(form["module_code"], "module")
        power = self._get_selected(form["power_code"], "power")
        card = self._get_selected(form["card_code"], "card")
        frame = self._get_selected(form["frame_code"], "frame")
        processors = self.db.list_products(category="processor")
        try:
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
            self.preview_panel.update_quote(self.quote_data)
            self.message.value = ""
        except ValueError as exc:
            self.quote_data = {}
            self.message.value = str(exc)
            self.message.color = ft.Colors.RED_700
        self.preview_panel.message.value = self.message.value
        self.page.update()

    def on_input_change(self, e):
        self.recalculate()

    def on_load_preset(self, name: str):
        presets = {
            "Màn hình Hội trường P2.5": {
                "environment": "indoor", "module_code": "M-P2.5-IN",
                "width_m": "4", "height_m": "2.5",
            },
            "Màn hình Outdoor P4": {
                "environment": "outdoor", "module_code": "M-P4-OUT",
                "width_m": "6", "height_m": "3",
            },
        }
        if name and name.startswith("saved:"):
            saved = self.db.get_configuration(int(name.split(":", 1)[1]))
            if saved:
                self.input_panel.set_values(saved["payload"])
                self.recalculate()
        elif name in presets:
            self.input_panel.set_values(presets[name])
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
        self.message.value = "Đã lưu cấu hình mẫu vào SQLite."
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
