import { describe, expect, test } from "bun:test";

import {
  commandExists,
  getBunVersion,
  getOS,
  runCommand,
} from "../../src/utils/system";

describe("utils/system", () => {
  test("getOS returns supported platform", () => {
    expect(["linux", "macos", "windows"]).toContain(getOS());
  });

  test("commandExists detects installed command", () => {
    expect(commandExists("git")).toBe(true);
    expect(commandExists("definitely-not-a-real-command")).toBe(false);
  });

  test("runCommand executes command and captures output", async () => {
    const result = await runCommand(["echo", "hello"]);
    expect(result.stdout).toContain("hello");
    expect(result.exitCode).toBe(0);
  });

  test("runCommand throws when command fails and check=true", async () => {
    const failingCommand =
      getOS() === "windows"
        ? ["cmd", "/c", "exit", "1"]
        : ["bash", "-lc", "exit 1"];

    await expect(runCommand(failingCommand, { check: true })).rejects.toThrow();
  });

  test("getBunVersion returns semver when bun exists", async () => {
    const version = await getBunVersion();
    if (commandExists("bun")) {
      expect(version).not.toBeNull();
      expect(version as string).toMatch(/^\d+\.\d+\.\d+/);
      return;
    }
    expect(version).toBeNull();
  });
});
