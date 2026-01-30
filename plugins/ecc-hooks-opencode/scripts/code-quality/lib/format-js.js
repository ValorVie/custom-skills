/**
 * Core logic for format-js hook
 * Auto-format JS/TS files with Prettier
 */

const { execFileSync } = require('child_process');

/**
 * Format a file with Prettier
 * @param {string} filePath - Path to the file to format
 * @param {object} [deps] - Injectable dependencies for testing
 * @param {function} [deps.execFileSync] - execFileSync function
 * @returns {{success: boolean, message: string}}
 */
function formatWithPrettier(filePath, deps = {}) {
  const _execFileSync = deps.execFileSync || execFileSync;

  if (!filePath) {
    return { success: false, message: '' };
  }

  try {
    _execFileSync('npx', ['prettier', '--write', filePath], {
      stdio: ['pipe', 'pipe', 'pipe']
    });
    return {
      success: true,
      message: `[Hook] Formatted with Prettier: ${filePath}`
    };
  } catch (e) {
    return { success: false, message: '' };
  }
}

/**
 * Process hook input and return result
 * @param {object} input - Hook input object
 * @param {object} [deps] - Injectable dependencies
 * @returns {{success: boolean, message: string}}
 */
function processHook(input, deps = {}) {
  const filePath = input?.tool_input?.file_path;
  return formatWithPrettier(filePath, deps);
}

module.exports = {
  formatWithPrettier,
  processHook
};
