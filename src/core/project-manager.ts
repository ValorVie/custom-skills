import {
  access,
  cp,
  mkdir,
  readdir,
  readFile,
  stat,
  writeFile,
} from "node:fs/promises";
import { basename, dirname, join, resolve } from "node:path";

import { runCommand } from "../utils/system";

export interface ProjectInitOptions {
  targetDir?: string;
  templateDir?: string;
  force?: boolean;
  onProgress?: (msg: string) => void;
}

export interface ProjectInitResult {
  success: boolean;
  targetDir: string;
  templateDir: string;
  copied: boolean;
  reverseSynced?: boolean;
  backupDir?: string;
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

async function pathExists(pathValue: string): Promise<boolean> {
  try {
    await access(pathValue);
    return true;
  } catch {
    return false;
  }
}

async function collectFiles(rootDir: string): Promise<string[]> {
  const files: string[] = [];

  async function walk(currentDir: string): Promise<void> {
    const entries = await readdir(currentDir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = join(currentDir, entry.name);
      if (entry.isDirectory()) {
        await walk(fullPath);
        continue;
      }

      if (entry.isFile()) {
        files.push(fullPath.slice(rootDir.length + 1));
      }
    }
  }

  await walk(rootDir);
  return files.sort((a, b) => a.localeCompare(b));
}

async function mergeLineByLine(
  sourcePath: string,
  targetPath: string,
): Promise<boolean> {
  const sourceContent = await readFile(sourcePath, "utf8");
  let targetContent = "";
  try {
    targetContent = await readFile(targetPath, "utf8");
  } catch {
    targetContent = "";
  }

  const sourceLines = sourceContent
    .split(/\r?\n/)
    .filter((line) => line.length > 0);
  const targetLines = targetContent
    .split(/\r?\n/)
    .filter((line) => line.length > 0);
  const existing = new Set(targetLines);
  const merged = [...targetLines];
  let changed = false;

  for (const line of sourceLines) {
    if (!existing.has(line)) {
      merged.push(line);
      changed = true;
    }
  }

  if (!changed) {
    return false;
  }

  await mkdir(dirname(targetPath), { recursive: true });
  await writeFile(targetPath, `${merged.join("\n")}\n`, "utf8");
  return true;
}

async function copyIfChanged(
  sourcePath: string,
  targetPath: string,
): Promise<boolean> {
  if (!(await pathExists(targetPath))) {
    await mkdir(dirname(targetPath), { recursive: true });
    await cp(sourcePath, targetPath, { recursive: true, force: true });
    return true;
  }

  const sourceContent = await readFile(sourcePath);
  const targetContent = await readFile(targetPath);
  if (sourceContent.equals(targetContent)) {
    return false;
  }

  await mkdir(dirname(targetPath), { recursive: true });
  await cp(sourcePath, targetPath, { recursive: true, force: true });
  return true;
}

async function backupTargetFile(
  targetPath: string,
  backupRoot: string,
  relativePath: string,
): Promise<void> {
  await mkdir(dirname(join(backupRoot, relativePath)), { recursive: true });
  await cp(targetPath, join(backupRoot, relativePath), {
    recursive: true,
    force: true,
  });
}

async function reverseSyncProjectToTemplate(
  targetDir: string,
  templateDir: string,
): Promise<void> {
  const templateEntries = await readdir(templateDir, { withFileTypes: true });
  for (const entry of templateEntries) {
    const sourcePath = join(targetDir, entry.name);
    const destinationPath = join(templateDir, entry.name);

    if (!(await pathExists(sourcePath))) {
      continue;
    }

    if (resolve(sourcePath) === resolve(templateDir)) {
      continue;
    }

    await cp(sourcePath, destinationPath, {
      recursive: true,
      force: true,
    });
  }
}

function shouldReverseSync(targetDir: string, force: boolean): boolean {
  if (!force) {
    return false;
  }

  const cwd = resolve(process.cwd());
  return basename(cwd) === "custom-skills" && resolve(targetDir) === cwd;
}

export async function initProject(
  options: ProjectInitOptions = {},
): Promise<ProjectInitResult> {
  const targetDir = resolve(options.targetDir ?? process.cwd());
  const templateDir = resolve(options.templateDir ?? defaultTemplateDir());
  const force = options.force ?? false;
  const onProgress = options.onProgress;
  const backupRoot = join(
    targetDir,
    ".ai-dev-backups",
    new Date().toISOString().replace(/[:.]/g, "-"),
  );

  if (!(await pathExists(templateDir))) {
    return {
      success: false,
      targetDir,
      templateDir,
      copied: false,
      message: "template directory not found",
    };
  }

  await mkdir(targetDir, { recursive: true });
  const templateFiles = await collectFiles(templateDir);

  let copied = false;
  let backupCreated = false;

  for (const relativePath of templateFiles) {
    const sourcePath = join(templateDir, relativePath);
    const targetPath = join(targetDir, relativePath);
    const fileName = relativePath.split(/[\\/]/).pop() ?? "";

    if (
      (fileName === ".gitignore" || fileName === ".gitattributes") &&
      !force
    ) {
      if (await mergeLineByLine(sourcePath, targetPath)) {
        copied = true;
        onProgress?.(`✓ 合併 ${relativePath}`);
      } else {
        onProgress?.(`  無變更 ${relativePath}`);
      }
      continue;
    }

    if (!force && (await pathExists(targetPath))) {
      const sourceStat = await stat(sourcePath);
      const targetStat = await stat(targetPath);
      if (sourceStat.isFile() && targetStat.isFile()) {
        await backupTargetFile(targetPath, backupRoot, relativePath);
        backupCreated = true;
      }
    }

    if (await copyIfChanged(sourcePath, targetPath)) {
      copied = true;
      onProgress?.(`✓ ${relativePath}`);
    } else {
      onProgress?.(`  無變更 ${relativePath}`);
    }
  }

  let reverseSynced = false;
  if (shouldReverseSync(targetDir, force)) {
    await reverseSyncProjectToTemplate(targetDir, templateDir);
    reverseSynced = true;
  }

  return {
    success: true,
    targetDir,
    templateDir,
    copied,
    reverseSynced,
    backupDir: backupCreated ? backupRoot : undefined,
    message: copied ? undefined : "project already up to date",
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
