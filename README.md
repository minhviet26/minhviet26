- 👋 Hi, I’m Trần Minh Việt
- 👀 I’m interested in technology
- 🌱 I’m currently learning TDC

## Ứng dụng quản lý nhắc lịch hẹn

Chương trình dòng lệnh giúp lưu trữ thông tin lịch hẹn với khách hàng và tự
động nhắc việc trên máy tính.

### Tính năng chính

- Lưu họ tên, số điện thoại, xe/đời xe và thời gian cần nhắc khách hàng.
- Tự động kiểm tra và hiển thị thông báo (sử dụng [plyer](https://github.com/kivy/plyer)).
- Danh sách lịch hẹn được lưu trong cơ sở dữ liệu SQLite nội bộ.

### Yêu cầu hệ thống

- Python >= 3.10
- Thư viện `plyer` để kích hoạt thông báo (tùy chọn nhưng được khuyến nghị).

### Cài đặt phụ thuộc

```bash
python -m pip install --upgrade pip
pip install plyer
```

### Cách chạy

```bash
python reminder_app.py
```

Khi chạy, chương trình hiển thị menu:

1. Thêm lịch hẹn mới.
2. Xem danh sách tất cả lịch hẹn.
3. Thoát chương trình.

Ứng dụng sẽ chạy nền để tự động gửi thông báo mỗi phút cho những lịch hẹn đến
thời gian nhắc nhở.
