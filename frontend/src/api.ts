export type Job = {
  id: string;
  case_id: string;
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  stage: string;
  error: string | null;
  created_at?: string;
  finished_at?: string | null;
  result: {
    volumes_cm3: Record<string, number>;
    seconds: number;
    selected_epoch: number;
    provenance?: {
      kind: "recorded_inference" | "live_inference";
      recorded_at?: string;
      note?: string;
    };
  } | null;
};
export type Study = {
  id: string;
  name: string;
  created_at: string;
  geometry: {
    shape: number[];
    spacing_mm: number[];
    orientation: string[];
    units_assumed_mm: boolean;
    demo?: { source: string; source_case: string };
  };
  latest_job: Job | null;
};
export type DemoInfo = {
  available: boolean;
  title?: string;
  source?: string;
  kind: string;
  recorded_at?: string;
  note: string;
};
export type SystemInfo = {
  version: string;
  database: string;
  database_engine?: string;
  cases: number;
  jobs: Record<"queued" | "running" | "completed" | "failed", number>;
  queue_capacity: number;
  storage_free_gb: number;
  model: ModelInfo;
  demo: DemoInfo;
  frontend_ready: boolean;
  runtime: Record<string, string>;
  limits: { upload_mb: number; workers: number; mode: string };
};
export type ModelInfo = {
  ready: boolean;
  device: string;
  error: string | null;
  name: string;
  training_epochs: number | null;
  selected_epoch: number | null;
  weights_sha256: string | null;
  test: {
    dice_mean: number;
    dice_wt: number;
    dice_tc: number;
    dice_et: number;
    case_count: number;
  } | null;
};
export async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`/api${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    const message = Array.isArray(detail)
      ? detail
          .map(
            (item: { loc?: Array<string | number>; msg?: string }) =>
              `${item.loc?.slice(1).join(".") || "Dữ liệu"}: ${item.msg || "không hợp lệ"}`,
          )
          .join("; ")
      : typeof detail === "string"
        ? detail
        : `HTTP ${response.status}`;
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
export const volumeUrl = (id: string, modality: string) =>
  `/api/cases/${id}/volumes/${modality}`;
export const artifactUrl = (id: string, artifact: string) =>
  `/api/jobs/${id}/artifacts/${artifact}`;
