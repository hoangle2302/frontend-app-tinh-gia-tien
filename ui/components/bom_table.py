from typing import Dict, List

import flet as ft


class BOMTable(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = ft.Padding(0, 0, 0, 0)
        self.bgcolor = ft.Colors.TRANSPARENT

        self.rows_column = ft.Column(spacing=8)

        self.content = ft.Card(
            elevation=0,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(
                radius=14,
                side=ft.BorderSide(width=1, color="#E2E8F0"),
            ),
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    width=4,
                                    height=16,
                                    bgcolor="#2563EB",
                                    border_radius=2,
                                ),
                                ft.Text(
                                    "Bảng kê vật tư (BOM)",
                                    size=15,
                                    weight=ft.FontWeight.BOLD,
                                    color="#0F172A",
                                ),
                            ],
                        ),
                        self.rows_column,
                    ],
                ),
            ),
        )

    def update_rows(self, bom_rows: List[Dict]):
        rows: List[ft.Control] = []
        for row in bom_rows:
            rows.append(
                ft.Container(
                    padding=ft.Padding(12, 10, 12, 10),
                    border=ft.Border.all(1, "#E2E8F0"),
                    border_radius=12,
                    bgcolor="#F8F9FC",
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(str(row["name"]), weight=ft.FontWeight.BOLD, size=14, color="#0F172A"),
                                    ft.Text(
                                        f"{row['line_total']:,.0f} đ",
                                        weight=ft.FontWeight.BOLD,
                                        size=14,
                                        color="#2563EB",
                                    ),
                                ],
                            ),
                            ft.Text(str(row["spec"]), size=12, color="#64748B"),
                            ft.Row(
                                wrap=True,
                                spacing=12,
                                controls=[
                                    ft.Text(f"SL: {row['qty']} {row['unit']}", size=12, color="#42474E"),
                                    ft.Text(f"Đơn giá: {row['unit_price']:,.0f} đ", size=12, color="#42474E"),
                                ],
                            ),
                        ],
                    ),
                )
            )
        self.rows_column.controls = rows
