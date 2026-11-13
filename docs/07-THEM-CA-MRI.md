# Tự thêm ca MRI

Mở `START_BRAINTUMOR.cmd`, sau đó bấm **Thêm ca MRI**.

Ứng dụng nhận các ca MRI khác nhau, không giới hạn ở bốn file trong thư mục `demo`. **Bốn file là bốn chuỗi xung của một ca**, không phải bốn ca bệnh.

## Chọn một ca khác

Ba ca MRI thật đã được sao chép nguyên vẹn từ bộ BraTS trên Google Drive của bạn vào máy:

- `F:\BrainTumorAI\data\mri_cases\BraTS-GLI-00016-000`
- `F:\BrainTumorAI\data\mri_cases\BraTS-GLI-00032-000`
- `F:\BrainTumorAI\data\mri_cases\BraTS-GLI-00048-000`

Các ca này thuộc danh sách `test` trong `models/model_metadata.json`, khác ca có sẵn `BraTS-GLI-00312-000`. Mỗi thư mục chứa bốn ảnh đầu vào, không chứa mask kết quả. File `data/mri_cases/manifest.json` lưu nguồn và SHA-256 của từng ảnh.

Ví dụ, nhập tên **BraTS-GLI-00016-000**, mở thư mục tương ứng rồi chọn:

| Ô tải lên | File |
|---|---|
| T1 Native | `BraTS-GLI-00016-000-t1n.nii.gz` |
| T1 Contrast | `BraTS-GLI-00016-000-t1c.nii.gz` |
| T2 Weighted | `BraTS-GLI-00016-000-t2w.nii.gz` |
| T2 FLAIR | `BraTS-GLI-00016-000-t2f.nii.gz` |

Không chọn `segmentation.nii.gz`: đó là mask kết quả, không phải ảnh đầu vào. Các file JSON cũng không dùng cho bốn ô MRI.

Chọn đủ bốn file → bấm **Tạo ca nghiên cứu** → bấm **Phân đoạn với AI**. Lần này mô hình thực sự chạy trên các ảnh vừa tải lên. Chờ hoàn tất rồi xem lớp phủ, thể tích và tải báo cáo.

Lặp lại với thư mục `00032` hoặc `00048` để trình bày trên các ca khác nhau. Bạn tự tải từng ca lên; ứng dụng không tự thêm các ca này vào thư viện.

## Dùng dữ liệu của bạn

Lấy bốn chuỗi xung của cùng một ca, cùng kích thước và affine, đơn vị mm, đã tiền xử lý theo BraTS. Tên file có thể khác: chọn theo loại ảnh T1 trước tiêm, T1 sau tiêm, T2 và FLAIR. Không trộn file từ các bệnh nhân/ca khác nhau. Ứng dụng chưa có bước chuyển DICOM, đăng ký ảnh, loại bỏ hộp sọ hoặc resample cho MRI thô của bệnh viện.

Nếu chỉ có một ảnh JPG/PNG hoặc thiếu chuỗi xung, mô hình bốn kênh hiện tại chưa phân tích được bộ đó. Không sao chép một ảnh vào nhiều ô để thay cho các chuỗi xung còn thiếu.

Giao diện hiện không tự mở hoặc import ca mẫu. Các ảnh đang có và kết quả đã lưu không bị xóa.
