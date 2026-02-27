import { describe, expect, test } from "bun:test";
import { access, mkdir, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import YAML from "yaml";

const TOGGLE_CLI_SCRIPT = `
import { Command } from "commander";
import { registerToggleCommand } from "./src/cli/toggle";

const program = new Command().name("ai-dev");
registerToggleCommand(program);
await program.parseAsync(["bun", "ai-dev", ...process.argv.slice(1)]);
`;

type ToggleConfigFile = {
  [target: string]: {
    [type: string]: {
      enabled?: boolean;
      disabled?: string[];
    };
  };
};

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

async function readToggleConfig(home: string): Promise<ToggleConfigFile> {
  const configPath = join(home, ".config", "custom-skills", "toggle-config.yaml");
  const content = await readFile(configPath, "utf8");
  const parsed = YAML.parse(content) as ToggleConfigFile | null;
  return parsed ?? {};
}

describe("core toggle-config compatibility", () => {
  test("single disable/enable updates disabled list in toggle-config", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-toggle-config-single-"));
    const skillDir = join(home, ".claude", "skills", "alpha");

    try {
      await mkdir(skillDir, { recursive: true });

      const disabled = runCli(
        [
          "toggle",
          "--target",
          "claude",
          "--type",
          "skills",
          "--name",
          "alpha",
          "--disable",
        ],
        home,
      );
      expect(disabled.exitCode).toBe(0);
      await access(join(home, ".claude", "skills", "alpha.disabled"));

      const afterDisable = await readToggleConfig(home);
      expect(afterDisable.claude?.skills?.disabled ?? []).toContain("alpha");

      const enabled = runCli(
        [
          "toggle",
          "--target",
          "claude",
          "--type",
          "skills",
          "--name",
          "alpha",
          "--enable",
        ],
        home,
      );
      expect(enabled.exitCode).toBe(0);
      await access(join(home, ".claude", "skills", "alpha"));

      const afterEnable = await readToggleConfig(home);
      expect(afterEnable.claude?.skills?.disabled ?? []).not.toContain("alpha");
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });

  test("--all disable/enable updates overall enabled flag in toggle-config", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-toggle-config-all-"));

    try {
      await mkdir(join(home, ".claude", "skills", "alpha"), { recursive: true });
      await mkdir(join(home, ".claude", "skills", "beta"), { recursive: true });

      const disableAll = runCli(
        [
          "toggle",
          "--target",
          "claude",
          "--type",
          "skills",
          "--all",
          "--disable",
        ],
        home,
      );
      expect(disableAll.exitCode).toBe(0);

      const afterDisableAll = await readToggleConfig(home);
      expect(afterDisableAll.claude?.skills?.enabled).toBe(false);

      const enableAll = runCli(
        [
          "toggle",
          "--target",
          "claude",
          "--type",
          "skills",
          "--all",
          "--enable",
        ],
        home,
      );
      expect(enableAll.exitCode).toBe(0);

      const afterEnableAll = await readToggleConfig(home);
      expect(afterEnableAll.claude?.skills?.enabled).toBe(true);
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });
});
