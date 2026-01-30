const {
  findTsConfigDir,
  checkTypeScript,
  formatErrors,
  processHook
} = require('../../scripts/code-quality/lib/check-typescript');
const { runScript } = require('../helpers/run-script');
const { createMockInput } = require('../helpers/mock-input');

describe('check-typescript (unit tests)', () => {
  describe('findTsConfigDir', () => {
    test('should find directory with tsconfig.json', () => {
      const mockFs = {
        existsSync: (path) => path === '/project/tsconfig.json'
      };

      const result = findTsConfigDir('/project/src/file.ts', { fs: mockFs });

      expect(result).toBe('/project');
    });

    test('should return null when no tsconfig found', () => {
      const mockFs = { existsSync: () => false };

      const result = findTsConfigDir('/project/src/file.ts', { fs: mockFs });

      expect(result).toBeNull();
    });

    test('should handle null file path', () => {
      const result = findTsConfigDir(null);

      expect(result).toBeNull();
    });
  });

  describe('checkTypeScript', () => {
    test('should return no errors when tsc passes', () => {
      const mockFs = {
        existsSync: (path) => path === '/project/tsconfig.json'
      };
      const mockExecSync = jest.fn();

      const result = checkTypeScript('/project/src/file.ts', {
        fs: mockFs,
        execFileSync: mockExecSync
      });

      expect(result.hasErrors).toBe(false);
      expect(result.errors).toHaveLength(0);
    });

    test('should return errors when tsc fails', () => {
      const mockFs = {
        existsSync: (path) => path === '/project/tsconfig.json'
      };
      const mockExecSync = jest.fn(() => {
        const error = new Error('tsc failed');
        error.stdout = 'file.ts(5,10): error TS2322: Type mismatch';
        throw error;
      });

      const result = checkTypeScript('/project/src/file.ts', {
        fs: mockFs,
        execFileSync: mockExecSync
      });

      expect(result.hasErrors).toBe(true);
      expect(result.errors).toHaveLength(1);
    });

    test('should handle null file path', () => {
      const result = checkTypeScript(null);

      expect(result.hasErrors).toBe(false);
      expect(result.errors).toHaveLength(0);
    });

    test('should return no errors when no tsconfig found', () => {
      const mockFs = { existsSync: () => false };

      const result = checkTypeScript('/project/src/file.ts', { fs: mockFs });

      expect(result.hasErrors).toBe(false);
    });
  });

  describe('formatErrors', () => {
    test('should format errors correctly', () => {
      const errors = ['file.ts(5,10): error TS2322: Type mismatch'];

      const messages = formatErrors('/path/to/file.ts', errors);

      expect(messages[0]).toContain('TypeScript errors');
      expect(messages[1]).toContain('TS2322');
    });

    test('should return empty array when no errors', () => {
      const messages = formatErrors('/path/to/file.ts', []);

      expect(messages).toHaveLength(0);
    });
  });

  describe('processHook', () => {
    test('should process valid input', () => {
      const mockFs = { existsSync: () => false };

      const result = processHook(
        { tool_input: { file_path: '/file.ts' } },
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

describe('check-typescript (integration tests)', () => {
  test('should output original input', async () => {
    const input = createMockInput('/path/to/file.ts');
    const result = await runScript('code-quality/check-typescript.js', input);

    expect(result.stdout).toBe(JSON.stringify(input));
    expect(result.exitCode).toBe(0);
  });
});
