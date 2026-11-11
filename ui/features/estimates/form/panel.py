"""LED configuration form: public Flet control facade.

Visual controls are created by FormFieldsMixin; layout, event handlers,
field style and input/output synchronization live in separate files.
"""
import math
from typing import Any, Callable, Dict, List
import flet as ft

from ui.features.estimates.form.fields import FormFieldsMixin
from ui.features.estimates.form.layout import FormLayoutMixin
from ui.features.estimates.form.styles import FormStylesMixin
from ui.features.estimates.form.interactions import FormInteractionsMixin
from ui.features.estimates.form.data import FormDataMixin

from ui.theme.tokens import UIColors

class InputPanel(
    FormFieldsMixin,
    FormLayoutMixin,
    FormStylesMixin,
    FormInteractionsMixin,
    FormDataMixin,
    ft.Container,
):
    PRIMARY_COLOR = UIColors.PRIMARY
    SECONDARY_COLOR = "#00687A"

    def __init__(
        self,
        options: Dict[str, List[Dict]],
        on_change: Callable,
        on_save: Callable,
        on_export_excel: Callable,
        on_export_pdf: Callable,
        on_load_preset: Callable,
        screen_types=None,
    ):
        super().__init__()
        self.options = options
        self.on_change = on_change
        self.on_save = on_save
        self.on_load_preset = on_load_preset

        self.padding = ft.Padding(4, 4, 4, 12)
        self.bgcolor = ft.Colors.TRANSPARENT

        self._create_mode_controls()
        self._create_display_controls()
        self._create_environment_controls()
        self._erp_screen_types = []
        self.erp_screen_types_dropdown = ft.Dropdown(
            label="Loại màn hình *",
            options=[],
            expand=True,
            visible=True,
            disabled=True,
            hint_text="Đang chờ dữ liệu từ FastBusiness",
            on_select=self._on_erp_screen_type_selected,
            **self._dropdown_style(),
        )
        self._create_module_and_dimension_controls()
        self._create_general_information_controls()
        self._create_material_controls()
        self._create_compatibility_controls()

        # Populate selects and calculate the initial UI state after every field exists.
        # Nạp dữ liệu dropdown ban đầu
        self._init_module_options()
        self._init_manual_options()
        self._sync_calc_display()

        # Dựng nội dung View
        self.content = self._build_layout()
        self.set_screen_types(screen_types or [])

    @staticmethod
    def _screen_type_environment(item):
        """Translate known ERP screen kinds to the calculator's legacy enum."""
        name = item.name.strip().casefold()
        if name in ("indoor", "trong nhà", "trong nha"):
            return "indoor"
        if name in ("outdoor", "ngoài trời", "ngoai troi"):
            return "outdoor"
        # Known IDs from this FastBusiness installation; no UI choices are invented.
        return {"1": "indoor", "2": "outdoor"}.get(item.code)

    def _find_screen_type(self, code):
        return next((item for item in self._erp_screen_types if item.code == code), None)

    def screen_type_code_for_environment(self, environment):
        return next(
            (item.code for item in self._erp_screen_types
             if self._screen_type_environment(item) == environment),
            None,
        )

    def set_screen_types(self, items):
        """Populate the UI with actual GetCompletionList results after ERP login."""
        self._erp_screen_types = list(items or [])
        available = {item.code for item in self._erp_screen_types}
        previous = self.erp_screen_types_dropdown.value
        self.erp_screen_types_dropdown.options = [
            ft.dropdown.Option(key=item.code, text=item.name)
            for item in self._erp_screen_types
        ]
        self.erp_screen_types_dropdown.disabled = not bool(available)
        self.erp_screen_types_dropdown.hint_text = (
            "Chọn loại màn hình" if available
            else "FastBusiness chưa trả về danh mục Loại màn hình"
        )
        self.erp_screen_types_dropdown.value = previous if previous in available else None
        if self.erp_screen_types_dropdown.value is None:
            self.env_mode_val = None
            self.environment.value = None
        else:
            selected = self._find_screen_type(self.erp_screen_types_dropdown.value)
            self.env_mode_val = self._screen_type_environment(selected)
            self.environment.value = self.env_mode_val
        try:
            if self.page is not None:
                self.update()
        except (RuntimeError, AttributeError):
            pass

    def select_screen_type(self, code):
        """Set a selected ERP key and synchronize calculation + module filtering."""
        if self._find_screen_type(code) is None:
            return False
        self.erp_screen_types_dropdown.value = code
        self._on_erp_screen_type_selected(None)
        return True

    def _on_erp_screen_type_selected(self, e):
        selected = self._find_screen_type(self.erp_screen_types_dropdown.value)
        environment = self._screen_type_environment(selected) if selected else None
        if environment is None:
            self.erp_screen_types_dropdown.error_text = (
                "Vui lòng chọn loại màn hình hợp lệ từ FastBusiness"
                if selected is None else "Loại màn hình này chưa được hỗ trợ trong bộ tính giá"
            )
            self.env_mode_val = None
            self.environment.value = None
            self._trigger_change(e)
            return
        self.erp_screen_types_dropdown.error_text = None
        self._set_env_mode(environment)

