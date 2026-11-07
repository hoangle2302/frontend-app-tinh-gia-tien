import flet as ft


# ==========================================
# APPLICATION CONFIGURATION & COLOR PALETTE
# ==========================================

APP_TITLE = "TOÀN TRUNG"

# Kích thước chuẩn iPhone 15 / 16 Pro
WINDOW_WIDTH = 393
WINDOW_HEIGHT = 852

LOGO_LIGHT = "logo_light.png"
LOGO_DARK = "logo_dark.png"
BG_IMAGE_LIGHT = "bg_light.png"
BG_IMAGE_DARK = "bg_dark.png"

LOGO_WIDTH = 175
LOGO_HEIGHT = 42

# Bảng màu thương hiệu (Brand Colors)
BRAND_PRIMARY = "#004A98"      # Xanh đậm thương hiệu
BRAND_SECONDARY = "#00B8E8"    # Xanh Cyan điểm nhấn

# Bảng màu theo giao diện Sáng / Tối
THEME_PALETTE = {
    "light": {
        "page_bg": "#FAFCFE",          # Nền sáng đồng bộ với bg_light.png
        "header_bg": "#FFFFFF",        # Nền header trắng tinh
        "card_bg": "#EBFFFFFF",        # Nền khung form trắng (hơi trong suốt nhẹ 92%)
        "card_border": "#E2E8F0",      # Viền khung form sáng
        "input_bg": "#F1F5F9",         # Nền ô nhập liệu
        "input_border": "#CBD5E1",     # Viền ô nhập liệu mặc định
        "text_primary": "#0F172A",     # Chữ chính (Đen xanh đậm)
        "text_secondary": "#64748B",   # Chữ phụ / Mô tả
        "divider": "#00B8E8",          # Đường kẻ phân cách xanh thương hiệu
        "theme_btn_bg": "#F1F5F9",     # Nền nút đổi theme
        "theme_btn_icon": "#334155",   # Màu icon đổi theme
    },
    "dark": {
        "page_bg": "#091322",          # Nền tối đồng bộ với bg_dark.png
        "header_bg": "#111827",        # Nền header tối
        "card_bg": "#D9111827",        # Nền khung form tối (trong suốt nhẹ 85%)
        "card_border": "#1E293B",      # Viền khung form tối
        "input_bg": "#1E293B",         # Nền ô nhập liệu tối
        "input_border": "#334155",     # Viền ô nhập liệu tối
        "text_primary": "#F8FAFC",     # Chữ chính (Trắng sáng)
        "text_secondary": "#94A3B8",   # Chữ phụ
        "divider": "#00B8E8",          # Đường kẻ phân cách
        "theme_btn_bg": "#1E293B",     # Nền nút đổi theme
        "theme_btn_icon": "#FFFFFF",   # Icon màu trắng theo yêu cầu
    },
}


async def main(page: ft.Page):

    # ======================================
    # WINDOW & PAGE SETTINGS
    # ======================================

    page.title = APP_TITLE
    # Chỉ cấu hình kích thước cửa sổ trên desktop.
    # Android sẽ sử dụng kích thước màn hình thiết bị thực tế.
    is_desktop = (
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

    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0  # Để Header, Divider và Background tràn viền đẹp mắt
    page.bgcolor = THEME_PALETTE["light"]["page_bg"]

    # Cấu hình Font & Theme mặc định
    page.theme = ft.Theme(color_scheme_seed=BRAND_PRIMARY)

    # ======================================
    # HEADER COMPONENT
    # ======================================

    logo_img = ft.Image(
        src=LOGO_LIGHT,
        width=LOGO_WIDTH,
        height=LOGO_HEIGHT,
        fit=ft.BoxFit.CONTAIN,
    )

    theme_button = ft.IconButton(
        icon=ft.Icons.DARK_MODE_OUTLINED,
        icon_color=THEME_PALETTE["light"]["theme_btn_icon"],
        bgcolor=THEME_PALETTE["light"]["theme_btn_bg"],
        icon_size=20,
        tooltip="Chuyển sang Dark Mode",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
    )

    header = ft.Container(
        content=ft.Row(
            controls=[
                logo_img,
                theme_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=THEME_PALETTE["light"]["header_bg"],
        padding=ft.Padding(left=20, top=14, right=20, bottom=14),
    )

    header_divider = ft.Divider(
        height=1,
        thickness=1,
        color=THEME_PALETTE["light"]["divider"],
    )

    # ======================================
    # LOGIN FORM COMPONENTS
    # ======================================

    title_text = ft.Text(
        "Đăng nhập hệ thống",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=THEME_PALETTE["light"]["text_primary"],
        text_align=ft.TextAlign.CENTER,
    )

    # Viền TextField theo API Flet 1.x (không dùng thuộc tính deprecated).
    def make_input_border(color: str):
        return {
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(color=color, width=1),
            ),
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(color=BRAND_SECONDARY, width=2),
            ),
            ft.ControlState.ERROR: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(color="#DC2626", width=1),
            ),
        }

    # Style chung cho TextField
    def create_input_field(
        label: str,
        icon,
        is_password: bool = False,
        autofocus: bool = False,
    ) -> ft.TextField:
        return ft.TextField(
            label=label,
            prefix_icon=icon,
            password=is_password,
            can_reveal_password=is_password,
            autofocus=autofocus,
            filled=True,
            bgcolor=THEME_PALETTE["light"]["input_bg"],
            border=make_input_border(THEME_PALETTE["light"]["input_border"]),
            text_size=14,
            label_style=ft.TextStyle(
                color=THEME_PALETTE["light"]["text_secondary"],
                size=13,
            ),
            hint_style=ft.TextStyle(
                color=THEME_PALETTE["light"]["text_secondary"],
                size=13,
            ),
            content_padding=ft.Padding(
                left=16, top=16, right=16, bottom=16
            ),
        )

    username_input = create_input_field(
        label="Tên đăng nhập",
        icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
        autofocus=True,
    )

    password_input = create_input_field(
        label="Mật khẩu",
        icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
        is_password=True,
    )

    # Banner thông báo trạng thái
    status_icon = ft.Icon(
        ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
        size=18,
        color="#16A34A",
    )
    status_text = ft.Text(
        value="",
        size=13,
        weight=ft.FontWeight.W_500,
        expand=True,
    )
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

    # ======================================
    # LOGIN BUTTON
    # ======================================

    login_button = ft.Container(
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

    # ======================================
    # MAIN CONTENT & BACKGROUND IMAGE
    # ======================================

    login_form = ft.Column(
        controls=[
            ft.Column(
                controls=[title_text],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(height=12),
            username_input,
            password_input,
            status_banner,
            ft.Container(height=4),
            login_button,
        ],
        spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        tight=True,
    )

    # Khung Card bao bọc Form giúp nổi bật trên nền ảnh tối bg.jpg
    form_card = ft.Container(
        content=login_form,
        bgcolor=THEME_PALETTE["light"]["card_bg"],
        border=ft.Border.all(1, THEME_PALETTE["light"]["card_border"]),
        border_radius=20,
        padding=ft.Padding(left=20, top=28, right=20, bottom=28),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=24,
            color="#66000000",
            offset=ft.Offset(0, 8),
        ),
    )

    footer_text = ft.Text(
        "© 2026 TOÀN TRUNG. All rights reserved.",
        size=12,
        color=THEME_PALETTE["light"]["text_secondary"],
        text_align=ft.TextAlign.CENTER,
    )

    footer = ft.Container(
        content=footer_text,
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding(
            left=0,
            top=12,
            right=0,
            bottom=20,
        ),
    )

    # Container chính chứa ảnh nền theo chế độ Light/Dark
    main_content = ft.Container(
        content=ft.Column(
            controls=[
                # Login Form - Có thể cuộn
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

        # Background
        image=ft.DecorationImage(
            src=BG_IMAGE_LIGHT,
            fit=ft.BoxFit.COVER,
            alignment=ft.Alignment.BOTTOM_CENTER,
        ),

        padding=ft.Padding(
            left=20,
            top=36,
            right=20,
            bottom=16,
        ),
        expand=True,
    )

    def show_status(message: str, is_error: bool = False):
        if is_error:
            status_icon.name = ft.Icons.ERROR_OUTLINE_ROUNDED
            status_icon.color = "#DC2626"
            status_text.color = "#DC2626"
            status_banner.bgcolor = "#FEF2F2" if page.theme_mode == ft.ThemeMode.LIGHT else "#3B1818"
            status_banner.border = ft.Border.all(1, "#FECACA" if page.theme_mode == ft.ThemeMode.LIGHT else "#7F1D1D")
        else:
            status_icon.name = ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED
            status_icon.color = "#16A34A"
            status_text.color = "#16A34A"
            status_banner.bgcolor = "#F0FDF4" if page.theme_mode == ft.ThemeMode.LIGHT else "#143321"
            status_banner.border = ft.Border.all(1, "#BBF7D0" if page.theme_mode == ft.ThemeMode.LIGHT else "#166534")

        status_text.value = message
        status_banner.visible = True

    def handle_login(e):
        username = (username_input.value or "").strip()
        password = password_input.value or ""

        username_input.error = None
        password_input.error = None
        status_banner.visible = False

        has_error = False

        if not username:
            username_input.error = "Vui lòng nhập tên đăng nhập"
            has_error = True

        if not password:
            password_input.error = "Vui lòng nhập mật khẩu"
            has_error = True

        if has_error:
            show_status("Vui lòng kiểm tra lại thông tin đăng nhập.", is_error=True)
            page.update()
            return

        show_status("Xác thực hợp lệ! Đang kết nối máy chủ...", is_error=False)
        page.update()

    login_button.on_click = handle_login

    async def focus_password(e):
        await password_input.focus()

    username_input.on_submit = focus_password
    password_input.on_submit = handle_login

    def change_mode_theme(e):
        is_dark = page.theme_mode == ft.ThemeMode.LIGHT
        mode_key = "dark" if is_dark else "light"
        palette = THEME_PALETTE[mode_key]

        page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        page.bgcolor = palette["page_bg"]

        # Quan trọng: thay DecorationImage của main_content theo Theme.
        # Tạo đối tượng mới để Flet nhận biết thuộc tính đã thay đổi.
        main_content.image = ft.DecorationImage(
            src=BG_IMAGE_DARK if is_dark else BG_IMAGE_LIGHT,
            fit=ft.BoxFit.COVER,
            alignment=ft.Alignment.BOTTOM_CENTER,
        )

        # Cập nhật Header & Logo
        header.bgcolor = palette["header_bg"]
        header_divider.color = palette["divider"]
        logo_img.src = LOGO_DARK if is_dark else LOGO_LIGHT

        theme_button.icon = (
            ft.Icons.LIGHT_MODE
            if is_dark
            else ft.Icons.DARK_MODE
        )
        theme_button.icon_color = palette["theme_btn_icon"]
        theme_button.bgcolor = palette["theme_btn_bg"]
        theme_button.tooltip = (
            "Chuyển sang Light Mode" if is_dark else "Chuyển sang Dark Mode"
        )

        # Cập nhật Khung Card, Text & Input
        form_card.bgcolor = palette["card_bg"]
        form_card.border = ft.Border.all(1, palette["card_border"])
        title_text.color = palette["text_primary"]

        for field in (username_input, password_input):
            field.bgcolor = palette["input_bg"]
            field.border = make_input_border(palette["input_border"])
            field.label_style = ft.TextStyle(color=palette["text_secondary"], size=13)
            field.hint_style = ft.TextStyle(color=palette["text_secondary"], size=13)

        footer_text.color = palette["text_secondary"]

        if status_banner.visible:
            is_err = status_icon.name == ft.Icons.ERROR_OUTLINE_ROUNDED
            show_status(status_text.value, is_error=is_err)

        page.update()

    theme_button.on_click = change_mode_theme

    # ======================================
    # LAYOUT ASSEMBLY
    # ======================================

    layout = ft.Column(
        controls=[
            header,
            header_divider,
            main_content
        ],
        spacing=0,
        expand=True,
    )

    page.add(layout)

    # Sau khi giao diện đã được đưa lên trang, căn giữa cửa sổ desktop.
    if is_desktop:
        await page.window.center()


if __name__ == "__main__":
    ft.run(
        main,
        assets_dir="assets",
    )