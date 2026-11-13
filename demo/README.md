# Ca mẫu dùng cho trình bày local

- Nguồn đầu vào: BraTS2023 GLI, ca đã ẩn danh `BraTS-GLI-00312-000`, từ dữ liệu đã có trong workspace của người dùng.
- Bốn modality: T1n, T1c, T2w, T2-FLAIR; kích thước 240 × 240 × 155.
- `segmentation.nii.gz` là **dự đoán đã ghi nhận** bằng checkpoint epoch 45 của thí nghiệm V2; không phải ground truth.
- `result.json` giữ thể tích, thời gian lần chạy gốc và thông tin truy xuất mô hình. Thời gian đó không phải thời gian mở demo.
- `manifest.json` chứa SHA-256 từng file. API xác minh checksum, hình học, nhãn và thể tích trước khi import.

Nút **Mở demo** sao chép dữ liệu này vào storage của ứng dụng, tạo ca và báo cáo với ID mới. Bấm nhiều lần sẽ mở lại cùng ca, không nhân bản. Xóa ca demo trong giao diện không xóa bundle này; có thể mở lại sau đó.

Nút **Phân tích lại** chạy model thật trên dữ liệu mẫu và tạo một job mới. Kết quả demo đã ghi nhận được giữ trong **Lịch sử phân tích**. PDF/JSON phân biệt rõ `recorded_inference` và `live_inference`.

Đây là gói trình bày local từ dữ liệu đang có, không phải một giấy phép phân phối lại BraTS. Các điều khoản của nguồn dataset vẫn áp dụng khi chia sẻ dữ liệu ra bên ngoài.
