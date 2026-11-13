import {
  ArrowDownToLine,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  X,
} from "lucide-react";
import { artifactUrl } from "./api";

const steps = [
  {
    label: "Dữ liệu đầu vào",
    heading: "Bắt đầu với bốn chuỗi xung MRI",
    text: "Dùng các tab T1 Native, T1 Contrast, T2 Weighted và T2 FLAIR bên dưới để so sánh cùng một ca. Cuộn chuột trong viewer để đi qua các lát cắt.",
  },
  {
    label: "Khám phá phân đoạn",
    heading: "So sánh vùng u với ảnh gốc",
    text: "Bật/tắt “Hiển thị vùng u” và kéo thanh độ trong suốt. Thử chế độ 3D ở thanh công cụ viewer. WT gồm toàn bộ vùng u; TC và ET là các vùng con.",
  },
  {
    label: "Báo cáo & xuất file",
    heading: "Mang kết quả ra khỏi workspace",
    text: "Xem thể tích ở bảng bên phải, mở PDF hoặc tải gói ZIP gồm mask NIfTI, báo cáo và JSON. Nguồn mô hình và loại kết quả được ghi trong báo cáo.",
  },
];
export default function DemoWalkthrough({
  step,
  onStep,
  onClose,
  jobId,
}: {
  step: number;
  onStep: (step: number) => void;
  onClose: () => void;
  jobId?: string;
}) {
  return (
    <section className="demo-walkthrough" aria-label="Hướng dẫn demo">
      <div className="walkthrough-top">
        <span className="demo-kicker">DEMO CÓ HƯỚNG DẪN</span>
        <button
          className="icon-button"
          aria-label="Ẩn hướng dẫn demo"
          onClick={onClose}
        >
          <X size={16} />
        </button>
      </div>
      <div className="walkthrough-steps">
        {steps.map((item, index) => (
          <button
            key={item.label}
            onClick={() => onStep(index)}
            aria-current={step === index ? "step" : undefined}
            className={step === index ? "current" : step > index ? "done" : ""}
          >
            <span>{step > index ? <CheckCircle2 size={15} /> : index + 1}</span>
            {item.label}
          </button>
        ))}
      </div>
      <div className="walkthrough-content">
        <div>
          <h2>{steps[step].heading}</h2>
          <p>{steps[step].text}</p>
        </div>
        <div className="walkthrough-actions">
          {step > 0 && (
            <button className="text-button" onClick={() => onStep(step - 1)}>
              <ArrowLeft size={14} /> Trước
            </button>
          )}
          {step < 2 ? (
            <button
              className="secondary-button"
              onClick={() => onStep(step + 1)}
            >
              Tiếp theo <ArrowRight size={14} />
            </button>
          ) : jobId ? (
            <a
              className="primary-button"
              href={`/api/jobs/${jobId}/bundle`}
              download
            >
              <ArrowDownToLine size={15} /> Tải gói kết quả
            </a>
          ) : (
            <button className="secondary-button" onClick={onClose}>
              Hoàn tất
            </button>
          )}
          {step === 2 && jobId && (
            <a
              className="text-button"
              href={artifactUrl(jobId, "report")}
              target="_blank"
              rel="noreferrer"
            >
              Mở báo cáo PDF
            </a>
          )}
        </div>
      </div>
    </section>
  );
}
