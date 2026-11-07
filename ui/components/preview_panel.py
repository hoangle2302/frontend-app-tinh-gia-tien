from typing import Any, Dict

import flet as ft

from ui.components.bom_table import BOMTable
from ui.components.summary_banner import SummaryBanner


class PreviewPanel(ft.Container):
    def __init__(self, on_export_excel, on_export_pdf, on_save_quote, on_share_quote):
        super().__init__(padding=ft.Padding(4, 4, 4, 12))
        self.summary = SummaryBanner()
        self.bom = BOMTable()
        self.total = ft.Text("0 VNĐ", size=24, weight=ft.FontWeight.BOLD, color="#006494")
        self.customer = ft.Column(
            spacing=4,
            controls=[
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(ft.Icons.PERSON_OUTLINE, size=16, color="#72777F"),
                        ft.Text("Khách hàng: Chưa cập nhật", size=13, color="#42474E"),
                    ],
                ),
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(ft.Icons.BUSINESS_OUTLINED, size=16, color="#72777F"),
                        ft.Text("Dự án: Chưa cập nhật", size=13, color="#42474E"),
                    ],
                ),
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(ft.Icons.PHONE_OUTLINED, size=16, color="#72777F"),
                        ft.Text("Điện thoại: Chưa cập nhật", size=13, color="#42474E"),
                    ],
                ),
            ],
        )
        self.message = ft.Text("", color=ft.Colors.GREEN_700)
        self.pricing_details = ft.Column(spacing=4)
        self.content = ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=4,
                                    height=24,
                                    bgcolor="#00687A",
                                    border_radius=2,
                                ),
                                ft.Column(
                                    spacing=1,
                                    controls=[
                                        ft.Text("Báo giá chi tiết", size=20, weight=ft.FontWeight.BOLD, color="#191C1E"),
                                        ft.Text("Xem trước kết quả dự toán và thông số", size=12, color="#72777F"),
                                    ],
                                ),
                            ],
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SHARE_OUTLINED,
                            tooltip="Chia sẻ / Sao chép",
                            style=ft.ButtonStyle(
                                side=ft.BorderSide(1, "#C2C7CF"),
                                shape=ft.CircleBorder(),
                            ),
                            on_click=on_share_quote,
                        ),
                    ],
                ),
                ft.Card(
                    elevation=0,
                    bgcolor=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(
                        radius=16,
                        side=ft.BorderSide(width=1, color="#E0E2EC"),
                    ),
                    content=ft.Container(
                        padding=16,
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Container(
                                            width=4,
                                            height=16,
                                            bgcolor="#006494",
                                            border_radius=2,
                                        ),
                                        ft.Text(
                                            "Thông tin khách hàng",
                                            size=15,
                                            weight=ft.FontWeight.BOLD,
                                            color="#191C1E",
                                        ),
                                    ],
                                ),
                                self.customer,
                            ],
                        ),
                    ),
                ),
                self.summary,
                self.bom,
                ft.Card(
                    elevation=0,
                    bgcolor="#EAF2FA",
                    shape=ft.RoundedRectangleBorder(
                        radius=16,
                        side=ft.BorderSide(width=1, color="#C2C7CF"),
                    ),
                    content=ft.Container(
                        padding=16,
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Container(
                                            width=4,
                                            height=16,
                                            bgcolor="#006494",
                                            border_radius=2,
                                        ),
                                        ft.Text("Chi tiết giá & Thanh toán", size=15, weight=ft.FontWeight.BOLD, color="#191C1E"),
                                    ],
                                ),
                                self.pricing_details,
                                ft.Divider(color="#C2C7CF", height=1),
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Text("Tổng cộng thanh toán:", size=14, weight=ft.FontWeight.BOLD, color="#191C1E"),
                                        self.total,
                                    ],
                                ),
                            ],
                        ),
                    ),
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.FilledButton(
                            "Tải Excel",
                            icon=ft.Icons.TABLE_VIEW,
                            expand=True,
                            height=44,
                            on_click=on_export_excel,
                            style=ft.ButtonStyle(
                                bgcolor="#006494",
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=20),
                            ),
                        ),
                        ft.FilledTonalButton(
                            "Xuất PDF",
                            icon=ft.Icons.PICTURE_AS_PDF_OUTLINED,
                            expand=True,
                            height=44,
                            on_click=on_export_pdf,
                            style=ft.ButtonStyle(
                                bgcolor="#CBE6FF",
                                color="#001E30",
                                shape=ft.RoundedRectangleBorder(radius=20),
                            ),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.OutlinedButton(
                            "Lưu báo giá",
                            icon=ft.Icons.SAVE_OUTLINED,
                            expand=True,
                            height=44,
                            on_click=on_save_quote,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=20),
                            ),
                        ),
                        ft.OutlinedButton(
                            "Sao chép tóm tắt",
                            icon=ft.Icons.COPY_ALL_OUTLINED,
                            expand=True,
                            height=44,
                            on_click=on_share_quote,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=20),
                            ),
                        ),
                    ],
                ),
                self.message,
            ],
        )

    def update_quote(self, quote: Dict[str, Any]):
        self.summary.update_data(quote["summary"])
        self.bom.update_rows(quote["bom"])
        self.total.value = f"{quote['pricing']['final_total']:,.0f} VNĐ"
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
        phone = customer.get("phone") or "Chưa cập nhật"
        if len(self.customer.controls) >= 3:
            self.customer.controls[0].controls[1].value = f"Khách hàng: {name}"
            self.customer.controls[1].controls[1].value = f"Dự án: {project}"
            self.customer.controls[2].controls[1].value = f"Điện thoại: {phone}"
