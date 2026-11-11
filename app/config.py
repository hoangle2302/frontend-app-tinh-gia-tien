"""Settings for an ERP-connected installation; no authentication bypass exists."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    APP_TITLE = "TOÀN TRUNG - Báo giá Màn hình LED"
    DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "bom_led.db"))
    DEFAULT_VAT = float(os.getenv("DEFAULT_VAT", "8"))
    DEFAULT_PROFIT = float(os.getenv("DEFAULT_PROFIT", "20"))

    # Authentication always calls the real FastBusiness server.
    FASTBUSINESS_BASE_URL = os.getenv("FASTBUSINESS_BASE_URL", "").strip().rstrip("/")
    FASTBUSINESS_DATABASE = os.getenv("FASTBUSINESS_DATABASE", "TOANTRUNG_FBISP2421_A").strip()
    FASTBUSINESS_UNIT = os.getenv("FASTBUSINESS_UNIT", "CTY").strip()
    FASTBUSINESS_TIMEOUT = float(os.getenv("FASTBUSINESS_TIMEOUT", "15"))
    FASTBUSINESS_VERIFY_TLS = os.getenv("FASTBUSINESS_VERIFY_TLS", "true").strip().lower() == "true"


settings = Settings()
