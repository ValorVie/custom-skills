#!/usr/bin/env bun

import { maybePrintV1HelpSnapshot } from "./cli/help-compat";
import { run } from "./cli/index";

const argv = process.argv.slice(2);
if (!(await maybePrintV1HelpSnapshot(argv))) {
  await run();
}
