# BrainTumor AI

Ứng dụng phân đoạn u não MRI bằng **3D U-Net**, với giao diện React, FastAPI, PyTorch/MONAI và trình xem MRI 3D NiiVue.

## Cài và chạy

Cần **Python 3.12–3.13**, **Node.js 22.12+ hoặc 24** và Internet cho lần cài đầu. CPU chạy được, không bắt buộc có GPU hay Docker.

```bash
git clone https://github.com/quoctu003/brain-tumor-segmentation.git
cd brain-tumor-segmentation
```

Hoặc tải **Code → Download ZIP** rồi giải nén vào ổ local.

- **Windows:** mở `START_BRAINTUMOR.cmd`.
- **macOS/Linux:** chạy `python3 scripts/launch.py`.

Launcher tự tạo `.venv`, cài thư viện, build giao diện và mở **http://127.0.0.1:8080**. Giữ terminal mở; nhấn **Ctrl+C** để dừng.

## Dataset và checkpoint

**[Tải dataset/checkpoint đã train trên Google Drive](https://drive.google.com/drive/folders/1DiVBV9V008vfxkIfmepf5g5WlCrqBVpV?usp=drive_link)**

Tải và giải nén inference bundle gồm `model_metadata.json` cùng `unet_v1_demo.pth` hoặc `unet_v2_best.pth`; `evaluation.json` là tùy chọn. Thư mục truyền vào phải chứa trực tiếp các file này:

```bash
python scripts/prepare_model.py --bundle "DUONG_DAN_DEN_BUNDLE"
```

Trên macOS/Linux dùng `python3` nếu máy không có lệnh `python`. Sau khi import, dừng và mở lại ứng dụng. Nếu chưa có checkpoint, giao diện vẫn chạy nhưng chức năng AI chưa sẵn sàng. Checkpoint raw/resume cần được export từ notebook trước khi import; quyền tải Drive phụ thuộc chủ thư mục.

## Sử dụng

Bấm **Thêm ca MRI**, chọn đủ `t1n`, `t1c`, `t2w`, `t2f` của cùng ca (`.nii`/`.nii.gz`), rồi bấm **Phân đoạn với AI**. Có thể xem ba mặt phẳng/3D và tải mask, PDF, JSON hoặc ZIP kết quả.

Đầu vào phải cùng shape/affine và đã tiền xử lý theo BraTS. Ứng dụng không tự registration, skull stripping hoặc resample.

Notebook train: [`notebooks/training.ipynb`](notebooks/training.ipynb). Model inference dùng best epoch 45 của lần train 50 epoch; test Dice mean ghi nhận trong metadata là **0.893744**, chưa phải kết quả đánh giá lại trong ứng dụng.

## Kiểm thử

Dùng Python trong `.venv`; cài thêm `backend/requirements-dev.txt`, rồi chạy:

```bash
python -m pytest backend/tests -q
cd frontend
npm test
npm run build
```

Chỉ phục vụ nghiên cứu local, chưa có đăng nhập/phân quyền và không thay thế chẩn đoán y khoa. Dataset, checkpoint và dữ liệu ca được giữ ngoài Git.
