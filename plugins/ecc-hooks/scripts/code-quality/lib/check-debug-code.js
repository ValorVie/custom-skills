/**
 * Core logic for check-debug-code hook (Stop hook)
 * Check for debug code in modified files
 * - JS/TS: console.log
 * - PHP: var_dump/print_r/dd/dump/error_log/ray
 * - Python: print/breakpoint/pdb/ic (excluding comments)
 */

const fs = require('fs');
const { execSync } = require('child_process');

/**
 * Check if we're in a git repository
 * @param {object} [deps] - Injectable dependencies
 * @returns {boolean}
 */
function isGitRepo(deps = {}) {
  const _execSync = deps.execSync || execSync;

  try {
    _execSync('git rev-parse --git-dir', {
      stdio: ['pipe', 'pipe', 'pipe']
    });
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Get list of modified files
 * @param {object} [deps] - Injectable dependencies
 * @returns {string[]}
 */
function getModifiedFiles(deps = {}) {
  const _fs = deps.fs || fs;
  const _execSync = deps.execSync || execSync;

  try {
    const files = _execSync('git diff --name-only HEAD', {
      encoding: 'utf8',
      timeout: 5000
    })
      .split('\n')
      .filter((f) => f && _fs.existsSync(f));

    return files;
  } catch (e) {
    return [];
  }
}

/**
 * Check JS/TS file for console.log
 * @param {string} filePath - Path to the file
 * @param {object} [deps] - Injectable dependencies
 * @returns {boolean}
 */
function hasJsDebugCode(filePath, deps = {}) {
  const _fs = deps.fs || fs;
  const content = _fs.readFileSync(filePath, 'utf8');
  return /console\.log/.test(content);
}

/**
 * Check PHP file for debug code
 * @param {string} filePath - Path to the file
 * @param {object} [deps] - Injectable dependencies
 * @returns {boolean}
 */
function hasPhpDebugCode(filePath, deps = {}) {
  const _fs = deps.fs || fs;
  const content = _fs.readFileSync(filePath, 'utf8');
  return /\b(var_dump|print_r|dd|dump|error_log|ray)\s*\(/.test(content);
}

/**
 * Check Python file for debug code (excluding comments)
 * @param {string} filePath - Path to the file
 * @param {object} [deps] - Injectable dependencies
 * @returns {boolean}
 */
function hasPythonDebugCode(filePath, deps = {}) {
  const _fs = deps.fs || fs;
  const content = _fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');

  return lines.some((line) => {
    if (/^\s*#/.test(line)) return false;
    return (
      /\b(print|pprint)\s*\(/.test(line) ||
      /\bbreakpoint\s*\(/.test(line) ||
      /\bpdb\./.test(line) ||
      /\bic\s*\(/.test(line)
    );
  });
}

/**
 * Check all modified files for debug code
 * @param {object} [deps] - Injectable dependencies
 * @returns {string[]} Array of warning messages
 */
function checkAllFiles(deps = {}) {
  if (!isGitRepo(deps)) {
    return [];
  }

  const files = getModifiedFiles(deps);
  const jsFiles = files.filter((f) => /\.(ts|tsx|js|jsx)$/.test(f));
  const phpFiles = files.filter((f) => /\.php$/.test(f));
  const pyFiles = files.filter((f) => /\.py$/.test(f));

  const warnings = [];

  jsFiles.forEach((f) => {
    if (hasJsDebugCode(f, deps)) {
      warnings.push(`[Hook] WARNING: console.log found in ${f}`);
    }
  });

  phpFiles.forEach((f) => {
    if (hasPhpDebugCode(f, deps)) {
      warnings.push(`[Hook] WARNING: Debug code (var_dump/dd/dump/ray) found in ${f}`);
    }
  });

  pyFiles.forEach((f) => {
    if (hasPythonDebugCode(f, deps)) {
      warnings.push(`[Hook] WARNING: Debug code (print/breakpoint/pdb/ic) found in ${f}`);
    }
  });

  return warnings;
}

/**
 * Process hook input and return result
 * @param {object} input - Hook input object (not used for Stop hook)
 * @param {object} [deps] - Injectable dependencies
 * @returns {{warnings: string[]}}
 */
function processHook(input, deps = {}) {
  const warnings = checkAllFiles(deps);
  return { warnings };
}

module.exports = {
  isGitRepo,
  getModifiedFiles,
  hasJsDebugCode,
  hasPhpDebugCode,
  hasPythonDebugCode,
  checkAllFiles,
  processHook
};
