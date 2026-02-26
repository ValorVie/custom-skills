import { afterEach, beforeEach, describe, expect, test } from "bun:test";
import {
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  writeFile,
} from "node:fs/promises";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";

import {
  type ConflictAction,
  distributeSkills,
} from "../../src/core/skill-distributor";
import { readManifest } from "../../src/utils/manifest";
import { COPY_TARGETS, type CopyTarget } from "../../src/utils/shared";

const MANIFEST_PATH = join(
  homedir(),
  ".config",
  "ai-dev",
  "manifests",
  "claude.yaml",
);

describe("core/skill-distributor", () => {
  let root: string;
  let sourceRoot: string;
  let targetSkills: string;
  let targetCommands: string;
  let targetAgents: string;
  let targetWorkflows: string;
  let savedTarget: CopyTarget;

  beforeEach(async () => {
    root = await mkdtemp(join(tmpdir(), "ai-dev-distribute-"));
    sourceRoot = join(root, "source");
    targetSkills = join(root, "targets", "claude", "skills");
    targetCommands = join(root, "targets", "claude", "commands");
    targetAgents = join(root, "targets", "claude", "agents");
    targetWorkflows = join(root, "targets", "claude", "workflows");

    // Save original target config
    savedTarget = { ...COPY_TARGETS.claude };

    // Override ALL paths to temp directories
    COPY_TARGETS.claude = {
      skills: targetSkills,
      commands: targetCommands,
      agents: targetAgents,
      workflows: targetWorkflows,
    };

    // Remove any existing manifest for claude
    await rm(MANIFEST_PATH, { force: true });
  });

  afterEach(async () => {
    // Restore original target config
    Object.assign(COPY_TARGETS.claude, savedTarget);

    // Clean up temp dir and test manifest
    await rm(root, { recursive: true, force: true });
    await rm(MANIFEST_PATH, { force: true });
  });

  test("distributeSkills copies skills to target and writes manifest", async () => {
    await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "alpha\n",
      "utf8",
    );

    const result = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
    });

    expect(result.errors.length).toBe(0);
    expect(result.conflicts.length).toBe(0);
    expect(result.orphansRemoved).toBe(0);
    expect(
      result.distributed.some(
        (item) =>
          item.target === "claude" &&
          item.type === "skills" &&
          item.name === "alpha",
      ),
    ).toBe(true);

    const copied = await readFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "utf8",
    );
    expect(copied.trim()).toBe("alpha");

    // Verify manifest was written
    const manifest = await readManifest("claude");
    expect(manifest).not.toBeNull();
    expect(manifest?.files.skills.alpha).toBeDefined();
    expect(manifest?.files.skills.alpha.hash).toMatch(/^sha256:/);
  });

  test("first-time distribution has no conflicts even with existing destination", async () => {
    await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "new\n",
      "utf8",
    );
    // Pre-existing destination with different content
    await mkdir(join(targetSkills, "alpha"), { recursive: true });
    await writeFile(join(targetSkills, "alpha", "SKILL.md"), "old\n", "utf8");

    const result = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
    });

    // First-time distribution: no manifest = no conflicts
    expect(result.conflicts.length).toBe(0);
    expect(result.distributed.length).toBe(1);

    const current = await readFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "utf8",
    );
    expect(current.trim()).toBe("new");
  });

  test("reports conflict when user modifies destination after distribution", async () => {
    await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "original\n",
      "utf8",
    );

    // First distribution
    const first = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
    });
    expect(first.errors.length).toBe(0);
    expect(first.distributed.length).toBe(1);

    // Simulate user modifying the destination
    await writeFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "user-modified\n",
      "utf8",
    );

    // Second distribution - should detect conflict
    const second = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
    });

    expect(second.conflicts.length).toBe(1);
    expect(second.conflicts[0]?.name).toBe("alpha");

    // Destination should NOT be overwritten
    const current = await readFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "utf8",
    );
    expect(current.trim()).toBe("user-modified");
  });

  test("source update without destination change is NOT a conflict", async () => {
    await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "v1\n",
      "utf8",
    );

    // First distribution
    await distributeSkills({ sourceRoot, targets: ["claude"] });

    // Update source (not destination)
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "v2\n",
      "utf8",
    );

    // Second distribution - destination unchanged from last distribution
    const result = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
    });

    expect(result.conflicts.length).toBe(0);
    expect(result.distributed.length).toBe(1);

    const current = await readFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "utf8",
    );
    expect(current.trim()).toBe("v2");
  });

  test("distributeSkills can force overwrite conflict", async () => {
    await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "original\n",
      "utf8",
    );

    // First distribution
    await distributeSkills({ sourceRoot, targets: ["claude"] });

    // Simulate user modification
    await writeFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "user-modified\n",
      "utf8",
    );

    // Force overwrite
    const result = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
      force: true,
    });

    // Force still records conflicts but overwrites them
    expect(result.conflicts.length).toBe(1);
    const current = await readFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "utf8",
    );
    expect(current.trim()).toBe("original");
  });

  test("distributeSkills uses symlink in developer mode", async () => {
    await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "alpha\n",
      "utf8",
    );

    const result = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
      devMode: true,
    });

    expect(result.errors.length).toBe(0);
    const info = await lstat(join(targetSkills, "alpha"));
    expect(info.isSymbolicLink()).toBe(true);
  });

  test("skipConflicts=true skips conflicting files", async () => {
    await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "original\n",
      "utf8",
    );

    // First distribution
    await distributeSkills({ sourceRoot, targets: ["claude"] });

    // Simulate user modification
    await writeFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "user-modified\n",
      "utf8",
    );

    // Skip conflicts
    const result = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
      skipConflicts: true,
    });

    expect(result.conflicts.length).toBe(1);
    const current = await readFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "utf8",
    );
    expect(current.trim()).toBe("user-modified");
  });

  test("backup=true backs up then overwrites conflicting files", async () => {
    await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "original\n",
      "utf8",
    );

    // First distribution
    await distributeSkills({ sourceRoot, targets: ["claude"] });

    // Simulate user modification
    await writeFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "user-modified\n",
      "utf8",
    );

    // Backup then overwrite
    const result = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
      backup: true,
    });

    expect(result.conflicts.length).toBe(1);
    // Destination should be overwritten with original
    const current = await readFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "utf8",
    );
    expect(current.trim()).toBe("original");
  });

  test("onConflict returning abort sets result.aborted and skips target", async () => {
    await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "original\n",
      "utf8",
    );

    // First distribution
    await distributeSkills({ sourceRoot, targets: ["claude"] });

    // Simulate user modification
    await writeFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "user-modified\n",
      "utf8",
    );

    // Abort via callback
    const result = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
      onConflict: async () => "abort" as ConflictAction,
    });

    expect(result.aborted).toBe(true);
    // Destination should remain unchanged
    const current = await readFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "utf8",
    );
    expect(current.trim()).toBe("user-modified");
  });

  test("no flags and no callback defaults to skip", async () => {
    await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "original\n",
      "utf8",
    );

    // First distribution
    await distributeSkills({ sourceRoot, targets: ["claude"] });

    // Simulate user modification
    await writeFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "user-modified\n",
      "utf8",
    );

    // No flags, no callback
    const result = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
    });

    expect(result.conflicts.length).toBe(1);
    const current = await readFile(
      join(targetSkills, "alpha", "SKILL.md"),
      "utf8",
    );
    expect(current.trim()).toBe("user-modified");
  });

  test("distributeSkills cleans up orphans", async () => {
    // Create two skills
    await mkdir(join(sourceRoot, "skills", "alpha"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "alpha", "SKILL.md"),
      "alpha\n",
      "utf8",
    );
    await mkdir(join(sourceRoot, "skills", "beta"), { recursive: true });
    await writeFile(
      join(sourceRoot, "skills", "beta", "SKILL.md"),
      "beta\n",
      "utf8",
    );

    // First distribution with both skills
    const first = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
    });
    expect(first.distributed.length).toBe(2);

    // Remove beta from source
    await rm(join(sourceRoot, "skills", "beta"), {
      recursive: true,
      force: true,
    });

    // Second distribution - beta should become orphan and be removed
    const second = await distributeSkills({
      sourceRoot,
      targets: ["claude"],
    });

    expect(second.orphansRemoved).toBe(1);

    // Verify beta was removed from destination
    let betaExists = true;
    try {
      await lstat(join(targetSkills, "beta"));
    } catch {
      betaExists = false;
    }
    expect(betaExists).toBe(false);
  });
});
