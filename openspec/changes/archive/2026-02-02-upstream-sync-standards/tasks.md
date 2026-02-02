# Tasks: upstream-sync-standards

## 任務清單

### C1: 小幅更新（7 檔）— 僅 meta 欄位更新，已直接覆蓋
- [x] 同步 acceptance-test-driven-development.ai.yaml (1.0.0→1.1.0)
- [x] 同步 behavior-driven-development.ai.yaml (1.0.0→1.1.0)
- [x] 同步 git-workflow.ai.yaml (1.2.1→1.3.0)
- [x] 同步 refactoring-standards.ai.yaml (新增 guide 欄位)
- [x] 同步 spec-driven-development.ai.yaml (source 路徑更新)
- [x] 同步 test-driven-development.ai.yaml (source 路徑更新)
- [x] 同步 testing.ai.yaml (新增 guide 欄位)

### C2: 大幅更新（2 檔）— 上游為更完整版本，已覆蓋
- [x] 合併 anti-hallucination.ai.yaml — 新增 Derivation Tags + Workflow Mapping（本地 1.4.0 無超前內容）
- [x] 合併 test-completeness-dimensions.ai.yaml — 新增第 8 維度 AI Test Generation Quality

### C3: 新增標準（選擇性採用）
- [x] 新增 requirement-engineering.ai.yaml (191 行，配套 requirement-assistant skill)
- [x] 新增 security-standards.ai.yaml (109 行，配套 security-review skill)
- [x] 評估 ai-agreement-standards.ai.yaml — 跳過（僅 20 行 2 條 rule，內容過薄）

### C4: 配套更新
- [x] 更新 manifest.json — 從上游覆蓋
- [x] 更新 upstream/last-sync.yaml — universal-dev-standards commit 更新為 a6412d7
- [x] 確認 CLAUDE.md 引用 — 無需調整（引用的是 .md 格式，新增的 .ai.yaml 由 AI 自動掃描）
