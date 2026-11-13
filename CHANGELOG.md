# Changelog

## Rà soát sau bàn giao — 2026-11-13

- Sửa `--prepare-only` để chuẩn bị/build độc lập với server đang chạy; khóa riêng cho frontend build.
- Kiểm tra kiến trúc và bảng nhãn metadata với protocol checkpoint, xóa metadata cũ nếu nạp lỗi.
- Thêm cấu hình pytest từ gốc và regression tests; backend hiện có 34 test đạt.
- Kiểm tra ca MRI khác bằng checkpoint thật, mask/PDF/JSON/ZIP và restart trong kho tạm riêng.
- Browser test nhận cả `.nii`/`.nii.gz`, đổi bốn chuỗi xung và 3D; đồng bộ tài liệu với luồng tự tải MRI.
- Xem chi tiết tại `docs/08-KIEM-TRA-TOAN-DU-AN.md`.

## 1.1.0 — 2026-11-13

- Tailwind CSS tích hợp qua Vite, trang mô tả công nghệ và hai chế độ database minh bạch.
- Biểu đồ thể tích trong giao diện và PDF, footer và phân trang báo cáo.
- Launcher PostgreSQL qua Docker Compose, tạo mật khẩu local và giữ volume khi dừng.

- Một launcher cho giao diện production và API; tự kiểm tra dependencies/build, mở trình duyệt, ghi log và quản lý shutdown.
- Demo một nút từ MRI BraTS local và dự đoán checkpoint thật đã ghi nhận; kiểm tra checksum, hình học, nhãn và thể tích.
- Hướng dẫn demo ba bước trong workspace, trang kịch bản trình bày và trang kiểm tra hệ thống.
- Lịch sử job và lựa chọn xem lại các lần phân tích trước.
- Xuất ZIP gồm mask, PDF, JSON và README; lưu nguồn kết quả recorded/live.
- Khóa storage để ngăn nhiều process API cùng sở hữu hàng đợi.
- Browser tests với API và storage tạm; kiểm tra WebGL, tải file, điều hướng và mobile.

## 1.0.0

React/TypeScript, FastAPI, SQLite/PostgreSQL, MONAI U-Net, NiiVue viewer, upload bốn modality, inference queue và xuất NIfTI/PDF/JSON.
