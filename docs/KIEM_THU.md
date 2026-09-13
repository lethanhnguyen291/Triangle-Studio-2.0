# Ghi nhận kiểm thử · Triangle Studio 2.0

Bản bàn giao đã chạy **16 kiểm thử thành công, không có kiểm thử bị bỏ qua trong lần chạy cuối**. Môi trường: Python 3.12.14, Pillow 12.3.0, Tk 8.6.14 trên Linux với màn hình X11 ảo.

## Đã kiểm chứng

- Tam giác 400 × 300 cho diện tích 60.000 px², cạnh huyền 500 px và chu vi 1.200 px.
- Xoay ở 6 góc và 4 tổ hợp lật giữ nguyên độ dài cạnh, diện tích; hộp ảnh chứa đủ hình.
- Từ chối số không hợp lệ, kích thước ngoài giới hạn, NaN/Infinity, màu sai và cờ sai kiểu.
- Đồng bộ vuông cân và chuẩn hóa góc xoay.
- PNG có alpha: nền ngoài hình trong suốt, phần tô và phần chỉ viền đúng; SVG hợp lệ về XML.
- Đọc cấu hình cũ 970 × 970 và vị trí 706/897; giữ lựa chọn đồng bộ và màu xanh lá cũ.
- Lưu/đọc cấu hình cùng mẫu tiếng Việt; không để lại tệp tạm sau khi ghi thành công.
- Cấu hình hỏng được báo lỗi và có bản sao; dữ liệu nhập sai không ghi đè cấu hình hợp lệ.
- Nhập liệu sai trên giao diện không làm mất hình hợp lệ gần nhất; mẫu nhanh sửa được trường đang nhập sai.
- Đồng bộ kích thước cập nhật thẻ thống kê và khóa ô chiều cao.
- Hoàn tác, làm lại và thay đổi mới sau hoàn tác.
- Hiện/ẩn hình nổi nhiều lần tái sử dụng cùng cửa sổ; kéo, co giãn, khóa và ẩn hoạt động.
- Lưu mẫu, nhập/xuất JSON, sao lưu trước khi nhập và lưu lại thiết lập.
- Mở ba tab ở cửa sổ tối thiểu; không có lỗi callback Tk trong kiểm thử giao diện.

Ảnh `giao-dien-2.0.png`, `mau-sac-2.0.png` và `cua-so-nho-2.0.png` chụp trực tiếp ứng dụng đang chạy. Đã xem lại bố cục ở 1220 × 850 và 980 × 680, điều chỉnh kích thước chữ của thẻ số liệu theo chiều rộng.

## Cần kiểm chứng trên Windows

- Độ trong suốt theo màu nền của cửa sổ nổi, icon/taskbar, hiển thị với mức DPI của máy người dùng.
- Chạy các script `.bat`, dựng EXE bằng PyInstaller và mở EXE trên Windows sạch.

Không có EXE 2.0 dựng sẵn trong gói này. Các bài kiểm thử cửa sổ chạy trên Linux dùng nền đặc; kết quả đó không thay thế kiểm thử nền trong suốt riêng của Windows.

## Bản sửa bộ khởi chạy sau bàn giao

CAI_DAT.bat và CHAY_UNG_DUNG.bat đã được cập nhật, có thêm TIM_PYTHON.bat để bỏ qua đường dẫn Launcher bị hỏng và kiểm tra Python thực sự chạy được. Đã rà soát luồng lệnh, nhãn nhảy và định dạng CRLF; chưa thực thi các file BAT trên Windows. Không chạy lại 16 kiểm thử giao diện/hình học vì bản sửa này không thay đổi mã Python.
