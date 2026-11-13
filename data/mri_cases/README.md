# Các ca MRI để tự tải lên

Mỗi thư mục là một ca BraTS khác nhau, gồm bốn ảnh NIfTI gốc: `t1n`, `t1c`, `t2w`, `t2f`.

- `BraTS-GLI-00016-000`
- `BraTS-GLI-00032-000`
- `BraTS-GLI-00048-000`

Mở `START_BRAINTUMOR.cmd` ở gốc dự án → **Thêm ca MRI** → chọn bốn ảnh trong **cùng một thư mục** → **Tạo ca nghiên cứu** → **Phân đoạn với AI**. Xem [hướng dẫn chọn từng file](../../docs/07-THEM-CA-MRI.md).

Nguồn: bộ BraTS đã có trên Google Drive của bạn; bản gốc không bị sửa. Cả ba ca thuộc tập `test` theo metadata của model đi kèm. `manifest.json` ghi đường dẫn nguồn và SHA-256 để kiểm tra tính nguyên vẹn. Không có ảnh tổng hợp hoặc kết quả AI dựng sẵn trong các thư mục này. Các ảnh được giữ cục bộ, không tự tải lên thư viện hoặc đưa vào gói phát hành.
