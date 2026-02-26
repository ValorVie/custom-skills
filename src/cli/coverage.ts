import type { Command } from "commander";

import {
  buildTestCommand,
  detectTestFramework,
  type TestFramework,
} from "../core/test-runner";
import { t } from "../utils/i18n";
import { runCommand } from "../utils/system";

function isFramework(value: string): value is TestFramework {
  return (
    value === "bun" ||
    value === "npm" ||
    value === "pytest" ||
    value === "phpunit"
  );
}

export function registerCoverageCommand(program: Command): void {
  program
    .command("coverage")
    .description("Run tests with coverage")
    .argument("[path]", "Optional test path")
    .option(
      "--framework <framework>",
      "Test framework (bun|npm|pytest|phpunit)",
    )
    .option("--source <path>", "Coverage source path")
    .action(
      async (
        path: string | undefined,
        options: { framework?: string; source?: string },
      ) => {
        const framework = options.framework
          ? isFramework(options.framework)
            ? options.framework
            : null
          : await detectTestFramework();

        if (!framework) {
          process.stderr.write(
            `${t("coverage.unsupported_framework", { framework: options.framework ?? "" })}\n`,
          );
          process.exitCode = 1;
          return;
        }

        const args = buildTestCommand({
          framework,
          path,
          coverage: true,
          source: options.source,
        });

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
