---
tags:
  - ai
  - mcp
  - postgresql
  - database
date created: 2026-03-02T15:00:00+08:00
date modified: 2026-03-02T15:00:00+08:00
description: Postgres MCP Pro 使用指南 — 在 AI 助手中直接管理、查詢與優化 PostgreSQL 資料庫
---

# Postgres MCP Pro — PostgreSQL 資料庫管理與優化

| 項目 | 內容 |
|------|------|
| **GitHub** | https://github.com/crystaldba/postgres-mcp |
| **Stars** | 2,222 |
| **語言** | Python |
| **授權** | MIT |
| **套件** | `postgres-mcp`（uvx / pip / Docker） |

---

## 解決什麼問題

AI 助手原生無法直接操作資料庫。Postgres MCP Pro 讓 AI 能直接連接 PostgreSQL，從 schema 理解、SQL 執行到效能優化一條龍完成。

| 沒有 Postgres MCP | 有 Postgres MCP |
|-------------------|-----------------|
| 手動複製 schema 給 AI 看 | AI 自動讀取 schema |
| 手動跑 EXPLAIN 再貼回來 | AI 直接跑 EXPLAIN 並分析 |
| 效能問題需 DBA 協助 | AI 自動建議最佳 index |
| 需切換到 psql / pgAdmin 操作 | 在對話中直接執行 SQL |

---

## 安裝

### 前置需求

| 需求 | 說明 |
|------|------|
| PostgreSQL 資料庫 | 需要有效的連線憑證 |
| Docker 或 Python 3.12+ | 執行 MCP Server |
| 網路連線 | 可存取目標資料庫 |

### 方式一：Docker（推薦，最穩定）

```bash
docker pull crystaldba/postgres-mcp
```

### 方式二：Python（uvx）

```bash
# 使用 uvx（推薦）
uv pip install postgres-mcp

# 或使用 pipx
pipx install postgres-mcp
```

---

## 設定

### Claude Code CLI（推薦）

```bash
# 開發環境（完整讀寫）
claude mcp add postgres --scope user \
  -e DATABASE_URI=postgresql://user:pass@localhost:5432/mydb \
  -- uvx postgres-mcp --access-mode=unrestricted

# 正式環境（唯讀）
claude mcp add postgres --scope user \
  -e DATABASE_URI=postgresql://user:pass@host:5432/proddb \
  -- uvx postgres-mcp --access-mode=restricted
```

### Claude Code 手動設定

**使用 uvx**：
```json
{
  "mcpServers": {
    "postgres": {
      "type": "stdio",
      "command": "uvx",
      "args": ["postgres-mcp", "--access-mode=unrestricted"],
      "env": {
        "DATABASE_URI": "postgresql://user:pass@localhost:5432/mydb"
      }
    }
  }
}
```

**使用 Docker**：
```json
{
  "mcpServers": {
    "postgres": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "-e", "DATABASE_URI",
        "crystaldba/postgres-mcp", "--access-mode=unrestricted"
      ],
      "env": {
        "DATABASE_URI": "postgresql://user:pass@host.docker.internal:5432/mydb"
      }
    }
  }
}
```

> Docker 內連接本機資料庫時，host 請用 `host.docker.internal` 而非 `localhost`。

### Cursor

透過 Command Palette → Cursor Settings → MCP 分頁設定，格式同 Claude Code。

### OpenCode

```json
{
  "mcp": {
    "postgres": {
      "type": "local",
      "command": ["uvx", "postgres-mcp", "--access-mode=unrestricted"],
      "environment": {
        "DATABASE_URI": "postgresql://user:pass@localhost:5432/mydb"
      }
    }
  }
}
```

---

## 存取模式

| 模式 | 參數 | 說明 | 適用環境 |
|------|------|------|----------|
| **Unrestricted** | `--access-mode=unrestricted` | 完整讀寫，可執行 DDL/DML | 開發、測試 |
| **Restricted** | `--access-mode=restricted` | 唯讀交易，有資源限制 | 正式環境 |

> **重要**：正式環境務必使用 `restricted` 模式，避免 AI 意外修改資料。

---

## MCP 工具

Postgres MCP Pro 提供 9 個工具：

### Schema 探索

| 工具 | 說明 |
|------|------|
| `list_schemas` | 列出所有 schema |
| `list_objects` | 列出表格、view、sequence、extension |
| `get_object_details` | 取得欄位、約束、index 詳細資訊 |

### SQL 執行

| 工具 | 說明 |
|------|------|
| `execute_sql` | 執行 SQL（受存取模式限制） |
| `explain_query` | 生成 EXPLAIN 計畫與成本分析 |

### 效能分析

| 工具 | 說明 |
|------|------|
| `get_top_queries` | 透過 pg_stat_statements 找出最慢的查詢 |
| `analyze_workload_indexes` | 分析整體工作負載，建議最佳 index |
| `analyze_query_indexes` | 針對特定查詢建議 index（最多 10 個） |
| `analyze_db_health` | 全面健康檢查 |

---

## 使用範例

### 資料庫健康檢查

```
檢查我的資料庫健康狀態，有沒有需要注意的問題
```

AI 會呼叫 `analyze_db_health`，回傳 index 健康度、連線使用率、buffer cache 效率、vacuum 狀態等。

### 慢查詢優化

```
找出我的資料庫中最慢的 5 個查詢，告訴我怎麼加速
```

AI 會呼叫 `get_top_queries` → `explain_query` → `analyze_query_indexes`，給出完整的優化建議。

### Schema 理解

```
幫我理解 users 表的結構，以及所有跟它關聯的表
```

### 直接執行 SQL

```
幫我查詢最近 7 天內建立的所有訂單數量，按日期分組
```

### Index 建議

```
分析我目前的工作負載，建議應該建立哪些 index
```

---

## 選用 Extension

為了完整功能，建議在資料庫中安裝以下 extension：

```sql
-- 查詢執行統計（用於找出慢查詢）
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 假設性 index 模擬（用於 index 建議）
CREATE EXTENSION IF NOT EXISTS hypopg;
```

| Extension | 功能 | 必要性 |
|-----------|------|--------|
| `pg_stat_statements` | 查詢統計分析 | 強烈推薦 |
| `hypopg` | 模擬假設性 index 效果 | 推薦 |

這兩個 extension 在主流雲端平台（AWS RDS、Azure SQL、Google Cloud SQL）都可直接啟用。

---

## SSE 傳輸模式（進階）

共用或遠端存取時，可用 SSE 模式啟動：

```bash
docker run -p 8000:8000 \
  -e DATABASE_URI=postgresql://user:pass@host:5432/mydb \
  crystaldba/postgres-mcp --access-mode=restricted --transport=sse
```

客戶端設定：
```json
{
  "mcpServers": {
    "postgres": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

---

## 安全注意事項

1. **永遠不要在正式環境用 unrestricted 模式**
2. 建議為 MCP 建立專用的資料庫使用者，限制最小權限
3. `DATABASE_URI` 包含密碼，不要提交到 git
4. Docker 模式預設不暴露端口，較為安全

---

## 故障排除

### Q: 連線失敗

**A:** 先用 psql 確認連線資訊正確：
```bash
psql "postgresql://user:pass@host:5432/mydb"
```

### Q: Docker 連不到本機資料庫

**A:** host 使用 `host.docker.internal`，不要用 `localhost`。

### Q: pg_stat_statements 相關工具失敗

**A:** 確認已安裝 extension：
```sql
SELECT * FROM pg_extension WHERE extname = 'pg_stat_statements';
```

### Q: 查詢超時

**A:** Restricted 模式有資源限制。複雜查詢可嘗試 unrestricted 模式（僅限開發環境）。
