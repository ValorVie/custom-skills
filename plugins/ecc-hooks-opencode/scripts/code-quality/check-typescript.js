#!/usr/bin/env node
/**
 * Run TypeScript type check on TS/TSX files
 * PostToolUse hook for Edit tool on .ts/.tsx files
 * Requires tsconfig.json in parent directory
 */

const { processHook } = require('./lib/check-typescript');

let data = '';

process.stdin.on('data', (chunk) => {
  data += chunk;
});

process.stdin.on('end', () => {
  try {
    const input = JSON.parse(data);
    const result = processHook(input);

    result.messages.forEach((m) => console.error(m));
  } catch (e) {
    // JSON parse error - silently skip
  }

  console.log(data);
});
