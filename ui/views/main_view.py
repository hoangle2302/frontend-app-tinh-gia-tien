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
            content=ft.Card(
                content=self.input_panel,
                elevation=5,
                bgcolor=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=20),
            ),
            expand=True,
        )
        self.quote_view = ft.Container(
            padding=ft.Padding(8, 4, 8, 4),
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
                        divider_color=ft.Colors.BLUE_GREY_100,
                        indicator_color=ft.Colors.CYAN_600,
                        indicator_thickness=3,
                        scrollable=True,
                        label_padding=ft.Padding(16, 0, 16, 0),
                        label_text_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD),
                        tabs=[
                            ft.Tab(label="Báo giá"),
                            ft.Tab(label="Danh mục"),
                            ft.Tab(label="Lịch sử"),
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
            ft.Container(
                height=2,
                bgcolor="#00AEEF",
                margin=ft.Margin(0, 0, 0, 2),
            ),
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
            "surface": "#202B36" if is_dark else ft.Colors.WHITE,
            "field": "#263442" if is_dark else ft.Colors.WHITE,
            "primary_text": "#F3F4F6" if is_dark else "#1A1A1A",
            "secondary_text": "#B8C2CC" if is_dark else "#6B7280",
            "border": "#465564" if is_dark else "#E0E0E0",
            "icon": "#B8C2CC" if is_dark else "#4B5563",
        }

        def visit(control):
            if isinstance(control, (ft.Card, ft.Container)):
                if getattr(control, "bgcolor", None) not in {"#00AEEF", "#F5F7FA"}:
                    control.bgcolor = palette["surface"]
            if isinstance(control, ft.Text):
                control.color = palette["primary_text"]
            elif isinstance(control, ft.Icon):
                control.color = palette["icon"]
            elif isinstance(control, (ft.TextField, ft.Dropdown)):
                control.bgcolor = palette["field"]
                control.border = {
                    ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                        border_radius=10,
                        side=ft.BorderSide(color=palette["border"]),
                    ),
                    ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                        border_radius=10,
                        side=ft.BorderSide(color="#00B4D8"),
                    ),
                }
                control.label_style = ft.TextStyle(color=palette["secondary_text"])
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

    def _build_history_view(self):
        self.history_rows = ft.Column(spacing=8)
        self.history_search = ft.TextField(
            label="Tìm khách hàng, dự án hoặc số báo giá",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=self._refresh_history,
        )
        self.history_status = ft.Dropdown(
            label="Trạng thái",
            value="all",
            width=130,
            options=[
                ft.dropdown.Option("all", "Tất cả"),
                ft.dropdown.Option("Nh\u00e1p"),
                ft.dropdown.Option("Đã gửi"),
                ft.dropdown.Option("Chốt"),
                ft.dropdown.Option("Hủy"),
            ],
            on_select=self._refresh_history,
        )
        view = ft.Container(
            expand=True,
            padding=ft.Padding(20, 16, 20, 16),
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text("Lịch sử báo giá", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                    ft.Text(
                        "Lưu lại báo giá để mở lại, xuất lại hoặc tiếp tục chỉnh sửa.",
                        color=ft.Colors.BLUE_GREY_700,
                    ),
                    ft.Row([self.history_search, self.history_status], spacing=8, wrap=True),
                    ft.Card(
                        elevation=2,
                        bgcolor=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=16),
                        content=ft.Container(
                            padding=16,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.HISTORY, size=34, color=ft.Colors.CYAN_600),
                                    ft.Text("Các báo giá đã lưu sẽ hiển thị tại đây.", color=ft.Colors.BLUE_GREY_700),
                                    ft.OutlinedButton(
                                        "Tạo báo giá mới",
                                        icon=ft.Icons.ADD,
                                        on_click=self._open_quote_tab,
                                    ),
                                ],
                            ),
                        ),
                    ),
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
        for item in history:
            self.history_rows.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Row(
                            wrap=True,
                            controls=[
                                ft.Column(
                                    expand=True,
                                    controls=[
                                        ft.Text(item["quote_name"], weight=ft.FontWeight.BOLD),
                                        ft.Text(
                                            f"{item.get('quote_number') or 'Chưa có số'} • "
                                            f"{item['customer_name'] or 'Chưa có khách hàng'} • "
                                            f"{item.get('project_name') or 'Chưa có dự án'}"
                                        ),
                                        ft.Text(f"{item['total']:,.0f} VNĐ", color=ft.Colors.BLUE_700),
                                    ],
                                ),
                                ft.Dropdown(
                                    value=item.get("status", "Nh\u00e1p"),
                                    width=105,
                                    options=[
                                        ft.dropdown.Option("Nh\u00e1p"),
                                        ft.dropdown.Option("Đã gửi"),
                                        ft.dropdown.Option("Chốt"),
                                        ft.dropdown.Option("Hủy"),
                                    ],
                                    on_select=lambda e, item_id=item["id"]: self._update_history_status(item_id, e.control.value),
                                ),
                                ft.FilledButton(
                                    "Mở",
                                    icon=ft.Icons.OPEN_IN_NEW,
                                    on_click=lambda e, item_id=item["id"]: self._load_history(item_id),
                                ),
                                ft.OutlinedButton(
                                    "Nhân bản",
                                    icon=ft.Icons.CONTENT_COPY,
                                    on_click=lambda e, item_id=item["id"]: self._clone_history(item_id),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    tooltip="Xóa lịch sử",
                                    on_click=lambda e, item_id=item["id"]: self._delete_history(item_id),
                                ),
                            ],
                        ),
                    )
                )
            )
        self.history_rows.visible = bool(history)
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
        )
        self.inventory_search = ft.TextField(
            label="Tìm kiếm vật tư",
            hint_text="Nhập tên hoặc mã vật tư",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=self._refresh_inventory,
        )
        self.inventory_rows = ft.Column(spacing=8)
        add_button = ft.FilledButton(
            "Thêm",
            icon=ft.Icons.ADD,
            on_click=self._open_add_product,
            style=ft.ButtonStyle(
                padding=ft.Padding(10, 8, 10, 8),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )
        view = ft.Container(
            expand=True,
            padding=ft.Padding(20, 16, 20, 16),
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text("Quản lý linh kiện & bảng giá", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                    ft.Row([self.inventory_search, self.inventory_category], spacing=8),
                    ft.Row([add_button]),
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
                if search in product["name"].lower() or search in product["code"].lower()
            ]
        self.inventory_rows.controls = []
        for product in products:
            price = ft.TextField(
                value=str(int(product["unit_price"])),
                label="Đơn giá",
                width=105,
                keyboard_type=ft.KeyboardType.NUMBER,
            )
            self.inventory_rows.controls.append(
                ft.Card(
                    elevation=2,
                    bgcolor=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=14),
                    content=ft.Container(
                        padding=10,
                        content=ft.Row(
                            wrap=True,
                            controls=[
                                ft.Column(
                                    expand=True,
                                    controls=[
                                        ft.Text(product["name"], weight=ft.FontWeight.BOLD),
                                        ft.Text(
                                            f"{product['code']} • {product['category']} • {product['unit']}"
                                        ),
                                        ft.Text(
                                            f"NCC: {product.get('supplier') or 'Chưa cập nhật'} • "
                                            f"Cập nhật: {product.get('updated_at', '-')}",
                                            size=11,
                                            color=ft.Colors.BLUE_GREY_600,
                                        ),
                                    ],
                                ),
                                ft.Row(
                                    spacing=2,
                                    controls=[
                                        price,
                                        ft.IconButton(
                                            icon=ft.Icons.SAVE,
                                            icon_color=ft.Colors.BLUE_700,
                                            tooltip="Lưu đơn giá",
                                            on_click=lambda e, code=product["code"], field=price: self._update_price(code, field),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE_OUTLINE,
                                            icon_color=ft.Colors.RED_600,
                                            tooltip="Xóa vật tư",
                                            on_click=lambda e, code=product["code"]: self._delete_product(code),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    )
                )
            )
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
        category = ft.Dropdown(
            label="Nhóm vật tư",
            value="module",
            options=[
                ft.dropdown.Option("module", "Module LED"),
                ft.dropdown.Option("power", "Nguồn"),
                ft.dropdown.Option("card", "Card thu"),
                ft.dropdown.Option("processor", "Bộ xử lý"),
                ft.dropdown.Option("frame", "Khung"),
                ft.dropdown.Option("service", "Dịch vụ"),
            ],
        )
        code = ft.TextField(label="Mã vật tư")
        name = ft.TextField(label="Tên vật tư")
        price = ft.TextField(label="Đơn giá", keyboard_type=ft.KeyboardType.NUMBER)
        supplier = ft.TextField(label="Nhà cung cấp")
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Thêm vật tư"),
            content=ft.Column([category, code, name, price, supplier], tight=True),
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Thêm",
                    on_click=lambda e: self._create_product(
                        dialog, category, code, name, price, supplier
                    ),
                ),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _close_dialog(self, dialog):
        dialog.open = False
        self.page.update()

    def _create_product(self, dialog, category, code, name, price, supplier):
        try:
            self.db.create_product({
                "category": category.value,
                "code": code.value.strip(),
                "name": name.value.strip(),
                "unit_price": float(price.value.replace(",", ".")),
                "unit": "pcs",
                "environment": "both",
                "spec_json": {},
                "supplier": supplier.value.strip(),
            })
            self._close_dialog(dialog)
            self._refresh_options()
            self._refresh_inventory()
            self.message.value = "Đã thêm vật tư mới."
            self.message.color = ft.Colors.GREEN_700
            self.page.update()
        except (ValueError, KeyError, sqlite3.IntegrityError) as exc:
            self.message.value = f"Không thể thêm vật tư: {exc}"
            self.message.color = ft.Colors.RED_700
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
