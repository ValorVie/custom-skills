/**
 * Core logic for check-debug-code hook (Stop hook)
 * Check for debug code in modified files
 * - JS/TS: console.log
 * - PHP: var_dump/print_r/dd/dump/error_log/ray
 * - Python: print/breakpoint/pdb/ic (excluding comments)
 */

const fs = require('fs');
const { execFileSync } = require('child_process');

/**
 * Check if we're in a git repository
 * @param {object} [deps] - Injectable dependencies
 * @returns {boolean}
 */
function isGitRepo(deps = {}) {
  const _execFileSync = deps.execFileSync || execFileSync;

  try {
    _execFileSync('git', ['rev-parse', '--git-dir'], {
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
  const _execFileSync = deps.execFileSync || execFileSync;

  try {
    const files = _execFileSync('git', ['diff', '--name-only', 'HEAD'], {
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
 * Check JS/TS file for console.log (excluding comments)
 * @param {string} filePath - Path to the file
 * @param {object} [deps] - Injectable dependencies
 * @returns {boolean}
 */
function hasJsDebugCode(filePath, deps = {}) {
  const _fs = deps.fs || fs;
  const content = _fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  let inBlockComment = false;

  return lines.some((line) => {
    // Track block comment state
    if (inBlockComment) {
      if (line.includes('*/')) {
        inBlockComment = false;
        // Check remaining content after block comment ends
        const afterComment = line.substring(line.indexOf('*/') + 2);
        if (/^\s*\/\//.test(afterComment)) return false;
        return /console\.log/.test(afterComment);
      }
      return false;
    }

    // Check for block comment start
    if (line.includes('/*') && !line.includes('*/')) {
      inBlockComment = true;
      // Check content before block comment
      const beforeComment = line.substring(0, line.indexOf('/*'));
      if (/^\s*\/\//.test(line)) return false;
      return /console\.log/.test(beforeComment);
    }

    // Skip single-line comments
    const trimmed = line.trim();
    if (trimmed.startsWith('//')) return false;

    // Handle inline block comments /* ... */ on same line
    const withoutBlockComments = line.replace(/\/\*.*?\*\//g, '');

    // Skip if line is mostly a comment
    if (/^\s*\/\//.test(withoutBlockComments)) return false;

    return /console\.log/.test(withoutBlockComments);
  });
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
 * Supports detection of import aliases like `from pdb import set_trace`
 * @param {string} filePath - Path to the file
 * @param {object} [deps] - Injectable dependencies
 * @returns {boolean}
 */
function hasPythonDebugCode(filePath, deps = {}) {
  const _fs = deps.fs || fs;
  const content = _fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');

  // Track imported debug functions
  const importedDebugFuncs = new Set();

  // Debug import patterns
  const debugImportPatterns = [
    /from\s+pdb\s+import\s+(.+)/,
    /from\s+ipdb\s+import\s+(.+)/,
    /from\s+pudb\s+import\s+(.+)/,
    /from\s+icecream\s+import\s+(.+)/,
    /from\s+pprint\s+import\s+(.+)/,
    /from\s+rich\s+import\s+print/
  ];

  return lines.some((line) => {
    // Skip comments
    if (/^\s*#/.test(line)) return false;

    // Check for debug imports and track them
    for (const pattern of debugImportPatterns) {
      const match = line.match(pattern);
      if (match) {
        // Parse imported names (handle 'as' aliases and multiple imports)
        const imports = match[1].split(',').map((s) => {
          const parts = s.trim().split(/\s+as\s+/);
          return parts[parts.length - 1].trim();
        });
        imports.forEach((name) => importedDebugFuncs.add(name));
        return true; // Import of debug tool is itself a warning
      }
    }

    // Check for standard debug patterns
    if (
      /\b(print|pprint)\s*\(/.test(line) ||
      /\bbreakpoint\s*\(/.test(line) ||
      /\bpdb\./.test(line) ||
      /\bipdb\./.test(line) ||
      /\bpudb\./.test(line) ||
      /\bic\s*\(/.test(line)
    ) {
      return true;
    }

    // Check for imported debug function calls
    for (const func of importedDebugFuncs) {
      const pattern = new RegExp(`\\b${func}\\s*\\(`);
      if (pattern.test(line)) {
        return true;
      }
    }

    return false;
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
