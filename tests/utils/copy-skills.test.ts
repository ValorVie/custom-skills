import { describe, expect, test } from "bun:test";
import { access, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  COPY_TARGETS,
  copySkills,
  getAllSkillNames,
} from "../../src/utils/shared";

describe("utils/copy-skills", () => {
  test("getAllSkillNames returns skill directories", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-copy-skills-"));

    try {
      await mkdir(join(root, "alpha"), { recursive: true });
      await mkdir(join(root, "beta"), { recursive: true });
      await writeFile(join(root, "alpha", "SKILL.md"), "alpha\n", "utf8");
      await writeFile(join(root, "beta", "SKILL.md"), "beta\n", "utf8");

      const skills = await getAllSkillNames(root);
      expect(skills).toEqual(["alpha", "beta"]);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("copySkills copies skills to selected target", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-copy-skills-"));
    const sourceDir = join(root, "source");
    const targetDir = join(root, "target");
    const previous = COPY_TARGETS.claude.skills;

    try {
      await mkdir(join(sourceDir, "alpha"), { recursive: true });
      await writeFile(join(sourceDir, "alpha", "SKILL.md"), "alpha\n", "utf8");

      COPY_TARGETS.claude.skills = targetDir;

      const result = await copySkills({
        sourceDir,
        targets: ["claude"],
      });

      expect(result.copied).toBe(1);
      await access(join(targetDir, "alpha", "SKILL.md"));
    } finally {
      COPY_TARGETS.claude.skills = previous;
      await rm(root, { recursive: true, force: true });
    }
  });
});
