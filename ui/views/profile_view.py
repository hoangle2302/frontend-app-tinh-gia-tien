from typing import Any, Callable, Dict
import flet as ft

from database.db_manager import DBManager
from ui.components.input_panel import InputPanel


class ProfileView(ft.Container):
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
                side=ft.BorderSide(1, "#C2C7CF"),
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
                side=ft.BorderSide(1, "#C2C7CF"),
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
                            bgcolor="#004A98",
                            border_radius=2,
                        ),
                        ft.Column(
                            spacing=1,
                            controls=[
                                ft.Text("Hồ sơ & Cài đặt hệ thống", size=20, weight=ft.FontWeight.BOLD, color="#191C1E"),
                                ft.Text("Thông tin pháp lý, điều khoản báo giá & quản lý tài khoản", size=12, color="#72777F"),
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
                radius=16,
                side=ft.BorderSide(width=1, color="#E0E2EC"),
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
                                    bgcolor="#004A98",
                                    border_radius=2,
                                ),
                                ft.Text(
                                    title,
                                    size=15,
                                    weight=ft.FontWeight.BOLD,
                                    color="#191C1E",
                                ),
                            ],
                        ),
                        *controls,
                    ],
                ),
            ),
        )

    def _handle_save_profile(self, e):
        try:
            vat_val = float(self.default_vat.value.replace(",", "."))
            profit_val = float(self.default_profit.value.replace(",", "."))
            warranty_val = int(self.default_warranty.value.replace(",", "."))
        except ValueError:
            self.status_msg.value = "Vui lòng nhập số hợp lệ cho VAT, Lợi nhuận và Bảo hành!"
            self.status_msg.color = ft.Colors.RED_700
            self.status_msg.visible = True
            self._app_page.update()
            return

        data = {
            "company_name": self.company_name.value.strip(),
            "address": self.address.value.strip(),
            "phone": self.phone.value.strip(),
            "email": self.email.value.strip(),
            "website": self.website.value.strip(),
            "tax_code": self.tax_code.value.strip(),
            "bank_account": self.bank_account.value.strip(),
            "default_vat": vat_val,
            "default_profit": profit_val,
            "default_warranty_months": warranty_val,
            "notes": self.notes.value.strip(),
        }

        self.db.update_company_profile(data)
        self.status_msg.value = "Đã lưu thông tin hồ sơ doanh nghiệp thành công!"
        self.status_msg.color = ft.Colors.GREEN_700
        self.status_msg.visible = True

        self._app_page.snack_bar = ft.SnackBar(
            ft.Text("Đã cập nhật hồ sơ doanh nghiệp!"),
            bgcolor=ft.Colors.GREEN_700,
        )
        self._app_page.snack_bar.open = True

        if self.on_profile_updated:
            self.on_profile_updated(data)

        self._app_page.update()

    def _handle_reset_defaults(self, e):
        self.company_name.value = "CÔNG TY TNHH ĐIỆN TỬ TOÀN TRUNG"
        self.address.value = "31 Núi Thành, Phường 13, Quận Tân Bình, TP. Hồ Chí Minh"
        self.phone.value = "0903 848 111"
        self.email.value = "toantrung@toantrung.com"
        self.website.value = "www.toantrung.com"
        self.tax_code.value = "0304620008"
        self.bank_account.value = "19020491823019 - Techcombank CN Tân Bình"
        self.default_vat.value = "8.0"
        self.default_profit.value = "20.0"
        self.default_warranty.value = "24"
        self.notes.value = "Báo giá có hiệu lực trong vòng 15 ngày kể từ ngày lập."
        self._handle_save_profile(None)

    def _handle_backup_db(self, e):
        import shutil
        from datetime import datetime
        try:
            now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_bom_led_{now_str}.db"
            shutil.copyfile(self.db.db_path, backup_name)
            self._app_page.snack_bar = ft.SnackBar(
                ft.Text(f"Đã sao lưu dữ liệu vào {backup_name}!"),
                bgcolor=ft.Colors.GREEN_700,
            )
            self._app_page.snack_bar.open = True
            self._app_page.update()
        except Exception as exc:
            self.status_msg.value = f"Lỗi sao lưu: {exc}"
            self.status_msg.color = ft.Colors.RED_700
            self.status_msg.visible = True
            self._app_page.update()
