import asyncio
import threading
import time
from typing import Any, Callable, Optional

import flet as ft


from ui.theme.tokens import UIColors
from ui.features.auth.loading_workflow import LoadingWorkflowMixin

class BrandLoadingView(LoadingWorkflowMixin, ft.Container):
    LOGO_SRC = "logo_white_brand.png"

    FALLBACK_LOGO = "full_logo2.png"

    def __init__(
        self,
        username: str,
        on_complete: Callable,
        page: ft.Page,
        db_manager: Optional[Any] = None,
    ):
        super().__init__()
        self._app_page = page
        self.username = username or "Người dùng"
        self.on_complete = on_complete
        self.db_manager = db_manager
        self.expand = True

        # Nền màu xanh thương hiệu Toàn Trung đồng nhất với logo
        self.bgcolor = "#0B4CA3"
        self.gradient = None
        self.alignment = ft.Alignment(0, 0)

        # 1. Logo thương hiệu thuần túy, không có khung viền hộp bao quanh
        self.logo_img = ft.Image(
            src=self.LOGO_SRC,
            width=260,
            fit=ft.BoxFit.CONTAIN,
        )

        self.logo_badge = ft.Container(
            content=self.logo_img,
            alignment=ft.Alignment(0, 0),
            scale=1.0,
            animate_scale=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        )

        # 2. Các thuộc tính mô tả & trạng thái hệ thống (lưu trữ phục vụ mô hình & kiểm thử)
        self.brand_title = ft.Text(
            "TOÀN TRUNG",
            size=23,
            weight=ft.FontWeight.W_800,
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        )

        self.brand_subtitle = ft.Text(
            "LED TECHNOLOGY & SOLUTIONS",
            size=10,
            weight=ft.FontWeight.BOLD,
            color="#38BDF8",
            text_align=ft.TextAlign.CENTER,
        )

        self.app_desc = ft.Text(
            "Hệ thống Báo giá Màn hình LED Chuyên nghiệp",
            size=12,
            color=UIColors.TEXT_SUBTLE,
            text_align=ft.TextAlign.CENTER,
        )

        self.user_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.VERIFIED_USER_ROUNDED,
                        size=14,
                        color="#34D399",
                    ),
                    ft.Text(
                        f"Chào mừng: {self.username}",
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=UIColors.SURFACE_SUBTLE,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
            ),
            bgcolor="#142847",
            border=ft.Border.all(1, "#38BDF833"),
            border_radius=18,
            padding=ft.Padding(14, 6, 14, 6),
        )

        self.step_label = ft.Text(
            "Đang chuẩn bị...",
            size=12,
            weight=ft.FontWeight.W_600,
            color=UIColors.BORDER,
            expand=True,
        )

        self.percent_text = ft.Text(
            "0%",
            size=12,
            weight=ft.FontWeight.BOLD,
            color="#38BDF8",
        )

        self.progress_bar = ft.ProgressBar(
            value=0.0,
            color=UIColors.SECONDARY,
            bgcolor="#1E293B",
            border_radius=4,
            bar_height=6,
        )

        self.status_icon = ft.Icon(
            ft.Icons.MEMORY_ROUNDED,
            size=15,
            color=UIColors.SECONDARY,
        )

        self.status_text = ft.Text(
            "Khởi tạo tài nguyên hệ thống...",
            size=11,
            color=UIColors.TEXT_SUBTLE,
            expand=True,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        self.progress_section = ft.Column(
            controls=[
                ft.Row(
                    controls=[self.step_label, self.percent_text],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                self.progress_bar,
                ft.Row(
                    controls=[self.status_icon, self.status_text],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=8,
            tight=True,
        )

        # 3. Khung hiển thị tối giản: Chỉ hiển thị Logo trên nền Background
        self.card = ft.Container(
            content=self.logo_badge,
            alignment=ft.Alignment(0, 0),
            opacity=0.0,
            scale=0.92,
            animate_opacity=ft.Animation(450, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(450, ft.AnimationCurve.EASE_OUT_BACK),
        )

        self.content = self.card
