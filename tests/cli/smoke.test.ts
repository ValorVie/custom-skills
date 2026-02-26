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
  test("--version outputs version from package.json", () => {
    const pkg = require("../../package.json") as { version: string };
    const result = runCli(["--version"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout.trim()).toBe(pkg.version);
  });

  test("--help shows zh-TW descriptions by default", () => {
    const result = runCli(["--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("install");
    expect(result.stdout).toContain("status");
    expect(result.stdout).toContain("tui");
    expect(result.stdout).toContain("首次安裝 AI 開發環境");
    expect(result.stdout).toContain("更新工具與拉取儲存庫");
    expect(result.stdout).toContain("分發 Skills 到各工具目錄");
  });

  test("--help shows global --lang option", () => {
    const result = runCli(["--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("--lang");
  });

  test("--lang can be passed globally", () => {
    const result = runCli(["--lang", "zh-TW", "status", "--json"]);
    expect(result.exitCode).toBe(0);
    const parsed = JSON.parse(result.stdout);
    expect(parsed).toHaveProperty("git");
  });

  test("status --json", () => {
    const result = runCli(["status", "--json"]);
    expect(result.exitCode).toBe(0);
    const parsed = JSON.parse(result.stdout);
    expect(parsed).toHaveProperty("git");
    expect(parsed).toHaveProperty("repos");
  });

  test("status shows grouped Chinese tables", () => {
    const result = runCli(["status"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("AI 開發環境狀態檢查");
    expect(result.stdout).toContain("核心工具");
    expect(result.stdout).toContain("全域 NPM 套件");
    expect(result.stdout).toContain("設定儲存庫");
  });

  test("install --help", () => {
    const result = runCli(["install", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("install");
    expect(result.stdout).toContain("--skip-skills");
    expect(result.stdout).toContain("--sync-project");
  });

  test("update --help", () => {
    const result = runCli(["update", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("update");
    expect(result.stdout).toContain("--skip-plugins");
  });

  test("clone --help", () => {
    const result = runCli(["clone", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("clone");
    expect(result.stdout).toContain("--force");
    expect(result.stdout).toContain("--skip-conflicts");
    expect(result.stdout).toContain("--sync-project");
  });

  test("list --json", () => {
    const result = runCli(["list", "--json"]);
    expect(result.exitCode).toBe(0);
    const parsed = JSON.parse(result.stdout);
    expect(Array.isArray(parsed)).toBe(true);
  });

  test("list --help", () => {
    const result = runCli(["list", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("--hide-disabled");
  });

  test("list groups by target and type with Chinese columns", () => {
    const result = runCli(["list", "--target", "claude", "--type", "skills"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("Claude Code - Skills");
    expect(result.stdout).toContain("名稱");
    expect(result.stdout).toContain("來源");
    expect(result.stdout).toContain("狀態");
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
    expect(result.stdout).toContain("--list");
  });

  test("add-repo --help", () => {
    const result = runCli(["add-repo", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("add-repo");
    expect(result.stdout).toContain("--analyze");
  });

  test("add-custom-repo --help", () => {
    const result = runCli(["add-custom-repo", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("add-custom-repo");
    expect(result.stdout).toContain("--fix");
  });

  test("update-custom-repo --help", () => {
    const result = runCli(["update-custom-repo", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("update-custom-repo");
    expect(result.stdout).toContain("--json");
  });

  test("test --help", () => {
    const result = runCli(["test", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("test");
    expect(result.stdout).toContain("--framework");
    expect(result.stdout).toContain("--source");
  });

  test("coverage --help", () => {
    const result = runCli(["coverage", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("coverage");
    expect(result.stdout).toContain("--framework");
    expect(result.stdout).toContain("--source");
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
    expect(result.stdout).toContain("--json");
  });

  test("project update --help", () => {
    const result = runCli(["project", "update", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("--only");
    expect(result.stdout).toContain("--json");
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

  test("standards overlaps", () => {
    const result = runCli(["standards", "overlaps"]);
    expect(result.exitCode).toBe(0);
  });

  test("standards sync --help", () => {
    const result = runCli(["standards", "sync", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("sync");
    expect(result.stdout).toContain("--json");
  });

  test("hooks --help", () => {
    const result = runCli(["hooks", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("hooks");
  });

  test("hooks uninstall --help", () => {
    const result = runCli(["hooks", "uninstall", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("--yes");
  });

  test("sync --help", () => {
    const result = runCli(["sync", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("sync");
  });

  test("sync status", () => {
    const result = runCli(["sync", "status"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("項目");
    expect(result.stdout).toContain("值");
  });

  test("sync push --help", () => {
    const result = runCli(["sync", "push", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("--force");
  });

  test("sync pull --help", () => {
    const result = runCli(["sync", "pull", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("--force");
    expect(result.stdout).toContain("--no-delete");
  });

  test("mem --help", () => {
    const result = runCli(["mem", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("mem");
  });

  test("mem status", () => {
    const result = runCli(["mem", "status"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("項目");
    expect(result.stdout).toContain("值");
  });

  test("mem auto --help", () => {
    const result = runCli(["mem", "auto", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("--enable");
    expect(result.stdout).toContain("--disable");
  });

  test("tui --help", () => {
    const result = runCli(["tui", "--help"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("tui");
  });
});
