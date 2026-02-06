/**
 * ECC Hooks for OpenCode
 *
 * OpenCode plugin that wraps the same scripts used by the Claude Code
 * ecc-hooks plugin. Provides:
 * - Code quality checks (JS/TS, PHP, Python)
 * - Memory persistence (session start/end, pre-compact)
 * - Strategic compact suggestions
 * - Dev server tmux enforcement
 * - Git push reminder
 */

import type { Plugin } from "@opencode-ai/plugin";
import { join } from "path";

const SCRIPTS_DIR = join(import.meta.dir, "scripts");

const CODE_QUALITY_DIR = join(SCRIPTS_DIR, "code-quality");
const MEMORY_DIR = join(SCRIPTS_DIR, "memory-persistence");
const COMPACT_DIR = join(SCRIPTS_DIR, "strategic-compact");
const STOP_DEBUG_CHECK = join(CODE_QUALITY_DIR, "check-debug-code-opencode.js");

// Patterns matching Claude Code hooks.json
const DEV_SERVER_PATTERN =
  /npm run dev|pnpm( run)? dev|yarn dev|bun run dev/;
const LONG_RUNNING_PATTERN =
  /npm (install|test)|pnpm (install|test)|yarn (install|test)?|bun (install|test)|cargo build|make|docker|pytest|vitest|playwright/;
const GIT_PUSH_PATTERN = /git push/;

const JS_TS_PATTERN = /\.(ts|tsx|js|jsx)$/;
const TS_ONLY_PATTERN = /\.(ts|tsx)$/;
const PHP_PATTERN = /\.php$/;
const PYTHON_PATTERN = /\.py$/;

export const EccHooksPlugin: Plugin = async ({ $, directory }) => {
  return {
    // ================================================================
    // Event Hook: Session lifecycle → memory persistence
    // Maps: Claude SessionStart/SessionEnd → OpenCode session events
    // ================================================================
    event: async ({ event }) => {
      try {
        if (event.type === "session.created") {
          await $`python3 ${join(MEMORY_DIR, "session-start.py")}`.quiet();
        }

        if (event.type === "session.deleted") {
          await $`node ${STOP_DEBUG_CHECK}`;
          await $`python3 ${join(MEMORY_DIR, "session-end.py")}`.quiet();
          await $`python3 ${join(MEMORY_DIR, "evaluate-session.py")}`.quiet();
        }
      } catch {
        // Non-critical: don't block on memory persistence failures
      }
    },

    // ================================================================
    // Pre-tool: dev server blocking, tmux reminder, git push reminder,
    //           strategic compact suggestion
    // Maps: Claude PreToolUse hooks
    // ================================================================
    "tool.execute.before": async (input, output) => {
      const tool = input.tool;
      const args = input.args as Record<string, unknown>;

      // --- Bash command interception ---
      if (tool === "bash") {
        const command = (args.command as string) || "";

        // Block dev servers outside tmux
        if (DEV_SERVER_PATTERN.test(command)) {
          throw new Error(
            "[Hook] BLOCKED: Dev server must run in tmux for log access\n" +
              '[Hook] Use: tmux new-session -d -s dev "npm run dev"\n' +
              "[Hook] Then: tmux attach -t dev",
          );
        }

        // Reminder for long-running commands
        if (LONG_RUNNING_PATTERN.test(command)) {
          console.error(
            "[Hook] Consider running in tmux for session persistence",
          );
          console.error("[Hook] tmux new -s dev  |  tmux attach -t dev");
        }

        // Reminder before git push
        if (GIT_PUSH_PATTERN.test(command)) {
          console.error("[Hook] Review changes before push...");
        }
      }

      // --- Strategic compact suggestion on edit/write ---
      if (tool === "edit" || tool === "write") {
        try {
          await $`python3 ${join(COMPACT_DIR, "suggest-compact.py")}`.quiet();
        } catch {
          // Non-critical
        }
      }
    },

    // ================================================================
    // Post-tool: code quality checks
    // Maps: Claude PostToolUse hooks for Edit tool
    // ================================================================
    "tool.execute.after": async (input) => {
      const tool = input.tool;
      const args = input.args as Record<string, unknown>;

      // --- Post-edit code quality checks ---
      if (tool === "edit" || tool === "write") {
        const filePath = (args.file_path || args.filePath) as string;
        if (!filePath) return;

        try {
          // JavaScript / TypeScript
          if (JS_TS_PATTERN.test(filePath)) {
            await $`node ${join(CODE_QUALITY_DIR, "format-js.js")}`.quiet();
            await $`node ${join(CODE_QUALITY_DIR, "warn-console-log.js")}`.quiet();
          }
          if (TS_ONLY_PATTERN.test(filePath)) {
            await $`node ${join(CODE_QUALITY_DIR, "check-typescript.js")}`.quiet();
          }

          // PHP
          if (PHP_PATTERN.test(filePath)) {
            await $`node ${join(CODE_QUALITY_DIR, "format-php.js")}`.quiet();
            await $`node ${join(CODE_QUALITY_DIR, "check-phpstan.js")}`.quiet();
            await $`node ${join(CODE_QUALITY_DIR, "warn-php-debug.js")}`.quiet();
          }

          // Python
          if (PYTHON_PATTERN.test(filePath)) {
            await $`node ${join(CODE_QUALITY_DIR, "format-python.js")}`.quiet();
            await $`node ${join(CODE_QUALITY_DIR, "check-mypy.js")}`.quiet();
            await $`node ${join(CODE_QUALITY_DIR, "warn-python-debug.js")}`.quiet();
          }
        } catch {
          // Non-critical: don't block on code quality check failures
        }
      }

      // --- PR URL detection after gh pr create ---
      if (tool === "bash") {
        const command = (args.command as string) || "";
        const output = (input as Record<string, unknown>).output as string || "";
        if (command.includes("gh pr create")) {
          const match = output.match(
            /https:\/\/github\.com\/[^/]+\/[^/]+\/pull\/\d+/,
          );
          if (match) {
            const parts = match[0].split("/");
            console.error(`[Hook] PR created: ${match[0]}`);
            console.error(
              `[Hook] To review: gh pr review ${parts[parts.length - 1]} --repo ${parts[3]}/${parts[4]}`,
            );
          }
        }
      }
    },

    // ================================================================
    // Compaction hook: preserve state before context compaction
    // Maps: Claude PreCompact hook
    // ================================================================
    "experimental.session.compacting": async (_input, output) => {
      try {
        await $`python3 ${join(MEMORY_DIR, "pre-compact.py")}`.quiet();
      } catch {
        // Non-critical
      }
    },
  };
};
