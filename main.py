import flet as ft

from database.db_manager import DBManager
from ui.views.auth_login_view import AuthLoginView
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
        color_scheme=ft.ColorScheme(
            primary="#004A98",
            on_primary=ft.Colors.WHITE,
            primary_container="#CBE6FF",
            on_primary_container="#001E30",
            secondary="#00B8E8",
            on_secondary=ft.Colors.WHITE,
            secondary_container="#ABEDFF",
            on_secondary_container="#001F26",
            tertiary="#525F70",
            surface="#FAFCFE",
            on_surface="#0F172A",
            surface_container="#EDF0F5",
            surface_container_high="#E7EAEF",
            outline="#72777F",
            outline_variant="#C2C7CF",
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
        color_scheme=ft.ColorScheme(
            primary="#8FCDFF",
            on_primary="#00344F",
            primary_container="#004B70",
            on_primary_container="#CBE6FF",
            secondary="#56D6F5",
            on_secondary="#003640",
            secondary_container="#004E5C",
            on_secondary_container="#ABEDFF",
            tertiary="#BAC8DB",
            surface="#091322",
            on_surface="#F8FAFC",
            surface_container="#1D2024",
            surface_container_high="#272A2E",
            outline="#8C9199",
            outline_variant="#42474E",
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
    page.bgcolor = "#FAFCFE"
    page.padding = 0
    page.spacing = 0

    theme_btn = ft.IconButton(
        icon=ft.Icons.DARK_MODE_OUTLINED,
        tooltip="Đổi giao diện sáng/tối",
        icon_color="#004A98",
        width=42,
        height=42,
        on_click=lambda e: _toggle_theme(page, e, app_state),
        style=ft.ButtonStyle(
            bgcolor="#EDF0F5",
            shape=ft.CircleBorder(),
            padding=0,
        ),
    )

    header_actions = ft.Row([theme_btn], spacing=6)

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

    # Content container
    content_area = ft.Container(expand=True)
    page.add(content_area)

    def on_login_success(username: str):
        app_state["username"] = username
        app_state["current_view"] = "main"

        # Hiển thị appbar trên màn hình chính
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
        app_state["login_view"].username_input.value = ""
        app_state["login_view"].password_input.value = ""
        app_state["login_view"].status_banner.visible = False

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
    page.bgcolor = "#091322" if is_dark else "#FAFCFE"

    if page.appbar:
        page.appbar.bgcolor = "#111827" if is_dark else ft.Colors.WHITE
        if page.appbar.leading and hasattr(page.appbar.leading, "content"):
            page.appbar.leading.content.src = "logo_dark.png" if is_dark else "logo_light.png"

    if e and hasattr(e, "control") and e.control:
        e.control.icon_color = "#8FCDFF" if is_dark else "#004A98"
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

    if app_state.get("login_view"):
        app_state["login_view"].apply_theme(is_dark)

    if app_state.get("main_view"):
        app_state["main_view"].apply_theme(is_dark)

    page.update()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
