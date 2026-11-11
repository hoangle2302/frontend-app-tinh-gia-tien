"""LoginPresentationMixin: isolated UI responsibilities; inherited by the screen coordinator.

Preserves original control construction and callbacks for migration safety.
"""
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import flet as ft
from app.config import settings
DEFAULT_LOGIN_DATABASE = settings.FASTBUSINESS_DATABASE
DEFAULT_LOGIN_UNIT = settings.FASTBUSINESS_UNIT


class LoginPresentationMixin:
    def reset(self):
        """Khôi phục lại giao diện ban đầu khi người dùng đăng xuất."""
        if self._unit_lookup_timer:
            self._unit_lookup_timer.cancel()
            self._unit_lookup_timer = None

        self._is_submitting = False
        self._user_exists = None
        self._last_checked_user = ""

        self._set_form_disabled(False)
        self.company_dropdown.error_text = None
        self.company_dropdown.value = DEFAULT_LOGIN_DATABASE

        self.username_input.value = ""
        self.username_input.error = None

        self.unit_dropdown.error_text = None
        self.unit_dropdown.options = [
            ft.dropdown.Option(key=DEFAULT_LOGIN_UNIT, text=DEFAULT_LOGIN_UNIT),
        ]
        self.unit_dropdown.value = DEFAULT_LOGIN_UNIT

        self.password_input.value = ""
        self.password_input.error = None

        self.status_banner.visible = False
        self.status_banner.opacity = 0.0
        self.status_banner.offset = ft.Offset(0, -0.1)

        self.login_button_content.controls = [self.login_btn_text, self.login_btn_icon]
        self.login_button.gradient = ft.LinearGradient(
            begin=ft.Alignment.CENTER_LEFT,
            end=ft.Alignment.CENTER_RIGHT,
            colors=[self.BRAND_PRIMARY, self.BRAND_SECONDARY],
        )
        self.login_button.scale = 1.0

        self.form_card.opacity = 1.0
        self.form_card.scale = 1.0
        self.form_card.offset = ft.Offset(0, 0)
        self._safe_update()
        self.load_initial_entity_data()

    def _safe_update(self, *controls):
        try:
            loop = getattr(self._app_page, "loop", None)
            import asyncio
            if isinstance(loop, asyncio.AbstractEventLoop) and loop.is_running():
                if controls:
                    loop.call_soon_threadsafe(self._app_page.update, *controls)
                else:
                    loop.call_soon_threadsafe(self._app_page.update)
            else:
                if controls:
                    self._app_page.update(*controls)
                else:
                    self._app_page.update()
        except Exception:
            pass

    def apply_theme(self, is_dark: bool):
        mode_key = "dark" if is_dark else "light"
        palette = self.THEME_PALETTE[mode_key]

        self.main_content.image = ft.DecorationImage(
            src=self.BG_IMAGE_DARK if is_dark else self.BG_IMAGE_LIGHT,
            fit=ft.BoxFit.COVER,
            alignment=ft.Alignment.BOTTOM_CENTER,
        )

        self.header.bgcolor = palette["header_bg"]
        self.header_divider.color = palette["divider"]
        self.logo_img.src = self.LOGO_DARK if is_dark else self.LOGO_LIGHT

        self.theme_button.icon = (
            ft.Icons.LIGHT_MODE
            if is_dark
            else ft.Icons.DARK_MODE
        )
        self.theme_button.icon_color = palette["theme_btn_icon"]
        self.theme_button.bgcolor = palette["theme_btn_bg"]
        self.theme_button.tooltip = (
            "Chuyển sang Light Mode" if is_dark else "Chuyển sang Dark Mode"
        )

        self.form_card.bgcolor = palette["card_bg"]
        self.form_card.border = ft.Border.all(1, palette["card_border"])
        self.title_text.color = palette["text_primary"]

        for field in (self.username_input, self.password_input):
            field.bgcolor = palette["input_bg"]
            field.color = palette["text_primary"]
            field.border = self._make_input_border(palette["input_border"])
            field.label_style = ft.TextStyle(color=palette["text_secondary"], size=13)
            field.hint_style = ft.TextStyle(color=palette["text_secondary"], size=13)

        for dd in (self.company_dropdown, self.unit_dropdown):
            dd.bgcolor = palette["input_bg"]
            dd.fill_color = palette["input_bg"]
            dd.border = self._make_input_border(palette["input_border"])
            dd.color = palette["text_primary"]
            dd.label_style = ft.TextStyle(color=palette["text_secondary"], size=13)
            dd.menu_style = ft.MenuStyle(
                bgcolor=palette["header_bg"],
                elevation=6,
                shape=ft.RoundedRectangleBorder(radius=12),
            )

        self.footer_text.color = palette["text_secondary"]

        if self.status_banner.visible:
            is_err = self.status_icon.name == ft.Icons.ERROR_OUTLINE_ROUNDED
            self._show_status(self.status_text.value, is_error=is_err)

    def on_resize(self, e=None):
        """Đồng bộ kích thước form_card và tất cả các ô nhập liệu theo chiều rộng cửa sổ hiển thị."""
        if self._app_page and hasattr(self._app_page, "width") and isinstance(self._app_page.width, (int, float)):
            target_w = min(380, max(280, self._app_page.width - 40))
            inner_w = target_w - 40
            self.form_card.width = target_w
            self.company_dropdown.width = inner_w
            self.username_input.width = inner_w
            self.unit_dropdown.width = inner_w
            self.password_input.width = inner_w
            self.login_button.width = inner_w
            self.status_banner.width = inner_w
            self._safe_update(
                self.form_card,
                self.company_dropdown,
                self.username_input,
                self.unit_dropdown,
                self.password_input,
                self.login_button,
                self.status_banner,
            )
