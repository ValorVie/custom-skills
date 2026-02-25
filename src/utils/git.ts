import { runCommand } from "./system";

export async function isGitRepo(repoPath: string): Promise<boolean> {
  const result = await runCommand(
    ["git", "-C", repoPath, "rev-parse", "--is-inside-work-tree"],
    { check: false },
  );
  return result.exitCode === 0 && result.stdout.trim() === "true";
}

export async function gitInit(repoPath: string): Promise<boolean> {
  const result = await runCommand(["git", "-C", repoPath, "init"], {
    check: false,
  });
  return result.exitCode === 0;
}

export async function gitClone(
  repositoryUrl: string,
  destinationPath: string,
): Promise<boolean> {
  const result = await runCommand(
    ["git", "clone", repositoryUrl, destinationPath],
    {
      check: false,
    },
  );
  return result.exitCode === 0;
}

export async function gitPull(repoPath: string): Promise<boolean> {
  const result = await runCommand(["git", "-C", repoPath, "pull"], {
    check: false,
  });
  return result.exitCode === 0;
}

export async function gitAddCommit(
  repoPath: string,
  message: string,
): Promise<boolean> {
  const addResult = await runCommand(["git", "-C", repoPath, "add", "-A"], {
    check: false,
  });
  if (addResult.exitCode !== 0) {
    return false;
  }

  const hasChanges = await runCommand(
    ["git", "-C", repoPath, "diff", "--cached", "--quiet"],
    { check: false },
  );
  if (hasChanges.exitCode === 0) {
    return false;
  }

  const commitResult = await runCommand(
    ["git", "-C", repoPath, "commit", "-m", message],
    { check: false },
  );
  return commitResult.exitCode === 0;
}

export async function gitPullRebase(repoPath: string): Promise<boolean> {
  const result = await runCommand(["git", "-C", repoPath, "pull", "--rebase"], {
    check: false,
  });
  return result.exitCode === 0;
}

export async function gitPush(repoPath: string): Promise<boolean> {
  const hasUpstream = await runCommand(
    [
      "git",
      "-C",
      repoPath,
      "rev-parse",
      "--abbrev-ref",
      "--symbolic-full-name",
      "@{upstream}",
    ],
    { check: false },
  );

  const command =
    hasUpstream.exitCode === 0
      ? ["git", "-C", repoPath, "push"]
      : ["git", "-C", repoPath, "push", "-u", "origin", "main"];

  const result = await runCommand(command, { check: false });
  return result.exitCode === 0;
}

export async function detectLocalChanges(repoPath: string): Promise<boolean> {
  const result = await runCommand(
    ["git", "-C", repoPath, "status", "--porcelain"],
    { check: false },
  );
  if (result.exitCode !== 0) {
    return false;
  }
  return result.stdout.trim().length > 0;
}
