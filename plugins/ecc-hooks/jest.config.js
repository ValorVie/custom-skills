module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/tests/**/*.test.js'],
  collectCoverageFrom: [
    'scripts/**/lib/**/*.js'
  ],
  coverageDirectory: 'coverage',
  verbose: true
};
