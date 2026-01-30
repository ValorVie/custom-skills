const {
  findProjectRoot,
  formatPhpFile,
  processHook
} = require('../../scripts/code-quality/lib/format-php');
const { runScript } = require('../helpers/run-script');
const { createMockInput } = require('../helpers/mock-input');

describe('format-php (unit tests)', () => {
  describe('findProjectRoot', () => {
    test('should find root with pint', () => {
      const mockFs = {
        existsSync: (path) => path.includes('vendor/bin/pint')
      };

      const root = findProjectRoot('/project/app/Models/User.php', { fs: mockFs });

      expect(root).toBeTruthy();
    });

    test('should return null when no formatter found', () => {
      const mockFs = { existsSync: () => false };

      const root = findProjectRoot('/project/app/User.php', { fs: mockFs });

      expect(root).toBeNull();
    });
  });

  describe('formatPhpFile', () => {
    test('should format with Pint', () => {
      const mockFs = {
        existsSync: (path) => path.includes('vendor/bin/pint')
      };
      const mockExecSync = jest.fn();

      const result = formatPhpFile('/project/app/User.php', {
        fs: mockFs,
        execFileSync: mockExecSync
      });

      expect(result.success).toBe(true);
      expect(result.formatter).toBe('Pint');
    });

    test('should handle null file path', () => {
      const result = formatPhpFile(null);

      expect(result.success).toBe(false);
    });
  });

  describe('processHook', () => {
    test('should handle missing tool_input', () => {
      const result = processHook({});

      expect(result.success).toBe(false);
    });
  });
});

describe('format-php (integration tests)', () => {
  test('should output original input', async () => {
    const input = createMockInput('/path/to/file.php');
    const result = await runScript('code-quality/format-php.js', input);

    expect(result.stdout).toBe(JSON.stringify(input));
    expect(result.exitCode).toBe(0);
  });
});
