"""Profile interaction handlers (SQLite operations preserved)."""
from typing import Any, Callable, Dict
import flet as ft

from database.db_manager import DBManager
from ui.components.input_panel import InputPanel


from ui.theme.tokens import UIColors

class ProfileActionsMixin:
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
