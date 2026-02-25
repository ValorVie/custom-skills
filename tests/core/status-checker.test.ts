import { describe, expect, test } from "bun:test";

import { checkEnvironment } from "../../src/core/status-checker";
import { NPM_PACKAGES, REPOS } from "../../src/utils/shared";

describe("core/status-checker", () => {
  test("checkEnvironment returns complete status payload", async () => {
    const status = await checkEnvironment();

    expect(status).toHaveProperty("git");
    expect(status).toHaveProperty("node");
    expect(status).toHaveProperty("bun");
    expect(status).toHaveProperty("gh");
    expect(Array.isArray(status.npmPackages)).toBe(true);
    expect(Array.isArray(status.repos)).toBe(true);
  });

  test("checkEnvironment includes configured packages and repositories", async () => {
    const status = await checkEnvironment();

    expect(status.npmPackages.length).toBe(NPM_PACKAGES.length);
    expect(status.repos.length).toBe(REPOS.length);
    expect(
      status.npmPackages.some(
        (pkg) => pkg.name === "@fission-ai/openspec@latest",
      ),
    ).toBe(true);
  });
});
