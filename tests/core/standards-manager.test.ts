import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  computeDisabledItems,
  detectOverlaps,
  getStandardsStatus,
  listProfiles,
  switchProfile,
  syncStandards,
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

  test("computeDisabledItems computes standards diff", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "ai-dev-standards-diff-"));

    try {
      const standardsRoot = join(projectRoot, ".standards");
      const profilesRoot = join(standardsRoot, "profiles");
      await mkdir(profilesRoot, { recursive: true });

      await writeFile(join(standardsRoot, "keep.ai.yaml"), "k: v\n", "utf8");
      await writeFile(join(standardsRoot, "drop.ai.yaml"), "k: v\n", "utf8");
      await writeFile(
        join(profilesRoot, "level-1.yaml"),
        "standards:\n  - keep.ai.yaml\n",
        "utf8",
      );

      const disabled = await computeDisabledItems("level-1", projectRoot);
      expect(disabled.standards).toEqual(["drop.ai.yaml"]);
    } finally {
      await rm(projectRoot, { recursive: true, force: true });
    }
  });

  test("switchProfile writes disabled.yaml and moves disabled standards", async () => {
    const projectRoot = await mkdtemp(
      join(tmpdir(), "ai-dev-standards-switch-disable-"),
    );

    try {
      const standardsRoot = join(projectRoot, ".standards");
      const profilesRoot = join(standardsRoot, "profiles");
      await mkdir(profilesRoot, { recursive: true });

      await writeFile(join(standardsRoot, "keep.ai.yaml"), "k: v\n", "utf8");
      await writeFile(join(standardsRoot, "drop.ai.yaml"), "k: v\n", "utf8");
      await writeFile(
        join(profilesRoot, "level-1.yaml"),
        "standards:\n  - keep.ai.yaml\n",
        "utf8",
      );

      const result = await switchProfile("level-1", { projectRoot });
      expect(result.success).toBe(true);

      const disabledYaml = Bun.file(join(standardsRoot, "disabled.yaml"));
      expect(await disabledYaml.exists()).toBe(true);
      const disabledContent = await disabledYaml.text();
      expect(disabledContent).toContain("drop.ai.yaml");

      expect(await Bun.file(join(standardsRoot, "keep.ai.yaml")).exists()).toBe(
        true,
      );
      expect(
        await Bun.file(
          join(standardsRoot, ".disabled", "drop.ai.yaml"),
        ).exists(),
      ).toBe(true);
    } finally {
      await rm(projectRoot, { recursive: true, force: true });
    }
  });

  test("syncStandards enforces disabled.yaml to .disabled", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "ai-dev-standards-sync-"));

    try {
      const standardsRoot = join(projectRoot, ".standards");
      await mkdir(standardsRoot, { recursive: true });

      await writeFile(join(standardsRoot, "drop.ai.yaml"), "k: v\n", "utf8");
      await writeFile(
        join(standardsRoot, "disabled.yaml"),
        "standards:\n  - drop.ai.yaml\n",
        "utf8",
      );

      const result = await syncStandards(projectRoot);
      expect(result.success).toBe(true);
      expect(result.movedToDisabled).toBe(1);
      expect(
        await Bun.file(
          join(standardsRoot, ".disabled", "drop.ai.yaml"),
        ).exists(),
      ).toBe(true);
    } finally {
      await rm(projectRoot, { recursive: true, force: true });
    }
  });
});
