const {
  isDebugLine,
  checkForDebugCode,
  formatWarnings,
  processHook
} = require('../../scripts/code-quality/lib/warn-python-debug');
const { runScript } = require('../helpers/run-script');
const { createMockInput } = require('../helpers/mock-input');

describe('warn-python-debug (unit tests)', () => {
  describe('isDebugLine', () => {
    test('should detect print()', () => {
      expect(isDebugLine('print("debug")')).toBe(true);
    });

    test('should detect breakpoint()', () => {
      expect(isDebugLine('breakpoint()')).toBe(true);
    });

    test('should detect pdb', () => {
      expect(isDebugLine('pdb.set_trace()')).toBe(true);
    });

    test('should detect ic()', () => {
      expect(isDebugLine('ic(value)')).toBe(true);
    });

    test('should ignore comment lines', () => {
      expect(isDebugLine('# print("commented")')).toBe(false);
      expect(isDebugLine('  # breakpoint()')).toBe(false);
    });

    test('should not match regular code', () => {
      expect(isDebugLine('return result')).toBe(false);
    });
  });

  describe('checkForDebugCode', () => {
    test('should detect print in file', () => {
      const mockFs = {
        existsSync: () => true,
        readFileSync: () => 'def main():\n    print("test")'
      };

      const result = checkForDebugCode('/path/to/file.py', { fs: mockFs });

      expect(result.found).toBe(true);
      expect(result.matches).toHaveLength(1);
    });

    test('should exclude commented print', () => {
      const mockFs = {
        existsSync: () => true,
        readFileSync: () => '# print("commented")\ndef main():\n    return True'
      };

      const result = checkForDebugCode('/path/to/file.py', { fs: mockFs });

      expect(result.found).toBe(false);
    });
  });

  describe('processHook', () => {
    test('should process input with debug code', () => {
      const mockFs = {
        existsSync: () => true,
        readFileSync: () => 'print("test")'
      };

      const result = processHook(
        { tool_input: { file_path: '/file.py' } },
        { fs: mockFs }
      );

      expect(result.warnings.length).toBeGreaterThan(0);
    });

    test('should handle null input', () => {
      const result = processHook(null);
      expect(result.warnings).toHaveLength(0);
    });
  });
});

describe('warn-python-debug (integration tests)', () => {
  test('should output original input', async () => {
    const input = createMockInput('/path/to/file.py');
    const result = await runScript('code-quality/warn-python-debug.js', input);

    expect(result.stdout).toBe(JSON.stringify(input));
    expect(result.exitCode).toBe(0);
  });
});
