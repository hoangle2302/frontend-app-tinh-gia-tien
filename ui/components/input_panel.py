from typing import Callable, Dict, List

import flet as ft


class InputPanel(ft.Container):
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

        self.padding = 16
        self.border_radius = 12
        self.bgcolor = ft.Colors.WHITE
        self.border = ft.Border.all(1, ft.Colors.BLUE_GREY_100)

        self.preset_dropdown = ft.Dropdown(
            label="Cấu hình mẫu",
            hint_text="Chọn cấu hình để áp dụng nhanh",
            options=[
                ft.dropdown.Option("Màn hình Hội trường P2.5"),
                ft.dropdown.Option("Màn hình Outdoor P4"),
            ],
            on_select=self._load_preset,
        )
        self.customer_name = ft.TextField(
            label="Tên khách hàng / Công ty",
            hint_text="Ví dụ: Công ty ABC",
            on_change=self._trigger_change,
        )
        self.project_name = ft.TextField(
            label="Tên dự án",
            hint_text="Ví dụ: Màn hình hội trường",
            on_change=self._trigger_change,
        )
        self.customer_phone = ft.TextField(
            label="Số điện thoại",
            keyboard_type=ft.KeyboardType.PHONE,
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
            options=[], on_select=self._trigger_change
        )
        self.width_input = ft.TextField(
            label="Chiều rộng W (m)", value="4", expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._trigger_change,
        )
        self.height_input = ft.TextField(
            label="Chiều cao H (m)", value="2.5", expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._trigger_change,
        )
        self.card_dropdown = ft.Dropdown(
            label="Thương hiệu card thu", expand=True,
            options=[], on_select=self._trigger_change
        )
        self.power_dropdown = ft.Dropdown(
            label="Loại nguồn", expand=True,
            options=[], on_select=self._trigger_change
        )
        self.frame_dropdown = ft.Dropdown(
            label="Loại khung", expand=True,
            options=[], on_select=self._trigger_change
        )
        self.discount_slider = ft.Slider(
            min=0, max=30, divisions=30, value=5, label="{value}%",
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
            keyboard_type=ft.KeyboardType.NUMBER, on_change=self._trigger_change,
        )
        self.transport_price_input = ft.TextField(
            label="Phí vận chuyển (VNĐ/chuyến)", value="1500000",
            keyboard_type=ft.KeyboardType.NUMBER, on_change=self._trigger_change,
        )
        self._load_options_for_environment("indoor")
        self.content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Cấu hình báo giá", size=22, weight=ft.FontWeight.BOLD),
                self.preset_dropdown,
                ft.Text("Thông tin khách hàng", weight=ft.FontWeight.BOLD),
                self.customer_name,
                self.project_name,
                self.customer_phone,
                ft.Text("1. Môi trường sử dụng", weight=ft.FontWeight.BOLD),
                self.environment,
                self.pitch_dropdown,
                ft.Row([self.width_input, self.height_input], spacing=8),
                self.card_dropdown,
                self.power_dropdown,
                self.frame_dropdown,
                ft.Text("2. Chiết khấu và dịch vụ", weight=ft.FontWeight.BOLD),
                self.discount_slider,
                self.include_install,
                self.install_price_input,
                self.include_transport,
                self.transport_price_input,
                ft.Divider(),
                ft.Row(
                    wrap=True,
                    controls=[
                        ft.FilledButton("Tải Excel", icon=ft.Icons.TABLE_VIEW, on_click=on_export_excel),
                        ft.OutlinedButton("Xuất PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=on_export_pdf),
                    ],
                ),
                ft.FilledButton("Lưu cấu hình", icon=ft.Icons.SAVE, on_click=on_save),
            ],
        )

    def _trigger_change(self, e):
        if e.control == self.environment:
            self._load_options_for_environment(self.environment.value)
        self.on_change(e)

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
        }
