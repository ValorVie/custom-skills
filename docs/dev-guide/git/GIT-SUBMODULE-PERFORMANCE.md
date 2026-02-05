# Git Submodule 效能調優指南

本指南說明如何優化多 Submodule 專案在 IDE 中的 Git 效能。

---

## 快速參考

| 問題 | 解決方案 |
|------|----------|
| IDE Git 載入緩慢 | 停用 `git.detectSubmodules` |
| 背景操作耗資源 | 停用 `git.autofetch`，延長刷新間隔 |
| 需要手動刷新 | `Cmd+Shift+P` → `Git: Refresh` |
| 查看所有狀態 | 終端機執行 `gss` alias |

---

## 問題診斷

### 檢查專案結構

```bash
# Git 倉庫大小
du -sh .git
du -sh .git/modules/

# Submodule 數量與大小
git submodule foreach --quiet 'echo "$path: $(du -sh . | cut -f1)"'

# 檔案總數
find . -type f | wc -l
```

### 常見效能殺手

| 因素 | 影響 | 檢查方式 |
|------|------|----------|
| Submodule 數量 | 每個都要解析 Git 狀態 | `git submodule status \| wc -l` |
| .git/modules/ 大小 | 儲存所有歷史 | `du -sh .git/modules/` |
| 大型檔案 | log、core dump、binary | `find . -size +10M -type f` |
| 深層目錄 | 掃描耗時 | `find . -type d \| wc -l` |

---

## IDE 設定優化

### VSCode / Antigravity / Cursor

在 `settings.json` 中加入：

```json
{
  // === Git 效能優化（必要） ===

  // 停用 submodule 自動偵測
  "git.detectSubmodules": false,

  // 停用自動 fetch
  "git.autofetch": false,

  // 延長自動刷新間隔（毫秒，預設 3000）
  "git.autoRefreshInterval": 60000,

  // === 檔案監控優化（建議） ===

  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/node_modules/**": true,
    "**/vendor/**": true,
    "**/logs/**": true,
    "**/*.log": true
  },

  "search.exclude": {
    "**/node_modules": true,
    "**/vendor": true,
    "**/logs": true,
    "**/*.log*": true,
    "**/core.*": true
  }
}
```

### 手動刷新 Git 狀態

| 方式 | 操作 |
|------|------|
| 命令面板 | `Cmd+Shift+P` → `Git: Refresh` |
| Source Control 面板 | 點擊右上角 🔄 刷新圖示 |
| 快捷鍵 | 可自訂綁定到 `git.refresh` |

---

## 終端機操作指南

### 推薦的 Shell Alias

加入 `~/.zshrc` 或 `~/.bashrc`：

```bash
# === Git Submodule 快速操作 ===

# 查看所有 submodule 狀態
alias gss='git submodule foreach --quiet "echo \"=== \$name ===\" && git status -s"'

# 只顯示有變更的 submodule
alias gssc='git submodule foreach --quiet "if [ -n \"\$(git status -s)\" ]; then echo \"=== \$name ===\" && git status -s; fi"'

# 所有 submodule fetch
alias gsf='git submodule foreach "git fetch --all"'

# 所有 submodule pull
alias gsp='git submodule foreach "git pull origin \$(git rev-parse --abbrev-ref HEAD) || true"'

# 查看 submodule 摘要
alias gsum='git submodule summary'
```

套用設定：
```bash
source ~/.zshrc
```

### 常用指令

#### 查看狀態

```bash
# 所有 submodule 簡潔狀態
git submodule foreach --quiet 'echo "=== $name ===" && git status -s'

# 只看有變更的
git submodule foreach --quiet 'if [ -n "$(git status -s)" ]; then echo "=== $name ===" && git status -s; fi'

# Submodule 版本狀態
git submodule status
```

#### 操作特定 Submodule

```bash
# 使用 -C 參數（不切換目錄）
git -C <submodule> status
git -C <submodule> diff
git -C <submodule> add .
git -C <submodule> commit -m "訊息"

# 或進入目錄操作
cd <submodule>
git status
```

#### 批次操作

```bash
# 所有 submodule 執行 fetch
git submodule foreach 'git fetch --all'

# 所有 submodule 執行 pull
git submodule foreach 'git pull origin $(git rev-parse --abbrev-ref HEAD) || true'

# 更新到 remote 最新 commit
git submodule update --remote
```

#### 初始化與同步

```bash
# 初始化並更新所有 submodule
git submodule update --init --recursive

# 同步 submodule URL（.gitmodules 變更後）
git submodule sync --recursive
```

---

## 維護建議

### 定期清理大檔案

```bash
# 找出大檔案
find . -type f -size +10M -not -path "./.git/*" | head -20

# 清除 core dump
find . -name "core.*" -type f -size +1M -delete

# 清除 log（確認後執行）
find . -name "*.log" -type f -size +10M -delete
```

### .gitignore 建議

確保各 submodule 的 `.gitignore` 包含：

```gitignore
# 大型檔案
core.*
*.log
*.log.*
*.log.gz

# 暫存目錄
logs/
tmp/
cache/

# 依賴目錄
node_modules/
vendor/
```

### Git 倉庫壓縮

```bash
# 主倉庫
git gc --aggressive

# 所有 submodule
git submodule foreach 'git gc --aggressive'
```

---

## 故障排除

### IDE 仍然緩慢

1. 確認設定生效：重新載入視窗 `Cmd+Shift+P` → `Developer: Reload Window`
2. 檢查擴充套件：停用可能干擾 Git 的擴充套件
3. 檢查 `.git/modules/` 大小，考慮是否需要 shallow clone

### Submodule URL 問題

```bash
# 檢查 URL
cat .gitmodules

# 若使用本地路徑且路徑不存在會超時
# 修改為有效 URL
git config submodule.<name>.url "新的 URL"

# 重新同步
git submodule sync
```

### Submodule 狀態不同步

```bash
# 完整重新同步
git submodule sync --recursive
git submodule update --init --recursive --force
```

---

## 相關文件

- [Git Submodule 操作指南](Git%20Submodule%20操作指南.md)
- [Git 工作流程指南](GIT-WORKFLOW.md)
