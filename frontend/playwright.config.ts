import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";

const edge =
  process.platform === "win32" &&
  existsSync("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe");
export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.e2e.ts",
  timeout: 180_000,
  expect: { timeout: 30_000 },
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:8086",
    viewport: { width: 1440, height: 1000 },
    headless: true,
    channel: edge ? "msedge" : undefined,
    launchOptions: {
      args: ["--use-angle=swiftshader-webgl", "--enable-unsafe-swiftshader"],
    },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "python ../scripts/serve_e2e.py",
    url: "http://127.0.0.1:8086/api/health",
    reuseExistingServer: false,
    timeout: 180_000,
    gracefulShutdown: { signal: "SIGINT", timeout: 15_000 },
  },
});
