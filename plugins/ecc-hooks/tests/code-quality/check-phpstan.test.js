const {
  findPhpStanRoot,
  runPhpStan,
  formatErrors,
  processHook
} = require('../../scripts/code-quality/lib/check-phpstan');
const { runScript } = require('../helpers/run-script');
const { createMockInput } = require('../helpers/mock-input');

describe('check-phpstan (unit tests)', () => {
  describe('findPhpStanRoot', () => {
    test('should find root with phpstan', () => {
      const mockFs = {
        existsSync: (path) => path.includes('vendor/bin/phpstan')
      };

      const root = findPhpStanRoot('/project/app/User.php', { fs: mockFs });

      expect(root).toBeTruthy();
    });

    test('should return null when no phpstan found', () => {
      const mockFs = { existsSync: () => false };

      const root = findPhpStanRoot('/project/app/User.php', { fs: mockFs });

      expect(root).toBeNull();
    });

    test('should handle null file path', () => {
      const root = findPhpStanRoot(null);

      expect(root).toBeNull();
    });
  });

  describe('runPhpStan', () => {
    test('should return no errors when phpstan passes', () => {
      const mockFs = {
        existsSync: (path) => path.includes('vendor/bin/phpstan')
      };
      const mockExecSync = jest.fn();

      const result = runPhpStan('/project/app/User.php', {
        fs: mockFs,
        execFileSync: mockExecSync
      });

      expect(result.hasErrors).toBe(false);
      expect(result.errors).toHaveLength(0);
    });

    test('should return errors when phpstan fails', () => {
      const mockFs = {
        existsSync: (path) => path.includes('vendor/bin/phpstan')
      };
      const mockExecSync = jest.fn(() => {
        const error = new Error('phpstan failed');
        error.stdout = '/project/app/User.php:10: Property not found';
        throw error;
      });

      const result = runPhpStan('/project/app/User.php', {
        fs: mockFs,
        execFileSync: mockExecSync
      });

      expect(result.hasErrors).toBe(true);
      expect(result.errors).toHaveLength(1);
    });

    test('should handle null file path', () => {
      const result = runPhpStan(null);

      expect(result.hasErrors).toBe(false);
      expect(result.errors).toHaveLength(0);
    });

    test('should return no errors when no phpstan root found', () => {
      const mockFs = { existsSync: () => false };

      const result = runPhpStan('/project/app/User.php', { fs: mockFs });

      expect(result.hasErrors).toBe(false);
    });
  });

  describe('formatErrors', () => {
    test('should format errors correctly', () => {
      const errors = ['/project/app/User.php:10: Property not found'];

      const messages = formatErrors('/path/to/file.php', errors);

      expect(messages[0]).toContain('PHPStan errors');
      expect(messages[1]).toContain('Property not found');
    });

    test('should return empty array when no errors', () => {
      const messages = formatErrors('/path/to/file.php', []);

      expect(messages).toHaveLength(0);
    });
  });

  describe('processHook', () => {
    test('should process valid input', () => {
      const mockFs = { existsSync: () => false };

      const result = processHook(
        { tool_input: { file_path: '/file.php' } },
        { fs: mockFs }
      );

      expect(result.hasErrors).toBe(false);
    });

    test('should handle missing tool_input', () => {
      const result = processHook({});

      expect(result.hasErrors).toBe(false);
    });
  });
});

describe('check-phpstan (integration tests)', () => {
  test('should output original input', async () => {
    const input = createMockInput('/path/to/file.php');
    const result = await runScript('code-quality/check-phpstan.js', input);

    expect(result.stdout).toBe(JSON.stringify(input));
    expect(result.exitCode).toBe(0);
  });
});
