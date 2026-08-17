# Neovim（LazyVim）完整安裝與使用指南

## 目錄

- [適用情境](#適用情境)
- [前置條件](#前置條件)
- [透過 settingZsh 安裝](#透過-settingzsh-安裝)
- [設定架構](#設定架構)
- [日常操作](#日常操作)
- [語言工具](#語言工具)
- [格式化與 Markdown](#格式化與-markdown)
- [SSH、OSC 52 與 tmux](#sshosc-52-與-tmux)
- [驗證與更新](#驗證與更新)
- [疑難排解](#疑難排解)
- [相關資源](#相關資源)

---

## 適用情境

這份指南說明如何透過 [ValorVie/settingZsh](https://github.com/ValorVie/settingZsh) 安裝 Neovim 與 LazyVim 配置，並涵蓋常用快捷鍵、語言工具、格式化、SSH clipboard 與 tmux 整合。

- 適用於 Linux、macOS、Windows，以及從 Windows 或其他桌面系統 SSH 到遠端主機的情境。
- 適合希望取得接近 VS Code 開發體驗，但仍保留 Vim 操作模式的人。
- 不包含 DAP、Neotest 或 AI Extra；這些功能可依專案需求另行啟用。
- 不會把任何 SSH host、私鑰或私人專案清單寫入 Neovim 配置。

完成後應可使用 Snacks 找檔與搜尋、LSP 跳轉與診斷、Prettier／Black 格式化、Markdown Preview、lazygit，以及 OSC 52 clipboard。

## 前置條件

- Git 與可連線至 GitHub 的網路。
- Linux 或 macOS 使用 Bash；Windows 使用 PowerShell／Batch 入口。
- 終端建議使用支援 Nerd Font 的字型。settingZsh 預設安裝 Maple Mono NL NF CN。
- SSH 複製需要外層 terminal 支援 OSC 52。
- 若在 tmux 內使用 OSC 52，完整推薦設定需要 tmux 3.3 以上。

## 透過 settingZsh 安裝

### Linux 與 macOS

```bash
git clone https://github.com/ValorVie/settingZsh.git
cd settingZsh
chmod +x setup.sh
./setup.sh
```

安裝程式會詢問是否安裝 editor 環境。輸入 `y` 後會部署 Vim、Neovim、nvm、Node.js、ripgrep、fd 與 lazygit；不同平台由 apt、Homebrew 或官方 release 提供套件。

Linux／macOS 可以安全重跑安裝。Neovim 配置相同時會略過；來源更新時，目前配置會保存到固定的 `~/.config/nvim.bak`，再部署新版，不會產生巢狀 backup。

### Windows

```powershell
git clone https://github.com/ValorVie/settingZsh.git
cd settingZsh
.\setup.bat
```

Windows 入口透過 winget 安裝 Neovim、nvm-windows、ripgrep、fd 與 lazygit，配置放在 `%LOCALAPPDATA%\nvim`。

### 第一次啟動

```bash
nvim
```

第一次啟動會依 `lazy-lock.json` 安裝 LazyVim 與外掛。等安裝完成後離開並重新開啟 Neovim；語言 server 可能在第一次開啟對應 workspace 時才由 Mason 補齊。

## 設定架構

settingZsh 內的 Neovim 配置位於 `nvim/`：

```text
nvim/
├── init.lua
├── lazyvim.json
├── lazy-lock.json
└── lua/
    ├── config/
    │   ├── autocmds.lua
    │   ├── keymaps.lua
    │   ├── options.lua
    │   ├── path.lua
    │   ├── phpstan.lua
    │   ├── tooling.lua
    │   └── whitespace.lua
    └── plugins/
        ├── editor.lua
        ├── languages.lua
        └── markdown.lua
```

主要選項如下：

| 選項 | 設定 | 說明 |
|------|------|------|
| 行號 | 絕對行號 | `<Leader>uL` 切換相對行號 |
| 縮排 | 4 個空格 | `tabstop`、`shiftwidth`、`softtabstop` 均為 4 |
| 換行 | 啟用 | 長行在視窗寬度處折行 |
| 滑鼠 | 關閉 | 避免攔截終端原生選取 |
| Clipboard | SSH 使用 OSC 52 | 非 SSH 保留 Neovim 原生 provider |
| 檔案結尾 | 保留 final newline | EditorConfig 可覆寫專案行為 |

Navigation 固定使用 Snacks picker 與 Snacks Explorer。Telescope、fzf-lua 與 Neo-tree 不會同時接管核心快捷鍵。

預設搜尋會略過 `.git`、`node_modules`、`vendor`、`target`、`dist`、`build`、cache 與虛擬環境等大型目錄，且不遞迴追蹤 symlink。

## 日常操作

Leader 鍵是空白鍵。按下 `<Space>` 後稍等，which-key 會顯示可用指令。

### 模式與基本編輯

| 操作 | 按鍵 |
|------|------|
| 進入 Insert mode | `i`、`a`、`o` |
| 回到 Normal mode | `Esc` 或 `jk` |
| 儲存 | `:w` |
| 離開 | `:q` |
| 儲存並離開 | `:wq` |
| 復原／重做 | `u`／`Ctrl+r` |
| 複製整行 | `yy` |
| 貼上 | `p`／`P` |

### 找檔、搜尋與專案

| 功能 | 按鍵 |
|------|------|
| 找檔 | `<Leader>ff` |
| 全文搜尋 | `<Leader>/` |
| 最近檔案 | `<Leader>fr` |
| 已開啟 Buffer | `<Leader>fb` |
| 檔案總管 | `<Leader>e` |
| 最近專案 | `<Leader>fp` |
| 恢復專案 Session | `<Leader>qs` |

### 路徑複製

| 位置 | 按鍵 | 輸出 |
|------|------|------|
| 一般 Buffer | `<Leader>yp` | 專案相對路徑 |
| 一般 Buffer | `<Leader>yL` | 專案相對 `path:line` |
| Snacks Explorer | `Y` | 絕對路徑 |
| Snacks Explorer | `gY` | 專案相對路徑 |

### 程式碼與 Git

| 功能 | 按鍵／指令 |
|------|------------|
| 跳至定義 | `gd` |
| 查看參照 | `gr` |
| 重新命名 | `<Leader>cr` |
| Code Action | `<Leader>ca` |
| 手動格式化 | `<Leader>cf` |
| 開啟終端 | `<Leader>ft` |
| 開啟 lazygit | `<Leader>gg` |
| LSP 狀態 | `:LspInfo` |

## 語言工具

| 語言 | 主要工具 |
|------|----------|
| PHP | Intelephense、PHPCS、php-cs-fixer；專案有 `vendor/bin/phpstan` 與設定時才執行 PHPStan |
| Python | Pyright、Ruff analysis、Black formatting、venv-selector |
| TypeScript／JavaScript | vtsls、ESLint、Prettier |
| Rust | rust-analyzer、rustaceanvim、Cargo |
| HTML／CSS | html、cssls、Prettier |
| JSON／YAML | jsonls、yamlls、SchemaStore |
| Docker／Compose | Docker／Compose language server、Hadolint |
| Markdown | Marksman、Prettier、Markdown Preview、TOC |

外掛宣告、可執行工具存在與 LSP attach 是三個不同狀態。遇到沒有補全或跳轉時，依序檢查：

```vim
:Lazy
:Mason
:LspInfo
:checkhealth
```

## 格式化與 Markdown

LazyVim 預設允許 format-on-save，可用 `<Leader>uf` 暫時切換。專案的 `.editorconfig` 優先於個人縮排、EOL、final newline 與 trailing-whitespace fallback。

Markdown 的行尾兩個空白代表硬換行，因此個人 trailing-whitespace fallback 會跳過 Markdown。Prettier 與 preview 保留；markdownlint 工具仍會安裝，但預設不發布 MD013、MD031、MD040 等格式 diagnostics。Marksman 的失效連結與文件結構 diagnostics 仍會顯示。

```vim
:MarkdownPreview
:MarkdownPreviewStop
```

也可按 `<Leader>cp` 切換 Markdown Preview，按 `<Leader>um` 切換終端內的 Markdown 渲染。

## SSH、OSC 52 與 tmux

### Neovim 的 clipboard register

SSH 下 settingZsh 強制使用 Neovim 內建 OSC 52 provider，但不把 `'clipboard'` 設為 `unnamedplus`。普通 `y` 仍只寫入 Neovim unnamed register；要複製到外層 terminal clipboard，請明確使用 `+` register：

```text
Visual 選取後按 "+y
Normal mode 使用 "+yy 或 "+y{motion}
```

這個選擇可避免普通 `p` 嘗試透過 OSC 52 讀取外層 clipboard。許多 terminal 支援 OSC 52 寫入，但不支援讀取；一般貼上可使用 terminal 原生貼上快捷鍵。

### 原生 Vim fallback

settingZsh 的 `vim/.vimrc` 也支援相同的 `"+yy`、`"+y{motion}` 與 Visual `"+y`。它不依賴 Vim 的 `+clipboard` feature，只需要遠端主機有 `base64`，並且外層 terminal 接受 OSC 52。

### tmux 設定

若 Vim／Neovim 位於 tmux 內，請在 tmux 3.3 以上加入：

```bash
set -g set-clipboard on
set -g allow-passthrough on
```

重新載入後檢查：

```bash
tmux show-options -gqv set-clipboard
tmux show-options -gqv allow-passthrough
```

兩行都應輸出 `on`。完整說明見 [tmux 終端多工器完整指南](./TMUX-GUIDE.md#系統剪貼簿整合)。

## 驗證與更新

### 安裝後檢查

```bash
nvim --version
rg --version
lazygit --version
```

在 settingZsh 儲存庫根目錄可執行不連網的配置測試：

```bash
bash tests/test_nvim_config.sh
```

確認外掛與語言工具已安裝後，再執行 opt-in runtime acceptance：

```bash
bash tests/accept_nvim_runtime.sh --run
```

這個 acceptance 會檢查主要 picker、必要 executable 與代表性 LSP attach，不會安裝或更新 package。OSC 52 是否真的進入外層 clipboard，以及瀏覽器能否開啟 preview，仍需要人工確認。

### 更新

```bash
./update.sh
```

Windows 使用：

```powershell
.\update.bat
```

更新前若有自己的 Neovim 客製化，先確認設定已納入版本控制或另有備份。

## 疑難排解

| 問題 | 先檢查 | 處理方式 |
|------|--------|----------|
| 啟動後仍是陽春畫面 | `:Lazy` | 等待外掛完成，再重開 Neovim |
| LSP 沒有 attach | `:Mason`、`:LspInfo` | 確認 executable、workspace root 與專案依賴 |
| 找不到檔案 | `<Leader>ff` | 確認檔案是否位於 ignore／exclude 目錄 |
| Markdown 格式警告太多 | `:lua vim.print(vim.diagnostic.get(0))` | settingZsh 預設已關閉 markdownlint；Marksman 仍會報失效連結 |
| SSH `y` 沒進系統剪貼簿 | 改試 `"+y` | 普通 `y` 不會自動寫入 `+` register |
| `"+y` 在 tmux 內失效 | `tmux show-options` | 啟用 `set-clipboard` 與 `allow-passthrough` |
| OSC 52 貼上失敗 | terminal clipboard read 支援 | 改用 Windows Terminal、WezTerm 等 terminal 的原生貼上 |
| Browser preview 沒開啟 | `:checkhealth`、`:MarkdownPreview` | SSH 環境可手動開啟 preview URL 或使用 port forwarding |

## 相關資源

- [ValorVie/settingZsh](https://github.com/ValorVie/settingZsh)
- [settingZsh README](https://github.com/ValorVie/settingZsh/blob/main/README.md)
- [settingZsh Editor 使用指南](https://github.com/ValorVie/settingZsh/blob/main/docs/editor-guide.md)
- [LazyVim 官方文件](https://www.lazyvim.org/)
- [Neovim OSC 52 說明](https://neovim.io/doc/user/provider.html#clipboard-osc52)
- [tmux 終端多工器完整指南](./TMUX-GUIDE.md)
- [LSP 安裝指南](../workflow/LSP-INSTALLATION-GUIDE.md)
