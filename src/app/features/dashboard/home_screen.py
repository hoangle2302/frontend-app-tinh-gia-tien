# src/app/features/dashboard/home_screen.py
"""Mobile-only Home cho Flet 1.x.

Dùng chung dữ liệu và callback do tầng đăng nhập/backend cung cấp.
Không tự xác thực hoặc đổi mật khẩu ở client.
"""

from collections.abc import Awaitable, Callable
import inspect

import flet as ft
import flet.canvas as cv

from app.core.assets import AppAssets


PRIMARY = "#004A98"
ACCENT = "#00B8E8"

OnLogout = Callable[[], None | Awaitable[None]]
# Backend xác nhận thành công bằng True; False là thất bại.
OnChangePassword = Callable[[str, str], bool | Awaitable[bool]]

# Thông số kích thước thanh Dock đã tinh chỉnh khoảng thở giữa Notch và Icon
BAR_HEIGHT = 92
BAR_RADIUS = 32
DOCK_TOP = 6
DOCK_BOTTOM = 2
DOCK_HEIGHT = BAR_HEIGHT + DOCK_TOP + DOCK_BOTTOM  # 100 px
DOCK_MARGIN_X = 12

# Kích thước vết lõm (Notch): giảm độ sâu xuống 10.5px để cách xa đỉnh icon hơn
NOTCH_WIDTH = 46.0
NOTCH_DEPTH = 12.5

DOCK_ANIMATION_MS = 320
DOCK_CURVE = ft.AnimationCurve.EASE_IN_OUT_CUBIC

# Bảng màu trích xuất trực tiếp từ ảnh mẫu
DOCK_GRADIENT_START = "#56CCF2"
DOCK_GRADIENT_END = "#188BEF"
DOCK_IDLE_COLOR = "#9CE3FF"
DOCK_ACTIVE_COLOR = "#FFFFFF"


def show_home(
    page: ft.Page,
    *,
    username: str,
    on_logout: OnLogout,
    on_change_password: OnChangePassword | None = None,
) -> None:
    """Hiển thị Home dành riêng cho mobile sau khi đăng nhập thành công.

    on_change_password là callback gọi API; nếu chưa truyền thì không cho
    phép gửi yêu cầu đổi mật khẩu, tránh báo thành công giả.
    """
    page.title = "TOÀN TRUNG | Trang chủ"
    page.padding = 0
    section = 0
    root = ft.Column(expand=True, spacing=0)
    # Các control được giữ nguyên khi đổi tab để animation hoạt động.
    dock_refs: dict[str, object] = {}
    content_holder: ft.Container | None = None

    dock_items = [
        ("Trang chủ", ft.Icons.HOME_OUTLINED),
        ("Tính giá", ft.Icons.CALCULATE_OUTLINED),
        ("Cài đặt", ft.Icons.SETTINGS_OUTLINED),
    ]

    def palette() -> dict[str, str]:
        if page.theme_mode == ft.ThemeMode.DARK:
            return {
                "bg": "#091322", "surface": "#111827", "card": "#152238",
                "text": "#F8FAFC", "secondary": "#94A3B8", "line": "#27364B",
            }
        return {
            "bg": "#F5F8FC", "surface": "#FFFFFF", "card": "#FFFFFF",
            "text": "#0F172A", "secondary": "#64748B", "line": "#E2E8F0",
        }

    def stat_card(
        label: str, value: str, icon: str, color: str, p: dict[str, str]
    ) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[
                        ft.Text(label, size=13, color=p["secondary"], expand=True),
                        ft.Icon(icon, size=20, color=color),
                    ]),
                    ft.Text(value, size=26, weight=ft.FontWeight.BOLD, color=p["text"]),
                    ft.Text("Dữ liệu minh họa", size=11, color=p["secondary"]),
                ],
                spacing=10,
            ),
            bgcolor=p["card"],
            border=ft.Border.all(1, p["line"]),
            border_radius=16,
            padding=18,
            expand=True,
        )

    def overview(p: dict[str, str]) -> ft.Control:
        cards = [
            stat_card("Đơn hàng", "128", ft.Icons.SHOPPING_BAG_OUTLINED, PRIMARY, p),
            stat_card("Sản phẩm", "245", ft.Icons.INVENTORY_2_OUTLINED, ACCENT, p),
            stat_card("Khách hàng", "64", ft.Icons.PEOPLE_OUTLINE, "#16A34A", p),
            stat_card("Doanh thu", "—", ft.Icons.INSIGHTS, "#F59E0B", p),
        ]
        return ft.Column(
            controls=[
                ft.Text("Tổng quan", size=25, weight=ft.FontWeight.BOLD, color=p["text"]),
                ft.Text(f"Xin chào, {username}! Chào mừng quay lại.", color=p["secondary"]),
                ft.Column(
                    controls=[
                        ft.Row(controls=cards[:2], spacing=10),
                        ft.Row(controls=cards[2:], spacing=10),
                    ],
                    spacing=10,
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(controls=[
                                ft.Icon(ft.Icons.TIPS_AND_UPDATES_OUTLINED, color=ACCENT),
                                ft.Text(
                                    "Bắt đầu sử dụng", size=17,
                                    weight=ft.FontWeight.W_600, color=p["text"],
                                ),
                            ]),
                            ft.Text(
                                "Đây là giao diện trang chủ mẫu. Bạn có thể kết nối API FastAPI "
                                "để tải dữ liệu thật, thêm biểu đồ, quản lý sản phẩm và người dùng.",
                                color=p["secondary"],
                            ),
                        ],
                        spacing=12,
                    ),
                    padding=20,
                    border_radius=16,
                    bgcolor=p["card"],
                    border=ft.Border.all(1, p["line"]),
                ),
            ],
            spacing=18,
        )

    def placeholder(title: str, icon: str, p: dict[str, str]) -> ft.Control:
        return ft.Column(
            controls=[
                ft.Text(title, size=25, weight=ft.FontWeight.BOLD, color=p["text"]),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(icon, size=42, color=ACCENT),
                            ft.Text(
                                f"Trang {title} đã sẵn sàng để phát triển",
                                color=p["text"], text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Hãy bổ sung screen và repository tương ứng khi kết nối API.",
                                color=p["secondary"], text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        spacing=14,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=35,
                    border_radius=16,
                    bgcolor=p["card"],
                    border=ft.Border.all(1, p["line"]),
                    alignment=ft.Alignment.CENTER,
                ),
            ],
            spacing=16,
        )

    def screen_content(p: dict[str, str]) -> ft.Control:
        if section == 0:
            return overview(p)
        if section == 1:
            return placeholder("Tính giá", ft.Icons.CALCULATE_OUTLINED, p)
        return placeholder("Cài đặt", ft.Icons.SETTINGS_OUTLINED, p)

    def build_notch_shapes(bg_color: str) -> list[cv.Shape]:
        """Vẽ vết lõm mượt bằng 2 đường cong Cubic Bézier đối xứng."""
        w = NOTCH_WIDTH
        d = NOTCH_DEPTH
        return [
            cv.Path(
                elements=[
                    cv.Path.MoveTo(0, -0.5),
                    cv.Path.LineTo(w, -0.5),
                    cv.Path.LineTo(w, 0),
                    cv.Path.CubicTo(
                        w * 0.72, 0,
                        w * 0.64, d,
                        w * 0.50, d,
                    ),
                    cv.Path.CubicTo(
                        w * 0.36, d,
                        w * 0.28, 0,
                        0, 0,
                    ),
                    cv.Path.Close(),
                ],
                paint=ft.Paint(
                    color=bg_color,
                    style=ft.PaintingStyle.FILL,
                    anti_alias=True,
                ),
            )
        ]

    def build_wave_shapes(width: float, height: float) -> list[cv.Shape]:
        """Tái tạo 2 lớp sóng uốn lượn bên trong nền thanh bar từ ảnh gốc."""
        w = max(width, 320.0)
        h = float(height)
        return [
            # Lớp sóng chéo góc dưới bên trái
            cv.Path(
                elements=[
                    cv.Path.MoveTo(0, h * 0.22),
                    cv.Path.CubicTo(
                        w * 0.18, h * 0.28,
                        w * 0.28, h * 0.62,
                        w * 0.12, h,
                    ),
                    cv.Path.LineTo(0, h),
                    cv.Path.Close(),
                ],
                paint=ft.Paint(
                    color="#18FFFFFF",
                    style=ft.PaintingStyle.FILL,
                    anti_alias=True,
                ),
            ),
            # Lớp sóng chính vồng từ đáy trái qua tâm sang đáy phải
            cv.Path(
                elements=[
                    cv.Path.MoveTo(w * 0.04, h),
                    cv.Path.CubicTo(
                        w * 0.22, h * 0.20,
                        w * 0.55, h * 0.22,
                        w * 0.94, h,
                    ),
                    cv.Path.Close(),
                ],
                paint=ft.Paint(
                    color="#16FFFFFF",
                    style=ft.PaintingStyle.FILL,
                    anti_alias=True,
                ),
            ),
        ]

    def navigate_to(index: int) -> None:
        nonlocal section
        if index not in range(len(dock_items)) or index == section:
            return
        section = index
        p = palette()
        if content_holder is not None:
            content_holder.content = screen_content(p)

        notch_runner = dock_refs.get("notch_runner")
        if isinstance(notch_runner, ft.Container):
            notch_runner.offset = ft.Offset(float(index), 0)

        for i, (
            icon_stage,
            active_ico,
            idle_ico,
            label_stage,
            active_label,
            idle_label,
        ) in enumerate(dock_refs.get("items", [])):
            selected = i == section
            icon_stage.scale = 1.0 if selected else 0.72
            icon_stage.offset = ft.Offset(0, 0.02 if selected else 0)
            active_ico.opacity = 1.0 if selected else 0.0
            idle_ico.opacity = 0.0 if selected else 1.0
            label_stage.offset = ft.Offset(0, 0.08 if selected else 0)
            active_label.opacity = 1.0 if selected else 0.0
            idle_label.opacity = 0.0 if selected else 1.0
        page.update()

    async def logout(e) -> None:
        result = on_logout()
        if inspect.isawaitable(result):
            await result

    def change_theme(e) -> None:
        page.theme_mode = (
            ft.ThemeMode.LIGHT
            if page.theme_mode == ft.ThemeMode.DARK
            else ft.ThemeMode.DARK
        )
        render()

    def open_change_password(e) -> None:
        p = palette()
        if on_change_password is None:
            page.show_dialog(ft.AlertDialog(
                title=ft.Text("Đổi mật khẩu"),
                content=ft.Text(
                    "Chưa kết nối chức năng đổi mật khẩu với máy chủ. "
                    "Cần cung cấp on_change_password để thực hiện xác thực và cập nhật mật khẩu."
                ),
                actions=[
                    ft.TextButton(content="Đóng", on_click=lambda _: page.pop_dialog()),
                ],
            ))
            return

        old_password = ft.TextField(
            label="Mật khẩu hiện tại", password=True, can_reveal_password=True,
        )
        new_password = ft.TextField(
            label="Mật khẩu mới", password=True, can_reveal_password=True,
        )
        confirm_password = ft.TextField(
            label="Xác nhận mật khẩu mới", password=True, can_reveal_password=True,
        )
        message = ft.Text("", size=12, color="#DC2626")
        save_button = ft.Button(content="Lưu thay đổi")

        async def save_password(e) -> None:
            old = old_password.value or ""
            new = new_password.value or ""
            confirm = confirm_password.value or ""
            if not old or not new or not confirm:
                message.value = "Vui lòng điền đầy đủ thông tin."
                page.update()
                return
            if new != confirm:
                message.value = "Xác nhận mật khẩu không khớp."
                page.update()
                return
            if old == new:
                message.value = "Mật khẩu mới phải khác mật khẩu hiện tại."
                page.update()
                return

            save_button.disabled = True
            message.value = "Đang xử lý yêu cầu..."
            message.color = p["secondary"]
            page.update()
            try:
                result = on_change_password(old, new)
                success = await result if inspect.isawaitable(result) else result
                if success is True:
                    old_password.value = ""
                    new_password.value = ""
                    confirm_password.value = ""
                    page.pop_dialog()
                    page.show_dialog(ft.AlertDialog(
                        title=ft.Text("Đổi mật khẩu"),
                        content=ft.Text("Mật khẩu đã được máy chủ xác nhận cập nhật."),
                        actions=[
                            ft.TextButton(
                                content="Đóng", on_click=lambda _: page.pop_dialog()
                            ),
                        ],
                    ))
                    return
                message.value = "Không thể đổi mật khẩu. Vui lòng kiểm tra và thử lại."
            except Exception:
                message.value = "Không kết nối được dịch vụ đổi mật khẩu. Vui lòng thử lại."
            finally:
                save_button.disabled = False
                message.color = "#DC2626"
                page.update()

        save_button.on_click = save_password
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Đổi mật khẩu"),
            content=ft.Column(
                controls=[old_password, new_password, confirm_password, message],
                spacing=12,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton(content="Hủy", on_click=lambda _: page.pop_dialog()),
                save_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.show_dialog(dialog)

    def render() -> None:
        nonlocal content_holder
        dark = page.theme_mode == ft.ThemeMode.DARK
        p = palette()
        page.bgcolor = p["bg"]
        logo_path = (
            AppAssets.Images.LOGO_DARK if dark else AppAssets.Images.LOGO_LIGHT
        )

        user_menu = ft.PopupMenuButton(
            tooltip="Tài khoản",
            content=ft.Container(
                content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE_OUTLINED, color=p["text"], size=27),
                padding=8,
                border_radius=24,
            ),
            menu_position=ft.PopupMenuPosition.UNDER,
            items=[
                ft.PopupMenuItem(
                    content="Đổi mật khẩu",
                    icon=ft.Icons.LOCK_OUTLINE,
                    on_click=open_change_password,
                ),
                ft.PopupMenuItem(),
                ft.PopupMenuItem(
                    content="Đăng xuất",
                    icon=ft.Icons.LOGOUT,
                    on_click=logout,
                ),
            ],
        )
        topbar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Image(src=logo_path, width=135, height=36, fit=ft.BoxFit.CONTAIN),
                            ft.Text(
                                "TRANG CHỦ", size=12,
                                weight=ft.FontWeight.BOLD,
                                color=p["secondary"],
                            ),
                        ],
                        spacing=10,
                        tight=True,
                    ),
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=(
                                    ft.Icons.LIGHT_MODE if dark
                                    else ft.Icons.DARK_MODE_OUTLINED
                                ),
                                icon_color=p["text"],
                                tooltip="Đổi chế độ sáng/tối",
                                on_click=change_theme,
                            ),
                            user_menu,
                        ],
                        spacing=0,
                        tight=True,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=p["surface"],
            padding=ft.Padding(left=16, top=10, right=10, bottom=10),
            border=ft.Border.only(bottom=ft.BorderSide(1, p["line"])),
        )

        content_holder = ft.Container(
            content=screen_content(p), padding=16,
        )
        body = ft.Column(
            controls=[
                topbar,
                ft.Column(
                    controls=[content_holder],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

        anim_opacity = ft.Animation(220, ft.AnimationCurve.EASE_IN_OUT)
        anim_transform = ft.Animation(DOCK_ANIMATION_MS, DOCK_CURVE)
        item_refs = []
        item_controls = []

        for i, (title, glyph) in enumerate(dock_items):
            selected = i == section
            active_ico = ft.Container(
                content=ft.Icon(glyph, size=34, color=DOCK_ACTIVE_COLOR),
                alignment=ft.Alignment.CENTER,
                opacity=1.0 if selected else 0.0,
                animate_opacity=anim_opacity,
            )
            idle_ico = ft.Container(
                content=ft.Icon(glyph, size=34, color=DOCK_IDLE_COLOR),
                alignment=ft.Alignment.CENTER,
                opacity=0.0 if selected else 1.0,
                animate_opacity=anim_opacity,
            )
            active_label = ft.Container(
                content=ft.Text(
                    title,
                    size=13.5,
                    weight=ft.FontWeight.W_600,
                    color=DOCK_ACTIVE_COLOR,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=1,
                ),
                opacity=1.0 if selected else 0.0,
                alignment=ft.Alignment.CENTER,
                animate_opacity=anim_opacity,
            )
            idle_label = ft.Container(
                content=ft.Text(
                    title,
                    size=11.5,
                    weight=ft.FontWeight.W_500,
                    color=DOCK_IDLE_COLOR,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=1,
                ),
                opacity=0.0 if selected else 1.0,
                alignment=ft.Alignment.CENTER,
                animate_opacity=anim_opacity,
            )
            icon_stage = ft.Container(
                content=ft.Stack(
                    width=44,
                    height=36,
                    alignment=ft.Alignment.CENTER,
                    controls=[idle_ico, active_ico],
                ),
                width=44,
                height=36,
                alignment=ft.Alignment.CENTER,
                scale=1.0 if selected else 0.72,
                offset=ft.Offset(0, 0.02 if selected else 0),
                animate_scale=anim_transform,
                animate_offset=anim_transform,
            )
            label_stage = ft.Container(
                content=ft.Stack(
                    width=92,
                    height=20,
                    alignment=ft.Alignment.CENTER,
                    controls=[idle_label, active_label],
                ),
                width=92,
                height=20,
                alignment=ft.Alignment.CENTER,
                offset=ft.Offset(0, 0.08 if selected else 0),
                animate_offset=anim_transform,
            )
            tab = ft.Container(
                content=ft.Column(
                    controls=[icon_stage, label_stage],
                    spacing=2,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
                expand=1,
                alignment=ft.Alignment.CENTER,
                on_click=lambda e, n=i: navigate_to(n),
                tooltip=title,
            )
            item_controls.append(tab)
            item_refs.append(
                (icon_stage, active_ico, idle_ico, label_stage, active_label, idle_label)
            )

        wave_canvas = cv.Canvas(
            width=float("inf"),
            height=BAR_HEIGHT,
            shapes=build_wave_shapes(360.0, BAR_HEIGHT),
        )

        notch_runner = ft.Container(
            expand=1,
            height=NOTCH_DEPTH,
            alignment=ft.Alignment.TOP_CENTER,
            offset=ft.Offset(float(section), 0),
            animate_offset=ft.Animation(DOCK_ANIMATION_MS, DOCK_CURVE),
            ignore_interactions=True,
            content=cv.Canvas(
                width=NOTCH_WIDTH,
                height=NOTCH_DEPTH,
                shapes=build_notch_shapes(p["bg"]),
            ),
        )

        notch_row = ft.Row(
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                notch_runner,
                *[ft.Container(expand=1) for _ in range(len(dock_items) - 1)],
            ],
        )

        base = ft.Container(
            top=DOCK_TOP,
            left=0,
            right=0,
            bottom=DOCK_BOTTOM,
            border_radius=BAR_RADIUS,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=[DOCK_GRADIENT_START, DOCK_GRADIENT_END],
            ),
            shadow=ft.BoxShadow(
                blur_radius=18,
                spread_radius=-4,
                offset=ft.Offset(0, 10),
                color="#33188BEF",
            ),
            content=ft.Stack(
                controls=[
                    wave_canvas,
                    ft.Container(
                        top=0,
                        left=0,
                        right=0,
                        height=NOTCH_DEPTH,
                        ignore_interactions=True,
                        content=notch_row,
                    ),
                ],
            ),
        )

        dock_stack = ft.Stack(
            height=DOCK_HEIGHT,
            clip_behavior=ft.ClipBehavior.NONE,
            controls=[
                base,
                # Thêm padding top=6 để đẩy cụm icon và chữ lùi xuống xa mũi nhọn hơn
                ft.Container(
                    top=DOCK_TOP,
                    left=0,
                    right=0,
                    bottom=DOCK_BOTTOM,
                    padding=ft.Padding(left=0, top=6, right=0, bottom=0),
                    content=ft.Row(
                        controls=item_controls,
                        spacing=0,
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            ],
        )
        dock = ft.Container(
            content=dock_stack,
            height=DOCK_HEIGHT,
            margin=ft.Margin(left=DOCK_MARGIN_X, top=0, right=DOCK_MARGIN_X, bottom=9),
        )
        dock_refs["notch_runner"] = notch_runner
        dock_refs["items"] = item_refs
        root.controls = [body, dock]
        page.update()

    page.clean()
    page.add(ft.SafeArea(content=root, expand=True))
    render()