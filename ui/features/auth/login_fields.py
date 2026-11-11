"""LoginFieldsMixin: isolated UI responsibilities; inherited by the screen coordinator.

Preserves original control construction and callbacks for migration safety.
"""
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import flet as ft
from app.config import settings
DEFAULT_LOGIN_DATABASE = settings.FASTBUSINESS_DATABASE
DEFAULT_LOGIN_UNIT = settings.FASTBUSINESS_UNIT


from ui.theme.tokens import UIColors

class LoginFieldsMixin:
    def _on_button_hover(self, e):
        if not self._is_submitting:
            self.login_button.scale = 1.02 if e.data == "true" else 1.0
            self._safe_update()

    def _make_input_border(self, color: str):
        return {
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(color=color, width=1),
            ),
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(color=self.BRAND_SECONDARY, width=2),
            ),
            ft.ControlState.ERROR: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(color=UIColors.ERROR, width=1.5),
            ),
        }

    def _create_dropdown_field(
        self,
        label: str,
        icon,
        options: list,
        value: Optional[str],
        on_select: Callable,
        palette: dict = None,
        width: Optional[int] = 320,
    ) -> ft.Dropdown:
        palette = palette or self.THEME_PALETTE["light"]
        return ft.Dropdown(
            width=width,
            label=label,
            leading_icon=icon,
            options=options,
            value=value,
            on_select=on_select,
            expanded_insets=ft.Padding(0, 0, 0, 0),
            filled=True,
            fill_color=palette["input_bg"],
            bgcolor=palette["input_bg"],
            border=self._make_input_border(palette["input_border"]),
            text_size=14,
            color=palette["text_primary"],
            label_style=ft.TextStyle(
                color=palette["text_secondary"],
                size=13,
            ),
            content_padding=ft.Padding(
                left=16, top=14, right=16, bottom=14
            ),
            menu_style=ft.MenuStyle(
                bgcolor=palette["header_bg"],
                elevation=6,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        )

    def _create_input_field(
        self,
        label: str,
        icon,
        is_password: bool = False,
        autofocus: bool = False,
        palette: dict = None,
        width: Optional[int] = 320,
    ) -> ft.TextField:
        palette = palette or self.THEME_PALETTE["light"]
        return ft.TextField(
            width=width,
            label=label,
            prefix_icon=icon,
            password=is_password,
            can_reveal_password=is_password,
            autofocus=autofocus,
            filled=True,
            fill_color=palette["input_bg"],
            bgcolor=palette["input_bg"],
            border=self._make_input_border(palette["input_border"]),
            text_size=14,
            color=palette["text_primary"],
            label_style=ft.TextStyle(
                color=palette["text_secondary"],
                size=13,
            ),
            hint_style=ft.TextStyle(
                color=palette["text_secondary"],
                size=13,
            ),
            content_padding=ft.Padding(
                left=16, top=14, right=16, bottom=14
            ),
        )

    def _show_status(self, message: str, is_error: bool = False):
        is_dark = self._app_page.theme_mode == ft.ThemeMode.DARK
        if is_error:
            self.status_icon.name = ft.Icons.ERROR_OUTLINE_ROUNDED
            self.status_icon.color = UIColors.ERROR
            self.status_text.color = UIColors.ERROR
            self.status_banner.bgcolor = "#3B1818" if is_dark else "#FEF2F2"
            self.status_banner.border = ft.Border.all(1, "#7F1D1D" if is_dark else "#FECACA")
        else:
            self.status_icon.name = ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED
            self.status_icon.color = UIColors.SUCCESS
            self.status_text.color = UIColors.SUCCESS
            self.status_banner.bgcolor = "#143321" if is_dark else "#F0FDF4"
            self.status_banner.border = ft.Border.all(1, "#166534" if is_dark else "#BBF7D0")

        self.status_text.value = message
        self.status_banner.visible = True
        self.status_banner.opacity = 1.0
        self.status_banner.offset = ft.Offset(0, 0)
        self._safe_update()

    def _hide_status(self):
        self.status_banner.opacity = 0.0
        self.status_banner.offset = ft.Offset(0, -0.1)
        self._safe_update()

    def _set_form_disabled(self, disabled: bool):
        self.company_dropdown.disabled = disabled
        self.username_input.disabled = disabled
        self.unit_dropdown.disabled = disabled
        self.password_input.disabled = disabled
