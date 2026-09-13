# Triangle Studio 2.0 · Mô hình tam giác

Bản nâng cấp từ ứng dụng **Vẽ Tam Giác 1.10** của bạn. Vẫn là ứng dụng desktop Python/Tkinter, chuyên tạo **tam giác vuông nổi trên màn hình**. Không cần tài khoản, không gửi dữ liệu ra mạng khi sử dụng.

## Chạy trên Windows

1. Giải nén toàn bộ thư mục `TriangleStudio_2.0` ra một nơi cố định.
2. Máy cần Python **3.10 trở lên**, có **Tcl/Tk**. Khi cài Python, chọn **Add python.exe to PATH**.
3. Nhấp đúp **CAI_DAT.bat** một lần. Bản đã sửa sẽ kiểm tra Python chạy được, bỏ qua đường dẫn Launcher bị hỏng và tìm bản còn hoạt động. File này tạo môi trường `.venv` riêng và tải Pillow để xuất PNG (bước cài đặt cần Internet).
4. Nhấp đúp **CHAY_UNG_DUNG.bat**. Những lần sau chỉ cần mở file này.

Nếu đã có Python/Tkinter, có thể chạy ngay `python main.py`; chỉ tính năng xuất PNG cần Pillow. Không sử dụng lại thư mục `venv` của bản cũ vì môi trường Python không phù hợp để chuyển nguyên giữa các máy.

### Chạy từ PyCharm / VS Code

Mở cả thư mục dự án, chọn trình thông dịch `.venv\Scripts\python.exe`, rồi chạy `main.py`.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Trên Linux/macOS: dùng Python có Tkinter, cài `requirements.txt` vào môi trường ảo rồi chạy `python main.py`. Phần nền tam giác nổi trong suốt sử dụng khả năng riêng của Windows; trên hệ khác, hình nổi có thể có nền đặc. File PNG/SVG xuất ra vẫn có nền trong suốt.

## Có gì mới?

- Giao diện tối xanh ngọc, bố cục bảng điều khiển + khung xem trước + thẻ thông số.
- Xem trước theo thời gian thực, có lưới, tên đỉnh A/B/C, độ dài cạnh và dấu góc vuông.
- Nhập chiều rộng/cao từ **20 đến 3.000 px**, đồng bộ hai cạnh để tạo tam giác vuông cân.
- Bốn mẫu kích thước: vuông cân, tỉ lệ 3:4, dáng cao, dáng rộng.
- Xoay liên tục, xoay nhanh 90°, lật ngang/dọc.
- Sáu màu nhanh, chọn màu tự do, màu viền độc lập, độ dày viền 1–12 px, bật/tắt tô nền.
- Độ hiển thị 15–100%, áp dụng trực tiếp cho hình nổi và ảnh xuất. Nút **Aurora** chọn nhanh phong cách xanh ngọc trong suốt.
- Kéo hình nổi bằng chuột trái; co giãn bằng chuột phải; con lăn đổi kích thước.
- Bật/tắt luôn nổi, khóa di chuyển/co giãn, đưa hình về giữa màn hình.
- Tính diện tích, chu vi, cạnh huyền và các góc của tam giác vuông theo kích thước thật đang nhập.
- Hoàn tác/làm lại tối đa 60 trạng thái hình trong phiên làm việc.
- Lưu tối đa 50 mẫu có tên; nhập/xuất thiết lập và bộ mẫu bằng JSON.
- Xuất **PNG có alpha** và **SVG vector** giữ màu, độ hiển thị, xoay/lật, kích thước.
- Tự lưu bằng thao tác thay thế tệp nguyên khối; hỗ trợ đọc cấu hình v1.10 và giữ bản sao khi cấu hình v2 bị lỗi.

## Thao tác nhanh

| Thao tác | Tác dụng |
|---|---|
| F2 | Hiện / ẩn tam giác nổi |
| Esc | Ẩn tam giác, giữ bảng điều khiển mở |
| Ctrl+S | Lưu cấu hình ngay |
| Ctrl+Z / Ctrl+Y | Hoàn tác / làm lại thiết lập hình |
| Ctrl+E | Xuất PNG |
| Chuột trái trên hình nổi | Kéo di chuyển |
| Chuột phải trên hình nổi | Kéo sang phải tăng rộng; kéo lên tăng cao |
| Con lăn trên hình nổi | Tăng / giảm kích thước khoảng 5% |
| Con lăn trong xem trước | Thay độ phóng đại xem trước, không đổi kích thước hình |
| Vừa khung | Đưa xem trước về mức tự căn vừa cửa sổ |

Phím tắt hoạt động khi ứng dụng hoặc hình nổi đang được chọn; không phải phím tắt toàn hệ thống. Ctrl+S/Z/Y/E dùng ở bảng điều khiển; F2/Esc dùng cả ở hình nổi. Khi chỉ vẽ viền, kéo trực tiếp đường viền của hình. Khóa ngăn thao tác chuột trên hình nổi; bạn vẫn chỉnh thiết lập từ bảng điều khiển được.

Kích thước là **pixel trong hệ tọa độ Tk**, không phải cm hoặc thước đo vật lý đã hiệu chuẩn. Bản xem trước tự thu vừa khung. Góc A ở đầu cạnh cao, B là góc vuông, C ở cuối cạnh rộng; xoay/lật không đổi tên đỉnh hay các thông số. PNG/SVG chỉ chứa tam giác, không chứa lưới, nhãn hoặc bảng số liệu. Ảnh có chừa lề nhỏ để viền không bị cắt.

## Dữ liệu và cấu hình cũ

- Bản `config.json` của bạn vẫn được giữ trong dự án. Khi chưa có cấu hình v2, ứng dụng đọc kích thước **970 × 970**, đồng bộ, vị trí và độ hiển thị cũ; giữ màu xanh lá của v1.
- Sau đó, cấu hình v2 nằm ở `%LOCALAPPDATA%\TriangleStudio\settings.json` trên Windows, tách khỏi mã nguồn và tệp EXE.
- Không tự bật hình nổi khi mở ứng dụng, để bạn xem trước và chọn vị trí trước. Nhấn **F2** để bật.
- Muốn thử diện mạo mới: chọn mẫu **Tỉ lệ 3 : 4**, mở tab **Màu sắc** → **Áp dụng phong cách Aurora**.
- **Khôi phục hình mặc định** chỉ đặt lại hình, không xóa bộ mẫu. Có thể hoàn tác.
- Nhập JSON yêu cầu xác nhận thay thiết lập và bộ mẫu. Bản trước khi nhập được giữ ở `before-import.json`, cùng thư mục cấu hình; có thể dùng nút nhập để khôi phục. Hoàn tác chỉ phục hồi thiết lập hình, không khôi phục danh sách mẫu/vị trí.
- Nếu tệp `settings.json` bị hỏng, ứng dụng báo trên thanh trạng thái và giữ bản `settings.json.invalid.bak` đầu tiên để xem lại.
- Vị trí hình nổi được giữ trong vùng màn hình chính khi bật; hình quá lớn vẫn có thể vượt mép phải/dưới. Dùng bảng điều khiển để giảm kích thước. Không có chế độ click xuyên hình.

## Tạo EXE mới

Sau khi chạy `CAI_DAT.bat`, nhấp đúp **TAO_EXE.bat** trên Windows. Script cài PyInstaller và dùng `TriangleStudio.spec` để tạo:

```text
dist\TriangleStudio_2.0.exe
```

Bản bàn giao **chưa kèm EXE 2.0 dựng sẵn**. Không chạy `VeTamGiac_1.10.exe` của gói cũ để xem giao diện mới. Tệp EXE mới phải được dựng trên Windows; môi trường kiểm thử bản bàn giao là Linux. Nếu muốn EXE đọc cấu hình v1 ở lần mở đầu, đặt `config.json` bên cạnh EXE trước khi mở (khi chưa có settings v2).

## Cấu trúc mã nguồn

| Tệp | Vai trò |
|---|---|
| `main.py` | Giao diện, trạng thái, hoàn tác, mẫu và thao tác người dùng |
| `triangle_logic.py` | Hình học, kiểm tra giá trị, xuất PNG/SVG |
| `overlay.py` | Cửa sổ nổi và thao tác chuột |
| `config_manager.py` | Lưu nguyên khối, chuyển cấu hình cũ sang định dạng mới |
| `TIM_PYTHON.bat` | Tìm Python hoạt động thay vì gọi bản mặc định có thể đã bị xóa |
| `TriangleStudio.spec` | Cấu hình đóng gói EXE |
| `tests/` | Kiểm thử tính toán, dữ liệu, xuất tệp và giao diện |
| `legacy_v1/` | Mã nguồn v1.10 gốc để bạn đối chiếu |
| `docs/` | Ảnh giao diện thực tế và ghi nhận kiểm thử |

## Đưa lên GitHub

Copy các tệp/thư mục trong bản mới vào thư mục kho bạn đang theo dõi. Giữ `.git` của kho hiện tại. Kiểm tra Changes → nhập `Nâng cấp Triangle Studio 2.0` → Commit → Push origin. `.gitignore` đã loại trừ môi trường ảo, build, dist và bộ nhớ đệm Python.

## Chạy kiểm thử

Từ thư mục dự án:

```bash
python -m unittest discover -s tests -v
```

Các kiểm thử giao diện cần môi trường có màn hình và Tkinter; chúng tự bỏ qua nếu không có màn hình. Xem `docs/KIEM_THU.md` để biết phần nào đã được kiểm chứng và phần nào cần kiểm tra trên Windows.
