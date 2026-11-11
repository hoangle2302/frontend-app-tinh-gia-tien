"""EstimateOptionsMixin: isolated UI responsibilities; inherited by the screen coordinator.

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

class EstimateOptionsMixin:
    def _refresh_options(self):
        self.options = {
            "modules": self.db.list_products(category="module"),
            "powers": self.db.list_products(category="power"),
            "cards": self.db.list_products(category="card"),
            "frames": self.db.list_products(category="frame"),
            "processors": self.db.list_products(category="processor"),
        }
        if hasattr(self, "input_panel"):
            # Propagate newly created/edited inventory records to open controls.
            self.input_panel.options = self.options
            self.input_panel._init_module_options()
            self.input_panel._init_manual_options()
            self.input_panel._sync_calc_display()
        if hasattr(self, "input_panel"):
            # Propagate newly created/edited inventory records to open controls.
            self.input_panel.options = self.options
            self.input_panel._init_module_options()
            self.input_panel._init_manual_options()
            self.input_panel._sync_calc_display()

    def _refresh_preset_options(self):
        options = []
        options.extend(
            ft.dropdown.Option(
                key=f"saved:{item['id']}",
                text=f"{item['name']} (đã lưu)",
            )
            for item in self.db.list_configurations()
        )
        self.input_panel.preset_dropdown.options = options

    def _build_category_selector(self, default_value: str = "module"):
        options = [
            ("module", "Module LED"),
            ("power", "Nguồn"),
            ("card", "Card thu"),
            ("processor", "Bộ xử lý"),
            ("frame", "Khung"),
            ("service", "Dịch vụ"),
        ]
        radio_group = ft.RadioGroup(
            value=default_value,
            content=ft.Row(
                wrap=True,
                spacing=6,
                run_spacing=4,
                controls=[
                    ft.Radio(
                        value=val,
                        label=lbl,
                        fill_color=UIColors.PRIMARY,
                    )
                    for val, lbl in options
                ],
            ),
        )
        container = ft.Container(
            padding=ft.Padding(10, 8, 10, 8),
            border=ft.Border.all(1, UIColors.BORDER_STRONG),
            border_radius=12,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Text("Nhóm vật tư *", size=12, color=UIColors.TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                    radio_group,
                ],
            ),
        )
        return radio_group, container
