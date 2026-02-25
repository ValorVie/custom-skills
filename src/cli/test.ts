import type { Command } from "commander";

import { runCommand } from "../utils/system";

export function registerTestCommand(program: Command): void {
  program
    .command("test")
    .description("Run Bun tests")
    .argument("[path]", "Optional test path")
    .option("-v, --verbose", "Verbose output")
    .option("-x, --fail-fast", "Stop on first failure")
    .option("-k, --keyword <keyword>", "Filter tests by name")
    .action(
      async (
        path: string | undefined,
        options: { verbose?: boolean; failFast?: boolean; keyword?: string },
      ) => {
        const args = ["bun", "test"];
        if (path) {
          args.push(path);
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

        const result = await runCommand(args, { check: false });
        if (result.stdout) {
          process.stdout.write(result.stdout);
        }
        if (result.stderr) {
          process.stderr.write(result.stderr);
        }
        if (result.exitCode !== 0) {
          process.exitCode = result.exitCode;
        }
      },
    );
}
