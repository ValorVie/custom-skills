# Claude Code Custom Commands

Custom slash commands for Universal Development Standards.

> **Workflow Guide**: For a comprehensive overview of how methodology commands work together, see **[Command Family Overview](./COMMAND-FAMILY-OVERVIEW.md)**.
>
> **工作流程指南**：關於方法論指令如何協同運作的完整說明，請參閱 **[指令家族總覽](./COMMAND-FAMILY-OVERVIEW.md)**。

## Available Commands | 可用命令

### Standards Management | 標準管理

Commands for managing Universal Development Standards in your project.

| Command | Description | 說明 |
|---------|-------------|------|
| [`/init`](./init.md) | Initialize standards in project | 初始化專案標準 |
| [`/update`](./update.md) | Update standards to latest version | 更新標準至最新版本 |
| [`/check`](./check.md) | Verify adoption status | 檢查採用狀態 |
| [`/config`](./config.md) | Configure standards settings | 配置標準設定 |

### Development Workflow | 開發工作流程

Commands for development workflow automation.

| Command | Description | 說明 |
|---------|-------------|------|
| [`/commit`](./commit.md) | Generate conventional commit messages | 產生 commit message |
| [`/git-commit`](./git-commit.md) | Full git workflow (sync, commit, push, PR) | 完整 Git 工作流 |
| [`/review`](./review.md) | Perform systematic code review | 執行程式碼審查 |
| [`/release`](./release.md) | Guide through release process | 引導發布流程 |
| [`/changelog`](./changelog.md) | Update CHANGELOG.md | 更新 CHANGELOG |
| [`/requirement`](./requirement.md) | Write user stories and requirements | 撰寫需求文件 |
| [`/spec`](./spec.md) | Create specification documents | 建立規格文件 |
| [`/docs`](./docs.md) | Create/update documentation | 建立/更新文件 |
| [`/coverage`](./coverage.md) | Analyze test coverage | 分析測試覆蓋率 |
| [`/refactor`](./refactor.md) | Guide refactoring decisions | 重構決策指南 |
| [`/reverse-spec`](./reverse-spec.md) | Reverse engineer code to SDD spec | 反向工程成 SDD 規格 |
| [`/reverse-bdd`](./reverse-bdd.md) | Transform SDD AC to BDD scenarios | SDD AC 轉換為 BDD 場景 |
| [`/reverse-tdd`](./reverse-tdd.md) | Analyze BDD-TDD coverage | BDD-TDD 覆蓋率分析 |
| [`/derive-bdd`](./derive-bdd.md) | Derive BDD scenarios from approved spec | 從規格推演 BDD 場景 |
| [`/derive-tdd`](./derive-tdd.md) | Derive TDD test skeletons from spec | 從規格推演 TDD 骨架 |
| [`/derive-atdd`](./derive-atdd.md) | (Optional) Derive ATDD acceptance tests | （可選）推演 ATDD 測試 |
| [`/derive-all`](./derive-all.md) | Derive all test structures from spec | 從規格推演完整測試結構 |
| [`/upstream-sync`](./upstream-sync.md) | Sync and analyze upstream repos | 上游同步與分析 |

### Methodology | 方法論

Commands for development methodology workflows.

| Command | Description | 說明 |
|---------|-------------|------|
| [`/methodology`](./methodology.md) | Manage active methodology | 管理開發方法論 |
| [`/tdd`](./tdd.md) | Test-Driven Development workflow | TDD 開發流程 |
| [`/bdd`](./bdd.md) | Behavior-Driven Development workflow | BDD 開發流程 |
| [`/atdd`](./atdd.md) | Acceptance Test-Driven Development workflow | ATDD 驗收流程 |

### OpenSpec Experimental (OPSX) | OpenSpec 實驗性工作流

Commands for the experimental OpenSpec artifact-based workflow.

| Command | Description | 說明 |
|---------|-------------|------|
| [`/opsx:explore`](./../opsx/explore.md) | Think through ideas and clarify requirements | 探索與釐清需求 |
| [`/opsx:new`](./../opsx/new.md) | Start a new change with proposal | 建立新變更 |
| [`/opsx:continue`](./../opsx/continue.md) | Continue working on a change | 繼續變更工作 |
| [`/opsx:ff`](./../opsx/ff.md) | Fast-forward through artifact creation | 快速建立 artifacts |
| [`/opsx:apply`](./../opsx/apply.md) | Implement tasks from a change | 實作變更任務 |
| [`/opsx:verify`](./../opsx/verify.md) | Verify implementation matches artifacts | 驗證實作 |
| [`/opsx:sync`](./../opsx/sync.md) | Sync delta specs to main specs | 同步 delta specs |
| [`/opsx:archive`](./../opsx/archive.md) | Archive a completed change | 歸檔變更 |
| [`/opsx:bulk-archive`](./../opsx/bulk-archive.md) | Archive multiple changes at once | 批次歸檔 |
| [`/opsx:onboard`](./../opsx/onboard.md) | Guided onboarding walkthrough | 引導式教學 |

### Documentation | 文件

| Command | Description | 說明 |
|---------|-------------|------|
| [`/generate-docs`](./generate-docs.md) | Generate usage documentation | 產生使用文件 |

### ECC Commands | ECC 指令

Commands from Everything Claude Code integration.

| Command | Description | 說明 |
|---------|-------------|------|
| [`/checkpoint`](./checkpoint.md) | Create git checkpoint (stash + tag) | 建立 Git 檢查點 |
| [`/build-fix`](./build-fix.md) | Iteratively fix build errors | 迭代修復建置錯誤 |
| [`/e2e`](./e2e.md) | Generate and run E2E tests | 產生並執行 E2E 測試 |
| [`/learn`](./learn.md) | Extract patterns from session | 從會話萃取模式 |
| [`/test-coverage`](./test-coverage.md) | Analyze test coverage gaps | 分析測試覆蓋率 |
| [`/eval`](./eval.md) | Eval-driven development workflow | Eval 驅動開發流程 |

## Commands vs Skills | 命令與技能

| Aspect | Commands | Skills |
|--------|----------|--------|
| **Trigger** | Manual (`/command`) | Automatic (context-based) |
| **Location** | `commands/` | `skills/` or root |
| **Use Case** | Explicit action | Background assistance |

## Adding Custom Commands | 新增自訂命令

Create a `.md` file in the `commands/` directory:

```markdown
---
description: Brief description of the command
allowed-tools: Read, Write, Bash(git:*)
argument-hint: "[optional arguments]"
---

# Command Name

Instructions for Claude...
```

## Installation | 安裝

Commands are automatically available after installing the plugin:

```bash
/plugin marketplace add AsiaOstrich/universal-dev-standards
/plugin install universal-dev-standards@asia-ostrich
```

## License | 授權

Dual-licensed: CC BY 4.0 (documentation) + MIT (code)
