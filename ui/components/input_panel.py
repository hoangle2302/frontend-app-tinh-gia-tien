from typing import Callable, Dict, List

import flet as ft


class InputPanel(ft.Container):
    BRAND_BLUE = "#007BFF"
    BRAND_CYAN = "#00AEEF"

    def __init__(
        self,
        options: Dict[str, List[Dict]],
        on_change: Callable,
        on_save: Callable,
        on_export_excel: Callable,
        on_export_pdf: Callable,
        on_load_preset: Callable,
    ):
        super().__init__()
        self.options = options
        self.on_change = on_change
        self.on_save = on_save
        self.on_load_preset = on_load_preset

        self.padding = 18
        self.border_radius = 20
        self.bgcolor = ft.Colors.WHITE
        self.border = None

        self.preset_dropdown = ft.Dropdown(
            label="Cấu hình mẫu",
            hint_text="Chọn cấu hình để áp dụng nhanh",
            **self._dropdown_style(),
            options=[
                ft.dropdown.Option("Màn hình Hội trường P2.5"),
                ft.dropdown.Option("Màn hình Outdoor P4"),
            ],
            on_select=self._load_preset,
        )
        self.customer_name = ft.TextField(
            label="Tên khách hàng / Công ty",
            hint_text="Ví dụ: Công ty ABC",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.project_name = ft.TextField(
            label="Tên dự án",
            hint_text="Ví dụ: Màn hình hội trường",
            prefix_icon=ft.Icons.WORK_OUTLINE,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.customer_phone = ft.TextField(
            label="Số điện thoại",
            prefix_icon=ft.Icons.PHONE_OUTLINED,
            keyboard_type=ft.KeyboardType.PHONE,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.screen_quantity = ft.TextField(
            label="Số lượng màn",
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.NUMBERS,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.environment = ft.RadioGroup(
            value="indoor",
            content=ft.Row(
                controls=[
                    ft.Radio(value="indoor", label="Trong nhà"),
                    ft.Radio(value="outdoor", label="Ngoài trời"),
                ]
            ),
            on_change=self._trigger_change,
        )
        self.pitch_dropdown = ft.Dropdown(
            label="Loại màn hình (Pixel Pitch)", expand=True,
            **self._dropdown_style(),
            options=[], on_select=self._trigger_change
        )
        # Loại trình chiếu
        self.display_mode = ft.Dropdown(
            label="Loại trình chiếu",
            value="both",
            expand=True,
            **self._dropdown_style(),
            options=[
                ft.dropdown.Option("online", "Online"),
                ft.dropdown.Option("offline", "Offline"),
                ft.dropdown.Option("both", "Online + Offline"),
            ],
            on_select=self._trigger_change,
        )
        self.width_input = ft.TextField(
            label="Chiều rộng W (m)", value="4", expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.STRAIGHTEN,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.height_input = ft.TextField(
            label="Chiều cao H (m)", value="2.5", expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.STRAIGHTEN,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.card_dropdown = ft.Dropdown(
            label="Thương hiệu card thu", expand=True,
            **self._dropdown_style(),
            options=[], on_select=self._trigger_change
        )
        self.power_dropdown = ft.Dropdown(
            label="Loại nguồn", expand=True,
            **self._dropdown_style(),
            options=[], on_select=self._trigger_change
        )
        self.frame_dropdown = ft.Dropdown(
            label="Loại khung", expand=True,
            **self._dropdown_style(),
            options=[], on_select=self._trigger_change
        )
        self.discount_slider = ft.Slider(
            min=0, max=100, divisions=100, value=0, label="{value}%",
            on_change=self._trigger_change,
        )
        self.profit_input = ft.TextField(
            label="Lợi nhuận (%)",
            value="20",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.TRENDING_UP,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.vat_input = ft.TextField(
            label="VAT (%)",
            value="8",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.RECEIPT_LONG,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.reserve_input = ft.TextField(
            label="Module dự phòng (%)",
            value="3",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.include_install = ft.Checkbox(
            label="Tính phí thi công", value=True, on_change=self._toggle_install
        )
        self.include_transport = ft.Checkbox(
            label="Tính phí vận chuyển", value=True, on_change=self._toggle_transport
        )
        self.install_price_input = ft.TextField(
            label="Phí thi công (VNĐ/m²)", value="350000",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.CONSTRUCTION,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.transport_price_input = ft.TextField(
            label="Phí vận chuyển (VNĐ/chuyến)", value="1500000",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.LOCAL_SHIPPING,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.additional_rows = ft.Column(spacing=8)
        self.additional_items = []
        self._load_options_for_environment("indoor")
        self.content = ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            width=4,
                            height=28,
                            bgcolor=ft.Colors.CYAN_600,
                            border_radius=4,
                        ),
                        ft.Column(
                            spacing=0,
                            controls=[
                                ft.Text("Tạo báo giá", size=22, weight=ft.FontWeight.BOLD, color="#1A1A1A"),
                                ft.Text("Nhập thông tin để bắt đầu", size=12, color=ft.Colors.BLUE_GREY_600),
                            ],
                        ),
                    ],
                ),
                self._section_card(
                    "Thông tin khách hàng",
                    [self.customer_name, self.project_name, self.customer_phone],
                ),
                self._section_card(
                    "Cấu hình màn hình",
                    [
                        self.environment,
                        self.pitch_dropdown,
                        self.display_mode,
                        ft.Row([self.width_input, self.height_input], spacing=8),
                        self.screen_quantity,
                        self.card_dropdown,
                        self.power_dropdown,
                        self.frame_dropdown,
                    ],
                ),
                self._section_card(
                    "Chiết khấu và dịch vụ",
                    [
                        self.discount_slider,
                        ft.Row([self.profit_input, self.vat_input], spacing=8),
                        self.reserve_input,
                        self.include_install,
                        self.install_price_input,
                        self.include_transport,
                        self.transport_price_input,
                    ],
                ),
                self._section_card(
                    "Hạng mục bổ sung",
                    [
                        self.additional_rows,
                        ft.OutlinedButton(
                            "Thêm vật tư",
                            icon=ft.Icons.ADD,
                            on_click=self._add_additional_item,
                        ),
                    ],
                ),
                ft.Divider(),
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.OutlinedButton(
                            "Xuất báo giá",
                            icon=ft.Icons.ARROW_FORWARD,
                            width=100,
                            height=58,
                            on_click=on_export_pdf,
                            style=self._secondary_button_style(),
                        ),
                        ft.OutlinedButton(
                            "Tải Excel",
                            icon=ft.Icons.TABLE_VIEW,
                            width=100,
                            height=58,
                            on_click=on_export_excel,
                            style=self._secondary_button_style(),
                        ),
                        ft.OutlinedButton(
                            "Lưu cấu hình",
                            icon=ft.Icons.SAVE,
                            width=100,
                            height=58,
                            on_click=on_save,
                            style=self._secondary_button_style(),
                        ),
                    ],
                ),
            ],
        )

    @classmethod
    def _field_style(cls):
        return {
            "border": cls._input_border(),
            "bgcolor": ft.Colors.WHITE,
            "cursor_color": cls.BRAND_BLUE,
            "label_style": ft.TextStyle(color="#6B7280"),
        }

    @classmethod
    def _dropdown_style(cls):
        return {
            "border": cls._input_border(),
            "bgcolor": ft.Colors.WHITE,
            "label_style": ft.TextStyle(color="#6B7280"),
        }

    @classmethod
    def _input_border(cls, default_color="#E0E0E0"):
        return {
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                border_radius=10,
                side=ft.BorderSide(color=default_color),
            ),
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                border_radius=10,
                side=ft.BorderSide(color=cls.BRAND_CYAN),
            ),
        }

    @classmethod
    def _primary_button_style(cls):
        return ft.ButtonStyle(
            bgcolor=cls.BRAND_BLUE,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=14),
            padding=ft.Padding(16, 14, 16, 14),
        )

    @classmethod
    def _secondary_button_style(cls):
        return ft.ButtonStyle(
            color=cls.BRAND_BLUE,
            side=ft.BorderSide(1, cls.BRAND_BLUE),
            shape=ft.RoundedRectangleBorder(radius=14),
            padding=ft.Padding(4, 0, 4, 0),
        )

    @staticmethod
    def _section_card(title: str, controls):
        return ft.Card(
            elevation=5,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=20),
            content=ft.Container(
                padding=ft.Padding(14, 12, 14, 14),
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text(title, size=17, weight=ft.FontWeight.BOLD, color="#1A1A1A"),
                        *controls,
                    ],
                ),
            ),
        )

    def _trigger_change(self, e):
        if e.control == self.environment:
            self._load_options_for_environment(self.environment.value)
        self.on_change(e)

    def _add_additional_item(self, e=None):
        name = ft.TextField(label="Tên vật tư", expand=True, **self._field_style())
        quantity = ft.TextField(label="SL", value="1", width=58, keyboard_type=ft.KeyboardType.NUMBER, **self._field_style())
        price = ft.TextField(label="Đơn giá", value="0", width=100, keyboard_type=ft.KeyboardType.NUMBER, **self._field_style())
        row = ft.Row(spacing=5, controls=[name, quantity, price])
        self.additional_items.append((name, quantity, price, row))
        row.controls.append(
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                tooltip="Xóa hạng mục",
                on_click=lambda event, item=(name, quantity, price, row): self._remove_additional_item(item),
            )
        )
        self.additional_rows.controls.append(row)
        self.page.update() if self.page else None

    def _remove_additional_item(self, item):
        self.additional_items.remove(item)
        self.additional_rows.controls.remove(item[3])
        self.on_change(None)

    def _toggle_install(self, e):
        self.install_price_input.disabled = not bool(self.include_install.value)
        if self.install_price_input.disabled:
            self.install_price_input.value = "0"
        elif self.install_price_input.value in {"0", ""}:
            self.install_price_input.value = "350000"
        self.on_change(e)

    def _toggle_transport(self, e):
        self.transport_price_input.disabled = not bool(self.include_transport.value)
        if self.transport_price_input.disabled:
            self.transport_price_input.value = "0"
        elif self.transport_price_input.value in {"0", ""}:
            self.transport_price_input.value = "1500000"
        self.on_change(e)

    def _load_preset(self, e):
        self.on_load_preset(self.preset_dropdown.value)

    def _load_options_for_environment(self, environment: str):
        modules = [m for m in self.options["modules"] if m["environment"] in {environment, "both"}]
        self.pitch_dropdown.options = [
            ft.dropdown.Option(key=m["code"], text=m["spec_json"]["pitch"]) for m in modules
        ]
        if modules and self.pitch_dropdown.value not in {m["code"] for m in modules}:
            self.pitch_dropdown.value = modules[0]["code"]
        for key, control in (
            ("cards", self.card_dropdown),
            ("powers", self.power_dropdown),
            ("frames", self.frame_dropdown),
        ):
            control.options = [ft.dropdown.Option(key=p["code"], text=p["name"]) for p in self.options[key]]
            if self.options[key] and not control.value:
                control.value = self.options[key][0]["code"]

    def set_values(self, values: Dict):
        self.environment.value = values.get("environment", "indoor")
        self._load_options_for_environment(self.environment.value)
        self.display_mode.value = values.get("display_mode", "both")
        for control, key in (
            (self.pitch_dropdown, "module_code"),
            (self.card_dropdown, "card_code"),
            (self.power_dropdown, "power_code"),
            (self.frame_dropdown, "frame_code"),
            (self.width_input, "width_m"),
            (self.height_input, "height_m"),
            (self.install_price_input, "install_price"),
            (self.transport_price_input, "transport_price"),
            (self.customer_name, "customer_name"),
            (self.project_name, "project_name"),
            (self.customer_phone, "customer_phone"),
            (self.screen_quantity, "screen_quantity"),
            (self.profit_input, "profit_percent"),
            (self.vat_input, "vat_percent"),
            (self.reserve_input, "reserve_percent"),
        ):
            if key in values:
                control.value = str(values[key])
        self.include_install.value = bool(values.get("include_install", True))
        self.include_transport.value = bool(values.get("include_transport", True))
        self._toggle_install(None)
        self._toggle_transport(None)

    def get_values(self) -> Dict:
        return {
            "environment": self.environment.value,
            "module_code": self.pitch_dropdown.value,
            "display_mode": self.display_mode.value,
            "card_code": self.card_dropdown.value,
            "power_code": self.power_dropdown.value,
            "frame_code": self.frame_dropdown.value,
            "width_m": self.width_input.value,
            "height_m": self.height_input.value,
            "discount_percent": self.discount_slider.value,
            "include_install": bool(self.include_install.value),
            "include_transport": bool(self.include_transport.value),
            "install_price": self.install_price_input.value if self.include_install.value else "0",
            "transport_price": self.transport_price_input.value if self.include_transport.value else "0",
            "customer_name": self.customer_name.value.strip(),
            "project_name": self.project_name.value.strip(),
            "customer_phone": self.customer_phone.value.strip(),
            "screen_quantity": self.screen_quantity.value,
            "profit_percent": self.profit_input.value,
            "vat_percent": self.vat_input.value,
            "reserve_percent": self.reserve_input.value,
            "additional_items": [
                {
                    "name": name.value.strip(),
                    "qty": quantity.value,
                    "unit_price": price.value,
                    "unit": "item",
                }
                for name, quantity, price, _ in self.additional_items
                if name.value.strip()
            ],
        }
