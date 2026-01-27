/**
 * Core logic for warn-php-debug hook
 * Detects debug code in PHP files (var_dump/print_r/dd/dump/error_log/ray)
 */

const fs = require('fs');

const DEBUG_PATTERN = /\b(var_dump|print_r|dd|dump|error_log|ray)\s*\(/;

/**
 * Check file for PHP debug code
 * @param {string} filePath - Path to the file to check
 * @param {object} [deps] - Injectable dependencies for testing
 * @param {object} [deps.fs] - File system module
 * @returns {{found: boolean, matches: Array<{line: number, content: string}>}}
 */
function checkForDebugCode(filePath, deps = {}) {
  const _fs = deps.fs || fs;

  if (!filePath || !_fs.existsSync(filePath)) {
    return { found: false, matches: [] };
  }

  const content = _fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const matches = [];

  lines.forEach((line, idx) => {
    if (DEBUG_PATTERN.test(line)) {
      matches.push({ line: idx + 1, content: line.trim() });
    }
  });

  return {
    found: matches.length > 0,
    matches
  };
}

/**
 * Format warning messages for PHP debug code findings
 * @param {string} filePath - The file path
 * @param {Array<{line: number, content: string}>} matches - Found matches
 * @param {number} [maxLines=5] - Maximum lines to show
 * @returns {string[]} Array of warning messages
 */
function formatWarnings(filePath, matches, maxLines = 5) {
  if (!matches.length) return [];

  const warnings = [];
  warnings.push(`[Hook] WARNING: Debug code found in ${filePath}`);

  matches.slice(0, maxLines).forEach((m) => {
    warnings.push(`  L${m.line}: ${m.content}`);
  });

  warnings.push('[Hook] Remove var_dump/print_r/dd/dump/ray before committing');
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
  const result = checkForDebugCode(filePath, deps);
  const warnings = formatWarnings(filePath, result.matches);

  return { warnings };
}

module.exports = {
  checkForDebugCode,
  formatWarnings,
  processHook,
  DEBUG_PATTERN
};
