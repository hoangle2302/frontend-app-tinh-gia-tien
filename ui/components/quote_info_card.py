"""Reusable LED quote information card (used by the configuration sheet)."""
import flet as ft
from ui.theme.tokens import UIColors


def make_info_card(title: str, icon, rows: list, on_edit_click=None):
    row_controls = []
    for label, val in rows:
        row_controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Text(label, size=11, color=UIColors.TEXT_SECONDARY),
                    ft.Text(
                        str(val),
                        size=11,
                        weight=ft.FontWeight.W_600,
                        color=UIColors.TEXT_PRIMARY,
                        text_align=ft.TextAlign.RIGHT,
                        expand=True,
                    ),
                ],
            )
        )
    header_right_controls = []
    if on_edit_click:
        header_right_controls.append(
            ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED,
                icon_size=15,
                icon_color=UIColors.PRIMARY,
                tooltip=f"Chỉnh sửa {title}",
                width=28,
                height=28,
                style=ft.ButtonStyle(padding=0),
                on_click=on_edit_click,
            )
        )
    return ft.Container(
        padding=ft.Padding(12, 10, 12, 10),
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, UIColors.BORDER),
        border_radius=12,
        content=ft.Column(
            spacing=5,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    width=24,
                                    height=24,
                                    border_radius=6,
                                    bgcolor="#EFF6FF",
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(icon, size=14, color=UIColors.PRIMARY),
                                ),
                                ft.Text(title, size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY),
                            ],
                        ),
                        *header_right_controls,
                    ],
                ),
                ft.Divider(height=1, color="#F1F5F9"),
                *row_controls,
            ],
        ),
    )
