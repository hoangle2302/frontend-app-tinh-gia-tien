"""API Client giao tiếp HTTP với hệ thống FastBusiness ERP."""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple

from api.constants import (
    DEFAULT_API_BASE_URL,
    DEFAULT_HEADERS,
    DEFAULT_TIMEOUT_SECONDS,
    SESSION_COOKIE_NAME,
)

logger = logging.getLogger(__name__)


class FastBusinessApiClient:
    """Client gửi yêu cầu HTTP (REST / ASMX WebService) tới máy chủ FastBusiness."""

    # Cookie jar dùng chung cho toàn bộ ứng dụng để duy trì phiên FastBusiness.SessionId
    _shared_cookies: Dict[str, str] = {}

    def __init__(
        self,
        base_url: str = DEFAULT_API_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = dict(DEFAULT_HEADERS)
        if headers:
            self.headers.update(headers)
        # Sử dụng chung bộ nhớ cookie với toàn bộ hệ thống
        self.cookies = FastBusinessApiClient._shared_cookies

    def set_session_id(self, session_id: str):
        """Thiết lập FastBusiness.SessionId vào cookie jar dùng chung."""
        if session_id:
            FastBusinessApiClient._shared_cookies[SESSION_COOKIE_NAME] = session_id
            self.cookies[SESSION_COOKIE_NAME] = session_id

    def get_session_id(self) -> Optional[str]:
        """Lấy giá trị FastBusiness.SessionId hiện tại."""
        return self.cookies.get(SESSION_COOKIE_NAME) or FastBusinessApiClient._shared_cookies.get(SESSION_COOKIE_NAME)

    def clear_session(self):
        """Xóa toàn bộ cookie và phiên làm việc."""
        self.cookies.clear()
        FastBusinessApiClient._shared_cookies.clear()

    def _prepare_headers(self, endpoint: str) -> Dict[str, str]:
        """Tạo headers hoàn chỉnh bao gồm Origin, Referer và Cookie theo mẫu chuẩn của FastBusiness."""
        headers = dict(self.headers)
        headers["Origin"] = self.base_url

        if "Login" in endpoint:
            headers["Referer"] = f"{self.base_url}/Main/Login.aspx"
        else:
            headers["Referer"] = f"{self.base_url}/Main/Sys.aspx"

        all_cookies = dict(FastBusinessApiClient._shared_cookies)
        all_cookies.update(self.cookies)
        if all_cookies:
            cookie_str = "; ".join(f"{k}={v}" for k, v in all_cookies.items())
            headers["Cookie"] = cookie_str

        return headers

    def _process_response_cookies(self, response_headers: Any):
        """Trích xuất và lưu trữ cookie từ Set-Cookie trong phản hồi HTTP."""
        if not response_headers:
            return

        cookie_list = []
        if hasattr(response_headers, "get_all"):
            cookie_list = response_headers.get_all("Set-Cookie") or []
        elif hasattr(response_headers, "getlist"):
            cookie_list = response_headers.getlist("Set-Cookie") or []
        else:
            raw_c = response_headers.get("Set-Cookie")
            if raw_c:
                cookie_list = [raw_c]

        for item in cookie_list:
            if not item:
                continue
            first_part = item.split(";")[0].strip()
            if "=" in first_part:
                c_name, c_val = first_part.split("=", 1)
                clean_name = c_name.strip()
                clean_val = c_val.strip()
                self.cookies[clean_name] = clean_val
                FastBusinessApiClient._shared_cookies[clean_name] = clean_val

    def is_reachable(self) -> bool:
        """Kiểm tra máy chủ ERP FastBusiness có đang phản hồi hay không."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/Main/Login.aspx",
                headers={"User-Agent": self.headers.get("User-Agent", "FastBusinessLedApp/1.0")},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=2) as response:
                self._process_response_cookies(response.headers)
                return response.status < 500
        except urllib.error.HTTPError as exc:
            return exc.code < 500
        except Exception:
            return False

    def post(
        self,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Gửi yêu cầu HTTP POST JSON tới endpoint.

        Returns:
            (success: bool, data: Optional[dict], error_message: Optional[str])
        """
        full_url = f"{self.base_url}/{endpoint.lstrip('/')}"
        json_data = json.dumps(payload if payload is not None else {}).encode("utf-8")
        headers = self._prepare_headers(endpoint)

        req = urllib.request.Request(
            full_url,
            data=json_data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                self._process_response_cookies(response.headers)
                raw_body = response.read().decode("utf-8")
                try:
                    parsed = json.loads(raw_body)
                    return True, parsed, None
                except json.JSONDecodeError as exc:
                    return False, None, f"Phản hồi không phải JSON hợp lệ: {exc}"
        except urllib.error.HTTPError as exc:
            if hasattr(exc, "headers"):
                self._process_response_cookies(exc.headers)

            body_str = ""
            detail_msg = ""
            try:
                body_str = exc.read().decode("utf-8", errors="ignore")
                if body_str:
                    try:
                        err_json = json.loads(body_str)
                        if isinstance(err_json, dict) and "Message" in err_json:
                            detail_msg = f" - Chi tiết: {err_json['Message']}"
                    except Exception:
                        detail_msg = f" - Nội dung: {body_str[:120]}"
            except Exception:
                pass

            err_msg = f"HTTP Error {exc.code}: {exc.reason}{detail_msg}"
            logger.info("API POST %s kết quả: %s", full_url, err_msg)
            return False, None, err_msg
        except urllib.error.URLError as exc:
            err_msg = f"Lỗi kết nối tới {full_url}: {exc.reason}"
            logger.info("Không thể kết nối ERP: %s", err_msg)
            return False, None, err_msg
        except Exception as exc:
            err_msg = f"Lỗi ngoại lệ: {str(exc)}"
            logger.error("Lỗi khi gọi API: %s", err_msg)
            return False, None, err_msg

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Gửi yêu cầu HTTP GET tới endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if params:
            query_str = urllib.parse.urlencode(params)
            url = f"{url}?{query_str}"

        headers = self._prepare_headers(endpoint)
        req = urllib.request.Request(
            url,
            headers=headers,
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                self._process_response_cookies(response.headers)
                raw_body = response.read().decode("utf-8")
                try:
                    parsed = json.loads(raw_body)
                    return True, parsed, None
                except json.JSONDecodeError:
                    return True, {"raw": raw_body}, None
        except Exception as exc:
            return False, None, str(exc)
