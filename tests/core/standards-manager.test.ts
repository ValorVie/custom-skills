import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  detectOverlaps,
  getStandardsStatus,
  listProfiles,
  switchProfile,
} from "../../src/core/standards-manager";

describe("core/standards-manager", () => {
  test("listProfiles and switchProfile work with profile files", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "ai-dev-standards-"));

    try {
      const profilesDir = join(projectRoot, ".standards", "profiles");
      await mkdir(profilesDir, { recursive: true });

      await writeFile(
        join(profilesDir, "level-1.yaml"),
        "skills:\n  - a\n",
        "utf8",
      );
      await writeFile(
        join(profilesDir, "level-2.yaml"),
        "skills:\n  - b\n",
        "utf8",
      );

      const profiles = await listProfiles(projectRoot);
      expect(profiles).toEqual(["level-1", "level-2"]);

      const switched = await switchProfile("level-1", { projectRoot });
      expect(switched.success).toBe(true);

      const status = await getStandardsStatus(projectRoot);
      expect(status.initialized).toBe(true);
      expect(status.activeProfile).toBe("level-1");
    } finally {
      await rm(projectRoot, { recursive: true, force: true });
    }
  });

  test("detectOverlaps finds duplicated items across profiles", async () => {
    const rootPath = join(tmpdir(), `ai-dev-standards-${Date.now()}-ov`);

    try {
      const profilesDir = join(rootPath, ".standards", "profiles");
      await mkdir(profilesDir, { recursive: true });

      await writeFile(
        join(profilesDir, "alpha.yaml"),
        "skills:\n  - common\n  - only-alpha\n",
        "utf8",
      );
      await writeFile(
        join(profilesDir, "beta.yaml"),
        "skills:\n  - common\n  - only-beta\n",
        "utf8",
      );

      const overlaps = await detectOverlaps(rootPath);
      expect(overlaps["skills:common"]).toEqual(["alpha", "beta"]);
    } finally {
      await rm(rootPath, { recursive: true, force: true });
    }
  });
});
