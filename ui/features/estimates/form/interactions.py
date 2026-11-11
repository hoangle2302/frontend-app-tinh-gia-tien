"""FormInteractionsMixin: isolated UI responsibilities; inherited by the screen coordinator.

Preserves original control construction and callbacks for migration safety.
"""
import math
from typing import Any, Callable, Dict, List
import flet as ft


from ui.theme.tokens import UIColors

class FormInteractionsMixin:
    def _set_mode(self, mode: str):
        self.config_mode = mode
        is_auto = mode == "auto"

        # Tab button style
        self.mode_btn_auto.bgcolor = UIColors.PRIMARY if is_auto else ft.Colors.WHITE
        self.mode_btn_auto.border = None if is_auto else ft.Border.all(1, UIColors.BORDER)
        self.mode_btn_auto.content.controls[0].color = ft.Colors.WHITE if is_auto else UIColors.TEXT_SECONDARY
        self.mode_btn_auto.content.controls[1].color = ft.Colors.WHITE if is_auto else UIColors.TEXT_SECONDARY

        self.mode_btn_manual.bgcolor = ft.Colors.WHITE if is_auto else UIColors.PRIMARY
        self.mode_btn_manual.border = ft.Border.all(1, UIColors.BORDER) if is_auto else None
        self.mode_btn_manual.content.controls[0].color = UIColors.TEXT_SECONDARY if is_auto else ft.Colors.WHITE
        self.mode_btn_manual.content.controls[1].color = UIColors.TEXT_SECONDARY if is_auto else ft.Colors.WHITE

        # Cập nhật mô tả chế độ
        if is_auto:
            self.mode_description.value = "Nhập số module; kích thước và độ phân giải được tính từ thông số module đã lưu."
            self.general_mode_tag.value = "Tự động tính*"
            self.general_warning_title.value = "Chờ cấu hình định mức"
            self.general_warning_desc.value = "Cần thông số kỹ thuật và định mức để tự tính. Hãng, mã và loại vẫn do bạn chọn; không tự chọn linh kiện."
            self.reserve_note_text.value = (
                "Module lắp = số cột × số hàng. Tổng module gồm dự phòng. "
                "Tổng pixel hiển thị không tính module dự phòng."
            )
        else:
            self.mode_description.value = "Tự nhập thông số và định mức; kiểm tra lại trước khi áp dụng."
            self.general_mode_tag.value = "Nhập thủ công"
            self.general_warning_title.value = "Kiểm tra thông số trước khi áp dụng"
            self.general_warning_desc.value = "Tự nhập thông số và định mức. Các mục chưa có dữ liệu được để trống, không suy đoán giá trị."
            self.reserve_note_text.value = "Tổng module gồm module dự phòng. Tổng pixel hiển thị không tính module dự phòng."

        # Cập nhật các badge tag
        tag_text = "Tự tính" if is_auto else "Nhập tay"
        for tag in [self.tag_w_mm, self.tag_w_px, self.tag_h_mm, self.tag_h_px, self.tag_installed, self.tag_total_mod, self.tag_total_px]:
            tag.content.value = tag_text

        # Bật/tắt chế độ read_only và icon bút chì (edit)
        is_read_only = is_auto
        fields_with_suffix = [
            (self.calc_w_mm, "mm"),
            (self.calc_w_px, "px"),
            (self.calc_h_mm, "mm"),
            (self.calc_h_px, "px"),
            (self.calc_total_pixels, "px"),
        ]
        for field, unit in fields_with_suffix:
            field.read_only = is_read_only
            field.border = self._input_border(UIColors.BORDER if is_read_only else UIColors.BORDER_STRONG)
            field.bgcolor = UIColors.SURFACE_SUBTLE if is_read_only else ft.Colors.TRANSPARENT
            if is_read_only:
                field.suffix = ft.Text(unit, size=12, color=UIColors.TEXT_SECONDARY)
            else:
                field.suffix = ft.Row(
                    tight=True,
                    spacing=4,
                    controls=[
                        ft.Text(unit, size=12, color=UIColors.TEXT_SECONDARY),
                        ft.Icon(ft.Icons.EDIT_OUTLINED, size=14, color=UIColors.PRIMARY),
                    ],
                )

        plain_fields = [
            self.calc_installed_modules,
            self.calc_total_modules,
            self.power_capacity_hint,
            self.alu_hint,
            self.area_hint,
            self.fan_hint,
            self.wire_hint,
            self.cabinet_hint,
        ]
        for field in plain_fields:
            field.read_only = is_read_only
            field.border = self._input_border(UIColors.BORDER if is_read_only else UIColors.BORDER_STRONG)
            field.bgcolor = UIColors.SURFACE_SUBTLE if is_read_only else ft.Colors.TRANSPARENT
            if is_read_only:
                field.suffix = None
                if field in [self.power_capacity_hint, self.alu_hint, self.area_hint, self.fan_hint, self.wire_hint, self.cabinet_hint]:
                    field.hint_text = "Chờ cấu hình định mức"
                    field.value = ""
            else:
                field.suffix = ft.Icon(ft.Icons.EDIT_OUTLINED, size=14, color=UIColors.PRIMARY)
                if field in [self.power_capacity_hint, self.alu_hint, self.area_hint, self.fan_hint, self.wire_hint, self.cabinet_hint]:
                    field.hint_text = "Chưa thiết lập"

        if is_auto:
            self._sync_calc_display()

        self._trigger_change(None)
        if getattr(self, "_Control__page", None):
            self.page.update()

    def _set_display_mode(self, mode: str):
        self.display_mode_val = mode
        self.display_mode.value = mode
        is_online = mode == "online"
        self.btn_online.bgcolor = UIColors.PRIMARY_SOFT if is_online else ft.Colors.WHITE
        self.btn_online.border = ft.Border.all(1.5, UIColors.PRIMARY) if is_online else ft.Border.all(1, UIColors.BORDER_STRONG)
        self.btn_online.content.controls[0].icon = ft.Icons.RADIO_BUTTON_CHECKED if is_online else ft.Icons.RADIO_BUTTON_UNCHECKED
        self.btn_online.content.controls[0].color = UIColors.PRIMARY if is_online else UIColors.TEXT_SECONDARY
        self.btn_online.content.controls[1].color = UIColors.PRIMARY if is_online else UIColors.TEXT_SECONDARY

        self.btn_offline.bgcolor = ft.Colors.WHITE if is_online else UIColors.PRIMARY_SOFT
        self.btn_offline.border = ft.Border.all(1, UIColors.BORDER_STRONG) if is_online else ft.Border.all(1.5, UIColors.PRIMARY)
        self.btn_offline.content.controls[0].icon = ft.Icons.RADIO_BUTTON_UNCHECKED if is_online else ft.Icons.RADIO_BUTTON_CHECKED
        self.btn_offline.content.controls[0].color = UIColors.TEXT_SECONDARY if is_online else UIColors.PRIMARY
        self.btn_offline.content.controls[1].color = UIColors.TEXT_SECONDARY if is_online else UIColors.PRIMARY
        self._trigger_change(None)
        if getattr(self, "_Control__page", None):
            self.page.update()

    def _set_env_mode(self, env: str):
        """Keep ERP selection and module filtering synchronized with the calculator."""
        if env not in ("indoor", "outdoor"):
            return
        code = self.screen_type_code_for_environment(env)
        if code is None:
            # No matching option from ERP: do not silently create a fake choice.
            return
        self.erp_screen_types_dropdown.value = code
        self.env_mode_val = env
        self.environment.value = env
        self._filter_modules_by_env(env)
        self._trigger_change(None)
        if getattr(self, "_Control__page", None):
            self.page.update()

    def _set_power_phase(self, phase: str):
        self.power_phase_val = phase
        is_1pha = phase == "1pha"
        self.btn_1pha.bgcolor = UIColors.PRIMARY_SOFT if is_1pha else ft.Colors.WHITE
        self.btn_1pha.border = ft.Border.all(1.5, UIColors.PRIMARY) if is_1pha else ft.Border.all(1, UIColors.BORDER_STRONG)
        self.btn_1pha.content.controls[0].icon = ft.Icons.RADIO_BUTTON_CHECKED if is_1pha else ft.Icons.RADIO_BUTTON_UNCHECKED
        self.btn_1pha.content.controls[0].color = UIColors.PRIMARY if is_1pha else UIColors.TEXT_SECONDARY
        self.btn_1pha.content.controls[1].color = UIColors.PRIMARY if is_1pha else UIColors.TEXT_SECONDARY

        self.btn_3pha.bgcolor = ft.Colors.WHITE if is_1pha else UIColors.PRIMARY_SOFT
        self.btn_3pha.border = ft.Border.all(1, UIColors.BORDER_STRONG) if is_1pha else ft.Border.all(1.5, UIColors.PRIMARY)
        self.btn_3pha.content.controls[0].icon = ft.Icons.RADIO_BUTTON_UNCHECKED if is_1pha else ft.Icons.RADIO_BUTTON_CHECKED
        self.btn_3pha.content.controls[0].color = UIColors.TEXT_SECONDARY if is_1pha else UIColors.PRIMARY
        self.btn_3pha.content.controls[1].color = UIColors.TEXT_SECONDARY if is_1pha else UIColors.PRIMARY

        if hasattr(self, "m_check_1pha"):
            self.m_check_1pha.value = is_1pha
        if hasattr(self, "m_check_3pha"):
            self.m_check_3pha.value = not is_1pha

        if getattr(self, "_Control__page", None):
            self.page.update()

    def _on_m_pha_changed(self, e):
        if e.control == self.m_check_1pha and self.m_check_1pha.value:
            self.m_check_3pha.value = False
            self._set_power_phase("1pha")
        elif e.control == self.m_check_3pha and self.m_check_3pha.value:
            self.m_check_1pha.value = False
            self._set_power_phase("3pha")
        elif not self.m_check_1pha.value and not self.m_check_3pha.value:
            self.m_check_1pha.value = True
            self._set_power_phase("1pha")
        self._trigger_change(e)

    def _on_m_hang_module_selected(self, e):
        self._trigger_change(e)

    def _on_m_hang_nguon_selected(self, e):
        self._trigger_change(e)

    def _on_m_hang_bxl_selected(self, e):
        self._trigger_change(e)

    def _on_manual_calc_clicked(self, e):
        self._trigger_change(e)

    def _init_manual_options(self):
        processors = self.options.get("processors", [])
        self.m_ma_bxl.options = [
            ft.dropdown.Option(key=p.get("code", str(p)), text=p.get("name", str(p)))
            for p in processors
        ]
        if self.m_ma_bxl.options and not self.m_ma_bxl.value:
            self.m_ma_bxl.value = self.m_ma_bxl.options[0].key

        cards = self.options.get("cards", [])
        self.m_ma_card.options = [
            ft.dropdown.Option(key=c.get("code", str(c)), text=c.get("name", str(c)))
            for c in cards
        ]
        if self.m_ma_card.options and not self.m_ma_card.value:
            self.m_ma_card.value = self.m_ma_card.options[0].key

        frames = self.options.get("frames", [])
        cbn_options = [ft.dropdown.Option(key="NONE", text="Không dùng")] + [
            ft.dropdown.Option(key=f.get("code", str(f)), text=f.get("name", str(f)))
            for f in frames
        ]
        for cbn in [self.m_ma_cbn1, self.m_ma_cbn2, self.m_ma_cbn3, self.m_ma_cbn4]:
            cbn.options = list(cbn_options)
            cbn.value = "NONE"
        if len(frames) > 0:
            self.m_ma_cbn1.value = frames[0].get("code")

    def _filter_modules_by_env(self, env: str):
        modules = [m for m in self.options.get("modules", []) if m.get("environment") in {env, "both"}]
        self.module_code_dropdown.options = [
            ft.dropdown.Option(key=m["code"], text=m.get("spec_json", {}).get("pitch", m["name"]))
            for m in modules
        ]
        if modules:
            if not any(m["code"] == self.module_code_dropdown.value for m in modules):
                self.module_code_dropdown.value = modules[0]["code"]
                self.pitch_dropdown.value = modules[0]["code"]
        else:
            self.module_code_dropdown.value = None
            self.pitch_dropdown.value = None
        self._sync_calc_display()

    def _init_module_options(self):
        modules = self.options.get("modules", [])
        for widget, products in (
            (self.module_brand_dropdown, modules),
            (self.power_brand_dropdown, self.options.get("powers", [])),
            (self.processor_brand_dropdown, self.options.get("processors", [])),
        ):
            brands = sorted({str(item.get("spec_json", {}).get("brand") or item.get("supplier") or "").strip()
                             for item in products} - {""})
            widget.options = [ft.dropdown.Option(brand) for brand in brands]
            widget.value = brands[0] if brands else None
        self.module_code_dropdown.options = [
            ft.dropdown.Option(key=m["code"], text=m.get("spec_json", {}).get("pitch", m["name"]))
            for m in modules
        ]
        # Keep the previous selection when the inventory is refreshed.
        default_mod = next((m for m in modules if m["code"] == self.module_code_dropdown.value), None)
        default_mod = default_mod or (modules[0] if modules else None)
        self.module_code_dropdown.value = default_mod["code"] if default_mod else None
        self.pitch_dropdown.value = default_mod["code"] if default_mod else None
        # Screen type is chosen by the user from FastBusiness, never inferred from a module.

        powers = self.options.get("powers", [])
        self.power_dropdown.options = [ft.dropdown.Option(key=item["code"], text=item["name"]) for item in powers]
        selected = self.power_dropdown.value
        self.power_dropdown.value = selected if any(item["code"] == selected for item in powers) else (powers[0]["code"] if powers else None)

        frames = self.options.get("frames", [])
        self.frame_dropdown.options = [ft.dropdown.Option(key=item["code"], text=item["name"]) for item in frames]
        selected = self.frame_dropdown.value
        self.frame_dropdown.value = selected if any(item["code"] == selected for item in frames) else (frames[0]["code"] if frames else None)

        cards = self.options.get("cards", [])
        self.card_dropdown.options = [ft.dropdown.Option(key=item["code"], text=item["name"]) for item in cards]
        selected = self.card_dropdown.value
        self.card_dropdown.value = selected if any(item["code"] == selected for item in cards) else (cards[0]["code"] if cards else None)

    def _get_current_module(self) -> Dict:
        code = self.module_code_dropdown.value
        for m in self.options.get("modules", []):
            if m["code"] == code:
                return m
        return {}

    def _on_module_code_selected(self, e):
        mod = self._get_current_module()
        self.pitch_dropdown.value = mod.get("code")
        self._sync_calc_display()
        self._trigger_change(e)

    def _change_modules_w(self, delta: int):
        self.num_modules_w = max(1, self.num_modules_w + delta)
        self.txt_modules_w.value = str(self.num_modules_w)
        self._sync_calc_display()
        self._trigger_change(None)

    def _on_txt_modules_w_changed(self, e):
        val = (self.txt_modules_w.value or "").strip()
        if val.isdigit() and int(val) > 0:
            self.num_modules_w = int(val)
            self._sync_calc_display()
            self._trigger_change(None)

    def _change_modules_h(self, delta: int):
        self.num_modules_h = max(1, self.num_modules_h + delta)
        self.txt_modules_h.value = str(self.num_modules_h)
        self._sync_calc_display()
        self._trigger_change(None)

    def _on_txt_modules_h_changed(self, e):
        val = (self.txt_modules_h.value or "").strip()
        if val.isdigit() and int(val) > 0:
            self.num_modules_h = int(val)
            self._sync_calc_display()
            self._trigger_change(None)

    def _change_reserve(self, delta: int):
        self.num_reserve_modules = max(0, self.num_reserve_modules + delta)
        self.txt_reserve_modules.value = str(self.num_reserve_modules)
        self._sync_calc_display()
        self._trigger_change(None)

    def _on_txt_reserve_changed(self, e):
        val = (self.txt_reserve_modules.value or "").strip()
        if val.isdigit() and int(val) >= 0:
            self.num_reserve_modules = int(val)
            self._sync_calc_display()
            self._trigger_change(None)

    def _on_manual_dimension_changed(self, e):
        # Khi ở chế độ thủ công và người dùng trực tiếp sửa kích thước mm
        if self.config_mode == "manual":
            try:
                w_mm = float((self.calc_w_mm.value or "0").replace(".", "").replace(",", "."))
                h_mm = float((self.calc_h_mm.value or "0").replace(".", "").replace(",", "."))
                self.width_input.value = f"{w_mm / 1000:.3f}"
                self.height_input.value = f"{h_mm / 1000:.3f}"
                self.preview_header_size.value = f"{int(w_mm):,} × {int(h_mm):,} mm".replace(",", ".")
            except ValueError:
                pass
            self._trigger_change(None)

    def _sync_calc_display(self):
        mod = self._get_current_module()
        spec = mod.get("spec_json", {})
        required = ("width_mm", "height_mm", "pixel_w", "pixel_h")
        if not mod or not all(spec.get(field) for field in required):
            self.module_spec_name.value = "Chưa có module hợp lệ"
            self.module_spec_details.value = "Hãy khai báo module và thông số kỹ thuật trong danh mục linh kiện."
            for control in (self.calc_w_mm, self.calc_w_px, self.calc_h_mm, self.calc_h_px,
                            self.calc_installed_modules, self.calc_total_modules, self.calc_total_pixels):
                control.value = ""
            self.width_input.value = ""
            self.height_input.value = ""
            self.preview_header_size.value = "Chưa có kích thước"
            self.preview_header_grid.value = "Chưa có dữ liệu module"
            self.preview_footer_note.value = ""
            self.preview_grid_column.controls = []
            return
        w_mm = float(spec["width_mm"])
        h_mm = float(spec["height_mm"])
        px_w = int(spec["pixel_w"])
        px_h = int(spec["pixel_h"])
        pitch = spec.get("pitch") or mod.get("code", "")

        # Cập nhật thông số theo sản phẩm đã chọn
        self.module_spec_name.value = f"Module {pitch}"
        self.module_spec_details.value = f"{int(w_mm)} × {int(h_mm)} mm  /  {px_w} × {px_h} px"

        # Tính toán
        total_w_mm = self.num_modules_w * w_mm
        total_h_mm = self.num_modules_h * h_mm
        total_px_w = self.num_modules_w * px_w
        total_px_h = self.num_modules_h * px_h
        installed = self.num_modules_w * self.num_modules_h
        total_mod = installed + self.num_reserve_modules
        total_px = total_px_w * total_px_h

        self.calc_w_mm.value = f"{int(total_w_mm):,}".replace(",", ".")
        self.calc_w_px.value = str(total_px_w)
        self.calc_h_mm.value = f"{int(total_h_mm):,}".replace(",", ".")
        self.calc_h_px.value = str(total_px_h)

        self.calc_installed_modules.value = str(installed)
        self.calc_total_modules.value = str(total_mod)
        self.calc_total_pixels.value = f"{total_px:,}".replace(",", ".")

        # Cập nhật các trường gửi về Engine Calculator
        self.width_input.value = f"{total_w_mm / 1000:.3f}"
        self.height_input.value = f"{total_h_mm / 1000:.3f}"
        if installed > 0:
            reserve_pct = (self.num_reserve_modules / installed) * 100
            self.reserve_input.value = f"{reserve_pct:.2f}"

        # Cập nhật Sơ đồ ma trận Module Preview
        self.preview_header_size.value = f"{int(total_w_mm):,} × {int(total_h_mm):,} mm".replace(",", ".")
        self.preview_header_grid.value = f"{self.num_modules_w} cột × {self.num_modules_h} hàng"
        self.preview_footer_note.value = f"Sơ đồ minh họa • {installed} module lắp"

        # Vẽ lưới (tối đa 10 cột × 6 hàng để vừa giao diện điện thoại)
        show_cols = min(self.num_modules_w, 10)
        show_rows = min(self.num_modules_h, 6)
        cell_width = max(16, min(28, int(260 / show_cols))) if show_cols else 20
        cell_height = 14

        self.preview_grid_column.controls = [
            ft.Row(
                spacing=3,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=cell_width,
                        height=cell_height,
                        border_radius=3,
                        bgcolor=UIColors.PRIMARY if r == 0 else "#93C5FD",
                    )
                    for c in range(show_cols)
                ],
            )
            for r in range(show_rows)
        ]

    def _trigger_change(self, e):
        self.on_change(e)

    def update_layout_preview(self, summary: Dict, message: str = ""):
        # Tương thích với callback từ MainView
        pass
