import { describe, expect, test } from "bun:test";

function runCli(args: string[], timeoutMs = 5000) {
  const result = Bun.spawnSync(["bun", "run", "src/cli.ts", ...args], {
    cwd: process.cwd(),
    env: process.env,
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

describe("cli list validation parity", () => {
  test("list rejects unknown target", () => {
    const result = runCli(["list", "--target", "unknown-target", "--json"]);
    expect(result.exitCode).toBe(1);
    expect(result.stdout).toContain("無效的目標");
  });

  test("list rejects unknown type", () => {
    const result = runCli(["list", "--type", "unknown-type", "--json"]);
    expect(result.exitCode).toBe(1);
    expect(result.stdout).toContain("無效的類型");
  });

  test("list rejects invalid target/type combination", () => {
    const result = runCli(["list", "--target", "codex", "--type", "agents"]);
    expect(result.exitCode).toBe(1);
    expect(result.stdout).toContain("無效的 target/type 組合");
  });
});
