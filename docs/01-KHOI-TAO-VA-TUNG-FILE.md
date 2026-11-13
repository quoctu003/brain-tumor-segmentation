# Bước 1 — Tạo dự án và hiểu từng file

Mục tiêu: tách ứng dụng sử dụng mô hình ra khỏi notebook huấn luyện. Notebook tiếp tục là nguồn thực nghiệm; ứng dụng chỉ thực hiện inference bằng checkpoint đã xác minh.

## 1. Cấu trúc

```text
BrainTumorAI/
├── README.md
├── .gitignore
├── .dockerignore
├── compose.yaml
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── schemas.py
│   │   ├── imaging.py
│   │   ├── inference.py
│   │   ├── reports.py
│   │   └── main.py
│   └── tests/
│       ├── test_api.py
│       └── test_imaging.py
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── index.html
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── main.tsx
│       ├── api.ts
│       ├── App.tsx
│       ├── UploadDialog.tsx
│       ├── MRIViewer.tsx
│       └── styles.css
├── models/
│   ├── README.md
│   ├── unet_v2_best.pth       [import từ export, không commit]
│   ├── model_metadata.json    [import từ export]
│   └── evaluation.json        [import từ export]
├── scripts/
│   ├── prepare_model.py
│   ├── smoke_model.py
│   ├── test.ps1
│   ├── start-backend.ps1
│   └── start-frontend.ps1
└── docs/
    ├── 01-KHOI-TAO-VA-TUNG-FILE.md
    ├── 02-KIEN-TRUC-VA-API.md
    ├── 03-KIEM-THU.md
    └── screenshots/
```

## 2. File gốc

| File | Vai trò | Khi cần sửa |
|---|---|---|
| `README.md` | Cài đặt, chạy, kết quả model và giới hạn | Khi thay đổi cách chạy hoặc phát hành |
| `.gitignore` | Loại môi trường, dữ liệu người dùng, model lớn và bản build khỏi Git | Khi thêm artifact mới |
| `.dockerignore` | Tránh đưa dataset, secrets và thư viện host vào Docker build context | Khi thêm thư mục runtime |
| `compose.yaml` | Ghép PostgreSQL, FastAPI và Nginx/React | Khi triển khai bằng Docker |

## 3. Backend: đi theo thứ tự này

| File | Nội dung chi tiết |
|---|---|
| `requirements.txt` | Dependencies runtime. Giới hạn major version; bản Torch/CUDA cần phù hợp máy. |
| `requirements-dev.txt` | Thêm pytest/httpx để kiểm thử API. |
| `.env.example` | Mẫu cấu hình DB, storage, model, device, CORS và giới hạn upload. Sao chép thành `.env` khi cài. |
| `app/__init__.py` | Khai báo package Python. |
| `app/config.py` | Đọc `.env` và biến môi trường. Đường dẫn tương đối được giải từ thư mục gốc BrainTumorAI. |
| `app/database.py` | SQLAlchemy engine/session và bảng Case/Job. SQLite bật foreign keys, WAL và busy timeout. |
| `app/schemas.py` | Kiểu JSON trả về; kiểm soát trường case và trạng thái job. |
| `app/imaging.py` | Đếm kích thước giải nén, kiểm tra bốn MRI, chuẩn hoá giống notebook, tính thể tích theo determinant affine. |
| `app/inference.py` | Xác minh SHA-256/protocol, dựng đúng U-Net, load strict, chạy patch 96³, ghép trên CPU, TTA nếu protocol bật, bỏ component nhỏ. |
| `app/reports.py` | Tạo PDF thực từ kết quả, nhãn vùng u và provenance model. Không tự tạo Dice cho ca mới. |
| `app/main.py` | App factory, lifespan, CORS, endpoints, upload theo chunk, hàng đợi 1 worker, cập nhật DB và tải artifact. |
| `tests/test_api.py` | Kiểm tra upload → job → PDF/JSON/mask → xoá; invalid input, giới hạn, tên file, database tồn tại qua restart. |
| `tests/test_imaging.py` | Kiểm tra affine/volume, giới hạn gzip, NaN, voxel count và chuẩn hoá giữ nền. |
| `Dockerfile` | Đóng gói backend Python 3.12. Không nhét model vào image; mount read-only. |

`Case` lưu: ID UUID, tên ẩn danh, ngày tạo, geometry JSON. `Job` lưu: case ID, trạng thái, progress, stage, thời gian, lỗi và result JSON.

## 4. Frontend: đi theo thứ tự này

| File | Nội dung chi tiết |
|---|---|
| `package.json` | Dependencies và ba lệnh dev/build/preview. |
| `package-lock.json` | Khoá cây dependency để `npm ci` tái lập cài đặt. |
| `index.html` | HTML entry, viewport, ngôn ngữ và title. |
| `tsconfig.json` | TypeScript strict, ES2022 và JSX React. |
| `vite.config.ts` | Dev server và proxy `/api` sang localhost:8000. |
| `src/main.tsx` | Mount React, StrictMode và CSS. |
| `src/api.ts` | Types của case/job/model, fetch JSON có xử lý lỗi, URL MRI/artifact. |
| `src/App.tsx` | Thư viện, tìm kiếm/lọc, model card, workspace ca, poll job, chạy inference, tải kết quả, xoá ca có xác nhận. |
| `src/UploadDialog.tsx` | Form chọn 4 modality, tên ca, trạng thái upload và lỗi. Gửi multipart/FormData. |
| `src/MRIViewer.tsx` | Khởi tạo NiiVue, nạp NIfTI theo affine, tô màu từng label, chuyển multiplanar/3D, opacity và fullscreen. |
| `src/styles.css` | Thiết kế dark workspace, responsive desktop/mobile, trạng thái focus và reduced motion. |
| `Dockerfile` | Build React trên Node24, serve dist bằng Nginx. |
| `nginx.conf` | SPA fallback và reverse proxy `/api` đến backend trong Docker. |

MRI viewer được lazy-load để trang thư viện không phải tải toàn bộ thư viện hình ảnh ngay khi mở app. Dữ liệu trong dashboard được lấy từ API, không điền số ca mẫu.

## 5. Model và script

| File | Vai trò |
|---|---|
| `models/README.md` | Giải thích nguồn model và tên export cũ. |
| `models/unet_v2_best.pth` | Trọng số inference epoch45 từ run50; không chứa optimizer runtime cho app. |
| `models/model_metadata.json` | Architecture, modality order, preprocessing, protocol, hash và metrics. |
| `models/evaluation.json` | Kết quả gốc từng ca validation/test để truy xuất nguồn số liệu. |
| `scripts/prepare_model.py` | Import bản sao model đã kiểm hash, không sửa source. Hỗ trợ `--bundle`. |
| `scripts/smoke_model.py` | Chạy model thật trên dữ liệu tổng hợp để xác nhận forward/export; không báo accuracy giả. |
| `scripts/test.ps1` | Chạy pytest trên Windows với thư mục temp riêng, tránh thư mục pytest cũ bị khóa. |
| `scripts/start-backend.ps1` | Dùng Python trong .venv nếu có, đặt runtime storage trên ổ local và khởi động Uvicorn một process. |
| `scripts/start-frontend.ps1` | Mở Vite ở frontend bằng npm run dev. Cần npm ci trước. |

## 6. Kiểm tra hoàn thành bước 1

1. `prepare_model.py` báo hash đúng, training_epochs=50, selected_epoch=45.
2. `/api/health` trả database connected; `/api/model` trả ready=true.
3. Trang React mở được và báo AI engine sẵn sàng.
4. Swagger hiển thị API; tests và frontend build chạy thành công.

Các phần tiếp theo đã được triển khai trong source: upload/lưu ca, inference, MRI viewer, xuất kết quả và Docker. Học hoặc tuỳ chỉnh từng phần theo kiến trúc trong tài liệu số 02.
