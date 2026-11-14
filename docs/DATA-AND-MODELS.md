# Dataset và checkpoint

Nguồn tải do tác giả cung cấp: **[Google Drive](https://drive.google.com/drive/folders/1DiVBV9V008vfxkIfmepf5g5WlCrqBVpV?usp=drive_link)**. Dataset/checkpoint không nằm trong GitHub. Quyền xem/tải phụ thuộc cấu hình Drive của chủ thư mục; lần rà soát này chưa xác nhận được nội dung thư mục qua trình duyệt tự động.

## Chuẩn bị inference bundle

Tìm và tải thư mục export `demo_bundle` của thí nghiệm `unet_v2_resumable_001`, nếu có trong nguồn chia sẻ. Giải nén ZIP rồi xác định thư mục chứa trực tiếp:

```text
demo_bundle/
  model_metadata.json
  unet_v1_demo.pth          # hoặc unet_v2_best.pth
  evaluation.json           # tùy chọn, kết quả đánh giá gốc
```

Từ gốc dự án:

```bash
python scripts/prepare_model.py --bundle "DUONG_DAN/demo_bundle"
```

Script hỗ trợ cả tên export gốc và tên model trong ứng dụng, chỉ chọn file có SHA-256 khớp metadata. Không ghi đè checkpoint nguồn. Model import nằm trong `models/`, không được Git theo dõi. Dừng server trước khi import và mở lại sau khi hoàn tất.

SHA-256 của bản inference đã kiểm tra:

```text
dbba1a212c9c8e0443d3c7fd763e22f9eb3ec80ce7fb4451c231ff0bebe0892f
```

Đây là best epoch 45 thuộc lần train 50 epoch. Tên `unet_v1_demo.pth` là tên export cũ; protocol bên trong xác định V2. Checksum kiểm tra tính toàn vẹn, không thay thế đánh giá chất lượng mô hình.

Checkpoint raw/resume chứa optimizer và trạng thái train không phải bundle inference. Không đổi tên raw checkpoint để ép ứng dụng nạp. Nếu Drive chỉ có raw checkpoint, cần chạy phần export của notebook tương ứng để tạo weights và metadata khớp nhau; không tự dựng metadata/metric giả.

## Chuẩn bị MRI

Chọn bốn file của cùng ca: `*-t1n.nii.gz`, `*-t1c.nii.gz`, `*-t2w.nii.gz`, `*-t2f.nii.gz`; `.nii` cũng được chấp nhận. File segmentation ground truth không thay thế cho một chuỗi xung đầu vào.

Không cần chuyển toàn bộ dataset vào dự án: giao diện cho phép chọn trực tiếp file ở thư mục bất kỳ. Chỉ cần một ca hợp lệ để thử luồng upload. MRI phải đã được tiền xử lý/căn chỉnh theo protocol BraTS. Tuân thủ điều khoản dữ liệu và quyền chia sẻ của nguồn cung cấp; liên kết Drive không tự cấp quyền tái phân phối.

## Khắc phục lỗi

| Hiện tượng | Xử lý |
|---|---|
| Drive yêu cầu quyền truy cập | Đăng nhập tài khoản được cấp quyền hoặc yêu cầu chủ thư mục chia sẻ |
| Không thấy `model_metadata.json` | Kiểm tra thư mục con sau giải nén; tải đúng inference bundle |
| `Source checksum mismatch` | Tải lại đủ weights và metadata từ cùng một lần export |
| `Model unavailable` sau import | Dừng và mở lại API; xem trang **Hệ thống** để đọc lỗi cụ thể |
| Shape/affine không khớp | Chọn đủ bốn modality cùng ca, đã đăng ký không gian từ trước |
| Không có GPU | Launcher mặc định cài CPU; suy luận vẫn chạy nhưng tốc độ phụ thuộc máy |
