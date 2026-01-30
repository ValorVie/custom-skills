#!/usr/bin/env node
/**
 * Auto-format PHP files with Pint or PHP-CS-Fixer after edit
 * PostToolUse hook for Edit tool on .php files
 */

const { processHook } = require('./lib/format-php');

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
