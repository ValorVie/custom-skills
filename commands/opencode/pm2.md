---
description: "PM2 Init - 自動分析專案並生成 PM2 服務管理命令"
argument-hint: "<project-path>"
---

# PM2 Init | 服務管理初始化

自動掃描專案結構，偵測服務類型，生成 PM2 配置檔與管理命令。

## 用法

```
/pm2 <project-path>
```

## 工作流程

1. 檢查 PM2 是否已安裝（未安裝則提示 `npm install -g pm2`）
2. 掃描專案結構，識別服務（前端/後端/資料庫）
3. 生成配置檔與管理命令

## 服務偵測

| 類型 | 偵測方式 | 預設 Port |
|------|----------|-----------|
| Vite | vite.config.* | 5173 |
| Next.js | next.config.* | 3000 |
| Nuxt | nuxt.config.* | 3000 |
| CRA | react-scripts in package.json | 3000 |
| Express/Node | server/backend/api 目錄 + package.json | 3000 |
| Django | manage.py + settings.py | 8000 |
| FastAPI | main.py + uvicorn/fastapi in requirements.txt 或 pyproject.toml | 8000 |
| Flask | app.py + flask in requirements.txt | 5000 |
| Go | go.mod / main.go | 8080 |

**Port 偵測優先順序**：使用者指定 > .env > 配置檔 > scripts args > 預設 port

## 生成檔案

```
project/
├── ecosystem.config.cjs              # PM2 配置
├── {backend}/start.cjs               # Python 包裝腳本（若適用）
└── commands/opencode/
    ├── pm2-all.md                    # 啟動全部 + monit
    ├── pm2-all-stop.md              # 停止全部
    ├── pm2-all-restart.md           # 重啟全部
    ├── pm2-{port}.md                # 啟動單一 + logs
    ├── pm2-{port}-stop.md           # 停止單一
    ├── pm2-{port}-restart.md        # 重啟單一
    ├── pm2-logs.md                  # 檢視全部日誌
    └── pm2-status.md               # 檢視狀態
```

## ecosystem.config.cjs

**必須使用 `.cjs` 副檔名**

```javascript
module.exports = {
  apps: [
    // Node.js (Vite/Next/Nuxt)
    {
      name: 'project-3000',
      cwd: './packages/web',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 3000',
      env: { NODE_ENV: 'development' }
    },
    // Python (FastAPI/Django)
    {
      name: 'project-8000',
      cwd: './backend',
      script: 'start.cjs',
      interpreter: 'node',
      env: { PYTHONUNBUFFERED: '1' }
    }
  ]
}
```

**框架腳本對映：**

| 框架 | script | args |
|------|--------|------|
| Vite | `node_modules/vite/bin/vite.js` | `--port {port}` |
| Next.js | `node_modules/next/dist/bin/next` | `dev -p {port}` |
| Nuxt | `node_modules/nuxt/bin/nuxt.mjs` | `dev --port {port}` |
| Express | `src/index.js` 或 `server.js` | - |
| Django | （使用 start.cjs 包裝） | - |
| FastAPI | （使用 start.cjs 包裝） | - |

### Python 包裝腳本 (start.cjs)

**FastAPI：**
```javascript
const { spawn } = require('child_process');
const proc = spawn('python3', ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'], {
  cwd: __dirname, stdio: 'inherit'
});
proc.on('close', (code) => process.exit(code));
```

**Django：**
```javascript
const { spawn } = require('child_process');
const proc = spawn('python3', ['manage.py', 'runserver', '0.0.0.0:8000'], {
  cwd: __dirname, stdio: 'inherit'
});
proc.on('close', (code) => process.exit(code));
```

## 重要規則

1. **配置檔**：`ecosystem.config.cjs`（非 .js）
2. **Node.js**：直接指定 bin 路徑
3. **Python**：使用 Node.js 包裝腳本
4. **最小內容**：每個命令檔只有 1-2 行描述 + bash 區塊
5. **直接執行**：不需 AI 解析，直接執行 bash 命令

## 執行

根據 `$ARGUMENTS`，執行初始化：

1. 掃描專案識別服務
2. 生成 `ecosystem.config.cjs`
3. 為 Python 服務生成 `{backend}/start.cjs`（若適用）
4. 在 `commands/opencode/` 生成命令檔
5. 顯示完成摘要

## 完成摘要格式

```
PM2 Init 完成
============

服務：
| Port | Name | Type |
|------|------|------|
| {port} | {name} | {type} |

指令：/pm2-all, /pm2-all-stop, /pm2-{port}, /pm2-{port}-stop, /pm2-logs, /pm2-status

終端指令：
pm2 start ecosystem.config.cjs && pm2 save  # 首次啟動
pm2 start all          # 啟動全部
pm2 stop all           # 停止全部
pm2 restart all        # 重啟全部
pm2 logs               # 檢視日誌
pm2 monit              # 監控面板
pm2 resurrect          # 還原已儲存程序

提示：首次啟動後執行 pm2 save 以啟用簡化指令。
```
