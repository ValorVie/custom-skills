/**
 * Core logic for format-php hook
 * Auto-format PHP files with Pint or PHP-CS-Fixer
 */

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

/**
 * Find project root with Pint or PHP-CS-Fixer
 * @param {string} filePath - Path to the PHP file
 * @param {object} [deps] - Injectable dependencies
 * @returns {string|null} Project root path or null
 */
function findProjectRoot(filePath, deps = {}) {
  const _fs = deps.fs || fs;

  if (!filePath) return null;

  let dir = path.dirname(filePath);

  while (dir !== '/') {
    if (
      _fs.existsSync(path.join(dir, 'vendor/bin/pint')) ||
      _fs.existsSync(path.join(dir, '.php-cs-fixer.php')) ||
      _fs.existsSync(path.join(dir, '.php-cs-fixer.dist.php'))
    ) {
      return dir;
    }
    dir = path.dirname(dir);
  }

  return null;
}

/**
 * Format a PHP file
 * @param {string} filePath - Path to the file to format
 * @param {object} [deps] - Injectable dependencies
 * @returns {{success: boolean, formatter: string|null, message: string}}
 */
function formatPhpFile(filePath, deps = {}) {
  const _fs = deps.fs || fs;
  const _execFileSync = deps.execFileSync || execFileSync;

  if (!filePath) {
    return { success: false, formatter: null, message: '' };
  }

  const root = findProjectRoot(filePath, deps);
  if (!root) {
    return { success: false, formatter: null, message: '' };
  }

  const pint = path.join(root, 'vendor/bin/pint');
  const fixer = path.join(root, 'vendor/bin/php-cs-fixer');

  if (_fs.existsSync(pint)) {
    try {
      _execFileSync(pint, [filePath], {
        cwd: root,
        stdio: ['pipe', 'pipe', 'pipe']
      });
      return {
        success: true,
        formatter: 'Pint',
        message: `[Hook] Formatted with Pint: ${filePath}`
      };
    } catch (e) {
      return { success: false, formatter: null, message: '' };
    }
  }

  if (_fs.existsSync(fixer)) {
    try {
      _execFileSync(fixer, ['fix', filePath], {
        cwd: root,
        stdio: ['pipe', 'pipe', 'pipe']
      });
      return {
        success: true,
        formatter: 'PHP-CS-Fixer',
        message: `[Hook] Formatted with PHP-CS-Fixer: ${filePath}`
      };
    } catch (e) {
      return { success: false, formatter: null, message: '' };
    }
  }

  return { success: false, formatter: null, message: '' };
}

/**
 * Process hook input and return result
 * @param {object} input - Hook input object
 * @param {object} [deps] - Injectable dependencies
 * @returns {{success: boolean, formatter: string|null, message: string}}
 */
function processHook(input, deps = {}) {
  const filePath = input?.tool_input?.file_path;
  return formatPhpFile(filePath, deps);
}

module.exports = {
  findProjectRoot,
  formatPhpFile,
  processHook
};
