#!/usr/bin/env node
/**
 * Auto-format Python files with Ruff or Black after edit
 * PostToolUse hook for Edit tool on .py files
 */

const { processHook } = require('./lib/format-python');

let data = '';

process.stdin.on('data', (chunk) => {
  data += chunk;
});

process.stdin.on('end', () => {
  try {
    const input = JSON.parse(data);
    const result = processHook(input);

    if (result.message) {
      console.error(result.message);
    }
  } catch (e) {
    // JSON parse error - silently skip
  }

  console.log(data);
});
