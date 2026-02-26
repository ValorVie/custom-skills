import type { Command } from "commander";

import { runTui } from "../tui/index";
import { t } from "../utils/i18n";

export function registerTuiCommand(program: Command): void {
  program
    .command("tui")
    .description(t("cmd.tui"))
    .action(() => {
      runTui();
    });
}
