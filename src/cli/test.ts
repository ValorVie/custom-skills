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

export function registerTestCommand(program: Command): void {
  program
    .command("test")
    .description(t("cmd.test"))
    .argument("[path]", "Optional test path")
    .option("-v, --verbose", t("opt.verbose"))
    .option("-x, --fail-fast", t("opt.fail_fast"))
    .option("-k, --keyword <keyword>", t("opt.keyword"))
    .option("--framework <framework>", t("opt.framework"))
    .option("--source <path>", t("opt.source"))
    .action(
      async (
        path: string | undefined,
        options: {
          verbose?: boolean;
          failFast?: boolean;
          keyword?: string;
          framework?: string;
          source?: string;
        },
      ) => {
        const framework = options.framework
          ? isFramework(options.framework)
            ? options.framework
            : null
          : await detectTestFramework();

        if (!framework) {
          process.stderr.write(
            `${t("test.unsupported_framework", { framework: options.framework ?? "" })}\n`,
          );
          process.exitCode = 1;
          return;
        }

        const args = buildTestCommand({
          framework,
          path,
          verbose: options.verbose,
          failFast: options.failFast,
          keyword: options.keyword,
          source: options.source,
          coverage: false,
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
