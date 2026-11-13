# Rà soát và cải thiện — 13/11/2026

Đợt này kiểm tra mã backend, frontend, cấu hình triển khai và đối chiếu luồng suy luận với notebook `SIC_Capstone_v2_RESUMABLE.ipynb`. Không sửa notebook, checkpoint hoặc số liệu đánh giá mô hình.

## Những vấn đề đã sửa

| Khu vực | Vấn đề và thay đổi |
|---|---|
| Chuyển ca khi AI đang chạy | Phản hồi cũ có thể cập nhật job vào ca đang mở khác. Chỉ cập nhật khi case ID và job ID phù hợp; phản hồi bắt đầu inference cũng kiểm tra ca hiện tại. |
| Thư viện nhiều trang | Tự cập nhật trước đây tải lại 50 ca đầu và làm mất các trang đã tải thêm. Nay cập nhật các job đang hoạt động, giữ thư viện hiện tại, ngăn yêu cầu tải thêm trùng nhau và loại ca trùng ID. |
| API client | Hỗ trợ DELETE trả 204, diễn giải lỗi validation và xử lý trang lỗi HTML từ proxy. |
| Upload | Kiểm tra phần mở rộng và file rỗng trước khi gửi; ghi file trên thread pool để tránh chặn event loop. Backend tiếp tục kiểm tra nội dung NIfTI thực tế. |
| Kiểm tra MRI | Từ chối dữ liệu complex và tín hiệu trở thành hằng số sau clipping; đánh dấu đơn vị mm giả định nếu bất kỳ modality nào thiếu đơn vị. |
| File MRI bị mất | Trả 404 thay vì lỗi 500 khi tải modality không còn trên đĩa; vẫn cho tải các modality còn nguyên. |
| Truy vấn thư viện | Lấy ca và job mới nhất trong một truy vấn thay vì thêm một truy vấn cho mỗi ca; thêm ID để thứ tự phân trang ổn định khi thời gian trùng nhau. |
| Thời gian API | Ngày tạo/kết thúc có UTC rõ ràng kể cả khi SQLite trả datetime không có timezone. |
| Hàng đợi | Nếu worker từ chối submit, job được đánh dấu failed thay vì mắc kẹt queued. Shutdown worker trong finally và chạy ngoài event loop. |
| SQLite trong bộ nhớ | Dùng chung kết nối giữa các thread API, tránh lỗi không tìm thấy bảng. |
| PDF tiếng Việt | Nhúng font Unicode khi có Arial/DejaVu hoặc `REPORT_FONT_PATH`. Docker cài DejaVu để tên ca tiếng Việt hiển thị được. |
| MRI viewer | Áp dụng opacity và trạng thái ẩn overlay ngay lúc nạp, dùng giá trị mới nhất khi nạp xong; vô hiệu hóa nút chế độ trong khi tải. Lỗi fullscreen không khóa viewer. |
| Hộp thoại | Giữ Tab trong hộp thoại, hỗ trợ Escape và trả focus về nút mở; khóa cuộn nền. Không đóng hộp thoại upload bằng Escape khi đang gửi. |
| Tài liệu API | Link `/docs` cùng origin và proxy `/docs`, `/openapi.json` cho cả Vite và nginx, thay vì cố định cổng 8000 trên máy trình duyệt. |
| Bảo trì | Định dạng mã frontend bằng Prettier, bổ sung lệnh format/check và kiểm thử hồi quy bằng Vitest. |

## Kết quả thực chạy của đợt này

| Kiểm tra | Kết quả |
|---|---|
| Backend | **24 passed**, không có test bị bỏ qua trên máy này |
| Frontend | **10 passed**: API client, chuyển ca, phân trang, upload, focus hộp thoại và trạng thái viewer |
| TypeScript + Vite | Production build thành công |
| Prettier | Đã định dạng và kiểm tra thành công |
| Audit dependencies runtime frontend | `npm audit --omit=dev --audit-level=high`: 0 vulnerabilities tại thời điểm chạy |
| Checkpoint thật | Strict load + forward + xuất NIfTI thành công trên CPU, input tổng hợp 32³, patch 96³ |
| Checksum weights | `dbba1a212c9c8e0443d3c7fd763e22f9eb3ec80ce7fb4451c231ff0bebe0892f` |

Các kiểm thử mới bao gồm hàng đợi đầy, bấm phân tích trùng, cấm xóa khi đang chạy, job lỗi rồi chạy lại, restart job bị gián đoạn, worker từ chối submit, file MRI thiếu và font PDF có glyph tiếng Việt.

Kiểm thử viewer dùng NiiVue giả để xác nhận quản lý trạng thái; **không thay thế kiểm thử WebGL2 trên trình duyệt thật**. Đợt này không chạy lại luồng giao diện trên ca BraTS thật, Docker/PostgreSQL hoặc GPU. Các ảnh chụp và số liệu ca thật trong tài liệu 03 là kết quả được ghi nhận trước đó.

Smoke test input tổng hợp không đo độ chính xác. Chưa chạy lại tập test có ground truth; chưa có cơ sở khẳng định Dice tăng hoặc thay đổi sau đợt sửa mã này.

## Chạy lại kiểm tra

Từ gốc dự án trên Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test.ps1
python scripts/smoke_model.py
cd frontend
npm ci
npm test
npm run build
npm run format:check
```

Nếu dùng `.venv`, thay `python` bằng `.\.venv\Scripts\python.exe` cho smoke test. Trên Linux/macOS, chạy `python -m pytest tests -q` từ `backend/`.

Để PDF hỗ trợ tiếng Việt ngoài Docker, cài Arial/DejaVu hoặc đặt `REPORT_FONT_PATH` trỏ tới file `.ttf` hỗ trợ tiếng Việt. Nếu không tìm được font, hệ thống dùng Helvetica; test font sẽ báo skip.

## Bản sao trước khi sửa

Workspace chưa có Git. Bản sao mã nguồn trước đợt cải thiện nằm tại `.codex-backups/before-improvements.zip`, gồm backend, frontend, scripts, docs, README, compose và gitignore. Không bao gồm notebook, checkpoint, dataset hoặc dependencies. Thư mục backup đã thêm vào `.gitignore`.

## Giới hạn còn lại

Ứng dụng vẫn dành cho nghiên cứu local một người dùng, với một process API và một worker inference. Đăng nhập/phân quyền, hàng đợi nhiều process, DICOM/PACS, tiền xử lý registration/skull stripping và đánh giá trên ground truth cần thiết kế và dữ liệu riêng; chưa được bổ sung trong đợt sửa này.
