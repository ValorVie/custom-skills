# 設計文件：auto-skill canonical state 與多工具投影

**日期：** 2026-03-12
**狀態：** 草案
**範圍：** ai-dev CLI — `update`、`clone` 與 `auto-skill` 路徑/投影邏輯

---

## 背景

`[已確認]` 目前 `auto-skill` 外部來源路徑仍使用 `~/.config/auto-skill`，且在開發者整合與最終分發階段都採 `copytree`。  
`[Source: Code]` `script/utils/paths.py`  
`[Source: Code]` `script/utils/shared.py`

`[已確認]` 現有 `ai-dev update` 只負責更新 repo 與套件，不會分發 Skills 到各工具目錄；實際分發由 `ai-dev clone` 負責。  
`[Source: Code]` `script/commands/update.py`

`[已確認]` `skills/auto-skill/.clonepolicy.json` 已明確區分：

- `*/_index.json` 使用 `key-merge`
- `knowledge-base/*.md` 使用 `skip-if-exists`
- `experience/*.md` 使用 `skip-if-exists`

這代表 `auto-skill` 模板本來就比較像「初始化/更新來源」，不是直接給工具寫入的唯一實體目錄。  
`[Source: Code]` `skills/auto-skill/.clonepolicy.json`

`[已確認]` 目前專案中已有一段跨平台 `symlink -> fallback copy` 的既有實作，使用於 OpenCode superpowers。  
`[Source: Code]` `script/utils/shared.py`

---

## 問題

目前 `auto-skill` 的管理模型有三個問題：

1. 缺乏工具無關的 canonical state，容易讓不同 AI 工具目錄各自漂移。
2. `copytree` 讓每個工具吃到獨立副本，更新後容易產生分叉與重複維護。
3. 路徑命名不一致，`~/.config/auto-skill` 無法反映這份資料是由 `ai-dev` 管理。

---

## 使用者需求與約束

本次已確認的需求如下：

1. `auto-skill` 的 canonical state 改為 `~/.config/ai-dev/skills/auto-skill`
2. 來源需要透過自己的抽象層管理，而不是綁在某一個工具根目錄
3. 實作需考慮多平台相容與等冪性
4. 參考 `vercel-labs/skills` 的模式確認 link 類型

---

## 方案比較

### 方案 A：延續目前的 copy 模型

- 優點：改動最少
- 缺點：每個工具都持有獨立副本，最容易漂移
- 缺點：無法反映 canonical state 與 projection 的責任分層

### 方案 B：檔案級 hard-link 到多個工具目錄

- 優點：磁碟使用量較低
- 缺點：hard-link 只適用檔案，不適合整個目錄樹
- 缺點：跨磁碟與跨平台行為更脆弱
- 缺點：刪除/覆蓋與目錄重建流程複雜，等冪性較差

### 方案 C：canonical state + directory symlink/junction + fallback copy

- 優點：與 `vercel-labs/skills` 的模型一致
- 優點：一份 canonical state，可投影到多個工具
- 優點：當平台或權限不支援連結時，仍可 fallback copy
- 優點：符合「來源抽象層 + 各工具 projection」的需求

**`[Recommended]` 採用方案 C。**

---

## 設計決策

### D1. `auto-skill` 路徑分層

定義三層：

1. **Template**
   - `~/.config/custom-skills/skills/auto-skill`
2. **Canonical User State**
   - `~/.config/ai-dev/skills/auto-skill`
3. **Tool Projections**
   - `~/.claude/skills/auto-skill`
   - `~/.codex/skills/auto-skill`
   - `~/.gemini/skills/auto-skill`
   - 其他支援工具目錄

### D2. `update` 與 `clone` 的責任

- `update`
  - 確保外部來源 repo 更新
  - 將 template 與外部來源整合到 canonical state
  - 不直接做最終工具分發

- `clone`
  - 從 canonical state 投影到各工具目錄
  - `auto-skill` 為特殊資源，使用 link-aware projection，而不是一般 `copytree`

### D3. projection 類型

- macOS / Linux：優先使用相對路徑 directory symlink
- Windows：優先使用 junction
- 任何失敗情況：fallback to copy

### D4. 等冪性

每次執行前都要先檢查：

- 目標是否已存在且已正確指向 canonical state
- 目標是否為 broken symlink / junction
- 目標是否為既有真實目錄

若已正確存在則跳過；若不一致則清理後重建。

---

## 與 `vercel-labs/skills` 的對照

`[已確認]` `vercel-labs/skills` 採用 canonical directory + symlink 模型，Windows 使用 `junction`，失敗時 fallback copy。  
`[Source: External]` `src/installer.ts`  
`[Source: External]` `README.md`

本次設計與其一致，但不直接照搬，原因如下：

- `ai-dev` 已有 Stage 1 / Stage 2 / Stage 3 架構
- `auto-skill` 還有 template merge 與 `.clonepolicy.json` 需求
- `ai-dev update` 與 `clone` 的責任已經固定，不宜完全改成上游 install 模型

---

## 具體資料流

### Flow 1：`ai-dev update`

1. 更新 `~/.config/auto-skill` 外部來源 repo
2. 將 template `skills/auto-skill` 與外部來源內容合併到 `~/.config/ai-dev/skills/auto-skill`
3. 套用 `.clonepolicy.json`
4. 不分發到工具目錄

### Flow 2：`ai-dev clone`

1. 先完成一般技能/命令/agents 分發
2. 針對 `auto-skill` 以 canonical state 為來源做 projection
3. 若可建立 link，建立 link
4. 若無法建立 link，改為 copy
5. 印出實際採用模式，方便除錯

---

## 實作範圍

### 目標

1. 新增 canonical state 路徑 helper
2. 將 `auto-skill` state 初始化/更新抽成獨立 helper
3. 將 `auto-skill` 投影抽成獨立 helper
4. 將 `clone` / `update` 接入該 helper
5. 補上跨平台與等冪測試

### 非目標

1. 本次不重構整個 Stage 2 / Stage 3 copy 架構
2. 本次不將所有技能分發都改成 symlink 模式
3. 本次不變更 `auto-skill` 內部的內容格式或索引協議

---

## 風險與對策

### 風險 1：Windows symlink 權限不足

對策：使用 junction 或 fallback copy。

### 風險 2：目標目錄已被手動修改

對策：若不是正確 link，先清理再重建；保留既有 copy fallback 路徑。

### 風險 3：parent path 本身也是 symlink

對策：建立相對路徑 link 前先 resolve parent path，避免 self-loop 或壞鏈結。

---

## 驗證策略

1. canonical state 路徑 helper 測試
2. template -> canonical state merge 測試
3. 目標已存在正確 symlink 時的等冪測試
4. broken symlink 清理測試
5. symlink 建立失敗時的 fallback copy 測試
6. `clone` / `update` 冒煙測試

