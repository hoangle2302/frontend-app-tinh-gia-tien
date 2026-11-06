from typing import Dict, List

import flet as ft


class BOMTable(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = 16
        self.border_radius = 16
        self.bgcolor = ft.Colors.WHITE
        side = ft.BorderSide(1, ft.Colors.BLUE_GREY_100)
        self.border = ft.Border(top=side, right=side, bottom=side, left=side)

        self.rows_column = ft.Column(spacing=8)

        self.content = ft.Column(
            controls=[
                ft.Text("Bảng kê vật tư (BOM)", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                self.rows_column,
            ]
        )

    def update_rows(self, bom_rows: List[Dict]):
        rows: List[ft.Control] = []
        for row in bom_rows:
            rows.append(
                ft.Container(
                    padding=ft.Padding(10, 8, 10, 8),
                    border=ft.Border(
                        top=ft.BorderSide(1, ft.Colors.BLUE_GREY_100),
                        right=ft.BorderSide(1, ft.Colors.BLUE_GREY_100),
                        bottom=ft.BorderSide(1, ft.Colors.BLUE_GREY_100),
                        left=ft.BorderSide(1, ft.Colors.BLUE_GREY_100),
                    ),
                    border_radius=8,
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(str(row["name"]), weight=ft.FontWeight.BOLD),
                            ft.Text(str(row["spec"]), size=12, color=ft.Colors.BLUE_GREY_700),
                            ft.Row(
                                wrap=True,
                                spacing=12,
                                controls=[
                                    ft.Text(f"Số lượng: {row['qty']} {row['unit']}"),
                                    ft.Text(f"Đơn giá: {row['unit_price']:,.0f} VNĐ"),
                                    ft.Text(
                                        f"Thành tiền: {row['line_total']:,.0f} VNĐ",
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLUE_700,
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            )
        self.rows_column.controls = rows
