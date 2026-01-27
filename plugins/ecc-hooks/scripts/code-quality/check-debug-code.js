#!/usr/bin/env node
/**
 * Check for debug code in modified files (Stop hook)
 * JS/TS: console.log
 * PHP: var_dump/print_r/dd/dump/error_log/ray
 * Python: print/breakpoint/pdb/ic (excluding comments)
 */

const { processHook } = require('./lib/check-debug-code');

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
    // JSON parse error or other error - silently skip
  }

  console.log(data);
});
