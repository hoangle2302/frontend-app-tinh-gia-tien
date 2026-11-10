from typing import Callable
import flet as ft


class AuthLoginView(ft.Container):
    LOGO_LIGHT = "logo_light.png"
    LOGO_DARK = "logo_dark.png"
    BG_IMAGE_LIGHT = "bg_light.png"
    BG_IMAGE_DARK = "bg_dark.png"

    LOGO_WIDTH = 175
    LOGO_HEIGHT = 42

    BRAND_PRIMARY = "#004A98"
    BRAND_SECONDARY = "#00B8E8"

    THEME_PALETTE = {
        "light": {
            "page_bg": "#FAFCFE",
            "header_bg": "#FFFFFF",
            "card_bg": "#EBFFFFFF",
            "card_border": "#E2E8F0",
            "input_bg": "#F1F5F9",
            "input_border": "#CBD5E1",
            "text_primary": "#0F172A",
            "text_secondary": "#64748B",
            "divider": "#00B8E8",
            "theme_btn_bg": "#F1F5F9",
            "theme_btn_icon": "#334155",
        },
        "dark": {
            "page_bg": "#091322",
            "header_bg": "#111827",
            "card_bg": "#D9111827",
            "card_border": "#1E293B",
            "input_bg": "#1E293B",
            "input_border": "#334155",
            "text_primary": "#F8FAFC",
            "text_secondary": "#94A3B8",
            "divider": "#00B8E8",
            "theme_btn_bg": "#1E293B",
            "theme_btn_icon": "#FFFFFF",
        },
    }

    def __init__(self, page: ft.Page, on_login_success: Callable, on_toggle_theme: Callable):
        super().__init__()
        self._app_page = page
        self.on_login_success = on_login_success
        self.on_toggle_theme = on_toggle_theme
        self.expand = True

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
            tooltip="Chuyển sang Light Mode" if is_dark else "Chuyển sang Dark Mode",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
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

        # Login Form
        self.title_text = ft.Text(
            "Đăng nhập hệ thống",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=palette["text_primary"],
            text_align=ft.TextAlign.CENTER,
        )

        self.username_input = self._create_input_field(
            label="Tên đăng nhập",
            icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
            autofocus=True,
            palette=palette,
        )

        self.password_input = self._create_input_field(
            label="Mật khẩu",
            icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
            is_password=True,
            palette=palette,
        )

        self.status_icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
            size=18,
            color="#16A34A",
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
            padding=ft.Padding(left=14, top=12, right=14, bottom=12),
            border_radius=10,
            visible=False,
        )

        self.login_button = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Đăng nhập",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Icon(
                        ft.Icons.ARROW_FORWARD_ROUNDED,
                        color=ft.Colors.WHITE,
                        size=19,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
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
            on_click=self._handle_login,
        )

        self.username_input.on_submit = lambda e: self.password_input.focus()
        self.password_input.on_submit = self._handle_login

        self.login_form = ft.Column(
            controls=[
                ft.Column(
                    controls=[self.title_text],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=12),
                self.username_input,
                self.password_input,
                self.status_banner,
                ft.Container(height=4),
                self.login_button,
            ],
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            tight=True,
        )

        self.form_card = ft.Container(
            content=self.login_form,
            bgcolor=palette["card_bg"],
            border=ft.Border.all(1, palette["card_border"]),
            border_radius=20,
            padding=ft.Padding(left=20, top=28, right=20, bottom=28),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=24,
                color="#66000000",
                offset=ft.Offset(0, 8),
            ),
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
                side=ft.BorderSide(color="#DC2626", width=1),
            ),
        }

    def _create_input_field(
        self,
        label: str,
        icon,
        is_password: bool = False,
        autofocus: bool = False,
        palette: dict = None,
    ) -> ft.TextField:
        palette = palette or self.THEME_PALETTE["light"]
        return ft.TextField(
            label=label,
            prefix_icon=icon,
            password=is_password,
            can_reveal_password=is_password,
            autofocus=autofocus,
            filled=True,
            bgcolor=palette["input_bg"],
            border=self._make_input_border(palette["input_border"]),
            text_size=14,
            label_style=ft.TextStyle(
                color=palette["text_secondary"],
                size=13,
            ),
            hint_style=ft.TextStyle(
                color=palette["text_secondary"],
                size=13,
            ),
            content_padding=ft.Padding(
                left=16, top=16, right=16, bottom=16
            ),
        )

    def _show_status(self, message: str, is_error: bool = False):
        is_dark = self._app_page.theme_mode == ft.ThemeMode.DARK
        if is_error:
            self.status_icon.name = ft.Icons.ERROR_OUTLINE_ROUNDED
            self.status_icon.color = "#DC2626"
            self.status_text.color = "#DC2626"
            self.status_banner.bgcolor = "#3B1818" if is_dark else "#FEF2F2"
            self.status_banner.border = ft.Border.all(1, "#7F1D1D" if is_dark else "#FECACA")
        else:
            self.status_icon.name = ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED
            self.status_icon.color = "#16A34A"
            self.status_text.color = "#16A34A"
            self.status_banner.bgcolor = "#143321" if is_dark else "#F0FDF4"
            self.status_banner.border = ft.Border.all(1, "#166534" if is_dark else "#BBF7D0")

        self.status_text.value = message
        self.status_banner.visible = True

    def _handle_login(self, e):
        username = (self.username_input.value or "").strip()
        password = self.password_input.value or ""

        self.username_input.error = None
        self.password_input.error = None
        self.status_banner.visible = False

        has_error = False

        if not username:
            self.username_input.error = "Vui lòng nhập tên đăng nhập"
            has_error = True

        if not password:
            self.password_input.error = "Vui lòng nhập mật khẩu"
            has_error = True

        if has_error:
            self._show_status("Vui lòng kiểm tra lại thông tin đăng nhập.", is_error=True)
            self._app_page.update()
            return

        self._show_status("Xác thực hợp lệ! Đang chuyển tiếp...", is_error=False)
        self._app_page.update()
        self.on_login_success(username)

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
            field.border = self._make_input_border(palette["input_border"])
            field.label_style = ft.TextStyle(color=palette["text_secondary"], size=13)
            field.hint_style = ft.TextStyle(color=palette["text_secondary"], size=13)

        self.footer_text.color = palette["text_secondary"]

        if self.status_banner.visible:
            is_err = self.status_icon.name == ft.Icons.ERROR_OUTLINE_ROUNDED
            self._show_status(self.status_text.value, is_error=is_err)

