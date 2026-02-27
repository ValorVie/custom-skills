import { describe, expect, test } from "bun:test";
import { Command } from "commander";

import { registerAddCustomRepoCommand } from "../../src/cli/add-custom-repo";
import { registerCloneCommand } from "../../src/cli/clone";
import { registerStandardsCommands } from "../../src/cli/standards";

async function runHelp(
  register: (program: Command) => void,
  args: string[],
): Promise<{ exitCode: number; stdout: string; stderr: string }> {
  const output: string[] = [];
  const errors: string[] = [];
  const program = new Command();
  program.exitOverride();
  program.configureOutput({
    writeOut: (str) => output.push(str),
    writeErr: (str) => errors.push(str),
  });
  register(program);

  try {
    await program.parseAsync(args, { from: "user" });
    return { exitCode: 0, stdout: output.join(""), stderr: errors.join("") };
  } catch (error) {
    if (
      error &&
      typeof error === "object" &&
      "code" in error &&
      error.code === "commander.helpDisplayed"
    ) {
      return { exitCode: 0, stdout: output.join(""), stderr: errors.join("") };
    }
    return {
      exitCode: 1,
      stdout: output.join(""),
      stderr:
        errors.join("") + (error instanceof Error ? error.message : String(error)),
    };
  }
}

function runCloneHelp() {
  return runHelp(registerCloneCommand, ["clone", "--help"]);
}

function runAddCustomRepoHelp() {
  return runHelp(registerAddCustomRepoCommand, ["add-custom-repo", "--help"]);
}

function runStandardsSyncHelp() {
  return runHelp(registerStandardsCommands, ["standards", "sync", "--help"]);
}

describe("cli help short options parity", () => {
  test("clone --help shows -f/-s/-b aliases", async () => {
    const result = await runCloneHelp();
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("-f, --force");
    expect(result.stdout).toContain("-s, --skip-conflicts");
    expect(result.stdout).toContain("-b, --backup");
  });

  test("add-custom-repo --help shows -n/-b aliases", async () => {
    const result = await runAddCustomRepoHelp();
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("-n, --name <name>");
    expect(result.stdout).toContain("-b, --branch <branch>");
  });

  test("standards sync --help shows -n/-t aliases", async () => {
    const result = await runStandardsSyncHelp();
    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("-n, --dry-run");
    expect(result.stdout).toContain(
      "-t, --target <claude|opencode|codex|gemini|antigravity>",
    );
  });
});
