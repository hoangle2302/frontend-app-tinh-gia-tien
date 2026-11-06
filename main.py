import flet as ft

from database.db_manager import DBManager
from ui.views.main_view import MainView


def main(page: ft.Page):
    theme_context = {"view": None}
    logo_container = ft.Container(
        width=220,
        height=52,
        alignment=ft.Alignment(-1, 0),
        content=ft.Image(
            src="logo_horizontal.png",
            width=215,
            height=46,
            fit=ft.BoxFit.CONTAIN,
        ),
    )
    page.title = "Báo giá Màn hình LED"
    page.window.width = 400
    page.window.height = 700
    page.window.min_width = 320
    page.window.min_height = 480
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F5F7FA"
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.BLUE_800,
            secondary=ft.Colors.CYAN_600,
            surface=ft.Colors.WHITE,
        ),
        visual_density=ft.VisualDensity.COMFORTABLE,
    )
    page.dark_theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#42A5F5",
            secondary="#00B4D8",
            surface="#17212B",
        ),
        visual_density=ft.VisualDensity.COMFORTABLE,
    )
    page.padding = 0
    page.spacing = 0
    page.appbar = ft.AppBar(
        leading=logo_container,
        leading_width=225,
        toolbar_height=58,
        bgcolor=ft.Colors.WHITE,
        elevation=0,
        actions=[
            ft.IconButton(
                icon=ft.Icons.DARK_MODE_OUTLINED,
                tooltip="Đổi chế độ sáng/tối",
                icon_color=ft.Colors.BLUE_800,
                width=48,
                height=48,
                on_click=lambda e: _toggle_theme(page, e, theme_context["view"]),
                style=ft.ButtonStyle(
                    bgcolor="#F5F7FA",
                    shape=ft.RoundedRectangleBorder(radius=12),
                    padding=0,
                ),
            ),
        ],
    )

    db = DBManager()
    db.initialize()

    view = MainView(page=page, db=db)
    theme_context["view"] = view
    view.mount()

    def on_resize(e=None):
        compact = page.width < 380
        logo_container.width = 165 if compact else 220
        logo_container.content.width = 160 if compact else 215
        page.appbar.leading_width = 170 if compact else 225
        view.on_resize(e)

    page.on_resize = on_resize
    on_resize()


def _toggle_theme(page: ft.Page, e, view=None):
    is_dark = page.theme_mode == ft.ThemeMode.LIGHT
    page.theme_mode = (
        ft.ThemeMode.DARK
        if is_dark
        else ft.ThemeMode.LIGHT
    )
    page.bgcolor = "#17212B" if is_dark else "#F5F7FA"
    page.appbar.bgcolor = "#17212B" if is_dark else ft.Colors.WHITE
    e.control.icon_color = "#42A5F5" if is_dark else ft.Colors.BLUE_800
    e.control.style = ft.ButtonStyle(
        bgcolor="#243442" if is_dark else "#F5F7FA",
        shape=ft.RoundedRectangleBorder(radius=12),
        padding=0,
    )
    e.control.icon = (
        ft.Icons.LIGHT_MODE_OUTLINED
        if is_dark
        else ft.Icons.DARK_MODE_OUTLINED
    )
    if view is not None:
        view.apply_theme(is_dark)
    page.update()


if __name__ == "__main__":
    ft.run(main)
