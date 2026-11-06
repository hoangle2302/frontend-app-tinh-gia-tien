# Báo giá Màn hình LED

Ứng dụng desktop/mobile viết bằng Python và [Flet](https://flet.dev/) để quản lý linh kiện, tính giá và lập báo giá màn hình LED. Dữ liệu được lưu cục bộ bằng SQLite trong file `bom_led.db`.

## 1. Yêu cầu môi trường

- Python 3.10 trở lên.
- Git.
- Để build Android: Android Studio, Android SDK, JDK và Flutter SDK.
- Để chạy Android Emulator: tạo sẵn một thiết bị ảo Android trong Android Studio.

## 2. Clone mã nguồn

```bash
git clone https://github.com/hoangle2302/frontend-app-tinh-gia-tien.git
cd frontend-app-tinh-gia-tien
```

## 3. Tạo và cài môi trường Python

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu PowerShell chặn kích hoạt môi trường ảo, chạy một lần:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Chạy ứng dụng

Đảm bảo đang ở thư mục gốc dự án và môi trường `.venv` đã được kích hoạt:

```bash
python main.py
```

Lần chạy đầu tiên sẽ khởi tạo/cập nhật cấu trúc database và dữ liệu mẫu trong `bom_led.db`.

## 5. Chạy kiểm thử

```bash
pytest
```

## 6. Build ứng dụng

### Build Android APK

Kiểm tra thiết bị và công cụ Android trước khi build:

```bash
flutter doctor
adb version
```

Build APK bằng Flet:

```bash
flet build apk
```

APK thường được tạo trong thư mục `build\apk\`. Có thể chỉ định thư mục đầu ra:

```bash
flet build apk --output build\apk
```

### Build ứng dụng Windows

```powershell
flet build windows
```

File cài đặt/đóng gói sẽ nằm trong thư mục `build\windows\`.

> Khi build lại sau khi thay đổi mã nguồn, nên xóa output build cũ nếu gặp lỗi cache:
>
> ```powershell
> Remove-Item -Recurse -Force build\apk
> flet build apk
> ```

## 7. Đưa APK lên Android Emulator

### Cách 1: Cài APK đã build bằng ADB

1. Mở Android Studio và khởi động một thiết bị trong **Device Manager**.
2. Kiểm tra emulator đã được nhận:

   ```powershell
   adb devices
   ```

   Kết quả phải có một thiết bị ở trạng thái `device`.

3. Cài APK:

   ```powershell
   adb install -r build\apk\frontend-app-tinh-gia-tien.apk
   ```

   Nếu tên file APK khác, thay bằng đúng đường dẫn file được tạo trong `build\apk`.

4. Mở ứng dụng từ màn hình emulator. Nếu cần gỡ bản cũ:

   ```powershell
   adb uninstall com.flet.frontend_app_tinh_gia_tien
   ```

### Cách 2: Chạy trực tiếp bằng Flet

Sau khi đã khởi động Android Emulator:

```powershell
flet run --android
```

Lệnh này build/chuyển ứng dụng lên thiết bị Android đang kết nối và thuận tiện cho việc thử nghiệm nhanh.

## 8. Cấu trúc thư mục chính

```text
main.py                 # Điểm khởi chạy ứng dụng
requirements.txt        # Các package Python
bom_led.db              # Database SQLite
database/               # Schema và lớp quản lý database
engine/                 # Logic tính toán và xuất dữ liệu
ui/                     # Giao diện Flet
assets/                 # Tài nguyên giao diện
tests/                  # Test tự động
build/                  # Các file build, không cần sửa mã nguồn tại đây
```

## 9. Một số lỗi thường gặp

### Không tìm thấy lệnh `flet`

Kiểm tra môi trường ảo đã được kích hoạt, sau đó cài lại dependency:

```powershell
python -m pip install -r requirements.txt
```

Có thể chạy Flet qua Python để tránh lỗi PATH:

```powershell
python -m flet build apk
```

### `adb devices` không hiển thị emulator

- Đảm bảo emulator đã khởi động hoàn toàn.
- Bật **USB debugging** trong tùy chọn nhà phát triển nếu dùng điện thoại thật.
- Kiểm tra lại Android SDK Platform-Tools và biến môi trường `PATH`.

### Build Android thất bại

Chạy các lệnh sau để kiểm tra thiếu công cụ hoặc cấu hình:

```powershell
flutter doctor -v
flet --version
```

