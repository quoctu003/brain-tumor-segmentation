# Chạy kiểm thử

Chạy từ gốc repository, trong `.venv` đã cài dependencies:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest backend/tests -q
```

Windows: `powershell -ExecutionPolicy Bypass -File scripts/test.ps1` dùng thư mục temp mới để tránh pytest temp cũ bị khóa. Nếu môi trường Python chung có nhiều plugin không liên quan, dùng `.venv` của dự án; không cần cài notebook/TensorFlow/MLflow để chạy ứng dụng.

```bash
cd frontend
npm ci
npm test
npm run format:check
npm run build
npm audit
```

Backend/API unit tests dùng ảnh tổng hợp và model giả được ghi rõ, không yêu cầu dữ liệu Drive. Không dùng kết quả này để báo cáo độ chính xác AI.

## Browser tests

Chạy `npm run build` trước. Tại `frontend/`, chạy:

```bash
npx playwright install chromium
npm run test:e2e
```

Test khởi động backend thật với database/storage tạm. Trên Windows có Edge thì dùng Edge; nơi khác dùng Chromium đã cài. Dữ liệu MRI tổng hợp được tạo trong thư mục tạm; không cần tải hoặc phân phối dataset thật. Kiểm tra upload `.nii`/`.nii.gz`, WebGL viewer, đổi modality, 3D và dialog mobile. Chế độ không có model chỉ kiểm giao diện/API; không giả vờ model đã sẵn sàng.

## Checkpoint thật

Sau khi import bundle:

```bash
python scripts/smoke_model.py
python scripts/verify_case.py --case-dir data/mri_cases/TEN_CA
```

Smoke test dùng input tổng hợp để kiểm forward và hình học đầu ra. `verify_case.py` cần MRI thật, kiểm mask/thể tích/artifact/restart trong kho tạm. Hai bước này không thay thế đánh giá Dice trên toàn bộ test set. Docker/PostgreSQL, CUDA và máy macOS/Linux cần kiểm chứng riêng.
