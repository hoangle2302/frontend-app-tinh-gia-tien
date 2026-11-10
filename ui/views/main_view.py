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


class MainView:
    def __init__(self, page: ft.Page, db: DBManager, on_logout: Callable = None):
        self.page = page
        self.db = db
        self.on_logout = on_logout
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
        self.input_panel.expand = True
        self.left_container = ft.Container(
            content=self.input_panel,
            expand=True,
        )
        # Thanh áp dụng cấu hình cố định phía dưới tab Lập dự toán
        self._total_texts = []
        quote_bar = self._build_apply_bar()
        self.quote_view = ft.Container(
            padding=ft.Padding(8, 4, 8, 0),
            content=ft.Column(
                spacing=8,
                expand=True,
                controls=[self.left_container, quote_bar],
            ),
            expand=True,
        )
        # Trạng thái tab Linh kiện
        self._inv_filter = "all"
        self._inv_selected = None
        self._inv_qty = 1
        self.selected_quote_ids = set()
        self.select_mode = False
        self.detail_mode = False
        self.active_detail_item = None
        self.inventory_view = self._build_inventory_view()
        self.summary_view = self._build_summary_view()
        self.history_view = self._build_history_view()
        self.list_view = self._build_list_view()
        self.profile_view = ProfileView(
            page=self.page,
            db=self.db,
            on_profile_updated=self._on_profile_updated,
            on_logout=self.on_logout,
        )

        # View container chứa trang hiện tại
        self.view_container = ft.Container(
            content=self.quote_view,
            expand=True,
        )

        # Nút hành động nổi (FAB menu mini) ở phía trên thanh NavigationBar
        self.action_menu_btn = self._build_action_menu_button()

        # Thanh Menu Navigation Bar đặt ở dưới cùng chuẩn Material 3
        self.nav_bar = ft.NavigationBar(
            selected_index=0,
            height=65,
            bgcolor="#FFFFFF",
            indicator_color="#E8EEFF",
            on_change=self._on_nav_change,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.EDIT_NOTE_OUTLINED,
                    selected_icon=ft.Icons.EDIT_NOTE,
                    label="Lập dự toán",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.WIDGETS_OUTLINED,
                    selected_icon=ft.Icons.WIDGETS,
                    label="Linh kiện",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                    selected_icon=ft.Icons.RECEIPT_LONG,
                    label="Tổng hợp",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.FORMAT_LIST_BULLETED_OUTLINED,
                    selected_icon=ft.Icons.FORMAT_LIST_BULLETED,
                    label="Danh sách",
                ),
            ],
        )

        self.layout = ft.Stack(
            expand=True,
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        self.view_container,
                        ft.Divider(height=1, thickness=1, color="#E2E8F0"),
                        self.nav_bar,
                    ],
                ),
                self.action_menu_btn,
            ],
        )

        self.tabs = self.layout
        self._mounted = False
        self.page.on_resize = self._on_resize
        self._on_resize()
        self.recalculate()

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
                            ft.Text(title, size=14, weight=ft.FontWeight.W_600, color="#64748B"),
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
            "surface": "#1D2024" if is_dark else ft.Colors.WHITE,
            "surface_card": "#1D2024" if is_dark else ft.Colors.WHITE,
            "field": ft.Colors.TRANSPARENT,
            "primary_text": "#E0E2E8" if is_dark else "#0F172A",
            "secondary_text": "#8C9199" if is_dark else "#64748B",
            "border": "#42474E" if is_dark else "#E2E8F0",
            "card_chip": "#272A2E" if is_dark else "#F1F5F9",
            "icon": "#8C9199" if is_dark else "#64748B",
        }

        if hasattr(self, "nav_bar"):
            self.nav_bar.bgcolor = "#111827" if is_dark else "#FFFFFF"
            self.nav_bar.indicator_color = "#004B70" if is_dark else "#E8EEFF"

        def visit(control):
            if isinstance(control, ft.Card):
                control.bgcolor = palette["surface_card"]
                if control.shape and isinstance(control.shape, ft.RoundedRectangleBorder):
                    control.shape.side = ft.BorderSide(width=1, color=palette["border"])
            elif isinstance(control, ft.Container):
                # Đổi màu nền cho các container card trong theme tối
                bg = getattr(control, "bgcolor", None)
                if bg in [ft.Colors.WHITE, "#F8FAFC", "#EFF6FF", "#F0F5FF"]:
                    if is_dark:
                        control.bgcolor = "#2A2E33" if bg in ["#F8FAFC", "#EFF6FF", "#F0F5FF"] else palette["surface_card"]
                elif bg in ["#1D2024", "#2A2E33"] and not is_dark:
                    control.bgcolor = ft.Colors.WHITE
                if getattr(control, "border", None):
                    control.border = ft.Border.all(1, palette["border"])
            if isinstance(control, ft.Text):
                if getattr(control, "color", None) not in {"#BA1A1A", "#2563EB", "#8FCDFF"}:
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
                        side=ft.BorderSide(width=2, color="#8FCDFF" if is_dark else "#2563EB"),
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
                        side=ft.BorderSide(width=2, color="#8FCDFF" if is_dark else "#2563EB"),
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
                        fill_color="#2563EB",
                    )
                    for val, lbl in options
                ],
            ),
        )
        container = ft.Container(
            padding=ft.Padding(10, 8, 10, 8),
            border=ft.Border.all(1, "#CBD5E1"),
            border_radius=12,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Text("Nhóm vật tư *", size=12, color="#64748B", weight=ft.FontWeight.W_500),
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
                                bgcolor="#2563EB",
                                border_radius=2,
                            ),
                            ft.Column(
                                spacing=1,
                                controls=[
                                    ft.Text("Lịch sử báo giá", size=20, weight=ft.FontWeight.BOLD, color="#0F172A"),
                                    ft.Text("Theo dõi trạng thái, mở lại hoặc xuất lại các báo giá đã tạo", size=12, color="#64748B"),
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
                            ft.Text("Tổng báo giá", size=11, color="#64748B", weight=ft.FontWeight.W_500),
                            ft.Text(f"{total_count} bản ghi", size=14, weight=ft.FontWeight.BOLD, color="#0F172A"),
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
                    bgcolor="#E8EEFF",
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
                        side=ft.BorderSide(width=1, color="#E2E8F0"),
                    ),
                    content=ft.Container(
                        padding=24,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.HISTORY_TOGGLE_OFF, size=36, color="#64748B"),
                                ft.Text("Chưa có báo giá nào trong danh sách", color="#64748B", size=14),
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
                "Đã gửi": ("#E8EEFF", "#004B70"),
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
                            side=ft.BorderSide(width=1, color="#E2E8F0"),
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
                                                        color="#2563EB",
                                                    ),
                                                ],
                                            ),
                                            ft.Text(
                                                f"{item['total']:,.0f} đ",
                                                weight=ft.FontWeight.BOLD,
                                                size=15,
                                                color="#2563EB",
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        f"Khách hàng: {item.get('customer_name') or 'Chưa cập nhật'}"
                                        + (f" • Dự án: {item.get('project_name')}" if item.get('project_name') else ""),
                                        size=13,
                                        color="#0F172A",
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
                                                color="#64748B",
                                            ),
                                            ft.Text(
                                                f"Ngày: {str(item.get('created_at', ''))[:16]}",
                                                size=11,
                                                color="#64748B",
                                            ),
                                        ],
                                    ),
                                    ft.Divider(color="#E2E8F0", height=1),
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

    # ------------------------------------------------------------------
    # [UI] Button tròn nhỏ chứa menu thao tác trên thanh navigation bar
    # ------------------------------------------------------------------
    def _build_action_menu_button(self):
        menu_items = [
            ft.PopupMenuItem(
                icon=ft.Icons.ADD,
                content=ft.Text("Tạo mới", size=13, weight=ft.FontWeight.W_600),
                on_click=lambda e: self._action_create_new(),
            ),
            ft.PopupMenuItem(
                icon=ft.Icons.EDIT_OUTLINED,
                content=ft.Text("Sửa", size=13),
                on_click=lambda e: self._action_edit_selected(),
            ),
            ft.PopupMenuItem(
                icon=ft.Icons.CLOSE,
                content=ft.Text("Xóa", size=13, color="#DC2626"),
                on_click=lambda e: self._action_delete_selected(),
            ),
            ft.PopupMenuItem(
                icon=ft.Icons.SEARCH,
                content=ft.Text("Tìm", size=13),
                on_click=lambda e: self._action_focus_search(),
            ),
            ft.PopupMenuItem(
                icon=ft.Icons.VISIBILITY_OUTLINED,
                content=ft.Text("Xem", size=13),
                on_click=lambda e: self._action_view_selected(),
            ),
            ft.PopupMenuItem(
                icon=ft.Icons.CONTENT_COPY_OUTLINED,
                content=ft.Text("Sao chép", size=13),
                on_click=lambda e: self._action_clone_selected(),
            ),
            ft.PopupMenuItem(
                icon=ft.Icons.DESELECT_OUTLINED,
                content=ft.Text("Bỏ chọn", size=13),
                on_click=lambda e: self._action_deselect_all(),
            ),
            ft.PopupMenuItem(
                icon=ft.Icons.REFRESH,
                content=ft.Text("Làm mới", size=13),
                on_click=lambda e: self._action_refresh_all(),
            ),
        ]

        action_btn = ft.PopupMenuButton(
            icon=ft.Icons.APPS_ROUNDED,
            icon_color=ft.Colors.WHITE,
            icon_size=18,
            tooltip="Menu thao tác nhanh",
            items=menu_items,
        )

        # Nút nổi Floating Action Button ở góc dưới phải sát trên NavigationBar, không chiếm diện tích layout
        return ft.Container(
            right=12,
            bottom=72,
            content=ft.Container(
                width=34,
                height=34,
                border_radius=17,
                bgcolor="#2563EB",
                shadow=ft.BoxShadow(blur_radius=6, color="#602563EB", offset=ft.Offset(0, 2)),
                alignment=ft.Alignment(0, 0),
                content=action_btn,
            ),
        )

    # ------------------------------------------------------------------
    # Các hành động của menu thao tác nhanh & chế độ chọn nhiều mục
    # ------------------------------------------------------------------
    def _action_create_new(self):
        self._go_tab(0)
        self.input_panel.project_name.value = ""
        self.input_panel.customer_name.value = ""
        self.input_panel.customer_phone.value = ""
        self.input_panel.num_modules_w = 8
        self.input_panel.num_modules_h = 4
        self.input_panel.num_reserve_modules = 2
        self.input_panel.txt_modules_w.value = "8"
        self.input_panel.txt_modules_h.value = "4"
        self.input_panel.txt_reserve_modules.value = "2"
        self.input_panel.additional_items.clear()
        self.input_panel.additional_rows.controls.clear()
        self.recalculate()
        if hasattr(self, "page") and self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text("Đã tạo mới cấu hình dự toán!"), bgcolor="#2563EB")
            self.page.snack_bar.open = True
            self.page.update()

    def _enable_select_mode(self, action_desc: str = ""):
        self.select_mode = True
        self._go_tab(3)
        self._refresh_list_view()
        if hasattr(self, "page") and self.page:
            msg = f"Đã mở chức năng chọn. Vui lòng tích chọn dự toán để {action_desc}." if action_desc else "Đã mở chức năng chọn."
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="#2563EB")
            self.page.snack_bar.open = True
            self.page.update()

    def _action_edit_selected(self):
        if not self.select_mode or len(self.selected_quote_ids) == 0:
            self._enable_select_mode("chỉnh sửa")
        elif len(self.selected_quote_ids) == 1:
            item_id = list(self.selected_quote_ids)[0]
            self.select_mode = False
            self.selected_quote_ids.clear()
            self._load_history(item_id)
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Đang mở chỉnh sửa dự toán đã chọn."), bgcolor="#2563EB")
                self.page.snack_bar.open = True
                self.page.update()
        else:
            self._go_tab(3)
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Vui lòng chỉ chọn đúng 1 dự toán để chỉnh sửa!"), bgcolor="#DC2626")
                self.page.snack_bar.open = True
                self.page.update()

    def _action_delete_selected(self):
        if not self.select_mode or len(self.selected_quote_ids) == 0:
            self._enable_select_mode("xóa")
        else:
            count = len(self.selected_quote_ids)
            for item_id in list(self.selected_quote_ids):
                self.db.delete_quote_history(item_id)
            self.select_mode = False
            self.selected_quote_ids.clear()
            self._refresh_list_view()
            self._refresh_history()
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Đã xóa thành công {count} dự toán!"), bgcolor="#DC2626")
                self.page.snack_bar.open = True
                self.page.update()

    def _action_focus_search(self):
        self._go_tab(3)
        if hasattr(self, "list_search") and hasattr(self, "page") and self.page:
            try:
                if hasattr(self.page, "run_task"):
                    self.page.run_task(self.list_search.focus)
                else:
                    self.list_search.autofocus = True
                    self.page.update()
            except Exception:
                pass

    def _action_view_selected(self):
        if not self.select_mode or len(self.selected_quote_ids) == 0:
            self._enable_select_mode("xem")
        else:
            item_id = list(self.selected_quote_ids)[0]
            self.select_mode = False
            self.selected_quote_ids.clear()
            self._open_quote_detail_view(item_id)

    def _action_clone_selected(self):
        if not self.select_mode or len(self.selected_quote_ids) == 0:
            self._enable_select_mode("sao chép")
        else:
            count = 0
            last_new_num = ""
            for item_id in list(self.selected_quote_ids):
                item = self.db.get_quote_history(item_id)
                if item:
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
                    last_new_num = new_item.get("quote_number") if new_item else f"DT-{new_id:03d}"
                    count += 1
            self.select_mode = False
            self.selected_quote_ids.clear()
            self._refresh_list_view()
            self._refresh_history()
            if hasattr(self, "page") and self.page:
                msg = (
                    f"Đã sao chép thành công và tạo mới {count} dự toán!"
                    if count > 1
                    else f"Đã sao chép thành công tạo mới: {last_new_num}!"
                )
                self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="#16A34A")
                self.page.snack_bar.open = True
                self.page.update()

    def _action_refresh_all(self):
        self.select_mode = False
        self.selected_quote_ids.clear()
        self._refresh_options()
        self._refresh_inventory()
        self._refresh_history()
        self._refresh_list_view()
        self.recalculate()
        if hasattr(self, "page") and self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text("Đã làm mới toàn bộ dữ liệu!"), bgcolor="#16A34A")
            self.page.snack_bar.open = True
            self.page.update()

    def _action_deselect_all(self):
        self.select_mode = False
        self.selected_quote_ids.clear()
        self._refresh_list_view()
        if hasattr(self, "page") and self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text("Đã ẩn chức năng chọn. Mọi thứ trở lại bình thường!"), bgcolor="#2563EB")
            self.page.snack_bar.open = True
            self.page.update()

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

    def _toggle_select_all(self, e):
        history = self._get_filtered_list_history()
        if e.control.value:
            self.selected_quote_ids = {item["id"] for item in history}
        else:
            self.selected_quote_ids.clear()
        self._refresh_list_view()

    def _toggle_select_item(self, item_id: int, value: bool = None):
        if value is None:
            if item_id in self.selected_quote_ids:
                self.selected_quote_ids.remove(item_id)
            else:
                self.selected_quote_ids.add(item_id)
        else:
            if value:
                self.selected_quote_ids.add(item_id)
            else:
                self.selected_quote_ids.discard(item_id)
        self._refresh_list_view()

    # ------------------------------------------------------------------
    # [UI] Tab "Danh sách" – Bảng danh sách dự toán với các thông số:
    # Đơn vị, Ngày, Số, Tên module, Diễn giải & Chọn / Thao tác nhiều mục
    # ------------------------------------------------------------------
    def _build_list_view(self):
        self.list_search = ft.TextField(
            label="Tìm kiếm theo số, module, khách hàng...",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=lambda e: self._refresh_list_view(),
            **InputPanel._field_style(),
        )
        self.list_count_text = ft.Text("", size=12, weight=ft.FontWeight.W_600, color="#64748B")
        self.list_subtitle_text = ft.Text("Bảng tổng hợp hồ sơ dự toán và thông số kỹ thuật", size=12, color="#64748B")
        self.select_all_cb = ft.Checkbox(
            label="Chọn tất cả",
            value=False,
            active_color="#2563EB",
            on_change=self._toggle_select_all,
        )
        self.select_count_text = ft.Text("Đã chọn: 0", size=12, color="#2563EB", weight=ft.FontWeight.BOLD)

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
                                color="#DC2626",
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
                        color="#2563EB",
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
                                    bgcolor="#DC2626",
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
                                    side=ft.BorderSide(1, "#CBD5E1"),
                                    color="#64748B",
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
                                    ft.Text("Danh sách dự toán", size=22, weight=ft.FontWeight.W_800, color="#0F172A"),
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
                            ft.Icon(ft.Icons.INBOX_OUTLINED, size=40, color="#94A3B8"),
                            ft.Text("Chưa có dự toán nào phù hợp", color="#64748B", size=14),
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
                bgcolor="#F8FAFC",
                border_radius=8,
                content=ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(
                            spacing=4,
                            controls=[
                                ft.Icon(icon, size=13, color="#64748B") if icon else ft.Container(width=0),
                                ft.Text(label, size=11, color="#64748B", weight=ft.FontWeight.W_500),
                            ],
                        ),
                        ft.Text(str(val), size=13, weight=ft.FontWeight.W_700, color="#0F172A", no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
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
                                icon_color="#2563EB",
                                on_click=lambda e: self._close_detail_view(),
                            ),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text(f"Chi tiết {q_num}", size=18, weight=ft.FontWeight.W_800, color="#0F172A"),
                                            ft.Container(
                                                padding=ft.Padding(6, 2, 6, 2),
                                                bgcolor="#ECFDF5",
                                                border_radius=6,
                                                border=ft.Border.all(1, "#A7F3D0"),
                                                content=ft.Text("CHỈ XEM", size=10, weight=ft.FontWeight.BOLD, color="#059669"),
                                            ),
                                        ],
                                    ),
                                    ft.Text(f"Ngày tạo: {date_str} • Trạng thái: {status_val}", size=11, color="#64748B"),
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
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), bgcolor="#2563EB"),
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
            border=ft.Border.all(1, "#E2E8F0"),
            border_radius=12,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row([ft.Icon(ft.Icons.BUSINESS, size=16, color="#2563EB"), ft.Text("Thông tin khách hàng & dự án", size=13, weight=ft.FontWeight.W_700, color="#0F172A")]),
                    ft.Row([_info_cell("Dự án", proj_name), _info_cell("Khách hàng", cust_name)]),
                    ft.Row([_info_cell("Số điện thoại", phone), _info_cell("Địa chỉ", address)]),
                ],
            ),
        )

        card_specs = ft.Container(
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, "#E2E8F0"),
            border_radius=12,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row([ft.Icon(ft.Icons.SETTINGS, size=16, color="#2563EB"), ft.Text("Thông số kỹ thuật màn hình", size=13, weight=ft.FontWeight.W_700, color="#0F172A")]),
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
                        bgcolor="#F8FAFC" if idx % 2 == 1 else ft.Colors.WHITE,
                        border_radius=6,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(f"{idx}. {cit.get('name')}", size=12, weight=ft.FontWeight.W_600, color="#0F172A", expand=True),
                                ft.Text(f"{qty_val:g} {cit.get('unit', '')}", size=12, color="#64748B", width=70, text_align=ft.TextAlign.RIGHT),
                                ft.Text(f"{price_val:,.0f} đ".replace(",", "."), size=12, color="#475569", width=95, text_align=ft.TextAlign.RIGHT),
                                ft.Text(f"{sub_val:,.0f} đ".replace(",", "."), size=12, weight=ft.FontWeight.W_700, color="#0F172A", width=105, text_align=ft.TextAlign.RIGHT),
                            ],
                        ),
                    )
                )
        else:
            bom_rows.append(
                ft.Container(
                    padding=12,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text("Dữ liệu linh kiện lưu trữ theo cấu hình tổng thể.", size=12, color="#64748B"),
                )
            )

        card_bom = ft.Container(
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, "#E2E8F0"),
            border_radius=12,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row([ft.Icon(ft.Icons.LIST_ALT, size=16, color="#2563EB"), ft.Text("Bảng kê linh kiện dự toán (BOM)", size=13, weight=ft.FontWeight.W_700, color="#0F172A")]),
                    ft.Container(
                        padding=ft.Padding(8, 4, 8, 4),
                        bgcolor="#E2E8F0",
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
                            ft.Text(f"Thuế VAT: {vat_pct}% • Lợi nhuận: {profit_pct}%", size=11, color="#64748B"),
                        ],
                    ),
                    ft.Text(f"{total_val:,.0f} đ".replace(",", "."), size=22, weight=ft.FontWeight.W_900, color="#2563EB"),
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
            border_card = ft.Border.all(2, "#2563EB")
        else:
            bg_card = ft.Colors.WHITE
            border_card = ft.Border.all(1, "#E2E8F0")

        # Hàng 1 bên trái: Có checkbox chỉ khi đang ở select_mode
        h1_left_controls = []
        if self.select_mode:
            h1_left_controls.append(
                ft.Checkbox(
                    value=is_selected,
                    active_color="#2563EB",
                    on_change=lambda e, i_id=item_id: self._toggle_select_item(i_id, e.control.value),
                )
            )
        h1_left_controls.extend([
            ft.Container(
                padding=ft.Padding(8, 2, 8, 2),
                bgcolor="#E8EEFF" if not (self.select_mode and is_selected) else "#DBEAFE",
                border_radius=6,
                content=ft.Text(number_str, size=12, weight=ft.FontWeight.W_700, color="#2563EB"),
            ),
            ft.Text(f"Đơn vị: {unit_str}", size=11, color="#64748B"),
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
                            ft.Text(f"Ngày: {date_str}", size=11, color="#64748B"),
                        ],
                    ),
                    # Hàng 2: Tên module & Giá
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Icon(ft.Icons.GRID_VIEW, size=16, color="#2563EB"),
                                    ft.Text(f"Tên module: {module_str}", size=14, weight=ft.FontWeight.W_700, color="#0F172A"),
                                ],
                            ),
                            ft.Text(f"{total_val:,.0f} đ".replace(",", "."), size=14, weight=ft.FontWeight.W_800, color="#2563EB"),
                        ],
                    ),
                    # Hàng 3: Diễn giải
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=15, color="#64748B"),
                            ft.Text(f"Diễn giải: {explanation}", size=12, color="#475569", expand=True),
                        ],
                    ),
                    # Hàng 4: Nút Xem / Sửa nhanh
                    ft.Divider(height=1, color="#E2E8F0" if not (self.select_mode and is_selected) else "#BFDBFE"),
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
                bgcolor="#16A34A",
            )
            self.page.snack_bar.open = True
            self.page.update()

    # ------------------------------------------------------------------
    # [UI] Thanh bottom bar cố định phía dưới (chuẩn theo mẫu UI)
    # ------------------------------------------------------------------
    def _build_apply_bar(self):
        self.apply_mode_text = ft.Text("Chế độ tự động", size=11, color="#64748B")
        self.apply_size_text = ft.Text("2.560 × 640 mm", size=12, weight=ft.FontWeight.W_700, color="#0F172A")
        return ft.Container(
            padding=ft.Padding(14, 10, 14, 10),
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, "#E2E8F0"),
            border_radius=14,
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[self.apply_mode_text, self.apply_size_text],
                    ),
                    ft.FilledButton(
                        "Áp dụng cấu hình",
                        icon=ft.Icons.ARROW_FORWARD,
                        height=46,
                        expand=True,
                        on_click=lambda e: self._go_tab(1),
                        style=InputPanel._primary_button_style(),
                    ),
                    ft.Text(
                        "Rà soát các mục chưa thiết lập trước khi chuyển sang bảng dự toán.",
                        size=10,
                        color="#64748B",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

    def _build_total_bar(self, button_text: str, button_icon, on_click, outlined: bool = False):
        total_text = ft.Text("0 đ", size=22, weight=ft.FontWeight.W_800, color="#0F172A")
        count_text = ft.Text("", size=12, color="#64748B")
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
                    side=ft.BorderSide(1, "#CBD5E1"),
                    color="#2563EB",
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
            border=ft.Border.all(1, "#E2E8F0"),
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
                                    ft.Text("Tổng dự toán tạm tính", size=12, color="#64748B"),
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

    # ------------------------------------------------------------------
    # [UI] Tab "Linh kiện" – Danh mục linh kiện (tìm kiếm, lọc nhóm, thêm vào dự toán)
    # ------------------------------------------------------------------
    CATEGORY_LABELS = [
        ("module", "Module LED"),
        ("power", "Nguồn"),
        ("card", "Card thu"),
        ("processor", "Bộ xử lý"),
        ("frame", "Khung"),
        ("service", "Dịch vụ"),
    ]
    CATEGORY_ICONS = {
        "module": ft.Icons.GRID_VIEW,
        "power": ft.Icons.BOLT,
        "card": ft.Icons.MEMORY,
        "processor": ft.Icons.DEVELOPER_BOARD,
        "frame": ft.Icons.CROP_FREE,
        "service": ft.Icons.CONSTRUCTION,
    }

    def _create_quote_and_go_list(self, e=None):
        """Tạo báo giá từ cấu hình hiện tại, lưu vào DB và chuyển thẳng sang tab Danh sách."""
        if not self.quote_data:
            self.recalculate()
        if not self.quote_data:
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Chưa có dữ liệu dự toán để tạo!"), bgcolor="#DC2626")
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

        self.selected_quote_ids.clear()
        self.select_mode = False
        self._refresh_history()
        self._refresh_list_view()
        self._go_tab(3)

        if hasattr(self, "page") and self.page:
            q_num = saved.get("quote_number") if saved else f"DT-{history_id:03d}"
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Đã tạo báo giá {q_num} thành công và lưu vào Danh sách!"),
                bgcolor="#16A34A",
            )
            self.page.snack_bar.open = True
            self.page.update()

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
        self.inventory_count = ft.Text("", size=12, weight=ft.FontWeight.W_600, color="#0F172A")
        self.inventory_rows = ft.Column(spacing=10)
        self.inventory_project = ft.Text("Chưa đặt tên dự án", size=13, weight=ft.FontWeight.W_600, color="#0F172A")
        self.inventory_project_sub = ft.Text("", size=11, color="#64748B")
        add_button = ft.IconButton(
            icon=ft.Icons.ADD,
            tooltip="Thêm vật tư mới vào danh mục",
            icon_color=ft.Colors.WHITE,
            bgcolor="#2563EB",
            width=36,
            height=36,
            style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0),
            on_click=self._open_add_product,
        )
        create_button = ft.FilledButton(
            "Tạo",
            icon=ft.Icons.CHECK,
            height=36,
            style=ft.ButtonStyle(
                bgcolor="#2563EB",
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(12, 0, 14, 0),
            ),
            on_click=self._create_quote_and_go_list,
        )
        project_banner = ft.Container(
            padding=ft.Padding(12, 10, 12, 10),
            bgcolor="#E8EEFF",
            border=ft.Border.all(1, "#C7D6FE"),
            border_radius=12,
            ink=True,
            on_click=lambda e: self._go_tab(2),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, color="#2563EB", size=20),
                    ft.Column(
                        spacing=0,
                        expand=True,
                        controls=[self.inventory_project, self.inventory_project_sub],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#2563EB"),
                ],
            ),
        )
        inv_total_text = ft.Text("0 đ", size=22, weight=ft.FontWeight.W_800, color="#0F172A")
        inv_count_text = ft.Text("", size=12, color="#64748B")
        self._total_texts.append((inv_total_text, inv_count_text))
        total_bar = ft.Container(
            padding=ft.Padding(14, 10, 14, 10),
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, "#E2E8F0"),
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
                                    ft.Text("Tổng dự toán tạm tính", size=12, color="#64748B"),
                                    inv_total_text,
                                ],
                            ),
                            inv_count_text,
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
                                    side=ft.BorderSide(1, "#CBD5E1"),
                                    color="#2563EB",
                                ),
                                on_click=lambda e: self._go_tab(0),
                            ),
                            ft.FilledButton(
                                "Tạo báo giá",
                                icon=ft.Icons.CHECK,
                                height=44,
                                expand=True,
                                style=InputPanel._primary_button_style(),
                                on_click=self._create_quote_and_go_list,
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
                                            ft.Text("Danh mục linh kiện", size=22, weight=ft.FontWeight.W_800, color="#0F172A"),
                                            ft.Text("Tìm đúng linh kiện, thêm nhanh vào dự toán.", size=12, color="#64748B"),
                                        ],
                                    ),
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            add_button,
                                            create_button,
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
                    total_bar,
                ],
            ),
        )
        self._refresh_inventory()
        return view

    def _set_inventory_filter(self, key: str):
        self._inv_filter = key
        self._inv_selected = None
        self._inv_qty = 1
        self._refresh_inventory()

    def _toggle_inventory_item(self, code: str):
        if self._inv_selected == code:
            self._inv_selected = None
        else:
            self._inv_selected = code
            self._inv_qty = 1
        self._refresh_inventory()

    def _change_inventory_qty(self, delta: int):
        self._inv_qty = max(1, self._inv_qty + delta)
        self._refresh_inventory()

    def _add_to_estimate(self, product: Dict[str, Any]):
        self.input_panel.add_additional(product["name"], self._inv_qty, product["unit_price"])
        self.message.value = f"Đã thêm {self._inv_qty} × {product['name']} vào dự toán."
        self.message.color = ft.Colors.GREEN_700
        self._inv_selected = None
        self._inv_qty = 1
        self.recalculate()
        self._refresh_inventory()
        self.page.snack_bar = ft.SnackBar(ft.Text(self.message.value), bgcolor="#2563EB")
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
                bgcolor="#2563EB" if self._inv_filter == key else ft.Colors.WHITE,
                border=ft.Border.all(1, "#2563EB" if self._inv_filter == key else "#E2E8F0"),
                on_click=lambda e, k=key: self._set_inventory_filter(k),
                content=ft.Text(
                    f"{label} · {counts.get(key, 0)}",
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE if self._inv_filter == key else "#0F172A",
                ),
            )
            for key, label in chips
        ]

        products = [p for p in all_products if self._inv_filter in ("all", p["category"])]
        if search:
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
                            ft.Icon(ft.Icons.SEARCH_OFF, size=36, color="#64748B"),
                            ft.Text("Không tìm thấy vật tư phù hợp", color="#64748B", size=14),
                        ],
                    ),
                )
            )
        for product in products:
            self.inventory_rows.controls.append(self._build_product_card(product))
        self._refresh_total_bars()
        self.page.update()

    def _build_product_card(self, product: Dict[str, Any]):
        selected = self._inv_selected == product["code"]
        in_estimate = self.input_panel.additional_qty_by_name(product["name"])
        icon = self.CATEGORY_ICONS.get(product["category"], ft.Icons.INVENTORY_2_OUTLINED)

        if in_estimate:
            status = ft.Text(f"✓ Đã có {in_estimate:g}", size=11, weight=ft.FontWeight.W_600, color="#16A34A")
        else:
            status = ft.Container()
        action = ft.FilledTonalButton(
            "Đang chọn" if selected else "Chọn",
            icon=ft.Icons.CHECK if selected else ft.Icons.ADD,
            height=34,
            style=ft.ButtonStyle(
                bgcolor="#E8EEFF",
                color="#2563EB",
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
                        ft.Text(product["name"], size=15, weight=ft.FontWeight.W_700, color="#0F172A"),
                        ft.Text(self._product_spec_line(product), size=11, color="#64748B"),
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
                    color="#0F172A",
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
                ft.Divider(color="#E2E8F0", height=1),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Số lượng thêm", size=13, color="#0F172A"),
                        ft.Container(
                            border=ft.Border.all(1, "#CBD5E1"),
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
                ft.Divider(color="#E2E8F0", height=1),
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
                                    icon_color="#2563EB",
                                    tooltip="Cập nhật giá nhanh",
                                    style=ft.ButtonStyle(bgcolor="#E8EEFF", shape=ft.CircleBorder()),
                                    on_click=lambda e, code=product["code"], field=price_field: self._update_price(code, field),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT_OUTLINED,
                                    icon_color="#00687A",
                                    tooltip="Chỉnh sửa thông tin",
                                    style=ft.ButtonStyle(bgcolor="#E8EEFF", shape=ft.CircleBorder()),
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
            border=ft.Border.all(1.5 if selected else 1, "#2563EB" if selected else "#E2E8F0"),
            content=ft.Column(spacing=10, controls=controls),
        )

    # ------------------------------------------------------------------
    # [UI] Tab "Tổng hợp" – Tổng hợp dự toán (chi phí, chiết khấu, VAT, ghi chú, xuất báo giá)
    # ------------------------------------------------------------------
    @staticmethod
    def _summary_row(label: str, value_text: ft.Text, bold: bool = False):
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(label, size=13, weight=ft.FontWeight.W_700 if bold else ft.FontWeight.W_400, color="#0F172A"),
                value_text,
            ],
        )

    def _build_summary_view(self):
        def money_text(size=13, bold=False, color="#0F172A"):
            return ft.Text("0 đ", size=size, weight=ft.FontWeight.W_800 if bold else ft.FontWeight.W_600, color=color)

        self.sum_code = ft.Text("DT-MỚI", size=12, color="#64748B")
        self.sum_name = ft.Text("Chưa đặt tên dự án", size=18, weight=ft.FontWeight.W_800, color="#0F172A")
        self.sum_total = ft.Text("0 đ", size=30, weight=ft.FontWeight.W_800, color="#2563EB")
        self.sum_total_note = ft.Text("", size=12, color="#64748B")
        self.sum_subtotal = money_text(bold=True)
        self.sum_subtotal_note = ft.Text("", size=12, color="#64748B")
        self.sum_profit = money_text()
        self.sum_transport = money_text()
        self.sum_discount_value = money_text()
        self.sum_before_vat = money_text(bold=True)
        self.sum_vat_value = money_text(bold=True)
        self.sum_grand = money_text(size=20, bold=True, color="#2563EB")

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

        def card(controls, bgcolor=ft.Colors.WHITE, border="#E2E8F0"):
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
                        content=ft.Text("Nháp", size=11, color="#64748B"),
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
                        ft.Text("TỔNG DỰ TOÁN", size=11, weight=ft.FontWeight.W_700, color="#2563EB"),
                        ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, color="#2563EB", size=18),
                    ],
                ),
                self.sum_total,
                self.sum_total_note,
            ],
            bgcolor="#E8EEFF",
            border="#C7D6FE",
        )
        cost_card = card([
            ft.Text("Các khoản chi phí", size=17, weight=ft.FontWeight.W_800, color="#0F172A"),
            self._summary_row("Tạm tính linh kiện", self.sum_subtotal, bold=True),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    self.sum_subtotal_note,
                    ft.TextButton("Chỉnh linh kiện ›", on_click=lambda e: self._go_tab(1)),
                ],
            ),
            ft.Divider(color="#E2E8F0", height=1),
            self.sum_install,
            self.sum_discount,
            self._summary_row("Lợi nhuận", self.sum_profit),
            self._summary_row("Vận chuyển", self.sum_transport),
            self._summary_row("Chiết khấu", self.sum_discount_value),
            ft.Divider(color="#E2E8F0", height=1),
            self._summary_row("Trước thuế", self.sum_before_vat, bold=True),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.sum_vat, self.sum_vat_value],
            ),
            ft.Divider(color="#E2E8F0", height=1),
            self._summary_row("Tổng cộng", self.sum_grand, bold=True),
        ])
        notes_card = card([self.sum_notes])
        export_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[ft.Text("Định dạng báo giá", size=13, color="#64748B"), self.sum_format],
        )
        export_button = ft.FilledButton(
            "Xuất báo giá",
            icon=ft.Icons.DOWNLOAD,
            height=48,
            expand=True,
            style=InputPanel._primary_button_style(),
            on_click=self._on_summary_export,
        )
        save_button = ft.OutlinedButton(
            "Lưu vào danh sách",
            icon=ft.Icons.SAVE_OUTLINED,
            height=48,
            expand=True,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                side=ft.BorderSide(1, "#CBD5E1"),
                color="#2563EB",
            ),
            on_click=self._create_quote_and_go_list,
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
                                    ft.Text("Tổng hợp dự toán", size=22, weight=ft.FontWeight.W_800, color="#0F172A"),
                                    ft.Text("Rà soát chi phí trước khi lưu và xuất báo giá.", size=12, color="#64748B"),
                                ],
                            ),
                            ft.FilledButton(
                                "Tạo báo giá",
                                icon=ft.Icons.CHECK,
                                height=36,
                                style=ft.ButtonStyle(
                                    bgcolor="#2563EB",
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                    padding=ft.Padding(12, 0, 14, 0),
                                ),
                                on_click=self._create_quote_and_go_list,
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
                    ft.Row([save_button]),
                    self.sum_message,
                    ft.Text("Chi tiết báo giá", size=17, weight=ft.FontWeight.W_800, color="#0F172A"),
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
                    ft.Icon(ft.Icons.EDIT_NOTE, color="#2563EB"),
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
                    ft.Icon(ft.Icons.ADD_BOX_OUTLINED, color="#2563EB"),
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
