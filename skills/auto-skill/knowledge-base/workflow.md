# 工作流程最佳實踐

此分類記錄工作流程和效率相關的經驗和最佳實踐。

---

## 🔧 mattpocock/skills 框架評估結論與三軌定位模型

**日期：** 2026-07-12
**情境：** 評估外部 AI 工作流框架能否納入本專案（superpowers、OpenSpec 之外的第三套），以及上游同步時的判斷依據
**最佳實踐：**

- 三軌定位模型：正式變更走 OpenSpec（重量軌，有規格資產累積與歸檔）；小變更走 mp-* 輕量軌（grill → to-issues → superpowers TDD → review，不開 change）；模糊大工作先走 mp-wayfinder（探索軌，proposal 之前）。superpowers 是橫切紀律層，不與流程框架同層比較。
- mattpocock/skills 的整合模式維持「改寫式」（`install_method: manual`）：上游一人維護、迭代快、有 breaking rename 前科（`to-issues`→`to-tickets`、`to-prd`→`to-spec`、`diagnose`→`diagnosing-bugs`），整包安裝會把漂移風險攤在執行期；改寫式把風險收斂在 audit 時點。
- 上游 audit 的基準點看 `upstream/mattpocock-skills/last-sync.yaml` 的 commit；比對時先查 rename 再查內容差異，否則 mapping.yaml 的 upstream_path 會誤判為刪除。
- 重疊排除原則：與 superpowers 功能等效的技能（tdd、diagnosing-bugs、code-review）不引入；與既有工具重疊者（handoff vs claude-mem）先跑 overlap 分析再決定。
- 完整評估與整合計畫見 `openspec/changes/expand-mp-lightweight-track/`（proposal、design、specs、tasks）。

<!-- 新的經驗條目會自動添加在這裡 -->
