import { describe, expect, test } from "bun:test";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  detectLocalChanges,
  gitAddCommit,
  gitClone,
  gitInit,
  isGitRepo,
} from "../../src/utils/git";
import { runCommand } from "../../src/utils/system";

describe("utils/git", () => {
  test("gitInit creates a git repository", async () => {
    const repoDir = await mkdtemp(join(tmpdir(), "ai-dev-git-"));

    try {
      expect(await isGitRepo(repoDir)).toBe(false);
      expect(await gitInit(repoDir)).toBe(true);
      expect(await isGitRepo(repoDir)).toBe(true);
    } finally {
      await rm(repoDir, { recursive: true, force: true });
    }
  });

  test("detectLocalChanges detects dirty and clean states", async () => {
    const repoDir = await mkdtemp(join(tmpdir(), "ai-dev-git-"));

    try {
      await gitInit(repoDir);
      await runCommand([
        "git",
        "-C",
        repoDir,
        "config",
        "user.email",
        "test@example.com",
      ]);
      await runCommand([
        "git",
        "-C",
        repoDir,
        "config",
        "user.name",
        "test-user",
      ]);

      const filePath = join(repoDir, "README.md");
      await writeFile(filePath, "hello\n", "utf8");

      expect(await detectLocalChanges(repoDir)).toBe(true);
      expect(await gitAddCommit(repoDir, "test commit")).toBe(true);
      expect(await detectLocalChanges(repoDir)).toBe(false);
    } finally {
      await rm(repoDir, { recursive: true, force: true });
    }
  });

  test("gitClone clones from local repository", async () => {
    const sourceRepo = await mkdtemp(join(tmpdir(), "ai-dev-git-src-"));
    const cloneDir = join(tmpdir(), `ai-dev-git-clone-${Date.now()}`);

    try {
      await gitInit(sourceRepo);
      await runCommand([
        "git",
        "-C",
        sourceRepo,
        "config",
        "user.email",
        "test@example.com",
      ]);
      await runCommand([
        "git",
        "-C",
        sourceRepo,
        "config",
        "user.name",
        "test-user",
      ]);
      await writeFile(join(sourceRepo, "a.txt"), "content\n", "utf8");
      await gitAddCommit(sourceRepo, "init");

      expect(await gitClone(sourceRepo, cloneDir)).toBe(true);
      expect(await isGitRepo(cloneDir)).toBe(true);
    } finally {
      await rm(sourceRepo, { recursive: true, force: true });
      await rm(cloneDir, { recursive: true, force: true });
    }
  });
});
