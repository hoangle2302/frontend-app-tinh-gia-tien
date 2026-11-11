# TOÀN TRUNG — Flet 1.1.2 + FastBusiness (ERP-only)

Ứng dụng hiện **bắt buộc xác thực với FastBusiness**. Không có tài khoản mặc định, chế độ bỏ qua xác thực, dữ liệu giá linh kiện tự sinh hoặc preset báo giá dựng sẵn.

## Cài đặt trên Windows

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python tools/check_erp_connection.py
python main.py
```

Sửa `.env` trước khi chạy, ví dụ:

```ini
FASTBUSINESS_BASE_URL=http://192.168.2.62
FASTBUSINESS_DATABASE=TOANTRUNG_FBISP2421_A
FASTBUSINESS_UNIT=CTY
FASTBUSINESS_TIMEOUT=15
FASTBUSINESS_VERIFY_TLS=true
```

`192.168.2.62` là địa chỉ trong đoạn mã tham chiếu của dự án; chỉ dùng được khi thiết bị đang ở mạng có thể truy cập máy chủ này. Nếu có địa chỉ khác, thay `FASTBUSINESS_BASE_URL`. Không nhập hoặc lưu mật khẩu trong `.env`; nhập trực tiếp trên màn hình đăng nhập.

## Kết nối FastBusiness

1. `POST /Main/Login.aspx/GetEntityData`
2. `POST /Main/Login.aspx/GetUnitData`
3. `POST /Main/Login.aspx/Refresh`
4. `POST /Main/Login.aspx/Challenge`
5. Tính challenge-MD5 tương thích giao thức FastBusiness cũ.
6. `POST /Main/Login.aspx/Login`: **chỉ mở MainView khi `d == true`**.
7. `GET /Main/zCostingSheet.aspx`, đọc chuỗi `cookie` được trả về trong trang.
8. `POST /FastBusiness.DataService.asmx/GetCompletionList` với controller `zdmloaimh` để lấy **Loại màn hình**.

Response `d.Rows` có thể là danh sách hai phần tử như `[["1", "Indoor"], ["2", "Outdoor"]]`. Hàm `parse_screen_types()` chuẩn hóa chúng thành cặp `code`/`name`. Giao diện chỉ hiển thị các lựa chọn thực sự được ERP trả về; trường này bắt buộc trước khi tính giá.

Toàn bộ phiên HTTPX nằm trong `app/fastbusiness/client.py`; `app/fastbusiness/service.py` xử lý phiên đăng nhập. Tác vụ kết nối chạy qua `asyncio.to_thread()` để UI Flet không bị đóng băng. Khi đăng xuất, phiên và cookie HTTPX được đóng.

## Phạm vi dữ liệu thực tế

- **FastBusiness:** đăng nhập và danh mục **Loại màn hình** (`zdmloaimh`) lấy từ máy chủ thật.
- **SQLite cục bộ:** người dùng tự tạo/sửa danh mục linh kiện, báo giá và hồ sơ. Lúc cài mới, sản phẩm trống; **không tự tạo mã hay đơn giá sản phẩm**.
- **Chưa tích hợp:** nguồn, module, cabinet, hãng, báo giá từ FastBusiness, vì chưa được cung cấp controller/API phù hợp. Không được hiểu dữ liệu SQLite là dữ liệu đồng bộ ERP.
- **Loại màn hình không còn dữ liệu hardcode trên UI**: dropdown lấy danh mục ERP thực tế; `[["1", "Indoor"], ["2", "Outdoor"]]` được chuyển thành các lựa chọn mã `1`/`2`. Engine vẫn nhận `indoor`/`outdoor` để tương thích. Các tùy chọn khác như Online/Offline vẫn là tùy chọn nghiệp vụ, chưa phải danh mục từ API.

Nếu dùng một database SQLite cũ đã có các sản phẩm dựng sẵn, bản này **không tự xóa dữ liệu người dùng**. Để có kho dữ liệu trống, tạo database mới bằng đường dẫn khác trong `DB_PATH` (sao lưu file cũ trước).

## Kiểm thử

```powershell
python -m pytest -q tests/test_fastbusiness_client.py tests/test_calculator.py tests/test_local_inventory_without_demo.py
# Khi Flet 1.1.2 được cài và có môi trường UI:
python -m pytest -q tests/test_ui_screen_types.py
python -m compileall -q app ui database engine main.py
```

Các kiểm thử dùng `httpx.MockTransport` để mô phỏng phản hồi mạng, **không phải** xác nhận đã kết nối ERP nội bộ. Để thử thật, chạy `python tools/check_erp_connection.py` khi ở cùng LAN hoặc VPN.

## Bảo mật

- FastBusiness sử dụng challenge-MD5 theo giao thức hiện tại; tương thích với ERP, không thay thế TLS.
- Máy chủ ví dụ dùng HTTP nội bộ. Không mở trực tiếp ERP ra Internet. Sử dụng HTTPS nếu máy chủ hỗ trợ, hoặc LAN/VPN đã được bảo vệ.
- Không log mật khẩu, cookie phiên hay token; không commit `.env` vào Git.

## Thư mục

```text
app/bootstrap.py                 # Khởi tạo trang, logout
app/config.py                    # Cấu hình tập trung
app/fastbusiness/client.py       # HTTPX / xác thực / danh mục ERP
app/fastbusiness/service.py      # Dịch vụ đăng nhập ERP-only
ui/features/auth/                # Form và xử lý đăng nhập
ui/features/estimates/           # Lập dự toán và danh mục Loại màn hình ERP
ui/features/inventory/           # Dữ liệu linh kiện SQLite do người dùng tạo
ui/features/quotes/              # Báo giá SQLite
ui/theme/                        # Theme và tokens
engine/                          # Tính toán / xuất báo giá
database/                        # SQLite, không seed dữ liệu tự sinh
```
