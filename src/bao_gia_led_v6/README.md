# LED Quote Mobile V6 — Nhận diện & kiểm tra trường bắt buộc (Flet 1.1.2)

V6 nâng cấp **trực tiếp** từ Mobile ERP báo giá LED V5. Vẫn giữ kiến trúc bốn bước, 10 danh mục, 16 trường Thông tin chung, tính toán LED, nhập chi phí và lưu bản nháp JSON. Chỉ bổ sung nguyên tắc UI và nghiệp vụ cho các trường bắt buộc mà người dùng đã xác nhận.

## Khởi chạy

Trên Windows, mở PowerShell tại thư mục này:

```powershell
py -m pip install -r requirements.txt
py app.py
```

Chạy tất cả kiểm thử:

```powershell
py -m unittest discover -v
```

## Bảy trường bắt buộc

| Nhóm | Trường | Key |
| --- | --- | --- |
| Bước 1 — Cấu hình | Loại màn hình | `loai_man_hinh` |
| Bước 1 — Cấu hình | Loại trình chiếu | `loai_trinh_chieu` |
| Bước 1 — Cấu hình | Hãng module | `hang_module` |
| Bước 1 — Cấu hình | Mã module | `ma_module` |
| Bước 2 — Thông tin chung | Hãng nguồn | `hang_nguon` |
| Bước 2 — Thông tin chung | Mã nguồn | `ma_nguon` |
| Bước 2 — Thông tin chung | Loại khung | `loai_khung` |

Các trường còn lại **không tự được coi là bắt buộc**. Nếu có thêm trường bắt buộc, chỉ cần đặt `required=True` trong `Field(...)` ở `form_schema.py`; bộ kiểm tra sử dụng cùng một schema.

## UI/UX được bổ sung

1. Nhãn của trường bắt buộc luôn có dấu **`*`**. Phía trên hai khu vực có chú thích: “* Bắt buộc để kiểm tra hoàn tất. Có thể lưu nháp trước”.
2. **Bộ đếm trực tiếp**: màn hình Cấu hình hiện 0/4; Thông tin chung hiện 0/3; Rà soát hiện 0/7. Khi nhập/xóa giá trị, bộ đếm cập nhật.
3. Mục **Thông tin chung** trong danh sách danh mục có trạng thái số trường đã nhập. Mỗi nhóm thu gọn có dòng trạng thái riêng, nhờ vậy người dùng không phải mở tất cả nhóm để tìm trường thiếu.
4. **Không tô đỏ khi mới mở biểu mẫu.** Chỉ sau khi bấm “Kiểm tra 7 trường bắt buộc”, những ô trống mới hiện đường viền lỗi và thông báo “Vui lòng nhập [tên trường].” (`TextField.error` của Flet 1.1.x).
5. Màn **Rà soát** có danh sách trường còn thiếu và nút **Điền ngay** cho từng trường. Nếu bấm Kiểm tra khi thiếu, hệ thống chuyển đến bước phù hợp; với Thông tin chung, mở đúng nhóm `ExpansionTile` chứa trường thiếu.
6. Khi nhập một giá trị hợp lệ sau bước kiểm tra, cảnh báo của chính ô đó sẽ được xóa ngay.
7. Danh sách bản nháp hiện tiến độ 0/7 ... 7/7 mà không giả định đã có đơn giá hoặc BOM.

## Hai hành động phải được phân biệt

### Lưu bản nháp

- Nút Lưu ở trên hoặc cuối quy trình vẫn cho phép lưu khi thiếu trường bắt buộc.
- Đây là **bản nháp**, không phải chứng từ đã duyệt/phát hành.
- Giữ toàn bộ dữ liệu chưa hoàn thiện, tránh mất công nhập khi người dùng phải dừng công việc.
- Thuộc tính JSON `required_fields_complete` cho biết cả bảy trường đã được điền hay chưa. Trường này không chứng minh báo giá có đủ vật tư hoặc giá bán.

### Kiểm tra 7 trường bắt buộc

- Nằm tại **Bước 4 — Rà soát**, chỉ tiếp tục khi đủ 7 trường. Khoảng trắng không được coi là dữ liệu hợp lệ.
- Nếu còn thiếu: hiện thông báo, đánh dấu các trường trống, dẫn về trường thiếu đầu tiên. Không tự tạo bản ghi hoàn tất.
- Nếu đã đủ: chạy tiếp kiểm tra dữ liệu số hiện hữu, rồi lưu **bản nháp đã đủ bảy trường**. Hệ thống **không** tự phát hành, phê duyệt hoặc gửi báo giá.

## Nơi chỉnh sửa

- `form_schema.py`: cờ `Field.required` cho từng trường.
- `required_validation.py`: kiểm tra dữ liệu thuần Python, nhóm trường, danh sách lỗi và điểm đến.
- `app.py`: dấu sao, tiến độ, trạng thái nhóm, `TextField.error`, nút kiểm tra và điều hướng.
- `test_required_validation.py`: kiểm thử riêng cho bảy trường, khoảng trắng, đủ/thiếu và tương thích bản nháp V5.

## Ghi chú nghiệp vụ và tương thích

- Các ô lookup vẫn nhập tay được; chưa có nguồn dữ liệu SKU hay danh sách hãng thực. Dấu `*` không thay thế việc xác minh mã sản phẩm khi kết nối API.
- Những trường như số module W/H, kích thước kỹ thuật, số lượng card/bộ nguồn và đơn giá **không** được suy đoán hay tự buộc nhập thêm.
- V6 dùng tiếp thư mục lưu mặc định `~/.bao_gia_led_v5/drafts.json` nhằm cho phép đọc bản nháp V5; không xóa hoặc ghi đè dữ liệu trước khi người dùng lưu. Có thể đặt tệp riêng bằng biến môi trường `LED_QUOTE_DATA_FILE`.
- Bộ quy tắc này phải được **xác thực lại tại FastAPI** khi triển khai backend; UI validation chỉ giúp người dùng thao tác, không đủ để bảo vệ tính toàn vẹn dữ liệu trên server.
- Kiểm thử logic thuần Python thành công. Có thêm kiểm tra mô phỏng dựng cây control và sự kiện bằng *Flet stub*. Đây **không** phải kiểm thử render/native Flet 1.1.2; cần thử trên điện thoại thực để kiểm tra bàn phím, cuộn và focus.

## Tài liệu tham khảo

- Flet TextField (kế thừa `FormFieldControl.error`): https://flet.dev/docs/controls/textfield/
- Flet FormFieldControl: https://flet.dev/docs/controls/formfieldcontrol/
- Flet ExpansionTile: https://flet.dev/docs/controls/expansiontile/
- Flet 1.1 và InputDecorationTheme: https://flet.dev/blog/flet-v-1-1-release-announcement/
- Material text fields / required marker: https://m2.material.io/design/components/text-fields.html
- GOV.UK field-level error + summary: https://design-system.service.gov.uk/components/error-message/
