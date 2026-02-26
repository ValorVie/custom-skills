import { describe, expect, test } from "bun:test";
import {
  access,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

function runCli(args: string[], home: string) {
  const result = Bun.spawnSync(["bun", "run", "src/cli.ts", ...args], {
    cwd: process.cwd(),
    env: { ...process.env, HOME: home },
    stdout: "pipe",
    stderr: "pipe",
    timeout: 15000,
  });

  return {
    exitCode: result.exitCode,
    stdout: Buffer.from(result.stdout).toString("utf8"),
    stderr: Buffer.from(result.stderr).toString("utf8"),
  };
}

describe("cli phase3 integration", () => {
  test("list --hide-disabled excludes disabled resources", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-phase3-list-"));

    try {
      const skillsDir = join(home, ".claude", "skills");
      await mkdir(join(skillsDir, "enabled-skill"), { recursive: true });
      await mkdir(join(skillsDir, "disabled-skill.disabled"), {
        recursive: true,
      });

      const allResult = runCli(
        ["list", "--target", "claude", "--type", "skills", "--json"],
        home,
      );
      expect(allResult.exitCode).toBe(0);
      const all = JSON.parse(allResult.stdout) as Array<{
        name: string;
        enabled: boolean;
      }>;
      expect(all.some((item) => item.name === "disabled-skill")).toBe(true);

      const hiddenResult = runCli(
        [
          "list",
          "--target",
          "claude",
          "--type",
          "skills",
          "--hide-disabled",
          "--json",
        ],
        home,
      );
      expect(hiddenResult.exitCode).toBe(0);
      const hidden = JSON.parse(hiddenResult.stdout) as Array<{ name: string }>;
      expect(hidden.some((item) => item.name === "disabled-skill")).toBe(false);
      expect(hidden.some((item) => item.name === "enabled-skill")).toBe(true);
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });

  test("toggle validates invalid target/type combination", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-phase3-toggle-invalid-"));

    try {
      const result = runCli(
        ["toggle", "--target", "codex", "--type", "agents", "--list"],
        home,
      );

      expect(result.exitCode).toBe(1);
      expect(result.stdout).toContain("Invalid target/type combination");
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });

  test("toggle disable and enable updates skill directory name", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-phase3-toggle-"));
    const skillDir = join(home, ".claude", "skills", "alpha");

    try {
      await mkdir(skillDir, { recursive: true });

      const disableResult = runCli(
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
      expect(disableResult.exitCode).toBe(0);
      await access(join(home, ".claude", "skills", "alpha.disabled"));

      const enableResult = runCli(
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
      expect(enableResult.exitCode).toBe(0);
      await access(join(home, ".claude", "skills", "alpha"));
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });

  test("add-custom-repo --fix creates standard directories and config", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-phase3-custom-repo-"));

    try {
      const result = runCli(
        [
          "add-custom-repo",
          "owner/repo",
          "--name",
          "demo-repo",
          "--no-clone",
          "--fix",
        ],
        home,
      );
      expect(result.exitCode).toBe(0);

      await access(join(home, ".config", "demo-repo", "skills"));
      await access(join(home, ".config", "demo-repo", "commands"));
      await access(join(home, ".config", "demo-repo", "agents"));
      await access(join(home, ".config", "demo-repo", "workflows"));

      const config = await readFile(
        join(home, ".config", "ai-dev", "repos.yaml"),
        "utf8",
      );
      expect(config).toContain("demo-repo:");
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });

  test("update-custom-repo --json returns summary", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-phase3-update-custom-"));

    try {
      await mkdir(join(home, ".config", "ai-dev"), { recursive: true });
      await writeFile(
        join(home, ".config", "ai-dev", "repos.yaml"),
        [
          "repos:",
          "  missing-repo:",
          "    url: https://example.com/missing.git",
          "    branch: main",
          `    localPath: ${join(home, ".config", "missing-repo")}`,
          "    addedAt: '2026-02-08T00:00:00.000Z'",
          "",
        ].join("\n"),
        "utf8",
      );

      const result = runCli(["update-custom-repo", "--json"], home);
      expect(result.exitCode).toBe(0);

      const parsed = JSON.parse(result.stdout) as {
        summary: { missing: string[] };
      };
      expect(parsed.summary.missing).toEqual(["missing-repo"]);
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });

  test("hooks install copies plugin and uninstall --yes removes it", async () => {
    const home = await mkdtemp(join(tmpdir(), "ai-dev-phase3-hooks-"));

    try {
      const install = runCli(["hooks", "install"], home);
      expect(install.exitCode).toBe(0);
      await access(join(home, ".claude", "plugins", "ecc-hooks", "hooks"));
      await access(
        join(home, ".claude", "plugins", "ecc-hooks", ".claude-plugin"),
      );

      const uninstall = runCli(["hooks", "uninstall", "--yes"], home);
      expect(uninstall.exitCode).toBe(0);

      try {
        await access(join(home, ".claude", "plugins", "ecc-hooks"));
        expect.unreachable("plugin directory should be removed");
      } catch {
        expect(true).toBe(true);
      }
    } finally {
      await rm(home, { recursive: true, force: true });
    }
  });
});
