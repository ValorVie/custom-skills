import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { syncStandards } from "../../src/core/standards-manager";
import {
  COPY_TARGETS,
  type ResourceType,
  type TargetType,
} from "../../src/utils/shared";

const RESOURCE_KEYS: ResourceType[] = ["skills", "commands", "agents"];

type TargetSnapshot = Record<string, string | undefined>;

function captureTargets(): TargetSnapshot {
  const snapshot: TargetSnapshot = {};
  for (const target of Object.keys(COPY_TARGETS) as TargetType[]) {
    for (const key of RESOURCE_KEYS) {
      snapshot[`${target}:${key}`] = COPY_TARGETS[target][key];
    }
  }
  return snapshot;
}

function restoreTargets(snapshot: TargetSnapshot): void {
  for (const target of Object.keys(COPY_TARGETS) as TargetType[]) {
    for (const key of RESOURCE_KEYS) {
      COPY_TARGETS[target][key] = snapshot[`${target}:${key}`];
    }
  }
}

function redirectTargets(root: string): void {
  for (const target of Object.keys(COPY_TARGETS) as TargetType[]) {
    for (const key of RESOURCE_KEYS) {
      if (!COPY_TARGETS[target][key]) continue;
      COPY_TARGETS[target][key] = join(root, "targets", target, key);
    }
  }
}

describe("core/standards-manager sync target + dry-run", () => {
  test("syncStandards with dryRun only reports counts and does not rename files", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-standards-dry-run-"));
    const snapshot = captureTargets();
    const standardsRoot = join(root, ".standards");
    const claudeSkillsRoot = join(root, "targets", "claude", "skills");

    try {
      redirectTargets(root);

      await mkdir(standardsRoot, { recursive: true });
      await writeFile(join(standardsRoot, "drop.ai.yaml"), "k: v\n", "utf8");
      await writeFile(
        join(standardsRoot, "disabled.yaml"),
        "standards:\n  - drop.ai.yaml\nskills:\n  - alpha\n",
        "utf8",
      );

      await mkdir(join(claudeSkillsRoot, "alpha"), { recursive: true });
      await writeFile(
        join(claudeSkillsRoot, "alpha", "SKILL.md"),
        "alpha\n",
        "utf8",
      );

      const result = await syncStandards(root, { dryRun: true });
      expect(result.success).toBe(true);
      expect(result.movedToDisabled).toBe(2);
      expect(result.restoredToActive).toBe(0);

      expect(await Bun.file(join(standardsRoot, "drop.ai.yaml")).exists()).toBe(
        true,
      );
      expect(
        await Bun.file(join(standardsRoot, ".disabled", "drop.ai.yaml")).exists(),
      ).toBe(false);
      expect(
        await Bun.file(join(claudeSkillsRoot, "alpha", "SKILL.md")).exists(),
      ).toBe(true);
      expect(
        await Bun.file(
          join(claudeSkillsRoot, "alpha.disabled", "SKILL.md"),
        ).exists(),
      ).toBe(false);
    } finally {
      restoreTargets(snapshot);
      await rm(root, { recursive: true, force: true });
    }
  });

  test("syncStandards target only affects selected target resources while standards sync stays global", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-standards-target-"));
    const snapshot = captureTargets();
    const standardsRoot = join(root, ".standards");
    const claudeSkillsRoot = join(root, "targets", "claude", "skills");
    const opencodeSkillsRoot = join(root, "targets", "opencode", "skills");

    try {
      redirectTargets(root);

      await mkdir(standardsRoot, { recursive: true });
      await writeFile(join(standardsRoot, "drop.ai.yaml"), "k: v\n", "utf8");
      await writeFile(
        join(standardsRoot, "disabled.yaml"),
        "standards:\n  - drop.ai.yaml\nskills:\n  - alpha\n",
        "utf8",
      );

      await mkdir(join(claudeSkillsRoot, "alpha"), { recursive: true });
      await writeFile(
        join(claudeSkillsRoot, "alpha", "SKILL.md"),
        "alpha\n",
        "utf8",
      );
      await mkdir(join(opencodeSkillsRoot, "alpha"), { recursive: true });
      await writeFile(
        join(opencodeSkillsRoot, "alpha", "SKILL.md"),
        "alpha\n",
        "utf8",
      );

      const result = await syncStandards(root, { target: "claude" });
      expect(result.success).toBe(true);
      expect(result.movedToDisabled).toBe(2);

      expect(
        await Bun.file(join(standardsRoot, ".disabled", "drop.ai.yaml")).exists(),
      ).toBe(true);

      expect(
        await Bun.file(
          join(claudeSkillsRoot, "alpha.disabled", "SKILL.md"),
        ).exists(),
      ).toBe(true);
      expect(
        await Bun.file(join(opencodeSkillsRoot, "alpha", "SKILL.md")).exists(),
      ).toBe(true);
      expect(
        await Bun.file(
          join(opencodeSkillsRoot, "alpha.disabled", "SKILL.md"),
        ).exists(),
      ).toBe(false);
    } finally {
      restoreTargets(snapshot);
      await rm(root, { recursive: true, force: true });
    }
  });
});
