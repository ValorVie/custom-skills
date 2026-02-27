import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const LOAD_CUSTOM_REPOS_SCRIPT = `
import { loadCustomRepos } from "./src/utils/custom-repos";

const config = await loadCustomRepos();
console.log(JSON.stringify(config));
`;

function runLoadCustomRepos(home: string): {
  exitCode: number;
  stdout: string;
  stderr: string;
} {
  const result = Bun.spawnSync(["bun", "-e", LOAD_CUSTOM_REPOS_SCRIPT], {
    cwd: process.cwd(),
    env: { ...process.env, HOME: home },
    stdout: "pipe",
    stderr: "pipe",
    timeout: 15_000,
  });

  return {
    exitCode: result.exitCode,
    stdout: Buffer.from(result.stdout).toString("utf8"),
    stderr: Buffer.from(result.stderr).toString("utf8"),
  };
}

type CustomReposConfig = {
  repos: Record<
    string,
    {
      url: string;
      branch: string;
      localPath: string;
      addedAt: string;
    }
  >;
};

describe("utils/custom-repos compatibility", () => {
  test("loadCustomRepos maps v1 snake_case fields and expands ~/ paths", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-custom-repos-v1-"));

    try {
      await mkdir(join(home, ".config", "ai-dev"), { recursive: true });
      await writeFile(
        join(home, ".config", "ai-dev", "repos.yaml"),
        [
          "repos:",
          "  legacy-repo:",
          "    url: https://example.com/legacy.git",
          "    branch: main",
          "    local_path: ~/.config/legacy-repo",
          "    added_at: '2026-02-08T00:00:00.000Z'",
          "",
        ].join("\n"),
        "utf8",
      );

      const result = runLoadCustomRepos(home);
      expect(result.exitCode).toBe(0);

      const parsed = JSON.parse(result.stdout) as CustomReposConfig;
      expect(parsed.repos["legacy-repo"]?.localPath).toBe(
        join(home, ".config", "legacy-repo"),
      );
      expect(parsed.repos["legacy-repo"]?.addedAt).toBe(
        "2026-02-08T00:00:00.000Z",
      );
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });

  test("loadCustomRepos keeps camelCase fields compatible", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-custom-repos-v2-"));
    const localPath = join(home, ".config", "camel-repo");
    const addedAt = "2026-02-09T00:00:00.000Z";

    try {
      await mkdir(join(home, ".config", "ai-dev"), { recursive: true });
      await writeFile(
        join(home, ".config", "ai-dev", "repos.yaml"),
        [
          "repos:",
          "  camel-repo:",
          "    url: https://example.com/camel.git",
          "    branch: develop",
          `    localPath: ${localPath}`,
          `    addedAt: '${addedAt}'`,
          "",
        ].join("\n"),
        "utf8",
      );

      const result = runLoadCustomRepos(home);
      expect(result.exitCode).toBe(0);

      const parsed = JSON.parse(result.stdout) as CustomReposConfig;
      expect(parsed.repos["camel-repo"]?.localPath).toBe(localPath);
      expect(parsed.repos["camel-repo"]?.addedAt).toBe(addedAt);
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });
});
