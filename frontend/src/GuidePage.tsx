import {
  ArrowDownToLine,
  ArrowRight,
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  FileUp,
  Layers3,
  Play,
  ShieldCheck,
} from "lucide-react";
import TechStack from "./TechStack";

export default function GuidePage({
  onDemo,
  onUpload,
}: {
  onDemo: () => void;
  onUpload: () => void;
}) {
  return (
    <div className="guide-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">QUICK START / PRESENTATION GUIDE</div>
          <h1>
            Một quy trình. <span>Từ đầu đến kết quả.</span>
          </h1>
          <p>
            Kịch bản trình bày rõ ràng cho người xem lần đầu và hướng dẫn sử
            dụng dữ liệu của bạn.
          </p>
        </div>
        <BookOpen size={32} />
      </div>
      <section className="guide-intro panel">
        <div>
          <span className="small-heading">BẮT ĐẦU VỚI CA MẪU</span>
          <h2>Demo trực quan trong khoảng 2 phút</h2>
          <p>
            Mở dữ liệu có sẵn, khám phá bốn chuỗi xung và giải thích kết quả.
            Thời gian này là kịch bản trình bày; không phải tốc độ suy luận.
          </p>
        </div>
        <button className="primary-button" onClick={onDemo}>
          <Play size={16} /> Đến nút mở demo <ArrowRight size={16} />
        </button>
      </section>
      <div className="guide-steps">
        {[
          {
            number: "01",
            icon: <FileUp />,
            title: "Giới thiệu dữ liệu",
            time: "30 giây",
            text: "Mở demo ở trang Ca nghiên cứu. Ca mẫu gồm T1n, T1c, T2w và T2-FLAIR đã căn chỉnh trên cùng lưới voxel.",
            detail: "Chỉ rõ nguồn BraTS và nhãn kết quả đã tính sẵn.",
          },
          {
            number: "02",
            icon: <Layers3 />,
            title: "Khám phá MRI & lớp phủ",
            time: "60 giây",
            text: "Đổi chuỗi xung, cuộn để chuyển lát cắt, thử chế độ 3D. Bật/tắt vùng u và thay đổi độ trong suốt để so sánh với ảnh gốc.",
            detail: "Đỏ: NCR/NET · Xanh: edema · Vàng: enhancing tumor.",
          },
          {
            number: "03",
            icon: <ArrowDownToLine />,
            title: "Đọc và xuất kết quả",
            time: "30 giây",
            text: "Giải thích thể tích WT, TC, ET; mở PDF hoặc tải toàn bộ kết quả ZIP gồm mask NIfTI, PDF và JSON truy xuất nguồn mô hình.",
            detail: "WT, TC, ET có vùng chồng nhau. Không cộng ba thể tích.",
          },
        ].map((step) => (
          <section className="guide-step panel" key={step.number}>
            <div className="guide-step-top">
              <span>{step.number}</span>
              {step.icon}
              <small>{step.time}</small>
            </div>
            <h2>{step.title}</h2>
            <p>{step.text}</p>
            <div className="guide-step-detail">{step.detail}</div>
          </section>
        ))}
      </div>
      <div className="guide-columns">
        <section className="panel documentation">
          <h2>
            <CheckCircle2 size={19} /> Dùng MRI của bạn
          </h2>
          <ul>
            <li>Bốn file NIfTI 3D: T1n, T1c, T2w, T2-FLAIR.</li>
            <li>
              Cùng kích thước và affine; đã registration và tiền xử lý theo
              BraTS.
            </li>
            <li>Đơn vị không gian mm, dữ liệu đã ẩn danh.</li>
            <li>
              Ứng dụng kiểm tra file trước khi lưu; không tự skull stripping,
              registration hoặc resample.
            </li>
          </ul>
          <button className="secondary-button" onClick={onUpload}>
            <FileUp size={16} /> Tải ca nghiên cứu của bạn
          </button>
        </section>
        <section className="panel documentation">
          <h2>
            <BrainCircuit size={19} /> Trình bày đúng về mô hình
          </h2>
          <p>
            Model 3D U-Net nhận bốn chuỗi xung. Checkpoint được chọn ở epoch 45
            trong lần huấn luyện 50 epoch.
          </p>
          <p>
            Dice trong model card thuộc tập test đã ghi nhận của lần train.
            Không có ground truth cho ca mới thì không tính được Dice của ca đó.
          </p>
          <p>
            Nút “Phân tích lại” chạy checkpoint thật và có thể cần chờ, tùy
            CPU/GPU và kích thước MRI.
          </p>
        </section>
      </div>
      <TechStack />
      <div className="notice-banner">
        <ShieldCheck size={20} />
        <div>
          <strong>Phạm vi nghiên cứu, được thể hiện rõ.</strong>
          <p>
            Demo không phải chẩn đoán và không mô phỏng một kết quả AI mới. Bản
            local dùng một process API, một worker inference; chưa có đăng nhập
            hoặc phân quyền.
          </p>
        </div>
      </div>
    </div>
  );
}
