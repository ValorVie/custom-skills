import { access, cp, mkdir } from "node:fs/promises";
import { join, resolve } from "node:path";

import { runCommand } from "../utils/system";

export interface ProjectInitOptions {
  targetDir?: string;
  templateDir?: string;
  force?: boolean;
}

export interface ProjectInitResult {
  success: boolean;
  targetDir: string;
  templateDir: string;
  copied: boolean;
  message?: string;
}

export interface ProjectUpdateOptions {
  only?: "openspec" | "uds";
  deps?: ProjectUpdateDependencies;
}

export interface ProjectUpdateDependencies {
  runCommandFn?: typeof runCommand;
}

export interface ProjectUpdateResult {
  openspec?: boolean;
  uds?: boolean;
  errors: string[];
}

function defaultTemplateDir(): string {
  return resolve(process.cwd(), "project-template");
}

export async function initProject(
  options: ProjectInitOptions = {},
): Promise<ProjectInitResult> {
  const targetDir = resolve(options.targetDir ?? process.cwd());
  const templateDir = resolve(options.templateDir ?? defaultTemplateDir());
  const force = options.force ?? false;

  try {
    await access(templateDir);
  } catch {
    return {
      success: false,
      targetDir,
      templateDir,
      copied: false,
      message: "template directory not found",
    };
  }

  const standardsPath = join(targetDir, ".standards");
  if (!force) {
    try {
      await access(standardsPath);
      return {
        success: true,
        targetDir,
        templateDir,
        copied: false,
        message: "project already initialized",
      };
    } catch {
      // continue
    }
  }

  await mkdir(targetDir, { recursive: true });
  await cp(templateDir, targetDir, {
    recursive: true,
    force,
  });

  return {
    success: true,
    targetDir,
    templateDir,
    copied: true,
  };
}

export async function updateProject(
  options: ProjectUpdateOptions = {},
): Promise<ProjectUpdateResult> {
  const runCommandFn = options.deps?.runCommandFn ?? runCommand;
  const result: ProjectUpdateResult = { errors: [] };
  const shouldRunOpenspec = !options.only || options.only === "openspec";
  const shouldRunUds = !options.only || options.only === "uds";

  if (shouldRunOpenspec) {
    const command = await runCommandFn(["openspec", "update"], {
      check: false,
    });
    result.openspec = command.exitCode === 0;
    if (!result.openspec) {
      result.errors.push("openspec update failed");
    }
  }

  if (shouldRunUds) {
    const command = await runCommandFn(["uds", "update"], { check: false });
    result.uds = command.exitCode === 0;
    if (!result.uds) {
      result.errors.push("uds update failed");
    }
  }

  return result;
}
