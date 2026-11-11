"""Small, testable HTTPX client based on test_33.py.

Does not import Flet or SQLite. One httpx.Client preserves the server-side
session cookies across the login sequence and completion-list query.
"""
from dataclasses import dataclass
import hashlib
import re
from typing import Any, Mapping

import httpx


class FastBusinessError(RuntimeError):
    """A remote request or protocol validation failed."""


@dataclass(frozen=True)
class ScreenType:
    code: str
    name: str


def hash_challenge(password: str, challenge: str) -> str:
    """Exactly the legacy ERP challenge hash described in the user sample.

    Required by the existing ERP protocol; not a modern password hashing scheme.
    """
    first = hashlib.md5(password.encode("utf-8")).hexdigest().lower()
    return hashlib.md5((challenge + first).encode("utf-8")).hexdigest().lower()


def parse_screen_types(rows: list[Any]) -> list[ScreenType]:
    """Convert FastBusiness d.Rows into code/label pairs.

    Supports the actual ERP result [["1", "Indoor"], ["2", "Outdoor"]]
    and the object-shaped rows used by other GetCompletionList instances.
    Only the ERP response supplies options; no hardcoded sample choices.
    """
    result: list[ScreenType] = []
    seen_codes: set[str] = set()
    for row in rows:
        if isinstance(row, (list, tuple)) and len(row) >= 2:
            code, name = row[0], row[1]
        elif isinstance(row, dict):
            code = next((row[k] for k in (
                "code", "Code", "ma", "Ma", "value", "Value", "ma_loai_mh", "ma_loai", "id"
            ) if row.get(k) is not None), None)
            name = next((row[k] for k in (
                "name", "Name", "ten", "Ten", "text", "Text", "ten_loai_mh", "ten_loai", "description"
            ) if row.get(k) is not None), None)
        else:
            continue
        code = str(code).strip() if code is not None else ""
        name = str(name).strip() if name is not None else ""
        if code and name and code not in seen_codes:
            result.append(ScreenType(code=code, name=name))
            seen_codes.add(code)
    return result


class FastBusinessClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 15,
        verify_tls: bool = True,
        transport: httpx.BaseTransport | None = None,
    ):
        if not base_url:
            raise FastBusinessError("Chưa cấu hình FASTBUSINESS_BASE_URL")
        if not base_url.startswith(("http://", "https://")):
            raise FastBusinessError("FASTBUSINESS_BASE_URL phải bắt đầu bằng http:// hoặc https://")
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            verify=verify_tls,
            transport=transport,
            follow_redirects=False,
            headers={
                "Accept": "*/*",
                "Accept-Language": "vi-VN,vi;q=0.9",
                "Content-Type": "application/json; charset=UTF-8",
                "Origin": self.base_url,
                "User-Agent": "ToanTrung-Flet/1.0",
            },
        )
        self.authenticated = False
        self.screen_cookie = ""

    def close(self) -> None:
        self.client.close()

    def _post(self, path: str, payload: Mapping | None = None, *, referer: str = "/Main/Login.aspx") -> dict:
        try:
            response = self.client.post(
                path,
                json=payload,
                headers={"Referer": self.base_url + referer},
            )
            response.raise_for_status()
            obj = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise FastBusinessError("Không thể kết nối hoặc đọc phản hồi FastBusiness") from exc
        if not isinstance(obj, dict):
            raise FastBusinessError("FastBusiness trả về dữ liệu không hợp lệ")
        return obj

    def login(self, username: str, password: str, database: str, unit: str = "CTY") -> bool:
        """GetEntityData → GetUnitData → Refresh → Challenge → Login."""
        self.authenticated = False
        self.screen_cookie = ""
        if not username.strip() or not password:
            raise FastBusinessError("Vui lòng nhập tài khoản và mật khẩu")
        self._post("/Main/Login.aspx/GetEntityData")
        self._post("/Main/Login.aspx/GetUnitData", {"u": username, "d": database})
        self._post("/Main/Login.aspx/Refresh")
        challenge = self._post("/Main/Login.aspx/Challenge").get("d")
        if not isinstance(challenge, str) or not challenge:
            raise FastBusinessError("Máy chủ không trả về challenge hợp lệ")
        result = self._post("/Main/Login.aspx/Login", {
            "user": username,
            "password": hash_challenge(password, challenge),
            "database": database,
            "unit": unit,
            "language": "v",
            "value": challenge,
            "force": True,
            "storage": True,
            "s": 0,
        })
        self.authenticated = result.get("d") is True
        return self.authenticated

    def get_cookie_from_page(self) -> str:
        if not self.authenticated:
            raise FastBusinessError("Cần đăng nhập trước khi lấy cookie dữ liệu")
        for path in ("/Main/zCostingSheet.aspx", "/Main/Default.aspx"):
            try:
                r = self.client.get(path, headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": self.base_url + "/Main/Login.aspx",
                })
                if r.status_code != 200:
                    continue
                m = re.search(r'"cookie"\s*:\s*"([^"\r\n]+)"', r.text)
                if m:
                    self.screen_cookie = m.group(1)
                    return self.screen_cookie
            except httpx.HTTPError:
                continue
        raise FastBusinessError("Không tìm thấy cookie trong trang tính giá")

    def get_screen_type_rows(self) -> list[Any]:
        """Request zdmloaimh using the cookie embedded in the post-login page."""
        cookie = self.screen_cookie or self.get_cookie_from_page()
        payload = {
            "type": 2,
            "prefixText": "",
            "count": 10,
            "language": "v",
            "controller": "zdmloaimh",
            "cookie": cookie,
            "pageItemEnd": "",
            "variable": None,
            "valueField": None,
            "textField": None,
            "dataTable": None,
            "keyFilter": "status = 1",
            "keyValid": "1 = 1",
            "check": False,
            "orderField": None,
            "lookupPageIndex": -1,
            "lookupRefresh": False,
            "filter": [],
            "sortExpression": None,
            "element": None,
        }
        data = self._post(
            "/FastBusiness.DataService.asmx/GetCompletionList",
            payload,
            referer="/Main/zCostingSheet.aspx",
        )
        d = data.get("d")
        if not isinstance(d, dict) or not isinstance(d.get("Rows"), list):
            raise FastBusinessError("GetCompletionList không trả về d.Rows dạng danh sách")
        return d["Rows"]  # [['1', 'Indoor'], ['2', 'Outdoor']]

    def get_screen_types(self) -> list[ScreenType]:
        return parse_screen_types(self.get_screen_type_rows())
