import { expect, test } from "@playwright/test";
import { gzipSync } from "node:zlib";

// Synthetic NIfTI-1: no patient data, Drive download or trained model needed.
function syntheticMRI(channel: number) {
  const side = 32;
  const buffer = Buffer.alloc(352 + side ** 3 * 4);
  buffer.writeInt32LE(348, 0);
  buffer.writeInt16LE(3, 40);
  for (let axis = 0; axis < 3; axis++) {
    buffer.writeInt16LE(side, 42 + axis * 2);
    buffer.writeFloatLE(1, 80 + axis * 4);
    buffer.writeFloatLE(1, 280 + axis * 20);
  }
  buffer.writeInt16LE(16, 70); // float32
  buffer.writeInt16LE(32, 72);
  buffer.writeFloatLE(352, 108);
  buffer.writeFloatLE(1, 112);
  buffer[123] = 2; // mm
  buffer.writeInt16LE(1, 254); // sform: identity affine
  buffer.write("n+1\0", 344, "ascii");
  for (let voxel = 0; voxel < side ** 3; voxel++) {
    buffer.writeFloatLE(
      1 + ((voxel * 17 + channel * 13) % 199),
      352 + voxel * 4,
    );
  }
  return buffer;
}

test("manual upload accepts four MRI files and opens the study viewer", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width: 1366, height: 768 });
  await page.goto("/?demo=1");
  await expect(
    page.getByRole("button", { name: "Thêm ca MRI", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Mở demo", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Hướng dẫn demo", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Thêm ca MRI", exact: true }).click();
  await page.getByLabel("Tên ca nghiên cứu").fill("MRI 01");
  const inputs = [
    ["T1 Native", "t1n"],
    ["T1 Contrast", "t1c"],
    ["T2 Weighted", "t2w"],
    ["T2 FLAIR", "t2f"],
  ];
  for (const [index, [label, name]] of inputs.entries()) {
    const volume = syntheticMRI(index);
    await page.getByLabel(label, { exact: true }).setInputFiles({
      name: name === "t1n" ? "t1n.nii" : `${name}.nii.gz`,
      mimeType: "application/octet-stream",
      buffer: name === "t1n" ? volume : gzipSync(volume),
    });
  }
  const create = page.getByRole("button", {
    name: "Tạo ca nghiên cứu",
    exact: true,
  });
  await expect(create).toBeEnabled();
  await expect(create).toBeInViewport();
  await page.screenshot({
    path: testInfo.outputPath("manual-upload.png"),
    fullPage: true,
  });
  const uploaded = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/cases") &&
      response.request().method() === "POST",
  );
  await create.click();
  expect((await uploaded).status()).toBe(201);
  await expect(
    page.getByRole("heading", { name: "MRI 01", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".viewer-canvas canvas")).toBeVisible();
  await expect(page.locator(".viewer-message")).toHaveCount(0, {
    timeout: 60_000,
  });
  const model = await (await page.request.get("/api/model")).json();
  const inference = page.getByRole("button", {
    name: "Phân đoạn với AI",
    exact: true,
  });
  if (model.ready) await expect(inference).toBeEnabled();
  else await expect(inference).toBeDisabled();
  await expect(
    page.getByRole("link", { name: /Tải toàn bộ kết quả/ }),
  ).toHaveCount(0);
  for (const [label] of inputs) {
    await page.getByRole("button", { name: label, exact: true }).click();
    await expect(page.locator(".viewer-canvas canvas")).toBeVisible();
    await expect(page.locator(".viewer-message")).toHaveCount(0, {
      timeout: 60_000,
    });
  }
  await page.getByRole("button", { name: "3D", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "3D", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "3 mặt phẳng", exact: true }).click();
  await page.screenshot({
    path: testInfo.outputPath("manual-viewer.png"),
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test("system and mobile upload remain usable without presentation text", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Hệ thống", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Trạng thái hệ thống" }),
  ).toBeVisible();
  await expect(page.getByText("Ca demo", { exact: true })).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("link", { name: /BrainTumor/ }).click();
  await page.getByRole("button", { name: "Thêm ca MRI", exact: true }).click();
  await expect(
    page.getByRole("dialog", { name: "Thêm ca MRI mới" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
