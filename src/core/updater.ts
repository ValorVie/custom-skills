import { access } from "node:fs/promises";
import { join } from "node:path";

import { BUN_PACKAGES, NPM_PACKAGES, REPOS } from "../utils/shared";
import { commandExists, runCommand } from "../utils/system";

export interface UpdateOptions {
  skipNpm?: boolean;
  skipBun?: boolean;
  skipRepos?: boolean;
}

export interface UpdateItemResult {
  name: string;
  success: boolean;
  message?: string;
}

export interface UpdateResult {
  npmPackages: UpdateItemResult[];
  bunPackages: UpdateItemResult[];
  repos: UpdateItemResult[];
  errors: string[];
}

export async function runUpdate(
  options: UpdateOptions = {},
): Promise<UpdateResult> {
  const skipNpm = options.skipNpm ?? false;
  const skipBun = options.skipBun ?? false;
  const skipRepos = options.skipRepos ?? false;

  const result: UpdateResult = {
    npmPackages: [],
    bunPackages: [],
    repos: [],
    errors: [],
  };

  if (!skipNpm) {
    if (!commandExists("npm")) {
      result.errors.push("npm is not installed");
    } else {
      for (const pkg of NPM_PACKAGES) {
        const updateResult = await runCommand(["npm", "install", "-g", pkg], {
          check: false,
        });
        result.npmPackages.push({
          name: pkg,
          success: updateResult.exitCode === 0,
          message:
            updateResult.exitCode === 0 ? undefined : updateResult.stderr,
        });
      }
    }
  }

  if (!skipBun) {
    if (!commandExists("bun")) {
      result.errors.push("bun is not installed");
    } else {
      for (const pkg of BUN_PACKAGES) {
        const updateResult = await runCommand(["bun", "install", "-g", pkg], {
          check: false,
        });
        result.bunPackages.push({
          name: pkg,
          success: updateResult.exitCode === 0,
          message:
            updateResult.exitCode === 0 ? undefined : updateResult.stderr,
        });
      }
    }
  }

  if (!skipRepos) {
    for (const repo of REPOS) {
      try {
        await access(join(repo.dir, ".git"));
      } catch {
        result.repos.push({
          name: repo.name,
          success: false,
          message: "repository not found",
        });
        continue;
      }

      const updateResult = await runCommand(
        ["git", "-C", repo.dir, "pull", "--ff-only"],
        {
          check: false,
        },
      );
      result.repos.push({
        name: repo.name,
        success: updateResult.exitCode === 0,
        message: updateResult.exitCode === 0 ? undefined : updateResult.stderr,
      });
    }
  }

  return result;
}
