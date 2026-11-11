"""Manual ERP integration smoke test (prompts for secrets, never logs them).

Run only after setting FASTBUSINESS_BASE_URL in .env and gaining access to ERP.
"""
from getpass import getpass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.fastbusiness.client import FastBusinessClient, FastBusinessError  # noqa: E402


def main():
    username = input("Tên đăng nhập FastBusiness: ").strip()
    password = getpass("Mật khẩu FastBusiness: ")
    with_client = FastBusinessClient(
        settings.FASTBUSINESS_BASE_URL,
        timeout=settings.FASTBUSINESS_TIMEOUT,
        verify_tls=settings.FASTBUSINESS_VERIFY_TLS,
    )
    try:
        if not with_client.login(username, password, settings.FASTBUSINESS_DATABASE, settings.FASTBUSINESS_UNIT):
            print("Đăng nhập thất bại")
            return 1
        print("Đăng nhập thành công")
        screen_types = with_client.get_screen_types()
        print(f"Nhận được {len(screen_types)} loại màn hình")
        for item in screen_types[:15]:
            print(f"  {item.code}: {item.name}")
        return 0
    except FastBusinessError as exc:
        print(f"Lỗi kết nối FastBusiness: {exc}")
        return 1
    finally:
        with_client.close()


if __name__ == '__main__':
    raise SystemExit(main())
