# 專案摘要指引

根據單一專案的 JSON bundle 產生可讀、可回顧的專案工作摘要。

## 優先順序

1. 先看 `git_commits`
   - 這是「已完成」工作的主證據
   - 需要把多個相關 commit 合併成 2-6 個工作主題，不要逐 commit 照抄
2. 再看 `session_summaries`
   - 用來補足沒有 commit 的進行中、研究、規劃、未提交工作
   - 允許綜合多個 session 推斷主題
3. `session_hints`
   - 只作輔助，不要被 workflow / skill chatter 帶偏

## 判讀規則

- `display_name` 是標題，沒有才退回 `short_name`
- 如果有明確 commit 主題，直接寫成具體成果，不要保守寫成「研究」
- 如果沒有 commit，但 `session_summaries` 顯示明確工作方向，仍然要寫出具體主題
  - 例如：研究 AEO 策略、設計 memo 架構、評估 SEO 模型，而不是只寫「研究/探索 session」
- 如果只有零碎證據、真的看不出主題，才使用「研究/探索 session（N 分鐘）」這種保守表述
- 忽略 workflow / meta 內容：
  - skill 啟動
  - `Find Skills`
  - `AGENTS.md`
  - `Implement the following plan`
  - 其他明顯不是工作內容的對話骨架
- 每個 bullet 都要像工作日誌，而不是 commit log 或工具輸出
- 若有延續中的內容，可在最後 1 條寫成「持續整理／繼續推進／評估中」

## 輸出格式

嚴格使用：

```md
#### <display_name>
- <主題要點 1>
- <主題要點 2>
```
