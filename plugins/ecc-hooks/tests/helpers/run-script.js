// Use requireActual to bypass any mocks
const { spawn } = jest.requireActual('child_process');
const path = require('path');

/**
 * Run a script with the given input and capture output
 * @param {string} scriptPath - Path to the script (relative to scripts/ or absolute)
 * @param {string|object} input - Input to send to stdin (string or object to be JSON stringified)
 * @returns {Promise<{stdout: string, stderr: string, exitCode: number}>}
 */
function runScript(scriptPath, input) {
  return new Promise((resolve) => {
    const absolutePath = path.isAbsolute(scriptPath)
      ? scriptPath
      : path.join(__dirname, '../../scripts', scriptPath);

    const child = spawn('node', [absolutePath], {
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('close', (exitCode) => {
      resolve({
        stdout: stdout.trim(),
        stderr: stderr.trim(),
        exitCode: exitCode || 0
      });
    });

    child.on('error', (err) => {
      resolve({
        stdout: '',
        stderr: err.message,
        exitCode: 1
      });
    });

    const inputStr = typeof input === 'string' ? input : JSON.stringify(input);
    child.stdin.write(inputStr);
    child.stdin.end();
  });
}

module.exports = {
  runScript
};
