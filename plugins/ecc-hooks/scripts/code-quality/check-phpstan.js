#!/usr/bin/env node
/**
 * Run PHPStan static analysis on PHP files
 * PostToolUse hook for Edit tool on .php files
 * Requires vendor/bin/phpstan in parent directory
 */

const { processHook } = require('./lib/check-phpstan');

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
