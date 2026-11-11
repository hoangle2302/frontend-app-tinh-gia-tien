"""Login UI coordinator. Network logic is preserved in login_workflow.py."""
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import flet as ft
from app.config import settings
DEFAULT_LOGIN_DATABASE = settings.FASTBUSINESS_DATABASE
DEFAULT_LOGIN_UNIT = settings.FASTBUSINESS_UNIT

from ui.features.auth.login_workflow import LoginWorkflowMixin
from ui.features.auth.login_fields import LoginFieldsMixin
from ui.features.auth.login_presentation import LoginPresentationMixin

from ui.theme.tokens import UIColors

class AuthLoginView(LoginWorkflowMixin, LoginFieldsMixin, LoginPresentationMixin, ft.Container):
    LOGO_LIGHT = "logo_light.png"

    LOGO_DARK = "logo_dark.png"

    BG_IMAGE_LIGHT = "bg_light.png"

    BG_IMAGE_DARK = "bg_dark.png"

    LOGO_WIDTH = 175

    LOGO_HEIGHT = 42

    BRAND_PRIMARY = "#004A98"

    BRAND_SECONDARY = UIColors.SECONDARY

    THEME_PALETTE = {
        "light": {
            "page_bg": "#FAFCFE",
            "header_bg": "#FFFFFF",
            "card_bg": "#EBFFFFFF",
            "card_border": UIColors.BORDER,
            "input_bg": "#F1F5F9",
            "input_border": UIColors.BORDER_STRONG,
            "text_primary": UIColors.TEXT_PRIMARY,
            "text_secondary": UIColors.TEXT_SECONDARY,
            "divider": UIColors.SECONDARY,
            "theme_btn_bg": "#F1F5F9",
            "theme_btn_icon": "#334155",
        },
        "dark": {
            "page_bg": UIColors.DARK_PAGE_BACKGROUND,
            "header_bg": "#111827",
            "card_bg": "#D9111827",
            "card_border": "#1E293B",
            "input_bg": "#1E293B",
            "input_border": "#334155",
            "text_primary": UIColors.SURFACE_SUBTLE,
            "text_secondary": UIColors.TEXT_SUBTLE,
            "divider": UIColors.SECONDARY,
            "theme_btn_bg": "#1E293B",
            "theme_btn_icon": "#FFFFFF",
        },
    }

    def __init__(self, page: ft.Page, on_login_success: Callable, on_toggle_theme: Callable, auth_service=None):
        super().__init__()
        self._app_page = page
        self.on_login_success = on_login_success
        self.on_toggle_theme = on_toggle_theme
        self.expand = True
        self._is_submitting = False

        # Trạng thái kiểm tra tài khoản & đơn vị từ FastBusiness ERP
        self._user_exists: Optional[bool] = None
        self._last_checked_user: str = ""
        self._unit_lookup_timer: Optional[threading.Timer] = None
        self.auth_service = auth_service

        is_dark = self._app_page.theme_mode == ft.ThemeMode.DARK
        palette = self.THEME_PALETTE["dark" if is_dark else "light"]

        # Header
        self.logo_img = ft.Image(
            src=self.LOGO_DARK if is_dark else self.LOGO_LIGHT,
            width=self.LOGO_WIDTH,
            height=self.LOGO_HEIGHT,
            fit=ft.BoxFit.CONTAIN,
        )

        self.theme_button = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE if is_dark else ft.Icons.DARK_MODE,
            icon_color=palette["theme_btn_icon"],
            bgcolor=palette["theme_btn_bg"],
            icon_size=20,
            visible=False,
            tooltip="Chuyển sang Light Mode" if is_dark else "Chuyển sang Dark Mode",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            on_click=self.on_toggle_theme,
        )

        self.header = ft.Container(
            content=ft.Row(
                controls=[
                    self.logo_img,
                    self.theme_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=palette["header_bg"],
            padding=ft.Padding(left=20, top=14, right=20, bottom=14),
        )

        self.header_divider = ft.Divider(
            height=1,
            thickness=1,
            color=palette["divider"],
        )

        # Login Form Title
        self.title_text = ft.Text(
            "Đăng nhập hệ thống",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=palette["text_primary"],
            text_align=ft.TextAlign.CENTER,
        )

        # 1. Công ty: giá trị mặc định lấy từ cấu hình (.env)
        self.company_dropdown = self._create_dropdown_field(
            label="Công ty",
            icon=ft.Icons.BUSINESS_ROUNDED,
            options=[
                ft.dropdown.Option(key=DEFAULT_LOGIN_DATABASE, text=DEFAULT_LOGIN_DATABASE),
            ],
            value=DEFAULT_LOGIN_DATABASE,
            on_select=self._on_company_changed,
            palette=palette,
        )

        # 2. Tên đăng nhập: chỉ kiểm tra dữ liệu khi nhấn Đăng nhập
        self.username_input = self._create_input_field(
            label="Tên",
            icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
            autofocus=True,
            palette=palette,
        )
        self.username_input.on_change = self._on_username_change
        self.username_input.on_blur = self._on_username_blur
        self.username_input.on_submit = self._on_username_submit

        # 3. Đơn vị: chọn mặc định từ cấu hình (.env)
        self.unit_dropdown = self._create_dropdown_field(
            label="Đơn vị",
            icon=ft.Icons.ACCOUNT_TREE_OUTLINED,
            options=[
                ft.dropdown.Option(key=DEFAULT_LOGIN_UNIT, text=DEFAULT_LOGIN_UNIT),
            ],
            value=DEFAULT_LOGIN_UNIT,
            on_select=self._on_unit_changed,
            palette=palette,
        )

        # 4. Trường "Mật khẩu"
        self.password_input = self._create_input_field(
            label="Mật khẩu",
            icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
            is_password=True,
            palette=palette,
        )
        self.password_input.on_submit = self._handle_login

        # Status Banner với chuyển động mượt mà
        self.status_icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
            size=18,
            color=UIColors.SUCCESS,
        )
        self.status_text = ft.Text(
            value="",
            size=13,
            weight=ft.FontWeight.W_500,
            expand=True,
        )
        self.status_banner = ft.Container(
            content=ft.Row(
                controls=[self.status_icon, self.status_text],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=320,
            padding=ft.Padding(left=14, top=12, right=14, bottom=12),
            border_radius=10,
            opacity=0.0,
            offset=ft.Offset(0, -0.1),
            animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            visible=False,
        )

        # Login Button với các trạng thái chuyển động
        self.login_btn_text = ft.Text(
            "Đăng nhập",
            size=16,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.WHITE,
        )
        self.login_btn_icon = ft.Icon(
            ft.Icons.ARROW_FORWARD_ROUNDED,
            color=ft.Colors.WHITE,
            size=19,
        )
        self.login_button_content = ft.Row(
            controls=[self.login_btn_text, self.login_btn_icon],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )
        self.login_button = ft.Container(
            content=self.login_button_content,
            width=320,
            height=52,
            border_radius=12,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=[self.BRAND_PRIMARY, self.BRAND_SECONDARY],
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=14,
                color="#400088CC",
                offset=ft.Offset(0, 6),
            ),
            ink=True,
            scale=1.0,
            animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            animate=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            on_click=self._handle_login,
            on_hover=self._on_button_hover,
        )

        self.login_form = ft.Column(
            controls=[
                ft.Column(
                    controls=[self.title_text],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=8),
                self.company_dropdown,
                self.username_input,
                self.unit_dropdown,
                self.password_input,
                self.status_banner,
                ft.Container(height=4),
                self.login_button,
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            tight=True,
        )

        self.form_card = ft.Container(
            content=self.login_form,
            width=360,
            bgcolor=palette["card_bg"],
            border=ft.Border.all(1, palette["card_border"]),
            border_radius=20,
            padding=ft.Padding(left=20, top=24, right=20, bottom=24),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=24,
                color="#66000000",
                offset=ft.Offset(0, 8),
            ),
            opacity=1.0,
            scale=1.0,
            offset=ft.Offset(0, 0),
            animate_opacity=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(350, ft.AnimationCurve.EASE_OUT_CUBIC),
            animate_offset=ft.Animation(350, ft.AnimationCurve.EASE_OUT_CUBIC),
        )

        self.footer_text = ft.Text(
            "© 2026 TOÀN TRUNG. All rights reserved.",
            size=12,
            color=palette["text_secondary"],
            text_align=ft.TextAlign.CENTER,
        )

        self.footer = ft.Container(
            content=self.footer_text,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding(
                left=0,
                top=12,
                right=0,
                bottom=20,
            ),
        )

        self.main_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(expand=True),
                    self.form_card,
                    ft.Container(expand=True),
                    self.footer,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            image=ft.DecorationImage(
                src=self.BG_IMAGE_DARK if is_dark else self.BG_IMAGE_LIGHT,
                fit=ft.BoxFit.COVER,
                alignment=ft.Alignment.BOTTOM_CENTER,
            ),
            padding=ft.Padding(
                left=20,
                top=20,
                right=20,
                bottom=12,
            ),
            expand=True,
        )

        self.content = ft.Column(
            controls=[
                self.header,
                self.header_divider,
                self.main_content,
            ],
            spacing=0,
            expand=True,
        )

        # Giữ form độc lập: chỉ xác thực sau khi người dùng nhấn Đăng nhập.
        self.load_initial_entity_data()
