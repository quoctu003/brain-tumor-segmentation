import { afterEach, describe, expect, it, vi } from "vitest";
import { request } from "./api";

afterEach(() => vi.unstubAllGlobals());

describe("API responses", () => {
  it("accepts an empty successful delete response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );
    await expect(
      request<void>("/cases/id", { method: "DELETE" }),
    ).resolves.toBeUndefined();
  });

  it("turns field validation errors into readable messages", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          Response.json(
            { detail: [{ loc: ["body", "name"], msg: "Field required" }] },
            { status: 422 },
          ),
        ),
    );
    await expect(request("/cases")).rejects.toThrow("name: Field required");
  });

  it("handles an HTML error page from the proxy", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response("<html>Bad gateway</html>", { status: 502 }),
        ),
    );
    await expect(request("/cases")).rejects.toThrow("HTTP 502");
  });
});
