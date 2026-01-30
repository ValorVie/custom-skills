const {
  isGitRepo,
  getModifiedFiles,
  hasJsDebugCode,
  hasPhpDebugCode,
  hasPythonDebugCode,
  checkAllFiles,
  processHook
} = require('../../scripts/code-quality/lib/check-debug-code');
const { runScript } = require('../helpers/run-script');
const { createMockInput } = require('../helpers/mock-input');

describe('check-debug-code (unit tests)', () => {
  describe('isGitRepo', () => {
    test('should return true in git repo', () => {
      const mockExecSync = jest.fn();

      const result = isGitRepo({ execFileSync: mockExecSync });

      expect(result).toBe(true);
    });

    test('should return false outside git repo', () => {
      const mockExecSync = jest.fn(() => {
        throw new Error('not a git repo');
      });

      const result = isGitRepo({ execFileSync: mockExecSync });

      expect(result).toBe(false);
    });
  });

  describe('getModifiedFiles', () => {
    test('should return modified files', () => {
      const mockFs = { existsSync: () => true };
      const mockExecSync = jest.fn(() => 'file1.js\nfile2.php\n');

      const files = getModifiedFiles({ fs: mockFs, execFileSync: mockExecSync });

      expect(files).toEqual(['file1.js', 'file2.php']);
    });

    test('should filter non-existing files', () => {
      const mockFs = { existsSync: (f) => f === 'file1.js' };
      const mockExecSync = jest.fn(() => 'file1.js\nfile2.php\n');

      const files = getModifiedFiles({ fs: mockFs, execFileSync: mockExecSync });

      expect(files).toEqual(['file1.js']);
    });

    test('should return empty array on error', () => {
      const mockExecSync = jest.fn(() => {
        throw new Error('git error');
      });

      const files = getModifiedFiles({ execFileSync: mockExecSync });

      expect(files).toEqual([]);
    });
  });

  describe('hasJsDebugCode', () => {
    test('should detect console.log', () => {
      const mockFs = {
        readFileSync: () => 'console.log("debug");'
      };

      const result = hasJsDebugCode('/file.js', { fs: mockFs });

      expect(result).toBe(true);
    });

    test('should not match regular code', () => {
      const mockFs = {
        readFileSync: () => 'return result;'
      };

      const result = hasJsDebugCode('/file.js', { fs: mockFs });

      expect(result).toBe(false);
    });
  });

  describe('hasPhpDebugCode', () => {
    test('should detect var_dump', () => {
      const mockFs = {
        readFileSync: () => 'var_dump($x);'
      };

      const result = hasPhpDebugCode('/file.php', { fs: mockFs });

      expect(result).toBe(true);
    });

    test('should detect dd', () => {
      const mockFs = {
        readFileSync: () => 'dd($request);'
      };

      const result = hasPhpDebugCode('/file.php', { fs: mockFs });

      expect(result).toBe(true);
    });

    test('should detect ray', () => {
      const mockFs = {
        readFileSync: () => 'ray($var);'
      };

      const result = hasPhpDebugCode('/file.php', { fs: mockFs });

      expect(result).toBe(true);
    });

    test('should not match regular code', () => {
      const mockFs = {
        readFileSync: () => 'return $result;'
      };

      const result = hasPhpDebugCode('/file.php', { fs: mockFs });

      expect(result).toBe(false);
    });
  });

  describe('hasPythonDebugCode', () => {
    test('should detect print', () => {
      const mockFs = {
        readFileSync: () => 'print("debug")'
      };

      const result = hasPythonDebugCode('/file.py', { fs: mockFs });

      expect(result).toBe(true);
    });

    test('should detect breakpoint', () => {
      const mockFs = {
        readFileSync: () => 'breakpoint()'
      };

      const result = hasPythonDebugCode('/file.py', { fs: mockFs });

      expect(result).toBe(true);
    });

    test('should detect pdb', () => {
      const mockFs = {
        readFileSync: () => 'pdb.set_trace()'
      };

      const result = hasPythonDebugCode('/file.py', { fs: mockFs });

      expect(result).toBe(true);
    });

    test('should detect ic', () => {
      const mockFs = {
        readFileSync: () => 'ic(value)'
      };

      const result = hasPythonDebugCode('/file.py', { fs: mockFs });

      expect(result).toBe(true);
    });

    test('should ignore comment lines', () => {
      const mockFs = {
        readFileSync: () => '# print("commented")'
      };

      const result = hasPythonDebugCode('/file.py', { fs: mockFs });

      expect(result).toBe(false);
    });

    test('should not match regular code', () => {
      const mockFs = {
        readFileSync: () => 'return result'
      };

      const result = hasPythonDebugCode('/file.py', { fs: mockFs });

      expect(result).toBe(false);
    });
  });

  describe('checkAllFiles', () => {
    test('should return warnings for files with debug code', () => {
      const mockFs = {
        existsSync: () => true,
        readFileSync: () => 'console.log("debug");'
      };
      const mockExecFileSync = jest.fn((cmd, args) => {
        if (args && args.includes('rev-parse')) return '';
        if (args && args.includes('diff')) return 'file.js\n';
        return '';
      });

      const warnings = checkAllFiles({ fs: mockFs, execFileSync: mockExecFileSync });

      expect(warnings.length).toBeGreaterThan(0);
      expect(warnings[0]).toContain('console.log');
    });

    test('should return empty when not in git repo', () => {
      const mockExecSync = jest.fn(() => {
        throw new Error('not a git repo');
      });

      const warnings = checkAllFiles({ execFileSync: mockExecSync });

      expect(warnings).toHaveLength(0);
    });
  });

  describe('processHook', () => {
    test('should return warnings', () => {
      const mockExecSync = jest.fn(() => {
        throw new Error('not a git repo');
      });

      const result = processHook({}, { execFileSync: mockExecSync });

      expect(result.warnings).toBeDefined();
    });
  });
});

describe('check-debug-code (integration tests)', () => {
  test('should output original input', async () => {
    const input = createMockInput('/path/to/file.js');
    const result = await runScript('code-quality/check-debug-code.js', input);

    expect(result.stdout).toBe(JSON.stringify(input));
    expect(result.exitCode).toBe(0);
  }, 15000);
});
