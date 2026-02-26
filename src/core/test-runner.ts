import { access, readFile } from "node:fs/promises";
import { join } from "node:path";

export type TestFramework = "bun" | "npm" | "pytest" | "phpunit";

export interface TestCommandOptions {
  framework: TestFramework;
  path?: string;
  verbose?: boolean;
  failFast?: boolean;
  keyword?: string;
  coverage?: boolean;
  source?: string;
}

async function pathExists(pathValue: string): Promise<boolean> {
  try {
    await access(pathValue);
    return true;
  } catch {
    return false;
  }
}

export async function detectTestFramework(
  projectRoot = process.cwd(),
): Promise<TestFramework> {
  if (
    (await pathExists(join(projectRoot, "bun.lock"))) ||
    (await pathExists(join(projectRoot, "bunfig.toml")))
  ) {
    return "bun";
  }

  if (
    (await pathExists(join(projectRoot, "pytest.ini"))) ||
    (await pathExists(join(projectRoot, "pyproject.toml")))
  ) {
    return "pytest";
  }

  if (
    (await pathExists(join(projectRoot, "phpunit.xml"))) ||
    (await pathExists(join(projectRoot, "phpunit.xml.dist"))) ||
    (await pathExists(join(projectRoot, "composer.json")))
  ) {
    return "phpunit";
  }

  if (await pathExists(join(projectRoot, "package.json"))) {
    try {
      const packageJsonRaw = await readFile(
        join(projectRoot, "package.json"),
        "utf8",
      );
      const packageJson = JSON.parse(packageJsonRaw) as {
        scripts?: Record<string, string>;
      };
      if (typeof packageJson.scripts?.test === "string") {
        return "npm";
      }
    } catch {
      return "npm";
    }
    return "npm";
  }

  return "bun";
}

export function buildTestCommand(options: TestCommandOptions): string[] {
  const args: string[] = [];

  if (options.framework === "bun") {
    args.push("bun", "test");
    if (options.coverage) {
      args.push("--coverage");
    }
    if (options.path) {
      args.push(options.path);
    }
    if (options.verbose) {
      args.push("--verbose");
    }
    if (options.failFast) {
      args.push("--bail");
    }
    if (options.keyword) {
      args.push("--test-name-pattern", options.keyword);
    }
    return args;
  }

  if (options.framework === "pytest") {
    args.push("pytest");
    if (options.path) {
      args.push(options.path);
    }
    if (options.verbose) {
      args.push("-v");
    }
    if (options.failFast) {
      args.push("-x");
    }
    if (options.keyword) {
      args.push("-k", options.keyword);
    }
    if (options.coverage) {
      args.push(`--cov=${options.source ?? "."}`, "--cov-report=term-missing");
    }
    return args;
  }

  if (options.framework === "phpunit") {
    args.push("phpunit");
    if (options.path) {
      args.push(options.path);
    }
    if (options.failFast) {
      args.push("--stop-on-failure");
    }
    if (options.coverage) {
      args.push("--coverage-text");
    }
    return args;
  }

  args.push("npm", "test");
  const npmArgs: string[] = [];
  if (options.path) {
    npmArgs.push(options.path);
  }
  if (options.verbose) {
    npmArgs.push("--verbose");
  }
  if (options.failFast) {
    npmArgs.push("--bail");
  }
  if (options.keyword) {
    npmArgs.push("--testNamePattern", options.keyword);
  }
  if (options.coverage) {
    npmArgs.push("--coverage");
    if (options.source) {
      npmArgs.push("--collectCoverageFrom", options.source);
    }
  }

  if (npmArgs.length > 0) {
    args.push("--", ...npmArgs);
  }

  return args;
}
