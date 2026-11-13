// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import UploadDialog from "./UploadDialog";

afterEach(() => cleanup());

it("rejects unsupported and empty uploads before sending a request", () => {
  render(<UploadDialog onClose={() => {}} onUploaded={() => {}} />);
  const input = screen.getByLabelText("T1 Native");
  fireEvent.change(input, {
    target: { files: [new File(["abc"], "scan.txt")] },
  });
  expect(screen.getByRole("alert").textContent).toContain("NIfTI");
  fireEvent.change(input, { target: { files: [new File([], "scan.nii.gz")] } });
  expect(screen.getByRole("alert").textContent).toContain("có dữ liệu");
  fireEvent.change(input, {
    target: { files: [new File(["nifti"], "scan.NII.GZ")] },
  });
  expect(screen.queryByRole("alert")).toBeNull();
  expect(screen.getByText("scan.NII.GZ")).toBeTruthy();
});

it("keeps keyboard focus inside the dialog and closes on Escape", () => {
  const onClose = vi.fn();
  const opener = document.createElement("button");
  document.body.appendChild(opener);
  opener.focus();
  const { unmount } = render(
    <UploadDialog onClose={onClose} onUploaded={() => {}} />,
  );
  const first = screen.getByRole("button", { name: "Đóng" });
  first.focus();
  fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
  expect(document.activeElement).toBe(screen.getByLabelText("T2 FLAIR"));
  fireEvent.keyDown(document, { key: "Escape" });
  expect(onClose).toHaveBeenCalledOnce();
  unmount();
  expect(document.activeElement).toBe(opener);
  opener.remove();
});
