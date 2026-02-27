import { describe, expect, test } from "bun:test";
import { access, mkdtemp, readFile, rm, writeFile, mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { SyncEngine } from "../../src/core/sync-engine";
import { paths } from "../../src/utils/paths";

describe("core/sync-engine init parity", () => {
  test("init throws when git clone fails", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-init-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        if (command[0] === "git" && command[1] === "clone") {
          return {
            stdout: "",
            stderr: "fatal: unable to access remote repository",
            exitCode: 1,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await expect(
        engine.init("https://bad.example.com/repo.git"),
      ).rejects.toThrow("git clone");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("init requires confirmation when sync config already exists", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-init-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    let runCalls = 0;

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async () => {
        runCalls += 1;
        return { stdout: "", stderr: "", exitCode: 0 };
      },
      confirmReinitFn: async () => false,
    });

    try {
      await engine.saveConfig({
        version: "1",
        remote: "https://example.com/existing.git",
        lastSync: null,
        directories: [],
      });

      await expect(
        engine.init("https://example.com/reinit.git"),
      ).rejects.toThrow("cancelled");
      expect(runCalls).toBe(0);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("init with remote performs bootstrap commit/pull/push and sets lastSync", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-init-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const calls: string[][] = [];

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        calls.push(command);
        if (command[0] === "git" && command[1] === "clone") {
          const cloneTarget = command[command.length - 1];
          if (cloneTarget) {
            await mkdir(cloneTarget, { recursive: true });
          }
        }
        if (command.includes("commit")) {
          return {
            stdout: "",
            stderr: "nothing to commit, working tree clean",
            exitCode: 1,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      const config = await engine.init("https://example.com/repo.git");

      expect(config.lastSync).not.toBeNull();
      expect(
        calls.some(
          (command) =>
            command[0] === "git" &&
            command.includes("pull") &&
            command.includes("--rebase"),
        ),
      ).toBe(true);
      expect(
        calls.some(
          (command) => command[0] === "git" && command.includes("push"),
        ),
      ).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("init with existing git repo updates remote in-place without reclone", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-init-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const calls: string[][] = [];

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        calls.push(command);
        if (command.includes("commit")) {
          return {
            stdout: "",
            stderr: "nothing to commit, working tree clean",
            exitCode: 1,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await mkdir(join(repoDir, ".git"), { recursive: true });
      await engine.init("https://example.com/repo.git");

      expect(
        calls.some((command) => command[0] === "git" && command[1] === "clone"),
      ).toBe(false);
      expect(
        calls.some(
          (command) =>
            command[0] === "git" &&
            command.includes("remote") &&
            command.includes("set-url"),
        ),
      ).toBe(true);
      expect(
        calls.some(
          (command) =>
            command[0] === "git" &&
            command.includes("fetch") &&
            command.includes("origin"),
        ),
      ).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("init restores plugins from manifest when remote content exists", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-init-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localClaudeDir = join(paths.home, ".claude");
    const calls: string[][] = [];

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        calls.push(command);
        if (command.includes("commit")) {
          return {
            stdout: "",
            stderr: "nothing to commit, working tree clean",
            exitCode: 1,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await rm(localClaudeDir, { recursive: true, force: true });
      await mkdir(join(repoDir, ".git"), { recursive: true });
      await mkdir(join(repoDir, "claude", "plugins"), { recursive: true });
      await writeFile(
        join(repoDir, "claude", "plugins", "plugin-manifest.json"),
        JSON.stringify(
          {
            version: 1,
            marketplaces: {
              demo: {
                source: "github",
                owner: "acme",
                repo: "demo-marketplace",
              },
            },
            plugins: [{ name: "demo-plugin", version: "1.0.0", scope: "user" }],
            enabledPlugins: ["demo-plugin"],
          },
          null,
          2,
        ),
        "utf8",
      );

      await engine.init("https://example.com/repo.git");

      await access(
        join(localClaudeDir, "plugins", "demo-plugin", ".claude-plugin"),
      );
      const settings = JSON.parse(
        await readFile(join(localClaudeDir, "settings.json"), "utf8"),
      ) as {
        enabledPlugins?: Record<string, unknown>;
      };
      expect(settings.enabledPlugins).toHaveProperty("demo-plugin");
      expect(
        calls.some(
          (command) =>
            command[0] === "git" &&
            command[1] === "clone" &&
            command.some((part) => part.includes("demo-marketplace.git")),
        ),
      ).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
      await rm(localClaudeDir, { recursive: true, force: true });
    }
  });
});
