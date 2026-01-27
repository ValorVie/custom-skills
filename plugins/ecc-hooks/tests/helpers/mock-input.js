/**
 * Create mock input for Claude Code hooks
 * @param {string} filePath - The file path to include in the mock input
 * @param {object} [options] - Additional options
 * @param {string} [options.tool] - The tool name (default: 'Edit')
 * @param {object} [options.toolOutput] - Additional tool output
 * @returns {object} Mock hook input object
 */
function createMockInput(filePath, options = {}) {
  const { tool = 'Edit', toolOutput = {} } = options;

  return {
    tool_name: tool,
    tool_input: {
      file_path: filePath
    },
    tool_output: toolOutput
  };
}

/**
 * Convert mock input to JSON string (for stdin simulation)
 * @param {string} filePath - The file path
 * @param {object} [options] - Additional options
 * @returns {string} JSON string
 */
function createMockInputString(filePath, options = {}) {
  return JSON.stringify(createMockInput(filePath, options));
}

module.exports = {
  createMockInput,
  createMockInputString
};
