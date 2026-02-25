import type { Command } from "commander";

import { runCommand } from "../utils/system";

export function registerCoverageCommand(program: Command): void {
  program
    .command("coverage")
    .description("Run tests with coverage")
    .argument("[path]", "Optional test path")
    .action(async (path?: string) => {
      const args = ["bun", "test", "--coverage"];
      if (path) {
        args.push(path);
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
    });
}
