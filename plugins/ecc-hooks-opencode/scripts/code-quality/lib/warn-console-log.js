/**
 * Core logic for warn-console-log hook
 * Detects console.log in JS/TS files and outputs warnings
 */

const fs = require('fs');

/**
 * Check file for console.log statements
 * @param {string} filePath - Path to the file to check
 * @param {object} [deps] - Injectable dependencies for testing
 * @param {object} [deps.fs] - File system module
 * @returns {{found: boolean, matches: Array<{line: number, content: string}>}}
 */
function checkForConsoleLog(filePath, deps = {}) {
  const _fs = deps.fs || fs;

  if (!filePath || !_fs.existsSync(filePath)) {
    return { found: false, matches: [] };
  }

  const content = _fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const matches = [];

  lines.forEach((line, idx) => {
    if (/console\.log/.test(line)) {
      matches.push({ line: idx + 1, content: line.trim() });
    }
  });

  return {
    found: matches.length > 0,
    matches
  };
}

/**
 * Format warning messages for console.log findings
 * @param {string} filePath - The file path
 * @param {Array<{line: number, content: string}>} matches - Found matches
 * @param {number} [maxLines=5] - Maximum lines to show
 * @returns {string[]} Array of warning messages
 */
function formatWarnings(filePath, matches, maxLines = 5) {
  if (!matches.length) return [];

  const warnings = [];
  warnings.push(`[Hook] WARNING: console.log found in ${filePath}`);

  matches.slice(0, maxLines).forEach((m) => {
    warnings.push(`  L${m.line}: ${m.content}`);
  });

  warnings.push('[Hook] Remove before committing');
  return warnings;
}

/**
 * Process hook input and return result
 * @param {object} input - Hook input object
 * @param {object} [deps] - Injectable dependencies
 * @returns {{warnings: string[]}}
 */
function processHook(input, deps = {}) {
  const filePath = input?.tool_input?.file_path;
  const result = checkForConsoleLog(filePath, deps);
  const warnings = formatWarnings(filePath, result.matches);

  return { warnings };
}

module.exports = {
  checkForConsoleLog,
  formatWarnings,
  processHook
};
