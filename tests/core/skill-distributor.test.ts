import { describe, expect, test } from "bun:test";
import {
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { distributeSkills } from "../../src/core/skill-distributor";
import { COPY_TARGETS } from "../../src/utils/shared";

describe("core/skill-distributor", () => {
  test("distributeSkills copies skills to target", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-distribute-"));
    const sourceRoot = join(root, "source");
    const targetSkills = join(root, "targets", "claude", "skills");
    const previousSkillsPath = COPY_TARGETS.claude.skills;

    try {
      await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
      await writeFile(
        join(sourceRoot, "skills", "alpha", "SKILL.md"),
        "alpha\n",
        "utf8",
      );
      COPY_TARGETS.claude.skills = targetSkills;

      const result = await distributeSkills({
        sourceRoot,
        targets: ["claude"],
      });

      expect(result.errors.length).toBe(0);
      expect(result.conflicts.length).toBe(0);
      expect(
        result.distributed.some(
          (item) =>
            item.target === "claude" &&
            item.type === "skills" &&
            item.name === "alpha",
        ),
      ).toBe(true);

      const copied = await readFile(
        join(targetSkills, "alpha", "SKILL.md"),
        "utf8",
      );
      expect(copied.trim()).toBe("alpha");
    } finally {
      COPY_TARGETS.claude.skills = previousSkillsPath;
      await rm(root, { recursive: true, force: true });
    }
  });

  test("distributeSkills reports conflicts without force", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-distribute-"));
    const sourceRoot = join(root, "source");
    const targetSkills = join(root, "targets", "claude", "skills");
    const previousSkillsPath = COPY_TARGETS.claude.skills;

    try {
      await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
      await writeFile(
        join(sourceRoot, "skills", "alpha", "SKILL.md"),
        "new\n",
        "utf8",
      );
      await mkdir(join(targetSkills, "alpha"), { recursive: true });
      await writeFile(join(targetSkills, "alpha", "SKILL.md"), "old\n", "utf8");

      COPY_TARGETS.claude.skills = targetSkills;
      const result = await distributeSkills({
        sourceRoot,
        targets: ["claude"],
      });

      expect(result.conflicts.length).toBe(1);
      const current = await readFile(
        join(targetSkills, "alpha", "SKILL.md"),
        "utf8",
      );
      expect(current.trim()).toBe("old");
    } finally {
      COPY_TARGETS.claude.skills = previousSkillsPath;
      await rm(root, { recursive: true, force: true });
    }
  });

  test("distributeSkills can force overwrite conflict", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-distribute-"));
    const sourceRoot = join(root, "source");
    const targetSkills = join(root, "targets", "claude", "skills");
    const previousSkillsPath = COPY_TARGETS.claude.skills;

    try {
      await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
      await writeFile(
        join(sourceRoot, "skills", "alpha", "SKILL.md"),
        "new\n",
        "utf8",
      );
      await mkdir(join(targetSkills, "alpha"), { recursive: true });
      await writeFile(join(targetSkills, "alpha", "SKILL.md"), "old\n", "utf8");

      COPY_TARGETS.claude.skills = targetSkills;
      const result = await distributeSkills({
        sourceRoot,
        targets: ["claude"],
        force: true,
      });

      expect(result.conflicts.length).toBe(0);
      const current = await readFile(
        join(targetSkills, "alpha", "SKILL.md"),
        "utf8",
      );
      expect(current.trim()).toBe("new");
    } finally {
      COPY_TARGETS.claude.skills = previousSkillsPath;
      await rm(root, { recursive: true, force: true });
    }
  });

  test("distributeSkills uses symlink in developer mode", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-distribute-"));
    const sourceRoot = join(root, "source");
    const targetSkills = join(root, "targets", "claude", "skills");
    const previousSkillsPath = COPY_TARGETS.claude.skills;

    try {
      await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
      await writeFile(
        join(sourceRoot, "skills", "alpha", "SKILL.md"),
        "alpha\n",
        "utf8",
      );

      COPY_TARGETS.claude.skills = targetSkills;
      const result = await distributeSkills({
        sourceRoot,
        targets: ["claude"],
        devMode: true,
      });

      expect(result.errors.length).toBe(0);
      const info = await lstat(join(targetSkills, "alpha"));
      expect(info.isSymbolicLink()).toBe(true);
    } finally {
      COPY_TARGETS.claude.skills = previousSkillsPath;
      await rm(root, { recursive: true, force: true });
    }
  });
});
