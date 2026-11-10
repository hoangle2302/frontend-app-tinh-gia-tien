"""Tìm nhanh dòng code chứa chữ hiển thị trên UI (không phân biệt hoa/thường, không phân biệt dấu).

Cách dùng (chạy ở thư mục gốc dự án):
    python tools/find_ui.py "loại màn hình"
    python tools/find_ui.py loai man hinh        # không dấu cũng tìm được
    python tools/find_ui.py --all "vat"          # tìm cả trong engine/, database/, auth/

Kết quả dạng:  đường_dẫn:dòng  [hàm/class chứa dòng đó]  nội dung
Bấm Ctrl+Click vào đường_dẫn:dòng trong terminal VS Code/PyCharm để nhảy tới code.
"""
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIRS = ["ui", "main.py"]
ALL_DIRS = ["ui", "engine", "database", "auth", "main.py"]
DEF_RE = re.compile(r"^\s*(?:async\s+)?(def|class)\s+(\w+)")


def normalize(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn").lower()


def iter_files(names):
    for name in names:
        path = ROOT / name
        if path.is_file():
            yield path
        elif path.is_dir():
            yield from sorted(p for p in path.rglob("*.py") if "__pycache__" not in p.parts)


def main():
    args = sys.argv[1:]
    use_all = "--all" in args
    args = [a for a in args if a != "--all"]
    if not args:
        print(__doc__)
        return
    query = normalize(" ".join(args))
    hits = 0
    for file in iter_files(ALL_DIRS if use_all else DEFAULT_DIRS):
        current = ""
        for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
            match = DEF_RE.match(line)
            if match:
                current = f"{match.group(1)} {match.group(2)}"
            if query in normalize(line):
                rel = file.relative_to(ROOT).as_posix()
                print(f"{rel}:{number}  [{current or 'module'}]  {line.strip()}")
                hits += 1
    print(f"\n{hits} kết quả cho '{' '.join(args)}'")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()

