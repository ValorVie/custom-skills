# Mode: uds-check

UDS（universal-dev-standards）的 `.standards/` 與鏡像 `skills/<id>/` SHA-256 檔案級漂移檢測。

**唯一保留 Python 腳本的 mode**——檔案級比對是確定性機械勞動，腳本快且穩定。

## 觸發

```
/custom-skills-upstream-ops uds-check
/custom-skills-upstream-ops uds-check --verbose              # 列出所有漂移檔案
/custom-skills-upstream-ops uds-check --report               # 寫 YAML 報告到 upstream/reports/uds-update/
/custom-skills-upstream-ops uds-check --json                 # JSON 輸出
/custom-skills-upstream-ops uds-check --exit-nonzero-on-drift  # CI 用，有漂移 exit 1
```

## 執行

```bash
.venv/bin/python skills/custom-skills-upstream-ops/scripts/check_uds.py [options]
```

## Requirements

- Python 3.9+
- PyYAML（本專案 `.venv` 已安裝）

## 比對範圍

| 本地位置 | 上游來源 |
|---------|---------|
| `.standards/` | `~/.config/universal-dev-standards/ai/standards/` |
| `skills/<id>/`（僅同名目錄） | `~/.config/universal-dev-standards/skills/<id>/` |

## 輸出分類

對每個檔案以 SHA-256 比對，分三類：

- **modified**：雙邊都有但內容不同（最重要，代表上游已更新或本地已客製）
- **added_upstream**：上游新增、本地尚未安裝
- **only_local**：本地獨有（可能是本專案客製化，**勿直接覆寫**）

## 決策表

| 情況 | 動作 |
|------|------|
| 完全同步 | 無動作 |
| commit behind，檔案無漂移 | `ai-dev clone` 已同步過，用 `maintenance update-last-sync` 更新 `last-sync.yaml` |
| `.standards/` modified | 對每檔 `diff` 上游 vs 本地，人工決定合併；保留本地客製 |
| `skills/` drift | `ai-dev clone` 重新分發，或對個別 skill 手動 diff |
| upstream_only 有新 skill | 依需求評估是否加入本專案 |
| only_local 有檔案 | **勿覆寫**，這是本專案延伸 |

## 何時用這個 mode

- `audit` 看到 UDS 落後時，跟進跑 uds-check 取得檔案級細節
- 套用 `ai-dev clone` 後，確認是否還有殘留漂移
- 定期稽核本專案 `.standards/` 是否偏離上游太遠
