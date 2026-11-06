from typing import Any, Dict

import flet as ft

from ui.components.bom_table import BOMTable
from ui.components.summary_banner import SummaryBanner


class PreviewPanel(ft.Container):
    def __init__(self, on_export_excel, on_export_pdf, on_save_quote, on_share_quote):
        super().__init__(padding=ft.Padding(8, 4, 12, 8))
        self.summary = SummaryBanner()
        self.bom = BOMTable()
        self.total = ft.Text("Tổng thanh toán: 0 VNĐ", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
        self.customer = ft.Column(
            spacing=2,
            controls=[
                ft.Text("Khách hàng: Chưa cập nhật", color=ft.Colors.BLUE_GREY_700),
                ft.Text("Dự án: Chưa cập nhật", color=ft.Colors.BLUE_GREY_700),
                ft.Text("Điện thoại: Chưa cập nhật", color=ft.Colors.BLUE_GREY_700),
            ],
        )
        self.message = ft.Text("", color=ft.Colors.GREEN_700)
        self.pricing_details = ft.Column(spacing=3)
        self.content = ft.Column(
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=0,
                            controls=[
                                ft.Text("Báo giá hiện tại", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                                ft.Text("Kiểm tra thông tin trước khi xuất báo giá", size=12, color=ft.Colors.BLUE_GREY_600),
                            ],
                        ),
                        ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.CYAN_600, size=30),
                    ],
                ),
                ft.Card(
                    elevation=5,
                    bgcolor=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=20),
                    content=ft.Container(
                        padding=16,
                        content=ft.Column(
                            spacing=6,
                            controls=[
                                ft.Text(
                                    "Thông tin báo giá",
                                    size=17,
                                    weight=ft.FontWeight.BOLD,
                                    color="#1A1A1A",
                                ),
                                self.customer,
                            ],
                        ),
                    ),
                ),
                ft.Card(
                    elevation=5,
                    bgcolor=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=20),
                    content=self.summary,
                ),
                ft.Card(
                    elevation=5,
                    bgcolor=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=20),
                    content=self.bom,
                ),
                ft.Divider(),
                self.total,
                ft.Card(
                    elevation=2,
                    bgcolor=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=16),
                    content=ft.Container(
                        padding=14,
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text("Chi tiết giá báo khách", size=17, weight=ft.FontWeight.BOLD, color="#1A1A1A"),
                                self.pricing_details,
                            ],
                        ),
                    ),
                ),
                ft.Row(
                    spacing=8,
                    wrap=True,
                    controls=[
                        ft.FilledButton(
                            "Tải Excel",
                            icon=ft.Icons.TABLE_VIEW,
                            width=155,
                            on_click=on_export_excel,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.BLUE_800,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=14),
                            ),
                        ),
                        ft.OutlinedButton("Xuất PDF", icon=ft.Icons.PICTURE_AS_PDF, width=155, on_click=on_export_pdf),
                    ],
                ),
                ft.Row(
                    spacing=8,
                    wrap=True,
                    controls=[
                        ft.OutlinedButton("Lưu báo giá", icon=ft.Icons.SAVE, width=155, on_click=on_save_quote),
                        ft.OutlinedButton("In / Chia sẻ", icon=ft.Icons.SHARE, width=155, on_click=on_share_quote),
                    ],
                ),
                self.message,
            ],
        )

    def update_quote(self, quote: Dict[str, Any]):
        self.summary.update_data(quote["summary"])
        self.bom.update_rows(quote["bom"])
        self.total.value = f"Tổng thanh toán: {quote['pricing']['final_total']:,.0f} VNĐ"
        pricing = quote["pricing"]
        self.pricing_details.controls = [
            ft.Text(f"Giá vốn: {pricing['cost_total']:,.0f} VNĐ"),
            ft.Text(f"Lợi nhuận: {pricing['profit_value']:,.0f} VNĐ"),
            ft.Text(f"Chiết khấu: {pricing['discount_value']:,.0f} VNĐ"),
            ft.Text(f"VAT ({pricing['vat_percent']:.0f}%): {pricing['vat_value']:,.0f} VNĐ"),
            ft.Text(
                f"Đơn giá/m² (chưa VAT): {pricing['unit_price_m2_before_vat']:,.0f} VNĐ",
                weight=ft.FontWeight.BOLD,
            ),
        ]
        customer = quote.get("customer", {})
        name = customer.get("name") or "Chưa có khách hàng"
        project = customer.get("project") or "Chưa có tên dự án"
        phone = customer.get("phone")
        self.customer.controls[0].value = f"Khách hàng: {name}"
        self.customer.controls[1].value = f"Dự án: {project}"
        self.customer.controls[2].value = f"Điện thoại: {phone or 'Chưa cập nhật'}"
