const {
  checkForConsoleLog,
  formatWarnings,
  processHook
} = require('../../scripts/code-quality/lib/warn-console-log');
const { runScript } = require('../helpers/run-script');
const { createMockInput } = require('../helpers/mock-input');

describe('warn-console-log (unit tests)', () => {
  describe('checkForConsoleLog', () => {
    test('should detect console.log in file content', () => {
      const mockFs = {
        existsSync: () => true,
        readFileSync: () => `
          function test() {
            console.log('debug');
            return true;
          }
        `
      };

      const result = checkForConsoleLog('/path/to/file.js', { fs: mockFs });

      expect(result.found).toBe(true);
      expect(result.matches).toHaveLength(1);
      expect(result.matches[0].content).toContain('console.log');
    });

    test('should return empty when no console.log found', () => {
      const mockFs = {
        existsSync: () => true,
        readFileSync: () => `
          function test() {
            return true;
          }
        `
      };

      const result = checkForConsoleLog('/path/to/file.js', { fs: mockFs });

      expect(result.found).toBe(false);
      expect(result.matches).toHaveLength(0);
    });

    test('should handle file not found', () => {
      const mockFs = {
        existsSync: () => false
      };

      const result = checkForConsoleLog('/nonexistent/file.js', { fs: mockFs });

      expect(result.found).toBe(false);
      expect(result.matches).toHaveLength(0);
    });

    test('should handle null file path', () => {
      const result = checkForConsoleLog(null);

      expect(result.found).toBe(false);
      expect(result.matches).toHaveLength(0);
    });

    test('should detect multiple console.log statements', () => {
      const mockFs = {
        existsSync: () => true,
        readFileSync: () => `
          console.log('1');
          console.log('2');
          console.log('3');
        `
      };

      const result = checkForConsoleLog('/path/to/file.js', { fs: mockFs });

      expect(result.found).toBe(true);
      expect(result.matches).toHaveLength(3);
    });
  });

  describe('formatWarnings', () => {
    test('should format warnings with line numbers', () => {
      const matches = [
        { line: 10, content: "console.log('test');" }
      ];

      const warnings = formatWarnings('/path/to/file.js', matches);

      expect(warnings).toHaveLength(3);
      expect(warnings[0]).toContain('WARNING');
      expect(warnings[0]).toContain('/path/to/file.js');
      expect(warnings[1]).toContain('L10');
    });

    test('should return empty array when no matches', () => {
      const warnings = formatWarnings('/path/to/file.js', []);

      expect(warnings).toHaveLength(0);
    });

    test('should limit output to maxLines', () => {
      const matches = [
        { line: 1, content: 'console.log(1)' },
        { line: 2, content: 'console.log(2)' },
        { line: 3, content: 'console.log(3)' },
        { line: 4, content: 'console.log(4)' },
        { line: 5, content: 'console.log(5)' },
        { line: 6, content: 'console.log(6)' },
        { line: 7, content: 'console.log(7)' }
      ];

      const warnings = formatWarnings('/path/to/file.js', matches, 3);

      // header + 3 lines + footer = 5
      expect(warnings).toHaveLength(5);
    });
  });

  describe('processHook', () => {
    test('should process valid input with console.log', () => {
      const mockFs = {
        existsSync: () => true,
        readFileSync: () => "console.log('test');"
      };
      const input = { tool_input: { file_path: '/path/to/file.js' } };

      const result = processHook(input, { fs: mockFs });

      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings[0]).toContain('WARNING');
    });

    test('should handle missing tool_input', () => {
      const result = processHook({});

      expect(result.warnings).toHaveLength(0);
    });

    test('should handle null input', () => {
      const result = processHook(null);

      expect(result.warnings).toHaveLength(0);
    });
  });
});

describe('warn-console-log (integration tests)', () => {
  test('should output original input with valid JSON', async () => {
    const input = createMockInput('/path/to/file.js');

    const result = await runScript('code-quality/warn-console-log.js', input);

    expect(result.stdout).toBe(JSON.stringify(input));
    expect(result.exitCode).toBe(0);
  });

  test('should handle empty input', async () => {
    const result = await runScript('code-quality/warn-console-log.js', '');

    expect(result.stdout).toBe('');
    expect(result.exitCode).toBe(0);
  });
});
