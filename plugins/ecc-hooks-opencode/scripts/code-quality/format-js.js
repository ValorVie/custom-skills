#!/usr/bin/env node
/**
 * Auto-format JS/TS files with Prettier after edit
 * PostToolUse hook for Edit tool on .ts/.tsx/.js/.jsx files
 */

const { processHook } = require('./lib/format-js');

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
