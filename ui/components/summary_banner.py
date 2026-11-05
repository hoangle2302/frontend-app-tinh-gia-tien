from typing import Dict

import flet as ft


class SummaryBanner(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = 10
        self.border_radius = 12
        self.bgcolor = ft.Colors.WHITE
        self.border = ft.Border.all(1, ft.Colors.BLUE_GREY_100)

        self.size_text = ft.Text("-", size=16, weight=ft.FontWeight.BOLD)
        self.res_text = ft.Text("-", size=16, weight=ft.FontWeight.BOLD)
        self.refresh_text = ft.Text("-", size=16, weight=ft.FontWeight.BOLD)
        self.module_text = ft.Text("-", size=16, weight=ft.FontWeight.BOLD)
        self.badge = ft.Container(
            content=ft.Text("Lệch kích thước > 5%", color=ft.Colors.WHITE, size=12),
            padding=ft.Padding(10, 6, 10, 6),
            border_radius=999,
            bgcolor=ft.Colors.ORANGE,
            visible=False,
        )
        self.badge.content.value = "Lệch kích thước > 5%"

        self.content = ft.Column(
            spacing=8,
            controls=[
                ft.Text("Tổng quan màn hình", size=18, weight=ft.FontWeight.BOLD),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        self._metric_card("Kích thước", self.size_text, ft.Colors.BLUE_50),
                        self._metric_card("Độ phân giải", self.res_text, ft.Colors.TEAL_50),
                        self._metric_card("Tần số quét", self.refresh_text, ft.Colors.INDIGO_50),
                        self._metric_card("Số module", self.module_text, ft.Colors.ORANGE_50),
                    ],
                ),
                self.badge,
            ],
        )

    @staticmethod
    def _metric_card(label: str, value: ft.Text, color: str) -> ft.Container:
        return ft.Container(
            width=125,
            padding=8,
            border_radius=10,
            bgcolor=color,
            content=ft.Column(
                spacing=3,
                controls=[ft.Text(label, size=11, color=ft.Colors.BLUE_GREY_700), value],
            ),
        )

    def update_data(self, summary: Dict):
        self.size_text.value = f"{summary['w_real']:.3f} × {summary['h_real']:.3f} m"
        self.res_text.value = f"{summary['res_w']} × {summary['res_h']}"
        self.refresh_text.value = f"{summary['refresh_rate_hz']} Hz"
        self.module_text.value = f"{summary['n_total']} cái"
        self.badge.visible = summary.get("deviation_pct", 0) > 5
