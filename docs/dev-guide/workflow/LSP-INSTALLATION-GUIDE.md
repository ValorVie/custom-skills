# LSP 安裝指南（PHP / Python / Rust / JS / TS / YAML / JSON / TOML / Markdown）

這份文件整理常用語言的 Language Server 安裝方式，適用於 Neovim、VS Code、OpenCode 等需要 LSP Server 可執行檔的環境。

## LSP 作用是什麼？

LSP（Language Server Protocol）是「編輯器」和「語言分析器」之間的通訊協定。

你可以把它想成：
- 編輯器負責顯示與操作（游標、UI、快捷鍵）
- Language Server 負責理解程式語意（型別、符號、引用關係）

實際能帶來的功能：

- 自動補全（不只是關鍵字，而是依型別推斷）
- 跳到定義 / 找所有引用
- 即時診斷（語法錯誤、型別錯誤、未使用變數）
- 重新命名符號（跨檔案一致修改）
- Hover 文件與函式簽名提示
- 程式碼動作（快速修正、匯入建議）

為什麼要安裝 LSP：

- 沒有 LSP 時，編輯器多半只剩語法上色與簡單字串搜尋
- 有 LSP 時，才有 IDE 級的語意能力（尤其大型專案差異很明顯）

---

## 快速總覽

| 語言 | 推薦 LSP Server | 安裝方式（推薦） | 驗證指令 |
|------|------------------|------------------|----------|
| PHP | PHPActor | `composer global require phpactor/phpactor` | `phpactor --version` |
| Python | basedpyright | `uv tool install basedpyright` | `basedpyright --version` |
| Rust | rust-analyzer | `rustup component add rust-analyzer` | `rust-analyzer --version` |
| JavaScript | typescript-language-server | `npm i -g typescript typescript-language-server` | `typescript-language-server --version` |
| TypeScript | typescript-language-server | `npm i -g typescript typescript-language-server` | `typescript-language-server --version` |
| YAML | yaml-language-server | `npm i -g yaml-language-server` | `yaml-language-server --help` |
| JSON | vscode-json-language-server | `npm i -g vscode-langservers-extracted` | `vscode-json-language-server --help` |
| TOML | taplo | macOS/Linux: `brew install taplo`；Windows: 下載 Releases binary | `taplo --version` |
| Markdown | marksman | macOS/Linux: `brew install marksman`；Windows: 下載 Releases 預編譯 binary | `marksman --version` |

---

## Composer 安裝（PHPActor 前置需求）

若系統尚未安裝 Composer，先完成這一步再安裝 PHPActor。

### macOS / Linux

```bash
php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
php composer-setup.php
php -r "unlink('composer-setup.php');"
sudo mv composer.phar /usr/local/bin/composer
```

### Windows（PowerShell）

請使用官方安裝程式：

- `https://getcomposer.org/Composer-Setup.exe`

安裝完成後重開終端機。

### 驗證

```bash
composer --version
```

---

## PHP（PHPActor）

```bash
composer global require phpactor/phpactor
```

驗證：

```bash
phpactor --version
```

備註：
- PHPActor 為免費開源方案，適合大型專案。
- 若仍想用 Intelephense，免費版可能在大型專案遇到索引限制。

---

## Python（basedpyright）

推薦使用 `uv` 安裝（與本專案工具鏈一致）：

```bash
uv tool install basedpyright
```

或使用 pip：

```bash
pip install basedpyright
```

驗證：

```bash
basedpyright --version
```

補充：
- `basedpyright-langserver` 是 LSP server 進程，本身需要 `--stdio` / `--node-ipc` / `--socket` 其中一種傳輸參數，不支援 `--version` 這種一般 CLI 驗證方式。
- 若要確認 langserver 可啟動，可用：`basedpyright-langserver --stdio`（會進入等待輸入狀態，`Ctrl+C` 離開）。

---

## Rust（rust-analyzer）

先安裝 Rust 工具鏈（若尚未安裝）：

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

安裝 `rust-analyzer` component：

```bash
rustup component add rust-analyzer
```

驗證：

```bash
rust-analyzer --version
```

---

## JavaScript / TypeScript（typescript-language-server）

```bash
npm i -g typescript typescript-language-server
```

驗證：

```bash
typescript-language-server --version
tsc --version
```

說明：
- JS 與 TS 一般共用同一個 `typescript-language-server`。
- 若需要額外 lint 診斷，可再搭配 `vscode-eslint-language-server`（非必要）。

---

## YAML（yaml-language-server）

```bash
npm i -g yaml-language-server
```

驗證：

```bash
yaml-language-server --help
```

補充：
- 常見 LSP client 啟動命令為 `yaml-language-server --stdio`。

---

## JSON（vscode-json-language-server）

```bash
npm i -g vscode-langservers-extracted
```

驗證：

```bash
vscode-json-language-server --help
```

補充：
- `vscode-json-language-server` 由 `vscode-langservers-extracted` 提供。
- 常見 LSP client 啟動命令為 `vscode-json-language-server --stdio`。

---

## TOML（taplo）

macOS / Linux（Homebrew）：

```bash
brew install taplo
```

Rust toolchain（Cargo）：

```bash
cargo install taplo-cli --locked --features lsp
```

Windows（官方 pre-built binary）：

1. 到 releases 頁面下載 Windows 版本 binary：
   - `https://github.com/tamasfe/taplo/releases`
2. 解壓並將 `taplo.exe` 放到 `PATH`

驗證：

```bash
taplo --version
```

補充：
- Taplo LSP 啟動命令為 `taplo lsp stdio`。
- 若使用 `@taplo/cli` 的 NPM 預設 build，通常不包含 LSP 功能。

---

## Markdown（marksman）

推薦使用 `marksman` 作為 `.md` 的 LSP server。

macOS / Linux（Homebrew）：

```bash
brew install marksman
```

驗證：

```bash
marksman --version
```

Windows（官方 pre-built binary）：

1. 到 releases 頁面下載 Windows 版本 binary：
   - `https://github.com/artempyanykh/marksman/releases`
2. 下載 `marksman-windows.exe`
3. 重新命名為 `marksman.exe`
4. 把 `marksman.exe` 放到你的 `PATH` 目錄（例如使用者自訂 `bin` 目錄）

驗證：

```powershell
marksman --version
```

補充：
- `marksman` 是 Markdown 專用 LSP server。
- 在常見 LSP client 設定中，啟動命令通常是 `marksman server`（不是 `--stdio`）。

---

## 常見問題

### 1) 安裝成功但仍顯示 command not found

通常是 PATH 沒包含使用者執行檔目錄。

- `uv tool` 常見位置：`~/.local/bin`
- `npm -g` 常見位置：`$(npm config get prefix)/bin`

檢查：

```bash
which basedpyright-langserver
which typescript-language-server
which yaml-language-server
which vscode-json-language-server
which taplo
which phpactor
which rust-analyzer
which marksman
```

### 2) LSP 客戶端抓不到 server

確認你的編輯器設定使用的是正確可執行檔名稱，例如：

- Python: `basedpyright-langserver`
- JS/TS: `typescript-language-server`
- YAML: `yaml-language-server`
- JSON: `vscode-json-language-server`
- TOML: `taplo`
- PHP: `phpactor`
- Rust: `rust-analyzer`
- Markdown: `marksman`

---

## 編輯器設定範例

以下提供常見開發環境的最小可用設定。

### Neovim（nvim-lspconfig）

```lua
local lspconfig = require("lspconfig")

lspconfig.phpactor.setup({})
lspconfig.rust_analyzer.setup({})
lspconfig.ts_ls.setup({})
lspconfig.basedpyright.setup({})
lspconfig.yamlls.setup({})
lspconfig.jsonls.setup({})
lspconfig.taplo.setup({})
lspconfig.marksman.setup({})
```

備註：
- `ts_ls` 對應 TypeScript/JavaScript 的 `typescript-language-server`。
- 若你的 `nvim-lspconfig` 版本不支援 `basedpyright`，可先用 `pyright` 代替。
- `yamlls` 對應 `yaml-language-server`，`jsonls` 對應 `vscode-json-language-server`，`taplo` 對應 TOML LSP。

### VS Code

建議安裝對應擴充套件：

- PHP: `phpactor.phpactor`
- Python: `detachhead.basedpyright`
- Rust: `rust-lang.rust-analyzer`
- YAML: `redhat.vscode-yaml`
- TOML: `tamasfe.even-better-toml`
- JSON: 內建 JSON 語言服務（通常不需額外安裝）
- JS/TS: 內建 TypeScript 語言服務（通常不需額外安裝）

可選設定（`.vscode/settings.json`）：

```json
{
  "python.analysis.typeCheckingMode": "strict",
  "rust-analyzer.check.command": "clippy"
}
```

### OpenCode（自訂 LSP）

若出現「No LSP server configured for extension」訊息，可在 `oh-my-opencode.json` 增加 `lsp` 設定：

```json
{
  "lsp": {
    "basedpyright": {
      "command": ["basedpyright-langserver", "--stdio"],
      "extensions": [".py", ".pyi"]
    },
    "typescript": {
      "command": ["typescript-language-server", "--stdio"],
      "extensions": [".js", ".jsx", ".ts", ".tsx"]
    },
    "yaml-ls": {
      "command": ["yaml-language-server", "--stdio"],
      "extensions": [".yaml", ".yml"]
    },
    "jsonls": {
      "command": ["vscode-json-language-server", "--stdio"],
      "extensions": [".json", ".jsonc"]
    },
    "taplo": {
      "command": ["taplo", "lsp", "stdio"],
      "extensions": [".toml"]
    },
    "marksman": {
      "command": ["marksman", "server"],
      "extensions": [".md", ".markdown", ".mdx"]
    }
  }
}
```
