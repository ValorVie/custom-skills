const {
  findMypyConfigDir,
  runMypy,
  formatErrors,
  processHook
} = require('../../scripts/code-quality/lib/check-mypy');
const { runScript } = require('../helpers/run-script');
const { createMockInput } = require('../helpers/mock-input');

describe('check-mypy (unit tests)', () => {
  describe('findMypyConfigDir', () => {
    test('should find directory with pyproject.toml', () => {
      const mockFs = {
        existsSync: (path) => path === '/project/pyproject.toml'
      };

      const result = findMypyConfigDir('/project/src/file.py', { fs: mockFs });

      expect(result).toBe('/project');
    });

    test('should find directory with mypy.ini', () => {
      const mockFs = {
        existsSync: (path) => path === '/project/mypy.ini'
      };

      const result = findMypyConfigDir('/project/src/file.py', { fs: mockFs });

      expect(result).toBe('/project');
    });

    test('should return null when no config found', () => {
      const mockFs = { existsSync: () => false };

      const result = findMypyConfigDir('/project/src/file.py', { fs: mockFs });

      expect(result).toBeNull();
    });

    test('should handle null file path', () => {
      const result = findMypyConfigDir(null);

      expect(result).toBeNull();
    });
  });

  describe('runMypy', () => {
    test('should return no errors when mypy passes', () => {
      const mockFs = {
        existsSync: (path) => path === '/project/pyproject.toml'
      };
      const mockExecSync = jest.fn();

      const result = runMypy('/project/src/file.py', {
        fs: mockFs,
        execSync: mockExecSync
      });

      expect(result.hasErrors).toBe(false);
      expect(result.errors).toHaveLength(0);
    });

    test('should return errors when mypy fails', () => {
      const mockFs = {
        existsSync: (path) => path === '/project/pyproject.toml'
      };
      const mockExecSync = jest.fn(() => {
        const error = new Error('mypy failed');
        error.stdout = 'file.py:5: error: Incompatible types';
        throw error;
      });

      const result = runMypy('/project/src/file.py', {
        fs: mockFs,
        execSync: mockExecSync
      });

      expect(result.hasErrors).toBe(true);
      expect(result.errors).toHaveLength(1);
    });

    test('should handle null file path', () => {
      const result = runMypy(null);

      expect(result.hasErrors).toBe(false);
      expect(result.errors).toHaveLength(0);
    });

    test('should return no errors when no config found', () => {
      const mockFs = { existsSync: () => false };

      const result = runMypy('/project/src/file.py', { fs: mockFs });

      expect(result.hasErrors).toBe(false);
    });
  });

  describe('formatErrors', () => {
    test('should format errors correctly', () => {
      const errors = ['file.py:5: error: Incompatible types'];

      const messages = formatErrors('/path/to/file.py', errors);

      expect(messages[0]).toContain('mypy errors');
      expect(messages[1]).toContain('Incompatible types');
    });

    test('should return empty array when no errors', () => {
      const messages = formatErrors('/path/to/file.py', []);

      expect(messages).toHaveLength(0);
    });
  });

  describe('processHook', () => {
    test('should process valid input', () => {
      const mockFs = { existsSync: () => false };

      const result = processHook(
        { tool_input: { file_path: '/file.py' } },
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

describe('check-mypy (integration tests)', () => {
  test('should output original input', async () => {
    const input = createMockInput('/path/to/file.py');
    const result = await runScript('code-quality/check-mypy.js', input);

    expect(result.stdout).toBe(JSON.stringify(input));
    expect(result.exitCode).toBe(0);
  });
});
