import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const TOGGLE_CLI_SCRIPT = `
import { Command } from "commander";
import { registerToggleCommand } from "./src/cli/toggle";

const program = new Command().name("ai-dev");
registerToggleCommand(program);
await program.parseAsync(["bun", "ai-dev", ...process.argv.slice(1)]);
`;

function runCli(args: string[], home: string) {
  const result = Bun.spawnSync(["bun", "-e", TOGGLE_CLI_SCRIPT, ...args], {
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

describe("cli toggle --list parity", () => {
  test("toggle --list includes v1 summary columns", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-toggle-list-parity-"));

    try {
      const result = runCli(["toggle", "--list"], home);
      expect(result.exitCode).toBe(0);
      expect(result.stdout).toContain("目標");
      expect(result.stdout).toContain("類型");
      expect(result.stdout).toContain("整體啟用");
      expect(result.stdout).toContain("停用項目");
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });
});
