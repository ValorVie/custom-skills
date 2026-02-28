import type { Command } from "commander";

import { createProgram } from "../../../src/cli/index";

export type NonHelpCase = {
  id: string;
  args: string[];
};

export type CommandNode = {
  path: string[];
  requiredArgCount: number;
};

function pathToId(path: string[]): string {
  if (path.length === 0) {
    return "root";
  }
  return path.join("-");
}

function countRequiredArgs(command: Command): number {
  return command.registeredArguments.filter((argument) => argument.required)
    .length;
}

export function listCommandNodes(): CommandNode[] {
  const program = createProgram();
  const nodes: CommandNode[] = [];

  function walk(command: Command, path: string[]): void {
    for (const subcommand of command.commands) {
      const subPath = [...path, subcommand.name()];
      nodes.push({
        path: subPath,
        requiredArgCount: countRequiredArgs(subcommand),
      });
      walk(subcommand, subPath);
    }
  }

  walk(program, []);
  return nodes;
}

function dedupeCases(cases: NonHelpCase[]): NonHelpCase[] {
  const map = new Map<string, NonHelpCase>();
  for (const item of cases) {
    map.set(item.id, item);
  }
  return [...map.values()];
}

export function buildNonHelpCommandMatrix(): NonHelpCase[] {
  const nodes = listCommandNodes();
  const matrix: NonHelpCase[] = [
    { id: "version-long", args: ["--version"] },
    { id: "version-short", args: ["-v"] },
    { id: "derive-tests-single-file", args: ["derive-tests", "__SPEC_FILE__"] },
    { id: "derive-tests-missing-path", args: ["derive-tests", "__MISSING_SPEC__"] },
    { id: "root-invalid-option", args: ["--parity-probe"] },
  ];

  for (const node of nodes) {
    const nodeId = pathToId(node.path);
    matrix.push({
      id: `${nodeId}-invalid-option`,
      args: [...node.path, "--parity-probe"],
    });

    if (node.requiredArgCount > 0) {
      matrix.push({
        id: `${nodeId}-missing-required-args`,
        args: [...node.path],
      });
    }
  }

  const PRIORITY_IDS = [
    "version-long",
    "version-short",
    "derive-tests-single-file",
    "derive-tests-missing-path",
    "root-invalid-option",
  ];
  const priorityMap = new Map(PRIORITY_IDS.map((id, index) => [id, index]));

  const deduped = dedupeCases(matrix);
  deduped.sort((left, right) => {
    const leftPriority = priorityMap.get(left.id) ?? Number.MAX_SAFE_INTEGER;
    const rightPriority = priorityMap.get(right.id) ?? Number.MAX_SAFE_INTEGER;
    if (leftPriority !== rightPriority) {
      return leftPriority - rightPriority;
    }
    return left.id.localeCompare(right.id);
  });

  return deduped;
}
