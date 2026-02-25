import { describe, expect, test } from "bun:test";
import { access, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  backup_file,
  cleanup_orphans,
  detect_conflicts,
  find_orphans,
  ManifestTracker,
} from "../../src/utils/manifest";

describe("utils/manifest-tracker", () => {
  test("ManifestTracker records resources and generates manifest", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-manifest-tracker-"));

    try {
      const skillDir = join(root, "skills", "foo");
      const commandFile = join(root, "commands", "bar.md");
      await mkdir(skillDir, { recursive: true });
      await mkdir(join(root, "commands"), { recursive: true });
      await writeFile(join(skillDir, "SKILL.md"), "hello\n", "utf8");
      await writeFile(commandFile, "command\n", "utf8");

      const tracker = new ManifestTracker("claude");
      await tracker.recordSkill("foo", skillDir);
      await tracker.recordCommand("bar", commandFile);

      const manifest = tracker.toManifest("2.0.0");
      expect(manifest.files.skills.foo).toBeDefined();
      expect(manifest.files.commands.bar).toBeDefined();
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("detect_conflicts and find_orphans work", async () => {
    const tracker = new ManifestTracker("claude");
    tracker.skills.set("foo", {
      name: "foo",
      hash: "sha256:new",
      source: "custom-skills",
      sourcePath: "/tmp/foo",
    });

    const oldManifest = {
      managedBy: "ai-dev" as const,
      version: "1.0.0",
      lastSync: new Date().toISOString(),
      target: "claude",
      files: {
        skills: {
          foo: { hash: "sha256:old", source: "custom-skills" },
          orphan: { hash: "sha256:orphan", source: "custom-skills" },
        },
        commands: {},
        agents: {},
        workflows: {},
      },
    };

    const conflicts = detect_conflicts(oldManifest, tracker);
    expect(conflicts.length).toBe(1);
    expect(conflicts[0]?.name).toBe("foo");

    const newManifest = tracker.toManifest("2.0.0");
    const orphans = find_orphans(oldManifest, newManifest);
    expect(orphans.skills).toEqual(["orphan"]);
  });

  test("cleanup_orphans and backup_file handle filesystem paths", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-manifest-tracker-"));

    try {
      const skillsPath = join(root, "skills");
      const commandsPath = join(root, "commands");
      await mkdir(join(skillsPath, "orphan-skill"), { recursive: true });
      await mkdir(commandsPath, { recursive: true });
      const orphanCommand = join(commandsPath, "orphan-command.md");
      await writeFile(orphanCommand, "orphan\n", "utf8");

      const removed = await cleanup_orphans(
        {
          skills: skillsPath,
          commands: commandsPath,
        },
        {
          skills: ["orphan-skill"],
          commands: ["orphan-command"],
          agents: [],
          workflows: [],
        },
      );
      expect(removed).toBe(2);

      const backupRoot = join(root, "backups");
      const sampleFile = join(root, "sample.md");
      await writeFile(sampleFile, "sample\n", "utf8");
      const backupPath = await backup_file(sampleFile, backupRoot);
      expect(backupPath).not.toBeNull();
      await access(backupPath as string);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});
