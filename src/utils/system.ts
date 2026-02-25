import { spawn, spawnSync } from "node:child_process";

export type SupportedOS = "linux" | "macos" | "windows";

export interface RunCommandOptions {
  cwd?: string;
  check?: boolean;
  env?: NodeJS.ProcessEnv;
  timeoutMs?: number;
}

export interface CommandResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

export function getOS(): SupportedOS {
  if (process.platform === "darwin") {
    return "macos";
  }
  if (process.platform === "win32") {
    return "windows";
  }
  return "linux";
}

export function commandExists(command: string): boolean {
  const checker = getOS() === "windows" ? "where" : "which";
  const result = spawnSync(checker, [command], { stdio: "ignore" });
  return result.status === 0;
}

export async function runCommand(
  command: string[],
  options: RunCommandOptions = {},
): Promise<CommandResult> {
  if (command.length === 0) {
    throw new Error("Command cannot be empty");
  }

  const { cwd, check = true, env, timeoutMs } = options;

  return await new Promise<CommandResult>((resolve, reject) => {
    const child = spawn(command[0], command.slice(1), {
      cwd,
      env,
      stdio: ["ignore", "pipe", "pipe"],
      shell: false,
    });

    let stdout = "";
    let stderr = "";
    let killedByTimeout = false;

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    let timer: NodeJS.Timeout | undefined;
    if (timeoutMs && timeoutMs > 0) {
      timer = setTimeout(() => {
        killedByTimeout = true;
        child.kill("SIGTERM");
      }, timeoutMs);
    }

    child.on("error", (error) => {
      if (timer) {
        clearTimeout(timer);
      }
      reject(error);
    });

    child.on("close", (code) => {
      if (timer) {
        clearTimeout(timer);
      }

      const result: CommandResult = {
        stdout,
        stderr,
        exitCode: code ?? -1,
      };

      if (killedByTimeout) {
        reject(new Error(`Command timed out: ${command.join(" ")}`));
        return;
      }

      if (check && result.exitCode !== 0) {
        reject(
          new Error(
            `Command failed (${result.exitCode}): ${command.join(" ")}\n${stderr}`,
          ),
        );
        return;
      }

      resolve(result);
    });
  });
}

export async function getBunVersion(): Promise<string | null> {
  if (!commandExists("bun")) {
    return null;
  }

  const result = await runCommand(["bun", "--version"], {
    check: false,
    timeoutMs: 5000,
  });

  if (result.exitCode !== 0) {
    return null;
  }

  const version = result.stdout.trim();
  return version.length > 0 ? version : null;
}
