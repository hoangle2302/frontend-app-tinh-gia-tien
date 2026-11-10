import asyncio
import threading
import time
from typing import Any, Callable, Optional

import flet as ft


class BrandLoadingView(ft.Container):
    """Màn hình tải thương hiệu TOÀN TRUNG với hiệu ứng chuyển động mượt mà,

    hiển thị logo phát sáng, thanh tiến trình gradient và các trạng thái nạp hệ thống.
    """

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
        self.pipeline_result: Optional[Any] = None
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
            color="#94A3B8",
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
                        color="#F8FAFC",
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
            color="#E2E8F0",
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
            color="#00B8E8",
            bgcolor="#1E293B",
            border_radius=4,
            bar_height=6,
        )

        self.status_icon = ft.Icon(
            ft.Icons.MEMORY_ROUNDED,
            size=15,
            color="#00B8E8",
        )

        self.status_text = ft.Text(
            "Khởi tạo tài nguyên hệ thống...",
            size=11,
            color="#94A3B8",
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

    def start(self):
        """Kích hoạt chuỗi chuyển động và cập nhật tiến trình."""
        threading.Thread(target=self._run_loading_sequence, daemon=True).start()

    def _sync_erp_background(self):
        """Chạy đồng bộ API FastBusiness trên luồng phụ biệt lập, không block UI."""
        try:
            from api.services import FastBusinessService

            api_service = FastBusinessService()
            self.pipeline_result = api_service.post_login_query_pipeline(
                db_manager=self.db_manager,
                username=self.username,
            )
        except Exception:
            pass

    def _run_loading_sequence(self):
        # 1. Hiệu ứng xuất hiện mượt mà của Logo
        time.sleep(0.05)
        self.card.opacity = 1.0
        self.card.scale = 1.0
        self.logo_badge.scale = 1.06
        self._safe_update(self.card, self.logo_badge)

        time.sleep(0.2)
        self.logo_badge.scale = 1.0
        self._safe_update(self.logo_badge)

        # Kích hoạt worker ngầm tải ERP ngay từ đầu, hoàn toàn tách rời UI Thread
        threading.Thread(target=self._sync_erp_background, daemon=True).start()

        # 2. Cập nhật tiến trình nạp ngầm
        stages = [0.25, 0.60, 0.85, 1.00]
        current_progress = 0.0
        for target_pct in stages:
            while current_progress < target_pct:
                current_progress = min(target_pct, round(current_progress + 0.05, 2))
                self.progress_bar.value = current_progress
                self.percent_text.value = f"{int(current_progress * 100)}%"
                time.sleep(0.02)
            time.sleep(0.05)

        # 3. Hiệu ứng thở nhẹ của logo khi hoàn tất
        self.logo_badge.scale = 1.04
        self._safe_update(self.logo_badge)
        time.sleep(0.12)

        # 4. Hiệu ứng mờ dần chuyển cảnh (Fade out)
        self.card.opacity = 0.0
        self.card.scale = 1.05
        self._safe_update(self.card)

        time.sleep(0.15)

        # 5. Gọi hàm hoàn tất để mở giao diện chính thông qua Dispatcher của Main Thread
        if self.on_complete:
            loop = getattr(self._app_page, "loop", None)
            if isinstance(loop, asyncio.AbstractEventLoop) and loop.is_running():
                loop.call_soon_threadsafe(self.on_complete)
            else:
                self.on_complete()

    def _safe_update(self, *controls):
        try:
            loop = getattr(self._app_page, "loop", None)
            if isinstance(loop, asyncio.AbstractEventLoop) and loop.is_running():
                if controls:
                    loop.call_soon_threadsafe(self._app_page.update, *controls)
                else:
                    loop.call_soon_threadsafe(self._app_page.update)
            else:
                if controls:
                    self._app_page.update(*controls)
                else:
                    self._app_page.update()
        except Exception:
            pass

