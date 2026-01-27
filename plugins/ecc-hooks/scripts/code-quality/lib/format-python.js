/**
 * Core logic for format-python hook
 * Auto-format Python files with Ruff or Black
 */

const { execSync } = require('child_process');

/**
 * Format a Python file with Ruff or Black
 * @param {string} filePath - Path to the file to format
 * @param {object} [deps] - Injectable dependencies
 * @returns {{success: boolean, formatter: string|null, message: string}}
 */
function formatPythonFile(filePath, deps = {}) {
  const _execSync = deps.execSync || execSync;

  if (!filePath) {
    return { success: false, formatter: null, message: '' };
  }

  // Try Ruff first
  try {
    _execSync(`ruff format ${JSON.stringify(filePath)}`, {
      stdio: ['pipe', 'pipe', 'pipe']
    });
    return {
      success: true,
      formatter: 'Ruff',
      message: `[Hook] Formatted with Ruff: ${filePath}`
    };
  } catch (e) {
    // Ruff not available - try Black
  }

  // Fall back to Black
  try {
    _execSync(`black ${JSON.stringify(filePath)}`, {
      stdio: ['pipe', 'pipe', 'pipe']
    });
    return {
      success: true,
      formatter: 'Black',
      message: `[Hook] Formatted with Black: ${filePath}`
    };
  } catch (e) {
    // Black not available
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
  return formatPythonFile(filePath, deps);
}

module.exports = {
  formatPythonFile,
  processHook
};
