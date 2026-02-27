import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { setLocale, t } from "../../src/utils/i18n";

function runCli(args: string[], home: string) {
  const result = Bun.spawnSync(["bun", "run", "src/cli.ts", ...args], {
    cwd: process.cwd(),
    env: { ...process.env, HOME: home, BUN_TMPDIR: "/tmp" },
    stdout: "pipe",
    stderr: "pipe",
    timeout: 20_000,
  });

  return {
    exitCode: result.exitCode,
    stdout: Buffer.from(result.stdout).toString("utf8"),
    stderr: Buffer.from(result.stderr).toString("utf8"),
  };
}

describe("cli mem output parity", () => {
  test("pull done message uses dynamic import method label", () => {
    setLocale("zh-TW");

    const rendered = t("mem.pull_done", {
      method: "API",
      si: "1",
      oi: "2",
      smi: "3",
      pi: "4",
      ss: "5",
      os: "6",
      sms: "7",
      ps: "8",
    });

    expect(rendered).toContain("(API)");
    expect(rendered).toContain("imported: 1s 2o 3sm 4p");
  });

  test("mem push unregistered output includes register hint", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-mem-output-parity-"));

    try {
      const result = runCli(["mem", "push"], home);
      expect(result.exitCode).not.toBe(0);
      expect(result.stderr).toContain("請先執行");
      expect(result.stderr).toContain("ai-dev mem register");
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });
});
