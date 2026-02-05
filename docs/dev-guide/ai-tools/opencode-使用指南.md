# OpenCode 完整使用指南

> 讓 AI 成為你的全職開發團隊

---

## 目錄

1. [簡介](#簡介)
2. [安裝與配置](#安裝與配置)
3. [基礎操作](#基礎操作)
4. [Oh My OpenCode：從實習生到項目經理](#oh-my-opencode從實習生到項目經理)
5. [核心 Agent 介紹](#核心-agent-介紹)
6. [魔法關鍵詞](#魔法關鍵詞)
7. [實戰場景](#實戰場景)
8. [進階技巧](#進階技巧)
9. [常見問題](#常見問題)
10. [最佳實踐](#最佳實踐)

---

## 簡介

### 什麼是 OpenCode？

OpenCode 是一個開源的 AI 編程助手，運行在你的終端機中。它提供：

- **終端機界面**：原生 TUI 體驗，零延遲
- **桌面應用**：跨平台圖形界面
- **IDE 擴展**：整合到你的編輯器

### 為什麼選擇 OpenCode？

| 特性 | OpenCode | 其他工具 |
|------|----------|---------|
| 多模型支援 | ✅ Claude、GPT、Gemini、Copilot | 限制 |
| LSP 整合 | ✅ 自動啟用 | ❌ |
| 可擴展性 | ✅ 無限擴展 | 限制 |
| 開源 | ✅ 完全開源 | ❌ 商業化 |
| 性能 | ✅ 零閃爍，高性能 | ⚠️ |

---

## 安裝與配置

### 第一步：安裝 OpenCode

#### 方法一：一鍵安裝（推薦）

```bash
curl -fsSL https://opencode.ai/install | bash
```

#### 方法二：使用套件管理器

```bash
# macOS / Linux (Homebrew)
brew install anomalyco/tap/opencode

# 使用 npm
npm install -g opencode-ai

# 使用 Bun
bun install -g opencode-ai
```

#### 方法三：Docker

```bash
docker run -it --rm ghcr.io/anomalyco/opencode
```

### 第二步：配置 API 提供商

#### 選項 A：使用 OpenCode Zen（推薦新手）

1. 啟動 OpenCode：`opencode`
2. 輸入命令：`/connect`
3. 選擇 `opencode`
4. 前往 [opencode.ai/auth](https://opencode.ai/auth) 註冊並獲取 API key
5. 貼上 API key

#### 選項 B：使用你現有的訂閱

OpenCode 支援多種提供商：

- **Claude Pro/Max**：直接使用 Claude 訂閱
- **ChatGPT Plus**：使用 OpenAI API
- **Gemini**：使用 Google AI
- **GitHub Copilot**：使用 Copilot 訂閱

配置方式：

```bash
# 設置環境變量
export ANTHROPIC_API_KEY="your-claude-key"
export OPENAI_API_KEY="your-openai-key"
export GOOGLE_API_KEY="your-gemini-key"
```

或使用 `/connect` 命令進行互動式配置。

### 第三步：驗證安裝

```bash
opencode --version
```

---

## 基礎操作

### 啟動 OpenCode

```bash
# 進入項目目錄
cd my-project

# 啟動 OpenCode
opencode
```

### 基本按鍵

| 按鍵 | 功能 |
|------|------|
| `Enter` | 發送訊息 |
| `Shift + Enter` | 換行（不發送） |
| `Tab` | 切換模式（計劃 ↔ 執行） |
| `@` | 引用文件或 agent |
| `/` | 輸入命令 |
| `!` | 執行終端命令 |
| `Ctrl+C` | 中斷當前操作 |

### 兩種模式

#### 計劃模式（Plan Mode）

- **用途**：讓 AI 先出方案，不會修改代碼
- **切換**：按 `Tab` 鍵
- **適合**：複雜功能、架構設計、需要審查的變更

#### 執行模式（Build Mode）

- **用途**：AI 直接動手修改代碼
- **切換**：按 `Tab` 鍵
- **適合**：簡單任務、明確的 bug 修復

### 基本命令

```bash
# 初始化項目（讓 AI 了解你的專案）
/init

# 撤銷上一步
/undo

# 重做
/redo

# 壓縮對話歷史
/compact

# 開始新對話
/new

# 分享對話
/share

# 查看可用模型
/models

# 退出
/exit
```

### 引用文件

使用 `@` 符號讓 AI 查看特定文件：

```
看看 @src/App.js 這個文件有什麼問題
```

---

## Oh My OpenCode：從實習生到項目經理

### 什麼是 Oh My OpenCode？

**普通 OpenCode**：像一個剛畢業的實習生，需要你一步步指導。

**Oh My OpenCode**：像一個帶著整個團隊的項目經理，自動分配任務並完成工作。

### 安裝 Oh My OpenCode

#### 自動安裝（推薦）

在 OpenCode 中輸入：

```
幫我安裝 oh-my-opencode 插件
```

或使用 LLM 安裝：

```bash
# 讓 AI 幫你安裝
bunx oh-my-opencode
```

#### 手動安裝

```bash
# 安裝插件
npm install -g oh-my-opencode

# 配置 OpenCode 加載插件
# 編輯 ~/.config/opencode/opencode.json
# 添加 "oh-my-opencode" 到 plugins 數組
```

### Oh My OpenCode 帶來的改變

| 功能 | 普通模式 | Oh My OpenCode |
|------|---------|----------------|
| Agent 數量 | 1 個 | 10+ 個專門 agent |
| 並行工作 | ❌ | ✅ |
| 自動研究 | ❌ | ✅ |
| 代碼搜索 | 基礎 | LSP + AST-Grep |
| 持續執行 | 會中途放棄 | 強制完成任務 |
| 架構諮詢 | ❌ | ✅ Oracle agent |

---

## 核心 Agent 介紹

安裝 Oh My OpenCode 後，你擁有一整個 AI 團隊：

### Sisyphus（西西弗斯）- 總指揮

- **模型**：Claude Opus 4.5
- **職責**：主要協調者，負責所有編碼工作
- **特點**：
  - 強制完成任務（不會說"我完成了"然後沒做完）
  - 自動調用其他專門 agent
  - 保持整潔的代碼（無過度註釋）

### Prometheus（普羅米修斯）- 規劃大師

- **模型**：Claude Opus 4.5
- **職責**：戰略規劃，通過訪談理解需求
- **使用方式**：按 `Tab` 切換到計劃模式
- **工作流程**：
  1. 訪談你了解需求
  2. 研究代碼庫
  3. 生成詳細工作計劃
  4. 生成待辦事項清單
  5. 執行 `/start-work` 開始實施

### Atlas（阿特拉斯）- 總協調者

- **模型**：Claude Opus 4.5
- **職責**：執行 Prometheus 生成的計劃
- **特點**：
  - 分配任務給專門 sub-agents
  - 獨立驗證每個任務
  - 跨會話追蹤進度
  - 可隨時恢復工作

### Oracle（先知）- 架構師

- **模型**：GPT-5.2
- **職責**：架構設計、調試複雜問題
- **特點**：高智商戰略支援
- **使用**：`@oracle 幫我看看這個架構合不合理`

### Librarian（圖書管理員）- 研究員

- **模型**：Big Pickle / Claude Sonnet 4.5
- **職責**：查找文檔、搜尋開源實現
- **能力**：
  - 查詢官方文檔（Context7）
  - 搜尋 GitHub 代碼（Grep.app）
  - 研究 best practices
- **使用**：`@librarian 這個功能在官方文檔怎麼寫的？`

### Explore（探索者）- 快速搜索

- **模型**：GPT-5 Nano (Grok Code)
- **職責**：超快速代碼庫搜索
- **特點**：上下文感知 grep
- **使用**：`@explore 找一下所有認證相關的代碼`

### Frontend Engineer - 前端專家

- **模型**：Gemini 3 Pro
- **職責**：UI/UX 開發
- **特點**：擅長前端框架和界面設計

### Multimodal Looker - 媒體分析師

- **模型**：Gemini 3 Flash
- **職責**：分析圖片、PDF、截圖
- **使用**：拖放圖片到終端機

### Metis - 預分析專家

- **模型**：Claude Sonnet 4.5
- **職責**：規劃前的缺口分析
- **特點**：發現潛在問題和模糊需求

### Momus - 審查官

- **模型**：Claude Sonnet 4.5
- **職責**：無情地找出計劃中的漏洞
- **特點**：高精度驗證

### Sisyphus Junior - 執行者

- **模型**：Claude Sonnet 4.5
- **職責**：執行具體任務
- **特點**：由 category system 自動生成

---

## 魔法關鍵詞

### `ulw` 或 `ultrawork` - 全力模式

**最重要的關鍵詞！**

在提示中加入 `ulw` 會啟動：

- ✅ 並行 agent 工作
- ✅ 深度代碼庫探索
- ✅ 自動研究文檔
- ✅ 持續執行直到完成
- ✅ 獨立驗證工作

**示例**：

```
ulw 幫我把項目從 JavaScript 改成 TypeScript
ulw 幫我重構這個項目
ulw 添加 OAuth2 認證
```

### `ultrathink` - 深度思考

觸發深度分析模式，適合複雜問題：

```
ultrathink 這個 bug 到底怎麼產生的？
ultrathink 分析這個架構的潛在問題
```

### `search` / `find` - 搜索模式

全力搜索代碼庫：

```
search 所有處理用戶輸入的地方
find 可能存在安全問題的代碼
```

### `analyze` - 分析模式

深度分析代碼或架構：

```
analyze 這個函數的性能瓶頸
analyze 這個模組的依賴關係
```

---

## 實戰場景

### 場景 1：讓 AI 寫代碼

**提示**：

```
ulw 幫我寫一個待辦事項小程序，能添加、刪除、標記完成
```

**AI 會自動**：
1. 規劃架構
2. 創建文件
3. 實現功能
4. 編寫測試
5. 驗證功能

### 場景 2：修復 Bug

**提示**：

```
運行 npm start 報錯了，幫我看看
```

或直接執行：

```
!npm start
```

**AI 會**：
1. 分析錯誤訊息
2. 查找相關代碼
3. 識別問題
4. 實現修復
5. 驗證修復

### 場景 3：解釋代碼

**提示**：

```
@src/utils/helper.js 這個文件是幹什麼的？
```

**AI 會**：
1. 讀取文件
2. 分析功能
3. 解釋邏輯
4. 指出潛在問題

### 場景 4：重構項目

**步驟 1：切換到計劃模式**

```
我想重構這個項目，你有什麼建議？
```

**步驟 2：查看計劃**

AI 會分析並提出重構方案。

**步驟 3：切回執行模式**

```
就按你說的方案來，開始吧
```

### 場景 5：添加認證功能

**使用 Prometheus 模式**：

1. 按 `Tab` 切換到計劃模式
2. 輸入：

```
我想添加用戶認證功能
```

3. Prometheus 會訪談你：
   - 使用哪種認證方式？
   - 需要支持哪些提供商？
   - 會話管理方式？
   - 等...

4. 確認計劃後，執行：

```
/start-work
```

### 場景 6：從圖片生成 UI

1. 準備設計稿圖片
2. 拖放圖片到終端機
3. 輸入：

```
ulw 根據這張圖片實現前端界面
```

---

## 進階技巧

### 初始化項目（重要）

```bash
/init
```

這會讓 OpenCode：
- 分析項目結構
- 創建 `AGENTS.md` 文件
- 了解技術棧
- 識別編碼規範

### 自定義 AGENTS.md

編輯項目根目錄的 `AGENTS.md`，告訴 AI 你的偏好：

```markdown
# 我的項目

## 專案描述
這是一個電子商務平台，使用 Next.js 和 Supabase。

## 代碼風格
- 使用中文寫註釋
- 變量名用駝峰命名法
- 函數名用動詞開頭

## 技術棧
- 前端：React、Next.js、Tailwind CSS
- 後端：Node.js、Supabase
- 測試：Jest、Testing Library

## 規則
- 所有 API 調用需要錯誤處理
- 組件必須有 TypeScript 類型
- 提交前必須通過 lint 檢查
```

### 使用 Ralph Loop（循環開發）

Ralph Loop 讓 AI 持續工作直到完成：

```
/ralph-loop
```

這會啟動自動循環，AI 會：
1. 執行任務
2. 驗證結果
3. 如果失敗，自動重試
4. 直到成功或達到最大嘗試次數

### 後台任務

讓多個 AI 同時工作：

```
ulw 幫我重構後端 API 同時更新前端文檔
```

AI 會：
- 派出一個 agent 重構後端
- 派出另一個 agent 更新文檔
- 並行執行
- 匯總結果

### 使用 Category System

Oh My OpenCode 自動根據任務類型選擇最優模型：

| Category | 預設模型 | 用途 |
|----------|---------|------|
| `quick` | GPT-5 Nano | 快速任務 |
| `visual` | Gemini 3 Pro | UI/UX 工作 |
| `business-logic` | Claude Opus | 複雜邏輯 |
| `docs` | Claude Sonnet | 文檔編寫 |

### 恢復中斷的工作

如果你的會話中斷：

```bash
# 查看進行中的工作
/start-work

# 選擇要恢復的計劃
# AI 會從上次停止的地方繼續
```

### 使用 MCP 工具

Oh My OpenCode 內建多個 MCP 服務器：

#### Exa - 網路搜索

```
@librarian 搜索 React 19 的最佳實踐
```

#### Context7 - 官方文檔

```
@librarian 查詢 Next.js App Router 的使用方法
```

#### Grep.app - GitHub 搜索

```
@librarian 搜尋其他項目如何實現 WebSocket
```

---

## 常見問題

### Q：AI 寫了一堆看不懂的東西

**A**：告訴它：

```
用更簡單的方式解釋，我是新手
```

或：

```
逐步解釋你剛才做了什麼
```

### Q：AI 改錯代碼了

**A**：輸入 `/undo` 撤銷，然後：

```
剛才的修改有問題，讓我說明我真正想要的...
```

### Q：對話太長，AI 開始變傻

**A**：輸入 `/compact` 清理對話歷史，或開始新對話 `/new`。

### Q：AI 干到一半停了

**A**：

```
ulw 繼續剛才的任務
```

或重新輸入原始提示並加上 `ulw`。

### Q：想讓 AI 看圖片

**A**：直接把圖片拖進終端窗口！支援 PNG、JPG、PDF。

### Q：如何讓 AI 使用特定 agent？

**A**：使用 `@` 提及：

```
@oracle 分析這個架構問題
@librarian 查詢這個 API 的文檔
@explore 搜索所有錯誤處理代碼
```

### Q：可以同時使用多個模型嗎？

**A**：可以！Oh My OpenCode 會自動：

- 用 Gemini 3 Pro 處理前端
- 用 GPT-5.2 處理架構
- 用 Claude Opus 處理主要邏輯
- 用 Haiku/Flash 處理簡單任務

你只需要配置好 API keys，系統會自動選擇最優模型。

---

## 最佳實踐

### 推薦工作流程

1. **進入項目目錄**
   ```bash
   cd my-project
   ```

2. **啟動 OpenCode**
   ```bash
   opencode
   ```

3. **初始化（首次）**
   ```
   /init
   ```

4. **複雜任務：使用 Prometheus 模式**
   - 按 `Tab` 切換到計劃模式
   - 描述需求
   - 回答訪談問題
   - 查看生成的計劃
   - 按 `Tab` 切回執行模式
   - 執行 `/start-work`

5. **簡單任務：直接 ulw**
   ```
   ulw 幫我添加錯誤處理
   ```

### 提示工程建議

#### ✅ 好的提示

```
ulw 添加用戶認證，使用 NextAuth.js，支援 Google 和 GitHub 登入
```

**特點**：
- 使用 `ulw` 啟動全力模式
- 明確指定功能
- 說明技術偏好
- 列出具體需求

#### ❌ 不好的提示

```
幫我弄個登入
```

**問題**：
- 過於模糊
- 缺少上下文
- 沒有說明偏好

### 何時使用哪種模式

| 情況 | 推薦方式 |
|------|---------|
| 快速修復 bug | 直接 `ulw` |
| 添加小功能 | 直接 `ulw` |
| 重構大模組 | Prometheus + `/start-work` |
| 新建功能模組 | Prometheus + `/start-work` |
| 架構諮詢 | `@oracle` |
| 文檔查詢 | `@librarian` |
| 代碼搜索 | `@explore` |

### Token 管理建議

Oh My OpenCode 設計時考慮了 token 效率：

1. **使用適當的模型**
   - 簡單任務用 Haiku/Flash/Nano
   - 複雜任務用 Opus/GPT-5.2

2. **利用並行處理**
   - 多個便宜模型並行工作
   - 比單個昂貴模型更高效

3. **定期壓縮對話**
   - 使用 `/compact` 清理歷史
   - 保持上下文精簡

4. **信任 agent 的選擇**
   - Category system 自動選擇最優模型
   - 無需手動指定

---

## 進階主題

### 模型配置範例

編輯 `~/.config/opencode/oh-my-opencode.json`：

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/master/assets/oh-my-opencode.schema.json",

  "agents": {
    // 主 agent 使用 Claude Opus
    "sisyphus": {
      "model": "anthropic/claude-opus-4-5"
    },

    // Oracle 使用 GPT-5.2 獲得高智商
    "oracle": {
      "model": "openai/gpt-5.2"
    },

    // Librarian 使用便宜模型
    "librarian": {
      "model": "zai-coding-plan/glm-4.7"
    },

    // Explore 使用超快模型
    "explore": {
      "model": "opencode/gpt-5-nano"
    }
  },

  "categories": {
    // 快速任務用 nano
    "quick": {
      "model": "opencode/gpt-5-nano"
    },

    // UI 任務用 Gemini
    "visual": {
      "model": "google/gemini-3-flash"
    }
  },

  "experimental": {
    // 激進的上下文壓縮
    "aggressive_truncation": true
  }
}
```

### LSP 整合

Oh My OpenCode 自動整合 LSP：

- **重構**：安全地重命名、移動函數
- **診斷**：實時錯誤檢測
- **定義跳轉**：快速導航
- **AST-Grep**：語法感知搜索

### 內建 Skills

#### Git Master

自動化 Git 工作流：

```
使用 git-master 技能提交這些變更
```

#### Playwright

瀏覽器自動化：

```
使用 playwright 測試這個登入流程
```

### Hooks 系統

25+ 內建 hooks，可通過配置禁用：

```jsonc
{
  "disabled_hooks": [
    "comment-checker",      // 允許更多註釋
    "todo-continuation"     // 允許提前停止
  ]
}
```

---

## 總結

### 七句話記住全部

1. **打開**：終端輸入 `opencode`
2. **說話**：直接打字告訴 AI 你想做什麼
3. **魔法詞**：加 `ulw` 讓 AI 全力工作
4. **引用文件**：用 `@文件名`
5. **執行命令**：用 `/命令`
6. **撤銷**：用 `/undo`
7. **切換模式**：按 `Tab`

### 最佳流程速記

```
進入項目 → opencode → /init → Tab（計劃）→ 描述需求 →
Tab（執行）→ /start-work → 完成
```

### 從實習生到項目經理

| 階段 | 特徵 |
|------|------|
| **普通 OpenCode** | 一個 AI 助手 |
| **Oh My OpenCode** | 一整個 AI 團隊 |
| **ulw 模式** | 自主運作的團隊 |
| **Prometheus + Atlas** | 有計劃的團隊 |

---

## 資源連結

- **OpenCode 官方文檔**：https://opencode.ai/docs/
- **Oh My OpenCode GitHub**：https://github.com/code-yeongyu/oh-my-opencode
- **Discord 社群**：https://discord.gg/PUwSMR9XNk
- **OpenCode Zen**：https://opencode.ai/auth

---

**最後的建議**：

不要過度思考。安裝 Oh My OpenCode，輸入 `ulw`，然後相信你的 AI 團隊。他們比你想象的更能幹。

**現在，去試試吧！** 🚀
