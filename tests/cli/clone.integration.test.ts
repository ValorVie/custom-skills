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

import { createProgram } from "../../src/cli/index";
import {
  COPY_TARGETS,
  type ResourceType,
  type TargetType,
} from "../../src/utils/shared";

const RESOURCE_KEYS: (ResourceType | "plugins")[] = [
  "skills",
  "commands",
  "agents",
  "workflows",
  "plugins",
];

type TargetSnapshot = Record<string, string | undefined>;

function captureTargets(): TargetSnapshot {
  const snapshot: TargetSnapshot = {};
  for (const target of Object.keys(COPY_TARGETS) as TargetType[]) {
    for (const key of RESOURCE_KEYS) {
      snapshot[`${target}:${key}`] = COPY_TARGETS[target][key];
    }
  }
  return snapshot;
}

function restoreTargets(snapshot: TargetSnapshot): void {
  for (const target of Object.keys(COPY_TARGETS) as TargetType[]) {
    for (const key of RESOURCE_KEYS) {
      COPY_TARGETS[target][key] = snapshot[`${target}:${key}`];
    }
  }
}

function redirectTargets(root: string): void {
  for (const target of Object.keys(COPY_TARGETS) as TargetType[]) {
    for (const key of RESOURCE_KEYS) {
      if (!COPY_TARGETS[target][key]) {
        continue;
      }
      COPY_TARGETS[target][key] = join(root, "targets", target, key);
    }
  }
}

async function runClone(args: string[]): Promise<string> {
  const program = createProgram();
  const originalLog = console.log;
  const output: string[] = [];

  console.log = (...values: unknown[]) => {
    output.push(values.map((value) => String(value)).join(" "));
  };

  try {
    await program.parseAsync(["clone", ...args], {
      from: "user",
    });
  } finally {
    console.log = originalLog;
  }

  return output.join("\n");
}

describe("cli/clone integration", () => {
  test("clone --json distributes skills and reports metadata", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-clone-"));
    const cwd = join(root, "custom-skills");
    const snapshot = captureTargets();
    const previousCwd = process.cwd();

    try {
      await mkdir(join(cwd, "skills", "alpha"), { recursive: true });
      await mkdir(join(cwd, "commands"), { recursive: true });
      await mkdir(join(cwd, "agents"), { recursive: true });
      await writeFile(
        join(cwd, "skills", "alpha", "SKILL.md"),
        "alpha\n",
        "utf8",
      );
      await writeFile(
        join(cwd, "package.json"),
        JSON.stringify({ name: "ai-dev" }),
        "utf8",
      );

      redirectTargets(root);
      process.chdir(cwd);

      const output = await runClone(["--json"]);
      const parsed = JSON.parse(output);

      expect(parsed.devMode).toBe(true);
      expect(parsed.metadata.updated > 0).toBe(true);
      expect(
        parsed.distributed.some(
          (item: { target: string; type: string; name: string }) =>
            item.target === "claude" &&
            item.type === "skills" &&
            item.name === "alpha",
        ),
      ).toBe(true);

      await access(
        join(root, "targets", "claude", "skills", "alpha", "SKILL.md"),
      );
    } finally {
      process.chdir(previousCwd);
      restoreTargets(snapshot);
      await rm(root, { recursive: true, force: true });
    }
  });

  test("clone non-json prints updated item details", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-clone-"));
    const cwd = join(root, "custom-skills");
    const snapshot = captureTargets();
    const previousCwd = process.cwd();

    try {
      await mkdir(join(cwd, "skills", "alpha"), { recursive: true });
      await mkdir(join(cwd, "commands"), { recursive: true });
      await mkdir(join(cwd, "agents"), { recursive: true });
      await writeFile(
        join(cwd, "skills", "alpha", "SKILL.md"),
        "alpha\n",
        "utf8",
      );
      await writeFile(
        join(cwd, "package.json"),
        JSON.stringify({ name: "ai-dev" }),
        "utf8",
      );

      redirectTargets(root);
      process.chdir(cwd);

      const output = await runClone([]);

      expect(output).toContain("分發完成！共");
      expect(output).toContain("本次更新明細：");
      expect(output).toContain("claude/skills: alpha");
    } finally {
      process.chdir(previousCwd);
      restoreTargets(snapshot);
      await rm(root, { recursive: true, force: true });
    }
  });

  test("clone --skip-conflicts keeps existing content", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-clone-"));
    const cwd = join(root, "custom-skills");
    const snapshot = captureTargets();
    const previousCwd = process.cwd();
    const targetFile = join(
      root,
      "targets",
      "claude",
      "skills",
      "alpha",
      "SKILL.md",
    );

    try {
      await mkdir(join(cwd, "skills", "alpha"), { recursive: true });
      await mkdir(join(cwd, "commands"), { recursive: true });
      await mkdir(join(cwd, "agents"), { recursive: true });
      await writeFile(
        join(cwd, "skills", "alpha", "SKILL.md"),
        "new\n",
        "utf8",
      );
      await writeFile(
        join(cwd, "package.json"),
        JSON.stringify({ name: "ai-dev" }),
        "utf8",
      );
      redirectTargets(root);
      process.chdir(cwd);

      // First run establishes baseline manifest/hash.
      await runClone(["--json"]);

      // Simulate user modification after distribution.
      await writeFile(targetFile, "old\n", "utf8");

      const output = await runClone(["--json", "--skip-conflicts"]);
      const parsed = JSON.parse(output);

      expect(parsed.conflicts.length > 0).toBe(true);
      expect((await readFile(targetFile, "utf8")).trim()).toBe("old");
    } finally {
      process.chdir(previousCwd);
      restoreTargets(snapshot);
      await rm(root, { recursive: true, force: true });
    }
  });

  test("clone --force overwrites conflicts and exposes sync-project flag", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-clone-"));
    const cwd = join(root, "custom-skills");
    const snapshot = captureTargets();
    const previousCwd = process.cwd();
    const targetFile = join(
      root,
      "targets",
      "claude",
      "skills",
      "alpha",
      "SKILL.md",
    );

    try {
      await mkdir(join(cwd, "skills", "alpha"), { recursive: true });
      await mkdir(join(cwd, "commands"), { recursive: true });
      await mkdir(join(cwd, "agents"), { recursive: true });
      await writeFile(
        join(cwd, "skills", "alpha", "SKILL.md"),
        "new\n",
        "utf8",
      );
      await writeFile(
        join(cwd, "package.json"),
        JSON.stringify({ name: "ai-dev" }),
        "utf8",
      );
      await mkdir(join(root, "targets", "claude", "skills", "alpha"), {
        recursive: true,
      });
      await writeFile(targetFile, "old\n", "utf8");

      redirectTargets(root);
      process.chdir(cwd);

      const output = await runClone([
        "--json",
        "--force",
        "--backup",
        "--sync-project",
      ]);
      const parsed = JSON.parse(output);

      // With --force, conflicts are reported but overwritten
      expect(parsed.syncProject).toBe(true);
      expect((await readFile(targetFile, "utf8")).trim()).toBe("new");
    } finally {
      process.chdir(previousCwd);
      restoreTargets(snapshot);
      await rm(root, { recursive: true, force: true });
    }
  });
});
