"""Mobile ERP Báo giá LED V5 — task-based redesign for Flet 1.1.2.

This is a functional, local-first quote DRAFT application (not an ERP backend).
The 10 legacy sections and their known fields are kept. Unknown forms are not
fabricated. Costs are based ONLY on explicitly entered items; no BOM guesses.
"""
from __future__ import annotations

from datetime import datetime
import sys
import flet as ft

from form_schema import ALL_FIELDS, HEADER_FIELDS, MODULE_DETAILS, COMMON_SECTIONS, REQUIRED_FIELDS
from required_validation import required_issues, required_progress
from content_navigation import CONTENT_GROUPS, CONTENT_META, fold
from quote_engine import CostLine, fmt_money, fmt_number, fmt_int, price_result, technical_result
from storage import QuoteStore, create_id
from ui_logic import STEPS, COST_TABS, next_step, section_status, quote_label, validate_draft

PRIMARY = "#295DA9"
INK = "#182438"
MUTED = "#69798E"
CANVAS = "#F5F7FB"
PALE = "#EAF1FD"
BORDER = "#E1E7F0"
ERROR = "#B42318"

CATEGORY_ICONS = {
    "Thông tin chung": ft.Icons.INFO_OUTLINE,
    "Thông tin Pro": ft.Icons.SETTINGS_OUTLINED,
    "Chi tiết": ft.Icons.LIST_ALT,
    "Thông tin card": ft.Icons.MEMORY,
    "Vật tư điện": ft.Icons.ELECTRICAL_SERVICES,
    "Vật tư cơ khí": ft.Icons.BUILD_OUTLINED,
    "Vật tư tủ điện": ft.Icons.POWER,
    "Manual": ft.Icons.EDIT_NOTE,
    "Tệp đính kèm": ft.Icons.ATTACH_FILE,
    "Ghi chú": ft.Icons.STICKY_NOTE_2_OUTLINED,
}
STEP_ICONS = (ft.Icons.MONITOR, ft.Icons.LAYERS, ft.Icons.CALCULATE, ft.Icons.CHECK_CIRCLE_OUTLINE)


def main(page: ft.Page):
    page.title = "LED Quote • Mobile V6"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = CANVAS
    page.padding = 0
    page.spacing = 0
    page.theme = ft.Theme(
        use_material3=True,
        color_scheme_seed=PRIMARY,
        input_decoration_theme=ft.InputDecorationTheme(
            border=ft.OutlineInputBorder(border_radius=13),
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=14),
            label_style=ft.TextStyle(size=14),
        ),
    )
    if sys.platform == "win32":
        page.window.width = 412
        page.window.height = 870

    store = QuoteStore()
    storage_error = None
    try:
        saved: list[dict] = store.load()
    except (OSError, ValueError) as exc:
        saved = []
        storage_error = f"Chưa đọc được tệp lưu trữ: {exc}"

    current: dict = {"id": None, "step": 0, "detail": None, "date": datetime.now(),
                     "completion_attempted": False}
    file_names: list[str] = []
    cost_rows: dict[str, list[dict]] = {name: [] for name in COST_TABS}
    cost_col: dict[str, ft.Column] = {}
    detail_panels: dict[str, ft.Control] = {}
    category_subtitles: dict[str, ft.Text] = {}

    def tip(message: str):
        page.show_dialog(ft.SnackBar(content=ft.Text(message), duration=3000))

    def small(txt: str):
        return ft.Text(txt, size=12, color=MUTED)

    def block(title: str, children: list[ft.Control], caption: str | None = None):
        items: list[ft.Control] = [ft.Text(title, size=17, weight=ft.FontWeight.BOLD, color=INK)]
        if caption:
            items.append(small(caption))
        items.extend(children)
        return ft.Container(
            padding=ft.Padding.all(15),
            border_radius=18,
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, BORDER),
            content=ft.Column(spacing=12, controls=items),
        )

    def field(label, value="", kind="text", *, multiline=False, on_change=None, hint=None):
        return ft.TextField(
            label=label, value=value, text_size=15,
            hint_text=hint,
            keyboard_type=ft.KeyboardType.NUMBER if kind in ("integer", "decimal") else ft.KeyboardType.TEXT,
            text_input_action=ft.TextInputAction.NEWLINE if multiline else ft.TextInputAction.NEXT,
            multiline=multiline, min_lines=3 if multiline else 1,
            max_lines=6 if multiline else 1,
            on_change=on_change,
        )

    def metric(label: str, output: ft.Text):
        return ft.Container(
            expand=1, border_radius=13, bgcolor="#F3F6FB", padding=ft.Padding.all(12),
            content=ft.Column(spacing=5, controls=[small(label), output]),
        )

    def alert_lookup(label: str):
        page.show_dialog(ft.AlertDialog(
            title=ft.Text(f"Tra cứu {label}"),
            content=ft.Text(
                "Phần mềm gốc có tra cứu mã, nhưng chưa có bảng danh mục thực tế. "
                "Hiện có thể nhập thủ công. Khi kết nối API, thay hộp thoại này bằng "
                "danh sách tra cứu được xác thực."
            ),
            actions=[ft.TextButton("Đóng", on_click=lambda _: page.pop_dialog())],
        ))

    # Single control per field, mounted once. This prevents losing edits on navigation.
    inputs: dict[str, ft.Control] = {}
    for spec in ALL_FIELDS:
        if spec.kind == "checkbox":
            inputs[spec.key] = ft.Checkbox(label=spec.label, value=False)
        else:
            default = "0" if spec.key == "so_module_du_phong" else ""
            inputs[spec.key] = field(spec.label + (" *" if spec.required else ""), default, spec.kind)

    def field_control(spec):
        base = inputs[spec.key]
        if spec.kind not in ("lookup", "number_lookup"):
            return base
        return ft.Row(spacing=2, controls=[
            ft.Container(expand=True, content=base),
            ft.IconButton(icon=ft.Icons.SEARCH, tooltip=f"Tra cứu {spec.label}",
                          on_click=lambda _, title=spec.label: alert_lookup(title)),
        ])

    def pair(a, b):
        return ft.Row(spacing=9, controls=[ft.Container(expand=1, content=a), ft.Container(expand=1, content=b)])

    # ---------------------------------------------------------------------
    # STEP 1: Configuration and technical metrics
    # ---------------------------------------------------------------------
    area_text = ft.Text("—", size=20, weight=ft.FontWeight.BOLD, color=PRIMARY)
    modules_text = ft.Text("—", size=20, weight=ft.FontWeight.BOLD, color=INK)
    dimensions_text = ft.Text("—", weight=ft.FontWeight.W_600)
    resolution_text = ft.Text("—", weight=ft.FontWeight.W_600)
    pixel_text = ft.Text("—", weight=ft.FontWeight.W_600)
    tech_warning = small("Nhập số module W/H và kích thước một module để tính diện tích.")
    date_text = ft.Text(current["date"].strftime("%d/%m/%Y"), weight=ft.FontWeight.W_600)
    date_picker = ft.DatePicker(value=current["date"])

    def change_date(e):
        if e.control.value:
            current["date"] = e.control.value
            date_text.value = current["date"].strftime("%d/%m/%Y")
            page.update()

    date_picker.on_change = change_date
    certificate_text = ft.Text("Số bản nháp tạo khi lưu", weight=ft.FontWeight.W_600, size=13)

    config_required_note = ft.Text("0/4 trường bắt buộc đã nhập", size=12, color=MUTED)
    common_required_note = ft.Text("0/3 trường bắt buộc đã nhập", size=12, color=MUTED)
    required_note = small("* Bắt buộc để kiểm tra hoàn tất. Có thể lưu nháp trước.")

    screen_primary = block("Màn hình và module", [
        required_note,
        config_required_note,
        small("Chọn thông tin thực tế; chưa có sẵn danh mục mã hoặc cấu hình của nhà sản xuất."),
        field_control(HEADER_FIELDS[0]),
        field_control(HEADER_FIELDS[1]),
        field_control(HEADER_FIELDS[2]),
        field_control(HEADER_FIELDS[3]),
        pair(field_control(HEADER_FIELDS[4]), field_control(HEADER_FIELDS[5])),
        ft.ExpansionTile(
            title="Dự phòng và diễn giải", maintain_state=True,
            controls_padding=ft.Padding.all(10),
            controls=[ft.Column(spacing=10, controls=[field_control(HEADER_FIELDS[6]), field_control(HEADER_FIELDS[7])])],
        ),
    ], "Các trường chính được giữ đúng tên theo hệ thống cũ.")

    technical = block("Kết quả kỹ thuật", [
        pair(metric("Diện tích hiển thị (m²)", area_text), metric("Tổng module gồm dự phòng", modules_text)),
        tech_warning,
        ft.ExpansionTile(
            title="Kích thước và pixel của module", maintain_state=True,
            subtitle=small("Dữ liệu của 1 module để tính W/H và độ phân giải"),
            controls_padding=ft.Padding.all(10),
            controls=[ft.Column(spacing=10, controls=[
                pair(field_control(MODULE_DETAILS[0]), field_control(MODULE_DETAILS[1])),
                pair(field_control(MODULE_DETAILS[2]), field_control(MODULE_DETAILS[3])),
            ])],
        ),
        ft.ExpansionTile(
            title="Thông số chi tiết", maintain_state=True,
            controls_padding=ft.Padding.all(10),
            controls=[ft.Column(spacing=10, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                       controls=[small("Kích thước hiển thị (mm)"), dimensions_text]),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                       controls=[small("Độ phân giải (px)"), resolution_text]),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                       controls=[small("Tổng pixel"), pixel_text]),
            ])],
        ),
    ], "Thông số chỉ được tính khi có dữ liệu đúng; không áp mặc định P2.5/P3/P4.")

    doc_block = block("Chứng từ", [
        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[small("Số chứng từ"), certificate_text]),
        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[small("Ngày lập"), date_text]),
        ft.OutlinedButton("Đổi ngày lập", icon=ft.Icons.CALENDAR_MONTH,
                          on_click=lambda _: page.show_dialog(date_picker)),
        small("Trạng thái: 0. Lập chứng từ (bản nháp). Chưa có quy trình phê duyệt."),
    ])
    stage1 = ft.Column(spacing=12, controls=[
        ft.Text("Thiết lập màn hình", size=23, weight=ft.FontWeight.BOLD),
        small("Bước 1/4 · Thông tin tạo cơ sở tính diện tích và vật tư."),
        screen_primary, technical,
        ft.ExpansionTile(title="Ngày lập & chứng từ", maintain_state=True,
                         controls_padding=ft.Padding.all(8), controls=[doc_block]),
    ])

    # ---------------------------------------------------------------------
    # STEP 2: Searchable grid-like navigation, each content form one drill-down
    # ---------------------------------------------------------------------
    common_sections: list[ft.Control] = []
    common_tiles: dict[str, ft.ExpansionTile] = {}
    section_required_notes: dict[str, ft.Text] = {}
    for index, sec in enumerate(COMMON_SECTIONS):
        children = []
        for spec in sec.fields:
            if spec.kind == "checkbox" and spec.key in ("nguon_dien_1pha", "nguon_dien_3pha"):
                continue
            children.append(field_control(spec))
        if index == len(COMMON_SECTIONS) - 1:
            children.insert(-1, ft.Column(spacing=4, controls=[
                small("Nguồn điện (hai lựa chọn độc lập theo biểu mẫu gốc)"),
                ft.Row(spacing=20, controls=[inputs["nguon_dien_1pha"], inputs["nguon_dien_3pha"]]),
            ]))
        section_required_notes[sec.label] = ft.Text("", size=12, color=MUTED)
        tile = ft.ExpansionTile(
            title=sec.label, subtitle=section_required_notes[sec.label],
            expanded=index == 0, maintain_state=True,
            controls_padding=ft.Padding.all(12),
            controls=[ft.Column(spacing=11, controls=children)],
        )
        common_tiles[sec.label] = tile
        common_sections.append(tile)

    common_panel = ft.Column(spacing=10, controls=[
        block("Thông tin chung", [
            small("* Bắt buộc để kiểm tra hoàn tất; chưa cần điền khi lưu nháp."),
            common_required_note,
            small("16 trường theo ảnh gốc; bảng tra cứu đang chờ kết nối danh mục."),
            *common_sections,
        ]),
    ])
    detail_panels["Thông tin chung"] = common_panel

    def add_cost_row(cat: str, initial: dict | None = None, *, update=True):
        item = initial or {}
        name = field("Tên vật tư / hạng mục", item.get("name", ""))
        qty = field("Số lượng", item.get("qty", ""), "decimal")
        unit = field("Đơn giá (VND)", item.get("price", ""), "decimal")
        row: dict = {"name": name, "qty": qty, "price": unit}

        def remove(_):
            cost_rows[cat].remove(row)
            cost_col[cat].controls.remove(row["view"])
            calculate()

        row["view"] = ft.Container(
            padding=ft.Padding.all(12), border=ft.Border.all(1, BORDER), border_radius=15,
            content=ft.Column(spacing=9, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    small("Dòng chi phí thực tế"),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, tooltip="Xóa dòng", on_click=remove),
                ]),
                name, pair(qty, unit),
            ]),
        )
        for ctrl in (name, qty, unit):
            ctrl.on_change = calculate
        cost_rows[cat].append(row)
        cost_col[cat].controls.append(row["view"])
        if update:
            calculate()

    for cat in COST_TABS:
        cost_col[cat] = ft.Column(spacing=9)
        detail_panels[cat] = ft.Column(spacing=10, controls=[block(cat, [
            small("Bảng chi phí tự nhập. Các trường nguyên bản của mục này chưa được cung cấp."),
            cost_col[cat],
            ft.FilledTonalButton("Thêm dòng chi phí", icon=ft.Icons.ADD,
                                 height=48, on_click=lambda _, c=cat: add_cost_row(c)),
        ])])
    for cat in ("Thông tin Pro", "Chi tiết", "Thông tin card"):
        detail_panels[cat] = ft.Column(controls=[block(cat, [
            ft.Icon(ft.Icons.INFO_OUTLINE, color=PRIMARY, size=26),
            ft.Text("Chưa có ảnh hoặc cấu trúc trường thực tế cho mục này."),
            small("Giữ đúng danh mục, không tạo ô nhập hay quy tắc tính tự suy đoán."),
        ])])

    note = field("Ghi chú", multiline=True, hint="Ghi yêu cầu của khách hàng / lưu ý thi công...")
    detail_panels["Ghi chú"] = ft.Column(controls=[block("Ghi chú", [note])])
    file_info = small("Chưa chọn tệp")

    def file_result(e):
        file_names[:] = [f.name for f in (e.files or [])]
        file_info.value = ", ".join(file_names) if file_names else "Chưa chọn tệp"
        page.update()

    picker = ft.FilePicker(on_result=file_result)
    page.services.append(picker)
    detail_panels["Tệp đính kèm"] = ft.Column(controls=[block("Tệp đính kèm", [
        small("Chỉ lưu tên các tệp đã chọn; bản nháp chưa upload hoặc lưu nội dung tệp."),
        ft.Button("Chọn tệp", icon=ft.Icons.ATTACH_FILE, action=ft.PickFiles(picker, allow_multiple=True)),
        file_info,
    ])])

    content_title = ft.Text("Danh mục nội dung", size=23, weight=ft.FontWeight.BOLD)
    category_search = field("Tìm nội dung", hint="Ví dụ: vat tu dien")
    browser_groups: list[ft.Control] = []
    category_cards: list[tuple[str, ft.Container]] = []
    for group in CONTENT_GROUPS:
        cards: list[ft.Control] = []
        for cat in group.items:
            subtitle = small("Chưa nhập dữ liệu")
            category_subtitles[cat] = subtitle
            card = ft.Container(
                bgcolor=ft.Colors.SURFACE, border=ft.Border.all(1, BORDER),
                border_radius=16, padding=ft.Padding.all(12),
                on_click=lambda _, item=cat: open_category(item),
                content=ft.Row(spacing=12, controls=[
                    ft.Container(width=43, height=43, border_radius=13, bgcolor=PALE,
                                 alignment=ft.Alignment.CENTER,
                                 content=ft.Icon(CATEGORY_ICONS[cat], color=PRIMARY, size=23)),
                    ft.Container(expand=True, content=ft.Column(spacing=3, controls=[
                        ft.Text(cat, size=15, weight=ft.FontWeight.W_600), subtitle,
                    ])),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=MUTED),
                ]),
            )
            cards.append(card)
            category_cards.append((cat, card))
        group_box = ft.Column(spacing=8, controls=[
            ft.Text(group.label.upper(), color=MUTED, size=12, weight=ft.FontWeight.BOLD),
            *cards,
        ])
        browser_groups.append(group_box)

    browser_panel = ft.Column(spacing=13, controls=[
        content_title,
        small("Chọn phần muốn nhập; không bắt buộc đi theo thứ tự 10 mục."),
        category_search,
        *browser_groups,
    ])

    def filter_categories(_=None):
        q = fold(category_search.value or "")
        for label, card in category_cards:
            card.visible = q in fold(label + " " + CONTENT_META[label].description)
        for group_box in browser_groups:
            group_box.visible = any(c.visible for c in group_box.controls[1:])
        page.update()

    category_search.on_change = filter_categories
    detail_title = ft.Text("Thông tin chung", size=19, weight=ft.FontWeight.BOLD)
    detail_header = ft.Row(spacing=8, controls=[
        ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Về danh mục",
                      on_click=lambda _: close_category()),
        ft.Container(expand=True, content=detail_title),
    ])
    detail_frame = ft.Column(visible=False, spacing=12, controls=[
        detail_header,
        *[detail_panels[cat] for cat in (cat for group in CONTENT_GROUPS for cat in group.items)],
    ])

    def refresh_status():
        snapshot_data = make_snapshot()
        for cat, subtitle in category_subtitles.items():
            if cat == "Thông tin chung":
                done, total = required_progress(snapshot_data, "Thông tin chung")
                subtitle.value = f"Bắt buộc: {done}/{total} đã nhập · " + section_status(cat, snapshot_data)
                subtitle.color = ERROR if current["completion_attempted"] and done < total else MUTED
            else:
                subtitle.value = section_status(cat, snapshot_data)

    def open_category(cat: str):
        current["detail"] = cat
        browser_panel.visible = False
        detail_frame.visible = True
        detail_title.value = cat
        for name, surface in detail_panels.items():
            surface.visible = name == cat
        refresh_status()
        page.update()

    def close_category():
        current["detail"] = None
        detail_frame.visible = False
        browser_panel.visible = True
        refresh_status()
        page.update()

    stage2 = ft.Column(spacing=13, controls=[browser_panel, detail_frame])

    # ---------------------------------------------------------------------
    # STEP 3: Prices; editable base inputs and derived read-only summaries
    # ---------------------------------------------------------------------
    total_quantity = field("Tổng số lượng (theo phần mềm gốc)", "", "decimal",
                           hint="Chưa xác định quy tắc/đơn vị")
    margin = field("Biên lợi nhuận gộp (%)", "", "decimal")
    manual_flag = ft.Checkbox(label="Tự nhập tổng giá bán", value=False)
    manual_sale = field("Tổng giá bán nhập thủ công (VND)", "", "decimal")
    manual_sale.visible = False
    cost_total = ft.Text("Chưa đủ dữ liệu", size=17, weight=ft.FontWeight.BOLD)
    sale_total = ft.Text("Chưa đủ dữ liệu", size=21, weight=ft.FontWeight.BOLD, color=PRIMARY)
    cost_m2 = ft.Text("—", weight=ft.FontWeight.W_600)
    sale_m2 = ft.Text("—", weight=ft.FontWeight.W_600)
    actual_margin = small("Biên lợi nhuận gộp thực tế: —")
    pricing_warning = ft.Text("Chưa nhập đơn giá vật tư", color=MUTED, size=12)
    footer_price = ft.Text("Chưa đủ dữ liệu", color=PRIMARY, weight=ft.FontWeight.BOLD, size=13)
    reviewed_price = ft.Text("Chưa đủ dữ liệu", color=PRIMARY, weight=ft.FontWeight.BOLD, size=18)

    def update_manual(_):
        manual_sale.visible = bool(manual_flag.value)
        calculate()

    manual_flag.on_change = update_manual
    for ctrl in (margin, manual_sale):
        ctrl.on_change = lambda _: calculate()

    def jump_to_category(cat: str):
        set_step(1)
        open_category(cat)

    stage3 = ft.Column(spacing=13, controls=[
        ft.Text("Chi phí & giá bán", size=23, weight=ft.FontWeight.BOLD),
        small("Bước 3/4 · Chi phí phải được nhập từ vật tư, hạng mục thực tế."),
        block("Giá bán dự kiến", [
            small("Tổng giá bán chưa gồm VAT và chưa xác nhận đầy đủ BOM."),
            sale_total,
            pair(metric("Tổng chi phí", cost_total), metric("Chi phí /m²", cost_m2)),
            pair(metric("Giá bán /m²", sale_m2), ft.Container(expand=1, content=ft.Column(controls=[actual_margin]))),
            pricing_warning,
        ]),
        block("Điều chỉnh giá", [
            margin, total_quantity, manual_flag, manual_sale,
            small("Biên lợi nhuận gộp: giá bán = giá vốn / (1 − biên gộp). "
                  "Trường 'Tổng số lượng' giữ nguyên để nhập, chưa dùng làm hệ số tính."),
        ]),
        block("Bổ sung chi phí", [
            ft.FilledTonalButton("Thêm vật tư điện", icon=ft.Icons.ELECTRICAL_SERVICES,
                                 height=48, on_click=lambda _: jump_to_category("Vật tư điện")),
            ft.OutlinedButton("Thêm chi phí thủ công", icon=ft.Icons.ADD,
                              height=48, on_click=lambda _: jump_to_category("Manual")),
            small("Các mục vật tư được giữ theo danh mục trong ảnh phần mềm gốc."),
        ]),
    ])

    # ---------------------------------------------------------------------
    # STEP 4: readable review, next actions, save draft
    # ---------------------------------------------------------------------
    review_id = ft.Text("Bản nháp mới", weight=ft.FontWeight.W_600)
    review_customer = ft.Text("Chưa nhập", weight=ft.FontWeight.W_600)
    review_module = ft.Text("Chưa nhập", weight=ft.FontWeight.W_600)
    review_area = ft.Text("—", weight=ft.FontWeight.W_600)
    review_lines = ft.Text("0", weight=ft.FontWeight.W_600)
    review_note = ft.Text("—", weight=ft.FontWeight.W_600, max_lines=3)
    review_hint = small("Kiểm tra thông tin trước khi lưu bản nháp.")

    def line(label, value):
        return ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                      controls=[small(label), ft.Container(expand=True, alignment=ft.Alignment.CENTER_RIGHT, content=value)])

    required_overview = ft.Text("Bắt buộc: 0/7 trường đã nhập", size=16,
                                weight=ft.FontWeight.BOLD, color=INK)
    missing_list = ft.Column(spacing=5)
    completion_button = ft.FilledButton(
        "Kiểm tra 7 trường bắt buộc", icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
        height=48, on_click=lambda _: check_required_and_store(),
    )
    stage4 = ft.Column(spacing=13, controls=[
        ft.Text("Rà soát báo giá", size=23, weight=ft.FontWeight.BOLD),
        small("Bước 4/4 · Xem toàn bộ trước khi lưu."),
        block("Trường bắt buộc", [
            required_overview,
            small("Dữ liệu thiếu sẽ được liệt kê và có nút đưa bạn đến đúng nơi nhập."),
            missing_list,
            completion_button,
            small("Lưu bản nháp được phép thiếu; thao tác kiểm tra sẽ từ chối nếu chưa đủ 7 trường."),
        ]),
        block("Thông tin chính", [
            line("Số bản nháp", review_id),
            line("Khách hàng", review_customer),
            line("Mã module", review_module),
            line("Diện tích", review_area),
            ft.TextButton("Chỉnh cấu hình", on_click=lambda _: set_step(0)),
        ]),
        block("Nội dung", [
            line("Dòng chi phí", review_lines),
            line("Ghi chú", review_note),
            ft.TextButton("Mở danh mục nội dung", on_click=lambda _: set_step(1)),
        ]),
        block("Kết quả báo giá", [
            reviewed_price, review_hint,
            ft.TextButton("Xem cách tính giá", on_click=lambda _: set_step(2)),
        ], "Bản nháp có thể được lưu dù chưa đủ đơn giá hoặc thông số kỹ thuật."),
    ])

    for key in ("so_module_w", "so_module_h", "so_module_du_phong",
                "module_rong_mm", "module_cao_mm", "module_pixel_w", "module_pixel_h"):
        inputs[key].on_change = lambda _: calculate()

    def make_snapshot() -> dict:
        return {
            "fields": {key: ctrl.value for key, ctrl in inputs.items()},
            "document_date": current["date"].strftime("%Y-%m-%d"),
            "total_quantity": total_quantity.value or "",
            "margin": margin.value or "",
            "manual_enabled": bool(manual_flag.value),
            "manual_sell": manual_sale.value or "",
            "lines": {cat: [
                {"name": row["name"].value or "", "qty": row["qty"].value or "",
                 "price": row["price"].value or ""} for row in entries
            ] for cat, entries in cost_rows.items()},
            "note": note.value or "",
            "attachment_names": list(file_names),
        }

    def calculate(_=None):
        snapshot_data = make_snapshot()
        fields_data = snapshot_data["fields"]
        try:
            specs = technical_result(fields_data)
            area_text.value = (fmt_number(specs.area_m2, 3) if specs.area_m2 is not None else "—")
            modules_text.value = fmt_int(specs.module_count)
            dimensions_text.value = (
                f"{fmt_number(specs.screen_width_mm, 1)} × {fmt_number(specs.screen_height_mm, 1)}"
                if specs.screen_width_mm is not None and specs.screen_height_mm is not None else "—"
            )
            resolution_text.value = (
                f"{fmt_int(specs.resolution_w)} × {fmt_int(specs.resolution_h)}"
                if specs.resolution_w is not None and specs.resolution_h is not None else "—"
            )
            pixel_text.value = fmt_int(specs.total_pixels)
            tech_warning.value = (
                "Dữ liệu kỹ thuật đã được tính từ thông số nhập vào."
                if specs.area_m2 is not None and specs.total_pixels is not None
                else "Cần W/H và kích thước/pixel một module để tính đầy đủ."
            )
        except ValueError as exc:
            specs = None
            area_text.value = modules_text.value = "—"
            dimensions_text.value = resolution_text.value = pixel_text.value = "—"
            tech_warning.value = str(exc)
        items = [CostLine(cat, row["name"].value or "", row["qty"].value or "",
                          row["price"].value or "")
                 for cat, entries in cost_rows.items() for row in entries]
        try:
            price = price_result(
                items, specs.area_m2 if specs else None,
                margin.value, manual_sale.value if manual_flag.value else None,
            )
            cost_total.value = fmt_money(price.cost)
            sale_total.value = fmt_money(price.selling)
            cost_m2.value = fmt_money(price.cost_per_m2)
            sale_m2.value = fmt_money(price.selling_per_m2)
            footer_price.value = fmt_money(price.selling)
            reviewed_price.value = fmt_money(price.selling)
            actual_margin.value = (
                "Biên gộp thực tế: " + fmt_number(price.gross_margin_percent, 2) + "%"
                if price.gross_margin_percent is not None else "Biên gộp thực tế: —"
            )
            if price.issues:
                pricing_warning.value = "Cần sửa: " + "; ".join(price.issues)
            elif price.completed_lines == 0:
                pricing_warning.value = "Chưa có dòng vật tư/chi phí hợp lệ."
            elif price.selling is None:
                pricing_warning.value = "Đã có giá vốn; nhập biên gộp hoặc tổng giá bán thủ công."
            else:
                pricing_warning.value = "Giá chỉ gồm chi phí đã khai báo; chưa kiểm tra đủ BOM."
        except ValueError as exc:
            cost_total.value = sale_total.value = cost_m2.value = sale_m2.value = "—"
            footer_price.value = reviewed_price.value = "Chưa đủ dữ liệu"
            pricing_warning.value = str(exc)
            actual_margin.value = "Biên gộp thực tế: —"
        refresh_review(snapshot_data)
        page.update()

    def refresh_review(data: dict):
        values = data["fields"]
        review_id.value = current["id"] or "Tạo mã khi lưu"
        review_customer.value = values.get("ma_khach_hang") or "Chưa nhập"
        review_module.value = values.get("ma_module") or "Chưa nhập"
        review_area.value = (area_text.value + " m²") if area_text.value != "—" else "—"
        review_lines.value = str(sum(len(v) for v in data["lines"].values()))
        review_note.value = (data["note"][:80] + "…" if len(data["note"]) > 80 else data["note"]) or "—"
        if pricing_warning.value.startswith("Giá chỉ gồm"):
            review_hint.value = "Bản nháp có giá tham khảo, chưa kiểm tra đủ vật tư hoặc VAT."
        else:
            review_hint.value = "Còn thông tin cần hoàn thiện trước khi phát hành báo giá."

    def update_required_ui(snapshot_data: dict | None = None):
        """Update progress without painting untouched empty fields in red."""
        data = snapshot_data if snapshot_data is not None else make_snapshot()
        config_done, config_total = required_progress(data, "Cấu hình")
        common_done, common_total = required_progress(data, "Thông tin chung")
        all_done, all_total = required_progress(data)
        issues = required_issues(data)
        missing_keys = {issue.key for issue in issues}
        config_required_note.value = f"Đã nhập {config_done}/{config_total} trường bắt buộc"
        common_required_note.value = f"Đã nhập {common_done}/{common_total} trường bắt buộc"
        required_overview.value = f"Đã nhập {all_done}/{all_total} trường bắt buộc"
        required_overview.color = ERROR if current["completion_attempted"] and issues else INK
        for key, ctrl in inputs.items():
            if key in required_specs_by_key:
                label = required_specs_by_key[key].label
                ctrl.error = (f"Vui lòng nhập {label}."
                              if current["completion_attempted"] and key in missing_keys else None)
        for sec in COMMON_SECTIONS:
            required_in_section = tuple(f for f in sec.fields if f.required)
            if not required_in_section:
                section_required_notes[sec.label].value = "Không có trường bắt buộc trong nhóm này"
                section_required_notes[sec.label].color = MUTED
                continue
            found = sum(str(data["fields"].get(f.key) or "").strip() != "" for f in required_in_section)
            remaining = len(required_in_section) - found
            section_required_notes[sec.label].value = (
                "Đã đủ trường bắt buộc" if remaining == 0
                else f"Cần bổ sung {remaining} trường bắt buộc"
            )
            section_required_notes[sec.label].color = (
                ERROR if current["completion_attempted"] and remaining else MUTED
            )
        missing_list.controls.clear()
        for issue in issues:
            missing_list.controls.append(ft.Container(
                padding=ft.Padding.symmetric(horizontal=9, vertical=7),
                bgcolor="#FFF8F6" if current["completion_attempted"] else "#F4F6FA",
                border_radius=9,
                content=ft.Row(spacing=5, controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE,
                            color=ERROR if current["completion_attempted"] else MUTED, size=17),
                    ft.Container(expand=True, content=ft.Text(issue.label, size=13)),
                    ft.TextButton("Điền ngay", on_click=lambda _, item=issue: jump_to_issue(item)),
                ]),
            ))
        if not issues:
            missing_list.controls.append(ft.Row(spacing=8, controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#237B53", size=19),
                ft.Text("Đã đủ 7 trường bắt buộc", color="#237B53", size=13),
            ]))

    required_specs_by_key = {f.key: f for f in REQUIRED_FIELDS}

    def on_required_change(key: str):
        update_required_ui()
        refresh_status()
        calculate()

    for spec in REQUIRED_FIELDS:
        inputs[spec.key].on_change = lambda _, key=spec.key: on_required_change(key)

    # ---------------------------------------------------------------------
    # Contextual navigation instead of 10 tabs and a huge continuous form
    # ---------------------------------------------------------------------
    stages = (stage1, stage2, stage3, stage4)
    progress_icons: list[ft.Container] = []
    for index, title in enumerate(STEPS):
        progress_icons.append(ft.Container(
            expand=1, padding=ft.Padding.symmetric(horizontal=3, vertical=10), border_radius=12,
            on_click=lambda _, i=index: set_step(i),
            content=ft.Column(spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                              controls=[ft.Icon(STEP_ICONS[index], size=21),
                                        ft.Text(title, size=10, text_align=ft.TextAlign.CENTER, max_lines=1)]),
        ))
    progress = ft.Container(bgcolor=ft.Colors.SURFACE,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                            content=ft.Row(spacing=5, controls=progress_icons))

    def set_step(index: int):
        current["step"] = max(0, min(3, index))
        if index != 1 and current["detail"] is not None:
            close_category()
        for idx, view in enumerate(stages):
            view.visible = idx == current["step"]
        for idx, tile in enumerate(progress_icons):
            active = idx == current["step"]
            tile.bgcolor = PALE if active else ft.Colors.SURFACE
            tile.border = ft.Border.all(1, "#BDD2EF" if active else ft.Colors.TRANSPARENT)
        previous.disabled = current["step"] == 0
        forward.content = "Lưu bản nháp" if current["step"] == 3 else "Tiếp tục"
        forward.icon = ft.Icons.SAVE_OUTLINED if current["step"] == 3 else ft.Icons.ARROW_FORWARD
        refresh_status()
        update_required_ui()
        calculate()

    def go_back(_):
        if current["detail"] is not None:
            close_category()
            return
        set_step(next_step(current["step"], -1))

    def next_action(_):
        if current["detail"] is not None:
            close_category()
            return
        if current["step"] == 3:
            save_quote()
        else:
            set_step(next_step(current["step"], +1))

    previous = ft.OutlinedButton("Quay lại", icon=ft.Icons.ARROW_BACK, expand=1, height=48,
                                 on_click=go_back)
    forward = ft.FilledButton("Tiếp tục", icon=ft.Icons.ARROW_FORWARD, expand=1, height=48,
                              on_click=next_action)
    save_top = ft.IconButton(icon=ft.Icons.SAVE_OUTLINED, tooltip="Lưu bản nháp",
                             on_click=lambda _: save_quote())
    edit_header = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
        ft.IconButton(icon=ft.Icons.CLOSE, tooltip="Trở về danh sách",
                      on_click=lambda _: confirm_close()),
        ft.Text("Lập báo giá LED", size=17, weight=ft.FontWeight.BOLD),
        save_top,
    ])
    stage_scroll = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=12,
                             controls=list(stages))
    editor = ft.Column(visible=False, expand=True, spacing=0, controls=[
        ft.Container(bgcolor=ft.Colors.SURFACE, padding=ft.Padding.symmetric(horizontal=6, vertical=4),
                     content=edit_header),
        progress,
        ft.Container(expand=True, padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                     content=stage_scroll),
        ft.Container(bgcolor=ft.Colors.SURFACE, padding=ft.Padding.symmetric(horizontal=12, vertical=9),
                     content=ft.Column(spacing=8, controls=[
                         ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                             small("Giá bán tạm tính"), footer_price,
                         ]),
                         ft.Row(spacing=8, controls=[previous, forward]),
                     ])),
    ])

    def populate(record: dict | None):
        current["completion_attempted"] = False
        current["id"] = record["id"] if record else None
        values = record["values"] if record else {}
        for spec in ALL_FIELDS:
            default = False if spec.kind == "checkbox" else ("0" if spec.key == "so_module_du_phong" else "")
            inputs[spec.key].value = values.get("fields", {}).get(spec.key, default)
        total_quantity.value = values.get("total_quantity", "")
        margin.value = values.get("margin", "")
        manual_flag.value = bool(values.get("manual_enabled", False))
        manual_sale.value = values.get("manual_sell", "")
        manual_sale.visible = manual_flag.value
        note.value = values.get("note", "")
        file_names[:] = values.get("attachment_names", [])
        file_info.value = ", ".join(file_names) if file_names else "Chưa chọn tệp"
        try:
            current["date"] = datetime.fromisoformat(values.get("document_date", ""))
        except ValueError:
            current["date"] = datetime.now()
        date_picker.value = current["date"]
        date_text.value = current["date"].strftime("%d/%m/%Y")
        certificate_text.value = current["id"] or "Tạo mã khi lưu"
        for cat in COST_TABS:
            cost_rows[cat].clear()
            cost_col[cat].controls.clear()
            for item in values.get("lines", {}).get(cat, []):
                add_cost_row(cat, item, update=False)
        close_category()
        set_step(0)
        update_required_ui()

    def open_editor(record=None):
        populate(record)
        home.visible = False
        editor.visible = True
        page.appbar.visible = False
        page.update()

    def close_editor():
        editor.visible = False
        home.visible = True
        page.appbar.visible = True
        refresh_home()

    def confirm_close():
        page.show_dialog(ft.AlertDialog(
            title=ft.Text("Rời biểu mẫu?"),
            content=ft.Text("Những thay đổi chưa lưu của phiên chỉnh sửa này sẽ không được ghi vào bản nháp."),
            actions=[
                ft.TextButton("Tiếp tục chỉnh sửa", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Rời biểu mẫu", on_click=lambda _: (page.pop_dialog(), close_editor())),
            ],
        ))

    def jump_to_issue(issue):
        if issue.step == 0:
            set_step(0)
        else:
            set_step(1)
            if issue.section in common_tiles:
                common_tiles[issue.section].expanded = True
            open_category("Thông tin chung")
        page.update()

    def check_required_and_store():
        current["completion_attempted"] = True
        data = make_snapshot()
        missing = required_issues(data)
        update_required_ui(data)
        refresh_status()
        if missing:
            jump_to_issue(missing[0])
            tip(f"Còn {len(missing)} trường bắt buộc. Đã mở nơi cần điền đầu tiên.")
            return
        save_quote(verified=True)

    def save_quote(*, verified: bool = False):
        nonlocal saved
        data = make_snapshot()
        if verified and required_issues(data):
            current["completion_attempted"] = True
            update_required_ui(data)
            tip("Cần nhập đủ 7 trường bắt buộc để xác nhận.")
            return
        try:
            validate_draft(data)
        except ValueError as exc:
            tip(str(exc))
            return
        id_ = current["id"] or create_id()
        now = datetime.now().isoformat(timespec="seconds")
        previous_record = next((q for q in saved if q["id"] == id_), None)
        record = {
            "id": id_, "created_at": previous_record["created_at"] if previous_record else now,
            "updated_at": now, "values": data,
            # This is NOT a published/approved quote: it only describes seven fields.
            "required_fields_complete": not bool(required_issues(data)),
        }
        try:
            saved = store.upsert(record)
        except (OSError, ValueError) as exc:
            tip(f"Chưa thể ghi bản nháp: {exc}")
            return
        current["id"] = id_
        close_editor()
        tip((f"Đã kiểm tra 7 trường bắt buộc và lưu bản nháp {id_}."
             if verified else f"Đã lưu bản nháp {id_} trên thiết bị."))

    def delete_record(id_: str):
        def confirmed(_):
            nonlocal saved
            try:
                saved = store.delete(id_)
            except (OSError, ValueError) as exc:
                tip(f"Không thể xóa: {exc}")
                page.pop_dialog()
                return
            page.pop_dialog()
            refresh_home()
        page.show_dialog(ft.AlertDialog(
            modal=True, title=ft.Text("Xóa bản nháp?"),
            content=ft.Text(f"Xóa {id_} khỏi dữ liệu cục bộ trên thiết bị?"),
            actions=[ft.TextButton("Hủy", on_click=lambda _: page.pop_dialog()),
                     ft.FilledButton("Xóa", on_click=confirmed)],
        ))

    search_home = field("Tìm báo giá", hint="Mã chứng từ, khách hàng, mã module")
    home_list = ft.Column(spacing=10)
    home_counter = ft.Text("0", size=28, weight=ft.FontWeight.BOLD, color=PRIMARY)
    home = ft.Column(expand=True, spacing=0, controls=[
        ft.Container(expand=True, padding=ft.Padding.all(13), content=ft.Column(
            expand=True, scroll=ft.ScrollMode.AUTO, spacing=14, controls=[
                ft.Container(
                    bgcolor=PALE, border_radius=20, padding=ft.Padding.all(18),
                    content=ft.Column(spacing=10, controls=[
                        ft.Text("Báo giá LED", color=INK, size=23, weight=ft.FontWeight.BOLD),
                        small("Tạo cấu hình, bổ sung vật tư và tính giá theo từng bước."),
                        ft.Row(spacing=9, controls=[
                            ft.Container(expand=True, content=ft.Column(spacing=1, controls=[
                                home_counter, small("Bản nháp cục bộ"),
                            ])),
                            ft.FilledButton("Tạo báo giá", icon=ft.Icons.ADD, height=48,
                                            on_click=lambda _: open_editor()),
                        ]),
                    ]),
                ),
                ft.Text("Bảng tính giá đã lưu", size=20, weight=ft.FontWeight.BOLD),
                search_home,
                home_list,
                small("Lưu cục bộ dưới dạng JSON. Không tự đồng bộ lên VPS, không phải báo giá đã phát hành."),
            ]),
        ),
    ])

    def refresh_home(_=None):
        home_counter.value = str(len(saved))
        q = fold(search_home.value or "")
        home_list.controls.clear()
        visible_count = 0
        for record in sorted(saved, key=lambda x: x.get("updated_at", ""), reverse=True):
            desc = quote_label(record["values"])
            if q and q not in fold(record["id"] + " " + desc):
                continue
            visible_count += 1
            id_ = record["id"]
            home_list.controls.append(ft.Container(
                bgcolor=ft.Colors.SURFACE, border=ft.Border.all(1, BORDER),
                border_radius=17, padding=ft.Padding.all(14),
                content=ft.Column(spacing=10, controls=[
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        ft.Text(id_, size=14, weight=ft.FontWeight.BOLD, color=INK),
                        ft.Container(bgcolor=PALE, padding=ft.Padding.symmetric(horizontal=9, vertical=5),
                                     border_radius=15, content=ft.Text("Bản nháp", size=11, color=PRIMARY)),
                    ]),
                    ft.Text(desc, size=15),
                    small(f"Trường bắt buộc: {required_progress(record['values'])[0]}/7 đã nhập"),
                    small("Cập nhật: " + record.get("updated_at", "").replace("T", " ")),
                    ft.Row(spacing=8, controls=[
                        ft.FilledTonalButton("Sửa", icon=ft.Icons.EDIT_OUTLINED,
                                             height=48, expand=1,
                                             on_click=lambda _, entry=record: open_editor(entry)),
                        ft.OutlinedButton("Xóa", icon=ft.Icons.DELETE_OUTLINE,
                                          height=48, expand=1,
                                          on_click=lambda _, key=id_: delete_record(key)),
                    ]),
                ]),
            ))
        if visible_count == 0:
            home_list.controls.append(block("Chưa có dữ liệu phù hợp", [
                small("Chọn Tạo báo giá để bắt đầu, hoặc thử từ khóa khác."),
            ]))
        page.update()

    search_home.on_change = refresh_home
    page.appbar = ft.AppBar(
        title=ft.Text("ERP Báo giá LED", weight=ft.FontWeight.W_600, size=17),
        center_title=True, bgcolor=ft.Colors.SURFACE,
    )
    for idx, view in enumerate(stages):
        view.visible = idx == 0
    page.add(ft.SafeArea(expand=True, content=ft.Column(
        expand=True, spacing=0, controls=[home, editor],
    )))
    set_step(0)
    update_required_ui()
    refresh_home()
    if storage_error:
        tip(storage_error + " — nên kiểm tra bản lưu cục bộ trước khi tiếp tục.")


if __name__ == "__main__":
    ft.run(main)
