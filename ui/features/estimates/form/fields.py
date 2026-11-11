"""Dedicated constructors for the form's groups of controls.

All constructors are called in the original dependency order.
"""
import math
from typing import Any, Callable, Dict, List
import flet as ft

from ui.theme.tokens import UIColors

class FormFieldsMixin:
    def _create_mode_controls(self):
        # Chế độ cấu hình: Tự động vs Thủ công
        self.config_mode = "auto"  # "auto" | "manual"

        # Tab chế độ: Tự động / Thủ công
        self.mode_btn_auto = ft.Container(
            expand=True,
            height=40,
            border_radius=10,
            ink=True,
            bgcolor=UIColors.PRIMARY,
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
            border=ft.Border.all(1, UIColors.BORDER),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_mode("manual"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.EDIT_OUTLINED, size=16, color=UIColors.TEXT_SECONDARY),
                    ft.Text("Thủ công", size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_SECONDARY),
                ],
            ),
        )

        # Mô tả chế độ
        self.mode_description = ft.Text(
            "Nhập số module; thông số lấy từ module đã khai báo.",
            size=11,
            color=UIColors.TEXT_SECONDARY,
        )


    def _create_display_controls(self):
        # Trình chiếu: Online vs Offline
        self.display_mode_val = "online"  # "online" | "offline"
        self.btn_online = ft.Container(
            expand=True,
            height=44,
            border_radius=10,
            ink=True,
            bgcolor=UIColors.PRIMARY_SOFT,
            border=ft.Border.all(1.5, UIColors.PRIMARY),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_display_mode("online"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED, size=18, color=UIColors.PRIMARY),
                    ft.Text("Online", size=13, weight=ft.FontWeight.W_700, color=UIColors.PRIMARY),
                ],
            ),
        )
        self.btn_offline = ft.Container(
            expand=True,
            height=44,
            border_radius=10,
            ink=True,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, UIColors.BORDER_STRONG),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_display_mode("offline"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, size=18, color=UIColors.TEXT_SECONDARY),
                    ft.Text("Offline", size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_SECONDARY),
                ],
            ),
        )


    def _create_environment_controls(self):
        # Internal calculator uses indoor/outdoor. UI choices come ONLY from ERP.
        self.env_mode_val = None


    def _create_module_and_dimension_controls(self):
        # Hãng module & Mã module
        self.module_brand_dropdown = ft.Dropdown(
            label="Hãng module",
            hint_text="Chọn hãng",
            expand=True,
            **self._dropdown_style(),
            options=[],
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

        # Chỉ hiển thị thông số thật của module đã được khai báo.
        self.module_spec_name = ft.Text("Chưa chọn module", size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY)
        self.module_spec_details = ft.Text("Chưa có thông số", size=11, color=UIColors.TEXT_SECONDARY)
        self.module_spec_box = ft.Container(
            padding=ft.Padding(12, 10, 12, 10),
            bgcolor=UIColors.SURFACE_SUBTLE,
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
                                bgcolor=UIColors.PRIMARY_SOFT,
                                border_radius=6,
                                content=ft.Text("Thông số module", size=10, weight=ft.FontWeight.W_600, color=UIColors.PRIMARY),
                            ),
                        ],
                    ),
                    self.module_spec_details,
                    ft.Text("Dữ liệu lấy từ danh mục linh kiện được khai báo trong ứng dụng.", size=10, color=UIColors.TEXT_SUBTLE),
                ],
            ),
        )

        # Sơ đồ ma trận module preview
        self.preview_header_size = ft.Text("Chưa có kích thước", size=12, weight=ft.FontWeight.W_700, color=UIColors.PRIMARY)
        self.preview_header_grid = ft.Text("Chưa có dữ liệu module", size=11, color=UIColors.TEXT_SECONDARY)
        self.preview_grid_column = ft.Column(spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.preview_footer_note = ft.Text("", size=10, color=UIColors.TEXT_SECONDARY)

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
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY),
            dense=True,
            content_padding=ft.Padding(0, 4, 0, 4),
            on_change=self._on_txt_modules_w_changed,
        )
        self.calc_w_mm = ft.TextField(
            label="Kích thước hiển thị W",
            value="2.560",
            suffix=ft.Text("mm", size=12, color=UIColors.TEXT_SECONDARY),
            read_only=True,
            expand=True,
            on_change=self._on_manual_dimension_changed,
            **self._read_only_field_style(),
        )
        self.calc_w_px = ft.TextField(
            label="Độ phân giải W",
            value="256",
            suffix=ft.Text("px", size=12, color=UIColors.TEXT_SECONDARY),
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
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY),
            dense=True,
            content_padding=ft.Padding(0, 4, 0, 4),
            on_change=self._on_txt_modules_h_changed,
        )
        self.calc_h_mm = ft.TextField(
            label="Kích thước hiển thị H",
            value="640",
            suffix=ft.Text("mm", size=12, color=UIColors.TEXT_SECONDARY),
            read_only=True,
            expand=True,
            on_change=self._on_manual_dimension_changed,
            **self._read_only_field_style(),
        )
        self.calc_h_px = ft.TextField(
            label="Độ phân giải H",
            value="64",
            suffix=ft.Text("px", size=12, color=UIColors.TEXT_SECONDARY),
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
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY),
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
            suffix=ft.Text("px", size=12, color=UIColors.TEXT_SECONDARY),
            read_only=True,
            expand=True,
            on_change=self._trigger_change,
            **self._read_only_field_style(),
        )

        self.reserve_note_text = ft.Text(
            "Module lắp = W × H = 8 × 4 = 32.\nTổng module = module lắp + dự phòng = 34.\nTổng pixel = 256 × 64 = 16.384 px, không tính module dự phòng.",
            size=10,
            color=UIColors.TEXT_SUBTLE,
        )


    def _create_general_information_controls(self):
        # Phần Thông tin chung (Header & Warning box)
        self.general_mode_tag = ft.Text("Tự động tính*", size=12, color=UIColors.PRIMARY)
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
            options=[],
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
            options=[],
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
            bgcolor=UIColors.PRIMARY_SOFT,
            border=ft.Border.all(1.5, UIColors.PRIMARY),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_power_phase("1pha"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED, size=18, color=UIColors.PRIMARY),
                    ft.Text("1 pha", size=13, weight=ft.FontWeight.W_700, color=UIColors.PRIMARY),
                ],
            ),
        )
        self.btn_3pha = ft.Container(
            expand=True,
            height=42,
            border_radius=10,
            ink=True,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, UIColors.BORDER_STRONG),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self._set_power_phase("3pha"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, size=18, color=UIColors.TEXT_SECONDARY),
                    ft.Text("3 pha", size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_SECONDARY),
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


    def _create_material_controls(self):
        # -------------------------------------------------------------
        # Các trường bổ sung theo ảnh định mức ERP, đồng bộ theo UI có sẵn
        # -------------------------------------------------------------
        # Module
        self.m_sl_module = ft.TextField(
            label="Số lượng",
            value="34",
            text_align=ft.TextAlign.RIGHT,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=85,
            **self._field_style(),
            on_change=self._trigger_change,
        )

        # Nguồn
        self.m_sl_nguon = ft.TextField(
            label="Số lượng",
            value="4",
            text_align=ft.TextAlign.RIGHT,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=85,
            **self._field_style(),
            on_change=self._trigger_change,
        )

        # Bộ xử lý
        self.m_ma_bxl = ft.Dropdown(
            label="Mã bộ xử lý",
            options=[],
            expand=True,
            **self._dropdown_style(),
            on_select=self._trigger_change,
        )
        self.m_sl_bxl = ft.TextField(
            label="Số lượng",
            value="1",
            text_align=ft.TextAlign.RIGHT,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=85,
            **self._field_style(),
            on_change=self._trigger_change,
        )

        # Card & sắp xếp
        self.m_ma_card = ft.Dropdown(
            label="Mã card",
            options=[],
            expand=True,
            **self._dropdown_style(),
            on_select=self._trigger_change,
        )
        self.m_quy_cach = ft.Dropdown(
            label="Hình thức sắp xếp",
            options=[
                ft.dropdown.Option("Mặc định"),
                ft.dropdown.Option("Theo cột (W x H)"),
                ft.dropdown.Option("Theo hàng (H x W)"),
                ft.dropdown.Option("So le"),
                ft.dropdown.Option("Cabinet chuẩn"),
            ],
            value="Mặc định",
            expand=True,
            **self._dropdown_style(),
            on_select=self._trigger_change,
        )
        self.m_sl_card = ft.TextField(
            label="Số lượng",
            value="2",
            text_align=ft.TextAlign.RIGHT,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=85,
            **self._field_style(),
            on_change=self._trigger_change,
        )

        # Cabinet 1 -> 4
        self.m_ma_cbn1 = ft.Dropdown(label="Mã cabinet 1", options=[], expand=True, **self._dropdown_style(), on_select=self._trigger_change)
        self.m_sl_cbn1 = ft.TextField(label="Số lượng", value="0", text_align=ft.TextAlign.RIGHT, keyboard_type=ft.KeyboardType.NUMBER, width=85, **self._field_style(), on_change=self._trigger_change)
        self.m_ma_cbn2 = ft.Dropdown(label="Mã cabinet 2", options=[], expand=True, **self._dropdown_style(), on_select=self._trigger_change)
        self.m_sl_cbn2 = ft.TextField(label="Số lượng", value="0", text_align=ft.TextAlign.RIGHT, keyboard_type=ft.KeyboardType.NUMBER, width=85, **self._field_style(), on_change=self._trigger_change)
        self.m_ma_cbn3 = ft.Dropdown(label="Mã cabinet 3", options=[], expand=True, **self._dropdown_style(), on_select=self._trigger_change)
        self.m_sl_cbn3 = ft.TextField(label="Số lượng", value="0", text_align=ft.TextAlign.RIGHT, keyboard_type=ft.KeyboardType.NUMBER, width=85, **self._field_style(), on_change=self._trigger_change)
        self.m_ma_cbn4 = ft.Dropdown(label="Mã cabinet 4", options=[], expand=True, **self._dropdown_style(), on_select=self._trigger_change)
        self.m_sl_cbn4 = ft.TextField(label="Số lượng", value="0", text_align=ft.TextAlign.RIGHT, keyboard_type=ft.KeyboardType.NUMBER, width=85, **self._field_style(), on_change=self._trigger_change)

        # Alu & Quạt & Điện
        self.m_ma_alu = ft.Dropdown(
            label="Alu theo khung",
            options=[ft.dropdown.Option("Không dùng"), ft.dropdown.Option("Alu ngoài trời 3mm"), ft.dropdown.Option("Alu trong nhà 2mm"), ft.dropdown.Option("Alu Alcorest 3mm 0.10")],
            value="Không dùng",
            expand=True,
            **self._dropdown_style(),
            on_select=self._trigger_change,
        )
        self.m_dien_tich = ft.TextField(
            label="Alu theo diện tích",
            value="0.00",
            suffix=ft.Text("m²", size=12, color=UIColors.TEXT_SECONDARY),
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
            **self._field_style(),
            on_change=self._trigger_change,
        )
        self.m_ma_alu_dt = ft.Dropdown(
            label="Mã Alu diện tích",
            options=[ft.dropdown.Option("Không dùng"), ft.dropdown.Option("Alu ngoài trời 3mm"), ft.dropdown.Option("Alu trong nhà 2mm"), ft.dropdown.Option("Alu Alcorest 3mm")],
            value="Không dùng",
            expand=True,
            **self._dropdown_style(),
            on_select=self._trigger_change,
        )
        self.m_ma_quat5v = ft.Dropdown(
            label="Quạt 5v",
            options=[ft.dropdown.Option("Không dùng"), ft.dropdown.Option("Quạt 5V 0.15A"), ft.dropdown.Option("Quạt 5V 0.20A"), ft.dropdown.Option("Quạt tản nhiệt 120mm 5V")],
            value="Không dùng",
            expand=True,
            **self._dropdown_style(),
            on_select=self._trigger_change,
        )
        self.m_loai_tu_dien = ft.Dropdown(
            label="Loại tủ điện",
            options=[ft.dropdown.Option("Không dùng"), ft.dropdown.Option("Tủ điện 1 Pha 30A"), ft.dropdown.Option("Tủ điện 1 Pha 60A"), ft.dropdown.Option("Tủ điện 3 Pha 50A"), ft.dropdown.Option("Tủ điện 3 Pha 100A")],
            value="Không dùng",
            expand=True,
            **self._dropdown_style(),
            on_select=self._trigger_change,
        )
        self.m_tiet_dien = ft.Dropdown(
            label="Tiết diện dây",
            options=[ft.dropdown.Option("Chưa thiết lập"), ft.dropdown.Option("Dây 2x1.5 mm²"), ft.dropdown.Option("Dây 2x2.5 mm²"), ft.dropdown.Option("Dây 2x4.0 mm²"), ft.dropdown.Option("Dây 2x6.0 mm²"), ft.dropdown.Option("Dây 4x4.0 mm² (3 pha)")],
            value="Chưa thiết lập",
            expand=True,
            **self._dropdown_style(),
            on_select=self._trigger_change,
        )
        self.m_check_tu_dien = ft.Checkbox(label="Có tủ điện", value=False, on_change=self._trigger_change)
        self.m_check_1pha = ft.Checkbox(label="1 Pha", value=True, on_change=self._on_m_pha_changed)
        self.m_check_3pha = ft.Checkbox(label="3 Pha", value=False, on_change=self._on_m_pha_changed)

        # Nút Tính chi phí
        self.m_btn_calc = ft.FilledButton(
            "Tính chi phí",
            icon=ft.Icons.CALCULATE_OUTLINED,
            height=42,
            style=ft.ButtonStyle(
                bgcolor=UIColors.PRIMARY,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(24, 10, 24, 10),
            ),
            on_click=self._on_manual_calc_clicked,
        )


    def _create_compatibility_controls(self):
        # Alias các trường đồng bộ với các trường có sẵn
        self.m_hang_module = self.module_brand_dropdown
        self.m_ma_module = self.module_code_dropdown
        self.m_hang_nguon = self.power_brand_dropdown
        self.m_ma_nguon = self.power_dropdown
        self.m_hang_bxl = self.processor_brand_dropdown
        self.m_loai_cb = self.cb_dropdown

        # Container tương thích chế độ
        self.auto_container = ft.Container(visible=True)
        self.manual_container = ft.Container(visible=False)

        # Các trường ẩn tương thích ngược cho engine tính toán
        self.environment = ft.RadioGroup(value=None, content=ft.Container())
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
