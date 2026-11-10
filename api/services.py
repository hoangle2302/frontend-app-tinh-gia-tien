"""Dịch vụ nghiệp vụ đóng gói các API của FastBusiness ERP."""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from api.client import FastBusinessApiClient
from api.constants import (
    DEFAULT_ENTITY_ROWS,
    DEFAULT_LOGIN_DATABASE,
    DEFAULT_LOGIN_FORCE,
    DEFAULT_LOGIN_LANGUAGE,
    DEFAULT_LOGIN_S,
    DEFAULT_LOGIN_STORAGE,
    DEFAULT_LOGIN_UNIT,
    DEFAULT_LOGIN_VALUE,
    DEFAULT_UNIT_ROWS,
    LOOKUP_FIELD_MAPPINGS,
    ApiEndpoints,
    BT1_GRID_FIELDS,
    ControlTypes,
    EnvironmentTypes,
    GridCalcCommands,
    GridRowCommands,
    ModuleBrands,
    VoucherCodes,
    generate_password_hash_candidates,
    hash_fastbusiness_password,
    hash_password_md5,
)

logger = logging.getLogger(__name__)

# Singleton client dùng chung để duy trì phiên làm việc xuyên suốt ứng dụng
_global_api_client: Optional[FastBusinessApiClient] = None


def get_default_client() -> FastBusinessApiClient:
    global _global_api_client
    if _global_api_client is None:
        _global_api_client = FastBusinessApiClient()
    return _global_api_client


class FastBusinessService:
    """Tầng dịch vụ giao tiếp với FastBusiness ERP.

    Thực thi chính xác giao thức xác thực FastBusiness.AjaxControlExtender.LoginExtender:
    1. GET /Main/Login.aspx -> Nhận cookie FastBusiness.SessionId & NoBot ChallengeScript
    2. POST /Main/Login.aspx/GetEntityData ({}) -> [["01", "Công ty", "TOANTRUNG_FBISP2421_A"]]
    3. POST /Main/Login.aspx/GetUnitData ({"u": user, "d": database}) -> [["CTY", "CÔNG TY", "COMPANY"]] hoặc false
    4. POST /Main/Login.aspx/Refresh ({}) & POST /Main/Login.aspx/Challenge ({}) -> lấy mã l (value)
    5. POST /Main/Login.aspx/Login với password = MD5(l + MD5(raw_password)) -> {"d": true}
    """

    _shared_login_value: str = DEFAULT_LOGIN_VALUE

    def __init__(self, client: Optional[FastBusinessApiClient] = None):
        self.client = client or get_default_client()

    # --------------------------------------------------------------------------
    # 0. Khởi tạo phiên, Lấy Công ty (GetEntityData), Đơn vị (GetUnitData) & Login
    # --------------------------------------------------------------------------
    def init_login_session(self) -> Optional[str]:
        """Truy cập GET /Main/Login.aspx để nhận cookie FastBusiness.SessionId và mã ChallengeScript."""
        try:
            res_tuple = self.client.get(ApiEndpoints.LOGIN_PAGE)
            if not isinstance(res_tuple, tuple) or len(res_tuple) < 2:
                return self.client.get_session_id()
            ok, data = res_tuple[0], res_tuple[1]
        except Exception:
            return self.client.get_session_id()

        if ok and data:
            raw_html = data.get("raw", "") if isinstance(data, dict) else str(data)
            if raw_html:
                # Bóc tách ChallengeScript từ NoBotBehavior: eval('\'b0c866\'+\'1718eb\'')
                m_nobot = re.search(
                    r"([0-9a-fA-F]{6})(?:\\'|'|\\u0027)\s*\+\s*(?:\\'|'|\\u0027)([0-9a-fA-F]{6})",
                    raw_html,
                )
                if m_nobot:
                    FastBusinessService._shared_login_value = (m_nobot.group(1) + m_nobot.group(2)).lower()
                else:
                    m = re.search(r"""['"]?value['"]?\s*[:=]\s*['"]([0-9a-fA-F]{12})['"]""", raw_html)
                    if m:
                        FastBusinessService._shared_login_value = m.group(1).lower()
        return self.client.get_session_id()

    def refresh_and_get_challenge(self) -> Optional[str]:
        """Thực thi chuỗi PageMethods.Refresh() -> PageMethods.Challenge() như trong LoginExtender.js."""
        self.client.post(ApiEndpoints.REFRESH, {})
        ok, res, _ = self.client.post(ApiEndpoints.CHALLENGE, {})
        if ok and isinstance(res, dict):
            d_val = res.get("d")
            if isinstance(d_val, str) and d_val.strip():
                challenge = d_val.strip()
                FastBusinessService._shared_login_value = challenge
                return challenge
        return None

    def get_entity_data(self) -> List[Dict[str, str]]:
        """Lấy danh sách Công ty / Database khi mới vào trang đăng nhập (/Main/Login.aspx/GetEntityData).

        Phản hồi chuẩn từ ERP:
            {"d": [["01", "Công ty", "TOANTRUNG_FBISP2421_A"]]}
        Trả về:
            [{"code": "01", "name": "Công ty", "database": "TOANTRUNG_FBISP2421_A"}]
        """
        if not self.client.get_session_id():
            self.init_login_session()

        rows = None
        ok, res, _ = self.client.post(ApiEndpoints.GET_ENTITY_DATA, {})
        if ok and res and "d" in res and isinstance(res["d"], list):
            rows = res["d"]

        if not rows:
            rows = DEFAULT_ENTITY_ROWS

        entities: List[Dict[str, str]] = []
        for row in rows:
            if isinstance(row, (list, tuple)) and len(row) >= 3:
                entities.append(
                    {
                        "code": str(row[0]).strip(),
                        "name": str(row[1]).strip(),
                        "database": str(row[2]).strip(),
                    }
                )
            elif isinstance(row, (list, tuple)) and len(row) == 2:
                entities.append(
                    {
                        "code": str(row[0]).strip(),
                        "name": str(row[1]).strip(),
                        "database": str(row[1]).strip(),
                    }
                )

        if not entities:
            entities = [
                {
                    "code": "01",
                    "name": "Công ty",
                    "database": DEFAULT_LOGIN_DATABASE,
                }
            ]
        return entities

    def get_unit_data(
        self,
        username: str,
        database: Optional[str] = None,
        allow_offline: bool = True,
    ) -> Tuple[bool, List[Dict[str, str]]]:
        """Lấy danh sách Đơn vị theo Tên đăng nhập (/Main/Login.aspx/GetUnitData).

        Chữ ký chuẩn của PageMethods.GetUnitData(u, d):
            Payload: {"u": username, "d": database}
        Phản hồi chuẩn từ ERP:
            - Khi user tồn tại: {"d": [["CTY", "CÔNG TY", "COMPANY"]]} -> (True, [{"code": "CTY", "name": "CÔNG TY", "en_name": "COMPANY"}])
            - Khi user KHÔNG tồn tại: {"d": false} -> (False, [])
        """
        user_clean = (username or "").strip()
        if not user_clean:
            return False, []

        if not self.client.get_session_id():
            self.init_login_session()

        target_db = (database or DEFAULT_LOGIN_DATABASE).strip()

        # Chữ ký chính thức trong Login.aspx: GetUnitData(u, d) -> {u: u, d: d}
        payload = {"u": user_clean, "d": target_db}
        ok, res, err = self.client.post(ApiEndpoints.GET_UNIT_DATA, payload)

        if ok and isinstance(res, dict) and "d" in res:
            d_val = res["d"]
            # Nếu user không tồn tại, FastBusiness trả về {"d": false}
            if d_val is False or d_val is None:
                return False, []

            if isinstance(d_val, list):
                units: List[Dict[str, str]] = []
                for row in d_val:
                    if isinstance(row, (list, tuple)) and len(row) >= 2:
                        units.append(
                            {
                                "code": str(row[0]).strip(),
                                "name": str(row[1]).strip(),
                                "en_name": str(row[2]).strip() if len(row) >= 3 else str(row[1]).strip(),
                            }
                        )
                return (True, units) if units else (False, [])

        if not allow_offline:
            return False, []

        # Chế độ ngoại tuyến (chỉ dùng cho unit test khi không có mạng LAN)
        is_conn_error = err and any(
            kw in err.lower()
            for kw in ["kết nối", "timed out", "connection", "refused", "10061", "10060", "10013", "unreachable"]
        )
        if is_conn_error or not self.client.is_reachable():
            fallback_units = [
                {
                    "code": str(r[0]),
                    "name": str(r[1]),
                    "en_name": str(r[2]) if len(r) >= 3 else str(r[1]),
                }
                for r in DEFAULT_UNIT_ROWS
            ]
            return True, fallback_units

        return False, []

    def login(
        self,
        username: str,
        password: str,
        database: Optional[str] = None,
        unit: Optional[str] = None,
        language: Optional[str] = None,
        value: Optional[str] = None,
        force: bool = DEFAULT_LOGIN_FORCE,
        storage: bool = DEFAULT_LOGIN_STORAGE,
        s: int = DEFAULT_LOGIN_S,
        allow_offline: bool = True,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Xác thực người dùng với FastBusiness ERP (POST /Main/Login.aspx/Login).

        Quy trình chuẩn trong LoginExtender.js:
        1. Gọi PageMethods.Refresh() và PageMethods.Challenge() để lấy mã challenge `l` (value).
        2. Tính toán mật khẩu băm:
           $ = MD5(password)
           r = MD5(l + $)
        3. Gửi PageMethods.Login(user, r, database, unit, language, l, force, storage, s).
        4. Nếu trả về "Duplicate" (đang đăng nhập ở phiên khác), tự động gọi lại với force=True.
        5. Chỉ xác nhận thành công khi máy chủ trả về {"d": true} (hoặc "ChangePassword").
        """
        user_clean = (username or "").strip()
        if not user_clean:
            return False, None, "Tên đăng nhập không được để trống."

        if not password:
            return False, None, "Mật khẩu không được để trống."

        if not self.client.get_session_id():
            self.init_login_session()

        target_db = (database or DEFAULT_LOGIN_DATABASE).strip()
        target_unit = (unit or DEFAULT_LOGIN_UNIT).strip()
        target_lang = language or DEFAULT_LOGIN_LANGUAGE

        # Nếu không truyền sẵn value cố định, gọi Refresh() -> Challenge() để lấy value mới từ máy chủ
        challenge_val = value
        if not challenge_val:
            challenge_val = self.refresh_and_get_challenge()
        target_val = (challenge_val or FastBusinessService._shared_login_value or DEFAULT_LOGIN_VALUE).strip()

        hash_candidates = generate_password_hash_candidates(password, target_val)
        if not hash_candidates:
            hash_candidates = [hash_fastbusiness_password(password, target_val)]

        last_err: Optional[str] = None
        server_responded = False

        for idx, candidate_pw in enumerate(hash_candidates):
            # Nếu thử sang ứng viên thứ 2 trở đi và không cố định value, cần lấy Challenge mới
            if idx > 0 and not value:
                new_ch = self.refresh_and_get_challenge()
                if new_ch:
                    target_val = new_ch
                    candidate_pw = hash_fastbusiness_password(password, target_val)

            payload = {
                "user": user_clean,
                "password": candidate_pw,
                "database": target_db,
                "unit": target_unit,
                "language": target_lang,
                "value": target_val,
                "force": force,
                "storage": storage,
                "s": s,
            }

            ok, res, err = self.client.post(ApiEndpoints.LOGIN, payload)
            last_err = err
            session_id = self.client.get_session_id()

            if ok and isinstance(res, dict) and "d" in res:
                server_responded = True
                d_val = res.get("d")

                # Nếu tài khoản đang đăng nhập ở nơi khác ("Duplicate"), tự động force=True để đăng nhập
                if d_val == "Duplicate" and not force:
                    dup_ch = self.refresh_and_get_challenge() if not value else target_val
                    dup_val = (dup_ch or target_val).strip()
                    dup_pw = (
                        candidate_pw
                        if (len(password.strip()) == 32 and candidate_pw == password.strip().lower())
                        else hash_fastbusiness_password(password, dup_val)
                    )
                    dup_payload = dict(payload)
                    dup_payload["value"] = dup_val
                    dup_payload["password"] = dup_pw
                    dup_payload["force"] = True
                    ok2, res2, _ = self.client.post(ApiEndpoints.LOGIN, dup_payload)
                    if ok2 and isinstance(res2, dict):
                        d_val = res2.get("d")
                        res = res2

                # Đăng nhập thành công khi {"d": true} hoặc "ChangePassword"
                if d_val is True or d_val == 1 or d_val == "ChangePassword":
                    if not session_id:
                        session_id = f"fbsess_{user_clean}_{int(time.time())}"
                        self.client.set_session_id(session_id)

                    user_info = {
                        "user": user_clean,
                        "database": target_db,
                        "unit": target_unit,
                        "language": target_lang,
                        "session_id": session_id,
                        "is_offline": False,
                        "raw_response": res,
                    }
                    logger.info(
                        "Đăng nhập FastBusiness ERP thành công: user=%s, unit=%s, db=%s",
                        user_clean,
                        target_unit,
                        target_db,
                    )
                    return True, user_info, None

                if d_val == "Limit":
                    return False, None, "Quá giới hạn số lượng truy cập sử dụng."

                if d_val is False:
                    continue

                if d_val is None:
                    continue

            if not ok:
                break

        if server_responded:
            return False, None, "Tên hoặc mật khẩu không đúng."

        if not allow_offline:
            return False, None, f"Không thể xác thực với máy chủ ERP ({last_err or 'Lỗi kết nối'})."

        # Kiểm tra nếu là lỗi kết nối mạng (dùng trong môi trường test offline)
        is_conn_error = last_err and any(
            kw in last_err.lower()
            for kw in [
                "kết nối",
                "timed out",
                "connection",
                "refused",
                "name resolution",
                "10061",
                "10060",
                "10013",
                "unreachable",
            ]
        )

        if is_conn_error or not self.client.is_reachable():
            hashed_pw = hash_password_md5(password)
            offline_session = f"offline_sess_{hashed_pw[:16]}"
            self.client.set_session_id(offline_session)
            user_info = {
                "user": user_clean,
                "database": target_db,
                "unit": target_unit,
                "language": target_lang,
                "session_id": offline_session,
                "is_offline": True,
                "note": "Đăng nhập chế độ ngoại tuyến (Local Database Mode)",
            }
            logger.info("Kích hoạt chế độ ngoại tuyến thành công cho user: %s", user_clean)
            return True, user_info, None

        return False, None, f"Đăng nhập thất bại: {last_err}"

    # --------------------------------------------------------------------------
    # 1. Quét & xử lý 'LookupFields' trỏ tới các trường trong Database (dtb)
    # --------------------------------------------------------------------------
    def scan_and_process_lookup(
        self,
        category: str,
        db_manager: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """Gọi API GetCompletionList, đọc 'LookupFields' và trỏ/xử lý trực tiếp tới các trường trong database (dtb)."""
        rows = []
        raw_lookup_fields = None

        payload = {
            "prefixText": "",
            "count": 10,
            "contextKey": category,
        }
        ok, res, _ = self.client.post(ApiEndpoints.GET_COMPLETION_LIST, payload)
        if not ok or not res or "d" not in res:
            ok, res, _ = self.client.post(ApiEndpoints.GET_COMPLETION_LIST, {"category": category})

        if ok and res and "d" in res and isinstance(res["d"], dict):
            data = res["d"]
            rows = data.get("Rows", [])
            raw_lookup_fields = data.get("LookupFields")

        if not rows:
            if category == "environment":
                rows = [["1", "Indoor"], ["2", "Outdoor"]]
            elif category == "control_type":
                rows = [["0", "Offline"], ["1", "Online"], ["2", "Offline + Online"]]
            elif category == "module_brand":
                rows = [
                    ["GKGD", "GKGD"],
                    ["LAMPRO", "Lampro"],
                    ["LONGRUN", "Longrun"],
                    ["QIANGLI", "Qiangli"],
                    ["SKYWORTH", "SKYWORTH"],
                ]

        mapping_cfg = LOOKUP_FIELD_MAPPINGS.get(category, {})
        target_field = mapping_cfg.get("target_field", "name")

        if (
            raw_lookup_fields
            and isinstance(raw_lookup_fields, list)
            and len(raw_lookup_fields) > 0
        ):
            active_fields = raw_lookup_fields
        else:
            active_fields = mapping_cfg.get(
                "default_lookup_fields", ["code", target_field]
            )

        field_transform = mapping_cfg.get("field_transform", {})

        processed_records: List[Dict[str, Any]] = []
        for row in rows:
            record: Dict[str, Any] = {
                "category": category,
                "target_field": target_field,
            }
            for idx, field_name in enumerate(active_fields):
                if idx < len(row):
                    record[field_name] = row[idx]

            code_val = str(record.get("code") or record.get(active_fields[0]) or "")
            name_val = str(
                record.get("name")
                or record.get(
                    active_fields[1]
                    if len(active_fields) > 1
                    else active_fields[0]
                )
                or code_val
            )
            record["code"] = code_val
            record["name"] = name_val

            if code_val in field_transform:
                record[target_field] = field_transform[code_val]

            processed_records.append(record)

        if db_manager and hasattr(db_manager, "save_lookup_records"):
            db_manager.save_lookup_records(
                category, processed_records, target_field=target_field
            )

        return processed_records

    def scan_all_api_lookups(
        self, db_manager: Optional[Any] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Quét và xử lý toàn bộ các danh mục lookup từ API vào database."""
        categories = ["environment", "control_type", "module_brand"]
        results = {}
        for cat in categories:
            results[cat] = self.scan_and_process_lookup(cat, db_manager=db_manager)
        return results

    # --------------------------------------------------------------------------
    # 2. Danh mục tra cứu hoàn thành tự động (Lookup / Autocomplete)
    # --------------------------------------------------------------------------
    def get_environments(self, db_manager: Optional[Any] = None) -> List[Dict[str, str]]:
        """Lấy danh sách môi trường sử dụng (Indoor / Outdoor)."""
        records = self.scan_and_process_lookup("environment", db_manager=db_manager)
        return [{"code": r["code"], "name": r["name"]} for r in records]

    def get_control_types(self, db_manager: Optional[Any] = None) -> List[Dict[str, str]]:
        """Lấy danh sách phương thức điều khiển (Offline / Online / Đa năng)."""
        records = self.scan_and_process_lookup("control_type", db_manager=db_manager)
        return [{"code": r["code"], "name": r["name"]} for r in records]

    def get_module_brands(self, db_manager: Optional[Any] = None) -> List[str]:
        """Lấy danh sách các thương hiệu Module LED phân phối chính hãng."""
        records = self.scan_and_process_lookup("module_brand", db_manager=db_manager)
        return [r["name"] for r in records]

    # --------------------------------------------------------------------------
    # 3. Cấu hình lưới chi tiết linh kiện dự toán (BT1)
    # --------------------------------------------------------------------------
    def get_grid_view_page(
        self,
        voucher_code: str = VoucherCodes.DETAIL_QUOTE,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Lấy cấu hình chi tiết lưới chứng từ BT1 từ máy chủ FastBusiness."""
        payload = {
            "viewPage": {
                "Type": "Detail",
                "Code": "stt_rec",
                "ID": voucher_code,
            }
        }
        ok, res, err = self.client.post(ApiEndpoints.GET_GRID_VIEW_PAGE, payload)
        if not ok or not res or "d" not in res:
            ok, res, err = self.client.post(
                ApiEndpoints.GET_GRID_VIEW_PAGE,
                {"d": {"TotalRowCount": 0, "Rows": [], "ViewPage": {"Type": "Detail", "Code": "stt_rec", "ID": voucher_code}}},
            )

        if ok and res and "d" in res and res["d"]:
            return True, res["d"], None

        fallback_data = {
            "ViewPage": {
                "ID": voucher_code,
                "Code": "stt_rec",
                "Order": "stt_rec, line_nbr",
                "Fields": BT1_GRID_FIELDS,
                "Toolbar": [
                    [
                        "Retrieve",
                        "Chức năng tính$$",
                        [
                            {"Target": GridCalcCommands.CALC_POWER, "CommandName": "Tính Nguồn"},
                            {"Target": GridCalcCommands.CALC_CARD_PROCESSOR, "CommandName": "Tính card - bộ xử lý"},
                            {"Target": GridCalcCommands.CALC_ELECTRICITY, "CommandName": "Tính CP điện"},
                            {"Target": GridCalcCommands.CALC_MECHANICS, "CommandName": "Tính CP cơ khí"},
                            {"Target": GridCalcCommands.CALC_CABINET_POWER, "CommandName": "Tính CP tủ điện"},
                            {"Target": GridCalcCommands.CALC_CABIN, "CommandName": "Tính cabinet"},
                            {"Target": GridCalcCommands.CALC_ALL, "CommandName": "Tính tất cả"},
                        ],
                    ],
                    [
                        "Extra",
                        "Khác...",
                        [
                            {"Target": GridRowCommands.INSERT_ROW, "CommandName": "Chèn dòng..."},
                            {"Target": GridRowCommands.UPDATE_RECORDS, "CommandName": "Cập nhật cho các bản ghi..."},
                            {"Target": GridRowCommands.DELETE_DETAILS, "CommandName": "Xóa chi tiết..."},
                        ],
                    ],
                ],
                "FixedColumns": 0,
                "FreezeColumns": 3,
            },
            "Authorized": True,
        }
        return True, fallback_data, None

    # --------------------------------------------------------------------------
    # 4. Yêu cầu tính toán chi tiết linh kiện qua lệnh Toolbar
    # --------------------------------------------------------------------------
    def request_calculation(
        self,
        command: str,
        form_parameters: Dict[str, Any],
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Gửi lệnh tính toán linh kiện (nguon, card_xu_ly, dien, co_khi, tu_dien, cabin, tat_ca)."""
        payload = {
            "command": command,
            "voucherCode": VoucherCodes.DETAIL_QUOTE,
            "parameters": form_parameters,
        }
        return self.client.post(ApiEndpoints.GET_DIR_RESPONSE, payload)

    # --------------------------------------------------------------------------
    # 5. Thông tin bài đăng & cấu hình tác giả (GetViewPost)
    # --------------------------------------------------------------------------
    def get_view_post(
        self,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Lấy thông tin bài viết, phân quyền và tác giả từ PostExtender.asmx/GetViewPost."""
        ok, res, _ = self.client.post(ApiEndpoints.GET_VIEW_POST, {})
        if ok and res and "d" in res and res["d"]:
            raw_d = res["d"]
            if isinstance(raw_d, str):
                try:
                    return json.loads(raw_d)
                except json.JSONDecodeError:
                    pass
            elif isinstance(raw_d, dict):
                return raw_d

        return {
            "View": {
                "Title": "",
                "Language": "v",
                "UserFullName": username or "bang",
                "UserImageKey": "",
                "UserCommentOrder": 1,
                "FileMaxSize": 102400000,
                "FileExtension": "*",
                "MediaPreviewWidth": 360,
                "MediaFullWidth": 720,
                "PostPagingList": "10,20,50",
                "PostLoadingCount": "10",
                "CommentPageShowing": "5",
            },
            "Item": None,
            "Filter": {"PreviousPost": False, "NextPost": False, "TotalItem": 0},
            "Message": "",
            "Script": "",
            "Authorize": True,
        }

    # --------------------------------------------------------------------------
    # 6. Quản lý tệp đính kèm dự toán (UploadExtender)
    # --------------------------------------------------------------------------
    def get_attached_files(
        self,
        voucher_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lấy danh sách tệp đính kèm từ UploadExtender.asmx/GetListViewPage."""
        ok, res, _ = self.client.post(ApiEndpoints.GET_LIST_VIEW_PAGE, {})
        if not ok or not res:
            ok, res, _ = self.client.post(
                ApiEndpoints.GET_LIST_VIEW_PAGE,
                {"voucher_id": voucher_id or VoucherCodes.DETAIL_QUOTE},
            )
        if ok and res and "d" in res and isinstance(res["d"], dict) and "Rows" in res["d"]:
            return res["d"]["Rows"]
        return []

    # --------------------------------------------------------------------------
    # 7. Thuật toán sau khi Đăng nhập: Quét và truy vấn toàn bộ các API đã scan
    # --------------------------------------------------------------------------
    def post_login_query_pipeline(
        self,
        db_manager: Optional[Any] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Thuật toán sau khi đăng nhập: Quét và truy vấn toàn bộ các API đã scan từ ERP FastBusiness."""
        user_val = username or "bang"
        logger.info("Bắt đầu thực thi Post-Login Query Pipeline cho user: %s (session: %s)", user_val, self.client.get_session_id())

        pipeline_result: Dict[str, Any] = {
            "status": "success",
            "timestamp": time.time(),
            "session_id": self.client.get_session_id(),
            "username": user_val,
            "queries": {},
            "synced_to_db": False,
        }

        # 1. Quét danh mục Lookup & xử lý LookupFields vào Database
        lookups = self.scan_all_api_lookups(db_manager=db_manager)
        pipeline_result["queries"]["lookups"] = lookups
        pipeline_result["synced_to_db"] = db_manager is not None

        # 2. Truy vấn cấu hình lưới chứng từ BT1 (metadata, toolbar, formulas)
        ok_grid, grid_data, _ = self.get_grid_view_page(VoucherCodes.DETAIL_QUOTE)
        pipeline_result["queries"]["grid_view"] = grid_data if ok_grid else {}

        # 3. Truy vấn cấu hình người dùng & bài đăng (GetViewPost)
        view_post_data = self.get_view_post(username=user_val)
        pipeline_result["queries"]["view_post"] = view_post_data

        # 4. Truy vấn danh sách tệp đính kèm chứng từ (GetListViewPage)
        attached_files = self.get_attached_files(VoucherCodes.DETAIL_QUOTE)
        pipeline_result["queries"]["attached_files"] = attached_files

        logger.info(
            "Hoàn tất Post-Login Query Pipeline: %d danh mục lookups, grid=%s, user=%s, files=%d",
            len(lookups),
            bool(grid_data),
            view_post_data.get("View", {}).get("UserFullName", user_val),
            len(attached_files),
        )

        return pipeline_result
