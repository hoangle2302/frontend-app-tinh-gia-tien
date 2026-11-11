"""FastBusiness-only auth service; each Flet page owns a private HTTP session."""
from dataclasses import dataclass, field
from app.config import settings
from .client import FastBusinessClient, FastBusinessError, ScreenType


@dataclass
class AuthResult:
    success: bool
    message: str
    screen_types: list[ScreenType] = field(default_factory=list)
    screen_types_warning: str = ""


class AuthService:
    """No offline mode. Success requires a positive FastBusiness login reply."""
    def __init__(self):
        self.client: FastBusinessClient | None = None
        self.screen_types: list[ScreenType] = []

    def login(self, username: str, password: str, database: str, unit: str) -> AuthResult:
        self.close()
        username, database, unit = username.strip(), database.strip(), unit.strip()
        if not username or not password or not database or not unit:
            return AuthResult(False, "Vui lòng nhập đầy đủ tên đăng nhập, mật khẩu, công ty và đơn vị")
        try:
            client = FastBusinessClient(
                settings.FASTBUSINESS_BASE_URL,
                timeout=settings.FASTBUSINESS_TIMEOUT,
                verify_tls=settings.FASTBUSINESS_VERIFY_TLS,
            )
        except FastBusinessError as exc:
            return AuthResult(False, str(exc))
        try:
            if not client.login(username, password, database, unit):
                client.close()
                return AuthResult(False, "FastBusiness từ chối đăng nhập. Kiểm tra tài khoản, mật khẩu và đơn vị.")
            self.client = client
            try:
                self.screen_types = client.get_screen_types()  # parses get_screen_type_rows() into code/label pairs
            except FastBusinessError as exc:
                # Authentication is real and succeeded; the catalogue is an independent request.
                return AuthResult(True, "Đăng nhập FastBusiness thành công", [], str(exc))
            return AuthResult(True, "Đăng nhập FastBusiness thành công", self.screen_types)
        except FastBusinessError as exc:
            client.close()
            return AuthResult(False, str(exc))

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
        self.screen_types = []
