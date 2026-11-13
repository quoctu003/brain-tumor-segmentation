import { expect, test } from "@playwright/test";
import { resolve } from "node:path";
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";

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
  for (const [label, name] of inputs) {
    const path = resolve(`../demo/${name}.nii.gz`);
    await page.getByLabel(label, { exact: true }).setInputFiles(
      name === "t1n"
        ? {
            name: "t1n.nii",
            mimeType: "application/octet-stream",
            buffer: gunzipSync(readFileSync(path)),
          }
        : path,
    );
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
  await expect(
    page.getByRole("button", { name: "Phân đoạn với AI", exact: true }),
  ).toBeEnabled();
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
