# src\app\features\auth\screens\login_screen.py

from collections.abc import Awaitable, Callable
import inspect

import flet as ft

from app.core.assets import AppAssets


APP_TITLE = "TOÀN TRUNG"
BRAND_PRIMARY = "#004A98"
BRAND_SECONDARY = "#00B8E8"
WINDOW_WIDTH = 393
WINDOW_HEIGHT = 852
LOGO_WIDTH = 175
LOGO_HEIGHT = 42

PALETTES = {
    "light": {
        "page_bg": "#FAFCFE",
        "header_bg": "#FFFFFF",
        "card_bg": "#EBFFFFFF",
        "card_border": "#E2E8F0",
        "input_bg": "#F1F5F9",
        "input_border": "#CBD5E1",
        "text_primary": "#0F172A",
        "text_secondary": "#64748B",
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
        "theme_btn_bg": "#1E293B",
        "theme_btn_icon": "#FFFFFF",
    },
}

# Hàm xác thực có thể được truyền từ layer controller khi tích hợp API.
# True = thành công; False = sai thông tin xác thực.
Authenticate = Callable[[str, str], bool | Awaitable[bool]]
OnLoginSuccess = Callable[[str], None | Awaitable[None]]


def input_border(color: str) -> dict:
    """Đường viền TextField theo Flet 1.x (không dùng API deprecated)."""
    return {
        ft.ControlState.DEFAULT: ft.OutlineInputBorder(
            border_radius=12, side=ft.BorderSide(color=color, width=1)
        ),
        ft.ControlState.FOCUSED: ft.OutlineInputBorder(
            border_radius=12, side=ft.BorderSide(color=BRAND_SECONDARY, width=2)
        ),
        ft.ControlState.ERROR: ft.OutlineInputBorder(
            border_radius=12, side=ft.BorderSide(color="#DC2626", width=1)
        ),
    }


def make_text_field(label: str, icon, *, password: bool = False) -> ft.TextField:
    p = PALETTES["light"]
    return ft.TextField(
        label=label,
        prefix_icon=icon,
        password=password,
        can_reveal_password=password,
        autofocus=False,
        filled=True,
        bgcolor=p["input_bg"],
        border=input_border(p["input_border"]),
        text_size=14,
        label_style=ft.TextStyle(color=p["text_secondary"], size=13),
        hint_style=ft.TextStyle(color=p["text_secondary"], size=13),
        content_padding=ft.Padding(left=16, top=16, right=16, bottom=16),
    )


async def show_login(
    page: ft.Page,
    *,
    authenticate: Authenticate | None = None,
    on_success: OnLoginSuccess | None = None,
) -> None:
    """Hiển thị trang đăng nhập.

    authenticate: callback xác thực tùy chọn, có thể đồng bộ hoặc async.
    Khi chưa truyền callback, màn hình chỉ kiểm tra dữ liệu đầu vào,
    không giả vờ đăng nhập thành công.
    """
    page.on_resize = None
    page.title = APP_TITLE
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=BRAND_PRIMARY)
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = PALETTES["light"]["page_bg"]

    # Chỉ thay đổi kích thước cửa sổ desktop, không ép Android dùng kích thước cố định.
    is_desktop = bool(
        page.platform is not None
        and page.platform.is_desktop()
        and not page.web
    )
    if is_desktop:
        page.window.width = WINDOW_WIDTH
        page.window.height = WINDOW_HEIGHT
        page.window.min_width = 360
        page.window.min_height = 640
        page.window.resizable = True

    p = PALETTES["light"]

    logo = ft.Image(
        src=AppAssets.Images.LOGO_LIGHT,
        width=LOGO_WIDTH,
        height=LOGO_HEIGHT,
        fit=ft.BoxFit.CONTAIN,
    )
    theme_button = ft.IconButton(
        icon=ft.Icons.DARK_MODE_OUTLINED,
        icon_color=p["theme_btn_icon"],
        bgcolor=p["theme_btn_bg"],
        icon_size=20,
        tooltip="Chuyển sang Dark Mode",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )
    header = ft.Container(
        content=ft.Row(
            controls=[logo, theme_button],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=p["header_bg"],
        padding=ft.Padding(left=20, top=14, right=20, bottom=14),
    )
    header_divider = ft.Divider(height=1, thickness=1, color=BRAND_SECONDARY)

    title = ft.Text(
        "Đăng nhập hệ thống",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=p["text_primary"],
        text_align=ft.TextAlign.CENTER,
    )
    username = make_text_field("Tên đăng nhập", ft.Icons.PERSON_OUTLINE_ROUNDED)
    password = make_text_field("Mật khẩu", ft.Icons.LOCK_OUTLINE_ROUNDED, password=True)

    status_icon = ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=18)
    status_text = ft.Text("", size=13, weight=ft.FontWeight.W_500, expand=True)
    status_banner = ft.Container(
        content=ft.Row(
            controls=[status_icon, status_text],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(left=14, top=12, right=14, bottom=12),
        border_radius=10,
        visible=False,
    )

    login_label = ft.Text(
        "Đăng nhập", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE
    )
    login_button = ft.Container(
        content=ft.Row(
            controls=[
                login_label,
                ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, color=ft.Colors.WHITE, size=19),
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
            colors=[BRAND_PRIMARY, BRAND_SECONDARY],
        ),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=14,
            color="#400088CC",
            offset=ft.Offset(0, 6),
        ),
        ink=True,
    )

    form_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(content=title, alignment=ft.Alignment.CENTER),
                ft.Container(height=12),
                username,
                password,
                status_banner,
                ft.Container(height=4),
                login_button,
            ],
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            tight=True,
        ),
        bgcolor=p["card_bg"],
        border=ft.Border.all(1, p["card_border"]),
        border_radius=20,
        padding=ft.Padding(left=20, top=28, right=20, bottom=28),
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=24, color="#66000000", offset=ft.Offset(0, 8)
        ),
    )
    footer_text = ft.Text(
        "© 2026 TOÀN TRUNG. All rights reserved.",
        size=12,
        color=p["text_secondary"],
        text_align=ft.TextAlign.CENTER,
    )
    footer = ft.Container(
        content=footer_text,
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding(left=0, top=12, right=0, bottom=20),
    )
    main_content = ft.Container(
        content=ft.Column(
            controls=[
                ft.Column(
                    controls=[form_card],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                footer,
            ],
            spacing=0,
            expand=True,
        ),
        image=ft.DecorationImage(
            src=AppAssets.Images.BG_LIGHT,
            fit=ft.BoxFit.COVER,
            alignment=ft.Alignment.BOTTOM_CENTER,
        ),
        padding=ft.Padding(left=20, top=36, right=20, bottom=16),
        expand=True,
    )

    def show_status(message: str, *, error: bool = False, info: bool = False) -> None:
        dark = page.theme_mode == ft.ThemeMode.DARK
        if error:
            status_icon.name = ft.Icons.ERROR_OUTLINE_ROUNDED
            color = "#FCA5A5" if dark else "#DC2626"
            background = "#3B1818" if dark else "#FEF2F2"
            outline = "#7F1D1D" if dark else "#FECACA"
        elif info:
            status_icon.name = ft.Icons.INFO_OUTLINE_ROUNDED
            color = "#7DD3FC" if dark else "#0369A1"
            background = "#122D43" if dark else "#E0F2FE"
            outline = "#075985" if dark else "#BAE6FD"
        else:
            status_icon.name = ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED
            color = "#4ADE80" if dark else "#16A34A"
            background = "#143321" if dark else "#F0FDF4"
            outline = "#166534" if dark else "#BBF7D0"

        status_icon.color = color
        status_text.color = color
        status_text.value = message
        status_banner.bgcolor = background
        status_banner.border = ft.Border.all(1, outline)
        status_banner.visible = True
        status_banner.data = (error, info)

    async def handle_login(e) -> None:
        user_value = (username.value or "").strip()
        password_value = password.value or ""
        username.error = None
        password.error = None
        status_banner.visible = False

        if not user_value:
            username.error = "Vui lòng nhập tên đăng nhập"
        if not password_value:
            password.error = "Vui lòng nhập mật khẩu"
        if username.error or password.error:
            show_status("Vui lòng kiểm tra lại thông tin đăng nhập.", error=True)
            page.update()
            return

        if authenticate is None:
            show_status("Dữ liệu hợp lệ. Chưa cấu hình máy chủ xác thực.", info=True)
            page.update()
            return

        navigated = False
        login_button.on_click = None
        login_label.value = "Đang xác thực..."
        page.update()
        try:
            response = authenticate(user_value, password_value)
            success = await response if inspect.isawaitable(response) else response
            if success is True:
                if on_success is not None:
                    result = on_success(user_value)
                    if inspect.isawaitable(result):
                        await result
                    navigated = True
                    return
                show_status("Đăng nhập thành công!")
            else:
                show_status("Tên đăng nhập hoặc mật khẩu không đúng.", error=True)
        except Exception:
            # Không hiển thị chi tiết exception/token cho người dùng.
            show_status("Không thể kết nối máy chủ. Vui lòng thử lại.", error=True)
        finally:
            if not navigated:
                login_label.value = "Đăng nhập"
                login_button.on_click = handle_login
                page.update()

    async def focus_password(e) -> None:
        await password.focus()

    def change_theme(e) -> None:
        dark = page.theme_mode != ft.ThemeMode.DARK
        page.theme_mode = ft.ThemeMode.DARK if dark else ft.ThemeMode.LIGHT
        palette = PALETTES["dark" if dark else "light"]
        page.bgcolor = palette["page_bg"]

        # Tất cả đường dẫn assets dùng cùng một nguồn AppAssets.
        logo.src = AppAssets.Images.LOGO_DARK if dark else AppAssets.Images.LOGO_LIGHT
        main_content.image = ft.DecorationImage(
            src=AppAssets.Images.BG_DARK if dark else AppAssets.Images.BG_LIGHT,
            fit=ft.BoxFit.COVER,
            alignment=ft.Alignment.BOTTOM_CENTER,
        )

        header.bgcolor = palette["header_bg"]
        theme_button.icon = ft.Icons.LIGHT_MODE if dark else ft.Icons.DARK_MODE
        theme_button.icon_color = palette["theme_btn_icon"]
        theme_button.bgcolor = palette["theme_btn_bg"]
        theme_button.tooltip = "Chuyển sang Light Mode" if dark else "Chuyển sang Dark Mode"
        form_card.bgcolor = palette["card_bg"]
        form_card.border = ft.Border.all(1, palette["card_border"])
        title.color = palette["text_primary"]
        footer_text.color = palette["text_secondary"]
        for field in (username, password):
            field.bgcolor = palette["input_bg"]
            field.border = input_border(palette["input_border"])
            field.label_style = ft.TextStyle(color=palette["text_secondary"], size=13)
            field.hint_style = ft.TextStyle(color=palette["text_secondary"], size=13)
        if status_banner.visible:
            error, info = status_banner.data or (False, False)
            show_status(status_text.value, error=error, info=info)
        page.update()

    username.on_submit = focus_password
    password.on_submit = handle_login
    login_button.on_click = handle_login
    theme_button.on_click = change_theme

    layout = ft.SafeArea(
        expand=True,
        content=ft.Column(
            controls=[header, header_divider, main_content],
            spacing=0,
            expand=True,
        ),
    )
    page.add(layout)
    if is_desktop:
        await page.window.center()
