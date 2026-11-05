import flet as ft

from database.db_manager import DBManager
from ui.views.main_view import MainView


def main(page: ft.Page):
    page.title = "Báo giá Màn hình LED"
    page.window_width = 1360
    page.window_height = 860
    page.min_width = 320
    page.min_height = 480
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.BLUE_700,
            secondary=ft.Colors.TEAL_600,
            surface=ft.Colors.WHITE,
        ),
        visual_density=ft.VisualDensity.COMFORTABLE,
    )
    page.padding = 4
    page.spacing = 0
    page.appbar = ft.AppBar(
        title=ft.Text("Báo giá Màn hình LED", weight=ft.FontWeight.BOLD),
        center_title=False,
        bgcolor=ft.Colors.BLUE_800,
        color=ft.Colors.WHITE,
    )

    db = DBManager()
    db.initialize()

    view = MainView(page=page, db=db)
    view.mount()


if __name__ == "__main__":
    ft.run(main)
