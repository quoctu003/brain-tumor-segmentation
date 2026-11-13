import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  Database,
  FileText,
  FolderOpen,
  HelpCircle,
  Layers3,
  ListFilter,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
  Waves,
  X,
  Server,
} from "lucide-react";
import {
  artifactUrl,
  request,
  type Job,
  type ModelInfo,
  type Study,
} from "./api";
import UploadDialog from "./UploadDialog";
import Modal from "./Modal";
import SystemPage from "./SystemPage";
import JobHistory from "./JobHistory";
import ErrorBoundary from "./ErrorBoundary";
import VolumeChart from "./VolumeChart";
const MRIViewer = lazy(() => import("./MRIViewer"));
const statusLabels: Record<string, string> = {
  queued: "Đang chờ",
  running: "Đang phân tích",
  completed: "Đã hoàn tất",
  failed: "Cần thử lại",
};
const studyName = (study: Study) =>
  study.geometry.demo ? study.name.replace(/^Demo\s*[·-]\s*/i, "") : study.name;
const dateLabel = (date: string) =>
  new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(
    new Date(
      date.endsWith("Z") || /[+-]\d\d:\d\d$/.test(date) ? date : date + "Z",
    ),
  );

export default function App() {
  const [studies, setStudies] = useState<Study[]>([]);
  const [view, setView] = useState<"library" | "system">("library");
  const [historicalJob, setHistoricalJob] = useState<Job | null>(null);
  const [selected, setSelected] = useState<Study | null>(null);
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [modal, setModal] = useState(false);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [modality, setModality] = useState("t2f");
  const [overlay, setOverlay] = useState(true);
  const [opacity, setOpacity] = useState(0.5);
  const [info, setInfo] = useState(false);
  const [onlyCompleted, setOnlyCompleted] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const moreInFlight = useRef(false);
  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const [cases, m] = await Promise.all([
        request<Study[]>("/cases?limit=50", { signal }),
        request<ModelInfo>("/model", { signal }),
      ]);
      if (signal?.aborted) return;
      setStudies(cases);
      setHasMore(cases.length === 50);
      setModel(m);
      setError("");
    } catch (e) {
      if (!signal?.aborted)
        setError(e instanceof Error ? e.message : "Không kết nối được API.");
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);
  const job =
    historicalJob?.case_id === selected?.id
      ? historicalJob
      : selected?.latest_job;
  const active =
    selected?.latest_job?.status === "queued" ||
    selected?.latest_job?.status === "running";
  function openStudy(study: Study) {
    setSelected(study);
    setHistoricalJob(null);
    setView("library");
    setModality("t2f");
    setOverlay(true);
    setStudies((list) =>
      list.some((item) => item.id === study.id)
        ? list.map((item) => (item.id === study.id ? study : item))
        : [study, ...list],
    );
    window.scrollTo?.({ top: 0, behavior: "smooth" });
  }
  const activeJobIds = studies
    .filter((s) => ["queued", "running"].includes(s.latest_job?.status || ""))
    .map((s) => s.latest_job!.id)
    .join(",");
  useEffect(() => {
    if (!activeJobIds) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      await Promise.all(
        activeJobIds.split(",").map(async (id) => {
          try {
            const next = await request<Job>(`/jobs/${id}`);
            if (cancelled) return;
            setSelected((study) =>
              study?.id === next.case_id && study.latest_job?.id === next.id
                ? { ...study, latest_job: next }
                : study,
            );
            setStudies((list) =>
              list.map((s) =>
                s.id === next.case_id && s.latest_job?.id === next.id
                  ? { ...s, latest_job: next }
                  : s,
              ),
            );
          } catch (e) {
            if (!cancelled)
              setError(
                e instanceof Error
                  ? e.message
                  : "Không cập nhật được tiến trình.",
              );
          }
        }),
      );
      if (!cancelled) timer = setTimeout(() => void poll(), 2000);
    }
    timer = setTimeout(() => void poll(), 2000);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [activeJobIds]);
  async function runInference() {
    if (!selected) return;
    setHistoricalJob(null);
    setBusy(true);
    setError("");
    try {
      const next = await request<Job>(`/cases/${selected.id}/inference`, {
        method: "POST",
      });
      setSelected((current) =>
        current?.id === next.case_id
          ? { ...current, latest_job: next }
          : current,
      );
      setStudies((list) =>
        list.map((s) =>
          s.id === next.case_id ? { ...s, latest_job: next } : s,
        ),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không thể bắt đầu phân tích");
    } finally {
      setBusy(false);
    }
  }
  async function deleteStudy(study: Study) {
    if (
      !confirm(
        `Xóa ca “${studyName(study)}” và các kết quả trong ứng dụng? Dữ liệu gốc bên ngoài ứng dụng vẫn được giữ.`,
      )
    )
      return;
    try {
      await request<void>(`/cases/${study.id}`, { method: "DELETE" });
      setSelected((current) => (current?.id === study.id ? null : current));
      setStudies((list) => list.filter((s) => s.id !== study.id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không thể xóa ca");
    }
  }
  async function loadMore() {
    if (moreInFlight.current) return;
    moreInFlight.current = true;
    setLoadingMore(true);
    try {
      const next = await request<Study[]>(
        `/cases?limit=50&offset=${studies.length}`,
      );
      setStudies((list) => [
        ...list,
        ...next.filter((s) => !list.some((existing) => existing.id === s.id)),
      ]);
      setHasMore(next.length === 50);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không tải được thêm ca");
    } finally {
      moreInFlight.current = false;
      setLoadingMore(false);
    }
  }
  const completed = studies.filter(
    (s) => s.latest_job?.status === "completed",
  ).length;
  const filtered = studies.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) &&
      (!onlyCompleted || s.latest_job?.status === "completed"),
  );
  const ready = job?.status === "completed";
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <a
          className="brand"
          href="/"
          onClick={(e) => {
            e.preventDefault();
            setSelected(null);
            setView("library");
            setHistoricalJob(null);
          }}
        >
          <span className="brand-icon">
            <BrainCircuit size={25} />
          </span>
          <span>
            BrainTumor<span className="brand-ai"> AI</span>
            <small>IMAGING INTELLIGENCE</small>
          </span>
        </a>
        <div className="workspace-label">
          WORKSPACE <span>LOCAL</span>
        </div>
        <button
          className={`nav-item ${view === "library" && !selected ? "active" : ""}`}
          onClick={() => {
            setSelected(null);
            setView("library");
          }}
        >
          <FolderOpen size={18} /> Ca nghiên cứu{" "}
          <span className="nav-count">
            {studies.length}
            {hasMore ? "+" : ""}
          </span>
        </button>
        <button className="nav-item" onClick={() => setInfo(true)}>
          <BrainCircuit size={18} /> Mô hình AI <span className="tiny-dot" />
        </button>
        <button
          className={`nav-item ${view === "system" ? "active" : ""}`}
          onClick={() => setView("system")}
          aria-label="Hệ thống"
        >
          <Server size={18} /> Hệ thống
        </button>
        <div className="sidebar-divider" />
        <p className="sidebar-caption">QUY TRÌNH PHÂN TÍCH</p>
        <div className="workflow-step">
          <span>01</span>
          <div>
            Tải MRI<small>4 chuỗi xung đa phương thức</small>
          </div>
        </div>
        <div className="workflow-line" />
        <div className="workflow-step">
          <span>02</span>
          <div>
            Phân đoạn 3D<small>3D U-Net · Sliding window</small>
          </div>
        </div>
        <div className="workflow-line" />
        <div className="workflow-step">
          <span>03</span>
          <div>
            Khám phá kết quả<small>Thể tích · Mask · Báo cáo</small>
          </div>
        </div>
        <div className="sidebar-bottom">
          <div className="privacy-card">
            <ShieldCheck size={18} />
            <strong>Không gian dữ liệu local</strong>
            <p>Ảnh MRI và kết quả được lưu trên máy chạy backend.</p>
          </div>
          <button className="nav-item" onClick={() => setInfo(true)}>
            <HelpCircle size={17} /> Thông tin dự án <ChevronRight size={14} />
          </button>
          <div className="profile">
            <span>BT</span>
            <div>
              Research workspace<small>Phiên bản 1.1 · Nghiên cứu</small>
            </div>
            <i className="live-dot" />
          </div>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={13} />
            <button
              onClick={() => {
                setSelected(null);
                setView("library");
              }}
            >
              Ca nghiên cứu
            </button>
            {view !== "library" && (
              <>
                <ChevronRight size={13} />
                <span>Hệ thống</span>
              </>
            )}
            {selected && view === "library" && (
              <>
                <ChevronRight size={13} />
                <span>{studyName(selected)}</span>
              </>
            )}
          </div>
          <div className="topbar-right">
            <span className={`connection ${model?.ready ? "connected" : ""}`}>
              <i />
              {model?.ready
                ? "AI engine sẵn sàng"
                : loading
                  ? "Đang kết nối…"
                  : "AI engine chưa sẵn sàng"}
            </span>
            <span className="research-badge">RESEARCH USE</span>
          </div>
        </header>
        <div className="page-content">
          {error && (
            <div className="error-box global-error" role="alert">
              <span>{error}</span>
              <button
                className="icon-button"
                aria-label="Đóng thông báo"
                onClick={() => setError("")}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {view === "system" ? (
            <SystemPage />
          ) : !selected ? (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">
                    <i className="live-dot" /> MRI SEGMENTATION WORKSPACE
                  </div>
                  <h1>
                    Mỗi lát cắt. <span>Một góc nhìn rõ hơn.</span>
                  </h1>
                  <p>
                    Quản lý MRI, phân đoạn u não và khám phá kết quả trong một
                    không gian.
                  </p>
                </div>
                <button
                  className="primary-button"
                  onClick={() => setModal(true)}
                >
                  <Plus size={18} /> Thêm ca MRI
                </button>
              </div>
              <div className="stats-grid">
                <Stat
                  icon={<FolderOpen size={20} />}
                  title="CA NGHIÊN CỨU ĐÃ TẢI"
                  value={`${studies.length}${hasMore ? "+" : ""}`}
                  detail="4 chuỗi xung / mỗi ca"
                />
                <Stat
                  icon={<CheckCircle2 size={20} />}
                  title="ĐÃ PHÂN TÍCH"
                  value={String(completed)}
                  detail="Ca có kết quả hoàn tất"
                />
                <Stat
                  icon={<Activity size={20} />}
                  title="DICE TRÊN TẬP TEST"
                  value={
                    model?.test
                      ? (model.test.dice_mean * 100).toFixed(2) + "%"
                      : "—"
                  }
                  detail={
                    model?.test
                      ? `${model.test.case_count} ca · Kết quả thực nghiệm V2`
                      : "Chờ xác minh mô hình"
                  }
                />
                <Stat
                  icon={<Layers3 size={20} />}
                  title="HUẤN LUYỆN V2"
                  value={
                    model?.training_epochs ? `${model.training_epochs}` : "—"
                  }
                  detail={
                    model?.selected_epoch
                      ? `epochs · Chọn model epoch ${model.selected_epoch}`
                      : "Chờ nạp checkpoint"
                  }
                />
              </div>
              <section className="study-section">
                <div className="section-heading">
                  <div>
                    <h2>
                      Thư viện ca nghiên cứu{" "}
                      <span>
                        {studies.length}
                        {hasMore ? "+" : ""}
                      </span>
                    </h2>
                    <p>Ảnh đầu vào và kết quả phân đoạn của bạn.</p>
                  </div>
                  <div className="table-tools">
                    <label className="search-field">
                      <Search size={16} />
                      <input
                        aria-label="Tìm ca nghiên cứu"
                        placeholder="Tìm ca nghiên cứu…"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                      />
                    </label>
                    <button
                      className={`secondary-button ${onlyCompleted ? "filter-active" : ""}`}
                      onClick={() => setOnlyCompleted(!onlyCompleted)}
                    >
                      <ListFilter size={15} />
                      {onlyCompleted ? "Đã hoàn tất" : "Tất cả ca"}
                    </button>
                  </div>
                </div>
                <div className="study-table">
                  <div className="table-row table-head">
                    <span>CA NGHIÊN CỨU</span>
                    <span>CHUỖI XUNG</span>
                    <span>NGÀY TẠO</span>
                    <span>TRẠNG THÁI</span>
                    <span />
                  </div>
                  {loading ? (
                    <div className="empty-state">
                      <span className="spinner" />
                      <p>Đang tải thư viện…</p>
                    </div>
                  ) : filtered.length ? (
                    filtered.map((study) => (
                      <button
                        className="table-row study-row"
                        key={study.id}
                        onClick={() => {
                          setSelected(study);
                          setHistoricalJob(null);
                          setModality("t2f");
                          setOverlay(true);
                        }}
                      >
                        <span className="study-name">
                          <span className="study-icon">
                            <BrainCircuit size={20} />
                          </span>
                          <span>
                            <strong>{studyName(study)}</strong>
                            <small>
                              {study.geometry.shape.join(" × ")} voxel
                            </small>
                          </span>
                        </span>
                        <span className="modality-pills">
                          <i>T1</i>
                          <i>T1c</i>
                          <i>T2</i>
                          <i>FLAIR</i>
                        </span>
                        <span className="date-cell">
                          {dateLabel(study.created_at)}
                        </span>
                        <span
                          className={`status-badge ${study.latest_job?.status || "new"}`}
                        >
                          <i />
                          {study.latest_job
                            ? statusLabels[study.latest_job.status]
                            : "Chưa phân tích"}
                        </span>
                        <ArrowRight size={16} />
                      </button>
                    ))
                  ) : (
                    <div className="empty-state">
                      <span className="empty-icon">
                        <BrainCircuit size={40} strokeWidth={1.2} />
                      </span>
                      <h3>
                        {search || onlyCompleted
                          ? "Không có ca phù hợp"
                          : "Sẵn sàng cho ca MRI đầu tiên"}
                      </h3>
                      <p>
                        {search || onlyCompleted
                          ? "Thay đổi từ khóa hoặc bộ lọc để tìm ca."
                          : "Tải lên T1n, T1c, T2w và T2-FLAIR để bắt đầu phân tích."}
                      </p>
                      {!search && !onlyCompleted && (
                        <button
                          className="secondary-button"
                          onClick={() => setModal(true)}
                        >
                          <Plus size={16} /> Tải MRI lên
                        </button>
                      )}
                    </div>
                  )}
                </div>
                {hasMore && (
                  <button
                    className="secondary-button load-more"
                    disabled={loadingMore}
                    onClick={() => void loadMore()}
                  >
                    {loadingMore ? "Đang tải…" : "Tải thêm ca"}
                  </button>
                )}
              </section>
              <div className="bottom-grid">
                <div className="model-card">
                  <div className="model-art">
                    <BrainCircuit size={46} strokeWidth={1} />
                    <span className="orbit orbit-one" />
                    <span className="orbit orbit-two" />
                  </div>
                  <div className="model-card-text">
                    <div className="eyebrow">POWERED BY 3D U-NET</div>
                    <h3>Từ MRI đa chuỗi xung đến bản đồ vùng u.</h3>
                    <p>
                      Phân đoạn WT, TC và ET bằng mô hình đã huấn luyện trên
                      BraTS2023 GLI.
                    </p>
                    <button
                      className="text-button"
                      onClick={() => setInfo(true)}
                    >
                      Xem thông tin mô hình <ArrowRight size={15} />
                    </button>
                  </div>
                </div>
                <div className="guide-card">
                  <span className="guide-icon">
                    <Waves size={21} />
                  </span>
                  <h3>Chuẩn bị ảnh đầu vào</h3>
                  <p>
                    4 thể tích MRI 3D, cùng kích thước và affine. Dữ liệu đã
                    đăng ký ảnh, theo protocol BraTS.
                  </p>
                  <span className="format-chip">
                    NIfTI <span>.nii / .nii.gz</span>
                  </span>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="page-heading case-heading">
                <div>
                  <div className="eyebrow">
                    MRI STUDY / {selected.id.slice(0, 8)}
                  </div>
                  <h1>{studyName(selected)}</h1>
                  <p>
                    {selected.geometry.shape.join(" × ")} voxel{" "}
                    <span className="dot-separator">·</span>{" "}
                    {selected.geometry.spacing_mm
                      .map((n) => n.toFixed(2))
                      .join(" × ")}{" "}
                    mm <span className="dot-separator">·</span>{" "}
                    {selected.geometry.orientation.join("")}
                  </p>
                </div>
                <div className="case-actions">
                  <button
                    className="icon-button delete-button"
                    title="Xóa ca"
                    aria-label="Xóa ca"
                    disabled={active || busy}
                    onClick={() => void deleteStudy(selected)}
                  >
                    <Trash2 size={17} />
                  </button>
                  <button
                    className="primary-button"
                    disabled={!model?.ready || active || busy}
                    onClick={() => void runInference()}
                  >
                    {active || busy ? (
                      <span className="spinner" />
                    ) : (
                      <Sparkles size={17} />
                    )}{" "}
                    {active
                      ? "Đang phân tích…"
                      : ready
                        ? "Phân tích lại"
                        : "Phân đoạn với AI"}
                  </button>
                </div>
              </div>
              {job?.result?.provenance?.kind === "recorded_inference" && (
                <div className="info-strip">
                  Kết quả được lưu từ một lần chạy trước. Chọn “Phân tích lại”
                  để chạy mô hình trên ảnh hiện tại.
                </div>
              )}
              <JobHistory
                key={selected.id}
                caseId={selected.id}
                latestJob={selected.latest_job}
                viewedJobId={job?.id}
                onChoose={(next) =>
                  setHistoricalJob(
                    next.id === selected.latest_job?.id ? null : next,
                  )
                }
              />
              {selected.geometry.units_assumed_mm && (
                <div className="info-strip">
                  Header không khai báo đơn vị không gian. Theo protocol BraTS,
                  tọa độ được hiểu là mm; hãy xác nhận trước khi diễn giải thể
                  tích.
                </div>
              )}
              {active && (
                <div className="job-progress">
                  <div>
                    <span className="spinner" />
                    <strong>{selected.latest_job?.stage}</strong>
                    <span>{selected.latest_job?.progress}%</span>
                  </div>
                  <progress value={selected.latest_job?.progress} max={100} />
                  <small>
                    Có thể chuyển sang ca khác trong khi phân tích. CPU sẽ chậm
                    hơn GPU.
                  </small>
                </div>
              )}
              {job?.status === "failed" && (
                <div className="error-box">{job.error}</div>
              )}
              <div className="workspace-grid">
                <div className="imaging-column">
                  <div className="modality-tabs">
                    {[
                      ["t1n", "T1 Native"],
                      ["t1c", "T1 Contrast"],
                      ["t2w", "T2 Weighted"],
                      ["t2f", "T2 FLAIR"],
                    ].map(([key, label]) => (
                      <button
                        className={modality === key ? "active" : ""}
                        onClick={() => setModality(key)}
                        key={key}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  <ErrorBoundary
                    key={`${selected.id}:${modality}:${job?.id ?? ""}`}
                  >
                    <Suspense
                      fallback={
                        <div className="viewer-placeholder">
                          <span className="spinner" /> Đang khởi tạo MRI viewer…
                        </div>
                      }
                    >
                      <MRIViewer
                        caseId={selected.id}
                        modality={modality}
                        jobId={ready ? job?.id : undefined}
                        opacity={opacity}
                        showOverlay={overlay}
                      />
                    </Suspense>
                  </ErrorBoundary>
                  <div className="viewer-help">
                    <ShieldCheck size={15} /> NiiVue / WebGL2{" "}
                    <span>Ảnh được hiển thị theo affine NIfTI gốc.</span>
                  </div>
                </div>
                <aside className="result-panel">
                  <div className="result-title">
                    <Layers3 size={18} />
                    <h2>Kết quả phân đoạn</h2>
                  </div>
                  <div className="overlay-control">
                    <label>
                      <input
                        type="checkbox"
                        checked={overlay}
                        disabled={!ready}
                        onChange={(e) => setOverlay(e.target.checked)}
                      />
                      Hiển thị vùng u
                    </label>
                    <span>{Math.round(opacity * 100)}%</span>
                  </div>
                  <input
                    className="opacity-slider"
                    aria-label="Độ trong suốt vùng u"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={opacity}
                    disabled={!ready}
                    onChange={(e) => setOpacity(Number(e.target.value))}
                  />
                  <div className="legend">
                    <span>
                      <i style={{ background: "#ef5b6c" }} />
                      NCR/NET
                    </span>
                    <span>
                      <i style={{ background: "#4dc796" }} />
                      Edema
                    </span>
                    <span>
                      <i style={{ background: "#fabc53" }} />
                      ET
                    </span>
                  </div>
                  <div className="result-divider" />
                  <span className="small-heading">THỂ TÍCH ƯỚC TÍNH</span>
                  {[
                    ["wt", "Whole Tumor", "Toàn bộ vùng u"],
                    ["tc", "Tumor Core", "Lõi u"],
                    ["et", "Enhancing Tumor", "Vùng u bắt thuốc"],
                  ].map(([key, label, detail]) => (
                    <div className="volume-card" key={key}>
                      <div>
                        <span className={`region-dot ${key}`} />
                        <strong>{label}</strong>
                        <small>{detail}</small>
                      </div>
                      <p>
                        {ready
                          ? (job?.result?.volumes_cm3[key]?.toFixed(2) ?? "—")
                          : "—"}
                        <small>cm³</small>
                      </p>
                    </div>
                  ))}
                  <p className="volume-note">
                    WT, TC và ET có phần chồng nhau; không cộng ba thể tích.
                  </p>
                  {ready && job?.result && (
                    <VolumeChart volumes={job.result.volumes_cm3} />
                  )}
                  <div className="result-divider" />
                  <div className="download-stack">
                    {ready ? (
                      <>
                        <a
                          className="primary-button"
                          href={`/api/jobs/${job.id}/bundle`}
                          download
                        >
                          <ArrowDownToLine size={16} /> Tải toàn bộ kết quả{" "}
                          <span className="zip-label">ZIP</span>
                        </a>
                        <a
                          className="secondary-button"
                          href={artifactUrl(job.id, "mask")}
                          download
                        >
                          <ArrowDownToLine size={16} /> Mask NIfTI{" "}
                          <ArrowRight size={14} />
                        </a>
                        <a
                          className="secondary-button"
                          href={artifactUrl(job.id, "report")}
                          download
                        >
                          <FileText size={16} /> Báo cáo PDF{" "}
                          <ArrowRight size={14} />
                        </a>
                        <a
                          className="text-button"
                          href={artifactUrl(job.id, "json")}
                          download
                        >
                          Tải kết quả JSON <ArrowDownToLine size={13} />
                        </a>
                      </>
                    ) : (
                      <p className="waiting-note">
                        Chạy phân đoạn AI để xem thể tích, lớp phủ và tải kết
                        quả.
                      </p>
                    )}
                  </div>
                  {ready && (
                    <div className="inference-detail">
                      <CheckCircle2 size={14} /> {job.result?.seconds}s · Model
                      epoch {job.result?.selected_epoch}
                    </div>
                  )}
                </aside>
              </div>
            </>
          )}
          <footer className="page-footer">
            <span>
              <ShieldCheck size={13} /> Dành cho nghiên cứu và minh họa. Không
              thay thế chẩn đoán y khoa.
            </span>
            <span>
              BrainTumor AI <i /> v1.1
            </span>
          </footer>
        </div>
      </main>
      {modal && (
        <UploadDialog
          onClose={() => setModal(false)}
          onUploaded={(study) => {
            setModal(false);
            openStudy(study);
          }}
        />
      )}
      {info && (
        <Modal
          labelledBy="model-title"
          className="model-modal"
          onClose={() => setInfo(false)}
        >
          <header>
            <div className="square-icon">
              <BrainCircuit size={23} />
            </div>
            <button
              className="icon-button"
              onClick={() => setInfo(false)}
              aria-label="Đóng"
            >
              <X size={20} />
            </button>
          </header>
          <div className="eyebrow">MODEL CARD</div>
          <h2 id="model-title">3D U-Net · V2</h2>
          <p>
            Huấn luyện {model?.training_epochs ?? "—"} epoch. Model được chọn ở
            epoch {model?.selected_epoch ?? "—"} theo full-validation.
          </p>
          <div className="model-facts">
            <span>
              <Database size={16} /> BraTS2023 GLI
            </span>
            <span>
              <Activity size={16} /> Thiết bị: {model?.device || "—"}
            </span>
          </div>
          {model?.test && (
            <>
              <h3>Kết quả test đã ghi nhận · {model.test.case_count} ca</h3>
              <div className="metric-grid">
                {[
                  ["WT", model.test.dice_wt],
                  ["TC", model.test.dice_tc],
                  ["ET", model.test.dice_et],
                ].map(([label, value]) => (
                  <div key={label}>
                    <small>Dice {label}</small>
                    <strong>{(Number(value) * 100).toFixed(2)}%</strong>
                  </div>
                ))}
              </div>
            </>
          )}
          <p>
            Chỉ số trên thuộc tập test của lần train V2, không phải độ chính xác
            của ca mới. Chưa có ground truth thì không tính Dice cho ca tải lên.
          </p>
          <p className="upload-note">
            Phù hợp MRI đã tiền xử lý theo BraTS. Không tự căn chỉnh ảnh, skull
            stripping hoặc resample.
          </p>
          {model?.error && <div className="error-box">{model.error}</div>}
          <small className="checksum">
            SHA-256: {model?.weights_sha256 || "Chưa xác minh"}
          </small>
          <a
            className="secondary-button"
            href="/docs"
            target="_blank"
            rel="noreferrer"
          >
            Mở tài liệu API <ArrowRight size={15} />
          </a>
        </Modal>
      )}
    </div>
  );
}
function Stat({
  icon,
  title,
  value,
  detail,
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <span>{title}</span>
        <div>{icon}</div>
      </div>
      <strong className="stat-value">{value}</strong>
      <p>{detail}</p>
    </div>
  );
}
