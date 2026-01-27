const {
  formatWithPrettier,
  processHook
} = require('../../scripts/code-quality/lib/format-js');
const { runScript } = require('../helpers/run-script');
const { createMockInput } = require('../helpers/mock-input');

describe('format-js (unit tests)', () => {
  describe('formatWithPrettier', () => {
    test('should format file successfully', () => {
      const mockExecSync = jest.fn();

      const result = formatWithPrettier('/path/to/file.js', { execSync: mockExecSync });

      expect(result.success).toBe(true);
      expect(result.message).toContain('Formatted with Prettier');
    });

    test('should handle prettier not available', () => {
      const mockExecSync = jest.fn(() => {
        throw new Error('npx: prettier not found');
      });

      const result = formatWithPrettier('/path/to/file.js', { execSync: mockExecSync });

      expect(result.success).toBe(false);
      expect(result.message).toBe('');
    });

    test('should handle null file path', () => {
      const result = formatWithPrettier(null);

      expect(result.success).toBe(false);
    });
  });

  describe('processHook', () => {
    test('should process valid input', () => {
      const mockExecSync = jest.fn();

      const result = processHook(
        { tool_input: { file_path: '/file.js' } },
        { execSync: mockExecSync }
      );

      expect(result.success).toBe(true);
    });

    test('should handle missing tool_input', () => {
      const result = processHook({});

      expect(result.success).toBe(false);
    });
  });
});

describe('format-js (integration tests)', () => {
  test('should output original input', async () => {
    const input = createMockInput('/path/to/file.js');
    const result = await runScript('code-quality/format-js.js', input);

    expect(result.stdout).toBe(JSON.stringify(input));
    expect(result.exitCode).toBe(0);
  });
});
