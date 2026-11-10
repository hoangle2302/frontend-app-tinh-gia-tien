import flet as ft


def main(page: ft.Page):
    page.title = "Mobile ERP Báo Giá LED - Flet 1.1.2"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F4F6F9"
    page.padding = 0

    # Khung chuẩn Mobile
    page.window.width = 400
    page.window.height = 860
    page.window.resizable = True

    def show_toast(message: str):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message), duration=2000
        )
        page.snack_bar.open = True
        page.update()

    # Style dùng chung cho các ô Input/Dropdown trên Mobile
    dense_pad = ft.Padding.symmetric(horizontal=10, vertical=9)

    # =========================================================================
    # 1. HEADER CỦA POPUP: TIÊU ĐỀ + 3 NÚT ICON BUTTON
    # =========================================================================
    popup_header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        ft.Icons.RECEIPT_LONG_ROUNDED,
                        size=20,
                        color=ft.Colors.PRIMARY,
                    ),
                    ft.Text(
                        "Lập báo giá màn hình",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
            ),
            ft.Row(
                spacing=4,
                tight=True,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.EDIT_NOTE,
                        tooltip="Chỉnh sửa thủ công",
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        icon_size=18,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.all(7),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=lambda e: show_toast("Chỉnh sửa thủ công"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ATTACH_FILE,
                        tooltip="Tệp đính kèm",
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        icon_size=18,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.all(7),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=lambda e: show_toast("Tệp đính kèm"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.STICKY_NOTE_2_OUTLINED,
                        tooltip="Ghi chú",
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        icon_size=18,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.all(7),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=lambda e: show_toast("Ghi chú"),
                    ),
                ],
            ),
        ],
    )

    # =========================================================================
    # 2. MAIN_1: THIẾT KẾ UI/UX CHO 17 TRƯỜNG TRONG ẢNH
    # =========================================================================

    # --- KHỐI 1.1: Thanh Thông tin chứng từ (Số CT, Ngày lập, Trạng thái) ---
    inp_ngay_lap = ft.TextField(
        label="Ngày lập *",
        value="09/11/2026",
        expand=5,
        text_size=12,
        dense=True,
        border_radius=8,
        content_padding=dense_pad,
        suffix_icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
    )

    inp_so_chung_tu = ft.TextField(
        label="Số CT *",
        value="404",
        expand=3,
        text_size=12,
        text_align=ft.TextAlign.RIGHT,
        dense=True,
        border_radius=8,
        content_padding=dense_pad,
    )

    sel_trang_thai_ct = ft.Dropdown(
        label="Trạng thái",
        value="0",
        expand=6,
        dense=True,
        text_size=12,
        border_radius=8,
        content_padding=dense_pad,
        options=[
            ft.DropdownOption(key="0", text="0. Lập chứng từ"),
            ft.DropdownOption(key="1", text="1. Chờ duyệt"),
            ft.DropdownOption(key="2", text="2. Đã duyệt"),
        ],
    )

    voucher_meta_row = ft.Row(
        spacing=6,
        controls=[inp_ngay_lap, inp_so_chung_tu, sel_trang_thai_ct],
    )

    # --- KHỐI 1.2: 4 Ô Tra cứu Cấu hình (Loại màn hình, Trình chiếu, Hãng, Mã module) ---
    sel_loai_man_hinh = ft.Dropdown(
        label="Loại màn hình *",
        expand=1,
        dense=True,
        text_size=12,
        border_radius=8,
        content_padding=dense_pad,
        options=[
            ft.DropdownOption(key="indoor", text="LED Indoor"),
            ft.DropdownOption(key="outdoor", text="LED Outdoor"),
            ft.DropdownOption(key="lcd", text="Màn ghép LCD"),
        ],
    )

    sel_loai_trinh_chieu = ft.Dropdown(
        label="Loại trình chiếu *",
        expand=1,
        dense=True,
        text_size=12,
        border_radius=8,
        content_padding=dense_pad,
        options=[
            ft.DropdownOption(key="sync", text="Đồng bộ (Online)"),
            ft.DropdownOption(key="async", text="Không đồng bộ"),
        ],
    )

    sel_hang_module = ft.Dropdown(
        label="Hãng module *",
        expand=1,
        dense=True,
        text_size=12,
        border_radius=8,
        content_padding=dense_pad,
        options=[
            ft.DropdownOption(key="qiangli", text="Qiangli"),
            ft.DropdownOption(key="gkgd", text="GKGD"),
            ft.DropdownOption(key="lampro", text="Lampro"),
        ],
    )

    sel_ma_module = ft.Dropdown(
        label="Mã module *",
        expand=1,
        dense=True,
        text_size=12,
        border_radius=8,
        content_padding=dense_pad,
        options=[
            ft.DropdownOption(key="p25_in", text="P2.5 Indoor (320x160)"),
            ft.DropdownOption(key="p3_in", text="P3.0 Indoor (192x192)"),
            ft.DropdownOption(key="p4_out", text="P4.0 Outdoor (320x160)"),
        ],
    )

    # --- KHỐI 1.3: Nhập kích thước Số lượng Module (W x H + Dự phòng) ---
    # Hàm tự động tính toán KT hiển thị, Độ phân giải, Tổng module, Tổng pixel
    def recalc_specs(e=None):
        try:
            w = int(inp_so_mod_w.value or 0)
            h = int(inp_so_mod_h.value or 0)
            dp = int(inp_so_mod_du_phong.value or 0)
        except ValueError:
            w, h, dp = 0, 0, 0

        # Giả định 1 tấm module chuẩn 320x160mm, độ phân giải 128x64 px
        kt_w = w * 320
        kt_h = h * 160
        res_w = w * 128
        res_h = h * 64
        tong_mod = (w * h) + dp
        tong_px = res_w * res_h

        val_kt_w.value = f"{kt_w:,}"
        val_kt_h.value = f"{kt_h:,}"
        val_res_w.value = f"{res_w:,}"
        val_res_h.value = f"{res_h:,}"
        val_tong_module.value = f"{tong_mod:,}"
        val_tong_pixel.value = f"{tong_px:,}"
        page.update()

    inp_so_mod_w = ft.TextField(
        label="Số module (W)",
        value="0",
        expand=1,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.RIGHT,
        text_size=13,
        dense=True,
        border_radius=8,
        content_padding=dense_pad,
        on_change=recalc_specs,
    )

    inp_so_mod_h = ft.TextField(
        label="Số module (H)",
        value="0",
        expand=1,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.RIGHT,
        text_size=13,
        dense=True,
        border_radius=8,
        content_padding=dense_pad,
        on_change=recalc_specs,
    )

    inp_so_mod_du_phong = ft.TextField(
        label="Dự phòng",
        value="0",
        expand=1,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.RIGHT,
        text_size=13,
        dense=True,
        border_radius=8,
        content_padding=dense_pad,
        on_change=recalc_specs,
    )

    # --- KHỐI 1.4: Bảng Dashboard Thông số tự động tính (Read-only Spec Card) ---
    val_kt_w = ft.Text("0", size=12, weight=ft.FontWeight.BOLD)
    val_kt_h = ft.Text("0", size=12, weight=ft.FontWeight.BOLD)
    val_res_w = ft.Text("0", size=12, weight=ft.FontWeight.BOLD)
    val_res_h = ft.Text("0", size=12, weight=ft.FontWeight.BOLD)
    val_tong_module = ft.Text(
        "0", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY
    )
    val_tong_pixel = ft.Text(
        "0", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY
    )

    def build_spec_box(title: str, w_ctrl: ft.Text, h_ctrl: ft.Text, unit: str):
        return ft.Container(
            expand=1,
            bgcolor=ft.Colors.SURFACE,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            content=ft.Column(
                spacing=2,
                tight=True,
                controls=[
                    ft.Text(
                        title, size=10, color=ft.Colors.ON_SURFACE_VARIANT
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("W:", size=11, color=ft.Colors.OUTLINE),
                            w_ctrl,
                            ft.Text("×", size=11, color=ft.Colors.OUTLINE),
                            ft.Text("H:", size=11, color=ft.Colors.OUTLINE),
                            h_ctrl,
                            ft.Text(unit, size=10, color=ft.Colors.OUTLINE),
                        ],
                    ),
                ],
            ),
        )

    spec_summary_card = ft.Container(
        bgcolor="#EEF2F6",
        border_radius=8,
        padding=ft.Padding.all(8),
        content=ft.Column(
            spacing=6,
            tight=True,
            controls=[
                # Hàng trên: KT hiển thị (W x H) | Độ phân giải (W x H)
                ft.Row(
                    spacing=6,
                    controls=[
                        build_spec_box(
                            "KT hiển thị (W × H)", val_kt_w, val_kt_h, "mm"
                        ),
                        build_spec_box(
                            "Độ phân giải (W × H)", val_res_w, val_res_h, "px"
                        ),
                    ],
                ),
                # Hàng dưới: Tổng module | Tổng pixel
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Container(
                            expand=1,
                            bgcolor=ft.Colors.SURFACE,
                            border_radius=6,
                            padding=ft.Padding.symmetric(
                                horizontal=8, vertical=5
                            ),
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Tổng module:",
                                        size=11,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                    val_tong_module,
                                ],
                            ),
                        ),
                        ft.Container(
                            expand=1,
                            bgcolor=ft.Colors.SURFACE,
                            border_radius=6,
                            padding=ft.Padding.symmetric(
                                horizontal=8, vertical=5
                            ),
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Tổng pixel:",
                                        size=11,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                    val_tong_pixel,
                                ],
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    # --- KHỐI 1.5: Ô Diễn giải ---
    inp_dien_giai = ft.TextField(
        label="Diễn giải",
        hint_text="Nhập ghi chú hoặc diễn giải cấu hình...",
        width=float("inf"),
        text_size=12,
        dense=True,
        border_radius=8,
        content_padding=dense_pad,
    )

    # TỔNG HỢP MAIN_1
    popup_main_1 = ft.Column(
        spacing=10,
        tight=True,
        controls=[
            ft.Text(
                "1. Thông tin chứng từ & Cấu hình Module",
                size=12,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.PRIMARY,
            ),
            # Hàng 1: Ngày lập | Số CT | Trạng thái
            voucher_meta_row,
            # Hàng 2: Loại màn hình | Loại trình chiếu
            ft.Row(
                spacing=8, controls=[sel_loai_man_hinh, sel_loai_trinh_chieu]
            ),
            # Hàng 3: Hãng module | Mã module
            ft.Row(spacing=8, controls=[sel_hang_module, sel_ma_module]),
            # Hàng 4: Số module (W) | Số module (H) | Dự phòng
            ft.Row(
                spacing=6,
                controls=[inp_so_mod_w, inp_so_mod_h, inp_so_mod_du_phong],
            ),
            # Hàng 5: Bảng đối chiếu tự động KT hiển thị, Độ phân giải, Tổng module, Tổng pixel
            spec_summary_card,
            # Hàng 6: Diễn giải
            inp_dien_giai,
        ],
    )

    # =========================================================================
    # 3. MAIN_2: GIỮ NGUYÊN 2 Ô SELECT (THÔNG TIN & VẬT TƯ)
    # =========================================================================
    select_1 = ft.Dropdown(
        label="Thông tin",
        expand=1,
        dense=True,
        text_size=12,
        border_radius=8,
        content_padding=dense_pad,
        options=[
            ft.DropdownOption(key="cat_1", text="Thông tin chung"),
            ft.DropdownOption(key="cat_2", text="Thông tin pro"),
            ft.DropdownOption(key="cat_3", text="Thông tin chi tiết"),
            ft.DropdownOption(key="cat_4", text="Thông tin chi card"),
        ],
    )

    select_2 = ft.Dropdown(
        label="Vật tư",
        expand=1,
        dense=True,
        text_size=12,
        border_radius=8,
        content_padding=dense_pad,
        options=[
            ft.DropdownOption(key="active", text="Vật tư điện"),
            ft.DropdownOption(key="pending", text="Vật tư cơ khí"),
            ft.DropdownOption(key="closed", text="Vật tư tủ điện"),
        ],
    )

    popup_main_2 = ft.Column(
        spacing=8,
        tight=True,
        controls=[
            ft.Text(
                "2. Danh mục Thông tin & Vật tư",
                size=12,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.PRIMARY,
            ),
            ft.Row(spacing=8, controls=[select_1, select_2]),
        ],
    )

    # =========================================================================
    # 4. FOOTER: ĐỐI CHIẾU SONG SONG CHI PHÍ & GIÁ BÁN THEO M2
    # =========================================================================
    inp_tong_so_luong = ft.TextField(
        label="Tổng số lượng",
        value="0.00",
        expand=1,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.RIGHT,
        text_size=12,
        border_radius=8,
        dense=True,
        content_padding=dense_pad,
    )

    inp_bien_do_loi_nhuan = ft.TextField(
        label="Biên lợi nhuận",
        value="0.00",
        suffix=ft.Text(" %", size=11, color=ft.Colors.ON_SURFACE_VARIANT),
        expand=1,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.RIGHT,
        text_size=12,
        border_radius=8,
        dense=True,
        content_padding=dense_pad,
    )

    inp_tong_chi_phi = ft.TextField(
        label="Tổng chi phí",
        value="0",
        expand=1,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.RIGHT,
        text_size=12,
        border_radius=8,
        dense=True,
        content_padding=dense_pad,
    )

    inp_don_gia_chi_phi_m2 = ft.TextField(
        label="Đơn giá chi phí",
        value="0",
        suffix=ft.Text(" / m2", size=11, color=ft.Colors.ON_SURFACE_VARIANT),
        expand=1,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.RIGHT,
        text_size=12,
        border_radius=8,
        dense=True,
        content_padding=dense_pad,
    )

    inp_tong_gia_ban = ft.TextField(
        label="Tổng giá bán",
        value="0",
        expand=1,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.RIGHT,
        text_size=12,
        border_radius=8,
        dense=True,
        content_padding=dense_pad,
    )

    inp_don_gia_ban_m2 = ft.TextField(
        label="Đơn giá giá bán",
        value="0",
        suffix=ft.Text(" / m2", size=11, color=ft.Colors.ON_SURFACE_VARIANT),
        expand=1,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.RIGHT,
        text_size=12,
        border_radius=8,
        dense=True,
        content_padding=dense_pad,
    )

    popup_footer = ft.Column(
        spacing=8,
        tight=True,
        controls=[
            ft.Text(
                "3. Tổng hợp Chi phí & Giá bán (m²)",
                size=12,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.PRIMARY,
            ),
            ft.Row(
                spacing=8,
                controls=[inp_tong_so_luong, inp_bien_do_loi_nhuan],
            ),
            ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    inp_tong_chi_phi,
                    ft.Icon(
                        ft.Icons.COMPARE_ARROWS_ROUNDED,
                        size=15,
                        color=ft.Colors.OUTLINE,
                    ),
                    inp_don_gia_chi_phi_m2,
                ],
            ),
            ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    inp_tong_gia_ban,
                    ft.Icon(
                        ft.Icons.COMPARE_ARROWS_ROUNDED,
                        size=15,
                        color=ft.Colors.OUTLINE,
                    ),
                    inp_don_gia_ban_m2,
                ],
            ),
        ],
    )

    # =========================================================================
    # 5. NÚT HÀNH ĐỘNG LƯU & HỦY
    # =========================================================================
    popup_actions = ft.Row(
        spacing=10,
        controls=[
            ft.OutlinedButton(
                content="Hủy",
                icon=ft.Icons.CLOSE,
                expand=1,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                on_click=lambda e: setattr(
                    popup_menu_container, "visible", False
                )
                or page.update(),
            ),
            ft.FilledButton(
                content="Lưu báo giá",
                icon=ft.Icons.SAVE_OUTLINED,
                expand=1,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                on_click=lambda e: show_toast("Đã lưu chứng từ #404!"),
            ),
        ],
    )

    # =========================================================================
    # 6. ĐÓNG GÓI CARD POPUP & KHUNG CHÍNH
    # =========================================================================
    popup_menu_container = ft.Container(
        visible=True,  # Mở sẵn để bạn xem ngay giao diện Main_1
        bgcolor=ft.Colors.SURFACE,
        border_radius=14,
        padding=ft.Padding.all(12),
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        shadow=ft.BoxShadow(
            blur_radius=12,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
        content=ft.Column(
            spacing=10,
            tight=True,
            controls=[
                popup_header,
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                popup_main_1,
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                popup_main_2,
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                popup_footer,
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                popup_actions,
            ],
        ),
    )

    def toggle_new_popup(e):
        popup_menu_container.visible = not popup_menu_container.visible
        page.update()

    main_buttons_row = ft.Row(
        spacing=8,
        controls=[
            ft.FilledTonalButton(
                content="Mới",
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                expand=1,
                height=38,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                on_click=toggle_new_popup,
            ),
            ft.OutlinedButton(
                content="Sửa",
                icon=ft.Icons.EDIT_OUTLINED,
                expand=1,
                height=38,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
            ),
            ft.OutlinedButton(
                content="Xóa",
                icon=ft.Icons.DELETE_OUTLINE,
                expand=1,
                height=38,
                style=ft.ButtonStyle(
                    color=ft.Colors.ERROR,
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
            ),
        ],
    )

    page.appbar = ft.AppBar(
        title=ft.Text("Quản lý Báo giá LED", size=16, weight=ft.FontWeight.W_600),
        center_title=True,
        bgcolor=ft.Colors.SURFACE,
        toolbar_height=46,
    )

    page.add(
        ft.Container(
            expand=True,
            padding=ft.Padding.all(10),
            content=ft.Column(
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                controls=[main_buttons_row, popup_menu_container],
            ),
        )
    )


if __name__ == "__main__":
    ft.run(main)