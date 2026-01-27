#!/usr/bin/env node
/**
 * Run mypy type check on Python files
 * PostToolUse hook for Edit tool on .py files
 * Requires pyproject.toml or mypy.ini in parent directory
 */

const { processHook } = require('./lib/check-mypy');

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
