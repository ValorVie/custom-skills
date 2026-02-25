import { cp, mkdir, readdir } from "node:fs/promises";
import { join } from "node:path";

import { paths } from "./paths";

export type TargetType =
  | "claude"
  | "antigravity"
  | "opencode"
  | "codex"
  | "gemini";

export type ResourceType = "skills" | "commands" | "agents" | "workflows";

export type CopyTarget = Partial<Record<ResourceType | "plugins", string>>;

export interface RepoDefinition {
  name: string;
  url: string;
  dir: string;
}

export const NPM_PACKAGES = [
  "@fission-ai/openspec@latest",
  "@google/gemini-cli",
  "universal-dev-standards",
  "opencode-ai@latest",
  "skills",
  "happy-coder",
] as const;

export const BUN_PACKAGES = ["@openai/codex"] as const;

export const REPOS: RepoDefinition[] = [
  {
    name: "custom-skills",
    url: "https://github.com/ValorVie/custom-skills.git",
    dir: paths.customSkills,
  },
  {
    name: "superpowers",
    url: "https://github.com/obra/superpowers.git",
    dir: paths.superpowersRepo,
  },
  {
    name: "uds",
    url: "https://github.com/AsiaOstrich/universal-dev-standards.git",
    dir: paths.udsRepo,
  },
  {
    name: "obsidian-skills",
    url: "https://github.com/kepano/obsidian-skills.git",
    dir: paths.obsidianSkillsRepo,
  },
  {
    name: "anthropic-skills",
    url: "https://github.com/anthropics/skills.git",
    dir: paths.anthropicSkillsRepo,
  },
  {
    name: "everything-claude-code",
    url: "https://github.com/affaan-m/everything-claude-code.git",
    dir: paths.everythingClaudeCodeRepo,
  },
  {
    name: "auto-skill",
    url: "https://github.com/Toolsai/auto-skill.git",
    dir: paths.autoSkillRepo,
  },
];

export const COPY_TARGETS: Record<TargetType, CopyTarget> = {
  claude: {
    skills: paths.claudeSkills,
    commands: paths.claudeCommands,
    agents: paths.claudeAgents,
    workflows: paths.claudeWorkflows,
  },
  antigravity: {
    skills: `${paths.antigravityConfig}/global_skills`,
    workflows: `${paths.antigravityConfig}/global_workflows`,
  },
  opencode: {
    skills: paths.opencodeSkills,
    commands: paths.opencodeCommands,
    agents: paths.opencodeAgents,
    plugins: paths.opencodePlugins,
  },
  codex: {
    skills: paths.codexSkills,
  },
  gemini: {
    skills: paths.geminiSkills,
    commands: paths.geminiCommands,
    agents: paths.geminiAgents,
  },
};

export async function getAllSkillNames(
  sourceDir = join(process.cwd(), "skills"),
): Promise<string[]> {
  try {
    const entries = await readdir(sourceDir, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isDirectory() && !entry.name.startsWith("."))
      .map((entry) => entry.name)
      .sort((a, b) => a.localeCompare(b));
  } catch {
    return [];
  }
}

export async function copySkills(
  options: { sourceDir?: string; targets?: TargetType[] } = {},
): Promise<{ copied: number; byTarget: Record<TargetType, number> }> {
  const sourceDir = options.sourceDir ?? join(process.cwd(), "skills");
  const targets =
    options.targets ?? (Object.keys(COPY_TARGETS) as TargetType[]);
  const skillNames = await getAllSkillNames(sourceDir);

  const byTarget = Object.fromEntries(
    targets.map((target) => [target, 0]),
  ) as Record<TargetType, number>;

  for (const target of targets) {
    const destinationBase = COPY_TARGETS[target].skills;
    if (!destinationBase) {
      continue;
    }

    await mkdir(destinationBase, { recursive: true });

    for (const skillName of skillNames) {
      const sourcePath = join(sourceDir, skillName);
      const destinationPath = join(destinationBase, skillName);
      await cp(sourcePath, destinationPath, {
        recursive: true,
        force: true,
      });
      byTarget[target] += 1;
    }
  }

  const copied = Object.values(byTarget).reduce((sum, count) => sum + count, 0);
  return { copied, byTarget };
}
