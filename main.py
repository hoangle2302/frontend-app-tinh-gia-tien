import flet as ft

from database.db_manager import DBManager
from ui.views.auth_login_view import AuthLoginView
from ui.views.brand_loading_view import BrandLoadingView
from ui.views.main_view import MainView


def main(page: ft.Page):
    app_state = {
        "current_view": "login",
        "main_view": None,
        "login_view": None,
        "username": None,
    }

    logo_container = ft.Container(
        width=175,
        height=42,
        alignment=ft.Alignment(-1, 0),
        content=ft.Image(
            src="logo_light.png",
            width=170,
            height=40,
            fit=ft.BoxFit.CONTAIN,
        ),
    )
    page.title = "TOÀN TRUNG - Báo giá Màn hình LED"
    page.window.width = 440
    page.window.height = 760
    page.window.min_width = 340
    page.window.min_height = 500
    page.scroll = None
    page.theme_mode = ft.ThemeMode.LIGHT

    # Material 3 Color Schemes
    page.theme = ft.Theme(
        canvas_color=ft.Colors.WHITE,
        card_bgcolor=ft.Colors.WHITE,
        color_scheme=ft.ColorScheme(
            primary="#2563EB",
            on_primary=ft.Colors.WHITE,
            primary_container="#E8EEFF",
            on_primary_container="#001E30",
            secondary="#00B8E8",
            on_secondary=ft.Colors.WHITE,
            secondary_container="#ABEDFF",
            on_secondary_container="#001F26",
            tertiary="#525F70",
            surface=ft.Colors.WHITE,
            on_surface="#0F172A",
            surface_container=ft.Colors.WHITE,
            surface_container_high=ft.Colors.WHITE,
            outline="#72777F",
            outline_variant="#C2C7CF",
        ),
        popup_menu_theme=ft.PopupMenuTheme(
            color=ft.Colors.WHITE,
            elevation=6,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        dropdown_theme=ft.DropdownTheme(
            menu_style=ft.MenuStyle(
                bgcolor=ft.Colors.WHITE,
                elevation=6,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        ),
        visual_density=ft.VisualDensity.STANDARD,
    )
    page.dark_theme = ft.Theme(
        canvas_color="#1D2024",
        card_bgcolor="#1D2024",
        color_scheme=ft.ColorScheme(
            primary="#8FCDFF",
            on_primary="#00344F",
            primary_container="#004B70",
            on_primary_container="#E8EEFF",
            secondary="#56D6F5",
            on_secondary="#003640",
            secondary_container="#004E5C",
            on_secondary_container="#ABEDFF",
            tertiary="#BAC8DB",
            surface="#1D2024",
            on_surface="#F8FAFC",
            surface_container="#1D2024",
            surface_container_high="#272A2E",
            outline="#8C9199",
            outline_variant="#42474E",
        ),
        popup_menu_theme=ft.PopupMenuTheme(
            color="#1D2024",
            elevation=6,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        dropdown_theme=ft.DropdownTheme(
            menu_style=ft.MenuStyle(
                bgcolor="#1D2024",
                elevation=6,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        ),
        visual_density=ft.VisualDensity.STANDARD,
    )
    page.bgcolor = "#F5F7FB"
    page.padding = 0
    page.spacing = 0

    theme_btn = ft.IconButton(
        icon=ft.Icons.DARK_MODE_OUTLINED,
        tooltip="Đổi giao diện sáng/tối",
        icon_color="#2563EB",
        width=38,
        height=38,
        on_click=lambda e: _toggle_theme(page, e, app_state),
        style=ft.ButtonStyle(
            bgcolor="#E8EEFF",
            shape=ft.CircleBorder(),
            padding=0,
        ),
        scale=1.0,
        animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
        animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
    )

    history_btn = ft.IconButton(
        icon=ft.Icons.HISTORY,
        tooltip="Lịch sử báo giá",
        icon_color="#2563EB",
        width=38,
        height=38,
        on_click=lambda e: app_state["main_view"] and app_state["main_view"].open_history(),
        style=ft.ButtonStyle(bgcolor="#E8EEFF", shape=ft.CircleBorder(), padding=0),
        scale=1.0,
        animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
    )

    avatar_btn = ft.IconButton(
        icon=ft.Icons.PERSON,
        tooltip="Hồ sơ",
        icon_color="#2563EB",
        width=38,
        height=38,
        on_click=lambda e: app_state["main_view"] and app_state["main_view"].open_profile(),
        style=ft.ButtonStyle(bgcolor="#E8EEFF", shape=ft.CircleBorder(), padding=0),
        scale=1.0,
        animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
    )

    header_actions = ft.Row([history_btn, theme_btn, avatar_btn], spacing=8)

    main_appbar = ft.AppBar(
        leading=logo_container,
        leading_width=185,
        toolbar_height=58,
        bgcolor=ft.Colors.WHITE,
        elevation=0,
        actions=[header_actions],
    )

    db = DBManager()
    db.initialize()

    # Content container sử dụng AnimatedSwitcher để chuyển đổi mượt mà giữa Đăng nhập, Loading và Màn chính
    content_area = ft.AnimatedSwitcher(
        content=ft.Container(expand=True),
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=320,
        reverse_duration=220,
        switch_in_curve=ft.AnimationCurve.EASE_OUT_CUBIC,
        switch_out_curve=ft.AnimationCurve.EASE_IN_CUBIC,
        expand=True,
    )
    page.add(content_area)

    def on_login_success(username: str):
        app_state["username"] = username
        app_state["current_view"] = "loading"

        # Ẩn AppBar trong lúc hiển thị màn hình nạp thương hiệu
        page.appbar = None

        def proceed():
            app_state["current_view"] = "main"
            page.appbar = main_appbar
            is_dark = page.theme_mode == ft.ThemeMode.DARK
            page.appbar.bgcolor = "#111827" if is_dark else ft.Colors.WHITE
            if page.appbar.leading and hasattr(page.appbar.leading, "content"):
                page.appbar.leading.content.src = "logo_dark.png" if is_dark else "logo_light.png"

            if not app_state["main_view"]:
                app_state["main_view"] = MainView(
                    page=page,
                    db=db,
                    on_logout=lambda p: _handle_logout(p, app_state),
                )
            if hasattr(app_state["main_view"], "input_panel"):
                app_state["main_view"].input_panel.customer_name.value = username

            content_area.content = app_state["main_view"].tabs
            app_state["main_view"].mount()
            app_state["main_view"].on_resize()
            page.update()

        brand_loader = BrandLoadingView(
            username=username,
            on_complete=proceed,
            page=page,
            db_manager=db,
        )
        content_area.content = brand_loader
        page.update()
        brand_loader.start()

    login_view = AuthLoginView(
        page=page,
        on_login_success=on_login_success,
        on_toggle_theme=lambda e: _toggle_theme(page, e, app_state),
    )
    app_state["login_view"] = login_view

    # Mặc định ở màn hình Login: Dùng header tích hợp sẵn trong LoginView
    page.appbar = None
    content_area.content = login_view

    def on_resize(e=None):
        compact = page.width < 380
        logo_container.width = 150 if compact else 175
        logo_container.content.width = 145 if compact else 170
        if page.appbar:
            page.appbar.leading_width = 155 if compact else 185
        if app_state["current_view"] == "main" and app_state["main_view"]:
            app_state["main_view"].on_resize(e)
        page.update()

    page.on_resize = on_resize
    on_resize()


def _handle_logout(page: ft.Page, app_state: dict):
    app_state["current_view"] = "login"
    app_state["username"] = None
    if app_state.get("login_view"):
        app_state["login_view"].reset()

    page.appbar = None
    if len(page.controls) > 0:
        page.controls[0].content = app_state["login_view"]

    page.update()


def _toggle_theme(page: ft.Page, e, app_state: dict):
    is_dark = page.theme_mode == ft.ThemeMode.LIGHT
    page.theme_mode = (
        ft.ThemeMode.DARK
        if is_dark
        else ft.ThemeMode.LIGHT
    )
    page.bgcolor = "#091322" if is_dark else "#F5F7FB"

    if page.appbar:
        page.appbar.bgcolor = "#111827" if is_dark else ft.Colors.WHITE
        if page.appbar.leading and hasattr(page.appbar.leading, "content"):
            page.appbar.leading.content.src = "logo_dark.png" if is_dark else "logo_light.png"

    if e and hasattr(e, "control") and e.control:
        e.control.icon_color = "#8FCDFF" if is_dark else "#2563EB"
        e.control.style = ft.ButtonStyle(
            bgcolor="#1D2024" if is_dark else "#EDF0F5",
            shape=ft.CircleBorder(),
            padding=0,
        )
        e.control.icon = (
            ft.Icons.LIGHT_MODE_OUTLINED
            if is_dark
            else ft.Icons.DARK_MODE_OUTLINED
        )
        current_rotate = getattr(e.control, "rotate", 0) or 0
        e.control.rotate = current_rotate + 3.14159 / 2
        e.control.animate_rotation = ft.Animation(300, ft.AnimationCurve.EASE_OUT)

    if app_state.get("login_view"):
        app_state["login_view"].apply_theme(is_dark)

    if app_state.get("main_view"):
        app_state["main_view"].apply_theme(is_dark)

    # Cập nhật style cho các nút header khi đổi theme sáng/tối
    if hasattr(page, "appbar") and page.appbar and hasattr(page.appbar, "actions") and page.appbar.actions:
        actions = page.appbar.actions[0].controls if page.appbar.actions[0] and hasattr(page.appbar.actions[0], "controls") else []
        for c in actions:
            if isinstance(c, ft.IconButton):
                c.icon_color = "#8FCDFF" if is_dark else "#2563EB"
                c.style.bgcolor = "#1D2024" if is_dark else "#E8EEFF"
            elif isinstance(c, ft.Container):
                c.bgcolor = "#1D2024" if is_dark else "#E8EEFF"
                if c.content and isinstance(c.content, ft.Text):
                    c.content.color = "#8FCDFF" if is_dark else "#2563EB"

    page.update()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
