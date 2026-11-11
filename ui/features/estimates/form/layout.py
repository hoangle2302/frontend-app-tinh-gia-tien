"""FormLayoutMixin: isolated UI responsibilities; inherited by the screen coordinator.

Preserves original control construction and callbacks for migration safety.
"""
import math
from typing import Any, Callable, Dict, List
import flet as ft


from ui.theme.tokens import UIColors

class FormLayoutMixin:
    def _build_layout(self):
        # 1. Header: Cấu hình LED
        header_block = ft.Column(
            spacing=4,
            controls=[
                ft.Text("Cấu hình LED", size=24, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
                ft.Text("Thiết lập thông số trước khi lập bảng dự toán.", size=12, color=UIColors.TEXT_SECONDARY),
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
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color=UIColors.PRIMARY),
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
                # A single required dropdown; choices are loaded from ERP get_screen_type_rows().
                self.erp_screen_types_dropdown,
                ft.Text("Loại trình chiếu", size=12, weight=ft.FontWeight.W_600, color=UIColors.TEXT_PRIMARY),
                ft.Row(spacing=8, controls=[self.btn_online, self.btn_offline]),
                ft.Row(spacing=8, controls=[self.module_brand_dropdown, self.module_code_dropdown, self.m_sl_module]),
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
                            content=ft.Text("W", size=11, weight=ft.FontWeight.W_700, color=UIColors.PRIMARY),
                        ),
                        ft.Text("Chiều rộng", size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY),
                    ],
                ),
                ft.Text("Số module W", size=12, color=UIColors.TEXT_SECONDARY),
                self._stepper_row(self.txt_modules_w, lambda delta: self._change_modules_w(delta)),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Column(expand=True, spacing=2, controls=[self.tag_w_mm, self.calc_w_mm]),
                        ft.Column(expand=True, spacing=2, controls=[self.tag_w_px, self.calc_w_px]),
                    ],
                ),
                ft.Text("Rộng hiển thị = số module W × rộng 1 module.\nĐộ phân giải W = số module W × độ phân giải W của 1 module.", size=10, color=UIColors.TEXT_SUBTLE),
                ft.Divider(color=UIColors.BORDER, height=1),
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
                            content=ft.Text("H", size=11, weight=ft.FontWeight.W_700, color=UIColors.PRIMARY),
                        ),
                        ft.Text("Chiều cao", size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY),
                    ],
                ),
                ft.Text("Số module H", size=12, color=UIColors.TEXT_SECONDARY),
                self._stepper_row(self.txt_modules_h, lambda delta: self._change_modules_h(delta)),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Column(expand=True, spacing=2, controls=[self.tag_h_mm, self.calc_h_mm]),
                        ft.Column(expand=True, spacing=2, controls=[self.tag_h_px, self.calc_h_px]),
                    ],
                ),
                ft.Text("Cao hiển thị = số module H × cao 1 module.\nĐộ phân giải H = số module H × độ phân giải H của 1 module.", size=10, color=UIColors.TEXT_SUBTLE),
            ],
        )

        # Card 3: Dự phòng & tổng module
        self.card_reserve = self._card_container(
            title="Dự phòng & tổng module",
            icon=ft.Icons.LAYERS_OUTLINED,
            controls=[
                ft.Text("Số module dự phòng", size=12, color=UIColors.TEXT_SECONDARY),
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
                ft.Text("Thông tin chung", size=16, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
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
                ft.Row(spacing=8, controls=[self.power_brand_dropdown, self.power_dropdown, self.m_sl_nguon]),
                self.power_capacity_hint,
                ft.Row(spacing=8, controls=[self.processor_brand_dropdown, self.m_ma_bxl, self.m_sl_bxl]),
                ft.Row(spacing=8, controls=[self.m_ma_card, self.m_quy_cach, self.m_sl_card]),
            ],
        )

        self.card_frame = self._card_container(
            title="Khung & vật liệu",
            icon=ft.Icons.CROP_FREE,
            controls=[
                self.frame_dropdown,
                ft.Row(spacing=8, controls=[self.m_ma_cbn1, self.m_sl_cbn1]),
                ft.Row(spacing=8, controls=[self.m_ma_cbn2, self.m_sl_cbn2]),
                ft.Row(spacing=8, controls=[self.m_ma_cbn3, self.m_sl_cbn3]),
                ft.Row(spacing=8, controls=[self.m_ma_cbn4, self.m_sl_cbn4]),
                self.m_ma_alu,
                ft.Row(spacing=8, controls=[self.m_dien_tich, self.m_ma_alu_dt]),
                ft.Text("Cần xác nhận tên mục", size=10, color="#B45309"),
            ],
        )

        self.card_electric = self._card_container(
            title="Điện & phụ trợ",
            icon=ft.Icons.BOLT,
            controls=[
                ft.Text("Nguồn điện", size=12, weight=ft.FontWeight.W_600, color=UIColors.TEXT_PRIMARY),
                ft.Row(spacing=8, controls=[self.btn_1pha, self.btn_3pha]),
                self.m_ma_quat5v,
                self.m_loai_tu_dien,
                self.cb_dropdown,
                self.cf_dropdown,
                self.m_tiet_dien,
                self.power_compensation_dropdown,
                ft.Container(
                    padding=ft.Padding(0, 8, 0, 0),
                    alignment=ft.Alignment(0, 0),
                    content=self.m_btn_calc,
                ),
                ft.Text("Các lựa chọn điện cần được xác nhận theo thông số kỹ thuật và phương án lắp đặt thực tế.", size=10, color=UIColors.TEXT_SECONDARY),
            ],
        )

        footer_note = ft.Column(
            spacing=2,
            controls=[
                ft.Text("Dữ liệu minh họa • Cần xác nhận thông số kỹ thuật", size=11, color="#B45309"),
                ft.Text("Nguồn tham khảo: toantrung.com.vn", size=11, color=UIColors.TEXT_SECONDARY),
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

    def apply_theme(self, is_dark: bool):
        bg_card = UIColors.DARK_SURFACE if is_dark else ft.Colors.WHITE
        border_card = "#42474E" if is_dark else UIColors.BORDER
        text_primary = "#E0E2E8" if is_dark else UIColors.TEXT_PRIMARY
        text_secondary = "#8C9199" if is_dark else UIColors.TEXT_SECONDARY

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
            self.module_spec_box.bgcolor = UIColors.SURFACE_SUBTLE
            self.module_spec_box.border = ft.Border.all(1, "#F1F5F9")
            self.module_spec_name.color = UIColors.TEXT_PRIMARY
            self.preview_container.bgcolor = "#F0F5FF"
            self.preview_container.border = ft.Border.all(1, "#D0E0FF")
            self.warning_general.bgcolor = "#FFFBEB"
            self.warning_general.border = ft.Border.all(1, "#FDE68A")

        # Cập nhật các nút lựa chọn chưa được active
        inactive_bg = UIColors.DARK_SURFACE if is_dark else ft.Colors.WHITE
        inactive_border = "#42474E" if is_dark else UIColors.BORDER_STRONG
        for btn, is_active in [
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
            content=ft.Text(text, size=10, weight=ft.FontWeight.W_600, color=UIColors.PRIMARY),
        )

    def _card_container(self, title: str, icon, controls: list):
        return ft.Container(
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border_radius=14,
            border=ft.Border.all(1, UIColors.BORDER),
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
                                content=ft.Icon(icon, size=18, color=UIColors.PRIMARY),
                            ),
                            ft.Text(title, size=15, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
                        ],
                    ),
                    *controls,
                ],
            ),
        )

    def _stepper_row(self, label_control: ft.Text, on_change_callback):
        return ft.Container(
            border=ft.Border.all(1, UIColors.BORDER_STRONG),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.REMOVE,
                        icon_size=18,
                        icon_color=UIColors.TEXT_SECONDARY,
                        on_click=lambda e: on_change_callback(-1),
                    ),
                    label_control,
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        icon_size=18,
                        icon_color=UIColors.TEXT_SECONDARY,
                        on_click=lambda e: on_change_callback(1),
                    ),
                ],
            ),
        )
