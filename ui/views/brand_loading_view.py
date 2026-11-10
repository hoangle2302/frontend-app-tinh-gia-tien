import threading
import time
from typing import Any, Callable, Optional

import flet as ft


class BrandLoadingView(ft.Container):
    """Màn hình tải thương hiệu TOÀN TRUNG với hiệu ứng chuyển động mượt mà,

    hiển thị logo phát sáng, thanh tiến trình gradient và các trạng thái nạp hệ thống.
    """

    LOGO_SRC = "full_logo2.png"
    FALLBACK_LOGO = "logo.png"

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

        # Nền gradient công nghệ hiện đại tông màu xanh thương hiệu Toàn Trung
        self.gradient = ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=["#020A17", "#051A38", "#082F6A", "#011024"],
        )
        self.alignment = ft.Alignment(0, 0)

        # 1. Logo thương hiệu với viền phát sáng và hiệu ứng phóng to / thu nhỏ
        self.logo_img = ft.Image(
            src=self.LOGO_SRC,
            width=100,
            height=100,
            fit=ft.BoxFit.CONTAIN,
        )

        self.logo_badge = ft.Container(
            content=self.logo_img,
            width=116,
            height=116,
            border_radius=24,
            bgcolor="#07162C",
            border=ft.Border.all(1.5, "#38BDF866"),
            alignment=ft.Alignment(0, 0),
            shadow=[
                ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=25,
                    color="#6600B8E8",
                    offset=ft.Offset(0, 6),
                ),
                ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=40,
                    color="#44004A98",
                    offset=ft.Offset(0, 12),
                ),
            ],
            scale=1.0,
            animate_scale=ft.Animation(600, ft.AnimationCurve.EASE_IN_OUT),
        )

        # 2. Tiêu đề thương hiệu và khẩu hiệu
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

        # 3. Huy hiệu chào mừng tài khoản đăng nhập
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

        # 4. Thanh tiến trình và thông báo tiến độ
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

        # 5. Khung thẻ chính giữa màn hình (Card) với hiệu ứng trong suốt (Glassmorphism)
        self.card = ft.Container(
            width=360,
            padding=ft.Padding(left=24, top=32, right=24, bottom=28),
            bgcolor="#101D33EE",
            border=ft.Border.all(1.2, "#38BDF844"),
            border_radius=24,
            shadow=[
                ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=30,
                    color="#4000B8E8",
                    offset=ft.Offset(0, 8),
                ),
                ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=50,
                    color="#35002F6C",
                    offset=ft.Offset(0, 16),
                ),
            ],
            opacity=0.0,
            scale=0.92,
            offset=ft.Offset(0, 0.04),
            animate_opacity=ft.Animation(450, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(450, ft.AnimationCurve.EASE_OUT_BACK),
            animate_offset=ft.Animation(450, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                controls=[
                    self.logo_badge,
                    ft.Container(height=4),
                    self.brand_title,
                    self.brand_subtitle,
                    self.app_desc,
                    ft.Container(height=4),
                    self.user_badge,
                    ft.Container(height=10),
                    self.progress_section,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                tight=True,
            ),
        )

        self.content = self.card

    def start(self):
        """Kích hoạt chuỗi chuyển động và cập nhật tiến trình."""
        threading.Thread(target=self._run_loading_sequence, daemon=True).start()

    def _run_loading_sequence(self):
        # 1. Hiệu ứng xuất hiện mượt mà của thẻ trung tâm
        time.sleep(0.05)
        self.card.opacity = 1.0
        self.card.scale = 1.0
        self.card.offset = ft.Offset(0, 0)
        self.logo_badge.scale = 1.04
        self._safe_update()

        time.sleep(0.2)
        self.logo_badge.scale = 1.0
        self._safe_update()

        # 2. Chuỗi các giai đoạn nạp hệ thống thực tế
        stages = [
            (
                0.25,
                "Khởi tạo hệ thống",
                "Thiết lập phiên làm việc FastBusiness ERP...",
                ft.Icons.MEMORY_ROUNDED,
            ),
            (
                0.60,
                "Đồng bộ danh mục & LookupFields",
                "Quét danh mục Module LED, bộ điều khiển & môi trường vào Database...",
                ft.Icons.WIDGETS_ROUNDED,
            ),
            (
                0.85,
                "Đồng bộ lưới BT1 & Quyền hạn",
                "Nạp cấu hình lưới chứng từ BT1, công thức tính & bài đăng...",
                ft.Icons.CALCULATE_ROUNDED,
            ),
            (
                1.00,
                "Sẵn sàng",
                f"Khởi chạy không gian làm việc cho {self.username}...",
                ft.Icons.CHECK_CIRCLE_ROUNDED,
            ),
        ]

        current_progress = 0.0
        for target_pct, step_title, status_msg, icon_name in stages:
            self.step_label.value = step_title
            self.status_text.value = status_msg
            self.status_icon.name = icon_name

            # Thực hiện thuật toán truy vấn toàn bộ API đã scan sau khi login
            if target_pct == 0.60:
                try:
                    from api.services import FastBusinessService

                    api_service = FastBusinessService()
                    self.pipeline_result = api_service.post_login_query_pipeline(
                        db_manager=self.db_manager,
                        username=self.username,
                    )
                except Exception:
                    pass

            while current_progress < target_pct:
                current_progress = min(target_pct, round(current_progress + 0.04, 2))
                self.progress_bar.value = current_progress
                self.percent_text.value = f"{int(current_progress * 100)}%"
                self._safe_update()
                time.sleep(0.025)

            time.sleep(0.12)

        # 3. Trạng thái hoàn tất thành công (100%)
        self.percent_text.color = "#10B981"
        self.step_label.color = "#10B981"
        self.status_icon.color = "#10B981"
        self.status_text.color = "#10B981"
        self.status_text.value = f"Đã sẵn sàng! Chào mừng {self.username}."
        self._safe_update()

        time.sleep(0.25)

        # 4. Hiệu ứng mờ dần chuyển cảnh (Fade out & Scale up exit)
        self.card.opacity = 0.0
        self.card.scale = 1.03
        self.card.offset = ft.Offset(0, -0.02)
        self._safe_update()

        time.sleep(0.3)

        # 5. Gọi hàm hoàn tất để mở giao diện chính
        if self.on_complete:
            self.on_complete()

    def _safe_update(self):
        try:
            self._app_page.update()
        except Exception:
            pass

