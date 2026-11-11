"""QuoteSheetMixin: isolated UI responsibilities; inherited by the screen coordinator.

Preserves original control construction and callbacks for migration safety.
"""
import copy
import sqlite3
import unicodedata
from typing import Any, Callable, Dict, List, Optional
import flet as ft
from database.db_manager import DBManager
from engine.calculator import CalculationInput, Calculators
from engine.exporter import QuoteExporter
from ui.components.input_panel import InputPanel
from ui.components.quote_info_card import make_info_card
from ui.components.preview_panel import PreviewPanel
from ui.views.profile_view import ProfileView


from ui.theme.tokens import UIColors

class QuoteSheetMixin:
    def _open_selected_summary_sheet(self, e=None):
        """Đẩy lên giao diện BottomSheet hiển thị các thứ người dùng đã chọn kèm khả năng điều chỉnh và Tạo báo giá mới."""
        if not self.quote_data:
            self.recalculate()

        if not self.quote_data:
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(self.message.value or "Vui lòng nhập kích thước màn hình hợp lệ để xem dự toán."),
                    bgcolor=UIColors.ERROR,
                )
                self.page.snack_bar.open = True
                self.page.update()
            return

        body_column = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=10)
        total_val_text = ft.Text("0 đ", size=22, weight=ft.FontWeight.W_800, color=UIColors.PRIMARY)
        items_count_text = ft.Text("", size=12, weight=ft.FontWeight.W_600, color=UIColors.TEXT_SECONDARY)

        def render_sheet():
            form = self.input_panel.get_values() if hasattr(self, "input_panel") else {}
            summary = self.quote_data.get("summary") or {}
            bom = self.quote_data.get("bom") or []
            pricing = self.quote_data.get("pricing") or {}

            proj_name = form.get("project_name") or "Chưa đặt tên dự án"
            cust_name = form.get("customer_name") or "Khách lẻ"
            w_m = float(form.get("width_m", 0) or 0)
            h_m = float(form.get("height_m", 0) or 0)
            size_str = f"{int(w_m*1000):,} × {int(h_m*1000):,} mm".replace(",", ".")
            total_val = pricing.get("final_total", 0)

            total_val_text.value = f"{self._money(total_val)} đ"
            items_count_text.value = f"{len(bom)} hạng mục đã chọn"

            # 1. Thẻ thông tin dự án & kích thước
            header_card = ft.Container(
                padding=ft.Padding(12, 10, 12, 10),
                bgcolor=UIColors.SURFACE_SUBTLE,
                border=ft.Border.all(1, UIColors.BORDER),
                border_radius=12,
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(ft.Icons.BUSINESS_OUTLINED, size=16, color=UIColors.PRIMARY),
                                        ft.Text(proj_name, size=14, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY),
                                    ],
                                ),
                                ft.Text(f"Khách: {cust_name}", size=12, color=UIColors.TEXT_SECONDARY),
                            ],
                        ),
                        ft.Divider(height=1, color=UIColors.BORDER),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(f"Kích thước: {size_str}", size=12, weight=ft.FontWeight.W_600, color="#334155"),
                                ft.Text(
                                    f"Module: {summary.get('n_ngang', 0)} × {summary.get('n_doc', 0)} ({summary.get('n_total', 0)} tấm)",
                                    size=12,
                                    weight=ft.FontWeight.W_600,
                                    color=UIColors.PRIMARY,
                                ),
                            ],
                        ),
                    ],
                ),
            )

            # Helper tạo card hiển thị thông tin từng mục cấu hình đã chọn kèm icon cây viết chỉnh sửa
            # Dedicated reusable component lives in ui/components/quote_info_card.py.

            # Helper mở popup dialog chỉnh sửa từng mục cấu hình
            def open_edit_dialog(title: str, controls: list, on_save_callback):
                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Container(
                                width=32,
                                height=32,
                                border_radius=8,
                                bgcolor="#EFF6FF",
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.EDIT_OUTLINED, size=18, color=UIColors.PRIMARY),
                            ),
                            ft.Text(f"Chỉnh sửa: {title}", size=15, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY),
                        ],
                    ),
                    content=ft.Container(
                        width=360,
                        content=ft.Column(
                            spacing=10,
                            tight=True,
                            scroll=ft.ScrollMode.AUTO,
                            controls=controls,
                        ),
                    ),
                    actions=[
                        ft.TextButton("Hủy", on_click=lambda e: self._close_dialog(dialog)),
                        ft.FilledButton(
                            "Lưu & Cập nhật",
                            style=ft.ButtonStyle(
                                bgcolor=UIColors.PRIMARY,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                            on_click=lambda e: (
                                on_save_callback(),
                                self._close_dialog(dialog),
                                self.recalculate(),
                                render_sheet(),
                            ),
                        ),
                    ],
                )
                if hasattr(self.page, "show_dialog"):
                    self.page.show_dialog(dialog)
                else:
                    self.page.dialog = dialog
                    dialog.open = True
                    self.page.update()

            # 1. Trình chiếu & module
            def edit_section_module(e):
                edit_env = ft.Dropdown(
                    label="Loại màn hình *",
                    value=form.get("screen_type_code") or self.input_panel.screen_type_code_for_environment(form.get("environment")),
                    options=[
                        ft.dropdown.Option(key=item.code, text=item.name)
                        for item in self.input_panel._erp_screen_types
                    ],
                    **InputPanel._dropdown_style(),
                )
                edit_disp = ft.Dropdown(
                    label="Loại trình chiếu",
                    value=form.get("display_mode", "online"),
                    options=[
                        ft.dropdown.Option(key="online", text="Trực tuyến (Online)"),
                        ft.dropdown.Option(key="offline", text="Ngoại tuyến (Offline)"),
                    ],
                    **InputPanel._dropdown_style(),
                )
                edit_brand = ft.Dropdown(
                    label="Hãng module",
                    value=form.get("m_hang_module") or "Toàn Trung",
                    options=[
                        ft.dropdown.Option("Toàn Trung"),
                        ft.dropdown.Option("Qiangli"),
                        ft.dropdown.Option("GKGD"),
                        ft.dropdown.Option("Cailiang"),
                    ],
                    **InputPanel._dropdown_style(),
                )
                modules = self.options.get("modules", [])
                edit_code = ft.Dropdown(
                    label="Mã module",
                    value=form.get("module_code"),
                    options=[
                        ft.dropdown.Option(key=m["code"], text=m.get("spec_json", {}).get("pitch", m["name"]))
                        for m in modules
                    ],
                    **InputPanel._dropdown_style(),
                )
                edit_qty = ft.TextField(
                    label="Số lượng module",
                    value=str(form.get("m_sl_module", summary.get("n_total", 34))),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    **InputPanel._field_style(),
                )

                def save_module():
                    if not self.input_panel.select_screen_type(edit_env.value):
                        return
                    self.input_panel._set_display_mode(edit_disp.value)
                    self.input_panel.module_brand_dropdown.value = edit_brand.value
                    if edit_code.value:
                        self.input_panel.module_code_dropdown.value = edit_code.value
                        self.input_panel._on_module_code_selected(None)
                    self.input_panel.m_sl_module.value = edit_qty.value

                open_edit_dialog("Trình chiếu & module", [edit_env, edit_disp, edit_brand, edit_code, edit_qty], save_module)

            env_text = form.get("screen_type_name") or "Chưa chọn"
            disp_text = "Trực tuyến (Online)" if form.get("display_mode") == "online" else "Ngoại tuyến (Offline)"
            module_brand = form.get("m_hang_module") or getattr(self.input_panel.module_brand_dropdown, "value", "Toàn Trung")
            module_obj = self._get_selected(form.get("module_code", ""), "module")
            module_code_text = module_obj.get("name") or form.get("module_code") or "Chưa chọn"
            module_qty_text = f"{form.get('m_sl_module', summary.get('n_total', 0))} tấm"

            card_display_module = make_info_card(
                "Trình chiếu & module",
                ft.Icons.GRID_VIEW_ROUNDED,
                [
                    ("Loại màn hình", env_text),
                    ("Loại trình chiếu", disp_text),
                    ("Hãng & Mã module", f"{module_brand} • {module_code_text}"),
                    ("Số lượng module", module_qty_text),
                ],
                on_edit_click=edit_section_module,
            )

            # 2. Kích thước & độ phân giải
            def edit_section_dimensions(e):
                edit_w = ft.TextField(
                    label="Số module ngang (W)",
                    value=str(getattr(self.input_panel, "num_modules_w", 8)),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    **InputPanel._field_style(),
                )
                edit_h = ft.TextField(
                    label="Số module dọc (H)",
                    value=str(getattr(self.input_panel, "num_modules_h", 4)),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    **InputPanel._field_style(),
                )

                def save_dimensions():
                    if edit_w.value and edit_w.value.strip().isdigit() and int(edit_w.value) > 0:
                        self.input_panel.num_modules_w = int(edit_w.value.strip())
                        self.input_panel.txt_modules_w.value = edit_w.value.strip()
                    if edit_h.value and edit_h.value.strip().isdigit() and int(edit_h.value) > 0:
                        self.input_panel.num_modules_h = int(edit_h.value.strip())
                        self.input_panel.txt_modules_h.value = edit_h.value.strip()
                    self.input_panel._sync_calc_display()

                open_edit_dialog("Kích thước & độ phân giải", [edit_w, edit_h], save_dimensions)

            dim_w_mm = float(form.get("width_m", 0) or 0) * 1000
            dim_h_mm = float(form.get("height_m", 0) or 0) * 1000
            dim_text = f"{int(dim_w_mm):,} × {int(dim_h_mm):,} mm".replace(",", ".")
            res_text = f"{summary.get('res_w', 0)} × {summary.get('res_h', 0)} px"
            matrix_text = f"{summary.get('n_ngang', 0)} cột (W) × {summary.get('n_doc', 0)} hàng (H)"
            area_val = (dim_w_mm * dim_h_mm) / 1_000_000
            area_text = f"{area_val:.2f} m²"

            card_dimensions = make_info_card(
                "Kích thước & độ phân giải",
                ft.Icons.STRAIGHTEN_ROUNDED,
                [
                    ("Kích thước hiển thị (W × H)", dim_text),
                    ("Độ phân giải hiển thị", res_text),
                    ("Số lượng module ma trận", matrix_text),
                    ("Diện tích hiển thị", area_text),
                ],
                on_edit_click=edit_section_dimensions,
            )

            # 3. Dự phòng & tổng module
            def edit_section_reserve(e):
                edit_res = ft.TextField(
                    label="Số module dự phòng",
                    value=str(getattr(self.input_panel, "num_reserve_modules", 2)),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    **InputPanel._field_style(),
                )

                def save_reserve():
                    if edit_res.value and edit_res.value.strip().isdigit() and int(edit_res.value) >= 0:
                        self.input_panel.num_reserve_modules = int(edit_res.value.strip())
                        self.input_panel.txt_reserve_modules.value = edit_res.value.strip()
                        self.input_panel._sync_calc_display()

                open_edit_dialog("Dự phòng & tổng module", [edit_res], save_reserve)

            installed_text = f"{summary.get('n_installed', 0)} tấm"
            reserve_text = f"{summary.get('n_reserve', 0)} tấm"
            total_mod_text = f"{summary.get('n_total', 0)} tấm"
            total_px_text = f"{summary.get('total_pixels', 0):,} px".replace(",", ".")

            card_reserve = make_info_card(
                "Dự phòng & tổng module",
                ft.Icons.LAYERS_OUTLINED,
                [
                    ("Module lắp đặt", installed_text),
                    ("Module dự phòng", reserve_text),
                    ("Tổng số module", total_mod_text),
                    ("Tổng pixel hiển thị", total_px_text),
                ],
                on_edit_click=edit_section_reserve,
            )

            # 4. Thông tin chung
            def edit_section_customer(e):
                edit_proj = ft.TextField(label="Tên dự án", value=form.get("project_name", ""), **InputPanel._field_style())
                edit_cust = ft.TextField(label="Mã / Tên khách hàng", value=form.get("customer_name", ""), **InputPanel._field_style())
                edit_phone = ft.TextField(label="Số điện thoại", value=form.get("customer_phone", ""), keyboard_type=ft.KeyboardType.PHONE, **InputPanel._field_style())

                def save_customer():
                    self.input_panel.project_name.value = edit_proj.value
                    self.input_panel.customer_name.value = edit_cust.value
                    self.input_panel.customer_phone.value = edit_phone.value

                open_edit_dialog("Thông tin chung", [edit_proj, edit_cust, edit_phone], save_customer)

            mode_text = "Nhập thủ công" if form.get("config_mode") == "manual" else "Tự động tính"

            card_customer = make_info_card(
                "Thông tin chung",
                ft.Icons.PERSON_OUTLINE,
                [
                    ("Tên dự án", proj_name),
                    ("Khách hàng", cust_name),
                    ("Số điện thoại", form.get("customer_phone") or "Chưa thiết lập"),
                    ("Chế độ tính toán", mode_text),
                ],
                on_edit_click=edit_section_customer,
            )

            # 5. Nguồn & bộ xử lý
            def edit_section_power_proc(e):
                edit_p_brand = ft.Dropdown(
                    label="Hãng nguồn",
                    value=form.get("m_hang_nguon", "CZCL"),
                    options=[
                        ft.dropdown.Option("CZCL"),
                        ft.dropdown.Option("Meanwell"),
                        ft.dropdown.Option("G-Energy"),
                        ft.dropdown.Option("Khác"),
                    ],
                    **InputPanel._dropdown_style(),
                )
                powers = self.options.get("powers", [])
                edit_p_code = ft.Dropdown(
                    label="Mã nguồn",
                    value=form.get("power_code"),
                    options=[ft.dropdown.Option(key=p["code"], text=p["name"]) for p in powers],
                    **InputPanel._dropdown_style(),
                )
                edit_p_qty = ft.TextField(
                    label="Số lượng nguồn",
                    value=str(form.get("m_sl_nguon", "4")),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    **InputPanel._field_style(),
                )
                edit_bxl_brand = ft.Dropdown(
                    label="Hãng bộ xử lý",
                    value=form.get("m_hang_bxl", "HD (Huidu)"),
                    options=[
                        ft.dropdown.Option("HD (Huidu)"),
                        ft.dropdown.Option("Novastar"),
                        ft.dropdown.Option("Colorlight"),
                        ft.dropdown.Option("Linsn"),
                    ],
                    **InputPanel._dropdown_style(),
                )
                edit_bxl_code = ft.Dropdown(
                    label="Mã bộ xử lý",
                    value=form.get("m_ma_bxl"),
                    options=list(self.input_panel.m_ma_bxl.options),
                    **InputPanel._dropdown_style(),
                )
                edit_bxl_qty = ft.TextField(
                    label="Số lượng BXL",
                    value=str(form.get("m_sl_bxl", "1")),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    **InputPanel._field_style(),
                )
                cards = self.options.get("cards", [])
                edit_card_code = ft.Dropdown(
                    label="Mã card thu",
                    value=form.get("card_code"),
                    options=[ft.dropdown.Option(key=c["code"], text=c["name"]) for c in cards],
                    **InputPanel._dropdown_style(),
                )
                edit_card_layout = ft.Dropdown(
                    label="Hình thức sắp xếp",
                    value=form.get("m_quy_cach", "Mặc định"),
                    options=list(self.input_panel.m_quy_cach.options),
                    **InputPanel._dropdown_style(),
                )
                edit_card_qty = ft.TextField(
                    label="Số lượng card",
                    value=str(form.get("m_sl_card", "2")),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    **InputPanel._field_style(),
                )

                def save_power_proc():
                    self.input_panel.power_brand_dropdown.value = edit_p_brand.value
                    if edit_p_code.value:
                        self.input_panel.power_dropdown.value = edit_p_code.value
                    self.input_panel.m_sl_nguon.value = edit_p_qty.value
                    self.input_panel.processor_brand_dropdown.value = edit_bxl_brand.value
                    if edit_bxl_code.value:
                        self.input_panel.m_ma_bxl.value = edit_bxl_code.value
                    self.input_panel.m_sl_bxl.value = edit_bxl_qty.value
                    if edit_card_code.value:
                        self.input_panel.m_ma_card.value = edit_card_code.value
                        self.input_panel.card_dropdown.value = edit_card_code.value
                    self.input_panel.m_quy_cach.value = edit_card_layout.value
                    self.input_panel.m_sl_card.value = edit_card_qty.value

                open_edit_dialog(
                    "Nguồn & bộ xử lý",
                    [
                        edit_p_brand, edit_p_code, edit_p_qty,
                        edit_bxl_brand, edit_bxl_code, edit_bxl_qty,
                        edit_card_code, edit_card_layout, edit_card_qty,
                    ],
                    save_power_proc,
                )

            power_brand = form.get("m_hang_nguon") or getattr(self.input_panel.power_brand_dropdown, "value", "CZCL")
            power_obj = self._get_selected(form.get("power_code", ""), "power")
            power_name = power_obj.get("name") or form.get("power_code") or "Chưa chọn"
            power_qty = f"{form.get('m_sl_nguon', '4')} cái"
            power_cap = getattr(self.input_panel.power_capacity_hint, "value", "") or "Theo định mức"

            bxl_brand = form.get("m_hang_bxl") or getattr(self.input_panel.processor_brand_dropdown, "value", "HD (Huidu)")
            bxl_code = form.get("m_ma_bxl", "")
            bxl_product = self.db.get_product_by_code(bxl_code) if bxl_code else None
            bxl_name = (bxl_product.get("name") if bxl_product else bxl_code) or "Chưa chọn"
            bxl_qty = f"{form.get('m_sl_bxl', '1')} cái"

            card_obj = self._get_selected(form.get("card_code", ""), "card")
            card_name = card_obj.get("name") or form.get("card_code") or "Chưa chọn"
            card_layout = form.get("m_quy_cach", "Mặc định")
            card_qty = f"{form.get('m_sl_card', '2')} cái"

            card_power_proc = make_info_card(
                "Nguồn & bộ xử lý",
                ft.Icons.SETTINGS_INPUT_COMPONENT_OUTLINED,
                [
                    ("Nguồn cấp", f"{power_brand} • {power_name} ({power_qty})"),
                    ("Công suất nguồn", power_cap),
                    ("Bộ xử lý hình ảnh", f"{bxl_brand} • {bxl_name} ({bxl_qty})"),
                    ("Card thu tín hiệu", f"{card_name} • {card_layout} ({card_qty})"),
                ],
                on_edit_click=edit_section_power_proc,
            )

            # 6. Khung & vật liệu
            def edit_section_frame(e):
                frames = self.options.get("frames", [])
                edit_frame = ft.Dropdown(
                    label="Loại khung",
                    value=form.get("frame_code"),
                    options=[ft.dropdown.Option(key=f["code"], text=f["name"]) for f in frames],
                    **InputPanel._dropdown_style(),
                )
                edit_alu = ft.Dropdown(
                    label="Alu theo khung",
                    value=form.get("m_ma_alu", "Không dùng"),
                    options=list(self.input_panel.m_ma_alu.options),
                    **InputPanel._dropdown_style(),
                )
                edit_dt = ft.TextField(
                    label="Alu diện tích (m²)",
                    value=str(form.get("m_dien_tich", "0.00")),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    **InputPanel._field_style(),
                )

                def save_frame():
                    if edit_frame.value:
                        self.input_panel.frame_dropdown.value = edit_frame.value
                    self.input_panel.m_ma_alu.value = edit_alu.value
                    self.input_panel.m_dien_tich.value = edit_dt.value

                open_edit_dialog("Khung & vật liệu", [edit_frame, edit_alu, edit_dt], save_frame)

            frame_obj = self._get_selected(form.get("frame_code", ""), "frame")
            frame_name = frame_obj.get("name") or form.get("frame_code") or "Chưa thiết lập"

            cbn_list = []
            for i in range(1, 5):
                c_code = form.get(f"m_ma_cbn{i}")
                c_qty = form.get(f"m_sl_cbn{i}", "0")
                if c_code and c_code != "NONE" and str(c_qty) not in ("0", "0.00", ""):
                    cbn_list.append(f"Cbn {i}: {c_code} ({c_qty} cái)")
            cbn_text = ", ".join(cbn_list) if cbn_list else "Theo kết cấu khung"

            alu_frame = form.get("m_ma_alu", "Không dùng")
            alu_area_val = form.get("m_dien_tich", "0.00")
            alu_area_code = form.get("m_ma_alu_dt", "Không dùng")
            alu_area_text = f"{alu_area_val} m² ({alu_area_code})"

            card_frame = make_info_card(
                "Khung & vật liệu",
                ft.Icons.CROP_FREE,
                [
                    ("Loại khung", frame_name),
                    ("Cabinet 1 – 4", cbn_text),
                    ("Alu theo khung", alu_frame),
                    ("Alu theo diện tích", alu_area_text),
                ],
                on_edit_click=edit_section_frame,
            )

            # 7. Điện & phụ trợ
            def edit_section_electric(e):
                edit_phase = ft.Dropdown(
                    label="Nguồn điện",
                    value=getattr(self.input_panel, "power_phase_val", "1pha"),
                    options=[
                        ft.dropdown.Option(key="1pha", text="1 Pha (220V)"),
                        ft.dropdown.Option(key="3pha", text="3 Pha (380V)"),
                    ],
                    **InputPanel._dropdown_style(),
                )
                edit_tu_dien = ft.Dropdown(
                    label="Loại tủ điện",
                    value=form.get("m_loai_tu_dien", "Không dùng"),
                    options=list(self.input_panel.m_loai_tu_dien.options),
                    **InputPanel._dropdown_style(),
                )
                edit_cb = ft.Dropdown(
                    label="Loại CB",
                    value=form.get("m_loai_cb", "Chưa thiết lập"),
                    options=list(self.input_panel.cb_dropdown.options),
                    **InputPanel._dropdown_style(),
                )
                edit_fan = ft.Dropdown(
                    label="Quạt 5V",
                    value=form.get("m_ma_quat5v", "Không dùng"),
                    options=list(self.input_panel.m_ma_quat5v.options),
                    **InputPanel._dropdown_style(),
                )
                edit_wire = ft.Dropdown(
                    label="Tiết diện dây",
                    value=form.get("m_tiet_dien", "Chưa thiết lập"),
                    options=list(self.input_panel.m_tiet_dien.options),
                    **InputPanel._dropdown_style(),
                )

                def save_electric():
                    self.input_panel._set_power_phase(edit_phase.value)
                    self.input_panel.m_loai_tu_dien.value = edit_tu_dien.value
                    self.input_panel.cb_dropdown.value = edit_cb.value
                    self.input_panel.m_ma_quat5v.value = edit_fan.value
                    self.input_panel.m_tiet_dien.value = edit_wire.value

                open_edit_dialog("Điện & phụ trợ", [edit_phase, edit_tu_dien, edit_cb, edit_fan, edit_wire], save_electric)

            phase_text = "1 Pha (220V)" if getattr(self.input_panel, "power_phase_val", "1pha") == "1pha" else "3 Pha (380V)"
            tu_dien_val = form.get("m_loai_tu_dien") or getattr(self.input_panel.m_loai_tu_dien, "value", "Không dùng")
            cabinet_box = f"Có tủ ({tu_dien_val})" if tu_dien_val and tu_dien_val not in ("Không dùng", "Chưa thiết lập") else "Không dùng tủ điện"
            cb_text = form.get("m_loai_cb", "Chưa chọn")
            cf_text = getattr(self.input_panel.cf_dropdown, "value", "Chưa chọn")
            fan_text = form.get("m_ma_quat5v", "Không dùng")
            wire_text = form.get("m_tiet_dien", "Chưa thiết lập")

            card_electric = make_info_card(
                "Điện & phụ trợ",
                ft.Icons.BOLT,
                [
                    ("Nguồn điện", phase_text),
                    ("Tủ điện", cabinet_box),
                    ("Thiết bị đóng cắt (CB / CF)", f"CB: {cb_text} • CF: {cf_text}"),
                    ("Quạt tản nhiệt 5V", fan_text),
                    ("Tiết diện dây cấp", wire_text),
                ],
                on_edit_click=edit_section_electric,
            )

            # 2. Điều chỉnh nhanh: Kích thước module, Module dự phòng & Chiết khấu & VAT
            cur_nw = int(getattr(self.input_panel, "num_modules_w", 8) or 8)
            cur_nh = int(getattr(self.input_panel, "num_modules_h", 4) or 4)
            cur_reserve = int(getattr(self.input_panel, "num_reserve_modules", 0) or 0)
            cur_discount = float(form.get("discount_percent", 0) or 0)
            cur_vat = float(form.get("vat_percent", 0) or 0)

            def adjust_nw(delta: int):
                self.input_panel._change_modules_w(delta)
                self.recalculate()
                render_sheet()

            def adjust_nh(delta: int):
                self.input_panel._change_modules_h(delta)
                self.recalculate()
                render_sheet()

            def adjust_reserve(delta: int):
                self.input_panel._change_reserve(delta)
                self.recalculate()
                render_sheet()

            def adjust_discount(delta: float):
                new_disc = min(100.0, max(0.0, cur_discount + delta))
                self.input_panel.discount_slider.value = new_disc
                self.recalculate()
                render_sheet()

            def adjust_vat(delta: float):
                new_vat = max(0.0, cur_vat + delta)
                self.input_panel.vat_input.value = f"{new_vat:g}"
                self.recalculate()
                render_sheet()

            adjust_card = ft.Container(
                padding=ft.Padding(12, 10, 12, 10),
                bgcolor="#EFF6FF",
                border=ft.Border.all(1, "#BFDBFE"),
                border_radius=12,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.Icon(ft.Icons.TUNE, size=15, color=UIColors.PRIMARY),
                                ft.Text("Tùy chỉnh nhanh thông số dự toán", size=12, weight=ft.FontWeight.W_700, color="#1E40AF"),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text("Module ngang (W):", size=12, color="#334155"),
                                ft.Container(
                                    border=ft.Border.all(1, UIColors.BORDER_STRONG),
                                    border_radius=8,
                                    bgcolor=ft.Colors.WHITE,
                                    content=ft.Row(
                                        spacing=0,
                                        controls=[
                                            ft.IconButton(ft.Icons.REMOVE, icon_size=15, width=28, height=28, on_click=lambda ev: adjust_nw(-1)),
                                            ft.Text(str(cur_nw), size=13, weight=ft.FontWeight.W_700, width=28, text_align=ft.TextAlign.CENTER),
                                            ft.IconButton(ft.Icons.ADD, icon_size=15, width=28, height=28, on_click=lambda ev: adjust_nw(1)),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text("Module dọc (H):", size=12, color="#334155"),
                                ft.Container(
                                    border=ft.Border.all(1, UIColors.BORDER_STRONG),
                                    border_radius=8,
                                    bgcolor=ft.Colors.WHITE,
                                    content=ft.Row(
                                        spacing=0,
                                        controls=[
                                            ft.IconButton(ft.Icons.REMOVE, icon_size=15, width=28, height=28, on_click=lambda ev: adjust_nh(-1)),
                                            ft.Text(str(cur_nh), size=13, weight=ft.FontWeight.W_700, width=28, text_align=ft.TextAlign.CENTER),
                                            ft.IconButton(ft.Icons.ADD, icon_size=15, width=28, height=28, on_click=lambda ev: adjust_nh(1)),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text("Module dự phòng:", size=12, color="#334155"),
                                ft.Container(
                                    border=ft.Border.all(1, UIColors.BORDER_STRONG),
                                    border_radius=8,
                                    bgcolor=ft.Colors.WHITE,
                                    content=ft.Row(
                                        spacing=0,
                                        controls=[
                                            ft.IconButton(ft.Icons.REMOVE, icon_size=15, width=28, height=28, on_click=lambda ev: adjust_reserve(-1)),
                                            ft.Text(str(cur_reserve), size=13, weight=ft.FontWeight.W_700, width=28, text_align=ft.TextAlign.CENTER),
                                            ft.IconButton(ft.Icons.ADD, icon_size=15, width=28, height=28, on_click=lambda ev: adjust_reserve(1)),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text("Chiết khấu (%):", size=12, color="#334155"),
                                ft.Container(
                                    border=ft.Border.all(1, UIColors.BORDER_STRONG),
                                    border_radius=8,
                                    bgcolor=ft.Colors.WHITE,
                                    content=ft.Row(
                                        spacing=0,
                                        controls=[
                                            ft.IconButton(ft.Icons.REMOVE, icon_size=15, width=28, height=28, on_click=lambda ev: adjust_discount(-1.0)),
                                            ft.Text(f"{cur_discount:g}%", size=13, weight=ft.FontWeight.W_700, width=42, text_align=ft.TextAlign.CENTER),
                                            ft.IconButton(ft.Icons.ADD, icon_size=15, width=28, height=28, on_click=lambda ev: adjust_discount(1.0)),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text("Thuế VAT (%):", size=12, color="#334155"),
                                ft.Container(
                                    border=ft.Border.all(1, UIColors.BORDER_STRONG),
                                    border_radius=8,
                                    bgcolor=ft.Colors.WHITE,
                                    content=ft.Row(
                                        spacing=0,
                                        controls=[
                                            ft.IconButton(ft.Icons.REMOVE, icon_size=15, width=28, height=28, on_click=lambda ev: adjust_vat(-1.0)),
                                            ft.Text(f"{cur_vat:g}%", size=13, weight=ft.FontWeight.W_700, width=42, text_align=ft.TextAlign.CENTER),
                                            ft.IconButton(ft.Icons.ADD, icon_size=15, width=28, height=28, on_click=lambda ev: adjust_vat(1.0)),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            )

            # 3. Linh kiện bổ sung đã chọn (Có thể điều chỉnh số lượng & xóa)
            additional_cards = []
            if hasattr(self, "input_panel") and self.input_panel.additional_items:
                for idx, add_item in enumerate(self.input_panel.additional_items):
                    n_field, q_field, p_field, r_ctrl = add_item
                    a_name = n_field.value or "Hạng mục thêm"
                    try:
                        a_qty = float(str(q_field.value or "1").replace(",", "."))
                    except ValueError:
                        a_qty = 1.0
                    try:
                        a_price = float(str(p_field.value or "0").replace(",", "."))
                    except ValueError:
                        a_price = 0.0
                    a_total = a_qty * a_price

                    def change_add_qty(item_ref=add_item, delta=1):
                        _, q_f, _, _ = item_ref
                        try:
                            old_q = float(str(q_f.value or "1").replace(",", "."))
                        except ValueError:
                            old_q = 1.0
                        new_q = max(1, old_q + delta)
                        q_f.value = f"{new_q:g}"
                        self.recalculate()
                        render_sheet()

                    def delete_add_item(item_ref=add_item):
                        self.input_panel._remove_additional_item(item_ref)
                        self.recalculate()
                        render_sheet()

                    additional_cards.append(
                        ft.Container(
                            padding=ft.Padding(10, 8, 10, 8),
                            bgcolor="#FEF3C7",
                            border=ft.Border.all(1, "#FCD34D"),
                            border_radius=10,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Row(
                                        spacing=8,
                                        expand=True,
                                        controls=[
                                            ft.Container(
                                                width=32,
                                                height=32,
                                                border_radius=8,
                                                bgcolor="#FDE68A",
                                                alignment=ft.Alignment(0, 0),
                                                content=ft.Icon(ft.Icons.ADD_BOX_OUTLINED, size=16, color="#B45309"),
                                            ),
                                            ft.Column(
                                                spacing=1,
                                                expand=True,
                                                controls=[
                                                    ft.Text(a_name, size=13, weight=ft.FontWeight.W_700, color="#92400E", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                                    ft.Text(f"Đơn giá: {self._money(a_price)} đ • Thành tiền: {self._money(a_total)} đ", size=11, color="#B45309"),
                                                ],
                                            ),
                                        ],
                                    ),
                                    ft.Row(
                                        spacing=4,
                                        controls=[
                                            ft.Container(
                                                border=ft.Border.all(1, UIColors.BORDER_STRONG),
                                                border_radius=8,
                                                bgcolor=ft.Colors.WHITE,
                                                content=ft.Row(
                                                    spacing=0,
                                                    controls=[
                                                        ft.IconButton(ft.Icons.REMOVE, icon_size=15, width=26, height=26, on_click=lambda ev, it=add_item: change_add_qty(it, -1)),
                                                        ft.Text(f"{a_qty:g}", size=12, weight=ft.FontWeight.W_700, width=26, text_align=ft.TextAlign.CENTER),
                                                        ft.IconButton(ft.Icons.ADD, icon_size=15, width=26, height=26, on_click=lambda ev, it=add_item: change_add_qty(it, 1)),
                                                    ],
                                                ),
                                            ),
                                            ft.IconButton(
                                                ft.Icons.DELETE_OUTLINE,
                                                icon_size=18,
                                                icon_color=UIColors.ERROR,
                                                tooltip="Xóa mục này",
                                                on_click=lambda ev, it=add_item: delete_add_item(it),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        )
                    )

            # 4. Danh sách linh kiện trong BOM
            bom_cards = []
            for item in bom:
                name = item.get("name", "")
                qty = item.get("qty", 0)
                unit = item.get("unit", "")
                unit_price = item.get("unit_price", 0)
                line_total = item.get("line_total", 0)
                spec = item.get("spec", "")

                name_lower = name.lower()
                icon = ft.Icons.EXTENSION_OUTLINED
                if "module" in name_lower:
                    icon = ft.Icons.GRID_VIEW
                elif "nguồn" in name_lower or "power" in name_lower:
                    icon = ft.Icons.BOLT
                elif "card" in name_lower:
                    icon = ft.Icons.MEMORY
                elif "bộ xử lý" in name_lower or "processor" in name_lower:
                    icon = ft.Icons.DEVELOPER_BOARD
                elif "khung" in name_lower or "cabinet" in name_lower:
                    icon = ft.Icons.CROP_FREE
                elif "lắp đặt" in name_lower or "thi công" in name_lower:
                    icon = ft.Icons.CONSTRUCTION
                elif "vận chuyển" in name_lower:
                    icon = ft.Icons.LOCAL_SHIPPING_OUTLINED

                bom_cards.append(
                    ft.Container(
                        padding=ft.Padding(10, 8, 10, 8),
                        bgcolor=UIColors.SURFACE_SUBTLE,
                        border=ft.Border.all(1, UIColors.BORDER),
                        border_radius=10,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    expand=True,
                                    controls=[
                                        ft.Container(
                                            width=32,
                                            height=32,
                                            border_radius=8,
                                            bgcolor=UIColors.PRIMARY_SOFT,
                                            alignment=ft.Alignment(0, 0),
                                            content=ft.Icon(icon, size=16, color=UIColors.PRIMARY),
                                        ),
                                        ft.Column(
                                            spacing=1,
                                            expand=True,
                                            controls=[
                                                ft.Text(name, size=13, weight=ft.FontWeight.W_700, color=UIColors.TEXT_PRIMARY, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                                ft.Text(f"{spec} • {self._money(unit_price)} đ/{unit}", size=11, color=UIColors.TEXT_SECONDARY),
                                            ],
                                        ),
                                    ],
                                ),
                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                    spacing=1,
                                    controls=[
                                        ft.Text(f"{qty:g} {unit}", size=12, weight=ft.FontWeight.W_600, color=UIColors.PRIMARY),
                                        ft.Text(f"{self._money(line_total)} đ", size=13, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
                                    ],
                                ),
                            ],
                        ),
                    )
                )

            # Ráp các phần lại vào body_column
            controls = [
                header_card,
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Thông tin cấu hình đã chọn:", size=13, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
                        ft.Row(
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    padding=ft.Padding(6, 2, 6, 2),
                                    bgcolor="#EFF6FF",
                                    border_radius=6,
                                    content=ft.Text("7 mục chi tiết", size=10, weight=ft.FontWeight.W_700, color=UIColors.PRIMARY),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT_OUTLINED,
                                    icon_size=16,
                                    icon_color=UIColors.PRIMARY,
                                    tooltip="Chỉnh sửa cấu hình trên form Lập dự toán",
                                    width=28,
                                    height=28,
                                    style=ft.ButtonStyle(padding=0),
                                    on_click=lambda e: self._apply_and_go_estimate(sheet),
                                ),
                            ],
                        ),
                    ],
                ),
                card_display_module,
                card_dimensions,
                card_reserve,
                card_customer,
                card_power_proc,
                card_frame,
                card_electric,
                adjust_card,
            ]
            if additional_cards:
                controls.append(ft.Text(f"Hạng mục bổ sung ({len(additional_cards)}):", size=12, weight=ft.FontWeight.W_700, color="#B45309"))
                controls.extend(additional_cards)

            controls.append(ft.Text("Danh mục thiết bị & linh kiện dự toán:", size=12, weight=ft.FontWeight.W_700, color="#475569"))
            controls.extend(bom_cards)

            body_column.controls = controls
            if hasattr(self, "page") and self.page:
                try:
                    self.page.update()
                except Exception:
                    pass

        # Dialog / BottomSheet
        sheet = ft.BottomSheet(
            show_drag_handle=True,
            draggable=True,
            scrollable=True,
            barrier_color="#99000000",
            shape=ft.RoundedRectangleBorder(radius=ft.BorderRadius(top_left=24, top_right=24, bottom_left=0, bottom_right=0)),
            content=ft.Container(
                height=min(720, int((self.page.height or 800) * 0.90)),
                bgcolor=ft.Colors.WHITE,
                border_radius=ft.BorderRadius(top_left=24, top_right=24, bottom_left=0, bottom_right=0),
                content=ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        # Header
                        ft.Container(
                            padding=ft.Padding(16, 4, 12, 10),
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Row(
                                        spacing=10,
                                        controls=[
                                            ft.Container(
                                                width=36,
                                                height=36,
                                                border_radius=10,
                                                bgcolor=UIColors.PRIMARY_SOFT,
                                                alignment=ft.Alignment(0, 0),
                                                content=ft.Icon(ft.Icons.TUNE, size=20, color=UIColors.PRIMARY),
                                            ),
                                            ft.Column(
                                                spacing=1,
                                                controls=[
                                                    ft.Text("Chi tiết cấu hình đã chọn", size=17, weight=ft.FontWeight.W_800, color=UIColors.TEXT_PRIMARY),
                                                    ft.Text("Kiểm tra, điều chỉnh thông số và tiến hành tạo báo giá", size=11, color=UIColors.TEXT_SECONDARY),
                                                ],
                                            ),
                                        ],
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CLOSE,
                                        icon_size=20,
                                        tooltip="Đóng",
                                        on_click=lambda ev: self._close_dialog(sheet),
                                    ),
                                ],
                            ),
                        ),
                        ft.Divider(height=1, color=UIColors.BORDER),
                        # Body scrollable
                        ft.Container(
                            expand=True,
                            padding=ft.Padding(16, 10, 16, 10),
                            content=body_column,
                        ),
                        # Footer with total & "Tạo báo giá mới" / "Áp dụng cấu hình & sang bảng dự toán"
                        ft.Container(
                            padding=ft.Padding(16, 12, 16, 14),
                            bgcolor=ft.Colors.WHITE,
                            border=ft.Border(top=ft.BorderSide(1, UIColors.BORDER)),
                            content=ft.Column(
                                spacing=10,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        vertical_alignment=ft.CrossAxisAlignment.END,
                                        controls=[
                                            ft.Column(
                                                spacing=1,
                                                controls=[
                                                    ft.Text("Tổng dự toán tạm tính", size=11, color=UIColors.TEXT_SECONDARY),
                                                    total_val_text,
                                                ],
                                            ),
                                            items_count_text,
                                        ],
                                    ),
                                    ft.Row(
                                        spacing=8,
                                        controls=[
                                            ft.OutlinedButton(
                                                "Áp dụng cấu hình & sang bảng dự toán",
                                                icon=ft.Icons.ARROW_FORWARD,
                                                height=46,
                                                expand=True,
                                                style=ft.ButtonStyle(
                                                    shape=ft.RoundedRectangleBorder(radius=12),
                                                    side=ft.BorderSide(1, UIColors.BORDER_STRONG),
                                                    color=UIColors.PRIMARY,
                                                ),
                                                on_click=lambda ev: self._apply_and_go_estimate(sheet),
                                            ),
                                            ft.FilledButton(
                                                "Tạo báo giá mới",
                                                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                                                height=46,
                                                expand=True,
                                                style=InputPanel._primary_button_style(),
                                                on_click=lambda ev: self._confirm_create_quote_from_sheet(sheet),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            ),
        )

        render_sheet()

        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(sheet)
        else:
            self.page.dialog = sheet
            sheet.open = True
            self.page.update()

    def _confirm_create_quote_from_sheet(self, sheet):
        self._close_dialog(sheet)
        self._create_quote_and_go_list()

    def _apply_and_go_estimate(self, sheet=None):
        if sheet:
            self._close_dialog(sheet)
        self._go_tab(1)
        if hasattr(self, "page") and self.page:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Đã áp dụng cấu hình và chuyển sang bảng dự toán linh kiện!"),
                bgcolor=UIColors.PRIMARY,
            )
            self.page.snack_bar.open = True
            self.page.update()
