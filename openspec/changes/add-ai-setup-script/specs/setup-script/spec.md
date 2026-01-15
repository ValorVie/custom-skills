# 能力：AI 環境設定腳本

## 新增需求 (ADDED Requirements)

### 需求：安裝邏輯 (Install Logic)
腳本必須實作 `install` 指令以執行初始設定。

#### 場景：macOS 全新安裝
給定已安裝 Homebrew 的全新 macOS 環境
當執行 `uv run script/main.py install` 時
則應該：
1. 檢查 Node.js 與 Git。
2. 建立 `~/.claude/skills`、`~/.config/custom-skills` 等目錄。
3. 安裝全域 NPM 套件（`@anthropic-ai/claude-code` 等）。
4. Clone `custom-skills`、`superpowers`、`universal-dev-standards`。
5. 複製 skills 到目標目錄。

#### 場景：Windows 全新安裝
給定已安裝 PowerShell 的全新 Windows 環境
當執行 `uv run script/main.py install` 時
則應該使用 Windows 路徑與指令執行對應步驟。

### 需求：維護邏輯 (Maintain Logic)
腳本必須實作 `maintain` 指令以進行每日更新。

#### 場景：每日更新
給定已安裝的環境
當執行 `uv run script/main.py maintain` 時
則應該：
1. 更新全域 NPM 套件。
2. 在已 clone 的儲存庫中執行 `git pull`。
3. 重新複製 skills 到目標目錄，覆寫舊檔。
4. 清理指定的過時檔案/目錄。

### 需求：跨平台支援 (Multi-platform Support)
腳本必須偵測作業系統並使用適當的路徑/指令。

#### 場景：偵測作業系統
當腳本啟動時
則應該識別當前是 macOS/Linux 或 Windows 並相應設定路徑。
