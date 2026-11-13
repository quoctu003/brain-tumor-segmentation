// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import DemoCard from "./DemoCard";
import { request } from "./api";

vi.mock("./api", () => ({ request: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

it("automatically opens once when requested by the demo launcher", async () => {
  window.history.replaceState(null, "", "/?demo=1");
  const onOpen = vi.fn();
  vi.mocked(request).mockImplementation(async (_, options) =>
    options?.method === "POST" ? { id: "demo" } : { available: true },
  );
  const { rerender } = render(
    <DemoCard onOpen={onOpen} onGuide={() => {}} autoOpen />,
  );
  await vi.waitFor(() => expect(onOpen).toHaveBeenCalledOnce());
  expect(window.location.search).toBe("");
  rerender(<DemoCard onOpen={onOpen} onGuide={() => {}} autoOpen />);
  expect(
    vi
      .mocked(request)
      .mock.calls.filter(([, options]) => options?.method === "POST"),
  ).toHaveLength(1);
});

it("opens the recorded demo with one click and clearly labels saved inference", async () => {
  const demo = { id: "demo-case", name: "Demo" };
  vi.mocked(request).mockImplementation(async (_, options) =>
    options?.method === "POST" ? demo : { available: true },
  );
  const onOpen = vi.fn();
  render(<DemoCard onOpen={onOpen} onGuide={() => {}} />);
  const button = await screen.findByRole("button", { name: "Mở demo" });
  // Wait for availability to finish loading.
  await vi.waitFor(() => expect(button.hasAttribute("disabled")).toBe(false));
  fireEvent.click(button);
  await vi.waitFor(() => expect(onOpen).toHaveBeenCalledWith(demo));
  expect(
    screen.getByText(/Kết quả đã tính sẵn từ checkpoint thật/),
  ).toBeTruthy();
  expect(
    vi
      .mocked(request)
      .mock.calls.filter(([, options]) => options?.method === "POST"),
  ).toHaveLength(1);
});

it("shows an actionable error after a failed demo import", async () => {
  vi.mocked(request).mockImplementation(async (_, options) => {
    if (options?.method === "POST") throw new Error("Demo checksum mismatch");
    return { available: true };
  });
  render(<DemoCard onOpen={() => {}} onGuide={() => {}} />);
  await vi.waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Mở demo" }).hasAttribute("disabled"),
    ).toBe(false),
  );
  fireEvent.click(screen.getByRole("button", { name: "Mở demo" }));
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Demo checksum mismatch",
  );
  expect(screen.getByRole("button", { name: "Thử mở lại" })).toBeTruthy();
});
