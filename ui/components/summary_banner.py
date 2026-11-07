from typing import Dict

import flet as ft


class SummaryBanner(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = ft.Padding(0, 0, 0, 0)
        self.bgcolor = ft.Colors.TRANSPARENT

        self.size_text = ft.Text("-", size=14, weight=ft.FontWeight.BOLD, color="#191C1E", no_wrap=True)
        self.res_text = ft.Text("-", size=14, weight=ft.FontWeight.BOLD, color="#191C1E", no_wrap=True)
        self.refresh_text = ft.Text("-", size=14, weight=ft.FontWeight.BOLD, color="#191C1E", no_wrap=True)
        self.module_text = ft.Text("-", size=14, weight=ft.FontWeight.BOLD, color="#191C1E", no_wrap=True)
        self.power_text = ft.Text("-", size=14, weight=ft.FontWeight.BOLD, color="#191C1E", no_wrap=True)
        self.card_text = ft.Text("-", size=14, weight=ft.FontWeight.BOLD, color="#191C1E", no_wrap=True)
        self.processor_text = ft.Text("-", size=13, weight=ft.FontWeight.W_500, color="#191C1E")
        self.area_text = ft.Text("-", size=14, weight=ft.FontWeight.BOLD, color="#191C1E", no_wrap=True)
        self.badge = ft.Container(
            content=ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=16, color="#BA1A1A"),
                    ft.Text("Lệch kích thước > 5%", color="#BA1A1A", size=12, weight=ft.FontWeight.W_500),
                ],
            ),
            padding=ft.Padding(10, 6, 12, 6),
            border_radius=12,
            bgcolor="#FFDAD6",
            visible=False,
        )

        self.content = ft.Card(
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
                                ft.Text("Thông số kỹ thuật", size=15, weight=ft.FontWeight.BOLD, color="#191C1E"),
                            ],
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                self._metric_card("Kích thước", self.size_text, ft.Icons.ASPECT_RATIO_OUTLINED),
                                self._metric_card("Độ phân giải", self.res_text, ft.Icons.GRID_VIEW_OUTLINED),
                            ],
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                self._metric_card("Tần số quét", self.refresh_text, ft.Icons.SPEED_OUTLINED),
                                self._metric_card("Số module", self.module_text, ft.Icons.VIEW_MODULE_OUTLINED),
                            ],
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                self._metric_card("Số nguồn", self.power_text, ft.Icons.POWER_OUTLINED),
                                self._metric_card("Card thu", self.card_text, ft.Icons.MEMORY_OUTLINED),
                            ],
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                self._metric_card("Diện tích", self.area_text, ft.Icons.SQUARE_FOOT_OUTLINED),
                                ft.Container(
                                    expand=True,
                                    padding=ft.Padding(12, 10, 12, 10),
                                    border_radius=12,
                                    bgcolor="#EDF0F5",
                                    content=ft.Column(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=4,
                                        controls=[
                                            ft.Row(
                                                spacing=4,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                controls=[
                                                    ft.Icon(ft.Icons.DEVELOPER_BOARD_OUTLINED, size=15, color="#006494"),
                                                    ft.Text("Bộ xử lý", size=12, color="#006494", weight=ft.FontWeight.BOLD),
                                                ],
                                            ),
                                            self.processor_text,
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        self.badge,
                    ],
                ),
            ),
        )

    @staticmethod
    def _metric_card(label: str, value: ft.Text, icon: str = None) -> ft.Container:
        return ft.Container(
            expand=True,
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=12,
            bgcolor="#F0F4F8",
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    ft.Row(
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(icon, size=15, color="#72777F") if icon else ft.Container(),
                            ft.Text(label, size=12, color="#72777F", weight=ft.FontWeight.W_500),
                        ],
                    ),
                    value,
                ],
            ),
        )

    def update_data(self, summary: Dict):
        self.size_text.value = f"{summary['w_real']:.3f} × {summary['h_real']:.3f} m"
        self.res_text.value = f"{summary['res_w']} × {summary['res_h']}"
        self.refresh_text.value = f"{summary['refresh_rate_hz']} Hz"
        self.module_text.value = f"{summary['n_total']} cái"
        self.power_text.value = f"{summary.get('power_count', 0)} cái"
        self.card_text.value = f"{summary.get('receiving_card_count', 0)} cái"
        self.area_text.value = f"{summary.get('area_m2', 0):.2f} m²"
        self.processor_text.value = (
            f"{summary.get('power_kw', 0):.2f} kW tối đa"
            f" • {summary.get('processor_name', '-')}"
        )
        self.badge.visible = summary.get("deviation_pct", 0) > 5
