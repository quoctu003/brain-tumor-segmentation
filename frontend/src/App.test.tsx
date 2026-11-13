// @vitest-environment jsdom
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import App from "./App";
import { request, type Job, type Study } from "./api";

vi.mock("./api", async (original) => ({
  ...(await original<typeof import("./api")>()),
  request: vi.fn(),
}));
vi.mock("./MRIViewer", () => ({
  default: ({ caseId }: { caseId: string }) => (
    <div data-testid="viewer">{caseId}</div>
  ),
}));

const job: Job = {
  id: "job-0",
  case_id: "case-0",
  status: "running",
  progress: 25,
  stage: "Segmenting",
  error: null,
  result: null,
};
function study(index: number, latest_job: Job | null = null): Study {
  return {
    id: `case-${index}`,
    name: `Study ${index}`,
    created_at: "2026-11-13T01:00:00Z",
    geometry: {
      shape: [12, 12, 12],
      spacing_mm: [1, 1, 1],
      orientation: ["R", "A", "S"],
      units_assumed_mm: false,
    },
    latest_job,
  };
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
async function openLibrary(
  cases: Study[],
  pending?: ReturnType<typeof deferred<Job>>,
) {
  vi.mocked(request).mockImplementation(async (path) => {
    if (path === "/model") return { ready: true };
    if (path === "/demo") return { available: true };
    if (path.endsWith("/jobs")) return [job];
    if (path.startsWith("/cases?"))
      return path.includes("offset=") ? [study(50)] : cases;
    if (path.startsWith("/jobs/")) return pending ? pending.promise : job;
    if (path.endsWith("/inference")) return pending ? pending.promise : job;
    throw new Error(`Unexpected request: ${path}`);
  });
  render(<App />);
  await screen.findByText("Study 0");
}
beforeEach(() => {
  vi.mocked(request).mockReset();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  window.history.replaceState(null, "", "/");
});

it("opens manual upload without promotional content or automatic case import", async () => {
  window.history.replaceState(null, "", "/?demo=1");
  await openLibrary([study(0)]);
  expect(screen.queryByRole("button", { name: "Mở demo" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Hướng dẫn demo" })).toBeNull();
  expect(vi.mocked(request).mock.calls.some(([path]) => path === "/demo")).toBe(
    false,
  );
  fireEvent.click(screen.getByRole("button", { name: "Thêm ca MRI" }));
  expect(screen.getByRole("dialog", { name: "Thêm ca MRI mới" })).toBeTruthy();
  for (const label of ["T1 Native", "T1 Contrast", "T2 Weighted", "T2 FLAIR"])
    expect(screen.getByLabelText(label)).toBeTruthy();
});

it("does not attach a late job update to a different selected study", async () => {
  const pending = deferred<Job>();
  await openLibrary([study(0, job), study(1)], pending);
  vi.useFakeTimers();
  fireEvent.click(screen.getByText("Study 0"));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2000);
  });
  fireEvent.click(screen.getByRole("link", { name: /BrainTumor/ }));
  fireEvent.click(screen.getByText("Study 1"));
  await act(async () => {
    pending.resolve({ ...job, progress: 70 });
  });
  expect(screen.getByRole("heading", { name: "Study 1" })).toBeTruthy();
  expect(screen.queryByText("Segmenting")).toBeNull();
  expect(
    screen
      .getByRole("button", { name: /Phân đoạn với AI/ })
      .hasAttribute("disabled"),
  ).toBe(false);
});

it("keeps additional pages while background jobs update", async () => {
  await openLibrary(
    Array.from({ length: 50 }, (_, i) => study(i, i === 0 ? job : null)),
  );
  fireEvent.click(screen.getByRole("button", { name: "Tải thêm ca" }));
  await screen.findByText("Study 50");
  vi.useFakeTimers();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(6000);
  });
  expect(screen.getByText("Study 50")).toBeTruthy();
  expect(
    vi
      .mocked(request)
      .mock.calls.filter(([path]) => path.startsWith("/cases?")),
  ).toHaveLength(2);
});

it("keeps the current study when an earlier inference request finishes", async () => {
  const pending = deferred<Job>();
  await openLibrary([study(0), study(1)], pending);
  fireEvent.click(screen.getByText("Study 0"));
  fireEvent.click(screen.getByRole("button", { name: /Phân đoạn với AI/ }));
  fireEvent.click(screen.getByRole("link", { name: /BrainTumor/ }));
  fireEvent.click(screen.getByText("Study 1"));
  await act(async () => {
    pending.resolve(job);
  });
  expect(screen.getByRole("heading", { name: "Study 1" })).toBeTruthy();
  expect(screen.queryByText("Segmenting")).toBeNull();
});
