import type { Command } from "commander";

import { runTui } from "../tui/index";

export function registerTuiCommand(program: Command): void {
  program
    .command("tui")
    .description("Launch interactive TUI")
    .action(() => {
      runTui();
    });
}
