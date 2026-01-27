/**
 * Core logic for check-typescript hook
 * Run TypeScript type check on TS/TSX files
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * Find tsconfig.json in parent directories
 * @param {string} filePath - Path to the TypeScript file
 * @param {object} [deps] - Injectable dependencies
 * @returns {string|null} Directory containing tsconfig.json or null
 */
function findTsConfigDir(filePath, deps = {}) {
  const _fs = deps.fs || fs;

  if (!filePath) return null;

  let dir = path.dirname(filePath);
  const { root } = path.parse(dir);

  while (dir !== root) {
    if (_fs.existsSync(path.join(dir, 'tsconfig.json'))) {
      return dir;
    }
    dir = path.dirname(dir);
  }

  return null;
}

/**
 * Run TypeScript type check
 * @param {string} filePath - Path to the file to check
 * @param {object} [deps] - Injectable dependencies
 * @returns {{hasErrors: boolean, errors: string[]}}
 */
function checkTypeScript(filePath, deps = {}) {
  const _execSync = deps.execSync || execSync;

  if (!filePath) {
    return { hasErrors: false, errors: [] };
  }

  const tsConfigDir = findTsConfigDir(filePath, deps);
  if (!tsConfigDir) {
    return { hasErrors: false, errors: [] };
  }

  try {
    _execSync('npx tsc --noEmit 2>&1', {
      cwd: tsConfigDir,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 60000
    });
    return { hasErrors: false, errors: [] };
  } catch (e) {
    const lines = (e.stdout || '')
      .split('\n')
      .filter((l) => l.includes(path.basename(filePath)))
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
  messages.push(`[Hook] TypeScript errors in ${filePath}:`);
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
  const result = checkTypeScript(filePath, deps);
  const messages = formatErrors(filePath, result.errors);

  return { hasErrors: result.hasErrors, messages };
}

module.exports = {
  findTsConfigDir,
  checkTypeScript,
  formatErrors,
  processHook
};
