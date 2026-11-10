"""Local draft repository (stdlib only); neither cloud sync nor multi-user ERP.

The directory defaults to ~/.bao_gia_led_v5. On mobile the effective HOME and
filesystem permissions depend on the packaged runtime; validate on target device.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4


def storage_path() -> Path:
    override = os.environ.get("LED_QUOTE_DATA_FILE")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".bao_gia_led_v5" / "drafts.json"


def create_id() -> str:
    return f"BG-{datetime.now():%Y%m%d}-{uuid4().hex[:6].upper()}"


class QuoteStore:
    def __init__(self, path: Path | None = None):
        self.path = path or storage_path()

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Tệp dữ liệu bản nháp không phải danh sách.")
        if any(not isinstance(q, dict) or not isinstance(q.get("id"), str)
               or not isinstance(q.get("values"), dict) for q in data):
            raise ValueError("Tệp dữ liệu bản nháp không đúng cấu trúc.")
        return data

    def write(self, quotes: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            temporary.write_text(json.dumps(quotes, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(self.path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def upsert(self, doc: dict) -> list[dict]:
        records = self.load()
        for index, old in enumerate(records):
            if old["id"] == doc["id"]:
                records[index] = doc
                break
        else:
            records.append(doc)
        self.write(records)
        return records

    def delete(self, doc_id: str) -> list[dict]:
        records = [r for r in self.load() if r["id"] != doc_id]
        self.write(records)
        return records
