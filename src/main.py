"""Entry point cho luồng Login → Home → Logout.

DEMO AUTH CHỈ DÙNG THỬ GIAO DIỆN, không dùng cho production.
Thay demo_authenticate bằng auth service gọi FastAPI qua HTTPS.
"""
from pathlib import Path
import flet as ft

from app.features.auth.screens.login_screen import show_login
from app.features.dashboard.home_screen import show_home

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


async def demo_authenticate(username: str, password: str) -> bool:
    # Cố tình chỉ dùng trong demo; tuyệt đối không hardcode mật khẩu thật.
    return username == "demo" and password == "demo123"


async def main(page: ft.Page) -> None:
    async def on_login_success(username: str) -> None:
        show_home(page, username=username, on_logout=show_login_again)

    async def show_login_again() -> None:
        page.clean()
        await show_login(
            page,
            authenticate=demo_authenticate,
            on_success=on_login_success,
        )

    await show_login_again()


if __name__ == "__main__":
    ft.run(main, assets_dir=str(ASSETS_DIR))
