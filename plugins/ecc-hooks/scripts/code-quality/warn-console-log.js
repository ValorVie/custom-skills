#!/usr/bin/env node
/**
 * Warn about console.log in JS/TS files after edit
 * PostToolUse hook for Edit tool on .ts/.tsx/.js/.jsx files
 */

const { processHook } = require('./lib/warn-console-log');

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
