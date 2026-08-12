# Prime Agent 路徑存取軟閘門

這個 Extension 在工具執行前掃描所有字串參數。命中路徑或檔名規則時，會先取消本次工具呼叫，要求模型留下結構化存取紀錄；紀錄成功後，才在固定期限內放行相同規則與完整目標。

這是防止模型忘記規範的防誤觸層，不是 OS sandbox。動態產生的路徑、symlink 或間接 subprocess 仍可能無法辨識，真正機密仍須依靠檔案權限或隔離環境。

## 檔案

- `blacklist.json`：regex、提示強度與一小時窗口設定。
- `index.ts`：Prime Agent Extension 與 `record_path_access` 工具。
- `policy.ts`：規則編譯、路徑比對、狀態機與 access log 追加。
- `~/.prime/access.log`：成功確認後產生的 append-only JSON Lines 稽核檔。

## 執行流程

1. 模型首次命中規則，原工具不執行。
2. 模型收到 access ID、完整位置、命中規則與自訂訊息。
3. 模型呼叫 `record_path_access`，提交：
   - access ID
   - 當下 RFC 3339 時間
   - 提示中的完整位置
   - 單行、trim 後 1–30 個 Unicode 字元的理由
4. Extension 驗證成功並追加 `~/.prime/access.log` 後，才允許模型重試原存取。
5. 相同規則集合與完整目標預設放行一小時；期間的存取不延長截止時間。

Context compaction、開新 session、Extension reload、Prime Agent 重啟、session reload 與子 Agent 都從空狀態重新計算。既有 access log 只供稽核，不能恢復或繼承放行。

## 設定格式

```json
{
  "version": 2,
  "softBlock": {
    "confirmWithinSeconds": 3600,
    "allowForSeconds": 3600
  },
  "pathPatterns": [
    {
      "id": "private-reports",
      "level": "warn",
      "pattern": "(?:^|/)private/reports(?:/|$)",
      "flags": "i",
      "message": "[警告] 請先確認存取規範。"
    }
  ],
  "fileNamePatterns": []
}
```

- `pathPatterns`：比對正規化後的完整候選路徑。
- `fileNamePatterns`：比對候選路徑最後一段檔名，但放行鍵仍保留完整候選值。
- `level`：`warn` 或 `block`；兩者都先軟阻擋，差別只在提示力度。缺省值為 `block`。
- `pattern`：JavaScript `RegExp` 字串；JSON 內的反斜線要寫成 `\`。
- `flags`：JavaScript regex flags，例如 `i`。
- `message`：模型收到的自訂規範說明。

內建 `dotenv-read-warning` 會對檔名中任何 `.env` 子字串送出 warn；它不取代較嚴格的 `dotenv-secrets` block，兩者可以同時命中。

路徑比對會展開已知 HOME 寫法、統一分隔符、做一次 percent decode 與純 lexical 的 `.`／`..` 收斂，也會解析常見的靜態 shell、Python 與 Node 組合。它不執行任意程式、command substitution、未知環境變數或 symlink resolution。單一工具呼叫若含多個受管制目標，會把所有目標與規則一起綁進 access key；location 以換行分隔。修改後執行 `/reload`。

## Access log

每筆有效紀錄以單行 JSON 追加，至少包含：

```json
{
  "access_id": "uuid",
  "logged_at": "主機 UTC 時間",
  "access_time": "模型填寫的 RFC 3339 時間",
  "location": "/normalized/target",
  "reason": "1–30 字理由",
  "level": "warn",
  "rule_ids": ["rule-id"]
}
```

首次建立的 `~/.prime/access.log` 使用 owner-only mode。一般模型工具不得直接讀取、覆寫、截斷或刪除它；只有 `record_path_access` 能追加通過驗證的紀錄。設定錯誤、無效紀錄或 log 寫入失敗都會 fail-closed。

無 UI、背景或子 Agent 模式仍會把軟阻擋提示作為錯誤工具結果送回模型，不會因無法顯示通知而放行。

## 驗證

```bash
cd ~/.prime/agent/extensions/path-blacklist
node --no-warnings policy.test.mjs
node --no-warnings index.test.mjs
```

Prime Agent loader 驗證需確認 `path-blacklist/index.ts` 自動發現、沒有 diagnostics，且註冊 `record_path_access`。

## Rollback

目前基線備份：

```text
~/.prime/agent/backups/path-blacklist.bak-20260811-202143/
```

Rollback 時先把現行目錄另存，再由備份還原 `~/.prime/agent/extensions/path-blacklist/`，核對備份內 `SHA256SUMS`，最後執行 `/reload`。不要刪除或覆寫 `~/.prime/access.log`；它是獨立稽核紀錄。
