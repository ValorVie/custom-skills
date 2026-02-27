import { describe, expect, test } from "bun:test";
import {
  access,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  writeFile,
} from "node:fs/promises";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";

import {
  createDefaultSyncEngine,
  defaultDirectories,
  expandHome,
  SyncEngine,
} from "../../src/core/sync-engine";

describe("sync-engine defaults", () => {
  const home = homedir();

  test("defaultDirectories returns expected structure", () => {
    const dirs = defaultDirectories();
    expect(dirs).toHaveLength(1);
    expect(dirs[0].path).toBe("~/.claude");
    expect(dirs[0].repoSubdir).toBe("claude");
    expect(dirs[0].ignoreProfile).toBe("claude");
    expect(dirs[0].customIgnore).toEqual([]);
  });

  test("expandHome expands ~ to homedir", () => {
    expect(expandHome("~/.claude")).toBe(join(home, ".claude"));
  });

  test("expandHome preserves absolute paths", () => {
    expect(expandHome("/absolute/path")).toBe("/absolute/path");
  });

  test("createDefaultSyncEngine returns SyncEngine instance", () => {
    const engine = createDefaultSyncEngine();
    expect(engine).toBeInstanceOf(SyncEngine);
  });
});

describe("core/sync-engine", () => {
  test("init creates config and default directory", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const engine = new SyncEngine(configPath, repoDir);

    try {
      const config = await engine.init("https://example.com/repo.git");
      expect(config.remote).toBe("https://example.com/repo.git");
      const raw = await readFile(configPath, "utf8");
      expect(raw.length > 0).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("add and remove directory update config", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const engine = new SyncEngine(configPath, repoDir);

    try {
      await engine.init("https://example.com/repo.git");
      const trackedDir = join(root, "workspace", "project");
      await mkdir(trackedDir, { recursive: true });
      const added = await engine.addDirectory(trackedDir);
      expect(
        added.directories.some((dir) => dir.path === trackedDir),
      ).toBe(true);

      const removed = await engine.removeDirectory(trackedDir);
      expect(
        removed.directories.some((dir) => dir.path === trackedDir),
      ).toBe(false);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push and pull sync files between local and repo dirs", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const engine = new SyncEngine(configPath, repoDir);

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");

      await engine.init("https://example.com/repo.git");
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      await engine.push();
      await rm(localDir, { recursive: true, force: true });
      await engine.pull();

      const restored = await readFile(join(localDir, "a.txt"), "utf8");
      expect(restored).toBe("hello\n");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("init without remote creates git helper files", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const engine = new SyncEngine(configPath, repoDir);

    try {
      const config = await engine.init();
      expect(config.remote).toBe("");

      const gitignore = await readFile(join(repoDir, ".gitignore"), "utf8");
      expect(gitignore).toContain("node_modules/");

      const gitattributes = await readFile(
        join(repoDir, ".gitattributes"),
        "utf8",
      );
      expect(gitattributes).toContain("filter=lfs");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push supports force option and writes manifest", async () => {
    const calls: string[][] = [];
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        calls.push(command);
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");

      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);
      await engine.push({ force: true });

      await access(join(repoDir, "plugin-manifest.json"));
      expect(
        calls.some(
          (command) =>
            command[0] === "git" &&
            command.includes("push") &&
            command.includes("--force"),
        ),
      ).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("pull supports no-delete and force options", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");

      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);
      await engine.push();

      await writeFile(join(localDir, "local-only.txt"), "keep\n", "utf8");
      await engine.pull({ noDelete: true, force: true });

      const kept = await readFile(join(localDir, "local-only.txt"), "utf8");
      expect(kept).toBe("keep\n");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("status includes local change count and remote behind count", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        if (command.includes("status")) {
          return { stdout: " M a.txt\n?? b.txt\n", stderr: "", exitCode: 0 };
        }
        if (command.includes("rev-list")) {
          return { stdout: "0 3\n", stderr: "", exitCode: 0 };
        }
        if (command.includes("rev-parse")) {
          return { stdout: "main\n", stderr: "", exitCode: 0 };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await engine.init();
      const status = await engine.status();
      expect(status.localChanges).toBe(2);
      expect(status.remoteBehind).toBe(3);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});
