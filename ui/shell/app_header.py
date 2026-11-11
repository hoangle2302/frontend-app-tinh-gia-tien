"""Reusable app header (logo, profile, quote history and theme actions)."""
from typing import Callable
import flet as ft
from ui.theme.tokens import UIColors


class AppHeader:
    def __init__(
        self,
        *,
        on_toggle_theme: Callable,
        on_history: Callable,
        on_profile: Callable,
    ):
        self.logo = ft.Container(
            width=175,
            height=42,
            alignment=ft.Alignment(-1, 0),
            content=ft.Image(src="logo_light.png", width=170, height=40, fit=ft.BoxFit.CONTAIN),
        )
        self.theme_button = ft.IconButton(
            icon=ft.Icons.DARK_MODE_OUTLINED,
            tooltip="Đổi giao diện sáng/tối",
            icon_color=UIColors.PRIMARY,
            width=38,
            height=38,
            on_click=on_toggle_theme,
            style=ft.ButtonStyle(bgcolor=UIColors.PRIMARY_SOFT, shape=ft.CircleBorder(), padding=0),
            animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )
        self.history_button = ft.IconButton(
            icon=ft.Icons.HISTORY,
            tooltip="Lịch sử báo giá",
            icon_color=UIColors.PRIMARY,
            width=38,
            height=38,
            on_click=on_history,
            style=ft.ButtonStyle(bgcolor=UIColors.PRIMARY_SOFT, shape=ft.CircleBorder(), padding=0),
            animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
        )
        self.profile_button = ft.IconButton(
            icon=ft.Icons.PERSON,
            tooltip="Hồ sơ",
            icon_color=UIColors.PRIMARY,
            width=38,
            height=38,
            on_click=on_profile,
            style=ft.ButtonStyle(bgcolor=UIColors.PRIMARY_SOFT, shape=ft.CircleBorder(), padding=0),
            animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
        )
        self.actions = ft.Row(
            controls=[self.theme_button, self.history_button, self.profile_button],
            spacing=8,
        )
        self.appbar = ft.AppBar(
            leading=self.logo,
            leading_width=185,
            toolbar_height=58,
            bgcolor=ft.Colors.WHITE,
            elevation=0,
            actions=[self.actions],
        )

    def on_resize(self, compact: bool) -> None:
        self.logo.width = 150 if compact else 175
        self.logo.content.width = 145 if compact else 170
        self.appbar.leading_width = 155 if compact else 185
