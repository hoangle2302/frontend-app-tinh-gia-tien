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
    assert login.form_card.width == 360
    assert (
        login.company_dropdown.width
        == login.username_input.width
        == login.unit_dropdown.width
        == login.password_input.width
        == 320
    )
    assert login.company_dropdown.expanded_insets == ft.Padding(0, 0, 0, 0)
    assert login.unit_dropdown.expanded_insets == ft.Padding(0, 0, 0, 0)
    assert login.company_dropdown.content_padding == login.username_input.content_padding
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

    # Kiểm tra on_resize và _safe_update nhận controls
    mock_page.width = 400
    login.on_resize()
    assert login.form_card.width == 360
    assert (
        login.company_dropdown.width
        == login.username_input.width
        == login.unit_dropdown.width
        == login.password_input.width
        == 320
    )


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


def test_quote_search_and_clone_and_detail_view():
    mock_page = MagicMock(spec=ft.Page)
    mock_page.theme_mode = ft.ThemeMode.LIGHT
    mock_page.width = 400
    mock_page.height = 800

    from ui.views.main_view import MainView
    from database.db_manager import DBManager

    db = DBManager()
    db.initialize()

    # Lưu 1 báo giá mẫu với tên có dấu
    test_id = db.save_quote_history(
        quote_name="Dự án Hội trường Khách sạn",
        customer_name="Công ty Toàn Trung",
        payload={
            "customer_name": "Công ty Toàn Trung",
            "project_name": "Dự án Hội trường Khách sạn",
            "module_code": "M-P2.5-IN",
            "width_m": "3.84",
            "height_m": "1.92",
            "screen_quantity": 1,
            "display_mode": "Online",
            "vat_percent": 10,
            "profit_percent": 15,
        },
        total=125000000.0,
        status="Nháp",
    )

    mv = MainView(page=mock_page, db=db)

    # 1. Kiểm tra tìm kiếm không dấu
    mv.list_search.value = "hoi truong toan trung"
    results = mv._get_filtered_list_history()
    assert any(r["id"] == test_id for r in results)

    # 2. Kiểm tra tìm kiếm theo module
    mv.list_search.value = "p2.5"
    results = mv._get_filtered_list_history()
    assert any(r["id"] == test_id for r in results)

    # 3. Kiểm tra xem chi tiết (chỉ xem)
    mv._open_quote_detail_view(test_id)
    assert mv.detail_mode is True
    assert mv.active_detail_item is not None
    assert mv.active_detail_item["id"] == test_id
    detail_content = mv.list_wrapper.content
    assert detail_content is not None
    # Đóng xem chi tiết
    mv._close_detail_view()
    assert mv.detail_mode is False

    # 4. Kiểm tra sao chép (tự động tạo 1 bảng tương tự trong DB)
    initial_count = len(db.list_quote_history())
    mv._clone_history(test_id)
    new_count = len(db.list_quote_history())
    assert new_count == initial_count + 1

    # Bản sao có tên mới chứa "(Bản sao)" và cùng tổng tiền
    cloned = db.list_quote_history()[0]
    assert "(Bản sao)" in cloned["quote_name"]
    assert cloned["total"] == 125000000.0


def test_input_panel_removed_elements():
    mock_page = MagicMock(spec=ft.Page)
    from ui.components.input_panel import InputPanel
    from database.db_manager import DBManager

    db = DBManager()
    db.initialize()

    panel = InputPanel(
        options={
            "modules": db.list_products("module"),
            "powers": db.list_products("power"),
            "cards": db.list_products("card"),
            "frames": db.list_products("frame"),
            "processors": db.list_products("processor"),
        },
        on_change=MagicMock(),
        on_save=MagicMock(),
        on_export_excel=MagicMock(),
        on_export_pdf=MagicMock(),
        on_load_preset=MagicMock(),
    )

    # Kiểm tra card_display_module có nút Loại màn hình (Trong nhà / Ngoài trời), không còn chữ (Indoor / Outdoor)
    module_controls_str = str(panel.card_display_module.content.controls)
    assert "Loại màn hình" in module_controls_str
    assert "Trong nhà" in module_controls_str
    assert "Ngoài trời" in module_controls_str
    assert "Indoor" not in module_controls_str
    assert "Outdoor" not in module_controls_str

    # Kiểm tra layout không còn nút "Lập dự toán" có mũi tên back và stepper "01 Cấu hình"
    panel_layout_str = str(panel.content)
    assert "01 Cấu hình" not in panel_layout_str
    assert "Lập dự toán" not in panel_layout_str


def test_brand_loading_view_appearance():
    mock_page = MagicMock(spec=ft.Page)
    loader = BrandLoadingView(
        username="TestUser",
        on_complete=MagicMock(),
        page=mock_page,
    )
    # Kiểm tra màu nền khớp màu xanh thương hiệu Toàn Trung của logo
    assert loader.bgcolor == "#0B4CA3"
    assert loader.gradient is None
    # Kiểm tra logo không còn khung viền/hộp bao quanh
    assert loader.logo_badge.border is None
    assert loader.logo_badge.bgcolor is None
    assert loader.logo_badge.shadow is None


def test_main_view_reset_from_profile_on_logout():
    from main import _handle_logout
    from ui.views.main_view import MainView
    from database.db_manager import DBManager

    mock_page = MagicMock(spec=ft.Page)
    mock_page.width = 400
    mock_page.controls = [MagicMock()]
    db = DBManager()
    db.initialize()

    mv = MainView(page=mock_page, db=db)
    # Người dùng mở màn hình Hồ sơ
    mv.open_profile()
    assert mv.view_container.content != mv.quote_view

    # Gọi reset của MainView
    mv.reset()
    assert mv.nav_bar.selected_index == 0
    assert mv.view_container.content == mv.quote_view

    # Kiểm tra kịch bản đăng xuất rồi đăng nhập lại
    mv.open_profile()
    app_state = {
        "current_view": "main",
        "username": "hoang",
        "main_view": mv,
        "login_view": MagicMock(),
    }
    _handle_logout(mock_page, app_state)
    assert app_state["current_view"] == "login"
    assert app_state["username"] is None
    # Sau khi logout, main_view đã được tự động reset về Tab 0 (Lập dự toán)
    assert mv.nav_bar.selected_index == 0
    assert mv.view_container.content == mv.quote_view


