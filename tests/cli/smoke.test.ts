import { describe, expect, test } from "bun:test";

function runCli(args: string[]) {
  const result = Bun.spawnSync(["bun", "run", "src/cli.ts", ...args], {
    cwd: process.cwd(),
    env: process.env,
    stdout: "pipe",
    stderr: "pipe",
  });

  return {
    exitCode: result.exitCode,
    stdout: Buffer.from(result.stdout).toString("utf8"),
    stderr: Buffer.from(result.stderr).toString("utf8"),
  };
}

describe("cli smoke", () => {
  test("--version outputs 2.0.0", () => {
    const result = runCli(["--version"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout.trim()).toBe("2.0.0");
  });

  test("--help shows top-level commands", () => {
    const result = runCli(["--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("install");
    expect(result.stdout).toContain("status");
    expect(result.stdout).toContain("tui");
  });

  test("status command runs", () => {
    const result = runCli(["status", "--json"]);
    expect(result.exitCode).toBe(0);
    const parsed = JSON.parse(result.stdout);
    expect(parsed).toHaveProperty("git");
    expect(parsed).toHaveProperty("repos");
  });
});
