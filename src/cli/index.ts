import { Command } from "commander";
import { isLocale, setLocale } from "../utils/i18n";
import { registerAddCustomRepoCommand } from "./add-custom-repo";
import { registerAddRepoCommand } from "./add-repo";
import { registerCloneCommand } from "./clone";
import { registerCoverageCommand } from "./coverage";
import { registerDeriveTestsCommand } from "./derive-tests";
import { registerHooksCommands } from "./hooks/index";
import { registerInstallCommand } from "./install";
import { registerListCommand } from "./list";
import { registerMemCommands } from "./mem/index";
import { registerProjectCommands } from "./project/index";
import { registerStandardsCommands } from "./standards/index";
import { registerStatusCommand } from "./status";
import { registerSyncCommands } from "./sync/index";
import { registerTestCommand } from "./test";
import { registerToggleCommand } from "./toggle";
import { registerTuiCommand } from "./tui";
import { registerUpdateCommand } from "./update";
import { registerUpdateCustomRepoCommand } from "./update-custom-repo";

export function createProgram(): Command {
  const program = new Command()
    .name("ai-dev")
    .description("AI development workflow CLI toolkit")
    .version("2.0.0")
    .option("--lang <locale>", "Output language (en|zh-TW)");

  program.hook("preAction", (command) => {
    const options = command.optsWithGlobals<{ lang?: string }>();
    if (!options.lang) {
      return;
    }

    if (!isLocale(options.lang)) {
      throw new Error(`Unsupported locale: ${options.lang}`);
    }

    setLocale(options.lang);
  });

  registerInstallCommand(program);
  registerUpdateCommand(program);
  registerCloneCommand(program);
  registerStatusCommand(program);
  registerListCommand(program);
  registerToggleCommand(program);
  registerAddRepoCommand(program);
  registerAddCustomRepoCommand(program);
  registerUpdateCustomRepoCommand(program);
  registerTestCommand(program);
  registerCoverageCommand(program);
  registerDeriveTestsCommand(program);
  registerProjectCommands(program);
  registerStandardsCommands(program);
  registerHooksCommands(program);
  registerSyncCommands(program);
  registerMemCommands(program);
  registerTuiCommand(program);

  return program;
}

export async function run(argv: string[] = process.argv): Promise<void> {
  const program = createProgram();
  await program.parseAsync(argv);
}
