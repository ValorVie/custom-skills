import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { checkEnvironment } from "../../src/core/status-checker";
import { NPM_PACKAGES, REPOS } from "../../src/utils/shared";

describe("core/status-checker", () => {
  test("checkEnvironment returns complete status payload", async () => {
    const status = await checkEnvironment();

    expect(status).toHaveProperty("git");
    expect(status).toHaveProperty("node");
    expect(status).toHaveProperty("bun");
    expect(status).toHaveProperty("gh");
    expect(Array.isArray(status.npmPackages)).toBe(true);
    expect(Array.isArray(status.repos)).toBe(true);
  });

  test("checkEnvironment includes configured packages and repositories", async () => {
    const status = await checkEnvironment();

    expect(status.npmPackages.length).toBe(NPM_PACKAGES.length);
    expect(status.repos.length).toBe(REPOS.length);
    expect(
      status.npmPackages.some(
        (pkg) => pkg.name === "@fission-ai/openspec@latest",
      ),
    ).toBe(true);
  });

  test("checkEnvironment reports repo remote comparison and upstream sync", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-status-checker-"));

    try {
      const sourcesPath = join(root, "upstream", "sources.yaml");
      const lastSyncPath = join(root, "upstream", "last-sync.yaml");
      await mkdir(join(root, "upstream"), { recursive: true });
      await writeFile(
        sourcesPath,
        [
          "sources:",
          "  sample:",
          "    repo: org/sample",
          "    branch: main",
          "    local_path: /tmp/sample",
          "    format: uds",
          "    install_method: standards",
          "",
        ].join("\n"),
        "utf8",
      );
      await writeFile(
        lastSyncPath,
        [
          "sample:",
          "  commit: abc123",
          "  synced_at: '2026-02-08T20:10:00.000000'",
          "",
        ].join("\n"),
        "utf8",
      );

      const status = await checkEnvironment({
        deps: {
          npmPackages: ["pkg-a"],
          repos: [
            {
              name: "repo-a",
              url: "https://example.com/repo-a.git",
              dir: "/tmp/repo-a",
            },
          ],
          commandExistsFn: () => true,
          resolveCommandPathFn: async () => "/usr/bin/fake",
          resolveVersionFn: async () => "1.0.0",
          accessFn: async (path) => {
            const text = String(path);
            if (text === "/tmp/repo-a" || text === "/tmp/repo-a/.git") {
              return;
            }
            if (text === "/tmp/sample" || text === "/tmp/sample/.git") {
              return;
            }
            throw new Error("missing");
          },
          runCommandFn: async (command: string[]) => {
            if (command.includes("fetch")) {
              return { stdout: "", stderr: "", exitCode: 0 };
            }
            if (command.includes("HEAD...@{upstream}")) {
              return { stdout: "0 3\n", stderr: "", exitCode: 0 };
            }
            if (command.includes("HEAD...origin/main")) {
              return { stdout: "0 3\n", stderr: "", exitCode: 0 };
            }
            if (command.includes("rev-parse")) {
              return { stdout: "main\n", stderr: "", exitCode: 0 };
            }
            if (command.includes("--contains")) {
              return { stdout: "abcdef\n", stderr: "", exitCode: 0 };
            }
            if (command.includes("abc123..HEAD")) {
              return { stdout: "1\n", stderr: "", exitCode: 0 };
            }
            if (
              command[0] === "npm" &&
              command[1] === "list" &&
              command[3] === "pkg-a"
            ) {
              return {
                stdout: JSON.stringify({
                  dependencies: { "pkg-a": { version: "1.2.3" } },
                }),
                stderr: "",
                exitCode: 0,
              };
            }
            return { stdout: "", stderr: "", exitCode: 0 };
          },
          upstreamSourcesPath: sourcesPath,
          upstreamLastSyncPath: lastSyncPath,
        },
      });

      expect(status.repos[0]?.behind).toBe(3);
      expect(status.repos[0]?.syncState).toBe("updates-available");
      expect(status.upstreamSync[0]?.status).toBe("behind");
      expect(status.upstreamSync[0]?.behind).toBe(1);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});
