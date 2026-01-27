const {
  checkForDebugCode,
  formatWarnings,
  processHook,
  DEBUG_PATTERN
} = require('../../scripts/code-quality/lib/warn-php-debug');
const { runScript } = require('../helpers/run-script');
const { createMockInput } = require('../helpers/mock-input');

describe('warn-php-debug (unit tests)', () => {
  describe('DEBUG_PATTERN', () => {
    test('should match var_dump', () => {
      expect(DEBUG_PATTERN.test('var_dump($x)')).toBe(true);
    });

    test('should match dd', () => {
      expect(DEBUG_PATTERN.test('dd($request)')).toBe(true);
    });

    test('should match ray', () => {
      expect(DEBUG_PATTERN.test('ray($var)')).toBe(true);
    });

    test('should not match regular code', () => {
      expect(DEBUG_PATTERN.test('return $result;')).toBe(false);
    });
  });

  describe('checkForDebugCode', () => {
    test('should detect var_dump in file', () => {
      const mockFs = {
        existsSync: () => true,
        readFileSync: () => `<?php\nvar_dump($data);`
      };

      const result = checkForDebugCode('/path/to/file.php', { fs: mockFs });

      expect(result.found).toBe(true);
      expect(result.matches).toHaveLength(1);
    });

    test('should handle file not found', () => {
      const mockFs = { existsSync: () => false };

      const result = checkForDebugCode('/nonexistent.php', { fs: mockFs });

      expect(result.found).toBe(false);
    });
  });

  describe('formatWarnings', () => {
    test('should format warnings correctly', () => {
      const matches = [{ line: 5, content: 'dd($x);' }];

      const warnings = formatWarnings('/file.php', matches);

      expect(warnings[0]).toContain('WARNING');
      expect(warnings[1]).toContain('L5');
    });
  });

  describe('processHook', () => {
    test('should process input with debug code', () => {
      const mockFs = {
        existsSync: () => true,
        readFileSync: () => 'dd($x);'
      };

      const result = processHook(
        { tool_input: { file_path: '/file.php' } },
        { fs: mockFs }
      );

      expect(result.warnings.length).toBeGreaterThan(0);
    });
  });
});

describe('warn-php-debug (integration tests)', () => {
  test('should output original input', async () => {
    const input = createMockInput('/path/to/file.php');
    const result = await runScript('code-quality/warn-php-debug.js', input);

    expect(result.stdout).toBe(JSON.stringify(input));
    expect(result.exitCode).toBe(0);
  });
});
