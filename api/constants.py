"""Định nghĩa các Hằng số, Endpoints, Danh mục và Cấu trúc dữ liệu quét từ ERP FastBusiness (api.txt).

Hệ thống ERP Toàn Trung:
    - Host mặc định: http://192.168.2.62
    - Mã chứng từ lập dự toán LED: BT1 (Báo giá chi tiết linh kiện LED)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ==============================================================================
# 1. BASE URL & SERVICE PATHS (Máy chủ ERP FastBusiness Toàn Trung)
# ==============================================================================
DEFAULT_API_HOST = "192.168.2.62"
DEFAULT_API_BASE_URL = f"http://{DEFAULT_API_HOST}"

SERVICE_REPORT_EXTENDER = "/AppService/FastBusiness.ReportExtenderService.asmx"
SERVICE_DATA_SERVICE = "/FastBusiness.DataService.asmx"
SERVICE_UPLOAD_EXTENDER = "/AppService/UploadExtender.asmx"
SERVICE_POST_EXTENDER = "/AppService/PostExtender.asmx"


# ==============================================================================
# 2. ENDPOINTS (Danh sách API endpoints quét từ api.txt)
# ==============================================================================
class ApiEndpoints:
    """Các Endpoint chính thức của ERP FastBusiness."""

    # Trang đăng nhập & các API khởi tạo phiên đăng nhập FastBusiness ERP
    LOGIN_PAGE = "/Main/Login.aspx"
    GET_ENTITY_DATA = "/Main/Login.aspx/GetEntityData"
    GET_UNIT_DATA = "/Main/Login.aspx/GetUnitData"
    GET_AUTH_METHOD = "/Main/Login.aspx/GetAuthenticationMethod"
    REFRESH = "/Main/Login.aspx/Refresh"
    CHALLENGE = "/Main/Login.aspx/Challenge"
    LOGIN = "/Main/Login.aspx/Login"

    # Lấy metadata cột, toolbar, script tính toán và dữ liệu lưới chi tiết voucher (BT1)
    GET_GRID_VIEW_PAGE = f"{SERVICE_REPORT_EXTENDER}/GetGridViewPage"

    # Lấy phản hồi danh mục trực tiếp
    GET_DIR_RESPONSE = f"{SERVICE_REPORT_EXTENDER}/GetDirResponse"

    # Lấy danh sách hoàn thành/gợi ý tìm kiếm (Lookup/AutoComplete)
    GET_COMPLETION_LIST = f"{SERVICE_DATA_SERVICE}/GetCompletionList"

    # Lấy danh sách tệp đính kèm trong chứng từ
    GET_LIST_VIEW_PAGE = f"{SERVICE_UPLOAD_EXTENDER}/GetListViewPage"

    # Lấy thông tin bài đăng, cấu hình giao diện và tác giả chứng từ
    GET_VIEW_POST = f"{SERVICE_POST_EXTENDER}/GetViewPost"


# ==============================================================================
# 2.1. LOGIN CONFIGURATION (Xác thực tài khoản ERP FastBusiness)
# ==============================================================================
DEFAULT_LOGIN_DATABASE = "TOANTRUNG_FBISP2421_A"
DEFAULT_LOGIN_UNIT = "CTY"
DEFAULT_LOGIN_LANGUAGE = "v"
DEFAULT_LOGIN_VALUE = "af9ac0f31b2d"
DEFAULT_LOGIN_FORCE = False
DEFAULT_LOGIN_STORAGE = True
DEFAULT_LOGIN_S = 0
SESSION_COOKIE_NAME = "FastBusiness.SessionId"

# Dữ liệu mặc định từ GetEntityData và GetUnitData
DEFAULT_ENTITY_ROWS = [["01", "Công ty", DEFAULT_LOGIN_DATABASE]]
DEFAULT_UNIT_ROWS = [[DEFAULT_LOGIN_UNIT, "CÔNG TY", "COMPANY"]]


def hash_password_md5(password: str) -> str:
    """Băm mật khẩu người dùng sang mã MD5 32 ký tự theo chuẩn FastBusiness."""
    import hashlib

    raw = (password or "").strip()
    if len(raw) == 32 and all(c in "0123456789abcdefABCDEF" for c in raw):
        return raw.lower()
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def hash_fastbusiness_password(password: str, challenge_value: str) -> str:
    """Thuật toán băm mật khẩu chuẩn của FastBusiness LoginExtender.js:
    $ = MD5(password)
    r = MD5(l + $)  với l là mã challenge (value) từ /Main/Login.aspx/Challenge
    """
    import hashlib

    raw = password or ""
    val = (challenge_value or "").strip()
    step1 = hashlib.md5(raw.encode("utf-8")).hexdigest().lower()
    if not val:
        return step1
    return hashlib.md5((val + step1).encode("utf-8")).hexdigest().lower()


def generate_password_hash_candidates(password: str, value: Optional[str] = None) -> List[str]:
    """Sinh danh sách mã băm MD5 theo chuẩn FastBusiness LoginExtender."""
    raw = (password or "").strip()
    val = (value or DEFAULT_LOGIN_VALUE).strip()
    candidates: List[str] = []

    def _add(h: str):
        if h and h not in candidates:
            candidates.append(h)

    # Nếu đầu vào đã là chuỗi MD5 32 ký tự hex (như trong request trace), ưu tiên thử trực tiếp đầu tiên
    if len(raw) == 32 and all(c in "0123456789abcdefABCDEF" for c in raw):
        _add(raw.lower())

    # Công thức chính thức trong LoginExtender.js: r = MD5(l + MD5(password))
    if val:
        _add(hash_fastbusiness_password(raw, val))

    _add(hash_password_md5(raw))
    return candidates


# ==============================================================================
# 3. VOUCHER & GRID METADATA (Chứng từ dự toán BT1)
# ==============================================================================
class VoucherCodes:
    """Mã loại chứng từ trong FastBusiness."""

    DETAIL_QUOTE = "BT1"  # Báo giá chi tiết linh kiện màn hình LED


GRID_ORDER_BY = "stt_rec, line_nbr"
GRID_ID = "BT1"


# ==============================================================================
# 4. TOOLBAR COMMANDS (Các lệnh tính toán nhanh trên thanh công cụ)
# ==============================================================================
class GridCalcCommands:
    """Mã lệnh tính toán tự động trong menu 'Chức năng tính$$' của lưới BT1."""

    CALC_POWER = "nguon"  # Tính Nguồn
    CALC_CARD_PROCESSOR = "card_xu_ly"  # Tính card - bộ xử lý
    CALC_ELECTRICITY = "dien"  # Tính CP điện
    CALC_MECHANICS = "co_khi"  # Tính CP cơ khí
    CALC_CABINET_POWER = "tu_dien"  # Tính CP tủ điện
    CALC_CABIN = "cabin"  # Tính cabinet
    CALC_ALL = "tat_ca"  # Tính tất cả


class GridRowCommands:
    """Mã lệnh xử lý dòng trong menu 'Khác...'."""

    INSERT_ROW = "05"  # Chèn dòng...
    UPDATE_RECORDS = "10"  # Cập nhật cho các bản ghi...
    DELETE_DETAILS = "20"  # Xóa chi tiết...


# ==============================================================================
# 5. LOOKUP / ENUMS (Danh mục tra cứu quét từ GetCompletionList)
# ==============================================================================
class EnvironmentTypes(str, Enum):
    """Môi trường lắp đặt màn hình LED (indoor_yn)."""

    INDOOR = "1"
    OUTDOOR = "2"


ENVIRONMENT_LABELS = {
    EnvironmentTypes.INDOOR: "Indoor (Trong nhà)",
    EnvironmentTypes.OUTDOOR: "Outdoor (Ngoài trời)",
}


class ControlTypes(str, Enum):
    """Phương thức điều khiển hệ thống (phan_loai)."""

    OFFLINE = "0"
    ONLINE = "1"
    HYBRID = "2"


CONTROL_TYPE_LABELS = {
    ControlTypes.OFFLINE: "Offline (Bộ nhớ trong / USB)",
    ControlTypes.ONLINE: "Online (Thời gian thực / Máy tính)",
    ControlTypes.HYBRID: "Offline + Online (Đa năng)",
}


class ModuleBrands(str, Enum):
    """Các hãng sản xuất Module LED quét từ ERP Toàn Trung."""

    GKGD = "GKGD"
    LAMPRO = "LAMPRO"
    LONGRUN = "LONGRUN"
    QIANGLI = "QIANGLI"
    SKYWORTH = "SKYWORTH"


# ==============================================================================
# 6. COMPONENT TYPES (Phân loại linh kiện 'loai' trong lưới BT1)
# ==============================================================================
class ComponentTypes(str, Enum):
    """Phân loại nhóm vật tư trong lưới chứng từ BT1."""

    MODULE = "module"
    POWER = "nguon"
    CARD = "card"
    PROCESSOR = "xu_ly"
    CABIN = "cabin"
    ELECTRICITY = "dien"
    MECHANICS = "co_khi"
    CABINET_POWER = "tu_dien"


# Ánh xạ giữa mã loại ERP sang category trong bảng SQLite nội bộ
ERP_TO_LOCAL_CATEGORY_MAP = {
    ComponentTypes.MODULE.value: "module",
    ComponentTypes.POWER.value: "power",
    ComponentTypes.CARD.value: "card",
    ComponentTypes.PROCESSOR.value: "processor",
    ComponentTypes.CABIN.value: "frame",
    ComponentTypes.MECHANICS.value: "frame",
    ComponentTypes.ELECTRICITY.value: "service",
    ComponentTypes.CABINET_POWER.value: "service",
}

LOCAL_TO_ERP_CATEGORY_MAP = {
    "module": ComponentTypes.MODULE.value,
    "power": ComponentTypes.POWER.value,
    "card": ComponentTypes.CARD.value,
    "processor": ComponentTypes.PROCESSOR.value,
    "frame": ComponentTypes.MECHANICS.value,
    "service": ComponentTypes.ELECTRICITY.value,
}


# ==============================================================================
# 7. FIELD SCHEMAS (Cấu trúc cột dữ liệu lưới BT1)
# ==============================================================================
BT1_GRID_FIELDS = [
    {
        "name": "ma_vt",
        "header_text": "Mã linh kiện",
        "type": "String",
        "width": 100,
        "max_length": 16,
        "visible": True,
        "readonly": False,
        "item_style": "AutoComplete",
        "item_controller": "zComponent",
        "item_reference": "dien_giai",
    },
    {
        "name": "dien_giai",
        "header_text": "Tên linh kiện",
        "type": "String",
        "width": 300,
        "visible": True,
        "readonly": True,
    },
    {
        "name": "dvt",
        "header_text": "Đvt",
        "type": "String",
        "width": 0,
        "visible": False,
        "item_style": "AutoComplete",
        "item_controller": "UOMItem",
        "item_reference": "ten_dvt",
    },
    {
        "name": "ten_dvt",
        "header_text": "Tên ĐVT",
        "type": "String",
        "width": 0,
        "visible": False,
        "readonly": True,
    },
    {
        "name": "he_so",
        "header_text": "Hệ số",
        "type": "Decimal",
        "width": 0,
        "visible": False,
        "default": 1.0,
    },
    {
        "name": "so_luong",
        "header_text": "Số lượng",
        "type": "Decimal",
        "width": 80,
        "visible": True,
        "readonly": False,
    },
    {
        "name": "gia_nt",
        "header_text": "Giá",
        "type": "Decimal",
        "width": 100,
        "visible": True,
        "readonly": False,
    },
    {
        "name": "tien_nt",
        "header_text": "Tiền",
        "type": "Decimal",
        "width": 100,
        "visible": True,
        "readonly": False,
    },
    {
        "name": "ghi_chu",
        "header_text": "Ghi chú",
        "type": "String",
        "width": 0,
        "visible": False,
    },
    {
        "name": "gia",
        "header_text": "Giá VND",
        "type": "Decimal",
        "width": 0,
        "visible": False,
    },
    {
        "name": "tien",
        "header_text": "Tiền VND",
        "type": "Decimal",
        "width": 0,
        "visible": False,
    },
    {
        "name": "quy_cach",
        "header_text": "Quy cách",
        "type": "String",
        "width": 0,
        "visible": False,
    },
    {
        "name": "ma_vv",
        "header_text": "Vụ việc",
        "type": "String",
        "width": 80,
        "visible": True,
        "item_style": "AutoComplete",
        "item_controller": "Job",
        "item_reference": "ten_vv",
    },
    {
        "name": "ten_vv",
        "header_text": "Tên vụ việc",
        "type": "String",
        "width": 0,
        "visible": False,
        "readonly": True,
    },
    {
        "name": "nhieu_dvt",
        "header_text": "Nhiều ĐVT",
        "type": "Boolean",
        "width": 0,
        "visible": False,
    },
    {
        "name": "stt_rec",
        "header_text": "STT Rec",
        "type": "String",
        "width": 0,
        "visible": False,
        "is_primary": True,
    },
    {
        "name": "stt_rec0",
        "header_text": "STT Rec 0",
        "type": "String",
        "width": 0,
        "visible": False,
        "is_primary": True,
    },
    {
        "name": "loai",
        "header_text": "Loại linh kiện",
        "type": "String",
        "width": 0,
        "visible": False,
    },
    {
        "name": "line_nbr",
        "header_text": "Số dòng",
        "type": "Int32",
        "width": 0,
        "visible": False,
    },
    {
        "name": "ct_yn",
        "header_text": "Tính tổng Y/N",
        "type": "Int32",
        "width": 0,
        "visible": False,
        "default": 0,
    },
]


# ==============================================================================
# 8. FORM PARAMETERS LIST (Tham số form truyền trong request tính toán)
# ==============================================================================
# Chuỗi tham số được trích xuất nguyên bản từ api.txt (dòng 105 - 118)
RAW_FORM_PARAMETERS = (
    "ngay_ct, indoor_yn, hang_nguon, ma_module, kt_hien_thi_w, kt_hien_thi_h, "
    "so_module_w, so_module_h, do_phan_giai_w, do_phan_giai_h, tong_pixel, "
    "cong_suat, day, mcb, mccb, hang_bxl, khung_sat, vao_hdmi_14, vao_hdmi_20, "
    "vao_dvi, vao_vga, vao_cvbs, vao_usb, vao_dp4k, vao_sdi, vao_fiber, vao_genlock, "
    "ra_lan, ra_dvi, ra_fiber, ra_khung_hinh, ra_audio, ma_nguon, phan_loai, "
    "nguon_dien, tu_dien, ma_alu, ma_quat5v, ra_hdmi, ra_hub75, vao_usbcfg, vao_lan, "
    "vao_wifi, vao_gps, vao_light, vao_temp, vao_4g, vao_bonho, vao_sim, "
    "check_vao_hdmi_14, check_vao_hdmi_20, check_vao_dvi, check_vao_vga, check_vao_cvbs, "
    "check_vao_usb, check_vao_dp4k, check_vao_sdi, check_vao_fiber, check_vao_genlock, "
    "check_ra_lan, check_ra_dvi, check_ra_fiber, check_ra_khung_hinh, check_ra_audio, "
    "check_ra_hdmi, check_ra_hub75, check_vao_usbcfg, check_vao_lan, check_vao_wifi, "
    "check_vao_gps, check_vao_light, check_vao_temp, check_vao_4g, check_vao_bonho, "
    "check_vao_sim, check_nguon_dien_1pha, check_nguon_dien_3pha, check_tu_dien, "
    "loai_tu_dien, loai_cb, tiet_dien, hang_module, m_hang_module, m_ma_module, "
    "m_hang_nguon, m_ma_nguon, m_hang_bxl, m_ma_bxl, m_ma_card, m_quy_cach, "
    "m_ma_cbn1, m_ma_cbn2, m_ma_cbn3, m_ma_cbn4, m_ma_alu, m_ma_quat5v, "
    "m_loai_tu_dien, m_loai_cb, m_tiet_dien, m_tu_dien, m_nguon_dien, "
    "m_check_nguon_dien_1pha, m_check_nguon_dien_3pha, m_sl_module, m_sl_nguon, "
    "m_sl_bxl, m_sl_card, m_sl_cbn1, m_sl_cbn2, m_sl_cbn3, m_sl_cbn4, sl_module1, "
    "m_check_tu_dien, ma_alu_dt, dien_tich, m_ma_alu_dt, m_dien_tich"
)

# Danh sách danh từ các tham số chuẩn hóa (list of str)
FORM_PARAMETERS_LIST: List[str] = [p.strip() for p in RAW_FORM_PARAMETERS.split(",")]


# ==============================================================================
# 9. DEFAULT HEADERS & TIMEOUT
# ==============================================================================
DEFAULT_HEADERS: Dict[str, str] = {
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "*/*",
    "Accept-Language": "vi-VN,vi;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

DEFAULT_TIMEOUT_SECONDS: int = 8


# ==============================================================================
# 10. LOOKUP FIELDS & DATABASE MAPPINGS (Ánh xạ LookupFields trỏ tới DB)
# ==============================================================================
LOOKUP_FIELD_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "environment": {
        "target_table": "products",
        "target_field": "environment",
        "default_lookup_fields": ["code", "environment"],
        "field_transform": {
            "1": "indoor",
            "2": "outdoor",
        },
    },
    "control_type": {
        "target_table": "products",
        "target_field": "control_type",
        "default_lookup_fields": ["code", "control_type"],
        "field_transform": {
            "0": "offline",
            "1": "online",
            "2": "hybrid",
        },
    },
    "module_brand": {
        "target_table": "products",
        "target_field": "supplier",
        "default_lookup_fields": ["code", "supplier"],
    },
    "component": {
        "target_table": "products",
        "target_field": "code",
        "default_lookup_fields": [
            "code",
            "name",
            "dvt",
            "unit_price",
            "category",
            "supplier",
        ],
    },
}


