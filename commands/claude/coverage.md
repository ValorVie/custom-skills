---
description: Analyze test coverage and provide recommendations. Use --generate to create missing tests.
allowed-tools: Read, Grep, Glob, Bash(npm run test:coverage:*), Bash(npx:*), Write, Edit
argument-hint: "[file or module to analyze | 要分析的檔案或模組] [--generate | -g]"
---

# Test Coverage Assistant | 測試覆蓋率助手

Analyze test coverage across multiple dimensions and provide actionable recommendations.

多維度分析測試覆蓋率並提供可執行的建議。

## Coverage Dimensions | 覆蓋率維度

| Dimension | What it Measures | 測量內容 |
|-----------|------------------|----------|
| **Line** | Lines executed | 執行的行數 |
| **Branch** | Decision paths | 決策路徑 |
| **Function** | Functions called | 呼叫的函數 |
| **Statement** | Statements executed | 執行的陳述式 |

## 8-Dimension Framework | 八維度框架

1. **Code Coverage** - Lines, branches, functions
2. **Requirement Coverage** - All requirements tested
3. **Risk Coverage** - High-risk areas tested
4. **Integration Coverage** - Component interactions
5. **Edge Case Coverage** - Boundary conditions
6. **Error Coverage** - Error handling paths
7. **Permission Coverage** - Access control scenarios
8. **AI Generation Quality** - AI-generated test effectiveness

## Workflow | 工作流程

1. **Run coverage tool** - Generate coverage report
2. **Analyze gaps** - Identify untested areas
3. **Prioritize** - Rank by risk and importance
4. **Recommend tests** - Suggest specific tests to add
5. **Track progress** - Monitor coverage over time

## Coverage Targets | 覆蓋率目標

| Level | Coverage | Use Case |
|-------|----------|----------|
| Minimum | 60% | Legacy code |
| Standard | 80% | Most projects |
| High | 90% | Critical systems |
| Critical | 95%+ | Safety-critical |

## Usage | 使用方式

- `/coverage` - Run coverage analysis (default mode)
- `/coverage src/auth` - Analyze specific module
- `/coverage --recommend` - Get test recommendations
- `/coverage --generate` or `/coverage -g` - Analyze and generate missing tests

## Generate Mode | 生成模式

When `--generate` or `-g` flag is provided:

當使用 `--generate` 或 `-g` 參數時：

1. Run tests with coverage: `npm test --coverage` or `pnpm test --coverage`
2. Analyze coverage report (coverage/coverage-summary.json)
3. Identify files below 80% coverage threshold
4. For each under-covered file:
   - Analyze untested code paths
   - Generate unit tests for functions
   - Generate integration tests for APIs
   - Generate E2E tests for critical flows
5. Verify new tests pass
6. Show before/after coverage metrics
7. Ensure project reaches 80%+ overall coverage

### Focus Areas | 聚焦點

- Happy path scenarios
- Error handling
- Edge cases (null, undefined, empty)
- Boundary conditions

## Reference | 參考

- Full standard: [test-coverage-assistant](../../test-coverage-assistant/SKILL.md)
- Core guide: [testing-standards](../../../../core/testing-standards.md)
