import flet as ft

from database.db_manager import DBManager
from app.fastbusiness.service import AuthService
from ui.views.auth_login_view import AuthLoginView
from ui.views.brand_loading_view import BrandLoadingView
from ui.views.main_view import MainView
from ui.shell.app_header import AppHeader
from ui.theme.flet_theme import install_theme
from ui.theme.tokens import UIColors


def main(page: ft.Page):
    app_state = {
        "current_view": "login",
        "main_view": None,
        "login_view": None,
        "username": None,
    }

    page.title = "TOÀN TRUNG - Báo giá Màn hình LED"
    page.window.width = 440
    page.window.height = 760
    page.window.min_width = 340
    page.window.min_height = 500
    page.scroll = None
    page.theme_mode = ft.ThemeMode.LIGHT

    # Unified Material theme lives in ui/theme/flet_theme.py
    install_theme(page)
    page.bgcolor = UIColors.PAGE_BACKGROUND
    page.padding = 0
    page.spacing = 0

    header = AppHeader(
        on_toggle_theme=lambda e: _toggle_theme(page, e, app_state),
        on_history=lambda e: app_state["main_view"] and app_state["main_view"].open_history(),
        on_profile=lambda e: app_state["main_view"] and app_state["main_view"].open_profile(),
    )
    main_appbar = header.appbar

    from app.config import settings
    db = DBManager(settings.DB_PATH)
    db.initialize()
    auth_service = AuthService()
    app_state["auth_service"] = auth_service

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
                    screen_types=auth_service.screen_types,
                )
            else:
                # Đảm bảo luôn chuyển về tab 0 (Lập dự toán) khi đăng nhập lại
                if hasattr(app_state["main_view"], "reset"):
                    app_state["main_view"].reset()
                else:
                    app_state["main_view"]._go_tab(0)
            if hasattr(app_state["main_view"], "input_panel"):
                app_state["main_view"].input_panel.customer_name.value = username
                app_state["main_view"].input_panel.set_screen_types(auth_service.screen_types)

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
        auth_service=auth_service,
    )
    app_state["login_view"] = login_view

    # Mặc định ở màn hình Login: Dùng header tích hợp sẵn trong LoginView
    page.appbar = None
    content_area.content = login_view

    def on_resize(e=None):
        compact = (page.width or 440) < 380
        header.on_resize(compact)
        if app_state["current_view"] == "main" and app_state["main_view"]:
            app_state["main_view"].on_resize(e)
        if app_state["current_view"] == "login" and app_state.get("login_view") and hasattr(app_state["login_view"], "on_resize"):
            app_state["login_view"].on_resize(e)
        page.update()

    page.on_resize = on_resize
    on_resize()


def _handle_logout(page: ft.Page, app_state: dict):
    app_state["current_view"] = "login"
    app_state["username"] = None
    if app_state.get("auth_service"):
        app_state["auth_service"].close()
    if app_state.get("login_view"):
        app_state["login_view"].reset()

    if app_state.get("main_view"):
        if hasattr(app_state["main_view"], "reset"):
            app_state["main_view"].reset()
        else:
            app_state["main_view"]._go_tab(0)

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
    page.bgcolor = UIColors.DARK_PAGE_BACKGROUND if is_dark else UIColors.PAGE_BACKGROUND

    if page.appbar:
        page.appbar.bgcolor = "#111827" if is_dark else ft.Colors.WHITE
        if page.appbar.leading and hasattr(page.appbar.leading, "content"):
            page.appbar.leading.content.src = "logo_dark.png" if is_dark else "logo_light.png"

    if e and hasattr(e, "control") and e.control:
        e.control.icon_color = "#8FCDFF" if is_dark else UIColors.PRIMARY
        e.control.style = ft.ButtonStyle(
            bgcolor=UIColors.DARK_SURFACE if is_dark else "#EDF0F5",
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
                c.icon_color = "#8FCDFF" if is_dark else UIColors.PRIMARY
                c.style.bgcolor = UIColors.DARK_SURFACE if is_dark else UIColors.PRIMARY_SOFT
            elif isinstance(c, ft.Container):
                c.bgcolor = UIColors.DARK_SURFACE if is_dark else UIColors.PRIMARY_SOFT
                if c.content and isinstance(c.content, ft.Text):
                    c.content.color = "#8FCDFF" if is_dark else UIColors.PRIMARY

    page.update()
