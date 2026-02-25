import { describe, expect, test } from "bun:test";

import { runInstall } from "../../src/core/installer";

describe("core/installer", () => {
  test("runInstall returns structured result", async () => {
    const result = await runInstall({
      skipNpm: true,
      skipBun: true,
      skipRepos: true,
    });

    expect(result).toHaveProperty("prerequisites");
    expect(result).toHaveProperty("npmPackages");
    expect(result).toHaveProperty("bunPackages");
    expect(result).toHaveProperty("repos");
    expect(result).toHaveProperty("errors");
  });

  test("runInstall respects skip options", async () => {
    const result = await runInstall({
      skipNpm: true,
      skipBun: true,
      skipRepos: true,
    });

    expect(result.npmPackages.length).toBe(0);
    expect(result.bunPackages.length).toBe(0);
    expect(result.repos.length).toBe(0);
  });
});
