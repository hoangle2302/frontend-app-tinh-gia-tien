"""Main workspace compositor.

Layout + state initialization live here; feature-specific UI and event handlers
are grouped in ui/features/ so each screen can be edited independently.
Existing integrations continue importing MainView from this module.
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

from ui.shell.navigation import NavigationMixin
from ui.shell.floating_actions import FloatingActionsMixin
from ui.features.estimates.options import EstimateOptionsMixin
from ui.features.estimates.estimate_screen import EstimateScreenMixin
from ui.features.estimates.estimate_actions import EstimateActionsMixin
from ui.features.estimates.quote_sheet import QuoteSheetMixin
from ui.features.quotes.history import QuoteHistoryMixin
from ui.features.quotes.listing import QuoteListingMixin
from ui.features.quotes.list_actions import QuoteListActionsMixin
from ui.features.quotes.detail import QuoteDetailMixin
from ui.features.inventory.screen import InventoryScreenMixin
from ui.features.inventory.product_actions import InventoryProductActionsMixin
from ui.features.summary.screen import SummaryScreenMixin

class MainView(
    NavigationMixin,
    FloatingActionsMixin,
    EstimateOptionsMixin,
    EstimateScreenMixin,
    EstimateActionsMixin,
    QuoteSheetMixin,
    QuoteHistoryMixin,
    QuoteListingMixin,
    QuoteListActionsMixin,
    QuoteDetailMixin,
    InventoryScreenMixin,
    InventoryProductActionsMixin,
    SummaryScreenMixin,
):
    CATEGORY_LABELS = [
        ("module", "Module LED"),
        ("power", "Nguồn"),
        ("card", "Card thu"),
        ("processor", "Bộ xử lý"),
        ("frame", "Khung"),
        ("service", "Dịch vụ"),
    ]

    CATEGORY_ICONS = {
        "module": ft.Icons.GRID_VIEW,
        "power": ft.Icons.BOLT,
        "card": ft.Icons.MEMORY,
        "processor": ft.Icons.DEVELOPER_BOARD,
        "frame": ft.Icons.CROP_FREE,
        "service": ft.Icons.CONSTRUCTION,
    }

    def __init__(self, page: ft.Page, db: DBManager, on_logout: Callable = None, screen_types=None):
        self.page = page
        self.db = db
        self.on_logout = on_logout
        self.calculator = Calculators()
        self.exporter = QuoteExporter()
        self.quote_data: Dict[str, Any] = {}
        self.message = ft.Text("", color=ft.Colors.GREEN_700)
        self._refresh_options()

        self.input_panel = InputPanel(
            options=self.options,
            on_change=self.on_input_change,
            on_save=self.on_save_config,
            on_export_excel=self.on_export_excel,
            on_export_pdf=self.on_export_pdf,
            on_load_preset=self.on_load_preset,
            screen_types=screen_types,
        )
        self._refresh_preset_options()
        self.preview_panel = PreviewPanel(
            self.on_export_excel,
            self.on_export_pdf,
            self.on_save_quote,
            self.on_share_quote,
        )
        self.input_panel.expand = True
        self.left_container = ft.Container(
            content=self.input_panel,
            expand=True,
        )
        # Thanh áp dụng cấu hình cố định phía dưới tab Lập dự toán
        self._total_texts = []
        self.quote_apply_bar = self._build_apply_bar()
        self.quote_view = ft.Container(
            padding=ft.Padding(8, 4, 8, 0),
            content=ft.Column(
                spacing=8,
                expand=True,
                controls=[self.left_container, self.quote_apply_bar],
            ),
            expand=True,
        )
        # Trạng thái tab Linh kiện
        self._inv_filter = "all"
        self._inv_selected = None
        self._inv_qty = 1
        self.selected_quote_ids = set()
        self.select_mode = False
        self.detail_mode = False
        self.active_detail_item = None
        self.inventory_view = self._build_inventory_view()
        self.summary_view = self._build_summary_view()
        self.history_view = self._build_history_view()
        self.list_view = self._build_list_view()
        self.profile_view = ProfileView(
            page=self.page,
            db=self.db,
            on_profile_updated=self._on_profile_updated,
            on_logout=self.on_logout,
        )

        # View container chứa trang hiện tại
        self.view_container = ft.Container(
            content=self.quote_view,
            expand=True,
        )

        # Nút hành động nổi (FAB menu mini) ở phía trên thanh NavigationBar
        self.action_menu_btn = self._build_action_menu_button()

        # Thanh Menu Navigation Bar đặt ở dưới cùng chuẩn Material 3
        self.nav_bar = ft.NavigationBar(
            selected_index=0,
            height=65,
            bgcolor=UIColors.SURFACE,
            indicator_color=UIColors.PRIMARY_SOFT,
            on_change=self._on_nav_change,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.EDIT_NOTE_OUTLINED,
                    selected_icon=ft.Icons.EDIT_NOTE,
                    label="Lập dự toán",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.WIDGETS_OUTLINED,
                    selected_icon=ft.Icons.WIDGETS,
                    label="Linh kiện",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                    selected_icon=ft.Icons.RECEIPT_LONG,
                    label="Tổng hợp",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.FORMAT_LIST_BULLETED_OUTLINED,
                    selected_icon=ft.Icons.FORMAT_LIST_BULLETED,
                    label="Danh sách",
                ),
            ],
        )

        self.layout = ft.Stack(
            expand=True,
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        self.view_container,
                        ft.Divider(height=1, thickness=1, color=UIColors.BORDER),
                        self.nav_bar,
                    ],
                ),
                self.action_menu_btn,
            ],
        )

        self.tabs = self.layout
        self._mounted = False
        # Global resize ownership stays with app.bootstrap; it delegates to this view.
        self._on_resize()
        self.recalculate()
        self._apply_card_expanded = False
        self._interacted_estimate = False
        self._interacted_inventory = False
        self._update_fab_visibility()
