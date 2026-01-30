/**
 * Core logic for check-mypy hook
 * Run mypy type check on Python files
 */

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

/**
 * Find directory with mypy config
 * @param {string} filePath - Path to the Python file
 * @param {object} [deps] - Injectable dependencies
 * @returns {string|null} Directory containing config or null
 */
function findMypyConfigDir(filePath, deps = {}) {
  const _fs = deps.fs || fs;

  if (!filePath) return null;

  let dir = path.dirname(filePath);
  const { root } = path.parse(dir);

  while (dir !== root) {
    if (
      _fs.existsSync(path.join(dir, 'pyproject.toml')) ||
      _fs.existsSync(path.join(dir, 'mypy.ini'))
    ) {
      return dir;
    }
    dir = path.dirname(dir);
  }

  return null;
}

/**
 * Run mypy type check
 * @param {string} filePath - Path to the file to check
 * @param {object} [deps] - Injectable dependencies
 * @returns {{hasErrors: boolean, errors: string[]}}
 */
function runMypy(filePath, deps = {}) {
  const _execFileSync = deps.execFileSync || execFileSync;

  if (!filePath) {
    return { hasErrors: false, errors: [] };
  }

  const configDir = findMypyConfigDir(filePath, deps);
  if (!configDir) {
    return { hasErrors: false, errors: [] };
  }

  try {
    _execFileSync('mypy', ['--no-error-summary', filePath], {
      cwd: configDir,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 60000
    });
    return { hasErrors: false, errors: [] };
  } catch (e) {
    const out = (e.stdout || '') + (e.stderr || '');
    const lines = out
      .split('\n')
      .filter((l) => /: error:/.test(l))
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
  messages.push(`[Hook] mypy errors in ${filePath}:`);
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
  const result = runMypy(filePath, deps);
  const messages = formatErrors(filePath, result.errors);

  return { hasErrors: result.hasErrors, messages };
}

module.exports = {
  findMypyConfigDir,
  runMypy,
  formatErrors,
  processHook
};
