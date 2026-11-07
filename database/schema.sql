PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,             -- module, power, card, processor, frame, service
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    environment TEXT,                   -- indoor / outdoor / both
    unit TEXT NOT NULL,
    unit_price REAL NOT NULL DEFAULT 0,
    spec_json TEXT NOT NULL DEFAULT '{}',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    ,supplier TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS saved_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quote_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_name TEXT NOT NULL,
    customer_name TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL,
    total REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    quote_number TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Nh\u00e1p',
    project_name TEXT NOT NULL DEFAULT '',
    module_code TEXT NOT NULL DEFAULT '',
    width_m REAL NOT NULL DEFAULT 0,
    height_m REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS company_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL DEFAULT 'CÔNG TY TNHH ĐIỆN TỬ TOÀN TRUNG',
    address TEXT NOT NULL DEFAULT '31 Núi Thành, Phường 13, Quận Tân Bình, TP. Hồ Chí Minh',
    phone TEXT NOT NULL DEFAULT '0903 848 111 - (028) 38 123 011',
    email TEXT NOT NULL DEFAULT 'toantrung@toantrung.com',
    website TEXT NOT NULL DEFAULT 'www.toantrung.com',
    tax_code TEXT NOT NULL DEFAULT '0304620008',
    bank_account TEXT NOT NULL DEFAULT '19020491823019 - Techcombank CN Tân Bình',
    default_vat REAL NOT NULL DEFAULT 8.0,
    default_profit REAL NOT NULL DEFAULT 20.0,
    default_warranty_months INTEGER NOT NULL DEFAULT 24,
    notes TEXT NOT NULL DEFAULT 'Báo giá có hiệu lực trong vòng 15 ngày kể từ ngày lập.',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_environment ON products(environment);
CREATE INDEX IF NOT EXISTS idx_quote_history_created_at ON quote_history(created_at);
