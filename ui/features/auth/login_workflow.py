"""Validate login fields on Flet's event loop; send real ERP IO to a worker."""
import asyncio
import flet as ft
from app.config import settings
from app.fastbusiness.service import AuthService


class LoginWorkflowMixin:
    def load_initial_entity_data(self):
        """Company/unit values come from the configured ERP installation."""
        return None

    def _on_company_changed(self, e):
        self.company_dropdown.error_text = None
        self._safe_update()

    def _on_unit_changed(self, e):
        self.unit_dropdown.error_text = None
        self._safe_update()

    def _on_username_change(self, e):
        self.username_input.error = None
        self._safe_update()

    def _on_username_blur(self, e):
        return None

    def _on_username_submit(self, e):
        try:
            self.password_input.focus()
        except Exception:
            pass

    def _handle_login(self, e):
        if self._is_submitting:
            return
        username = (self.username_input.value or "").strip()
        password = self.password_input.value or ""
        database = (self.company_dropdown.value or "").strip()
        unit = (self.unit_dropdown.value or "").strip()
        self.company_dropdown.error_text = None
        self.unit_dropdown.error_text = None
        self.username_input.error = None
        self.password_input.error = None
        if not database:
            self.company_dropdown.error_text = "Vui lòng chọn công ty"
        if not unit:
            self.unit_dropdown.error_text = "Vui lòng chọn đơn vị"
        if not username:
            self.username_input.error = "Vui lòng nhập tài khoản"
        if not password:
            self.password_input.error = "Vui lòng nhập mật khẩu"
        if not (database and unit and username and password):
            self._show_status("Vui lòng kiểm tra các trường bắt buộc", is_error=True)
            self._safe_update()
            return
        if not settings.FASTBUSINESS_BASE_URL:
            self._show_status("Chưa thiết lập FASTBUSINESS_BASE_URL trong .env", is_error=True)
            self._safe_update()
            return

        self._is_submitting = True
        self._set_form_disabled(True)
        self.login_button_content.controls = [
            ft.ProgressRing(width=18, height=18, color=ft.Colors.WHITE),
            ft.Text("Đang xác thực với FastBusiness...", color=ft.Colors.WHITE, size=14),
        ]
        self._safe_update()
        try:
            # Flet 1.1.2 keeps callbacks responsive with run_task / asyncio.to_thread.
            self._app_page.run_task(self._authenticate_with_erp, username, password, database, unit)
        except Exception:
            self._is_submitting = False
            self._set_form_disabled(False)
            self.login_button_content.controls = [self.login_btn_text, self.login_btn_icon]
            self._show_status("Không thể khởi chạy tác vụ đăng nhập", is_error=True)
            self._safe_update()

    async def _authenticate_with_erp(self, username: str, password: str, database: str, unit: str):
        success = False
        try:
            service = self.auth_service or AuthService()
            result = await asyncio.to_thread(service.login, username, password, database, unit)
            if not result.success:
                self._show_status(result.message, is_error=True)
                return
            if result.screen_types_warning:
                self._show_status(
                    "Đăng nhập thành công; không tải được loại màn hình: " + result.screen_types_warning,
                    is_error=True,
                )
            else:
                self._show_status(result.message)
            self.login_button_content.controls = [
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.WHITE),
                ft.Text("Đăng nhập thành công", color=ft.Colors.WHITE),
            ]
            self._safe_update()
            success = True
            if self.on_login_success:
                self.on_login_success(username)
        except Exception:
            self._show_status("Lỗi kết nối FastBusiness; kiểm tra cấu hình, máy chủ hoặc nhật ký", is_error=True)
        finally:
            self._is_submitting = False
            self._set_form_disabled(False)
            if not success:
                self.login_button_content.controls = [self.login_btn_text, self.login_btn_icon]
            self._safe_update()
