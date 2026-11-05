from typing import Any, Dict

import flet as ft

from ui.components.bom_table import BOMTable
from ui.components.summary_banner import SummaryBanner


class PreviewPanel(ft.Container):
    def __init__(self, on_export_excel, on_export_pdf, on_save_quote, on_share_quote):
        super().__init__(expand=True, padding=6)
        self.summary = SummaryBanner()
        self.bom = BOMTable()
        self.total = ft.Text("Tổng thanh toán: 0 VNĐ", size=28, weight=ft.FontWeight.BOLD)
        self.customer = ft.Column(
            spacing=2,
            controls=[
                ft.Text("Khách hàng: Chưa cập nhật", color=ft.Colors.BLUE_GREY_700),
                ft.Text("Dự án: Chưa cập nhật", color=ft.Colors.BLUE_GREY_700),
                ft.Text("Điện thoại: Chưa cập nhật", color=ft.Colors.BLUE_GREY_700),
            ],
        )
        self.message = ft.Text("", color=ft.Colors.GREEN_700)
        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Báo giá hiện tại", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    padding=12,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Text("Thông tin báo giá", weight=ft.FontWeight.BOLD),
                            self.customer,
                        ],
                    ),
                ),
                self.summary,
                self.bom,
                ft.Divider(),
                self.total,
                ft.Row(
                    wrap=True,
                    controls=[
                        ft.FilledButton("Tải Excel", icon=ft.Icons.TABLE_VIEW, on_click=on_export_excel),
                        ft.OutlinedButton("Xuất PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=on_export_pdf),
                        ft.OutlinedButton("Lưu báo giá", icon=ft.Icons.SAVE, on_click=on_save_quote),
                        ft.OutlinedButton("In / Chia sẻ", icon=ft.Icons.SHARE, on_click=on_share_quote),
                    ],
                ),
                self.message,
            ],
        )

    def update_quote(self, quote: Dict[str, Any]):
        self.summary.update_data(quote["summary"])
        self.bom.update_rows(quote["bom"])
        self.total.value = f"Tổng thanh toán: {quote['pricing']['final_total']:,.0f} VNĐ"
        customer = quote.get("customer", {})
        name = customer.get("name") or "Chưa có khách hàng"
        project = customer.get("project") or "Chưa có tên dự án"
        phone = customer.get("phone")
        self.customer.controls[0].value = f"Khách hàng: {name}"
        self.customer.controls[1].value = f"Dự án: {project}"
        self.customer.controls[2].value = f"Điện thoại: {phone or 'Chưa cập nhật'}"
