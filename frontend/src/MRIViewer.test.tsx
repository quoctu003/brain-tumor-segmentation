// @vitest-environment jsdom
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import MRIViewer from "./MRIViewer";

const state = vi.hoisted(() => ({ load: vi.fn(), opacity: vi.fn() }));
vi.mock("@niivue/niivue", () => ({
  MULTIPLANAR_TYPE: { GRID: 0 },
  SHOW_RENDER: { NEVER: 0 },
  SLICE_TYPE: { MULTIPLANAR: 0, RENDER: 1 },
  Niivue: class {
    volumes = [{}, { setColormapLabel: vi.fn() }];
    attachToCanvas = vi.fn().mockResolvedValue(undefined);
    loadVolumes = state.load;
    setOpacity = state.opacity;
    updateGLVolume = vi.fn();
    setSliceType = vi.fn();
    resizeListener = vi.fn();
    cleanup = vi.fn();
  },
}));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it("loads a hidden overlay with zero opacity and uses the latest setting after loading", async () => {
  let finish!: () => void;
  state.load.mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        finish = resolve;
      }),
  );
  const { rerender } = render(
    <MRIViewer
      caseId="case"
      modality="t2f"
      jobId="job"
      opacity={0.8}
      showOverlay={false}
    />,
  );
  await waitFor(() => expect(state.load).toHaveBeenCalled());
  expect(state.load.mock.calls[0][0][1].opacity).toBe(0);
  rerender(
    <MRIViewer
      caseId="case"
      modality="t2f"
      jobId="job"
      opacity={0.3}
      showOverlay
    />,
  );
  finish();
  await waitFor(() => expect(state.opacity).toHaveBeenLastCalledWith(1, 0.3));
});

it("keeps the viewer usable when fullscreen is unsupported", async () => {
  state.load.mockResolvedValue(undefined);
  render(<MRIViewer caseId="case" modality="t2f" opacity={0.5} showOverlay />);
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "3D" }).hasAttribute("disabled"),
    ).toBe(false),
  );
  fireEvent.click(screen.getByRole("button", { name: "Toàn màn hình" }));
  expect(screen.getByRole("alert").textContent).toContain("không hỗ trợ");
  expect(
    screen.getByRole("button", { name: "3D" }).hasAttribute("disabled"),
  ).toBe(false);
});
