/**
 * Custom Tools for OpenCode
 *
 * These tools extend OpenCode with additional capabilities:
 * - run-tests: Auto-detect and run test suites
 * - check-coverage: Analyze test coverage
 * - security-audit: Comprehensive security scanning
 *
 * Ported from everything-claude-code upstream.
 */

export { default as runTests } from "./run-tests.js"
export { default as checkCoverage } from "./check-coverage.js"
export { default as securityAudit } from "./security-audit.js"
