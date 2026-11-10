import flet as ft
from unittest.mock import MagicMock
from ui.views.brand_loading_view import BrandLoadingView
from ui.views.auth_login_view import AuthLoginView


def test_brand_loading_view_init():
    mock_page = MagicMock(spec=ft.Page)
    mock_page.theme_mode = ft.ThemeMode.LIGHT
    on_complete_mock = MagicMock()

    loader = BrandLoadingView(
        username="AdminLED",
        on_complete=on_complete_mock,
        page=mock_page,
    )

    assert loader.username == "AdminLED"
    assert loader.expand is True
    assert loader.progress_bar is not None
    assert loader.card is not None
    assert loader.logo_badge is not None
    assert loader.status_icon is not None
    assert loader.percent_text.value == "0%"
    assert "AdminLED" in loader.user_badge.content.controls[1].value


def test_brand_loading_view_sequence():
    mock_page = MagicMock(spec=ft.Page)
    mock_page.theme_mode = ft.ThemeMode.LIGHT
    completed = []

    def on_complete():
        completed.append(True)

    loader = BrandLoadingView(
        username="Tester",
        on_complete=on_complete,
        page=mock_page,
    )

    # Chạy trực tiếp sequence (synchronous test)
    loader._run_loading_sequence()

    assert loader.progress_bar.value == 1.0
    assert loader.percent_text.value == "100%"
    assert len(completed) == 1


def test_auth_login_view_init_and_reset():
    mock_page = MagicMock(spec=ft.Page)
    mock_page.theme_mode = ft.ThemeMode.LIGHT
    on_login_mock = MagicMock()
    on_theme_mock = MagicMock()

    login = AuthLoginView(
        page=mock_page,
        on_login_success=on_login_mock,
        on_toggle_theme=on_theme_mock,
    )

    assert login.username_input is not None
    assert login.password_input is not None
    assert login.login_button is not None
    assert login.form_card is not None
    assert login._is_submitting is False

    # Giả lập nhập liệu và reset
    login.username_input.value = "user123"
    login.password_input.value = "pass123"
    login.username_input.disabled = True
    login.reset()

    assert login.username_input.value == ""
    assert login.password_input.value == ""
    assert login.username_input.disabled is False
    assert login._is_submitting is False


def test_auth_login_validation_error():
    mock_page = MagicMock(spec=ft.Page)
    mock_page.theme_mode = ft.ThemeMode.LIGHT
    on_login_mock = MagicMock()

    login = AuthLoginView(
        page=mock_page,
        on_login_success=on_login_mock,
        on_toggle_theme=MagicMock(),
    )

    # Bỏ trống thông tin đăng nhập và gọi _handle_login
    login.username_input.value = ""
    login.password_input.value = ""
    login._handle_login(None)

    assert login.username_input.error is not None
    assert login.status_banner.visible is True
    assert on_login_mock.call_count == 0



def test_auth_login_four_fields_and_unit_lookup(monkeypatch):
    mock_page = MagicMock(spec=ft.Page)
    mock_page.theme_mode = ft.ThemeMode.LIGHT
    on_login_mock = MagicMock()

    login = AuthLoginView(
        page=mock_page,
        on_login_success=on_login_mock,
        on_toggle_theme=MagicMock(),
    )

    # Kiểm tra đủ 4 trường theo đúng thứ tự: Công ty -> Tên -> Đơn Vị -> Mật khẩu
    assert login.company_dropdown is not None
    assert login.username_input is not None
    assert login.unit_dropdown is not None
    assert login.password_input is not None
    assert login.company_dropdown.value == "TOANTRUNG_FBISP2421_A"
    assert login.unit_dropdown.value == "CTY"

    # Giả lập GetUnitData trả về {"d": false} khi nhập user không tồn tại
    from api.services import FastBusinessService
    monkeypatch.setattr(
        FastBusinessService,
        "get_unit_data",
        lambda self, u, database=None, **kwargs: (False, []) if u == "ghost_user" else (True, [{"code": "CTY", "name": "CÔNG TY", "en_name": "COMPANY"}]),
    )

    login.username_input.value = "ghost_user"
    res_false = login._lookup_unit_for_user("ghost_user")
    assert res_false is False
    assert login.unit_dropdown.value is None
    assert login.username_input.error is not None

    # Giả lập nhập "bang" -> GetUnitData trả về [["CTY", "CÔNG TY", "COMPANY"]]
    login.username_input.value = "bang"
    res_true = login._lookup_unit_for_user("bang")
    assert res_true is True
    assert login.unit_dropdown.value == "CTY"
    assert login.username_input.error is None
