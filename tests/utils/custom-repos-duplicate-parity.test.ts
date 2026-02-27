import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

function runCli(args: string[], home: string, timeoutMs = 10000) {
  const result = Bun.spawnSync(["bun", "run", "src/cli.ts", ...args], {
    cwd: process.cwd(),
    env: { ...process.env, HOME: home },
    stdout: "pipe",
    stderr: "pipe",
    timeout: timeoutMs,
  });

  return {
    exitCode: result.exitCode,
    stdout: Buffer.from(result.stdout).toString("utf8"),
    stderr: Buffer.from(result.stderr).toString("utf8"),
  };
}

describe("utils custom repos duplicate parity", () => {
  test("add-custom-repo rejects duplicate name", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-custom-repo-dup-name-"));

    try {
      const first = runCli(
        ["add-custom-repo", "owner/repo-a", "--name", "demo", "--no-clone"],
        home,
      );
      expect(first.exitCode).toBe(0);

      const second = runCli(
        ["add-custom-repo", "owner/repo-b", "--name", "demo", "--no-clone"],
        home,
      );
      expect(second.exitCode).toBe(1);
      expect(second.stdout.toLowerCase()).toContain("already");
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });

  test("add-custom-repo rejects duplicate repository across URL formats", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-custom-repo-dup-url-"));

    try {
      const first = runCli(
        ["add-custom-repo", "owner/repo-c", "--name", "demo-a", "--no-clone"],
        home,
      );
      expect(first.exitCode).toBe(0);

      const second = runCli(
        [
          "add-custom-repo",
          "https://github.com/owner/repo-c.git",
          "--name",
          "demo-b",
          "--no-clone",
        ],
        home,
      );
      expect(second.exitCode).toBe(1);
      expect(second.stdout.toLowerCase()).toContain("already");
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });
});
