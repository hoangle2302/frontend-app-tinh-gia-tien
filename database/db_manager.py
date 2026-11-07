import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class DBManager:
    def __init__(self, db_path: Optional[str] = None):
        base_dir = Path(__file__).resolve().parent.parent
        self.db_path = db_path or str(base_dir / "bom_led.db")
        self.schema_path = Path(__file__).resolve().parent / "schema.sql"

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        schema_sql = self.schema_path.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(schema_sql)
            self._migrate_schema(conn)
            conn.commit()
        self.seed_mock_data()

    @staticmethod
    def _migrate_schema(conn: sqlite3.Connection) -> None:
        """Bổ sung cột cho các database cũ mà không làm mất dữ liệu."""
        migrations = {
            "products": {
                "supplier": "TEXT NOT NULL DEFAULT ''",
            },
            "quote_history": {
                "quote_number": "TEXT NOT NULL DEFAULT ''",
                "status": "TEXT NOT NULL DEFAULT 'Nh\\u00e1p'",
                "project_name": "TEXT NOT NULL DEFAULT ''",
                "module_code": "TEXT NOT NULL DEFAULT ''",
                "width_m": "REAL NOT NULL DEFAULT 0",
                "height_m": "REAL NOT NULL DEFAULT 0",
            },
        }
        for table, columns in migrations.items():
            existing = {
                row["name"]
                for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
            }
            for name, definition in columns.items():
                if name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

        rows = conn.execute(
            "SELECT id, created_at FROM quote_history WHERE quote_number = '' OR quote_number IS NULL"
        ).fetchall()
        for row in rows:
            year = str(row["created_at"] or "")[:4] or "2026"
            conn.execute(
                "UPDATE quote_history SET quote_number = ? WHERE id = ?",
                (f"BG-{year}-{row['id']:03d}", row["id"]),
            )
        conn.execute(
            "UPDATE quote_history SET status = ? WHERE status = ?",
            ("Nh\u00e1p", r"Nh\u005cu00e1p"),
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_quote_history_quote_number "
            "ON quote_history(quote_number)"
        )

    def seed_mock_data(self) -> None:
        with self._connect() as conn:
            products = [
                # Modules
                {
                    "category": "module",
                    "code": "M-P1.25-IN",
                    "name": "LED Module P1.25 Indoor",
                    "environment": "indoor",
                    "unit": "pcs",
                    "unit_price": 680000,
                    "spec_json": {
                        "pitch": "P1.25",
                        "width_mm": 320,
                        "height_mm": 160,
                        "pixel_w": 256,
                        "pixel_h": 128,
                        "max_current_a": 3.8,
                        "refresh_rate_hz": 3840,
                    },
                },
                {
                    "category": "module",
                    "code": "M-P2-IN",
                    "name": "LED Module P2 Indoor",
                    "environment": "indoor",
                    "unit": "pcs",
                    "unit_price": 520000,
                    "spec_json": {
                        "pitch": "P2",
                        "width_mm": 320,
                        "height_mm": 160,
                        "pixel_w": 160,
                        "pixel_h": 80,
                        "max_current_a": 3.8,
                        "refresh_rate_hz": 3840,
                    },
                },
                {
                    "category": "module",
                    "code": "M-P2.5-IN",
                    "name": "LED Module P2.5 Indoor",
                    "environment": "indoor",
                    "unit": "pcs",
                    "unit_price": 420000,
                    "spec_json": {
                        "pitch": "P2.5",
                        "width_mm": 320,
                        "height_mm": 160,
                        "pixel_w": 128,
                        "pixel_h": 64,
                        "max_current_a": 3.5,
                        "refresh_rate_hz": 3840,
                    },
                },
                {
                    "category": "module",
                    "code": "M-P3-IN",
                    "name": "LED Module P3 Indoor",
                    "environment": "indoor",
                    "unit": "pcs",
                    "unit_price": 330000,
                    "spec_json": {
                        "pitch": "P3",
                        "width_mm": 192,
                        "height_mm": 192,
                        "pixel_w": 64,
                        "pixel_h": 64,
                        "max_current_a": 2.8,
                        "refresh_rate_hz": 3840,
                    },
                },
                {
                    "category": "module",
                    "code": "M-P4-OUT",
                    "name": "LED Module P4 Outdoor",
                    "environment": "outdoor",
                    "unit": "pcs",
                    "unit_price": 510000,
                    "spec_json": {
                        "pitch": "P4",
                        "width_mm": 320,
                        "height_mm": 160,
                        "pixel_w": 80,
                        "pixel_h": 40,
                        "max_current_a": 4.2,
                        "refresh_rate_hz": 1920,
                    },
                },
                {
                    "category": "module",
                    "code": "M-P5-OUT",
                    "name": "LED Module P5 Outdoor",
                    "environment": "outdoor",
                    "unit": "pcs",
                    "unit_price": 450000,
                    "spec_json": {
                        "pitch": "P5",
                        "width_mm": 320,
                        "height_mm": 160,
                        "pixel_w": 64,
                        "pixel_h": 32,
                        "max_current_a": 3.6,
                        "refresh_rate_hz": 1920,
                    },
                },
                {
                    "category": "module",
                    "code": "M-P10-OUT",
                    "name": "LED Module P10 Outdoor",
                    "environment": "outdoor",
                    "unit": "pcs",
                    "unit_price": 390000,
                    "spec_json": {
                        "pitch": "P10",
                        "width_mm": 320,
                        "height_mm": 160,
                        "pixel_w": 32,
                        "pixel_h": 16,
                        "max_current_a": 3.2,
                        "refresh_rate_hz": 1920,
                    },
                },
                {
                    "category": "module",
                    "code": "M-P2.5-OUT",
                    "name": "LED Module P2.5 Outdoor",
                    "environment": "outdoor",
                    "unit": "pcs",
                    "unit_price": 580000,
                    "spec_json": {
                        "pitch": "P2.5",
                        "width_mm": 320,
                        "height_mm": 160,
                        "pixel_w": 128,
                        "pixel_h": 64,
                        "max_current_a": 4.8,
                        "refresh_rate_hz": 3840,
                    },
                },
                # Power supplies
                {
                    "category": "power",
                    "code": "PS-5V40A",
                    "name": "Power Supply 5V40A",
                    "environment": "both",
                    "unit": "pcs",
                    "unit_price": 290000,
                    "spec_json": {"voltage": 5, "max_current_a": 40},
                },
                {
                    "category": "power",
                    "code": "PS-5V60A",
                    "name": "Power Supply 5V60A",
                    "environment": "both",
                    "unit": "pcs",
                    "unit_price": 410000,
                    "spec_json": {"voltage": 5, "max_current_a": 60},
                },
                # Receiving cards
                {
                    "category": "card",
                    "code": "CARD-NOVA-MRV336",
                    "name": "Novastar MRV336",
                    "environment": "both",
                    "unit": "pcs",
                    "unit_price": 1450000,
                    "spec_json": {"brand": "Novastar", "capacity_pixels": 650000},
                },
                {
                    "category": "card",
                    "code": "CARD-HD-R712",
                    "name": "HD R712",
                    "environment": "both",
                    "unit": "pcs",
                    "unit_price": 950000,
                    "spec_json": {"brand": "HD", "capacity_pixels": 450000},
                },
                {
                    "category": "card",
                    "code": "CARD-LINSN-RV908",
                    "name": "Linsn RV908",
                    "environment": "both",
                    "unit": "pcs",
                    "unit_price": 1050000,
                    "spec_json": {"brand": "Linsn", "capacity_pixels": 520000},
                },
                # Video processors
                {
                    "category": "processor",
                    "code": "VP-MID",
                    "name": "Video Processor Mid Range",
                    "environment": "both",
                    "unit": "pcs",
                    "unit_price": 16500000,
                    "spec_json": {"min_pixels": 0, "max_pixels": 1300000, "tier": "mid"},
                },
                {
                    "category": "processor",
                    "code": "VP-HIGH",
                    "name": "Video Processor High End",
                    "environment": "both",
                    "unit": "pcs",
                    "unit_price": 28900000,
                    "spec_json": {"min_pixels": 2300001, "max_pixels": 10000000, "tier": "high"},
                },
                # Frame options
                {
                    "category": "frame",
                    "code": "FRAME-ALU-CAST",
                    "name": "Cabinet Nhom Duc",
                    "environment": "both",
                    "unit": "m2",
                    "unit_price": 2100000,
                    "spec_json": {"type": "Cabinet nhom duc"},
                },
                {
                    "category": "frame",
                    "code": "FRAME-STEEL-ALU",
                    "name": "Khung Sat Op Alu",
                    "environment": "both",
                    "unit": "m2",
                    "unit_price": 1250000,
                    "spec_json": {"type": "Khung sat op alu"},
                },
                # Services
                {
                    "category": "service",
                    "code": "SERVICE-INSTALL",
                    "name": "Thi cong lap dat",
                    "environment": "both",
                    "unit": "m2",
                    "unit_price": 350000,
                    "spec_json": {},
                },
                {
                    "category": "service",
                    "code": "SERVICE-TRANSPORT",
                    "name": "Van chuyen",
                    "environment": "both",
                    "unit": "job",
                    "unit_price": 1500000,
                    "spec_json": {},
                },
            ]

            conn.executemany(
                """
                INSERT OR IGNORE INTO products(category, code, name, environment, unit, unit_price, spec_json)
                VALUES(:category, :code, :name, :environment, :unit, :unit_price, :spec_json)
                """,
                [
                    {
                        **item,
                        "spec_json": json.dumps(item["spec_json"], ensure_ascii=True),
                    }
                    for item in products
                ],
            )
            conn.commit()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        data["spec_json"] = json.loads(data.get("spec_json") or "{}")
        return data

    def list_products(self, category: Optional[str] = None, environment: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM products WHERE is_active = 1"
        params: List[Any] = []

        if category:
            sql += " AND category = ?"
            params.append(category)
        if environment and environment in {"indoor", "outdoor"}:
            sql += " AND (environment = ? OR environment = 'both')"
            params.append(environment)

        sql += " ORDER BY category, name"

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_product_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE code = ? AND is_active = 1",
                (code,),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def save_configuration(self, name: str, payload: Dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO saved_configurations(name, payload_json) VALUES(?, ?)",
                (name, json.dumps(payload, ensure_ascii=True)),
            )
            conn.commit()

    def list_configurations(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM saved_configurations ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_configuration(self, configuration_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM saved_configurations WHERE id = ?", (configuration_id,)
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["payload"] = json.loads(data.pop("payload_json"))
        return data

    def save_quote_history(
        self,
        quote_name: str,
        customer_name: str,
        payload: Dict[str, Any],
        total: float,
        status: str = "Nh\u00e1p",
    ) -> int:
        year = str(__import__("datetime").datetime.now().year)
        with self._connect() as conn:
            next_number = conn.execute(
                "SELECT COUNT(*) + 1 FROM quote_history WHERE quote_number LIKE ?",
                (f"BG-{year}-%",),
            ).fetchone()[0]
            input_data = payload
            cursor = conn.execute(
                """
                INSERT INTO quote_history(
                    quote_name, customer_name, payload_json, total, quote_number,
                    status, project_name, module_code, width_m, height_m
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quote_name,
                    customer_name,
                    json.dumps(payload, ensure_ascii=True),
                    float(total),
                    f"BG-{year}-{next_number:03d}",
                    status,
                    input_data.get("project_name", ""),
                    input_data.get("module_code", ""),
                    float(input_data.get("width_m") or 0),
                    float(input_data.get("height_m") or 0),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def list_quote_history(
        self, search: str = "", status: str = "all"
    ) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if search.strip():
            clauses.append("(customer_name LIKE ? OR project_name LIKE ? OR quote_number LIKE ?)")
            term = f"%{search.strip()}%"
            params.extend([term, term, term])
        if status != "all":
            clauses.append("status = ?")
            params.append(status)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM quote_history{where} ORDER BY created_at DESC, id DESC",
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def update_quote_status(self, history_id: int, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE quote_history SET status = ? WHERE id = ?",
                (status, history_id),
            )
            conn.commit()

    def get_quote_history(self, history_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM quote_history WHERE id = ?", (history_id,)
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["payload"] = json.loads(data.pop("payload_json"))
        return data

    def delete_quote_history(self, history_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM quote_history WHERE id = ?", (history_id,))
            conn.commit()

    def create_product(self, product: Dict[str, Any]) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO products
                    (category, code, name, environment, unit, unit_price, spec_json, supplier)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product["category"],
                    product["code"],
                    product["name"],
                    product.get("environment", "both"),
                    product.get("unit", "pcs"),
                    float(product.get("unit_price", 0)),
                    json.dumps(product.get("spec_json", {}), ensure_ascii=True),
                    product.get("supplier", ""),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def update_product(self, code: str, product_data: Dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE products 
                SET name = ?, category = ?, unit = ?, unit_price = ?, supplier = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE code = ?
                """,
                (
                    product_data["name"],
                    product_data["category"],
                    product_data.get("unit", "pcs"),
                    float(product_data.get("unit_price", 0)),
                    product_data.get("supplier", ""),
                    code,
                ),
            )
            conn.commit()

    def update_product_price(self, code: str, unit_price: float) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE products SET unit_price = ?, updated_at = CURRENT_TIMESTAMP WHERE code = ?",
                (float(unit_price), code),
            )
            conn.commit()

    def delete_product(self, code: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE products SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE code = ?",
                (code,),
            )
            conn.commit()
