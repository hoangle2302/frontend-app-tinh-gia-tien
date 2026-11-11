import json
from typing import List, Dict

import flet as ft


class InventoryView(ft.Container):
    def __init__(self, products: List[Dict]):
        super().__init__()
        self.expand = True
        self.padding = 16

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Category")),
                ft.DataColumn(ft.Text("Code")),
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Unit")),
                ft.DataColumn(ft.Text("Price")),
                ft.DataColumn(ft.Text("Spec")),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(p["category"])),
                        ft.DataCell(ft.Text(p["code"])),
                        ft.DataCell(ft.Text(p["name"])),
                        ft.DataCell(ft.Text(p["unit"])),
                        ft.DataCell(ft.Text(f"{p['unit_price']:,.0f}")),
                        ft.DataCell(ft.Text(json.dumps(p["spec_json"]))),
                    ]
                )
                for p in products
            ],
            column_spacing=20,
            heading_row_color=ft.Colors.BLUE_GREY_50,
        )

        self.content = ft.Column(
            controls=[
                ft.Text("Danh mục linh kiện (chỉ đọc)", size=18, weight=ft.FontWeight.BOLD),
                ft.Row(scroll=ft.ScrollMode.ALWAYS, controls=[table]),
            ]
        )
