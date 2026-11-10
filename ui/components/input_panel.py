import math
from typing import Any, Callable, Dict, List

import flet as ft


class InputPanel(ft.Container):
    PRIMARY_COLOR = "#2563EB"
    SECONDARY_COLOR = "#00687A"

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

        self.padding = ft.Padding(4, 4, 4, 12)
        self.bgcolor = ft.Colors.TRANSPARENT

        # Chế độ cấu hình: Tự động vs Thủ công
        self.config_mode = "auto"  # "auto" | "manual"

        # Tab chế độ: Tự động / Thủ công
        self.mode_btn_auto = ft.Container(
            expand=True,
            height=40,
            border_radius=10,
            ink=True,
            bgcolor="#2563EB",
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_mode("auto"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, size=16, color=ft.Colors.WHITE),
                    ft.Text("Tự động", size=13, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                ],
            ),
        )
        self.mode_btn_manual = ft.Container(
            expand=True,
            height=40,
            border_radius=10,
            ink=True,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, "#E2E8F0"),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_mode("manual"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.EDIT_OUTLINED, size=16, color="#64748B"),
                    ft.Text("Thủ công", size=13, weight=ft.FontWeight.W_700, color="#64748B"),
                ],
            ),
        )

        # Mô tả chế độ
        self.mode_description = ft.Text(
            "Nhập số module; kích thước và độ phân giải được suy ra theo thông số mẫu.",
            size=11,
            color="#64748B",
        )

        # Trình chiếu: Online vs Offline
        self.display_mode_val = "online"  # "online" | "offline"
        self.btn_online = ft.Container(
            expand=True,
            height=44,
            border_radius=10,
            ink=True,
            bgcolor="#E8EEFF",
            border=ft.Border.all(1.5, "#2563EB"),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_display_mode("online"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED, size=18, color="#2563EB"),
                    ft.Text("Online", size=13, weight=ft.FontWeight.W_700, color="#2563EB"),
                ],
            ),
        )
        self.btn_offline = ft.Container(
            expand=True,
            height=44,
            border_radius=10,
            ink=True,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, "#CBD5E1"),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_display_mode("offline"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, size=18, color="#64748B"),
                    ft.Text("Offline", size=13, weight=ft.FontWeight.W_700, color="#64748B"),
                ],
            ),
        )

        # Môi trường: Trong nhà (indoor) vs Ngoài trời (outdoor)
        self.env_mode_val = "indoor"  # "indoor" | "outdoor"
        self.btn_indoor = ft.Container(
            expand=True,
            height=44,
            border_radius=10,
            ink=True,
            bgcolor="#E8EEFF",
            border=ft.Border.all(1.5, "#2563EB"),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_env_mode("indoor"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED, size=18, color="#2563EB"),
                    ft.Text("Trong nhà", size=13, weight=ft.FontWeight.W_700, color="#2563EB"),
                ],
            ),
        )
        self.btn_outdoor = ft.Container(
            expand=True,
            height=44,
            border_radius=10,
            ink=True,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, "#CBD5E1"),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_env_mode("outdoor"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, size=18, color="#64748B"),
                    ft.Text("Ngoài trời", size=13, weight=ft.FontWeight.W_700, color="#64748B"),
                ],
            ),
        )

        # Hãng module & Mã module
        self.module_brand_dropdown = ft.Dropdown(
            label="Hãng module",
            hint_text="Chọn hãng",
            expand=True,
            **self._dropdown_style(),
            options=[
                ft.dropdown.Option("Qiangli"),
                ft.dropdown.Option("GKGD"),
                ft.dropdown.Option("Cailiang"),
                ft.dropdown.Option("Toàn Trung"),
            ],
            value="Toàn Trung",
            on_select=self._trigger_change,
        )
        self.module_code_dropdown = ft.Dropdown(
            label="Mã module",
            hint_text="Chọn mã",
            expand=True,
            **self._dropdown_style(),
            options=[],
            on_select=self._on_module_code_selected,
        )

        # Card thông số module mẫu
        self.module_spec_name = ft.Text("Module P10", size=13, weight=ft.FontWeight.W_700, color="#0F172A")
        self.module_spec_details = ft.Text("320 × 160 mm  /  32 × 16 px", size=11, color="#64748B")
        self.module_spec_box = ft.Container(
            padding=ft.Padding(12, 10, 12, 10),
            bgcolor="#F8FAFC",
            border_radius=10,
            border=ft.Border.all(1, "#F1F5F9"),
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            self.module_spec_name,
                            ft.Container(
                                padding=ft.Padding(6, 2, 6, 2),
                                bgcolor="#E8EEFF",
                                border_radius=6,
                                content=ft.Text("Thông số mẫu", size=10, weight=ft.FontWeight.W_600, color="#2563EB"),
                            ),
                        ],
                    ),
                    self.module_spec_details,
                    ft.Text("Chỉ dùng minh họa, không phải mã sản phẩm chính thức của Toàn Trung.", size=10, color="#94A3B8"),
                ],
            ),
        )

        # Sơ đồ ma trận module preview
        self.preview_header_size = ft.Text("2.560 × 640 mm", size=12, weight=ft.FontWeight.W_700, color="#2563EB")
        self.preview_header_grid = ft.Text("8 cột × 4 hàng", size=11, color="#64748B")
        self.preview_grid_column = ft.Column(spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.preview_footer_note = ft.Text("Sơ đồ minh họa • 32 module lắp", size=10, color="#64748B")

        self.preview_container = ft.Container(
            padding=ft.Padding(14, 12, 14, 12),
            bgcolor="#F0F5FF",
            border=ft.Border.all(1, "#D0E0FF"),
            border_radius=12,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[self.preview_header_size, self.preview_header_grid],
                    ),
                    self.preview_grid_column,
                    self.preview_footer_note,
                ],
            ),
        )

        # Badge tag chế độ (Tự tính vs Nhập tay)
        self.tag_w_mm = self._badge_tag("Tự tính")
        self.tag_w_px = self._badge_tag("Tự tính")
        self.tag_h_mm = self._badge_tag("Tự tính")
        self.tag_h_px = self._badge_tag("Tự tính")
        self.tag_installed = self._badge_tag("Tự tính")
        self.tag_total_mod = self._badge_tag("Tự tính")
        self.tag_total_px = self._badge_tag("Tự tính")

        # Số module W (chiều rộng)
        self.num_modules_w = 8
        self.txt_modules_w = ft.TextField(
            value="8",
            width=70,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.NONE,
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_700, color="#0F172A"),
            dense=True,
            content_padding=ft.Padding(0, 4, 0, 4),
            on_change=self._on_txt_modules_w_changed,
        )
        self.calc_w_mm = ft.TextField(
            label="Kích thước hiển thị W",
            value="2.560",
            suffix=ft.Text("mm", size=12, color="#64748B"),
            read_only=True,
            expand=True,
            on_change=self._on_manual_dimension_changed,
            **self._read_only_field_style(),
        )
        self.calc_w_px = ft.TextField(
            label="Độ phân giải W",
            value="256",
            suffix=ft.Text("px", size=12, color="#64748B"),
            read_only=True,
            expand=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )

        # Số module H (chiều cao)
        self.num_modules_h = 4
        self.txt_modules_h = ft.TextField(
            value="4",
            width=70,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.NONE,
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_700, color="#0F172A"),
            dense=True,
            content_padding=ft.Padding(0, 4, 0, 4),
            on_change=self._on_txt_modules_h_changed,
        )
        self.calc_h_mm = ft.TextField(
            label="Kích thước hiển thị H",
            value="640",
            suffix=ft.Text("mm", size=12, color="#64748B"),
            read_only=True,
            expand=True,
            on_change=self._on_manual_dimension_changed,
            **self._read_only_field_style(),
        )
        self.calc_h_px = ft.TextField(
            label="Độ phân giải H",
            value="64",
            suffix=ft.Text("px", size=12, color="#64748B"),
            read_only=True,
            expand=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )

        # Dự phòng & tổng module
        self.num_reserve_modules = 2
        self.txt_reserve_modules = ft.TextField(
            value="2",
            width=70,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.NONE,
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_700, color="#0F172A"),
            dense=True,
            content_padding=ft.Padding(0, 4, 0, 4),
            on_change=self._on_txt_reserve_changed,
        )
        self.calc_installed_modules = ft.TextField(
            label="Module lắp",
            value="32",
            read_only=True,
            expand=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )
        self.calc_total_modules = ft.TextField(
            label="Tổng module",
            value="34",
            read_only=True,
            expand=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )
        self.calc_total_pixels = ft.TextField(
            label="Tổng pixel hiển thị",
            value="16.384",
            suffix=ft.Text("px", size=12, color="#64748B"),
            read_only=True,
            expand=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )

        self.reserve_note_text = ft.Text(
            "Module lắp = W × H = 8 × 4 = 32.\nTổng module = module lắp + dự phòng = 34.\nTổng pixel = 256 × 64 = 16.384 px, không tính module dự phòng.",
            size=10,
            color="#94A3B8",
        )

        # Phần Thông tin chung (Header & Warning box)
        self.general_mode_tag = ft.Text("Tự động tính*", size=12, color="#2563EB")
        self.general_warning_title = ft.Text("Chờ cấu hình định mức", size=12, weight=ft.FontWeight.W_700, color="#B45309")
        self.general_warning_desc = ft.Text(
            "Cần thông số kỹ thuật và định mức để tự tính. Hãng, mã và loại vẫn do bạn chọn; không tự chọn linh kiện.",
            size=11,
            color="#D97706",
        )

        # Các trường thông tin chung
        self.customer_name = ft.TextField(
            label="Mã khách hàng",
            hint_text="Chưa thiết lập",
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.project_name = ft.TextField(
            label="Tên dự án",
            hint_text="Bảng năng suất xưởng",
            value="Bảng năng suất xưởng",
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.customer_phone = ft.TextField(
            label="Số điện thoại",
            hint_text="Chưa thiết lập",
            keyboard_type=ft.KeyboardType.PHONE,
            **self._field_style(),
            on_change=self._trigger_change,
        )

        # Nguồn & Bộ xử lý
        self.power_brand_dropdown = ft.Dropdown(
            label="Hãng nguồn",
            hint_text="Chọn hãng",
            expand=True,
            **self._dropdown_style(),
            options=[ft.dropdown.Option("Meanwell"), ft.dropdown.Option("CZCL"), ft.dropdown.Option("G-Energy"), ft.dropdown.Option("Khác")],
            value="CZCL",
            on_select=self._trigger_change,
        )
        self.power_dropdown = ft.Dropdown(
            label="Mã nguồn",
            hint_text="Chọn mã",
            expand=True,
            **self._dropdown_style(),
            options=[],
            on_select=self._trigger_change,
        )
        self.power_capacity_hint = ft.TextField(
            label="Công suất",
            hint_text="Chờ cấu hình định mức",
            read_only=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )
        self.processor_brand_dropdown = ft.Dropdown(
            label="Hãng bộ xử lý",
            hint_text="Chọn hãng",
            **self._dropdown_style(),
            options=[ft.dropdown.Option("HD (Huidu)"), ft.dropdown.Option("Novastar"), ft.dropdown.Option("Linsn"), ft.dropdown.Option("Colorlight")],
            value="HD (Huidu)",
            on_select=self._trigger_change,
        )

        # Khung & vật liệu
        self.frame_dropdown = ft.Dropdown(
            label="Loại khung",
            hint_text="Chưa thiết lập",
            **self._dropdown_style(),
            options=[],
            on_select=self._trigger_change,
        )
        self.alu_hint = ft.TextField(
            label="Alu theo khung",
            hint_text="Chờ cấu hình định mức",
            read_only=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )
        self.area_hint = ft.TextField(
            label="Al theo diện tích",
            hint_text="Chờ cấu hình định mức",
            read_only=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )

        # Điện & phụ trợ
        self.power_phase_val = "1pha"  # "1pha" | "3pha"
        self.btn_1pha = ft.Container(
            expand=True,
            height=42,
            border_radius=10,
            ink=True,
            bgcolor="#E8EEFF",
            border=ft.Border.all(1.5, "#2563EB"),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_power_phase("1pha"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED, size=18, color="#2563EB"),
                    ft.Text("1 pha", size=13, weight=ft.FontWeight.W_700, color="#2563EB"),
                ],
            ),
        )
        self.btn_3pha = ft.Container(
            expand=True,
            height=42,
            border_radius=10,
            ink=True,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, "#CBD5E1"),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_power_phase("3pha"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, size=18, color="#64748B"),
                    ft.Text("3 pha", size=13, weight=ft.FontWeight.W_700, color="#64748B"),
                ],
            ),
        )
        self.fan_hint = ft.TextField(
            label="Quạt 5V",
            hint_text="Chờ cấu hình định mức",
            read_only=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )
        self.power_compensation_dropdown = ft.Dropdown(
            label="Loại bù điện",
            hint_text="Chưa thiết lập",
            **self._dropdown_style(),
            options=[ft.dropdown.Option("Chưa thiết lập"), ft.dropdown.Option("Có bù điện"), ft.dropdown.Option("Không")],
            value="Chưa thiết lập",
        )
        self.cb_dropdown = ft.Dropdown(
            label="Loại CB",
            hint_text="Chưa thiết lập",
            **self._dropdown_style(),
            options=[ft.dropdown.Option("Chưa thiết lập"), ft.dropdown.Option("CB 16A"), ft.dropdown.Option("CB 32A"), ft.dropdown.Option("CB 63A")],
            value="Chưa thiết lập",
        )
        self.cf_dropdown = ft.Dropdown(
            label="Loại CF",
            hint_text="Chưa thiết lập",
            **self._dropdown_style(),
            options=[ft.dropdown.Option("Chưa thiết lập"), ft.dropdown.Option("Khởi động từ 220V"), ft.dropdown.Option("Khởi động từ 380V")],
            value="Chưa thiết lập",
        )
        self.wire_hint = ft.TextField(
            label="Tiết diện dây",
            hint_text="Chờ cấu hình định mức",
            read_only=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )
        self.cabinet_hint = ft.TextField(
            label="Tủ điện",
            hint_text="Chờ cấu hình định mức",
            read_only=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )

        # Các trường ẩn tương thích ngược cho engine tính toán
        self.environment = ft.RadioGroup(value="indoor", content=ft.Container())
        self.display_mode = ft.Dropdown(value="online")
        self.pitch_dropdown = ft.Dropdown()
        self.width_input = ft.TextField(value="2.56")
        self.height_input = ft.TextField(value="0.64")
        self.screen_quantity = ft.TextField(value="1")
        self.card_dropdown = ft.Dropdown()
        self.discount_slider = ft.Slider(value=0)
        self.profit_input = ft.TextField(value="20")
        self.vat_input = ft.TextField(value="8")
        self.reserve_input = ft.TextField(value="3")
        self.include_install = ft.Checkbox(value=True)
        self.include_transport = ft.Checkbox(value=True)
        self.install_price_input = ft.TextField(value="350000")
        self.transport_price_input = ft.TextField(value="1500000")
        self.additional_items = []
        self.additional_rows = ft.Column(spacing=8)
        self.preset_dropdown = ft.Dropdown(value="Màn hình Hội trường P2.5")

        # Nạp dữ liệu dropdown ban đầu
        self._init_module_options()
        self._sync_calc_display()

        # Dựng nội dung View
        self.content = self._build_layout()

    # -------------------------------------------------------------
    # Giao diện tổng thể
    # -------------------------------------------------------------
    def _build_layout(self):
        # 1. Header: Cấu hình LED
        header_block = ft.Column(
            spacing=4,
            controls=[
                ft.Text("Cấu hình LED", size=24, weight=ft.FontWeight.W_800, color="#0F172A"),
                ft.Text("Thiết lập thông số trước khi lập bảng dự toán.", size=12, color="#64748B"),
                ft.Container(height=6),
                ft.Row(spacing=8, controls=[self.mode_btn_auto, self.mode_btn_manual]),
                self.mode_description,
            ],
        )

        # 2. Alert box ví dụ cấu hình
        self.info_banner = ft.Container(
            padding=ft.Padding(12, 10, 12, 10),
            bgcolor="#EFF6FF",
            border=ft.Border.all(1, "#DBEAFE"),
            border_radius=12,
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color="#2563EB"),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text("Ví dụ cấu hình", size=12, weight=ft.FontWeight.W_700, color="#1E40AF"),
                            ft.Text(
                                "Bảng năng suất xưởng • Bản minh họa riêng. Chưa áp dụng vào DT-001, không đổi số tiền cũ.",
                                size=11,
                                color="#3B82F6",
                            ),
                        ],
                    ),
                ],
            ),
        )

        # Card 1: Trình chiếu & module
        self.card_display_module = self._card_container(
            title="Trình chiếu & module",
            icon=ft.Icons.GRID_VIEW_ROUNDED,
            controls=[
                ft.Text("Loại màn hình", size=12, weight=ft.FontWeight.W_600, color="#0F172A"),
                ft.Row(spacing=8, controls=[self.btn_indoor, self.btn_outdoor]),
                ft.Text("Loại trình chiếu", size=12, weight=ft.FontWeight.W_600, color="#0F172A"),
                ft.Row(spacing=8, controls=[self.btn_online, self.btn_offline]),
                ft.Row(spacing=8, controls=[self.module_brand_dropdown, self.module_code_dropdown]),
                self.module_spec_box,
            ],
        )

        # Card 2: Kích thước & độ phân giải
        self.card_dimensions = self._card_container(
            title="Kích thước & độ phân giải",
            icon=ft.Icons.STRAIGHTEN_ROUNDED,
            controls=[
                self.preview_container,
                ft.Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=22,
                            height=22,
                            border_radius=6,
                            bgcolor="#EFF6FF",
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text("W", size=11, weight=ft.FontWeight.W_700, color="#2563EB"),
                        ),
                        ft.Text("Chiều rộng", size=13, weight=ft.FontWeight.W_700, color="#0F172A"),
                    ],
                ),
                ft.Text("Số module W", size=12, color="#64748B"),
                self._stepper_row(self.txt_modules_w, lambda delta: self._change_modules_w(delta)),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Column(expand=True, spacing=2, controls=[self.tag_w_mm, self.calc_w_mm]),
                        ft.Column(expand=True, spacing=2, controls=[self.tag_w_px, self.calc_w_px]),
                    ],
                ),
                ft.Text("Rộng hiển thị = số module W × rộng 1 module.\nĐộ phân giải W = số module W × độ phân giải W của 1 module.", size=10, color="#94A3B8"),
                ft.Divider(color="#E2E8F0", height=1),
                ft.Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=22,
                            height=22,
                            border_radius=6,
                            bgcolor="#EFF6FF",
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text("H", size=11, weight=ft.FontWeight.W_700, color="#2563EB"),
                        ),
                        ft.Text("Chiều cao", size=13, weight=ft.FontWeight.W_700, color="#0F172A"),
                    ],
                ),
                ft.Text("Số module H", size=12, color="#64748B"),
                self._stepper_row(self.txt_modules_h, lambda delta: self._change_modules_h(delta)),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Column(expand=True, spacing=2, controls=[self.tag_h_mm, self.calc_h_mm]),
                        ft.Column(expand=True, spacing=2, controls=[self.tag_h_px, self.calc_h_px]),
                    ],
                ),
                ft.Text("Cao hiển thị = số module H × cao 1 module.\nĐộ phân giải H = số module H × độ phân giải H của 1 module.", size=10, color="#94A3B8"),
            ],
        )

        # Card 3: Dự phòng & tổng module
        self.card_reserve = self._card_container(
            title="Dự phòng & tổng module",
            icon=ft.Icons.LAYERS_OUTLINED,
            controls=[
                ft.Text("Số module dự phòng", size=12, color="#64748B"),
                self._stepper_row(self.txt_reserve_modules, lambda delta: self._change_reserve(delta)),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Column(expand=True, spacing=2, controls=[self.tag_installed, self.calc_installed_modules]),
                        ft.Column(expand=True, spacing=2, controls=[self.tag_total_mod, self.calc_total_modules]),
                    ],
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Column(expand=True, spacing=2, controls=[self.tag_total_px, self.calc_total_pixels]),
                    ],
                ),
                self.reserve_note_text,
            ],
        )

        # Section: Thông tin chung
        header_general = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("Thông tin chung", size=16, weight=ft.FontWeight.W_800, color="#0F172A"),
                self.general_mode_tag,
            ],
        )

        self.warning_general = ft.Container(
            padding=ft.Padding(12, 10, 12, 10),
            bgcolor="#FFFBEB",
            border=ft.Border.all(1, "#FDE68A"),
            border_radius=12,
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color="#B45309"),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            self.general_warning_title,
                            self.general_warning_desc,
                        ],
                    ),
                ],
            ),
        )

        self.card_customer = self._card_container(
            title="Thông tin khách hàng",
            icon=ft.Icons.PERSON_OUTLINE,
            controls=[
                self.customer_name,
                self.project_name,
                self.customer_phone,
                ft.Text("Cần xác nhận tên mục", size=10, color="#B45309"),
            ],
        )

        self.card_power_proc = self._card_container(
            title="Nguồn & bộ xử lý",
            icon=ft.Icons.SETTINGS_INPUT_COMPONENT_OUTLINED,
            controls=[
                ft.Row(spacing=8, controls=[self.power_brand_dropdown, self.power_dropdown]),
                self.power_capacity_hint,
                self.processor_brand_dropdown,
            ],
        )

        self.card_frame = self._card_container(
            title="Khung & vật liệu",
            icon=ft.Icons.CROP_FREE,
            controls=[
                self.frame_dropdown,
                self.alu_hint,
                self.area_hint,
                ft.Text("Cần xác nhận tên mục", size=10, color="#B45309"),
            ],
        )

        self.card_electric = self._card_container(
            title="Điện & phụ trợ",
            icon=ft.Icons.BOLT,
            controls=[
                ft.Text("Nguồn điện", size=12, weight=ft.FontWeight.W_600, color="#0F172A"),
                ft.Row(spacing=8, controls=[self.btn_1pha, self.btn_3pha]),
                self.fan_hint,
                self.power_compensation_dropdown,
                ft.Text("Cần xác nhận tên mục", size=10, color="#B45309"),
                self.cb_dropdown,
                self.cf_dropdown,
                ft.Text("Cần xác nhận tên mục", size=10, color="#B45309"),
                self.wire_hint,
                self.cabinet_hint,
                ft.Text("Các lựa chọn điện cần được xác nhận theo thông số kỹ thuật và phương án lắp đặt thực tế.", size=10, color="#64748B"),
            ],
        )

        footer_note = ft.Column(
            spacing=2,
            controls=[
                ft.Text("Dữ liệu minh họa • Cần xác nhận thông số kỹ thuật", size=11, color="#B45309"),
                ft.Text("Nguồn tham khảo: toantrung.com.vn", size=11, color="#64748B"),
            ],
        )

        return ft.Column(
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                header_block,
                self.info_banner,
                self.card_display_module,
                self.card_dimensions,
                self.card_reserve,
                header_general,
                self.warning_general,
                self.card_customer,
                self.card_power_proc,
                self.card_frame,
                self.card_electric,
                footer_note,
            ],
        )

    # -------------------------------------------------------------
    # Helpers Widget Style
    # -------------------------------------------------------------
    def apply_theme(self, is_dark: bool):
        bg_card = "#1D2024" if is_dark else ft.Colors.WHITE
        border_card = "#42474E" if is_dark else "#E2E8F0"
        text_primary = "#E0E2E8" if is_dark else "#0F172A"
        text_secondary = "#8C9199" if is_dark else "#64748B"

        cards = [
            self.card_display_module,
            self.card_dimensions,
            self.card_reserve,
            self.card_customer,
            self.card_power_proc,
            self.card_frame,
            self.card_electric,
        ]
        for c in cards:
            c.bgcolor = bg_card
            c.border = ft.Border.all(1, border_card)

        # Cập nhật banner ví dụ cấu hình
        if is_dark:
            self.info_banner.bgcolor = "#1E293B"
            self.info_banner.border = ft.Border.all(1, "#334155")
            self.module_spec_box.bgcolor = "#1E293B"
            self.module_spec_box.border = ft.Border.all(1, "#334155")
            self.module_spec_name.color = "#E0E2E8"
            self.preview_container.bgcolor = "#1E293B"
            self.preview_container.border = ft.Border.all(1, "#334155")
            self.warning_general.bgcolor = "#292524"
            self.warning_general.border = ft.Border.all(1, "#44403C")
        else:
            self.info_banner.bgcolor = "#EFF6FF"
            self.info_banner.border = ft.Border.all(1, "#DBEAFE")
            self.module_spec_box.bgcolor = "#F8FAFC"
            self.module_spec_box.border = ft.Border.all(1, "#F1F5F9")
            self.module_spec_name.color = "#0F172A"
            self.preview_container.bgcolor = "#F0F5FF"
            self.preview_container.border = ft.Border.all(1, "#D0E0FF")
            self.warning_general.bgcolor = "#FFFBEB"
            self.warning_general.border = ft.Border.all(1, "#FDE68A")

        # Cập nhật các nút lựa chọn chưa được active
        inactive_bg = "#1D2024" if is_dark else ft.Colors.WHITE
        inactive_border = "#42474E" if is_dark else "#CBD5E1"
        for btn, is_active in [
            (self.btn_indoor, self.env_mode_val == "indoor"),
            (self.btn_outdoor, self.env_mode_val == "outdoor"),
            (self.btn_online, self.display_mode_val == "online"),
            (self.btn_offline, self.display_mode_val == "offline"),
            (self.btn_1pha, self.power_phase_val == "1pha"),
            (self.btn_3pha, self.power_phase_val == "3pha"),
        ]:
            if not is_active:
                btn.bgcolor = inactive_bg
                btn.border = ft.Border.all(1, inactive_border)

        # Chế độ tự động / thủ công nút không active
        if self.config_mode == "auto":
            self.mode_btn_manual.bgcolor = inactive_bg
            self.mode_btn_manual.border = ft.Border.all(1, border_card)
        else:
            self.mode_btn_auto.bgcolor = inactive_bg
            self.mode_btn_auto.border = ft.Border.all(1, border_card)

        # Cập nhật màu text trong các ô số W, H, dự phòng
        self.txt_modules_w.text_style = ft.TextStyle(size=16, weight=ft.FontWeight.W_700, color=text_primary)
        self.txt_modules_h.text_style = ft.TextStyle(size=16, weight=ft.FontWeight.W_700, color=text_primary)
        self.txt_reserve_modules.text_style = ft.TextStyle(size=16, weight=ft.FontWeight.W_700, color=text_primary)

    def _badge_tag(self, text: str):
        return ft.Container(
            padding=ft.Padding(6, 2, 6, 2),
            bgcolor="#EFF6FF",
            border_radius=6,
            content=ft.Text(text, size=10, weight=ft.FontWeight.W_600, color="#2563EB"),
        )

    def _card_container(self, title: str, icon, controls: list):
        return ft.Container(
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border_radius=14,
            border=ft.Border.all(1, "#E2E8F0"),
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=32,
                                height=32,
                                border_radius=8,
                                bgcolor="#EFF6FF",
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(icon, size=18, color="#2563EB"),
                            ),
                            ft.Text(title, size=15, weight=ft.FontWeight.W_800, color="#0F172A"),
                        ],
                    ),
                    *controls,
                ],
            ),
        )

    def _stepper_row(self, label_control: ft.Text, on_change_callback):
        return ft.Container(
            border=ft.Border.all(1, "#CBD5E1"),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.REMOVE,
                        icon_size=18,
                        icon_color="#64748B",
                        on_click=lambda e: on_change_callback(-1),
                    ),
                    label_control,
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        icon_size=18,
                        icon_color="#64748B",
                        on_click=lambda e: on_change_callback(1),
                    ),
                ],
            ),
        )

    @classmethod
    def _field_style(cls, suffix_icon=None):
        style = {
            "border": cls._input_border(),
            "bgcolor": ft.Colors.TRANSPARENT,
            "cursor_color": cls.PRIMARY_COLOR,
            "label_style": ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color="#64748B"),
            "dense": True,
        }
        if suffix_icon:
            style["suffix"] = ft.Icon(suffix_icon, size=16, color="#64748B")
        return style

    @classmethod
    def _read_only_field_style(cls):
        return {
            "border": cls._input_border("#E2E8F0"),
            "bgcolor": "#F8FAFC",
            "label_style": ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color="#64748B"),
            "dense": True,
        }

    @classmethod
    def _dropdown_style(cls):
        return {
            "border": cls._input_border(),
            "bgcolor": ft.Colors.WHITE,
            "label_style": ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color="#64748B"),
            "dense": True,
            "menu_style": ft.MenuStyle(
                bgcolor=ft.Colors.WHITE,
                elevation=6,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        }

    @classmethod
    def _input_border(cls, default_color="#CBD5E1"):
        return {
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                border_radius=10,
                side=ft.BorderSide(width=1, color=default_color),
            ),
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                border_radius=10,
                side=ft.BorderSide(width=1.5, color=cls.PRIMARY_COLOR),
            ),
        }

    @classmethod
    def _primary_button_style(cls):
        return ft.ButtonStyle(
            bgcolor=cls.PRIMARY_COLOR,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(16, 12, 16, 12),
        )

    # -------------------------------------------------------------
    # Logic tương tác UI: Chuyển đổi Tự động vs Thủ công
    # -------------------------------------------------------------
    def _set_mode(self, mode: str):
        self.config_mode = mode
        is_auto = mode == "auto"

        # Tab button style
        self.mode_btn_auto.bgcolor = "#2563EB" if is_auto else ft.Colors.WHITE
        self.mode_btn_auto.border = None if is_auto else ft.Border.all(1, "#E2E8F0")
        self.mode_btn_auto.content.controls[0].color = ft.Colors.WHITE if is_auto else "#64748B"
        self.mode_btn_auto.content.controls[1].color = ft.Colors.WHITE if is_auto else "#64748B"

        self.mode_btn_manual.bgcolor = ft.Colors.WHITE if is_auto else "#2563EB"
        self.mode_btn_manual.border = ft.Border.all(1, "#E2E8F0") if is_auto else None
        self.mode_btn_manual.content.controls[0].color = "#64748B" if is_auto else ft.Colors.WHITE
        self.mode_btn_manual.content.controls[1].color = "#64748B" if is_auto else ft.Colors.WHITE

        # Cập nhật mô tả chế độ
        if is_auto:
            self.mode_description.value = "Nhập số module; kích thước và độ phân giải được suy ra theo thông số mẫu."
            self.general_mode_tag.value = "Tự động tính*"
            self.general_warning_title.value = "Chờ cấu hình định mức"
            self.general_warning_desc.value = "Cần thông số kỹ thuật và định mức để tự tính. Hãng, mã và loại vẫn do bạn chọn; không tự chọn linh kiện."
            self.reserve_note_text.value = (
                "Module lắp = W × H = 8 × 4 = 32.\n"
                "Tổng module = module lắp + dự phòng = 34.\n"
                "Tổng pixel = 256 × 64 = 16.384 px, không tính module dự phòng."
            )
        else:
            self.mode_description.value = "Tự nhập thông số và định mức; kiểm tra lại trước khi áp dụng."
            self.general_mode_tag.value = "Nhập thủ công"
            self.general_warning_title.value = "Kiểm tra thông số trước khi áp dụng"
            self.general_warning_desc.value = "Tự nhập thông số và định mức. Các mục chưa có dữ liệu được để trống, không suy đoán giá trị."
            self.reserve_note_text.value = "Tổng module gồm module dự phòng. Tổng pixel hiển thị không tính module dự phòng."

        # Cập nhật các badge tag
        tag_text = "Tự tính" if is_auto else "Nhập tay"
        for tag in [self.tag_w_mm, self.tag_w_px, self.tag_h_mm, self.tag_h_px, self.tag_installed, self.tag_total_mod, self.tag_total_px]:
            tag.content.value = tag_text

        # Bật/tắt chế độ read_only và icon bút chì (edit)
        is_read_only = is_auto
        fields_with_suffix = [
            (self.calc_w_mm, "mm"),
            (self.calc_w_px, "px"),
            (self.calc_h_mm, "mm"),
            (self.calc_h_px, "px"),
            (self.calc_total_pixels, "px"),
        ]
        for field, unit in fields_with_suffix:
            field.read_only = is_read_only
            field.border = self._input_border("#E2E8F0" if is_read_only else "#CBD5E1")
            field.bgcolor = "#F8FAFC" if is_read_only else ft.Colors.TRANSPARENT
            if is_read_only:
                field.suffix = ft.Text(unit, size=12, color="#64748B")
            else:
                field.suffix = ft.Row(
                    tight=True,
                    spacing=4,
                    controls=[
                        ft.Text(unit, size=12, color="#64748B"),
                        ft.Icon(ft.Icons.EDIT_OUTLINED, size=14, color="#2563EB"),
                    ],
                )

        plain_fields = [
            self.calc_installed_modules,
            self.calc_total_modules,
            self.power_capacity_hint,
            self.alu_hint,
            self.area_hint,
            self.fan_hint,
            self.wire_hint,
            self.cabinet_hint,
        ]
        for field in plain_fields:
            field.read_only = is_read_only
            field.border = self._input_border("#E2E8F0" if is_read_only else "#CBD5E1")
            field.bgcolor = "#F8FAFC" if is_read_only else ft.Colors.TRANSPARENT
            if is_read_only:
                field.suffix = None
                if field in [self.power_capacity_hint, self.alu_hint, self.area_hint, self.fan_hint, self.wire_hint, self.cabinet_hint]:
                    field.hint_text = "Chờ cấu hình định mức"
                    field.value = ""
            else:
                field.suffix = ft.Icon(ft.Icons.EDIT_OUTLINED, size=14, color="#2563EB")
                if field in [self.power_capacity_hint, self.alu_hint, self.area_hint, self.fan_hint, self.wire_hint, self.cabinet_hint]:
                    field.hint_text = "Chưa thiết lập"

        if is_auto:
            self._sync_calc_display()

        self._trigger_change(None)
        if getattr(self, "_Control__page", None):
            self.page.update()

    def _set_display_mode(self, mode: str):
        self.display_mode_val = mode
        self.display_mode.value = mode
        is_online = mode == "online"
        self.btn_online.bgcolor = "#E8EEFF" if is_online else ft.Colors.WHITE
        self.btn_online.border = ft.Border.all(1.5, "#2563EB") if is_online else ft.Border.all(1, "#CBD5E1")
        self.btn_online.content.controls[0].icon = ft.Icons.RADIO_BUTTON_CHECKED if is_online else ft.Icons.RADIO_BUTTON_UNCHECKED
        self.btn_online.content.controls[0].color = "#2563EB" if is_online else "#64748B"
        self.btn_online.content.controls[1].color = "#2563EB" if is_online else "#64748B"

        self.btn_offline.bgcolor = ft.Colors.WHITE if is_online else "#E8EEFF"
        self.btn_offline.border = ft.Border.all(1, "#CBD5E1") if is_online else ft.Border.all(1.5, "#2563EB")
        self.btn_offline.content.controls[0].icon = ft.Icons.RADIO_BUTTON_UNCHECKED if is_online else ft.Icons.RADIO_BUTTON_CHECKED
        self.btn_offline.content.controls[0].color = "#64748B" if is_online else "#2563EB"
        self.btn_offline.content.controls[1].color = "#64748B" if is_online else "#2563EB"
        self._trigger_change(None)
        if getattr(self, "_Control__page", None):
            self.page.update()

    def _set_env_mode(self, env: str):
        self.env_mode_val = env
        self.environment.value = env
        is_indoor = env == "indoor"
        self.btn_indoor.bgcolor = "#E8EEFF" if is_indoor else ft.Colors.WHITE
        self.btn_indoor.border = ft.Border.all(1.5, "#2563EB") if is_indoor else ft.Border.all(1, "#CBD5E1")
        self.btn_indoor.content.controls[0].icon = ft.Icons.RADIO_BUTTON_CHECKED if is_indoor else ft.Icons.RADIO_BUTTON_UNCHECKED
        self.btn_indoor.content.controls[0].color = "#2563EB" if is_indoor else "#64748B"
        self.btn_indoor.content.controls[1].color = "#2563EB" if is_indoor else "#64748B"

        self.btn_outdoor.bgcolor = ft.Colors.WHITE if is_indoor else "#E8EEFF"
        self.btn_outdoor.border = ft.Border.all(1, "#CBD5E1") if is_indoor else ft.Border.all(1.5, "#2563EB")
        self.btn_outdoor.content.controls[0].icon = ft.Icons.RADIO_BUTTON_UNCHECKED if is_indoor else ft.Icons.RADIO_BUTTON_CHECKED
        self.btn_outdoor.content.controls[0].color = "#64748B" if is_indoor else "#2563EB"
        self.btn_outdoor.content.controls[1].color = "#64748B" if is_indoor else "#2563EB"

        # Lọc danh sách module tương ứng với môi trường đã chọn
        self._filter_modules_by_env(env)
        self._trigger_change(None)
        if getattr(self, "_Control__page", None):
            self.page.update()

    def _set_power_phase(self, phase: str):
        self.power_phase_val = phase
        is_1pha = phase == "1pha"
        self.btn_1pha.bgcolor = "#E8EEFF" if is_1pha else ft.Colors.WHITE
        self.btn_1pha.border = ft.Border.all(1.5, "#2563EB") if is_1pha else ft.Border.all(1, "#CBD5E1")
        self.btn_1pha.content.controls[0].icon = ft.Icons.RADIO_BUTTON_CHECKED if is_1pha else ft.Icons.RADIO_BUTTON_UNCHECKED
        self.btn_1pha.content.controls[0].color = "#2563EB" if is_1pha else "#64748B"
        self.btn_1pha.content.controls[1].color = "#2563EB" if is_1pha else "#64748B"

        self.btn_3pha.bgcolor = ft.Colors.WHITE if is_1pha else "#E8EEFF"
        self.btn_3pha.border = ft.Border.all(1, "#CBD5E1") if is_1pha else ft.Border.all(1.5, "#2563EB")
        self.btn_3pha.content.controls[0].icon = ft.Icons.RADIO_BUTTON_UNCHECKED if is_1pha else ft.Icons.RADIO_BUTTON_CHECKED
        self.btn_3pha.content.controls[0].color = "#64748B" if is_1pha else "#2563EB"
        self.btn_3pha.content.controls[1].color = "#64748B" if is_1pha else "#2563EB"
        if getattr(self, "_Control__page", None):
            self.page.update()

    def _filter_modules_by_env(self, env: str):
        modules = [m for m in self.options.get("modules", []) if m.get("environment") in {env, "both"}]
        self.module_code_dropdown.options = [
            ft.dropdown.Option(key=m["code"], text=m.get("spec_json", {}).get("pitch", m["name"]))
            for m in modules
        ]
        if modules:
            # Nếu mã đang chọn không thuộc môi trường mới thì đổi sang cái đầu tiên
            if not any(m["code"] == self.module_code_dropdown.value for m in modules):
                self.module_code_dropdown.value = modules[0]["code"]
                self.pitch_dropdown.value = modules[0]["code"]
        self._sync_calc_display()

    def _init_module_options(self):
        modules = self.options.get("modules", [])
        self.module_code_dropdown.options = [
            ft.dropdown.Option(key=m["code"], text=m.get("spec_json", {}).get("pitch", m["name"]))
            for m in modules
        ]
        # Mặc định chọn P10 Outdoor nếu có
        default_mod = next((m for m in modules if "P10" in m["code"]), modules[0] if modules else None)
        if default_mod:
            self.module_code_dropdown.value = default_mod["code"]
            self.pitch_dropdown.value = default_mod["code"]
            self.environment.value = default_mod.get("environment", "outdoor")

        powers = self.options.get("powers", [])
        self.power_dropdown.options = [ft.dropdown.Option(key=p["code"], text=p["name"]) for p in powers]
        if powers:
            self.power_dropdown.value = powers[0]["code"]

        frames = self.options.get("frames", [])
        self.frame_dropdown.options = [ft.dropdown.Option(key=f["code"], text=f["name"]) for f in frames]
        if frames:
            self.frame_dropdown.value = frames[0]["code"]

        cards = self.options.get("cards", [])
        self.card_dropdown.options = [ft.dropdown.Option(key=c["code"], text=c["name"]) for c in cards]
        if cards:
            self.card_dropdown.value = cards[0]["code"]

    def _get_current_module(self) -> Dict:
        code = self.module_code_dropdown.value
        for m in self.options.get("modules", []):
            if m["code"] == code:
                return m
        return self.options.get("modules", [{}])[0]

    def _on_module_code_selected(self, e):
        mod = self._get_current_module()
        self.pitch_dropdown.value = mod.get("code")
        self.environment.value = mod.get("environment", "indoor")
        self._sync_calc_display()
        self._trigger_change(e)

    def _change_modules_w(self, delta: int):
        self.num_modules_w = max(1, self.num_modules_w + delta)
        self.txt_modules_w.value = str(self.num_modules_w)
        self._sync_calc_display()
        self._trigger_change(None)

    def _on_txt_modules_w_changed(self, e):
        val = (self.txt_modules_w.value or "").strip()
        if val.isdigit() and int(val) > 0:
            self.num_modules_w = int(val)
            self._sync_calc_display()
            self._trigger_change(None)

    def _change_modules_h(self, delta: int):
        self.num_modules_h = max(1, self.num_modules_h + delta)
        self.txt_modules_h.value = str(self.num_modules_h)
        self._sync_calc_display()
        self._trigger_change(None)

    def _on_txt_modules_h_changed(self, e):
        val = (self.txt_modules_h.value or "").strip()
        if val.isdigit() and int(val) > 0:
            self.num_modules_h = int(val)
            self._sync_calc_display()
            self._trigger_change(None)

    def _change_reserve(self, delta: int):
        self.num_reserve_modules = max(0, self.num_reserve_modules + delta)
        self.txt_reserve_modules.value = str(self.num_reserve_modules)
        self._sync_calc_display()
        self._trigger_change(None)

    def _on_txt_reserve_changed(self, e):
        val = (self.txt_reserve_modules.value or "").strip()
        if val.isdigit() and int(val) >= 0:
            self.num_reserve_modules = int(val)
            self._sync_calc_display()
            self._trigger_change(None)

    def _on_manual_dimension_changed(self, e):
        # Khi ở chế độ thủ công và người dùng trực tiếp sửa kích thước mm
        if self.config_mode == "manual":
            try:
                w_mm = float((self.calc_w_mm.value or "0").replace(".", "").replace(",", "."))
                h_mm = float((self.calc_h_mm.value or "0").replace(".", "").replace(",", "."))
                self.width_input.value = f"{w_mm / 1000:.3f}"
                self.height_input.value = f"{h_mm / 1000:.3f}"
                self.preview_header_size.value = f"{int(w_mm):,} × {int(h_mm):,} mm".replace(",", ".")
            except ValueError:
                pass
            self._trigger_change(None)

    def _sync_calc_display(self):
        mod = self._get_current_module()
        spec = mod.get("spec_json", {})
        w_mm = float(spec.get("width_mm", 320))
        h_mm = float(spec.get("height_mm", 160))
        px_w = int(spec.get("pixel_w", 32))
        px_h = int(spec.get("pixel_h", 16))
        pitch = spec.get("pitch", "P10")

        # Cập nhật card thông số module mẫu
        self.module_spec_name.value = f"Module {pitch}"
        self.module_spec_details.value = f"{int(w_mm)} × {int(h_mm)} mm  /  {px_w} × {px_h} px"

        # Tính toán
        total_w_mm = self.num_modules_w * w_mm
        total_h_mm = self.num_modules_h * h_mm
        total_px_w = self.num_modules_w * px_w
        total_px_h = self.num_modules_h * px_h
        installed = self.num_modules_w * self.num_modules_h
        total_mod = installed + self.num_reserve_modules
        total_px = total_px_w * total_px_h

        self.calc_w_mm.value = f"{int(total_w_mm):,}".replace(",", ".")
        self.calc_w_px.value = str(total_px_w)
        self.calc_h_mm.value = f"{int(total_h_mm):,}".replace(",", ".")
        self.calc_h_px.value = str(total_px_h)

        self.calc_installed_modules.value = str(installed)
        self.calc_total_modules.value = str(total_mod)
        self.calc_total_pixels.value = f"{total_px:,}".replace(",", ".")

        # Cập nhật các trường gửi về Engine Calculator
        self.width_input.value = f"{total_w_mm / 1000:.3f}"
        self.height_input.value = f"{total_h_mm / 1000:.3f}"
        if installed > 0:
            reserve_pct = (self.num_reserve_modules / installed) * 100
            self.reserve_input.value = f"{reserve_pct:.2f}"

        # Cập nhật Sơ đồ ma trận Module Preview
        self.preview_header_size.value = f"{int(total_w_mm):,} × {int(total_h_mm):,} mm".replace(",", ".")
        self.preview_header_grid.value = f"{self.num_modules_w} cột × {self.num_modules_h} hàng"
        self.preview_footer_note.value = f"Sơ đồ minh họa • {installed} module lắp"

        # Vẽ lưới (tối đa 10 cột × 6 hàng để vừa giao diện điện thoại)
        show_cols = min(self.num_modules_w, 10)
        show_rows = min(self.num_modules_h, 6)
        cell_width = max(16, min(28, int(260 / show_cols))) if show_cols else 20
        cell_height = 14

        self.preview_grid_column.controls = [
            ft.Row(
                spacing=3,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=cell_width,
                        height=cell_height,
                        border_radius=3,
                        bgcolor="#2563EB" if r == 0 else "#93C5FD",
                    )
                    for c in range(show_cols)
                ],
            )
            for r in range(show_rows)
        ]

    def _trigger_change(self, e):
        self.on_change(e)

    def update_layout_preview(self, summary: Dict, message: str = ""):
        # Tương thích với callback từ MainView
        pass

    # -------------------------------------------------------------
    # Tương thích các hàm thêm / xóa / get / set
    # -------------------------------------------------------------
    def add_additional(self, name: str, qty, unit_price):
        self._add_additional_item()
        name_field, qty_field, price_field, _ = self.additional_items[-1]
        name_field.value = name
        qty_field.value = str(qty)
        price_field.value = str(int(unit_price))
        self.on_change(None)

    def additional_qty_by_name(self, name: str) -> float:
        total = 0.0
        for name_field, qty_field, _, _ in self.additional_items:
            if (name_field.value or "").strip() == name:
                try:
                    total += float(str(qty_field.value).replace(",", "."))
                except ValueError:
                    pass
        return total

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

    def _remove_additional_item(self, item):
        self.additional_items.remove(item)
        self.additional_rows.controls.remove(item[3])
        self.on_change(None)

    def set_values(self, values: Dict):
        for control, key in (
            (self.customer_name, "customer_name"),
            (self.project_name, "project_name"),
            (self.customer_phone, "customer_phone"),
            (self.screen_quantity, "screen_quantity"),
            (self.profit_input, "profit_percent"),
            (self.vat_input, "vat_percent"),
        ):
            if key in values:
                control.value = str(values[key])

        if "module_code" in values:
            self.module_code_dropdown.value = values["module_code"]
            self.pitch_dropdown.value = values["module_code"]
        if "power_code" in values:
            self.power_dropdown.value = values["power_code"]
        if "card_code" in values:
            self.card_dropdown.value = values["card_code"]
        if "frame_code" in values:
            self.frame_dropdown.value = values["frame_code"]

        # Kích thước W / H (m) -> suy ra số module
        mod = self._get_current_module()
        w_mm = float(mod.get("spec_json", {}).get("width_mm", 320))
        h_mm = float(mod.get("spec_json", {}).get("height_mm", 160))
        if "width_m" in values and w_mm > 0:
            self.num_modules_w = max(1, round(float(values["width_m"]) * 1000 / w_mm))
            self.txt_modules_w.value = str(self.num_modules_w)
        if "height_m" in values and h_mm > 0:
            self.num_modules_h = max(1, round(float(values["height_m"]) * 1000 / h_mm))
            self.txt_modules_h.value = str(self.num_modules_h)

        self._sync_calc_display()

    def get_values(self) -> Dict:
        mod = self._get_current_module()
        code = mod.get("code") or self.module_code_dropdown.value
        return {
            "config_mode": self.config_mode,
            "environment": mod.get("environment", "both"),
            "module_code": code,
            "display_mode": self.display_mode_val,
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
            "customer_name": (self.customer_name.value or "").strip(),
            "project_name": (self.project_name.value or "").strip(),
            "customer_phone": (self.customer_phone.value or "").strip(),
            "screen_quantity": self.screen_quantity.value or "1",
            "profit_percent": self.profit_input.value or "20",
            "vat_percent": self.vat_input.value or "8",
            "reserve_percent": self.reserve_input.value or "3",
            "additional_items": [
                {
                    "name": name.value.strip(),
                    "qty": quantity.value,
                    "unit_price": price.value,
                    "unit": "item",
                }
                for name, quantity, price, _ in self.additional_items
                if name.value and name.value.strip()
            ],
        }
