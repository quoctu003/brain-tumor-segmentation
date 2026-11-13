import { useEffect, useRef, useState } from "react";
import { ArrowRight, Check, Play, ShieldCheck } from "lucide-react";
import { request, type DemoInfo, type Study } from "./api";

export default function DemoCard({
  onOpen,
  onGuide,
  autoOpen = false,
}: {
  onOpen: (study: Study) => void;
  onGuide: () => void;
  autoOpen?: boolean;
}) {
  const [info, setInfo] = useState<DemoInfo | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const autoAttempted = useRef(false);
  useEffect(() => {
    if (autoOpen && info?.available && !autoAttempted.current) {
      autoAttempted.current = true;
      void open();
    }
  }, [autoOpen, info?.available]);
  useEffect(() => {
    const controller = new AbortController();
    request<DemoInfo>("/demo", { signal: controller.signal })
      .then(setInfo)
      .catch((e) => {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : "Không đọc được ca demo.");
      });
    return () => controller.abort();
  }, []);
  async function open() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const study = await request<Study>("/demo", { method: "POST" });
      if (autoOpen) {
        const url = new URL(window.location.href);
        url.searchParams.delete("demo");
        window.history.replaceState(window.history.state, "", url);
      }
      onOpen(study);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Không mở được demo. Hãy thử lại.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="demo-hero" aria-labelledby="demo-heading">
      <div className="demo-copy">
        <span className="demo-kicker">
          <span className="live-dot" /> INTERACTIVE DEMO{" "}
          <span className="demo-tag">CA MRI THẬT</span>
        </span>
        <h2 id="demo-heading">
          Từ ảnh MRI đến kết quả.
          <br />
          <span>Khám phá bằng một lần nhấn.</span>
        </h2>
        <p>
          Mở ca BraTS mẫu với đủ bốn chuỗi xung, lớp phủ u 3D, thể tích và báo
          cáo. Không cần tự chọn file.
        </p>
        <div className="demo-benefits">
          <span>
            <Check size={14} /> 4 chuỗi xung
          </span>
          <span>
            <Check size={14} /> Mask từ model thật
          </span>
          <span>
            <Check size={14} /> PDF & JSON
          </span>
        </div>
        <div className="demo-actions">
          <button
            className="primary-button"
            onClick={() => void open()}
            disabled={busy || !info?.available}
          >
            {busy ? <span className="spinner" /> : <Play size={16} />}{" "}
            {busy ? "Đang chuẩn bị ca mẫu…" : "Mở demo"}
            <ArrowRight size={16} />
          </button>
          <button className="text-button" onClick={onGuide}>
            Xem kịch bản trình bày <ArrowRight size={14} />
          </button>
        </div>
        {error && (
          <p role="alert" className="demo-error">
            {error}{" "}
            <button className="text-button" onClick={() => void open()}>
              Thử mở lại
            </button>
          </p>
        )}
        {info && !info.available && (
          <p className="demo-error">
            Chưa có gói demo. Xem mục Hệ thống để kiểm tra dữ liệu.
          </p>
        )}
        <p className="demo-disclosure">
          <ShieldCheck size={13} /> Kết quả đã tính sẵn từ checkpoint thật. Bấm
          “Phân tích lại” trong ca để chạy AI mới.
        </p>
      </div>
      <div className="demo-preview">
        <div className="preview-label">
          <span>BRATS2023 GLI</span>
          <span className="preview-dot" /> RECORDED PREDICTION
        </div>
        <img
          src="/demo-preview.png"
          alt="Ba lát cắt MRI của ca BraTS mẫu với lớp phủ phân đoạn đã ghi nhận"
        />
        <div className="preview-caption">
          <span>
            <i className="region-dot wt" /> Whole tumor
          </span>
          <span>
            3D U-Net <i /> Selected epoch 45
          </span>
        </div>
      </div>
    </section>
  );
}
