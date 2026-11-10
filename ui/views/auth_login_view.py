import threading
import time
from typing import Any, Callable, Dict, List, Optional

import flet as ft

from api.constants import DEFAULT_LOGIN_DATABASE, DEFAULT_LOGIN_UNIT


class AuthLoginView(ft.Container):
    LOGO_LIGHT = "logo_light.png"
    LOGO_DARK = "logo_dark.png"
    BG_IMAGE_LIGHT = "bg_light.png"
    BG_IMAGE_DARK = "bg_dark.png"

    LOGO_WIDTH = 175
    LOGO_HEIGHT = 42

    BRAND_PRIMARY = "#004A98"
    BRAND_SECONDARY = "#00B8E8"

    THEME_PALETTE = {
        "light": {
            "page_bg": "#FAFCFE",
            "header_bg": "#FFFFFF",
            "card_bg": "#EBFFFFFF",
            "card_border": "#E2E8F0",
            "input_bg": "#F1F5F9",
            "input_border": "#CBD5E1",
            "text_primary": "#0F172A",
            "text_secondary": "#64748B",
            "divider": "#00B8E8",
            "theme_btn_bg": "#F1F5F9",
            "theme_btn_icon": "#334155",
        },
        "dark": {
            "page_bg": "#091322",
            "header_bg": "#111827",
            "card_bg": "#D9111827",
            "card_border": "#1E293B",
            "input_bg": "#1E293B",
            "input_border": "#334155",
            "text_primary": "#F8FAFC",
            "text_secondary": "#94A3B8",
            "divider": "#00B8E8",
            "theme_btn_bg": "#1E293B",
            "theme_btn_icon": "#FFFFFF",
        },
    }

    def __init__(self, page: ft.Page, on_login_success: Callable, on_toggle_theme: Callable):
        super().__init__()
        self._app_page = page
        self.on_login_success = on_login_success
        self.on_toggle_theme = on_toggle_theme
        self.expand = True
        self._is_submitting = False

        # Trạng thái kiểm tra tài khoản & đơn vị từ FastBusiness ERP
        self._user_exists: Optional[bool] = None
        self._last_checked_user: str = ""
        self._unit_lookup_timer: Optional[threading.Timer] = None

        is_dark = self._app_page.theme_mode == ft.ThemeMode.DARK
        palette = self.THEME_PALETTE["dark" if is_dark else "light"]

        # Header
        self.logo_img = ft.Image(
            src=self.LOGO_DARK if is_dark else self.LOGO_LIGHT,
            width=self.LOGO_WIDTH,
            height=self.LOGO_HEIGHT,
            fit=ft.BoxFit.CONTAIN,
        )

        self.theme_button = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE if is_dark else ft.Icons.DARK_MODE,
            icon_color=palette["theme_btn_icon"],
            bgcolor=palette["theme_btn_bg"],
            icon_size=20,
            tooltip="Chuyển sang Light Mode" if is_dark else "Chuyển sang Dark Mode",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            on_click=self.on_toggle_theme,
        )

        self.header = ft.Container(
            content=ft.Row(
                controls=[
                    self.logo_img,
                    self.theme_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=palette["header_bg"],
            padding=ft.Padding(left=20, top=14, right=20, bottom=14),
        )

        self.header_divider = ft.Divider(
            height=1,
            thickness=1,
            color=palette["divider"],
        )

        # Login Form Title
        self.title_text = ft.Text(
            "Đăng nhập hệ thống",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=palette["text_primary"],
            text_align=ft.TextAlign.CENTER,
        )

        # 1. Trường "Công ty" (Nạp từ /Main/Login.aspx/GetEntityData khi mới vào trang)
        self.company_dropdown = self._create_dropdown_field(
            label="Công ty",
            icon=ft.Icons.BUSINESS_ROUNDED,
            options=[
                ft.dropdown.Option(key=DEFAULT_LOGIN_DATABASE, text="01 - Công ty"),
            ],
            value=DEFAULT_LOGIN_DATABASE,
            on_select=self._on_company_changed,
            palette=palette,
        )

        # 2. Trường "Tên" (Khi nhập sẽ gọi /Main/Login.aspx/GetUnitData để nạp Đơn vị)
        self.username_input = self._create_input_field(
            label="Tên",
            icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
            autofocus=True,
            palette=palette,
        )
        self.username_input.on_change = self._on_username_change
        self.username_input.on_blur = self._on_username_blur
        self.username_input.on_submit = self._on_username_submit

        # 3. Trường "Đơn Vị" (Được nạp động từ GetUnitData theo Tên)
        self.unit_dropdown = self._create_dropdown_field(
            label="Đơn vị",
            icon=ft.Icons.ACCOUNT_TREE_OUTLINED,
            options=[
                ft.dropdown.Option(key=DEFAULT_LOGIN_UNIT, text=f"{DEFAULT_LOGIN_UNIT} - CÔNG TY"),
            ],
            value=DEFAULT_LOGIN_UNIT,
            on_select=self._on_unit_changed,
            palette=palette,
        )

        # 4. Trường "Mật khẩu"
        self.password_input = self._create_input_field(
            label="Mật khẩu",
            icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
            is_password=True,
            palette=palette,
        )
        self.password_input.on_submit = self._handle_login

        # Status Banner với chuyển động mượt mà
        self.status_icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
            size=18,
            color="#16A34A",
        )
        self.status_text = ft.Text(
            value="",
            size=13,
            weight=ft.FontWeight.W_500,
            expand=True,
        )
        self.status_banner = ft.Container(
            content=ft.Row(
                controls=[self.status_icon, self.status_text],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=14, top=12, right=14, bottom=12),
            border_radius=10,
            opacity=0.0,
            offset=ft.Offset(0, -0.1),
            animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            visible=False,
        )

        # Login Button với các trạng thái chuyển động
        self.login_btn_text = ft.Text(
            "Đăng nhập",
            size=16,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.WHITE,
        )
        self.login_btn_icon = ft.Icon(
            ft.Icons.ARROW_FORWARD_ROUNDED,
            color=ft.Colors.WHITE,
            size=19,
        )
        self.login_button_content = ft.Row(
            controls=[self.login_btn_text, self.login_btn_icon],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )
        self.login_button = ft.Container(
            content=self.login_button_content,
            height=52,
            border_radius=12,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=[self.BRAND_PRIMARY, self.BRAND_SECONDARY],
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=14,
                color="#400088CC",
                offset=ft.Offset(0, 6),
            ),
            ink=True,
            scale=1.0,
            animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            animate=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            on_click=self._handle_login,
            on_hover=self._on_button_hover,
        )

        self.login_form = ft.Column(
            controls=[
                ft.Column(
                    controls=[self.title_text],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=8),
                self.company_dropdown,
                self.username_input,
                self.unit_dropdown,
                self.password_input,
                self.status_banner,
                ft.Container(height=4),
                self.login_button,
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            tight=True,
        )

        self.form_card = ft.Container(
            content=self.login_form,
            bgcolor=palette["card_bg"],
            border=ft.Border.all(1, palette["card_border"]),
            border_radius=20,
            padding=ft.Padding(left=20, top=24, right=20, bottom=24),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=24,
                color="#66000000",
                offset=ft.Offset(0, 8),
            ),
            opacity=1.0,
            scale=1.0,
            offset=ft.Offset(0, 0),
            animate_opacity=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(350, ft.AnimationCurve.EASE_OUT_CUBIC),
            animate_offset=ft.Animation(350, ft.AnimationCurve.EASE_OUT_CUBIC),
        )

        self.footer_text = ft.Text(
            "© 2026 TOÀN TRUNG. All rights reserved.",
            size=12,
            color=palette["text_secondary"],
            text_align=ft.TextAlign.CENTER,
        )

        self.footer = ft.Container(
            content=self.footer_text,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding(
                left=0,
                top=12,
                right=0,
                bottom=20,
            ),
        )

        self.main_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(expand=True),
                    self.form_card,
                    ft.Container(expand=True),
                    self.footer,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            image=ft.DecorationImage(
                src=self.BG_IMAGE_DARK if is_dark else self.BG_IMAGE_LIGHT,
                fit=ft.BoxFit.COVER,
                alignment=ft.Alignment.BOTTOM_CENTER,
            ),
            padding=ft.Padding(
                left=20,
                top=20,
                right=20,
                bottom=12,
            ),
            expand=True,
        )

        self.content = ft.Column(
            controls=[
                self.header,
                self.header_divider,
                self.main_content,
            ],
            spacing=0,
            expand=True,
        )

        # Tự động gọi GetEntityData ngay khi vừa mở trang đăng nhập
        self.load_initial_entity_data()

    # --------------------------------------------------------------------------
    # Luồng gọi API GetEntityData & GetUnitData theo pattern FastBusiness ERP
    # --------------------------------------------------------------------------
    def load_initial_entity_data(self):
        """Gọi API /Main/Login.aspx/GetEntityData khi mới vào trang đăng nhập."""
        def _worker():
            try:
                from api.services import FastBusinessService

                service = FastBusinessService()
                entities = service.get_entity_data()
                if entities:
                    self._apply_entities_to_dropdown(entities)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_entities_to_dropdown(self, entities: List[Dict[str, str]]):
        options = []
        for ent in entities:
            code = ent.get("code", "")
            name = ent.get("name", "Công ty")
            db_val = ent.get("database", DEFAULT_LOGIN_DATABASE)
            label_text = f"{code} - {name}" if code else name
            options.append(ft.dropdown.Option(key=db_val, text=label_text))

        if options:
            self.company_dropdown.options = options
            current_val = self.company_dropdown.value
            if not any(opt.key == current_val for opt in options):
                self.company_dropdown.value = options[0].key
            self._safe_update()

    def _on_company_changed(self, e):
        self.company_dropdown.error_text = None
        username = (self.username_input.value or "").strip()
        if username:
            self._trigger_unit_lookup(username, immediate=True)
        else:
            self._safe_update()

    def _on_unit_changed(self, e):
        self.unit_dropdown.error_text = None
        self._safe_update()

    def _on_username_change(self, e):
        username = (self.username_input.value or "").strip()
        self.username_input.error = None
        if not username:
            self._user_exists = None
            self._last_checked_user = ""
            if self._unit_lookup_timer:
                self._unit_lookup_timer.cancel()
            self._safe_update()
            return

        # Debounce 420ms khi người dùng đang gõ Tên để tự động nạp Đơn vị
        self._trigger_unit_lookup(username, immediate=False)

    def _on_username_blur(self, e):
        username = (self.username_input.value or "").strip()
        if username and username != self._last_checked_user:
            self._trigger_unit_lookup(username, immediate=True)

    def _on_username_submit(self, e):
        username = (self.username_input.value or "").strip()
        if username:
            self._trigger_unit_lookup(username, immediate=True)
        try:
            self.password_input.focus()
        except Exception:
            pass

    def _trigger_unit_lookup(self, username: str, immediate: bool = False):
        if self._unit_lookup_timer:
            self._unit_lookup_timer.cancel()
            self._unit_lookup_timer = None

        if immediate:
            threading.Thread(
                target=self._lookup_unit_for_user,
                args=(username,),
                daemon=True,
            ).start()
        else:
            self._unit_lookup_timer = threading.Timer(
                0.42,
                self._lookup_unit_for_user,
                args=(username,),
            )
            self._unit_lookup_timer.daemon = True
            self._unit_lookup_timer.start()

    def _lookup_unit_for_user(self, username: str) -> bool:
        """Gọi /Main/Login.aspx/GetUnitData để kiểm tra user và lấy danh sách Đơn vị."""
        user_clean = (username or "").strip()
        if not user_clean:
            return False

        database = (self.company_dropdown.value or DEFAULT_LOGIN_DATABASE).strip()
        try:
            from api.services import FastBusinessService

            service = FastBusinessService()
            exists, units = service.get_unit_data(user_clean, database=database, allow_offline=False)
        except Exception:
            exists, units = False, []

        # Chỉ cập nhật UI nếu ô input vẫn đang mang giá trị user_clean
        current_input = (self.username_input.value or "").strip()
        if current_input and current_input != user_clean:
            return exists

        self._last_checked_user = user_clean
        self._user_exists = exists

        if exists and units:
            self.username_input.error = None
            self.unit_dropdown.error_text = None
            self.unit_dropdown.disabled = False
            self.unit_dropdown.options = [
                ft.dropdown.Option(
                    key=u["code"],
                    text=f"{u['code']} - {u['name']}" if u.get("name") else u["code"],
                )
                for u in units
            ]
            # Giữ nguyên đơn vị nếu hợp lệ, hoặc chọn mặc định đơn vị đầu tiên (VD: CTY)
            if not any(u["code"] == self.unit_dropdown.value for u in units):
                self.unit_dropdown.value = units[0]["code"]
            if self.status_banner.visible and self.status_icon.name == ft.Icons.ERROR_OUTLINE_ROUNDED:
                self._hide_status()
            else:
                self._safe_update()
            return True
        else:
            # Khi API trả về {"d": false} -> User không tồn tại
            self.unit_dropdown.options = []
            self.unit_dropdown.value = None
            self.username_input.error = f"Tài khoản '{user_clean}' không tồn tại"
            self._show_status(f"Tài khoản '{user_clean}' không tồn tại trên hệ thống!", is_error=True)
            return False

    # --------------------------------------------------------------------------
    # UI Helpers & Styling
    # --------------------------------------------------------------------------
    def _on_button_hover(self, e):
        if not self._is_submitting:
            self.login_button.scale = 1.02 if e.data == "true" else 1.0
            self._safe_update()

    def _make_input_border(self, color: str):
        return {
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(color=color, width=1),
            ),
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(color=self.BRAND_SECONDARY, width=2),
            ),
            ft.ControlState.ERROR: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(color="#DC2626", width=1.5),
            ),
        }

    def _create_dropdown_field(
        self,
        label: str,
        icon,
        options: list,
        value: Optional[str],
        on_select: Callable,
        palette: dict = None,
    ) -> ft.Dropdown:
        palette = palette or self.THEME_PALETTE["light"]
        return ft.Dropdown(
            label=label,
            leading_icon=icon,
            options=options,
            value=value,
            on_select=on_select,
            expanded_insets=0,
            filled=True,
            fill_color=palette["input_bg"],
            bgcolor=palette["input_bg"],
            border_radius=12,
            border_color=palette["input_border"],
            focused_border_color=self.BRAND_SECONDARY,
            focused_border_width=2,
            text_size=14,
            color=palette["text_primary"],
            label_style=ft.TextStyle(
                color=palette["text_secondary"],
                size=13,
            ),
            content_padding=ft.Padding(
                left=16, top=14, right=16, bottom=14
            ),
            menu_style=ft.MenuStyle(
                bgcolor=palette["header_bg"],
                elevation=6,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        )

    def _create_input_field(
        self,
        label: str,
        icon,
        is_password: bool = False,
        autofocus: bool = False,
        palette: dict = None,
    ) -> ft.TextField:
        palette = palette or self.THEME_PALETTE["light"]
        return ft.TextField(
            label=label,
            prefix_icon=icon,
            password=is_password,
            can_reveal_password=is_password,
            autofocus=autofocus,
            filled=True,
            bgcolor=palette["input_bg"],
            border=self._make_input_border(palette["input_border"]),
            text_size=14,
            color=palette["text_primary"],
            label_style=ft.TextStyle(
                color=palette["text_secondary"],
                size=13,
            ),
            hint_style=ft.TextStyle(
                color=palette["text_secondary"],
                size=13,
            ),
            content_padding=ft.Padding(
                left=16, top=16, right=16, bottom=16
            ),
        )

    def _show_status(self, message: str, is_error: bool = False):
        is_dark = self._app_page.theme_mode == ft.ThemeMode.DARK
        if is_error:
            self.status_icon.name = ft.Icons.ERROR_OUTLINE_ROUNDED
            self.status_icon.color = "#DC2626"
            self.status_text.color = "#DC2626"
            self.status_banner.bgcolor = "#3B1818" if is_dark else "#FEF2F2"
            self.status_banner.border = ft.Border.all(1, "#7F1D1D" if is_dark else "#FECACA")
        else:
            self.status_icon.name = ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED
            self.status_icon.color = "#16A34A"
            self.status_text.color = "#16A34A"
            self.status_banner.bgcolor = "#143321" if is_dark else "#F0FDF4"
            self.status_banner.border = ft.Border.all(1, "#166534" if is_dark else "#BBF7D0")

        self.status_text.value = message
        self.status_banner.visible = True
        self.status_banner.opacity = 1.0
        self.status_banner.offset = ft.Offset(0, 0)
        self._safe_update()

    def _hide_status(self):
        self.status_banner.opacity = 0.0
        self.status_banner.offset = ft.Offset(0, -0.1)
        self._safe_update()

    def _set_form_disabled(self, disabled: bool):
        self.company_dropdown.disabled = disabled
        self.username_input.disabled = disabled
        self.unit_dropdown.disabled = disabled
        self.password_input.disabled = disabled

    def _handle_login(self, e):
        if self._is_submitting:
            return

        if self._unit_lookup_timer:
            self._unit_lookup_timer.cancel()
            self._unit_lookup_timer = None

        database = (self.company_dropdown.value or "").strip()
        username = (self.username_input.value or "").strip()
        unit = (self.unit_dropdown.value or "").strip()
        password = self.password_input.value or ""

        self.company_dropdown.error_text = None
        self.username_input.error = None
        self.unit_dropdown.error_text = None
        self.password_input.error = None

        has_error = False

        if not database:
            self.company_dropdown.error_text = "Vui lòng chọn công ty"
            has_error = True

        if not username:
            self.username_input.error = "Vui lòng nhập tên đăng nhập"
            has_error = True
        elif self._last_checked_user == username and self._user_exists is False:
            self.username_input.error = f"Tài khoản '{username}' không tồn tại"
            has_error = True

        if not password:
            self.password_input.error = "Vui lòng nhập mật khẩu"
            has_error = True

        if has_error:
            self.login_button.scale = 0.97
            self._safe_update()

            def _reset_btn_scale():
                time.sleep(0.12)
                self.login_button.scale = 1.0
                self._safe_update()

            threading.Thread(target=_reset_btn_scale, daemon=True).start()
            err_banner = (
                f"Tài khoản '{username}' không tồn tại trên hệ thống!"
                if (username and self._user_exists is False)
                else "Vui lòng kiểm tra lại thông tin đăng nhập."
            )
            self._show_status(err_banner, is_error=True)
            return

        # Bắt đầu chuỗi hiệu ứng xác thực
        self._is_submitting = True
        self._set_form_disabled(True)

        # Trạng thái 1: Nút biến đổi thành vòng xoay đang xác thực
        self.login_button.scale = 0.98
        self.login_button_content.controls = [
            ft.ProgressRing(
                width=18,
                height=18,
                stroke_width=2.4,
                color=ft.Colors.WHITE,
            ),
            ft.Text(
                "Đang xác thực thông tin...",
                size=15,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.WHITE,
            ),
        ]
        self._show_status("Đang kiểm tra tài khoản & đơn vị hệ thống...", is_error=False)
        self._safe_update()

        def _proceed_login_animation():
            nonlocal unit
            try:
                from api.services import FastBusinessService

                api_service = FastBusinessService()

                # Bước 1: Kiểm tra Đơn vị (GetUnitData) nếu chưa kiểm tra cho user này
                if self._last_checked_user != username or not unit:
                    user_ok = self._lookup_unit_for_user(username)
                    if not user_ok:
                        self._is_submitting = False
                        self._set_form_disabled(False)
                        self.login_button_content.controls = [self.login_btn_text, self.login_btn_icon]
                        self.login_button.scale = 1.0
                        self._safe_update()
                        return
                    unit = (self.unit_dropdown.value or DEFAULT_LOGIN_UNIT).strip()

                # Bước 2: Gọi API Login (/Main/Login.aspx/Login) -> bắt buộc trả về {"d": true}
                success, user_info, err_msg = api_service.login(
                    username=username,
                    password=password,
                    database=database or DEFAULT_LOGIN_DATABASE,
                    unit=unit or DEFAULT_LOGIN_UNIT,
                    allow_offline=False,
                )
            except Exception as exc:
                success, user_info, err_msg = (
                    False,
                    None,
                    f"Lỗi kết nối máy chủ xác thực: {exc}",
                )

            if not success:
                self._is_submitting = False
                self._set_form_disabled(False)
                self.login_button_content.controls = [self.login_btn_text, self.login_btn_icon]
                self.login_button.scale = 1.0
                self._show_status(err_msg or "Đăng nhập thất bại. Vui lòng kiểm tra lại mật khẩu.", is_error=True)
                self._safe_update()
                return

            # Trạng thái 2: Xác nhận thành công với icon tích xanh và gradient Emerald
            is_offline = user_info.get("is_offline", False) if user_info else False
            status_text = (
                "Xác thực ngoại tuyến hợp lệ! Đang mở hệ thống..."
                if is_offline
                else "Đăng nhập FastBusiness ERP thành công! Đang tải thương hiệu..."
            )

            self.login_button.gradient = ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=["#059669", "#00B8E8"],
            )
            self.login_button_content.controls = [
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE_ROUNDED,
                    color=ft.Colors.WHITE,
                    size=20,
                ),
                ft.Text(
                    "Đăng nhập thành công!",
                    size=15,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE,
                ),
            ]
            self.login_button.scale = 1.02
            self._show_status(status_text, is_error=False)
            self._safe_update()

            time.sleep(0.15)
            self.login_button.scale = 1.0
            self._safe_update()

            time.sleep(0.35)

            # Trạng thái 3: Thẻ form mờ dần và trượt nhẹ lên trên (Exit animation)
            self.form_card.opacity = 0.0
            self.form_card.offset = ft.Offset(0, -0.05)
            self.form_card.scale = 0.96
            self._safe_update()

            time.sleep(0.25)

            # Trạng thái 4: Chuyển tiếp tới màn hình tải thương hiệu
            if self.on_login_success:
                self.on_login_success(username)

        threading.Thread(target=_proceed_login_animation, daemon=True).start()

    def reset(self):
        """Khôi phục lại giao diện ban đầu khi người dùng đăng xuất."""
        if self._unit_lookup_timer:
            self._unit_lookup_timer.cancel()
            self._unit_lookup_timer = None

        self._is_submitting = False
        self._user_exists = None
        self._last_checked_user = ""

        self._set_form_disabled(False)
        self.company_dropdown.error_text = None
        self.company_dropdown.value = DEFAULT_LOGIN_DATABASE

        self.username_input.value = ""
        self.username_input.error = None

        self.unit_dropdown.error_text = None
        self.unit_dropdown.options = [
            ft.dropdown.Option(key=DEFAULT_LOGIN_UNIT, text=f"{DEFAULT_LOGIN_UNIT} - CÔNG TY"),
        ]
        self.unit_dropdown.value = DEFAULT_LOGIN_UNIT

        self.password_input.value = ""
        self.password_input.error = None

        self.status_banner.visible = False
        self.status_banner.opacity = 0.0
        self.status_banner.offset = ft.Offset(0, -0.1)

        self.login_button_content.controls = [self.login_btn_text, self.login_btn_icon]
        self.login_button.gradient = ft.LinearGradient(
            begin=ft.Alignment.CENTER_LEFT,
            end=ft.Alignment.CENTER_RIGHT,
            colors=[self.BRAND_PRIMARY, self.BRAND_SECONDARY],
        )
        self.login_button.scale = 1.0

        self.form_card.opacity = 1.0
        self.form_card.scale = 1.0
        self.form_card.offset = ft.Offset(0, 0)
        self._safe_update()
        self.load_initial_entity_data()

    def _safe_update(self):
        try:
            self._app_page.update()
        except Exception:
            pass

    def apply_theme(self, is_dark: bool):
        mode_key = "dark" if is_dark else "light"
        palette = self.THEME_PALETTE[mode_key]

        self.main_content.image = ft.DecorationImage(
            src=self.BG_IMAGE_DARK if is_dark else self.BG_IMAGE_LIGHT,
            fit=ft.BoxFit.COVER,
            alignment=ft.Alignment.BOTTOM_CENTER,
        )

        self.header.bgcolor = palette["header_bg"]
        self.header_divider.color = palette["divider"]
        self.logo_img.src = self.LOGO_DARK if is_dark else self.LOGO_LIGHT

        self.theme_button.icon = (
            ft.Icons.LIGHT_MODE
            if is_dark
            else ft.Icons.DARK_MODE
        )
        self.theme_button.icon_color = palette["theme_btn_icon"]
        self.theme_button.bgcolor = palette["theme_btn_bg"]
        self.theme_button.tooltip = (
            "Chuyển sang Light Mode" if is_dark else "Chuyển sang Dark Mode"
        )

        self.form_card.bgcolor = palette["card_bg"]
        self.form_card.border = ft.Border.all(1, palette["card_border"])
        self.title_text.color = palette["text_primary"]

        for field in (self.username_input, self.password_input):
            field.bgcolor = palette["input_bg"]
            field.color = palette["text_primary"]
            field.border = self._make_input_border(palette["input_border"])
            field.label_style = ft.TextStyle(color=palette["text_secondary"], size=13)
            field.hint_style = ft.TextStyle(color=palette["text_secondary"], size=13)

        for dd in (self.company_dropdown, self.unit_dropdown):
            dd.bgcolor = palette["input_bg"]
            dd.fill_color = palette["input_bg"]
            dd.border_color = palette["input_border"]
            dd.color = palette["text_primary"]
            dd.label_style = ft.TextStyle(color=palette["text_secondary"], size=13)
            dd.menu_style = ft.MenuStyle(
                bgcolor=palette["header_bg"],
                elevation=6,
                shape=ft.RoundedRectangleBorder(radius=12),
            )

        self.footer_text.color = palette["text_secondary"]

        if self.status_banner.visible:
            is_err = self.status_icon.name == ft.Icons.ERROR_OUTLINE_ROUNDED
            self._show_status(self.status_text.value, is_error=is_err)
