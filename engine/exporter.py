from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Font


class QuoteExporter:
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.font_path = self._find_unicode_font()

    @staticmethod
    def _find_unicode_font() -> Optional[Path]:
        candidates = [
            Path(r"C:\Windows\Fonts\arial.ttf"),
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
            Path(r"C:\Windows\Fonts\DejaVuSans.ttf"),
        ]
        return next((path for path in candidates if path.exists()), None)

    def export_excel(self, quote_data: Dict[str, Any]) -> str:
        file_path = self.export_dir / f"bao_gia_led_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "Báo giá BOM"
        ws["A1"] = "BÁO GIÁ VẬT TƯ MÀN HÌNH LED"
        ws["A1"].font = Font(size=14, bold=True)
        summary, pricing = quote_data["summary"], quote_data["pricing"]
        ws["A3"], ws["B3"] = "Kích thước thực tế", f"{summary['w_real']:.3f}m x {summary['h_real']:.3f}m"
        ws["A4"], ws["B4"] = "Độ phân giải", f"{summary['res_w']} x {summary['res_h']}"
        headers = ["Tên vật tư", "Thông số", "Số lượng", "Đơn vị", "Đơn giá", "Thành tiền"]
        for col, header in enumerate(headers, 1):
            ws.cell(6, col, header).font = Font(bold=True)
        for row_idx, row in enumerate(quote_data["bom"], 7):
            for col, value in enumerate(
                [row["name"], row["spec"], row["qty"], row["unit"], row["unit_price"], row["line_total"]], 1
            ):
                ws.cell(row_idx, col, value)
        end = 7 + len(quote_data["bom"])
        for offset, label, value in (
            (1, "Tạm tính", pricing["sub_total"]),
            (2, f"Chiết khấu ({pricing['discount_percent']}%)", pricing["discount_value"]),
            (3, "Tổng thanh toán", pricing["final_total"]),
        ):
            ws.cell(end + offset, 5, label).font = Font(bold=True)
            ws.cell(end + offset, 6, value).font = Font(bold=True)
        for col in "ABCDEF":
            ws.column_dimensions[col].width = 24
        wb.save(file_path)
        return str(file_path.resolve())

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
        pdf.cell(0, 10, "BÁO GIÁ VẬT TƯ MÀN HÌNH LED", new_x="LMARGIN", new_y="NEXT")
        summary, pricing = quote_data["summary"], quote_data["pricing"]
        pdf.set_font(font_name, "", 10)
        for line in (
            f"Khách hàng: {quote_data.get('customer', {}).get('name', '') or 'Chưa cập nhật'}",
            f"Dự án: {quote_data.get('customer', {}).get('project', '') or 'Chưa cập nhật'}",
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
        pdf.cell(0, 8, f"Tạm tính: {pricing['sub_total']:,.0f} VNĐ", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Chiết khấu: -{pricing['discount_value']:,.0f} VNĐ", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Tổng thanh toán: {pricing['final_total']:,.0f} VNĐ", new_x="LMARGIN", new_y="NEXT")
        pdf.output(str(file_path))
        return str(file_path.resolve())

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
