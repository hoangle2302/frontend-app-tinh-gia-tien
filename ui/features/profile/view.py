from typing import Any, Callable, Dict
import flet as ft

from database.db_manager import DBManager
from ui.components.input_panel import InputPanel


from ui.theme.tokens import UIColors
from ui.features.profile.actions import ProfileActionsMixin

class ProfileView(ProfileActionsMixin, ft.Container):
    def __init__(
        self,
        page: ft.Page,
        db: DBManager,
        on_profile_updated: Callable = None,
        on_logout: Callable = None,
    ):
        super().__init__()
        self._app_page = page
        self.db = db
        self.on_profile_updated = on_profile_updated
        self.on_logout = on_logout
        self.expand = True
        self.padding = ft.Padding(16, 12, 16, 16)

        profile = self.db.get_company_profile()

        # Input fields: để riêng từng dòng để hiển thị trọn vẹn số điện thoại, email, MST, website
        self.company_name = ft.TextField(
            label="Tên doanh nghiệp",
            value=profile.get("company_name", ""),
            prefix_icon=ft.Icons.BUSINESS_ROUNDED,
            **InputPanel._field_style(),
        )

        self.address = ft.TextField(
            label="Địa chỉ trụ sở / Xưởng sản xuất",
            value=profile.get("address", ""),
            prefix_icon=ft.Icons.LOCATION_ON_OUTLINED,
            multiline=True,
            min_lines=2,
            max_lines=3,
            **InputPanel._field_style(),
        )

        self.phone = ft.TextField(
            label="Hotline / Số điện thoại",
            value=profile.get("phone", ""),
            prefix_icon=ft.Icons.PHONE_IN_TALK_OUTLINED,
            **InputPanel._field_style(),
        )

        self.email = ft.TextField(
            label="Email liên hệ",
            value=profile.get("email", ""),
            prefix_icon=ft.Icons.MAIL_OUTLINE_ROUNDED,
            **InputPanel._field_style(),
        )

        self.tax_code = ft.TextField(
            label="Mã số thuế (MST)",
            value=profile.get("tax_code", ""),
            prefix_icon=ft.Icons.BADGE_OUTLINED,
            **InputPanel._field_style(),
        )

        self.website = ft.TextField(
            label="Website công ty",
            value=profile.get("website", ""),
            prefix_icon=ft.Icons.LANGUAGE_ROUNDED,
            **InputPanel._field_style(),
        )

        self.bank_account = ft.TextField(
            label="Tài khoản thanh toán / Ngân hàng",
            value=profile.get("bank_account", ""),
            prefix_icon=ft.Icons.ACCOUNT_BALANCE_OUTLINED,
            multiline=True,
            min_lines=2,
            max_lines=3,
            **InputPanel._field_style(),
        )

        # Cấu hình mặc định
        self.default_vat = ft.TextField(
            label="VAT mặc định (%)",
            value=str(profile.get("default_vat", 8.0)),
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.RECEIPT_LONG,
            expand=True,
            **InputPanel._field_style(),
        )

        self.default_profit = ft.TextField(
            label="Lợi nhuận mặc định (%)",
            value=str(profile.get("default_profit", 20.0)),
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.TRENDING_UP,
            expand=True,
            **InputPanel._field_style(),
        )

        self.default_warranty = ft.TextField(
            label="Thời gian bảo hành (tháng)",
            value=str(profile.get("default_warranty_months", 24)),
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.VERIFIED_OUTLINED,
            **InputPanel._field_style(),
        )

        self.notes = ft.TextField(
            label="Ghi chú & Điều khoản mẫu trên Báo giá",
            value=profile.get("notes", ""),
            prefix_icon=ft.Icons.NOTES_ROUNDED,
            multiline=True,
            min_lines=2,
            max_lines=4,
            **InputPanel._field_style(),
        )

        self.status_msg = ft.Text("", size=13, weight=ft.FontWeight.W_500, visible=False)

        # Các nút chức năng
        self.save_btn = ft.FilledButton(
            "Lưu thông tin hồ sơ",
            icon=ft.Icons.SAVE_OUTLINED,
            height=46,
            style=InputPanel._primary_button_style(),
            on_click=self._handle_save_profile,
        )

        self.reset_btn = ft.OutlinedButton(
            "Khôi phục mặc định",
            icon=ft.Icons.RESTART_ALT_ROUNDED,
            expand=True,
            height=44,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                side=ft.BorderSide(1, UIColors.BORDER_STRONG),
                padding=ft.Padding(8, 0, 8, 0),
            ),
            on_click=self._handle_reset_defaults,
        )

        self.backup_btn = ft.OutlinedButton(
            "Sao lưu dữ liệu",
            icon=ft.Icons.BACKUP_OUTLINED,
            expand=True,
            height=44,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                side=ft.BorderSide(1, UIColors.BORDER_STRONG),
                padding=ft.Padding(8, 0, 8, 0),
            ),
            on_click=self._handle_backup_db,
        )

        self.logout_btn = ft.FilledButton(
            "Đăng xuất khỏi hệ thống",
            icon=ft.Icons.LOGOUT_ROUNDED,
            height=46,
            style=ft.ButtonStyle(
                bgcolor="#BA1A1A",
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda e: self.on_logout(self._app_page) if self.on_logout else None,
        )

        self.main_column = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            width=4,
                            height=24,
                            bgcolor=UIColors.PRIMARY,
                            border_radius=2,
                        ),
                        ft.Column(
                            spacing=1,
                            controls=[
                                ft.Text("Hồ sơ & Cài đặt hệ thống", size=20, weight=ft.FontWeight.BOLD, color=UIColors.TEXT_PRIMARY),
                                ft.Text("Thông tin pháp lý, điều khoản báo giá & quản lý tài khoản", size=12, color=UIColors.TEXT_SECONDARY),
                            ],
                        ),
                    ],
                ),
                self._section_card(
                    "Thông tin pháp nhân & Liên hệ",
                    [
                        self.company_name,
                        self.address,
                        self.phone,
                        self.email,
                        self.tax_code,
                        self.website,
                        self.bank_account,
                    ],
                ),
                self._section_card(
                    "Cấu hình & Điều khoản báo giá mẫu",
                    [
                        ft.Row([self.default_vat, self.default_profit], spacing=8),
                        self.default_warranty,
                        self.notes,
                    ],
                ),
                self.status_msg,
                self.save_btn,
                self._section_card(
                    "Tiện ích & Hệ thống",
                    [
                        ft.Row([self.reset_btn, self.backup_btn], spacing=8),
                        self.logout_btn,
                    ],
                ),
                ft.Container(height=40),
            ],
        )

        self.inner_wrapper = ft.Container(
            content=self.main_column,
            expand=True,
        )

        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            controls=[self.inner_wrapper],
        )

    def on_resize(self, page_width: float):
        if page_width >= 900:
            self.inner_wrapper.width = 720
            self.inner_wrapper.expand = False
        else:
            self.inner_wrapper.width = None
            self.inner_wrapper.expand = True

    def _section_card(self, title: str, controls):
        return ft.Card(
            elevation=0,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(
                radius=14,
                side=ft.BorderSide(width=1, color=UIColors.BORDER),
            ),
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    width=4,
                                    height=16,
                                    bgcolor=UIColors.PRIMARY,
                                    border_radius=2,
                                ),
                                ft.Text(
                                    title,
                                    size=15,
                                    weight=ft.FontWeight.BOLD,
                                    color=UIColors.TEXT_PRIMARY,
                                ),
                            ],
                        ),
                        *controls,
                    ],
                ),
            ),
        )
