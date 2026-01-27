#!/usr/bin/env node
/**
 * Warn about debug code (var_dump/print_r/dd/dump/ray) in PHP files after edit
 * PostToolUse hook for Edit tool on .php files
 */

const { processHook } = require('./lib/warn-php-debug');

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
