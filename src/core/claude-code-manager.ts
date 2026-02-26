import { commandExists, runCommand } from "../utils/system";

export type ClaudeInstallType = "npm" | "native" | null;

export interface ClaudeManagerDeps {
  commandExistsFn?: typeof commandExists;
  runCommandFn?: typeof runCommand;
}

export interface ClaudeStatusResult {
  type: ClaudeInstallType;
  version: string | null;
}

export interface ClaudeUpdateResult {
  success: boolean;
  message?: string;
}

export async function getClaudeInstallType(
  deps: ClaudeManagerDeps = {},
): Promise<ClaudeInstallType> {
  const commandExistsFn = deps.commandExistsFn ?? commandExists;
  const runCommandFn = deps.runCommandFn ?? runCommand;

  if (!commandExistsFn("claude")) {
    return null;
  }

  if (!commandExistsFn("npm")) {
    return "native";
  }

  const npmCheck = await runCommandFn(
    ["npm", "list", "-g", "@anthropic-ai/claude-code", "--depth=0"],
    { check: false, timeoutMs: 15_000 },
  );

  if (npmCheck.exitCode === 0 && npmCheck.stdout.includes("claude-code")) {
    return "npm";
  }

  return "native";
}

export function showInstallInstructions(
  onProgress: (message: string) => void,
): void {
  onProgress("安裝 Claude Code:");
  onProgress("  macOS/Linux: curl -fsSL https://claude.ai/install.sh | sh");
  onProgress("  macOS (Homebrew): brew install claude");
  onProgress("  Windows: winget install Anthropic.Claude");
}

export async function showClaudeStatus(
  onProgress: (message: string) => void,
  deps: ClaudeManagerDeps = {},
): Promise<ClaudeStatusResult> {
  const runCommandFn = deps.runCommandFn ?? runCommand;
  const type = await getClaudeInstallType(deps);

  if (type === null) {
    showInstallInstructions(onProgress);
    return { type: null, version: null };
  }

  const versionResult = await runCommandFn(["claude", "--version"], {
    check: false,
    timeoutMs: 10_000,
  });
  const version =
    versionResult.exitCode === 0
      ? (versionResult.stdout.trim().split(/\r?\n/)[0] ?? null)
      : null;

  if (type === "npm") {
    onProgress("⚠ Claude Code 透過 npm 安裝，建議改用原生安裝方式");
    onProgress("  移除 npm 版本: npm uninstall -g @anthropic-ai/claude-code");
    showInstallInstructions(onProgress);
  } else {
    const suffix = version ? ` ${version}` : "";
    onProgress(`✓ Claude Code (native)${suffix}`);
  }

  return { type, version };
}

export async function updateClaudeCode(
  onProgress: (message: string) => void,
  deps: ClaudeManagerDeps = {},
): Promise<ClaudeUpdateResult> {
  const runCommandFn = deps.runCommandFn ?? runCommand;
  const type = await getClaudeInstallType(deps);

  if (type === null) {
    onProgress("Claude Code 未安裝");
    showInstallInstructions(onProgress);
    return { success: false, message: "not installed" };
  }

  if (type === "npm") {
    onProgress("更新 Claude Code (npm)...");
    const result = await runCommandFn(
      ["npm", "install", "-g", "@anthropic-ai/claude-code@latest"],
      { check: false, timeoutMs: 120_000 },
    );

    if (result.exitCode === 0) {
      onProgress("⚠ 建議改用原生安裝方式以取得最佳體驗");
    }

    return {
      success: result.exitCode === 0,
      message: result.exitCode === 0 ? undefined : result.stderr,
    };
  }

  onProgress("更新 Claude Code...");
  const result = await runCommandFn(["claude", "update"], {
    check: false,
    timeoutMs: 120_000,
  });

  return {
    success: result.exitCode === 0,
    message: result.exitCode === 0 ? undefined : result.stderr,
  };
}
