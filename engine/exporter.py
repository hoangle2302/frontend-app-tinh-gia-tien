from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


class QuoteExporter:
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.font_path = self._find_unicode_font()

    @staticmethod
    def _find_unicode_font() -> Optional[Path]:
        candidates = [
            Path(r"C:\Windows\Fonts\arial.ttf"),
            Path(r"C:\Windows\Fonts\arialuni.ttf"),
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
            Path(r"C:\Windows\Fonts\DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]
        return next((path for path in candidates if path.exists()), None)

    def export_excel(self, quote_data: Dict[str, Any]) -> str:
        file_path = self.export_dir / f"bao_gia_led_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "Báo giá"
        summary, pricing = quote_data["summary"], quote_data["pricing"]
        customer = quote_data.get("customer", {})
        self._write_excel_title(ws, "BÁO GIÁ MÀN HÌNH LED")
        details = [
            ("Số báo giá", quote_data.get("quote_number", self._temporary_quote_number())),
            ("Ngày báo giá", datetime.now().strftime("%d/%m/%Y")),
            ("Khách hàng", customer.get("name") or "Chưa cập nhật"),
            ("Dự án", customer.get("project") or "Chưa cập nhật"),
            ("Kích thước", f"{summary['w_real']:.3f}m x {summary['h_real']:.3f}m"),
            ("Độ phân giải", f"{summary['res_w']} x {summary['res_h']} px"),
            ("Diện tích", f"{summary['area_m2']:.2f} m²"),
        ]
        for row_idx, (label, value) in enumerate(details, 3):
            ws.cell(row_idx, 1, label).font = Font(bold=True)
            ws.cell(row_idx, 2, value)
        self._write_excel_summary(ws, pricing, 11)
        quote_headers = ["Hạng mục", "Thông số", "Số lượng", "Đơn vị"]
        for col, header in enumerate(quote_headers, 1):
            cell = ws.cell(20, col, header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="17A2B8")
        for row_idx, row in enumerate(quote_data["bom"], 21):
            for col, value in enumerate(
                [row["name"], row["spec"], row["qty"], row["unit"]], 1
            ):
                ws.cell(row_idx, col, value)

        bom_ws = wb.create_sheet("BOM chi tiết")
        self._write_excel_title(bom_ws, "BOM CHI TIẾT - NỘI BỘ")
        headers = ["Tên vật tư", "Thông số", "Số lượng", "Đơn vị", "Đơn giá vốn", "Thành tiền"]
        for col, header in enumerate(headers, 1):
            cell = bom_ws.cell(3, col, header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1A5FB4")
        for row_idx, row in enumerate(quote_data["bom"], 4):
            for col, value in enumerate(
                [row["name"], row["spec"], row["qty"], row["unit"], row["unit_price"], row["line_total"]], 1
            ):
                bom_ws.cell(row_idx, col, value)
        self._format_excel_columns(ws, ["A", "B", "C", "D", "E", "F"])
        self._format_excel_columns(bom_ws, ["A", "B", "C", "D", "E", "F"])
        for sheet in (ws, bom_ws):
            for row in sheet.iter_rows():
                for cell in row:
                    cell.alignment = Alignment(vertical="center", wrap_text=True)
                    if isinstance(cell.value, (int, float)) and cell.column >= 5:
                        cell.number_format = '#,##0'
        wb.save(file_path)
        return str(file_path.resolve())

    @staticmethod
    def _temporary_quote_number() -> str:
        return f"BG-{datetime.now():%Y-%m-%d-%H%M%S}"

    @staticmethod
    def _write_excel_title(ws, title: str) -> None:
        ws.merge_cells("A1:F1")
        ws["A1"] = title
        ws["A1"].font = Font(size=14, bold=True, color="1A5FB4")

    @staticmethod
    def _write_excel_summary(ws, pricing: Dict[str, Any], row: int) -> None:
        for offset, label, value in (
            (0, "Giá vốn", pricing["cost_total"]),
            (1, "Lợi nhuận", pricing["profit_value"]),
            (2, "Chiết khấu", pricing["discount_value"]),
            (3, f"VAT ({pricing['vat_percent']}%)", pricing["vat_value"]),
            (4, "TỔNG BÁO GIÁ", pricing["final_total"]),
        ):
            ws.cell(row + offset, 5, label).font = Font(bold=True)
            ws.cell(row + offset, 6, value).font = Font(bold=True)

    @staticmethod
    def _format_excel_columns(ws, columns: List[str]) -> None:
        for column in columns:
            ws.column_dimensions[column].width = 24

    def export_pdf(self, quote_data: Dict[str, Any]) -> str:
        file_path = self.export_dir / f"bao_gia_led_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=12)
        if self.font_path:
            pdf.add_font("Unicode", "", str(self.font_path))
            pdf.add_font("Unicode", "B", str(self.font_path))
            font_name = "Unicode"
        else:
            font_name = "Helvetica"
        pdf.set_font(font_name, "B", 14)
        pdf.cell(0, 10, "TOAN TRUNG - BAO GIA MAN HINH LED", new_x="LMARGIN", new_y="NEXT")
        summary, pricing = quote_data["summary"], quote_data["pricing"]
        pdf.set_font(font_name, "", 10)
        customer = quote_data.get("customer", {})
        for line in (
            f"So bao gia: {quote_data.get('quote_number', self._temporary_quote_number())}",
            f"Ngay: {datetime.now():%d/%m/%Y}",
            f"Khach hang: {customer.get('name', '') or 'Chua cap nhat'}",
            f"Du an: {customer.get('project', '') or 'Chua cap nhat'}",
            f"Kích thước thực tế: {summary['w_real']:.3f}m x {summary['h_real']:.3f}m",
            f"Độ phân giải: {summary['res_w']} x {summary['res_h']}",
            f"Tổng điểm ảnh: {summary['pixels']:,}",
        ):
            pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
        self._draw_table_header(pdf, font_name)
        for row in quote_data["bom"]:
            self._draw_table_row(pdf, font_name, [
                row["name"], row["spec"], str(row["qty"]), row["unit"],
                f"{row['unit_price']:,.0f}", f"{row['line_total']:,.0f}",
            ])
        pdf.ln(4)
        pdf.set_font(font_name, "B", 11)
        pdf.cell(0, 8, f"Gia von: {pricing['cost_total']:,.0f} VND", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Loi nhuan: {pricing['profit_value']:,.0f} VND", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"VAT: {pricing['vat_value']:,.0f} VND", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"TONG BAO GIA: {pricing['final_total']:,.0f} VND", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_name, "", 9)
        pdf.multi_cell(
            0,
            6,
            "Bang chu: " + self._number_to_words(int(pricing["final_total"])) + " dong.",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.multi_cell(
            0,
            6,
            "Hieu luc 15 ngay | Bao hanh 24 thang | Thanh toan theo thoa thuan.",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(8)
        pdf.cell(90, 8, "Dai dien Toan Trung", align="C")
        pdf.cell(90, 8, "Khach hang", align="C")
        pdf.output(str(file_path))
        return str(file_path.resolve())

    @staticmethod
    def _number_to_words(value: int) -> str:
        if value == 0:
            return "khong"
        units = ["", "mot", "hai", "ba", "bon", "nam", "sau", "bay", "tam", "chin"]
        scales = ["", "nghin", "trieu", "ty"]

        def group(number: int) -> str:
            hundred, remainder = divmod(number, 100)
            ten, unit = divmod(remainder, 10)
            words = []
            if hundred:
                words.extend([units[hundred], "tram"])
            if ten > 1:
                words.extend([units[ten], "muoi"])
                if unit:
                    words.append("lam" if unit == 5 else units[unit])
            elif ten == 1:
                words.extend(["muoi", "lam" if unit == 5 else units[unit]] if unit else ["muoi"])
            elif unit:
                if hundred:
                    words.append("linh")
                words.append("lam" if unit == 5 and ten else units[unit])
            return " ".join(words)

        parts = []
        scale_index = 0
        while value:
            value, part = divmod(value, 1000)
            if part:
                parts.insert(0, f"{group(part)} {scales[scale_index]}".strip())
            scale_index += 1
        return " ".join(parts)

    def _draw_table_header(self, pdf: FPDF, font_name: str):
        pdf.set_font(font_name, "B", 8)
        for width, title in zip([42, 34, 15, 14, 38, 42], ["Vật tư", "Thông số", "SL", "ĐV", "Đơn giá", "Thành tiền"]):
            pdf.cell(width, 8, title, border=1)
        pdf.ln()

    def _draw_table_row(self, pdf: FPDF, font_name: str, values: List[str]):
        pdf.set_font(font_name, "", 8)
        for width, value in zip([42, 34, 15, 14, 38, 42], values):
            pdf.cell(width, 8, str(value)[:28], border=1)
        pdf.ln()
