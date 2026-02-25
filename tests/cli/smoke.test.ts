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

  test("status --json", () => {
    const result = runCli(["status", "--json"]);
    expect(result.exitCode).toBe(0);
    const parsed = JSON.parse(result.stdout);
    expect(parsed).toHaveProperty("git");
    expect(parsed).toHaveProperty("repos");
  });

  test("install --help", () => {
    const result = runCli(["install", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("install");
  });

  test("update --help", () => {
    const result = runCli(["update", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("update");
  });

  test("clone --help", () => {
    const result = runCli(["clone", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("clone");
  });

  test("list --json", () => {
    const result = runCli(["list", "--json"]);
    expect(result.exitCode).toBe(0);
    const parsed = JSON.parse(result.stdout);
    expect(Array.isArray(parsed)).toBe(true);
  });

  test("list --target claude --type skills --json", () => {
    const result = runCli(
      ["list", "--target", "claude", "--type", "skills", "--json"],
      10000,
    );
    expect(result.exitCode).toBe(0);
    const parsed = JSON.parse(result.stdout);
    expect(Array.isArray(parsed)).toBe(true);
  });

  test("toggle --help", () => {
    const result = runCli(["toggle", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("toggle");
  });

  test("add-repo --help", () => {
    const result = runCli(["add-repo", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("add-repo");
  });

  test("add-custom-repo --help", () => {
    const result = runCli(["add-custom-repo", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("add-custom-repo");
  });

  test("update-custom-repo --help", () => {
    const result = runCli(["update-custom-repo", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("update-custom-repo");
  });

  test("test --help", () => {
    const result = runCli(["test", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("test");
  });

  test("coverage --help", () => {
    const result = runCli(["coverage", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("coverage");
  });

  test("derive-tests --help", () => {
    const result = runCli(["derive-tests", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("derive-tests");
  });

  test("project --help", () => {
    const result = runCli(["project", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("project");
  });

  test("project init --help", () => {
    const result = runCli(["project", "init", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("init");
  });

  test("standards --help", () => {
    const result = runCli(["standards", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("standards");
  });

  test("standards status", () => {
    const result = runCli(["standards", "status"]);
    expect(result.exitCode).toBe(0);
  });

  test("standards list", () => {
    const result = runCli(["standards", "list"]);
    expect(result.exitCode).toBe(0);
  });

  test("hooks --help", () => {
    const result = runCli(["hooks", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("hooks");
  });

  test("sync --help", () => {
    const result = runCli(["sync", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("sync");
  });

  test("sync status", () => {
    const result = runCli(["sync", "status"]);
    expect(result.exitCode).toBe(0);
  });

  test("mem --help", () => {
    const result = runCli(["mem", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("mem");
  });

  test("mem status", () => {
    const result = runCli(["mem", "status"]);
    expect(result.exitCode).toBe(0);
  });

  test("tui --help", () => {
    const result = runCli(["tui", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("tui");
  });
});
