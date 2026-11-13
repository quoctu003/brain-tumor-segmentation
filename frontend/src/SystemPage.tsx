import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  CheckCircle2,
  CircleAlert,
  Cpu,
  Database,
  ExternalLink,
  HardDrive,
  RefreshCw,
  Server,
  ShieldCheck,
} from "lucide-react";
import { request, type SystemInfo } from "./api";

export default function SystemPage() {
  const [data, setData] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updated, setUpdated] = useState("");
  const refresh = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const next = await request<SystemInfo>("/system", { signal });
      if (signal?.aborted) return;
      setData(next);
      setUpdated(new Date().toLocaleTimeString("vi-VN"));
      setError("");
    } catch (e) {
      if (!signal?.aborted)
        setError(
          e instanceof Error ? e.message : "Không kiểm tra được hệ thống.",
        );
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void refresh(controller.signal);
    return () => controller.abort();
  }, [refresh]);
  return (
    <div className="system-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">OPERATIONS / LOCAL WORKSPACE</div>
          <h1>Trạng thái hệ thống</h1>
          <p>
            Theo dõi kết nối, mô hình, dữ liệu mẫu và năng lực xử lý hiện tại.
          </p>
        </div>
        <button
          className="secondary-button"
          disabled={loading}
          onClick={() => void refresh()}
        >
          <RefreshCw size={15} />
          {loading ? "Đang kiểm tra…" : "Kiểm tra lại"}
        </button>
      </div>
      {error && (
        <div role="alert" className="error-box">
          {error}
        </div>
      )}
      {!data && loading && (
        <div className="panel system-loading">
          <span className="spinner" /> Đang kiểm tra các dịch vụ…
        </div>
      )}
      {data && (
        <>
          <div className="system-grid">
            {[
              {
                icon: <Database />,
                name: "Database",
                ok: data.database === "connected",
                value: "Đã kết nối",
                detail: `${data.database_engine === "postgresql" ? "PostgreSQL" : "SQLite"} · ${data.cases} ca nghiên cứu được lưu`,
              },
              {
                icon: <Cpu />,
                name: "AI engine",
                ok: data.model.ready,
                value: data.model.ready ? "Sẵn sàng" : "Chưa sẵn sàng",
                detail: `Thiết bị: ${data.model.device.toUpperCase()}`,
              },
              {
                icon: <Activity />,
                name: "Hàng đợi AI",
                ok: data.jobs.queued + data.jobs.running < data.queue_capacity,
                value: `${data.jobs.queued + data.jobs.running} / ${data.queue_capacity}`,
                detail: "Số tác vụ đang chờ và đang xử lý",
              },
              {
                icon: <HardDrive />,
                name: "Dung lượng trống",
                ok: data.storage_free_gb > 1,
                value: `${data.storage_free_gb.toFixed(1)} GB`,
                detail: "Trên ổ lưu trữ dữ liệu ứng dụng",
              },
            ].map((card) => (
              <section className="panel system-card" key={card.name}>
                <div className="system-card-top">
                  {card.icon}
                  <span
                    className={`service-pill ${card.ok ? "ok" : "warning"}`}
                  >
                    {card.ok ? (
                      <CheckCircle2 size={12} />
                    ) : (
                      <CircleAlert size={12} />
                    )}{" "}
                    {card.ok ? "OK" : "Cần kiểm tra"}
                  </span>
                </div>
                <span className="small-heading">{card.name}</span>
                <h2>{card.value}</h2>
                <p>{card.detail}</p>
              </section>
            ))}
          </div>
          {data.model.error && (
            <div role="alert" className="error-box">
              {data.model.error}
            </div>
          )}
          <div className="guide-columns">
            <section className="panel documentation">
              <h2>
                <Server size={19} /> Hàng đợi xử lý
              </h2>
              <div className="queue-grid">
                {[
                  ["Đang chờ", data.jobs.queued],
                  ["Đang chạy", data.jobs.running],
                  ["Hoàn tất", data.jobs.completed],
                  ["Thất bại", data.jobs.failed],
                ].map(([label, value]) => (
                  <div key={label}>
                    <strong>{value}</strong>
                    <span>{label}</span>
                  </div>
                ))}
              </div>
              <p>
                Tối đa {data.queue_capacity} job đang chờ/chạy. Một worker xử lý
                tuần tự; số hoàn tất/thất bại bao gồm lịch sử các lần chạy.
              </p>
            </section>
            <section className="panel documentation">
              <h2>
                <Cpu size={19} /> Phiên bản & cấu hình
              </h2>
              <dl className="runtime-list">
                <div>
                  <dt>BrainTumor AI</dt>
                  <dd>{data.version}</dd>
                </div>
                {Object.entries(data.runtime).map(([key, value]) => (
                  <div key={key}>
                    <dt>{key}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
                <div>
                  <dt>Giới hạn mỗi file</dt>
                  <dd>{data.limits.upload_mb} MB</dd>
                </div>
                <div>
                  <dt>Giao diện production</dt>
                  <dd>{data.frontend_ready ? "Đã build" : "Chưa build"}</dd>
                </div>
              </dl>
            </section>
          </div>
          <div className="notice-banner">
            <ShieldCheck size={20} />
            <div>
              <strong>Vận hành local · Không gian nghiên cứu</strong>
              <p>
                Ảnh và kết quả được xử lý trên máy chạy backend. Dừng bằng
                Ctrl+C trong cửa sổ khởi động; dữ liệu đã lưu được giữ lại. Khi
                khởi động lại, job chưa xong được đánh dấu thất bại để chạy lại.
              </p>
            </div>
            <a
              className="secondary-button"
              href="/docs"
              target="_blank"
              rel="noreferrer"
            >
              API docs <ExternalLink size={14} />
            </a>
          </div>
          <p className="system-updated">
            Cập nhật lúc {updated} · Thông tin tại thời điểm kiểm tra
          </p>
        </>
      )}
    </div>
  );
}
