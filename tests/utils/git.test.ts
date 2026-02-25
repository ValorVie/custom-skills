import { describe, expect, test } from "bun:test";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  detectLocalChanges,
  gitAddCommit,
  gitClone,
  gitInit,
  gitPull,
  gitPullRebase,
  gitPush,
  isGitRepo,
} from "../../src/utils/git";
import { runCommand } from "../../src/utils/system";

async function configureGitUser(repoDir: string): Promise<void> {
  await runCommand([
    "git",
    "-C",
    repoDir,
    "config",
    "user.email",
    "test@example.com",
  ]);
  await runCommand(["git", "-C", repoDir, "config", "user.name", "test-user"]);
}

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

  test("gitPull and gitPullRebase return false when no remote is configured", async () => {
    const repoDir = await mkdtemp(join(tmpdir(), "ai-dev-git-"));

    try {
      await gitInit(repoDir);
      expect(await gitPull(repoDir)).toBe(false);
      expect(await gitPullRebase(repoDir)).toBe(false);
    } finally {
      await rm(repoDir, { recursive: true, force: true });
    }
  });

  test("gitPush and gitPull work with a local bare remote", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-git-remote-"));
    const remoteRepo = join(root, "remote.git");
    const sourceRepo = await mkdtemp(join(root, "source-"));
    const cloneRepo = join(root, "clone");

    try {
      await runCommand(["git", "init", "--bare", remoteRepo]);
      await gitInit(sourceRepo);
      await configureGitUser(sourceRepo);

      await writeFile(join(sourceRepo, "a.txt"), "one\n", "utf8");
      await gitAddCommit(sourceRepo, "initial commit");
      await runCommand(["git", "-C", sourceRepo, "branch", "-M", "main"]);
      await runCommand([
        "git",
        "-C",
        sourceRepo,
        "remote",
        "add",
        "origin",
        remoteRepo,
      ]);

      expect(await gitPush(sourceRepo)).toBe(true);

      await runCommand([
        "git",
        "-C",
        remoteRepo,
        "symbolic-ref",
        "HEAD",
        "refs/heads/main",
      ]);

      expect(await gitClone(remoteRepo, cloneRepo)).toBe(true);

      await writeFile(join(sourceRepo, "a.txt"), "two\n", "utf8");
      await gitAddCommit(sourceRepo, "second commit");
      expect(await gitPush(sourceRepo)).toBe(true);

      expect(await gitPull(cloneRepo)).toBe(true);
      expect(await gitPullRebase(cloneRepo)).toBe(true);

      const pulled = await readFile(join(cloneRepo, "a.txt"), "utf8");
      expect(pulled).toBe("two\n");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});
