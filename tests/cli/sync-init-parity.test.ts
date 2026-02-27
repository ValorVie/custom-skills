import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

function runCli(args: string[], home: string) {
  const result = Bun.spawnSync(["bun", "run", "src/cli.ts", ...args], {
    cwd: process.cwd(),
    env: { ...process.env, HOME: home },
    stdout: "pipe",
    stderr: "pipe",
    timeout: 15000,
  });

  return {
    exitCode: result.exitCode,
    stdout: Buffer.from(result.stdout).toString("utf8"),
    stderr: Buffer.from(result.stderr).toString("utf8"),
  };
}

describe("cli sync init parity", () => {
  test("sync init requires --remote option", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-sync-init-parity-"));

    try {
      const result = runCli(["sync", "init"], home);
      expect(result.exitCode).not.toBe(0);
      expect(result.stderr).toContain("--remote");
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });
});
