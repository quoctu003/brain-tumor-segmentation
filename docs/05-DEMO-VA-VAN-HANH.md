# Khởi động và vận hành

## Mở ứng dụng

Nhấp đúp **`START_BRAINTUMOR.cmd`** tại gốc dự án. Trình duyệt mở **http://127.0.0.1:8080**. Giao diện và API dùng chung địa chỉ; không cần mở riêng hai terminal. File `DEMO_BRAINTUMOR.cmd` là tên tương thích cũ và cũng mở trang chủ, không tự nhập ca hay kết quả.

Bấm **Thêm ca MRI**, tự chọn bốn chuỗi xung của một ca, tạo ca rồi bấm **Phân đoạn với AI**. Xem [hướng dẫn từng file và ba ca khác nhau](07-THEM-CA-MRI.md). Ảnh mới được kiểm tra trước khi lưu; AI chạy khi bạn bấm nút phân đoạn.

Lần đầu cần Python 3.11–3.13 và Node.js 22.12+ hoặc 24. Launcher chuẩn bị dependencies nếu thiếu và build giao diện khi mã thay đổi; cần mạng nếu phải tải thư viện. Khi bản build đã sẵn và mã không đổi, không cần Node để phục vụ ứng dụng. Font giao diện có fallback hệ thống khi không có mạng.

Giữ cửa sổ launcher mở trong khi dùng. Nhấn **Ctrl+C** để dừng. Launcher chờ tối đa 30 giây trước khi dừng cưỡng bức; job chưa xong được đánh dấu thất bại vào lần khởi động sau. Ca và kết quả đã lưu được giữ lại. Chỉ dùng một API process cho cùng vùng dữ liệu; không thêm `--workers 2`.

Mở lại file CMD khi ứng dụng đang chạy sẽ mở lại trang đó. Nếu cổng 8080 bị chương trình khác chiếm:

```powershell
python scripts/launch.py --port 8081
```

Các lệnh hỗ trợ, chạy tại gốc dự án:

```powershell
python scripts/launch.py --check          # Chỉ kiểm tra điều kiện
python scripts/launch.py --prepare-only   # Chuẩn bị môi trường/build, không chạy server
python scripts/launch.py --no-browser     # Chạy và không tự mở trình duyệt
python scripts/launch.py --verify         # Kiểm tra UI/API/model status rồi dừng server thử
```

`--prepare-only` có thể build giao diện trong khi server đang mở. Sau khi build, tải lại trình duyệt bằng **Ctrl+F5**. Nếu sửa backend thì dừng và khởi động lại ứng dụng. Khi dùng terminal với `.venv`, gọi `.\.venv\Scripts\python.exe` thay cho `python` để dùng đúng môi trường.

## Xem và xuất kết quả

Sau khi AI hoàn tất, đổi chuỗi xung, cuộn lát cắt, bật/tắt lớp phủ, điều chỉnh opacity hoặc chọn **3D**. Thể tích WT/TC/ET có phần chồng nhau, không cộng ba số này.

**Tải toàn bộ kết quả** xuất ZIP chứa mask NIfTI, PDF có biểu đồ, JSON và README. Có thể tải riêng từng file. **Phân tích lại** tạo một job mới; các kết quả trước vẫn có trong **Lịch sử phân tích**. Chỉ hiển thị kết quả khi các artifact đã được ghi xong.

Trang **Hệ thống** hiển thị database thực đang dùng, model, hàng đợi, dung lượng trống và phiên bản runtime. Nếu model không nạp được, xem thông báo tại đây và log backend; nút phân đoạn không được bật.

## Dữ liệu và log

Mặc định launcher lưu tại:

```text
%LOCALAPPDATA%/BrainTumorAI/
  storage/                Database, bản sao MRI và kết quả
  logs/setup.log          Cài dependencies và build giao diện
  logs/backend.log        API, model và lỗi inference
```

Các biến môi trường `STORAGE_DIR`, `DATABASE_URL`, `MODEL_PATH`, `MODEL_METADATA_PATH`, `FRONTEND_DIST` đổi cấu hình. Đường dẫn tương đối tính từ gốc dự án. Xóa ca trong ứng dụng chỉ xóa bản sao do ứng dụng quản lý; dữ liệu gốc bên ngoài vẫn được giữ.

## PostgreSQL

Mở `START_POSTGRES_DEMO.cmd` khi Docker Desktop đang chạy. Script chạy PostgreSQL, FastAPI và nginx/frontend tại cổng 8080; dừng bản local trước để tránh trùng cổng. Mật khẩu ngẫu nhiên được lưu tại `%LOCALAPPDATA%/BrainTumorAI/docker.env`. Dừng bằng `scripts/stop-postgres.ps1`; volume dữ liệu được giữ.

SQLite local và PostgreSQL Docker dùng hai kho dữ liệu riêng; chuyển chế độ không tự chuyển các ca đã tải. Chế độ PostgreSQL chưa được kiểm thử chạy thực tế trên máy hiện tại vì chưa có Docker. Xem [bảng công nghệ](00-KIEN-TRUC-CONG-NGHE.md).

## Kiểm thử và đóng gói

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test.ps1
python scripts/smoke_model.py
cd frontend
npm test
npm run format:check
npm run build
npm run test:e2e
```

Script backend chọn thư mục tạm riêng để tránh lỗi quyền của thư mục pytest mặc định trên Windows. Có thể gọi `python -m pytest` từ gốc nhờ `pytest.ini`; nếu gặp lỗi quyền Temp, dùng `scripts/test.ps1`.

Browser tests dùng Edge headless ở vị trí mặc định trên Windows; máy khác cần `npx playwright install chromium`. API kiểm thử dùng cổng 8086, database và storage riêng. Kiểm thử một ca thật bằng script riêng tại gốc dự án:

```powershell
python scripts/verify_case.py --case-dir data/mri_cases/BraTS-GLI-00016-000
```

Đóng gói tại gốc dự án:

```powershell
python scripts/launch.py --prepare-only
python scripts/package_release.py --output releases/BrainTumorAI-reviewed.zip
```

Script không ghi đè release đã tồn tại. ZIP chứa mã nguồn, bản build, checkpoint, bundle cũ và tài liệu; không chứa `.env`, database người dùng, `data/mri_cases`, môi trường Python, `node_modules` hoặc log. `RELEASE_MANIFEST.json` lưu SHA-256 từng file. File ZIP 1.1.0 cũ là ảnh chụp của bản giao diện ban đầu, không tự cập nhật theo workspace.

Ứng dụng phục vụ nghiên cứu local. Chưa có xác thực/phân quyền nhiều người dùng, migrations database, DICOM/PACS, xử lý MRI bệnh viện thô, queue phân tán hoặc xác nhận lâm sàng.
