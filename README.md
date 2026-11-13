# BrainTumor AI

Mã nguồn cho dự án **brain-tumor-segmentation**. Repository không chứa dataset MRI, checkpoint, metadata/evaluation model hoặc database cá nhân. Sau khi clone, chuẩn bị Python/Node theo hướng dẫn dưới đây và dùng `scripts/prepare_model.py --bundle <thư-mục-bundle-V2>` để nhập model riêng. Không có model thì giao diện/API vẫn mở được, chức năng chạy AI sẽ báo chưa sẵn sàng.

Notebook huấn luyện được chia sẻ tại [`notebooks/training.ipynb`](notebooks/training.ipynb), đã bỏ output và trạng thái thực thi. Kiểm thử backend dùng ảnh tổng hợp được đánh dấu rõ, không cần dataset riêng. Browser/inference tests cần chuẩn bị dữ liệu và model có quyền sử dụng tại máy chạy kiểm thử.

**Khởi động:** mở [`START_BRAINTUMOR.cmd`](START_BRAINTUMOR.cmd), bấm **Thêm ca MRI** rồi tự chọn bốn ảnh. Không cần mở riêng backend/frontend. Xem [hướng dẫn chọn file](docs/07-THEM-CA-MRI.md).

Lịch sử rà soát: [thay đổi và kết quả kiểm thử nền tảng](docs/04-RA-SOAT-VA-CAI-THIEN.md). Các bước mở hai terminal bên dưới dành cho chế độ phát triển.

Ứng dụng nghiên cứu phân đoạn u não MRI: **React + Vite + Tailwind CSS · Python + FastAPI · PyTorch + MONAI · PostgreSQL + SQLAlchemy · NiiVue · NiBabel + NumPy**.

Chuẩn công nghệ và luồng dữ liệu: [kiến trúc công nghệ](docs/00-KIEN-TRUC-CONG-NGHE.md). Dùng `START_POSTGRES_DEMO.cmd` cho PostgreSQL qua Docker, hoặc `START_BRAINTUMOR.cmd` để chạy local với SQLite.

Xem [báo cáo rà soát hiện tại](docs/08-KIEM-TRA-TOAN-DU-AN.md). [Ảnh và kết quả bàn giao 1.1 ban đầu](docs/06-KIEM-THU-VA-BAN-GIAO-1.1.md) được giữ làm lịch sử; một số màn hình trong đó đã thay đổi.

Mã nguồn được tạo riêng, không sửa hoặc xoá notebook, dataset và checkpoint trong thư mục cha.

## Bắt đầu từ bước 1

Xem [hướng dẫn từng bước và từng file](docs/01-KHOI-TAO-VA-TUNG-FILE.md). Kiến trúc và hợp đồng API ở [docs/02-KIEN-TRUC-VA-API.md](docs/02-KIEN-TRUC-VA-API.md).

Ảnh ứng dụng và kết quả kiểm thử thực tế: [docs/03-KIEM-THU.md](docs/03-KIEM-THU.md).

### 1. Chuẩn bị thư mục và môi trường

Khuyến nghị chép **BrainTumorAI/** vào ổ SSD local trước khi cài môi trường. Google Drive có thể gây lỗi khi tạo `node_modules`, `.venv` và khóa SQLite.

Yêu cầu: Python 3.11–3.13, Node.js 22.12+ hoặc 24, trình duyệt hỗ trợ WebGL2. GPU CUDA là tuỳ chọn. Dùng Python 3.12 cho Docker.

Mở PowerShell trong `BrainTumorAI/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
Copy-Item backend/.env.example backend/.env
```

PyTorch CUDA: chọn bản phù hợp với máy tại https://pytorch.org/get-started/locally/. Bản CPU vẫn chạy được nhưng chậm hơn.

### 2. Kết nối checkpoint đã train

Nếu dự án vẫn nằm cạnh `runs_v2/`:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_model.py
```

Nếu chuyển sang thư mục khác:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_model.py --bundle 'G:\duong-dan\BraTS2023_GLI\runs_v2\unet_v2_resumable_001\demo_bundle'
```

Script kiểm tra SHA-256 trước và sau khi sao chép, giữ nguyên source. Bản dự án tại workspace đã được import model.

### 3. Chạy backend

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-backend.ps1
```

- API: http://127.0.0.1:8000/api/health
- Swagger: http://127.0.0.1:8000/docs
- Script mặc định đặt SQLite và ảnh ca trong `%LOCALAPPDATA%\BrainTumorAI\storage` để tránh khóa file trên Drive.
- Chỉ chạy **một process API**. Không thêm `--workers 2`: hàng đợi inference thuộc process hiện tại.
- Có thể chạy thủ công: `cd backend` rồi `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Khi đó cấu hình đọc từ `backend/.env`, đường dẫn tương đối tính từ gốc dự án.

### 4. Chạy frontend trong PowerShell thứ hai

```powershell
cd frontend
npm ci
npm run dev
```

Mở http://127.0.0.1:5173. Vite chuyển `/api` đến backend; không cần hardcode URL cho ảnh MRI.

### 5. Phân tích MRI

1. Bấm **Thêm ca MRI**, nhập tên ca ẩn danh.
2. Chọn đủ T1n, T1c, T2w, T2-FLAIR dạng `.nii` hoặc `.nii.gz`.
3. Mở ca, bấm **Phân đoạn với AI**.
4. Xem ba mặt phẳng/3D, đổi modality, bật/tắt lớp phủ và chỉnh opacity.
5. Tải mask NIfTI, PDF và JSON sau khi hoàn tất.

Ảnh đầu vào phải cùng shape và affine, đã đăng ký theo protocol BraTS. Backend kiểm tra NIfTI, giá trị hữu hạn, tín hiệu, affine và giới hạn kích thước trước khi lưu ca. Không thực hiện skull stripping, registration, crop hay resample. Header không khai báo đơn vị được hiểu là mm theo BraTS và được đánh dấu trong giao diện.

## Checkpoint và kết quả đã đối chiếu

| Nội dung | Giá trị |
|---|---|
| Thí nghiệm | `unet_v2_resumable_001` |
| Checkpoint cuối đã đọc | `unet3d_brats_last (14).pth`, epoch **50**, `complete=True` |
| Checkpoint đưa vào inference | Bản được chọn tại epoch **45**, không phải trọng số epoch cuối |
| Mô hình | MONAI 3D U-Net, 4 kênh đầu vào, 4 lớp đầu ra |
| SHA-256 weights | `dbba1a212c9c8e0443d3c7fd763e22f9eb3ec80ce7fb4451c231ff0bebe0892f` |
| Validation | 183 ca, Dice mean **0.875809** |
| Held-out test | 194 ca, Dice mean **0.893744** |
| Dice WT / TC / ET trên test | **0.920528 / 0.908923 / 0.851781** |

Nguồn số liệu: `model_metadata.json` và `evaluation.json` trong export gốc. Đây là số liệu **đã ghi nhận trong lần train**, chưa được chạy lại toàn bộ trong quá trình xây dựng ứng dụng. Môi trường nguồn dùng Torch `2.14.1+cu130`, MONAI `1.6.1`; môi trường máy này khác phiên bản. Load và smoke test kiểm tra tính chạy được, không chứng minh kết quả số học hoàn toàn giống nguồn.

Tên export gốc `unet_v1_demo.pth` là tên cũ; protocol bên trong xác nhận V2. Không suy luận phiên bản từ tên file.

## Database và lưu trữ

- Local: SQLite, hai bảng `cases` và `jobs`; metadata nằm trong DB, file MRI/mask/PDF nằm trên ổ đĩa.
- Docker: PostgreSQL 17 + volume lưu file. Chạy `python scripts/prepare_model.py` trước.

```powershell
# Chọn mật khẩu URL-safe (chữ, số, dấu gạch); không commit vào Git.
$env:POSTGRES_PASSWORD = 'thay-bang-mat-khau-cua-ban'
docker compose up --build
```

Mở http://127.0.0.1:8080. Docker mặc định chạy CPU. PostgreSQL và casefiles dùng named volumes. API và web chỉ bind localhost. Docker cần Docker Desktop; cấu hình này chưa được xác nhận bằng một lần chạy Docker nếu Docker không có trong máy.

## Kiểm tra

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test.ps1
.\.venv\Scripts\python.exe scripts/smoke_model.py
cd frontend
npm test
npm run build
npm run format:check
```

Trên hệ điều hành khác, chạy `python -m pytest tests -q` từ `backend/`. Script Windows tạo thư mục test mới trong `%LOCALAPPDATA%/BrainTumorAI-tests` để tránh thư mục temp pytest cũ đang bị khóa.

API tests dùng model giả rõ ràng để kiểm tra vòng đời case/job/artifact, không tạo chỉ số mô hình. `smoke_model.py` chạy **trọng số thật** với input tổng hợp 32³, patch vẫn 96³ theo protocol. Chỉ kiểm tra forward, nhãn và affine đầu ra; không đánh giá độ chính xác trên dữ liệu tổng hợp.

## Giới hạn vận hành hiện tại

- Bản local một người dùng. Chưa có đăng nhập/phân quyền; không đưa trực tiếp lên mạng công cộng.
- Một worker inference, hàng đợi có giới hạn. Khi server khởi động lại, job chưa xong được đánh dấu failed để chạy lại, không báo thành công giả.
- Thanh tiến độ là các giai đoạn xử lý, không phải tỷ lệ số patch đã chạy.
- Chưa có DICOM/PACS, đánh giá ground truth cho ca tải lên hoặc hiệu chuẩn lâm sàng.
- Font giao diện tải từ Google Fonts nếu có mạng; có fallback hệ thống. MRI vẫn được xử lý ở backend local.
- Hệ thống phục vụ nghiên cứu/minh hoạ; kết quả không thay thế chẩn đoán y khoa.

Không xoá checkpoint cũ chỉ vì hậu tố `(1)`, `(2)`…: chúng có thể là các trạng thái huấn luyện khác nhau do Drive lưu trùng tên. Dọn các file đó cần đối chiếu nội dung và giữ best/last/recovery riêng.
