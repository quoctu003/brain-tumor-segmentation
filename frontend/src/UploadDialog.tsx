import { useState } from "react";
import { Check, FileUp, UploadCloud, X } from "lucide-react";
import { request, type Study } from "./api";
import Modal from "./Modal";

const modalities = [
  { key: "t1n", title: "T1 Native", detail: "Ảnh T1 trước tiêm" },
  { key: "t1c", title: "T1 Contrast", detail: "Ảnh T1 sau tiêm" },
  { key: "t2w", title: "T2 Weighted", detail: "Ảnh T2" },
  { key: "t2f", title: "T2 FLAIR", detail: "Ảnh T2-FLAIR" },
];
export default function UploadDialog({
  onClose,
  onUploaded,
}: {
  onClose: () => void;
  onUploaded: (study: Study) => void;
}) {
  const [name, setName] = useState("");
  const [files, setFiles] = useState<Record<string, File>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = new FormData();
      data.append("name", name.trim());
      for (const m of modalities) data.append(m.key, files[m.key]);
      const study = await request<Study>("/cases", {
        method: "POST",
        body: data,
      });
      onUploaded(study);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Tải lên thất bại");
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal
      labelledBy="upload-title"
      onClose={onClose}
      busy={busy}
      className="upload-modal"
    >
      <header>
        <div className="square-icon">
          <UploadCloud size={22} />
        </div>
        <button
          disabled={busy}
          onClick={onClose}
          className="icon-button"
          aria-label="Đóng"
        >
          <X size={20} />
        </button>
      </header>
      <h2 id="upload-title">Thêm ca MRI mới</h2>
      <p>Nạp đủ 4 chuỗi xung đã được căn chỉnh trên cùng lưới voxel.</p>
      <form onSubmit={(e) => void submit(e)}>
        <label className="field-label" htmlFor="study-name">
          Tên ca nghiên cứu
        </label>
        <input
          autoFocus
          id="study-name"
          className="text-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Ví dụ: BraTS-GLI-00016-000"
          maxLength={120}
          required
          disabled={busy}
        />
        <div className="upload-grid">
          {modalities.map((m) => (
            <label
              className={`upload-slot ${files[m.key] ? "has-file" : ""}`}
              key={m.key}
            >
              <input
                type="file"
                aria-label={m.title}
                accept=".nii,.nii.gz"
                disabled={busy}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (
                    file &&
                    (!/\.nii(\.gz)?$/i.test(file.name) || file.size === 0)
                  ) {
                    setError(
                      `${m.title}: chọn file NIfTI .nii hoặc .nii.gz có dữ liệu.`,
                    );
                    e.target.value = "";
                    setFiles((f) => {
                      const next = { ...f };
                      delete next[m.key];
                      return next;
                    });
                    return;
                  }
                  setError("");
                  setFiles((f) => {
                    const next = { ...f };
                    if (file) next[m.key] = file;
                    else delete next[m.key];
                    return next;
                  });
                }}
              />
              <span className="upload-icon">
                {files[m.key] ? <Check size={20} /> : <FileUp size={20} />}
              </span>
              <strong>{m.title}</strong>
              <small>{files[m.key]?.name || m.detail}</small>
              <em>
                {files[m.key]
                  ? `${(files[m.key].size / 1024 ** 2).toFixed(1)} MB`
                  : ".nii hoặc .nii.gz"}
              </em>
            </label>
          ))}
        </div>
        <p className="upload-note">
          MRI theo protocol BraTS, đơn vị mm. Ứng dụng không tự đăng ký ảnh hoặc
          resample. Chỉ dùng dữ liệu đã ẩn danh.
        </p>
        {error && (
          <div className="error-box" role="alert">
            {error}
          </div>
        )}
        <button
          className="primary-button full-width"
          disabled={
            busy || !name.trim() || modalities.some((m) => !files[m.key])
          }
        >
          {busy ? (
            <>
              <span className="spinner" /> Đang tải và kiểm tra ảnh…
            </>
          ) : (
            <>
              <UploadCloud size={17} /> Tạo ca nghiên cứu
            </>
          )}
        </button>
      </form>
    </Modal>
  );
}
