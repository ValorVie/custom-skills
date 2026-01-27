#!/usr/bin/env node
/**
 * Warn about debug code (print/breakpoint/pdb/ic) in Python files after edit
 * PostToolUse hook for Edit tool on .py files
 */

const { processHook } = require('./lib/warn-python-debug');

let data = '';

process.stdin.on('data', (chunk) => {
  data += chunk;
});

process.stdin.on('end', () => {
  try {
    const input = JSON.parse(data);
    const { warnings } = processHook(input);

    warnings.forEach((w) => console.error(w));
  } catch (e) {
    // JSON parse error - silently skip
  }

  console.log(data);
});
