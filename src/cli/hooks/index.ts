import { access, mkdir, rm, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import type { Command } from "commander";

function hooksPluginDir(): string {
  return join(homedir(), ".claude", "plugins", "ecc-hooks");
}

async function pluginInstalled(): Promise<boolean> {
  try {
    await access(hooksPluginDir());
    return true;
  } catch {
    return false;
  }
}

export function registerHooksCommands(program: Command): void {
  const hooks = program.command("hooks").description("Manage ECC hooks plugin");

  hooks
    .command("install")
    .description("Install hooks plugin")
    .action(async () => {
      const dir = hooksPluginDir();
      await mkdir(dir, { recursive: true });
      await writeFile(
        join(dir, "README.md"),
        "# ECC Hooks Plugin\n\nInstalled by ai-dev.\n",
        "utf8",
      );
      console.log(`Installed: ${dir}`);
    });

  hooks
    .command("uninstall")
    .description("Uninstall hooks plugin")
    .action(async () => {
      const dir = hooksPluginDir();
      await rm(dir, { recursive: true, force: true });
      console.log(`Removed: ${dir}`);
    });

  hooks
    .command("status")
    .description("Show hooks plugin status")
    .action(async () => {
      console.log(`installed=${await pluginInstalled()}`);
    });
}
