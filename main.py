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
    page.title = "Báo giá Màn hình LED - toàn trung"
    page.window.width = 440
    page.window.height = 760
    page.window.min_width = 340
    page.window.min_height = 500
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT

    # Material 3 Color Schemes
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#006494",
            on_primary=ft.Colors.WHITE,
            primary_container="#CBE6FF",
            on_primary_container="#001E30",
            secondary="#00687A",
            on_secondary=ft.Colors.WHITE,
            secondary_container="#ABEDFF",
            on_secondary_container="#001F26",
            tertiary="#525F70",
            surface="#F8F9FC",
            on_surface="#191C1E",
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
            surface="#101418",
            on_surface="#E0E2E8",
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
    page.bgcolor = "#F8F9FC"
    page.padding = 0
    page.spacing = 0
    page.appbar = ft.AppBar(
        leading=logo_container,
        leading_width=225,
        toolbar_height=60,
        bgcolor=ft.Colors.TRANSPARENT,
        elevation=0,
        actions=[
            ft.IconButton(
                icon=ft.Icons.DARK_MODE_OUTLINED,
                tooltip="Đổi giao diện sáng/tối",
                icon_color="#006494",
                width=44,
                height=44,
                on_click=lambda e: _toggle_theme(page, e, theme_context["view"]),
                style=ft.ButtonStyle(
                    bgcolor="#EDF0F5",
                    shape=ft.CircleBorder(),
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
    page.bgcolor = "#101418" if is_dark else "#F8F9FC"
    e.control.icon_color = "#8FCDFF" if is_dark else "#006494"
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
    if view is not None:
        view.apply_theme(is_dark)
    page.update()


if __name__ == "__main__":
    ft.run(main)
