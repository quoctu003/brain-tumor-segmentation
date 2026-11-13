import { useEffect, useRef, useState } from "react";
import {
  MULTIPLANAR_TYPE,
  Niivue,
  SHOW_RENDER,
  SLICE_TYPE,
} from "@niivue/niivue";
import { Maximize2, ScanLine } from "lucide-react";
import { artifactUrl, volumeUrl } from "./api";

type Props = {
  caseId: string;
  modality: string;
  jobId?: string;
  opacity: number;
  showOverlay: boolean;
};
export default function MRIViewer({
  caseId,
  modality,
  jobId,
  opacity,
  showOverlay,
}: Props) {
  const host = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const viewer = useRef<Niivue | null>(null);
  const display = useRef({ opacity, showOverlay });
  display.current = { opacity, showOverlay };
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [fullscreenError, setFullscreenError] = useState("");
  const [mode, setMode] = useState<"multi" | "3d">("multi");
  useEffect(() => {
    let cancelled = false;
    const canvas = canvasRef.current!;
    const nv = new Niivue({
      backColor: [0.035, 0.045, 0.055, 1],
      crosshairColor: [0.35, 0.85, 0.77, 0.65],
      isColorbar: false,
      isRadiologicalConvention: true,
      show3Dcrosshair: true,
      isOrientCube: true,
      isResizeCanvas: true,
      multiplanarLayout: MULTIPLANAR_TYPE.GRID,
      multiplanarShowRender: SHOW_RENDER.NEVER,
      loadingText: "Loading MRI...",
    });
    viewer.current = nv;
    setLoading(true);
    setError("");
    async function load() {
      try {
        await nv.attachToCanvas(canvas);
        if (cancelled) return;
        const volumes = [
          {
            url: volumeUrl(caseId, modality),
            name: `${modality}.nii.gz`,
            colormap: "gray",
            opacity: 1,
          },
        ];
        if (jobId)
          volumes.push({
            url: artifactUrl(jobId, "mask"),
            name: "segmentation.nii.gz",
            colormap: "warm",
            opacity: display.current.showOverlay ? display.current.opacity : 0,
          });
        await nv.loadVolumes(volumes);
        if (cancelled) return;
        if (nv.volumes[1]) {
          nv.volumes[1].setColormapLabel({
            R: [0, 239, 77, 250],
            G: [0, 91, 199, 188],
            B: [0, 108, 150, 83],
            A: [0, 255, 255, 255],
            I: [0, 1, 2, 3],
            labels: ["Background", "NCR/NET", "Edema", "ET"],
          });
          nv.updateGLVolume();
          nv.setOpacity(
            1,
            display.current.showOverlay ? display.current.opacity : 0,
          );
        }
        nv.setSliceType(SLICE_TYPE.MULTIPLANAR);
        nv.resizeListener();
        setMode("multi");
        setLoading(false);
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof Error
              ? e.message
              : "Không thể mở MRI. Kiểm tra WebGL2.",
          );
          setLoading(false);
        }
      } finally {
        if (cancelled) nv.cleanup();
      }
    }
    void load();
    return () => {
      cancelled = true;
      if (viewer.current === nv) viewer.current = null;
      nv.cleanup();
    };
  }, [caseId, modality, jobId]);
  useEffect(() => {
    if (!loading && viewer.current?.volumes[1])
      viewer.current.setOpacity(1, showOverlay ? opacity : 0);
  }, [opacity, showOverlay, loading]);
  function changeMode(next: "multi" | "3d") {
    setMode(next);
    viewer.current?.setSliceType(
      next === "multi" ? SLICE_TYPE.MULTIPLANAR : SLICE_TYPE.RENDER,
    );
  }
  async function toggleFullscreen() {
    setFullscreenError("");
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (host.current?.parentElement?.requestFullscreen)
        await host.current.parentElement.requestFullscreen();
      else setFullscreenError("Trình duyệt không hỗ trợ toàn màn hình.");
    } catch {
      setFullscreenError("Trình duyệt không cho phép toàn màn hình.");
    }
  }
  return (
    <div className="viewer-shell">
      <div className="viewer-toolbar">
        <span>
          <ScanLine size={15} /> MRI VIEWER <i /> {modality.toUpperCase()}
        </span>
        <div className="segmented">
          <button
            className={mode === "multi" ? "selected" : ""}
            disabled={loading || !!error}
            aria-pressed={mode === "multi"}
            onClick={() => changeMode("multi")}
          >
            3 mặt phẳng
          </button>
          <button
            className={mode === "3d" ? "selected" : ""}
            disabled={loading || !!error}
            aria-pressed={mode === "3d"}
            onClick={() => changeMode("3d")}
          >
            3D
          </button>
        </div>
        <button
          className="icon-button"
          title="Toàn màn hình"
          aria-label="Toàn màn hình"
          onClick={() => void toggleFullscreen()}
        >
          <Maximize2 size={16} />
        </button>
      </div>
      <div className="viewer-canvas" ref={host}>
        <canvas
          ref={canvasRef}
          key={`${caseId}:${modality}:${jobId ?? ""}`}
          aria-label="MRI ba mặt phẳng: axial, coronal, sagittal"
          tabIndex={0}
        />
      </div>
      {loading && (
        <div className="viewer-message">
          <span className="spinner" /> Đang tải thể tích MRI…
        </div>
      )}
      {error && (
        <div className="viewer-message error">Không thể mở MRI: {error}</div>
      )}
      <div className="viewer-footer">
        {fullscreenError && <span role="alert">{fullscreenError}</span>}
        <span>
          <i className="live-dot" /> Hướng hiển thị radiological · R / L theo
          ảnh
        </span>
        <span>Cuộn: lát cắt · Kéo: vị trí · Chuột phải: độ tương phản</span>
      </div>
    </div>
  );
}
