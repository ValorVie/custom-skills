import { describe, expect, test } from "bun:test";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

import pkg from "../../package.json";

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

describe("cli version parity", () => {
  test("--version matches package.json", () => {
    const result = runCli(["--version"]);
    expect(result.exitCode).toBe(0);
    expect(result.stdout.trim()).toBe(pkg.version);
  });

  test("createProgram version is sourced from package.json", async () => {
    const source = await readFile(join(process.cwd(), "src/cli/index.ts"), "utf8");
    expect(source).toContain("package.json");
  });
});
