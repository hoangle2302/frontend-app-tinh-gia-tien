from unittest.mock import MagicMock
import tempfile
import os
import api
from database.db_manager import DBManager


def test_api_constants_endpoints():
    assert api.DEFAULT_API_HOST == "192.168.2.62"
    assert api.DEFAULT_API_BASE_URL == "http://192.168.2.62"
    assert "GetGridViewPage" in api.ApiEndpoints.GET_GRID_VIEW_PAGE
    assert "GetCompletionList" in api.ApiEndpoints.GET_COMPLETION_LIST
    assert "GetListViewPage" in api.ApiEndpoints.GET_LIST_VIEW_PAGE
    assert "GetViewPost" in api.ApiEndpoints.GET_VIEW_POST


def test_voucher_and_commands():
    assert api.VoucherCodes.DETAIL_QUOTE == "BT1"
    assert api.GridCalcCommands.CALC_POWER == "nguon"
    assert api.GridCalcCommands.CALC_CARD_PROCESSOR == "card_xu_ly"
    assert api.GridCalcCommands.CALC_ELECTRICITY == "dien"
    assert api.GridCalcCommands.CALC_MECHANICS == "co_khi"
    assert api.GridCalcCommands.CALC_CABINET_POWER == "tu_dien"
    assert api.GridCalcCommands.CALC_CABIN == "cabin"
    assert api.GridCalcCommands.CALC_ALL == "tat_ca"


def test_lookups_and_brands():
    brands = [b.value for b in api.ModuleBrands]
    assert "GKGD" in brands
    assert "LAMPRO" in brands
    assert "QIANGLI" in brands
    assert "SKYWORTH" in brands
    assert "LONGRUN" in brands

    assert api.EnvironmentTypes.INDOOR.value == "1"
    assert api.EnvironmentTypes.OUTDOOR.value == "2"

    assert api.ControlTypes.OFFLINE.value == "0"
    assert api.ControlTypes.ONLINE.value == "1"
    assert api.ControlTypes.HYBRID.value == "2"


def test_form_parameters_scan():
    # Kiểm tra 117 tham số trích xuất từ api.txt
    assert len(api.FORM_PARAMETERS_LIST) == 117
    assert "ngay_ct" in api.FORM_PARAMETERS_LIST
    assert "kt_hien_thi_w" in api.FORM_PARAMETERS_LIST
    assert "kt_hien_thi_h" in api.FORM_PARAMETERS_LIST
    assert "tong_pixel" in api.FORM_PARAMETERS_LIST
    assert "cong_suat" in api.FORM_PARAMETERS_LIST
    assert "hang_bxl" in api.FORM_PARAMETERS_LIST
    assert "vao_hdmi_14" in api.FORM_PARAMETERS_LIST
    assert "ra_lan" in api.FORM_PARAMETERS_LIST


def test_bt1_fields_structure():
    field_names = [f["name"] for f in api.BT1_GRID_FIELDS]
    assert "ma_vt" in field_names
    assert "dien_giai" in field_names
    assert "so_luong" in field_names
    assert "gia_nt" in field_names
    assert "tien_nt" in field_names
    assert "loai" in field_names
    assert "ct_yn" in field_names


def test_lookup_fields_explicit_mapping_to_dtb():
    # Giả lập API trả về LookupFields chỉ định rõ các trường DB
    mock_client = MagicMock()
    mock_client.post.return_value = (
        True,
        {
            "d": {
                "TotalRowCount": 2,
                "Rows": [["BRAND-01", "GKGD Opto"], ["BRAND-02", "Lampro Display"]],
                "LookupFields": ["code", "supplier"],
            }
        },
        None,
    )

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    tmp.close()

    try:
        db = DBManager(db_path=db_path)
        db.initialize()

        service = api.FastBusinessService(client=mock_client)
        # Scan API và xử lý LookupFields vào database
        records = service.scan_and_process_lookup("module_brand", db_manager=db)

        assert len(records) == 2
        assert records[0]["supplier"] == "GKGD Opto"
        assert records[0]["target_field"] == "supplier"

        # Kiểm tra bảng lookup_values trong dtb
        db_records = db.get_lookup_records("module_brand")
        assert len(db_records) == 2
        assert db_records[0]["target_field"] == "supplier"
        assert db_records[0]["name"] == "GKGD Opto"
    finally:
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except Exception:
            pass


def test_lookup_fields_null_fallback_mapping_to_dtb():
    # Giả lập API trả về LookupFields: null (như nguyên mẫu trong api.txt)
    mock_client = MagicMock()
    mock_client.post.return_value = (
        True,
        {
            "d": {
                "TotalRowCount": 2,
                "Rows": [["1", "Indoor"], ["2", "Outdoor"]],
                "LookupFields": None,
            }
        },
        None,
    )

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    tmp.close()

    try:
        db = DBManager(db_path=db_path)
        db.initialize()

        service = api.FastBusinessService(client=mock_client)
        records = service.scan_and_process_lookup("environment", db_manager=db)

        assert len(records) == 2
        assert records[0]["target_field"] == "environment"
        # Giá trị "1" được transform thành "indoor" trỏ khớp trường environment trong bảng products
        assert records[0]["environment"] == "indoor"
        assert records[1]["environment"] == "outdoor"

        db_records = db.get_lookup_records("environment")
        assert len(db_records) == 2
        assert db_records[0]["code"] == "1"
        assert db_records[0]["name"] == "Indoor"
    finally:
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except Exception:
            pass


def test_scan_all_api_lookups():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    tmp.close()

    try:
        db = DBManager(db_path=db_path)
        db.initialize()

        service = api.FastBusinessService()
        all_lookups = service.scan_all_api_lookups(db_manager=db)

        assert "environment" in all_lookups
        assert "control_type" in all_lookups
        assert "module_brand" in all_lookups

        assert len(all_lookups["module_brand"]) == 5
        assert len(all_lookups["environment"]) == 2

        # Kiểm tra dtb đã lưu trữ đầy đủ
        saved_brands = db.get_lookup_records("module_brand")
        assert len(saved_brands) == 5
    finally:
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except Exception:
            pass


def test_hash_password_md5():
    # Trường hợp chuỗi MD5 hex có sẵn (như trong trace yêu cầu: be029f28e4556b8995911063a8e48f0c)
    raw_md5 = "be029f28e4556b8995911063a8e48f0c"
    assert api.hash_password_md5(raw_md5) == "be029f28e4556b8995911063a8e48f0c"

    # Trường hợp mật khẩu dạng text thường (ví dụ: '123456')
    hashed = api.hash_password_md5("123456")
    assert len(hashed) == 32
    assert hashed == "e10adc3949ba59abbe56e057f20f883e"


def test_api_client_cookie_and_headers():
    client = api.FastBusinessApiClient(base_url="http://192.168.2.62")
    assert client.get_session_id() is None

    # Thiết lập SessionId thủ công
    client.set_session_id("manlhzb4os1zkgxojbi0mkpn")
    assert client.get_session_id() == "manlhzb4os1zkgxojbi0mkpn"

    headers = client._prepare_headers(api.ApiEndpoints.LOGIN)
    assert headers["Origin"] == "http://192.168.2.62"
    assert "Login.aspx" in headers["Referer"]
    assert "FastBusiness.SessionId=manlhzb4os1zkgxojbi0mkpn" in headers["Cookie"]

    # Kiểm tra xử lý Set-Cookie từ HTTP Response Header
    mock_resp_headers = MagicMock()
    mock_resp_headers.get_all.return_value = [
        "FastBusiness.SessionId=new_token_9999; path=/; HttpOnly",
        "OtherCookie=123; path=/",
    ]
    client._process_response_cookies(mock_resp_headers)
    assert client.get_session_id() == "new_token_9999"
    assert client.cookies.get("OtherCookie") == "123"

    client.clear_session()
    assert len(client.cookies) == 0


def test_login_service_online_success():
    mock_client = MagicMock()
    # Giả lập phản hồi POST thành công
    mock_client.post.return_value = (True, {"d": True}, None)
    mock_client.get_session_id.return_value = "manlhzb4os1zkgxojbi0mkpn"

    service = api.FastBusinessService(client=mock_client)
    ok, user_info, err = service.login(
        username="bang",
        password="be029f28e4556b8995911063a8e48f0c",
        database="TOANTRUNG_FBISP2421_A",
        unit="CTY",
        language="v",
        value="5ee03f08a401",
    )

    assert ok is True
    assert err is None
    assert user_info["user"] == "bang"
    assert user_info["database"] == "TOANTRUNG_FBISP2421_A"
    assert user_info["session_id"] == "manlhzb4os1zkgxojbi0mkpn"
    assert user_info["is_offline"] is False

    # Kiểm tra đúng endpoint và đúng các trường trong payload
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args[0]
    assert call_args[0] == api.ApiEndpoints.LOGIN
    payload = call_args[1]
    assert payload["user"] == "bang"
    assert payload["password"] == "be029f28e4556b8995911063a8e48f0c"
    assert payload["database"] == "TOANTRUNG_FBISP2421_A"
    assert payload["unit"] == "CTY"
    assert payload["language"] == "v"
    assert payload["value"] == "5ee03f08a401"
    assert payload["force"] is False
    assert payload["storage"] is True
    assert payload["s"] == 0


def test_login_service_offline_fallback():
    mock_client = MagicMock()
    # Giả lập máy chủ ERP nội bộ chưa bật hoặc không kết nối được
    mock_client.post.return_value = (False, None, "Lỗi kết nối tới http://192.168.2.62: timed out")
    mock_client.is_reachable.return_value = False
    mock_client.get_session_id.return_value = None

    service = api.FastBusinessService(client=mock_client)
    ok, user_info, err = service.login(
        username="bang",
        password="plain_password_123",
    )

    assert ok is True
    assert err is None
    assert user_info["user"] == "bang"
    assert user_info["is_offline"] is True
    assert "offline_sess_" in user_info["session_id"]
    mock_client.set_session_id.assert_called()


def test_get_view_post_parsing():
    mock_client = MagicMock()
    # Dữ liệu JSON string nguyên bản trích từ api.txt dòng 10629
    api_txt_d = '{"View":{"Title":"","Language":"v","UserFullName":"truong","UserImageKey":"","UserCommentOrder":1,"FileMaxSize":102400000,"FileExtension":"*","MediaPreviewWidth":360,"MediaFullWidth":720,"PostPagingList":"10,20,50","PostLoadingCount":"10","CommentPageShowing":"5"},"Item":null,"Filter":{"PreviousPost":false,"NextPost":false,"TotalItem":0},"Message":"","Script":"","Authorize":true}'
    mock_client.post.return_value = (True, {"d": api_txt_d}, None)

    service = api.FastBusinessService(client=mock_client)
    post_info = service.get_view_post(username="truong")

    assert post_info["Authorize"] is True
    assert post_info["View"]["UserFullName"] == "truong"
    assert post_info["View"]["FileMaxSize"] == 102400000


def test_post_login_query_pipeline():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    tmp.close()

    try:
        db = DBManager(db_path=db_path)
        db.initialize()

        service = api.FastBusinessService()
        pipeline_res = service.post_login_query_pipeline(db_manager=db, username="bang")

        assert pipeline_res["status"] == "success"
        assert pipeline_res["username"] == "bang"
        assert pipeline_res["synced_to_db"] is True

        # 1. Truy vấn danh mục Lookups (GetCompletionList) đã quét và đồng bộ vào DB
        assert "lookups" in pipeline_res["queries"]
        assert len(pipeline_res["queries"]["lookups"]["environment"]) == 2
        assert len(pipeline_res["queries"]["lookups"]["control_type"]) == 3
        assert len(pipeline_res["queries"]["lookups"]["module_brand"]) == 5

        # 2. Truy vấn metadata lưới chứng từ BT1 (GetGridViewPage)
        assert "grid_view" in pipeline_res["queries"]
        grid = pipeline_res["queries"]["grid_view"]
        assert grid.get("Authorized") is True
        toolbar = grid.get("ViewPage", {}).get("Toolbar", [])
        assert len(toolbar) >= 2

        # 3. Truy vấn cấu hình người dùng & bài đăng (GetViewPost)
        assert "view_post" in pipeline_res["queries"]
        view_post = pipeline_res["queries"]["view_post"]
        assert view_post.get("Authorize") is True
        assert view_post.get("View", {}).get("UserFullName") == "bang"

        # 4. Truy vấn danh sách tệp đính kèm (GetListViewPage)
        assert "attached_files" in pipeline_res["queries"]

        # Kiểm tra dữ liệu thực sự đã nằm trong database (dtb)
        env_in_db = db.get_lookup_records("environment")
        assert len(env_in_db) == 2
        brands_in_db = db.get_lookup_records("module_brand")
        assert len(brands_in_db) == 5
    finally:
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except Exception:
            pass


def test_shared_session_across_instances():
    client1 = api.FastBusinessApiClient()
    client1.set_session_id("session_cross_instance_123")

    client2 = api.FastBusinessApiClient()
    assert client2.get_session_id() == "session_cross_instance_123"

    service1 = api.FastBusinessService()
    service2 = api.FastBusinessService()
    assert service1.client.get_session_id() == "session_cross_instance_123"
    assert service2.client.get_session_id() == "session_cross_instance_123"

    headers = client2._prepare_headers("/AppService/PostExtender.asmx/GetViewPost")
    assert "FastBusiness.SessionId=session_cross_instance_123" in headers["Cookie"]


def test_get_entity_data_and_get_unit_data():
    mock_client = MagicMock()
    mock_client.get_session_id.return_value = "2jjucsxfqb1c1joc5dnjjk0j"

    # 1. Test GetEntityData: {"d":[["01","Công ty","TOANTRUNG_FBISP2421_A"]]}
    mock_client.post.return_value = (
        True,
        {"d": [["01", "Công ty", "TOANTRUNG_FBISP2421_A"]]},
        None,
    )
    service = api.FastBusinessService(client=mock_client)
    entities = service.get_entity_data()
    assert len(entities) == 1
    assert entities[0]["code"] == "01"
    assert entities[0]["name"] == "Công ty"
    assert entities[0]["database"] == "TOANTRUNG_FBISP2421_A"

    # 2. Test GetUnitData khi user "bang" tồn tại: {"d":[["CTY","CÔNG TY","COMPANY"]]}
    mock_client.post.return_value = (
        True,
        {"d": [["CTY", "CÔNG TY", "COMPANY"]]},
        None,
    )
    exists, units = service.get_unit_data("bang", database="TOANTRUNG_FBISP2421_A")
    assert exists is True
    assert len(units) == 1
    assert units[0]["code"] == "CTY"
    assert units[0]["name"] == "CÔNG TY"
    assert units[0]["en_name"] == "COMPANY"

    # 3. Test GetUnitData khi user KHÔNG tồn tại: {"d": false}
    mock_client.post.return_value = (
        True,
        {"d": False},
        None,
    )
    exists_invalid, units_invalid = service.get_unit_data("user_khong_ton_tai", database="TOANTRUNG_FBISP2421_A")
    assert exists_invalid is False
    assert units_invalid == []


def test_login_trace_d_true_and_d_false():
    mock_client = MagicMock()
    mock_client.get_session_id.return_value = "2jjucsxfqb1c1joc5dnjjk0j"
    mock_client.post.return_value = (True, {"d": True}, None)

    service = api.FastBusinessService(client=mock_client)
    ok, info, err = service.login(
        username="bang",
        password="3dcaaf6c7bedd928691f0d3c76e264ee",
        database="TOANTRUNG_FBISP2421_A",
        unit="CTY",
        language="v",
        value="af9ac0f31b2d",
    )
    assert ok is True
    assert err is None
    assert info["user"] == "bang"
    assert info["database"] == "TOANTRUNG_FBISP2421_A"
    assert info["unit"] == "CTY"
    assert info["session_id"] == "2jjucsxfqb1c1joc5dnjjk0j"

    # Kiểm tra khi sai mật khẩu trả về {"d": false}
    mock_client.post.return_value = (True, {"d": False}, None)
    ok_fail, info_fail, err_fail = service.login(
        username="bang",
        password="wrong_password",
        database="TOANTRUNG_FBISP2421_A",
        unit="CTY",
    )
    assert ok_fail is False
    assert info_fail is None
    assert err_fail is not None
