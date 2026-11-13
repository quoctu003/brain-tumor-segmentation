import { useEffect, useState } from "react";
import { History } from "lucide-react";
import { request, type Job } from "./api";

export default function JobHistory({
  caseId,
  latestJob,
  viewedJobId,
  onChoose,
}: {
  caseId: string;
  latestJob?: Job | null;
  viewedJobId?: string;
  onChoose: (job: Job) => void;
}) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    request<Job[]>(`/cases/${caseId}/jobs`, { signal: controller.signal })
      .then((next) => {
        if (!controller.signal.aborted) {
          setJobs(next);
          setError("");
        }
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError("Chưa tải được lịch sử. Kết quả hiện tại vẫn dùng được.");
      });
    return () => controller.abort();
  }, [caseId, latestJob?.id, latestJob?.status]);
  if (!latestJob) return null;
  const labels: Record<string, string> = {
    completed: "Hoàn tất",
    failed: "Thất bại",
    running: "Đang chạy",
    queued: "Đang chờ",
  };
  return (
    <div className="history-bar">
      <label htmlFor="job-history">
        <History size={15} /> Lịch sử phân tích
      </label>
      <select
        id="job-history"
        value={viewedJobId ?? latestJob.id}
        onChange={(event) => {
          const next = jobs.find((job) => job.id === event.target.value);
          if (next) onChoose(next);
        }}
      >
        {(jobs.length ? jobs : [latestJob]).map((job) => (
          <option key={job.id} value={job.id}>
            {job.result?.provenance?.kind === "recorded_inference"
              ? "Kết quả đã lưu"
              : labels[job.status]}{" "}
            ·{" "}
            {job.created_at
              ? new Date(
                  job.created_at.endsWith("Z")
                    ? job.created_at
                    : job.created_at + "Z",
                ).toLocaleString("vi-VN")
              : job.id.slice(0, 8)}
            {job.id === latestJob.id ? " · Mới nhất" : ""}
          </option>
        ))}
      </select>
      {error && <span role="status">{error}</span>}
      {viewedJobId && viewedJobId !== latestJob.id && (
        <span className="history-note">Đang xem một lần chạy trước</span>
      )}
    </div>
  );
}
