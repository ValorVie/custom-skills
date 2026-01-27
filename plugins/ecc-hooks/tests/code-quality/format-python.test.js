const {
  formatPythonFile,
  processHook
} = require('../../scripts/code-quality/lib/format-python');
const { runScript } = require('../helpers/run-script');
const { createMockInput } = require('../helpers/mock-input');

describe('format-python (unit tests)', () => {
  describe('formatPythonFile', () => {
    test('should format with Ruff', () => {
      const mockExecSync = jest.fn();

      const result = formatPythonFile('/path/to/file.py', { execSync: mockExecSync });

      expect(result.success).toBe(true);
      expect(result.formatter).toBe('Ruff');
    });

    test('should fall back to Black when Ruff fails', () => {
      let callCount = 0;
      const mockExecSync = jest.fn(() => {
        callCount++;
        if (callCount === 1) throw new Error('ruff not found');
        return '';
      });

      const result = formatPythonFile('/path/to/file.py', { execSync: mockExecSync });

      expect(result.success).toBe(true);
      expect(result.formatter).toBe('Black');
    });

    test('should handle no formatter available', () => {
      const mockExecSync = jest.fn(() => {
        throw new Error('not found');
      });

      const result = formatPythonFile('/path/to/file.py', { execSync: mockExecSync });

      expect(result.success).toBe(false);
      expect(result.formatter).toBeNull();
    });

    test('should handle null file path', () => {
      const result = formatPythonFile(null);

      expect(result.success).toBe(false);
    });
  });

  describe('processHook', () => {
    test('should process valid input', () => {
      const mockExecSync = jest.fn();

      const result = processHook(
        { tool_input: { file_path: '/file.py' } },
        { execSync: mockExecSync }
      );

      expect(result.success).toBe(true);
    });
  });
});

describe('format-python (integration tests)', () => {
  test('should output original input', async () => {
    const input = createMockInput('/path/to/file.py');
    const result = await runScript('code-quality/format-python.js', input);

    expect(result.stdout).toBe(JSON.stringify(input));
    expect(result.exitCode).toBe(0);
  });
});
