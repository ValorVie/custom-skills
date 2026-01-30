/**
 * Core logic for check-phpstan hook
 * Run PHPStan static analysis on PHP files
 */

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

/**
 * Find project root with PHPStan
 * @param {string} filePath - Path to the PHP file
 * @param {object} [deps] - Injectable dependencies
 * @returns {string|null} Project root path or null
 */
function findPhpStanRoot(filePath, deps = {}) {
  const _fs = deps.fs || fs;

  if (!filePath) return null;

  let dir = path.dirname(filePath);
  const { root } = path.parse(dir);

  while (dir !== root) {
    if (_fs.existsSync(path.join(dir, 'vendor/bin/phpstan'))) {
      return dir;
    }
    dir = path.dirname(dir);
  }

  return null;
}

/**
 * Run PHPStan analysis
 * @param {string} filePath - Path to the file to check
 * @param {object} [deps] - Injectable dependencies
 * @returns {{hasErrors: boolean, errors: string[]}}
 */
function runPhpStan(filePath, deps = {}) {
  const _execFileSync = deps.execFileSync || execFileSync;

  if (!filePath) {
    return { hasErrors: false, errors: [] };
  }

  const root = findPhpStanRoot(filePath, deps);
  if (!root) {
    return { hasErrors: false, errors: [] };
  }

  try {
    _execFileSync(
      path.join(root, 'vendor/bin/phpstan'),
      ['analyse', '--error-format=raw', filePath],
      {
        cwd: root,
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 60000
      }
    );
    return { hasErrors: false, errors: [] };
  } catch (e) {
    const lines = (e.stdout || '')
      .split('\n')
      .filter((l) => l.trim())
      .slice(0, 10);

    return {
      hasErrors: lines.length > 0,
      errors: lines
    };
  }
}

/**
 * Format error messages
 * @param {string} filePath - The file path
 * @param {string[]} errors - Error messages
 * @returns {string[]} Formatted error messages
 */
function formatErrors(filePath, errors) {
  if (!errors.length) return [];

  const messages = [];
  messages.push(`[Hook] PHPStan errors in ${filePath}:`);
  errors.forEach((e) => messages.push(`  ${e}`));
  return messages;
}

/**
 * Process hook input and return result
 * @param {object} input - Hook input object
 * @param {object} [deps] - Injectable dependencies
 * @returns {{hasErrors: boolean, messages: string[]}}
 */
function processHook(input, deps = {}) {
  const filePath = input?.tool_input?.file_path;
  const result = runPhpStan(filePath, deps);
  const messages = formatErrors(filePath, result.errors);

  return { hasErrors: result.hasErrors, messages };
}

module.exports = {
  findPhpStanRoot,
  runPhpStan,
  formatErrors,
  processHook
};
