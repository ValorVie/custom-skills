# Vibe Coding Dev Workflow Framework（Production Baseline）

## 目錄

- [文件定位](#文件定位)
- [最終 Stack 規格](#最終-stack-規格)
- [工作區版型（已運作型態）](#工作區版型已運作型態)
- [工具職責邊界](#工具職責邊界)
- [標準任務 Runbook（單一任務端到端）](#標準任務-runbook單一任務端到端)
- [PR 與 Code Review 運作規格](#pr-與-code-review-運作規格)
- [範例演示 A：一般功能開發](#範例演示-a一般功能開發)
- [範例演示 B：緊急 Hotfix](#範例演示-b緊急-hotfix)
- [範例演示 C：大型 Refactor](#範例演示-c大型-refactor)
- [Definition of Done](#definition-of-done)
- [參考資料](#參考資料)

---

## 文件定位

本文件描述的是「已經在運作中」的最終型態工作流。

範圍包含：

- 日常任務如何從開始到 merge 完成
- 各工具在流程中的固定責任與交接點
- Feature / Hotfix / Refactor 三種場景的實戰演示

---

## 最終 Stack 規格

### Windows

- Terminal：`WezTerm`
- AI Coding：`Claude Code` 或 `OpenCode`
- File Navigation：`Yazi`
- Git UI：`Lazygit`
- Deep Review：`VS Code`

### macOS

- Terminal：`Alacritty`
- Workspace Multiplexer：`zellij`
- AI Coding：`Claude Code` 或 `OpenCode`
- File Navigation：`Yazi`
- Git UI：`Lazygit`
- Deep Review：`VS Code`

---

## 工作區版型（已運作型態）

### Windows 版型

- Pane 1：AI 開發（`Claude Code` / `OpenCode`）
- Pane 2：Git 操作（`lazygit`）
- Pane 3：測試與建置（test/build/lint）
- 需要檔案密集操作時切到 `yazi`

### macOS 版型（zellij）

- Tab 1：AI 開發
- Tab 2：Lazygit
- Tab 3：Yazi
- Tab 4：Test / Build / Logs

---

## 工具職責邊界

| 工具 | 固定職責 | 不負責 |
|------|----------|--------|
| WezTerm / Alacritty | 統一終端執行環境 | 版本控制決策 |
| zellij（macOS） | 長工作階段編排（Tab/Pane） | 代碼審查 |
| Yazi | 導覽、搬移、重命名、預覽 | commit 歷史整理 |
| Claude Code / OpenCode | 需求拆解、程式實作、除錯 | PR 最終把關 |
| Lazygit | stage、commit、branch、rebase、衝突處理 | 跨檔案語意審查 |
| VS Code | 最終 code review、PR 討論回覆 | 日常高頻 Git 操作 |

---

## 標準任務 Runbook（單一任務端到端）

1. **建立任務分支**
   - 分支命名：`feature/*`、`hotfix/*`、`refactor/*`
2. **檔案定位**
   - 用 `yazi` 進入目標目錄與檔案集合。
3. **AI 實作**
   - 在 `Claude Code` 或 `OpenCode` 完成變更。
4. **本地驗證**
   - 執行 test、build、lint；不通過不得進入下一步。
5. **Git 整理**
   - 在 `lazygit` 進行分批 stage 與語意化 commit。
6. **最終審查**
   - 在 `VS Code` 進行 final review（跨檔案脈絡、命名一致性、風險點）。
7. **送審與合併**
   - 回 `lazygit` push、建立 PR、等待 CI 與 review 完成後合併。

---

## PR 與 Code Review 運作規格

每個 PR 固定包含：

- 背景：為什麼要改
- 範圍：改了哪些模組
- 驗證：跑了哪些測試與結果
- 風險：相容性、效能、資料一致性

每個 PR 固定檢查：

- commit 是否可讀（一個 commit 一個意圖）
- diff 是否可審（避免混入無關格式變更）
- CI 是否全綠

---

## 範例演示 A：一般功能開發

情境：新增「設定頁可切換通知頻率」功能。

### A-1 建分支

```bash
git checkout -b feature/notification-frequency
```

### A-2 實作與驗證

```bash
# 在 AI 工具完成修改後
pnpm test
pnpm build
```

### A-3 Lazygit 整理 commit

- Commit 1：`功能(settings): 新增通知頻率欄位與狀態管理`
- Commit 2：`測試(settings): 補上通知頻率切換測試`

### A-4 VS Code final review

- 確認 UI 文案、型別、測試可讀性
- 確認無無關檔案進入 diff

### A-5 送 PR

- PR 標題：`功能(settings): 支援通知頻率切換`
- PR 內容：背景 / 範圍 / 驗證 / 風險

---

## 範例演示 B：緊急 Hotfix

情境：付款頁在空購物車時會拋出例外。

### B-1 建分支

```bash
git checkout -b hotfix/checkout-empty-cart-guard
```

### B-2 最小修補

- 只改防呆判斷與錯誤訊息回傳
- 不混入重構或命名整理

### B-3 最小必要驗證

```bash
pnpm test -t "checkout"
pnpm build
```

### B-4 提交與送審

- Commit：`修正(checkout): 空購物車結帳時回傳可預期錯誤`
- PR 類型：hotfix
- Review 重點：回歸範圍與風險註記

---

## 範例演示 C：大型 Refactor

情境：將訂單模組 service 層拆分，改善維護性。

### C-1 建分支

```bash
git checkout -b refactor/order-service-split
```

### C-2 分段提交策略

- Commit 1：抽出 `OrderValidator`
- Commit 2：抽出 `OrderPricing`
- Commit 3：調整呼叫端並補測試

### C-3 每段都可驗證

```bash
pnpm test
pnpm build
```

### C-4 Review 策略

- 先看「行為不變」證據（測試、輸出）
- 再看「結構變更」是否降低耦合

---

## Definition of Done

任務完成必須同時滿足：

- 功能或修正目標可驗證
- test / build / lint 全部通過
- commit 歷史可讀且可追溯
- PR 描述完整（背景、範圍、驗證、風險）
- 已完成 VS Code final review
- 已完成 reviewer 回饋處理

---

## 參考資料

- Yazi 指南：`docs/dev-guide/terminal/YAZI-GUIDE.md`
- Lazygit 指南：`docs/dev-guide/git/LAZYGIT-GUIDE.md`
- Git 工作流：`docs/dev-guide/git/GIT-WORKFLOW.md`
- 開發工作流：`docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md`
- WezTerm 指南：`docs/dev-guide/terminal/WEZTERM-GUIDE.md`
- Alacritty 指南：`docs/dev-guide/terminal/ALACRITTY-GUIDE.md`
- Zellij 指南：`docs/dev-guide/terminal/ZELLIJ-GUIDE.md`
