"""QuoteListActionsMixin: isolated UI responsibilities; inherited by the screen coordinator.

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
from ui.components.preview_panel import PreviewPanel
from ui.views.profile_view import ProfileView


from ui.theme.tokens import UIColors

class QuoteListActionsMixin:
    def _action_create_new(self):
        self._interacted_estimate = False
        self._interacted_inventory = False
        self._update_fab_visibility()
        self._go_tab(0)
        self.input_panel.project_name.value = ""
        self.input_panel.customer_name.value = ""
        self.input_panel.customer_phone.value = ""
        self.input_panel.num_modules_w = 8
        self.input_panel.num_modules_h = 4
        self.input_panel.num_reserve_modules = 2
        self.input_panel.txt_modules_w.value = "8"
        self.input_panel.txt_modules_h.value = "4"
        self.input_panel.txt_reserve_modules.value = "2"
        self.input_panel.additional_items.clear()
        self.input_panel.additional_rows.controls.clear()
        self.recalculate()
        if hasattr(self, "page") and self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text("Đã tạo mới cấu hình dự toán!"), bgcolor=UIColors.PRIMARY)
            self.page.snack_bar.open = True
            self.page.update()

    def _enable_select_mode(self, action_desc: str = ""):
        self.select_mode = True
        self._go_tab(3)
        self._refresh_list_view()
        if hasattr(self, "page") and self.page:
            msg = f"Đã mở chức năng chọn. Vui lòng tích chọn dự toán để {action_desc}." if action_desc else "Đã mở chức năng chọn."
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=UIColors.PRIMARY)
            self.page.snack_bar.open = True
            self.page.update()

    def _action_edit_selected(self):
        if not self.select_mode or len(self.selected_quote_ids) == 0:
            self._enable_select_mode("chỉnh sửa")
        elif len(self.selected_quote_ids) == 1:
            item_id = list(self.selected_quote_ids)[0]
            self.select_mode = False
            self.selected_quote_ids.clear()
            self._load_history(item_id)
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Đang mở chỉnh sửa dự toán đã chọn."), bgcolor=UIColors.PRIMARY)
                self.page.snack_bar.open = True
                self.page.update()
        else:
            self._go_tab(3)
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Vui lòng chỉ chọn đúng 1 dự toán để chỉnh sửa!"), bgcolor=UIColors.ERROR)
                self.page.snack_bar.open = True
                self.page.update()

    def _action_delete_selected(self):
        if not self.select_mode or len(self.selected_quote_ids) == 0:
            self._enable_select_mode("xóa")
        else:
            count = len(self.selected_quote_ids)
            for item_id in list(self.selected_quote_ids):
                self.db.delete_quote_history(item_id)
            self.select_mode = False
            self.selected_quote_ids.clear()
            self._refresh_list_view()
            self._refresh_history()
            if hasattr(self, "page") and self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Đã xóa thành công {count} dự toán!"), bgcolor=UIColors.ERROR)
                self.page.snack_bar.open = True
                self.page.update()

    def _action_focus_search(self):
        self._go_tab(3)
        if hasattr(self, "list_search") and hasattr(self, "page") and self.page:
            try:
                if hasattr(self.page, "run_task"):
                    self.page.run_task(self.list_search.focus)
                else:
                    self.list_search.autofocus = True
                    self.page.update()
            except Exception:
                pass

    def _action_view_selected(self):
        if not self.select_mode or len(self.selected_quote_ids) == 0:
            self._enable_select_mode("xem")
        else:
            item_id = list(self.selected_quote_ids)[0]
            self.select_mode = False
            self.selected_quote_ids.clear()
            self._open_quote_detail_view(item_id)

    def _action_clone_selected(self):
        if not self.select_mode or len(self.selected_quote_ids) == 0:
            self._enable_select_mode("sao chép")
        else:
            count = 0
            last_new_num = ""
            for item_id in list(self.selected_quote_ids):
                item = self.db.get_quote_history(item_id)
                if item:
                    payload = copy.deepcopy(item.get("payload") or {})
                    orig_name = item.get("quote_name") or item.get("project_name") or "Dự toán"
                    new_name = f"{orig_name} (Bản sao)"
                    new_id = self.db.save_quote_history(
                        quote_name=new_name,
                        customer_name=item.get("customer_name") or "",
                        payload=payload,
                        total=item.get("total", 0),
                        status="Nháp",
                    )
                    new_item = self.db.get_quote_history(new_id)
                    last_new_num = new_item.get("quote_number") if new_item else f"DT-{new_id:03d}"
                    count += 1
            self.select_mode = False
            self.selected_quote_ids.clear()
            self._refresh_list_view()
            self._refresh_history()
            if hasattr(self, "page") and self.page:
                msg = (
                    f"Đã sao chép thành công và tạo mới {count} dự toán!"
                    if count > 1
                    else f"Đã sao chép thành công tạo mới: {last_new_num}!"
                )
                self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=UIColors.SUCCESS)
                self.page.snack_bar.open = True
                self.page.update()

    def _action_refresh_all(self):
        self.select_mode = False
        self.selected_quote_ids.clear()
        self._refresh_options()
        self._refresh_inventory()
        self._refresh_history()
        self._refresh_list_view()
        self.recalculate()
        if hasattr(self, "page") and self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text("Đã làm mới toàn bộ dữ liệu!"), bgcolor=UIColors.SUCCESS)
            self.page.snack_bar.open = True
            self.page.update()

    def _action_deselect_all(self):
        self.select_mode = False
        self.selected_quote_ids.clear()
        self._refresh_list_view()
        if hasattr(self, "page") and self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text("Đã ẩn chức năng chọn. Mọi thứ trở lại bình thường!"), bgcolor=UIColors.PRIMARY)
            self.page.snack_bar.open = True
            self.page.update()

    def _toggle_select_all(self, e):
        history = self._get_filtered_list_history()
        if e.control.value:
            self.selected_quote_ids = {item["id"] for item in history}
        else:
            self.selected_quote_ids.clear()
        self._refresh_list_view()

    def _toggle_select_item(self, item_id: int, value: bool = None):
        if value is None:
            if item_id in self.selected_quote_ids:
                self.selected_quote_ids.remove(item_id)
            else:
                self.selected_quote_ids.add(item_id)
        else:
            if value:
                self.selected_quote_ids.add(item_id)
            else:
                self.selected_quote_ids.discard(item_id)
        self._refresh_list_view()
