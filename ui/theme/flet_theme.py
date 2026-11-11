"""Application-wide Flet 1.1.2 light and dark Material theme."""
import flet as ft
from ui.theme.tokens import UIColors

def install_theme(page: ft.Page) -> None:
    """Apply design-system themes. Colors used by each screen are in tokens.py."""
    page.theme = ft.Theme(
        canvas_color=ft.Colors.WHITE,
        card_bgcolor=ft.Colors.WHITE,
        color_scheme=ft.ColorScheme(
            primary=UIColors.PRIMARY,
            on_primary=ft.Colors.WHITE,
            primary_container=UIColors.PRIMARY_SOFT,
            on_primary_container="#001E30",
            secondary=UIColors.SECONDARY,
            on_secondary=ft.Colors.WHITE,
            secondary_container="#ABEDFF",
            on_secondary_container="#001F26",
            tertiary="#525F70",
            surface=ft.Colors.WHITE,
            on_surface=UIColors.TEXT_PRIMARY,
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
        canvas_color=UIColors.DARK_SURFACE,
        card_bgcolor=UIColors.DARK_SURFACE,
        color_scheme=ft.ColorScheme(
            primary="#8FCDFF",
            on_primary="#00344F",
            primary_container="#004B70",
            on_primary_container=UIColors.PRIMARY_SOFT,
            secondary="#56D6F5",
            on_secondary="#003640",
            secondary_container="#004E5C",
            on_secondary_container="#ABEDFF",
            tertiary="#BAC8DB",
            surface=UIColors.DARK_SURFACE,
            on_surface=UIColors.SURFACE_SUBTLE,
            surface_container=UIColors.DARK_SURFACE,
            surface_container_high="#272A2E",
            outline="#8C9199",
            outline_variant="#42474E",
        ),
        popup_menu_theme=ft.PopupMenuTheme(
            color=UIColors.DARK_SURFACE,
            elevation=6,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        dropdown_theme=ft.DropdownTheme(
            menu_style=ft.MenuStyle(
                bgcolor=UIColors.DARK_SURFACE,
                elevation=6,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        ),
        visual_density=ft.VisualDensity.STANDARD,
    )
