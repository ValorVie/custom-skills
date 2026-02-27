import { spawn } from "node:child_process";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

import type { Target } from "../hooks/useResources";

const DEFAULT_EDITOR = "vim";
const EDITOR_SPLIT_REGEX = /\s+/;

export interface OpenResult {
  success: boolean;
  message: string;
}

export type CommandRunner = (
  command: string,
  args: string[],
) => Promise<void>;

export function getMcpConfigPath(target: Target): string | null {
  const home = homedir();
  switch (target) {
    case "claude":
      return join(home, ".claude", "claude_desktop_config.json");
    case "opencode":
      return join(home, ".config", "opencode", "config.json");
    default:
      return null;
  }
}

export function resolveEditor(env = process.env): string {
  const editor = env.EDITOR?.trim();
  if (editor && editor.length > 0) {
    return editor;
  }
  return DEFAULT_EDITOR;
}

export function buildEditorCommand(
  configPath: string,
  env = process.env,
): [string, string[]] {
  const editor = resolveEditor(env);
  const [command = DEFAULT_EDITOR, ...extraArgs] = editor
    .split(EDITOR_SPLIT_REGEX)
    .filter(Boolean);
  return [command, [...extraArgs, configPath]];
}

export function buildFolderOpenCommand(
  configPath: string,
  platform = process.platform,
): [string, string[]] {
  const folder = dirname(configPath);

  if (platform === "darwin") {
    return ["open", [folder]];
  }

  if (platform === "win32") {
    return ["explorer", [folder]];
  }

  return ["xdg-open", [folder]];
}

export function spawnDetachedCommand(
  command: string,
  args: string[],
): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      detached: true,
      stdio: "ignore",
      shell: false,
    });

    child.once("error", reject);
    child.once("spawn", () => {
      child.unref();
      resolve();
    });
  });
}

export function spawnForegroundCommand(
  command: string,
  args: string[],
): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      detached: false,
      stdio: "inherit",
      shell: false,
    });

    child.once("error", reject);
    child.once("close", (exitCode) => {
      if ((exitCode ?? 1) !== 0) {
        reject(
          new Error(
            `Command failed (${exitCode ?? 1}): ${command} ${args.join(" ")}`,
          ),
        );
        return;
      }
      resolve();
    });
  });
}

export async function openMcpConfigInEditor(
  target: Target,
  runner: CommandRunner = spawnForegroundCommand,
  env = process.env,
): Promise<OpenResult> {
  const configPath = getMcpConfigPath(target);
  if (!configPath) {
    return {
      success: false,
      message: `MCP config is not available for target: ${target}`,
    };
  }

  const [command, args] = buildEditorCommand(configPath, env);
  try {
    await runner(command, args);
    return {
      success: true,
      message: `Opened MCP config in editor: ${configPath}`,
    };
  } catch (error) {
    return {
      success: false,
      message: `Failed to open MCP config in editor: ${String(error)}`,
    };
  }
}

export async function openMcpConfigFolder(
  target: Target,
  runner: CommandRunner = spawnDetachedCommand,
  platform = process.platform,
): Promise<OpenResult> {
  const configPath = getMcpConfigPath(target);
  if (!configPath) {
    return {
      success: false,
      message: `MCP config is not available for target: ${target}`,
    };
  }

  const folder = dirname(configPath);
  const [command, args] = buildFolderOpenCommand(configPath, platform);
  try {
    await runner(command, args);
    return {
      success: true,
      message: `Opened MCP config folder: ${folder}`,
    };
  } catch (error) {
    return {
      success: false,
      message: `Failed to open MCP config folder: ${String(error)}`,
    };
  }
}
