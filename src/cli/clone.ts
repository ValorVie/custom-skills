import { existsSync } from "node:fs";
import { cp, mkdir, readdir, readFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join, resolve } from "node:path";
import chalk from "chalk";
import type { Command } from "commander";

import {
  type DistributeResult,
  distributeSkills,
} from "../core/skill-distributor";
import {
  detectMetadataChanges,
  handleMetadataChanges,
  hasChanges,
} from "../utils/git-helpers";
import { t } from "../utils/i18n";
import { paths } from "../utils/paths";

interface CloneCommandResult extends DistributeResult {
  devMode: boolean;
  syncProject: boolean;
  metadata: {
    updated: number;
    unchanged: number;
    changed: boolean;
  };
}

function shortenPath(p: string): string {
  const home = homedir();
  return p.startsWith(home) ? p.replace(home, "~") : p;
}

async function detectDeveloperMode(
  cwd: string,
): Promise<{ isDev: boolean; projectRoot: string | null }> {
  // Check for package.json with name "ai-dev"
  const packageJsonPath = join(cwd, "package.json");
  try {
    const content = await readFile(packageJsonPath, "utf-8");
    const pkg = JSON.parse(content);
    // Match "ai-dev" or scoped "@xxx/ai-dev"
    const pkgName = pkg.name ?? "";
    if (pkgName !== "ai-dev" && !pkgName.endsWith("/ai-dev"))
      return { isDev: false, projectRoot: null };
  } catch {
    return { isDev: false, projectRoot: null };
  }

  // Exclude ~/.config/custom-skills itself
  const resolved = resolve(cwd);
  const configCustomSkills = resolve(paths.customSkills);
  if (resolved === configCustomSkills)
    return { isDev: false, projectRoot: null };

  return { isDev: true, projectRoot: cwd };
}

async function integrateToDevProject(
  devProjectRoot: string,
  onProgress?: (message: string) => void,
): Promise<void> {
  const log = onProgress ?? (() => {});
  const dstSkills = join(devProjectRoot, "skills");
  await mkdir(dstSkills, { recursive: true });

  // UDS skills (excluding agents, workflows, commands)
  const srcUds = join(paths.udsRepo, "skills", "claude-code");
  if (existsSync(srcUds)) {
    log(`${shortenPath(srcUds)}`);
    log(`  → ${shortenPath(dstSkills)}`);
    const entries = await readdir(srcUds, { withFileTypes: true });
    for (const entry of entries) {
      if (["agents", "workflows", "commands"].includes(entry.name)) continue;
      const src = join(srcUds, entry.name);
      const dst = join(dstSkills, entry.name);
      await cp(src, dst, { recursive: true, force: true });
    }
  }

  // UDS agents → agents/claude + agents/opencode
  const srcUdsAgents = join(paths.udsRepo, "skills", "claude-code", "agents");
  if (existsSync(srcUdsAgents)) {
    for (const target of ["claude", "opencode"]) {
      const dst = join(devProjectRoot, "agents", target);
      log(`${shortenPath(srcUdsAgents)}`);
      log(`  → ${shortenPath(dst)}`);
      await mkdir(dst, { recursive: true });
      await cp(srcUdsAgents, dst, { recursive: true, force: true });
    }
  }

  // UDS workflows → commands/workflows
  const srcUdsWorkflows = join(
    paths.udsRepo,
    "skills",
    "claude-code",
    "workflows",
  );
  if (existsSync(srcUdsWorkflows)) {
    const dst = join(devProjectRoot, "commands", "workflows");
    log(`${shortenPath(srcUdsWorkflows)}`);
    log(`  → ${shortenPath(dst)}`);
    await mkdir(dst, { recursive: true });
    await cp(srcUdsWorkflows, dst, { recursive: true, force: true });
  }

  // UDS commands → commands/claude
  const srcUdsCommands = join(
    paths.udsRepo,
    "skills",
    "claude-code",
    "commands",
  );
  if (existsSync(srcUdsCommands)) {
    const dst = join(devProjectRoot, "commands", "claude");
    log(`${shortenPath(srcUdsCommands)}`);
    log(`  → ${shortenPath(dst)}`);
    await mkdir(dst, { recursive: true });
    await cp(srcUdsCommands, dst, { recursive: true, force: true });
  }

  // Obsidian skills
  const srcObsidian = join(paths.obsidianSkillsRepo, "skills");
  if (existsSync(srcObsidian)) {
    log(`${shortenPath(srcObsidian)}`);
    log(`  → ${shortenPath(dstSkills)}`);
    await cp(srcObsidian, dstSkills, { recursive: true, force: true });
  }

  // Anthropic skill-creator
  const srcAnthropic = join(
    paths.anthropicSkillsRepo,
    "skills",
    "skill-creator",
  );
  if (existsSync(srcAnthropic)) {
    const dst = join(dstSkills, "skill-creator");
    log(`${shortenPath(srcAnthropic)}`);
    log(`  → ${shortenPath(dst)}`);
    await cp(srcAnthropic, dst, { recursive: true, force: true });
  }

  // Auto-Skill
  const srcAutoSkill = paths.autoSkillRepo;
  if (existsSync(srcAutoSkill) && existsSync(join(srcAutoSkill, "SKILL.md"))) {
    const dst = join(dstSkills, "auto-skill");
    log(`${shortenPath(srcAutoSkill)}`);
    log(`  → ${shortenPath(dst)}`);
    await mkdir(dst, { recursive: true });
    // Copy excluding .git, assets, README.md
    const entries = await readdir(srcAutoSkill, { withFileTypes: true });
    for (const entry of entries) {
      if ([".git", "assets", "README.md"].includes(entry.name)) continue;
      const src = join(srcAutoSkill, entry.name);
      const entryDst = join(dst, entry.name);
      await cp(src, entryDst, { recursive: true, force: true });
    }
  }
}

async function runClone(options: {
  force?: boolean;
  skipConflicts?: boolean;
  backup?: boolean;
  syncProject?: boolean;
  onProgress?: (message: string) => void;
}): Promise<CloneCommandResult> {
  const cwd = process.cwd();
  const { isDev: devMode, projectRoot } = await detectDeveloperMode(cwd);
  const syncProject = options.syncProject ?? true;

  // Dev mode: integrate external sources if syncProject enabled
  if (devMode && syncProject && projectRoot) {
    options.onProgress?.("開發者模式：整合外部來源到開發目錄");
    await integrateToDevProject(projectRoot, options.onProgress);
  }

  // Check source directory exists
  const customSkillsDir = devMode ? cwd : paths.customSkills;
  if (!existsSync(customSkillsDir)) {
    const errorMsg = `來源目錄不存在 (${shortenPath(customSkillsDir)})`;
    throw new Error(errorMsg);
  }

  const distribution = await distributeSkills({
    force: options.force,
    skipConflicts: options.skipConflicts,
    backup: options.backup,
    devMode,
    sourceRoot: devMode ? cwd : customSkillsDir,
    onProgress: options.onProgress,
  });

  return {
    ...distribution,
    devMode,
    syncProject,
    metadata: {
      updated: distribution.distributed.length,
      unchanged: distribution.unchanged,
      changed: distribution.distributed.length > 0,
    },
  };
}

export function registerCloneCommand(program: Command): void {
  program
    .command("clone")
    .description(t("cmd.clone"))
    .option("--force", t("opt.force"))
    .option("--skip-conflicts", t("opt.skip_conflicts"))
    .option("--backup", t("opt.backup"))
    .option("--sync-project", t("opt.sync_project"), true)
    .option("--no-sync-project", t("opt.no_sync_project"))
    .option("--json", t("opt.json"))
    .action(
      async (options: {
        force?: boolean;
        skipConflicts?: boolean;
        backup?: boolean;
        syncProject?: boolean;
        json?: boolean;
      }) => {
        let result: CloneCommandResult;
        try {
          result = await runClone({
            force: options.force,
            skipConflicts: options.skipConflicts,
            backup: options.backup,
            syncProject: options.syncProject,
            onProgress: options.json
              ? undefined
              : (msg) => console.log(chalk.dim(`  ${msg}`)),
          });
        } catch (error) {
          const message =
            error instanceof Error ? error.message : String(error);
          if (options.json) {
            console.log(JSON.stringify({ error: message }, null, 2));
          } else {
            console.log(chalk.bold.red(`錯誤：${message}`));
            console.log(chalk.dim("請先執行 ai-dev install 或 ai-dev update"));
          }
          process.exit(1);
        }

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        // Dev mode hints
        if (result.devMode && result.syncProject) {
          console.log(chalk.bold.blue("開發者模式：整合外部來源到開發目錄"));
        } else if (result.devMode) {
          const cwd = process.cwd();
          console.log(
            chalk.dim(
              `提示：使用 --sync-project 可整合外部來源到開發目錄 (${shortenPath(cwd)})`,
            ),
          );
        }

        console.log(chalk.bold.blue("\n分發 Skills 到各工具目錄..."));

        // Distribution results
        if (result.distributed.length > 0) {
          for (const item of result.distributed) {
            console.log(
              chalk.green(`  ✓ ${item.target}/${item.type}: ${item.name}`),
            );
          }
        }

        console.log(
          chalk.bold.green(
            `\n分發完成！共 ${result.metadata.updated} 項更新，${result.metadata.unchanged} 項未變更`,
          ),
        );

        // Conflicts
        if (result.conflicts.length > 0) {
          console.log(chalk.yellow("\n衝突："));
          for (const conflict of result.conflicts) {
            console.log(
              chalk.yellow(
                `  ! ${conflict.target}/${conflict.type}: ${conflict.name}`,
              ),
            );
          }
        }

        // Errors
        if (result.errors.length > 0) {
          console.log(chalk.red("\n錯誤："));
          for (const error of result.errors) {
            console.log(chalk.red(`  ✗ ${error}`));
          }
        }

        // Dev mode: detect and handle metadata changes
        if (result.devMode) {
          const cwd = process.cwd();
          const changes = detectMetadataChanges(cwd);
          if (hasChanges(changes)) {
            handleMetadataChanges(changes, cwd);
          }
        }
      },
    );
}
