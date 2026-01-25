# Proposal: refactor-profile-overlap-detection

## Summary

重新設計 Profile 系統架構，**基於重疊檢測來切換體系**，而非複製檔案。保留各體系原生格式（UDS 用 YAML，ECC 用 Markdown），透過停用/啟用重疊資源來實現切換。

## Background

### 原有提案的問題

原有的 `implement-profile-system` 和 `dynamic-profile-loading` 提案採用「複製標準檔案」的方式：

```
profiles/standards/uds/*.ai.yaml  → 複製到 .standards/
profiles/standards/ecc/*.ai.yaml  → 複製到 .standards/
```

**問題：**
1. **違反原生格式原則**：ECC 體系是 skills/commands/agents/hooks（Markdown），不是 YAML
2. **忽略功能重疊本質**：切換 Profile 的真正意義是「選擇用哪個體系的功能」，而非「複製不同的 YAML 檔案」
3. **重複造輪子**：`/upstream-sync` 和 `/upstream-compare` skills 已經能判定重疊

### 兩個體系的本質差異

| 項目 | UDS 體系 | ECC 體系 |
|------|----------|----------|
| **格式** | `.standards/*.ai.yaml` | `skills/*.md`, `commands/*.md`, `agents/*.md` |
| **核心內容** | 規範文件（commit, testing, code-review） | 原生組件（skills, commands, hooks） |
| **觸發方式** | AI 讀取 YAML 內容 | Skills 自動觸發或手動 /command |
| **範例** | `commit-message.ai.yaml` 定義類型 | `commit-standards/SKILL.md` 定義工作流 |

### 重疊分析（根據 eval-everything-claude-code 報告）

**ECC 獨有（UDS 沒有）：**
- hooks 系統（memory-persistence, strategic-compact）
- e2e-runner agent
- build-fix command
- checkpoint command
- eval-harness skill

**UDS 獨有（ECC 沒有）：**
- `.standards/*.ai.yaml` 規範檔案（繁體中文提交類型等）
- SDD/BDD/ATDD 完整整合
- Methodology System skill
- Forward Derivation skill

**功能重疊（同時存在）：**

| 功能 | UDS 對應 | ECC 對應 | 類型 |
|------|----------|----------|------|
| TDD 工作流 | `testing-guide/SKILL.md` + `test-driven-development.ai.yaml` | `tdd-workflow/SKILL.md` | skill + yaml |
| 提交訊息 | `commit-standards/SKILL.md` + `commit-message.ai.yaml` | ECC commit 設定（英文類型） | skill + yaml |
| Code Review | `code-review-assistant/SKILL.md` + `code-review.ai.yaml` | ECC code-reviewer agent | skill + yaml + agent |
| 測試規範 | `testing-guide/SKILL.md` + `testing.ai.yaml` | ECC testing patterns | skill + yaml |

### 目標

1. **保留各體系原生格式**：UDS 用 YAML，ECC 用 Markdown
2. **基於重疊檢測切換**：切換 profile 時，停用重疊資源，啟用目標體系
3. **整合 upstream-sync/compare**：利用現有工具判定重疊
4. **簡化架構**：不複製檔案，只做啟用/停用

## Motivation

### 使用者價值

- **真正的體系切換**：不只是 YAML 檔案不同，而是整個開發風格不同
- **保留自訂內容**：非重疊的 skills/commands 保持啟用
- **清晰的差異**：
  - UDS：繁體中文提交、完整 SDD/TDD/BDD 整合、詳盡規範
  - ECC：英文提交、hooks 自動化、實戰導向 TDD

### 技術價值

- **不違反原生格式**：各體系保持各自的檔案格式
- **利用現有工具**：`/upstream-sync` 和 `/upstream-compare` 已能判定重疊
- **可擴展**：未來新增體系只需定義重疊項目

## Scope

### 包含範圍

1. **重疊定義格式**
   - 定義 `profiles/overlaps.yaml` 格式
   - 記錄哪些 skills/yamls 在切換時需互斥

2. **停用機制整合**
   - 利用現有 `resource-disable` spec 的 `disabled.yaml`
   - 切換 profile 時更新 `disabled.yaml`

3. **Profile 定義簡化**
   - `profiles/*.yaml` 只定義：name, description, overlaps 引用
   - 不再需要 `includes`, `overrides`, `inherits`

4. **CLI 指令更新**
   - `ai-dev standards switch` 基於重疊定義切換
   - `ai-dev standards show` 顯示重疊項目

5. **upstream-sync/compare 增強**
   - 新增「重疊項目識別」輸出
   - 自動更新 `overlaps.yaml`

### 不包含範圍

- 複製標準檔案到 `.standards/`（不需要）
- Profile 繼承機制（不需要，改用重疊定義）
- 建立 `profiles/standards/` 目錄（不需要）

## Design Considerations

### 核心設計：重疊定義

```yaml
# profiles/overlaps.yaml
version: "1.0.0"
description: "定義各體系間的功能重疊項目"

# 重疊群組定義
groups:
  tdd-workflow:
    description: "TDD 工作流功能"
    uds:
      skills:
        - testing-guide          # skills/testing-guide/
      standards:
        - testing.ai.yaml        # .standards/testing.ai.yaml
        - test-driven-development.ai.yaml
    ecc:
      skills:
        - tdd-workflow           # skills/tdd-workflow/ (from ECC)
      commands:
        - tdd                    # commands/claude/tdd.md

  commit-message:
    description: "提交訊息規範"
    uds:
      skills:
        - commit-standards
      standards:
        - commit-message.ai.yaml
        - traditional-chinese.ai.yaml
    ecc:
      skills:
        - commit-standards       # 共用，但 profile 會調整行為
      # ECC 不需要 .standards/commit-message.ai.yaml

  code-review:
    description: "Code Review 功能"
    uds:
      skills:
        - code-review-assistant
      standards:
        - code-review.ai.yaml
        - checkin-standards.ai.yaml
    ecc:
      skills:
        - code-review-assistant  # 可共用
      agents:
        - code-reviewer          # ECC 有專門的 agent
```

### Profile 定義簡化

```yaml
# profiles/uds.yaml
name: uds
display_name: "Universal Dev Standards"
description: "完整的 UDS 標準體系，包含繁體中文提交訊息與完整 SDD/TDD/BDD 整合"

# 此 profile 啟用時，在重疊群組中選擇 uds 方案
overlap_preference: uds

# 額外停用項目（ECC 獨有功能，UDS 不使用）
disable_when_active:
  skills:
    - eval-harness
    - strategic-compact
    - continuous-learning
  commands:
    - build-fix
    - checkpoint
    - e2e
```

```yaml
# profiles/ecc.yaml
name: ecc
display_name: "Everything Claude Code"
description: "ECC 標準體系，採用 TypeScript/React 導向的實戰開發標準"

overlap_preference: ecc

# 額外停用項目（UDS 獨有功能，ECC 不使用）
disable_when_active:
  standards:
    - traditional-chinese.ai.yaml
    - acceptance-test-driven-development.ai.yaml
    - forward-derivation-standards.ai.yaml
  skills:
    - methodology-system
    - atdd-assistant
    - forward-derivation
```

```yaml
# profiles/minimal.yaml
name: minimal
display_name: "Minimal Standards"
description: "最小化標準體系，僅包含核心開發規範"

overlap_preference: minimal  # 使用最小化選項

# 停用大部分功能
disable_when_active:
  skills:
    - all-except:
        - commit-standards
        - testing-guide
  standards:
    - all-except:
        - commit-message.ai.yaml
        - testing.ai.yaml
        - checkin-standards.ai.yaml
```

### 切換邏輯

```python
def switch_profile(target_profile: str) -> dict:
    """
    切換 Profile 的核心邏輯

    1. 載入重疊定義 (overlaps.yaml)
    2. 載入目標 Profile 定義
    3. 計算需停用的項目
    4. 更新 disabled.yaml
    5. 更新 active.yaml
    """
    overlaps = load_overlaps()
    profile = load_profile(target_profile)

    to_disable = set()

    # 處理重疊群組
    for group_name, group_def in overlaps['groups'].items():
        pref = profile['overlap_preference']

        # 停用非偏好體系的項目
        for system_name, system_items in group_def.items():
            if system_name != pref:
                to_disable.update(collect_items(system_items))

    # 處理額外停用項目
    if 'disable_when_active' in profile:
        to_disable.update(collect_items(profile['disable_when_active']))

    # 更新 disabled.yaml
    update_disabled_yaml(to_disable)

    # 更新 active.yaml
    update_active_profile(target_profile)

    return {
        "success": True,
        "profile": target_profile,
        "disabled_count": len(to_disable),
        "disabled_items": list(to_disable)
    }
```

### 與現有 resource-disable spec 整合

現有的 `disabled.yaml` 格式：

```yaml
# .claude/disabled.yaml
skills:
  - skill-name-1
  - skill-name-2
commands:
  - command-name-1
agents:
  - agent-name-1
```

Profile 切換時，會**合併**現有的停用項目與 profile 定義的停用項目。

### 架構比較

| 方面 | 原設計（複製檔案） | 新設計（重疊停用） |
|------|-------------------|-------------------|
| 切換機制 | 複製 YAML 到 .standards/ | 更新 disabled.yaml |
| ECC 格式 | 強制轉成 YAML | 保留原生 Markdown |
| 重疊處理 | 用不同內容的 YAML | 停用衝突項目 |
| 自訂保護 | 需追蹤 managed_files | 自然保留（只停用重疊） |
| 複雜度 | 高（檔案複製+覆寫+來源解析） | 低（更新 disabled.yaml） |

### 與 upstream-sync/compare 整合

```yaml
# /upstream-compare 輸出新增欄位
overlap_analysis:
  detected_overlaps:
    - group: tdd-workflow
      uds_items: [testing-guide, testing.ai.yaml, test-driven-development.ai.yaml]
      ecc_items: [tdd-workflow skill, tdd command]
      recommendation: "ECC 版本更實戰導向，建議 ECC profile 使用 ECC 版本"

  new_overlaps:
    - skill: "new-skill-from-upstream"
      overlaps_with: "existing-skill"
      recommendation: "加入 overlaps.yaml"
```

## Success Criteria

### 功能驗收

- [ ] `profiles/overlaps.yaml` 定義檔案已建立且格式正確
- [ ] `profiles/uds.yaml`, `profiles/ecc.yaml`, `profiles/minimal.yaml` 使用新格式
- [ ] `ai-dev standards switch ecc` 正確更新 `disabled.yaml`
- [ ] 切換後，ECC skills/commands 保持 Markdown 格式
- [ ] 切換後，UDS `.standards/*.ai.yaml` 保持 YAML 格式
- [ ] `/upstream-compare` 輸出包含 overlap_analysis

### 差異驗證

- [ ] UDS Profile：啟用 `.standards/*.ai.yaml`，停用 ECC hooks
- [ ] ECC Profile：啟用 ECC skills/commands/hooks，停用部分 UDS yaml
- [ ] Minimal Profile：只保留核心功能

### 相容性驗證

- [ ] 現有 `disabled.yaml` 內容保留
- [ ] `resource-disable` spec 功能不受影響
- [ ] `/upstream-sync` 仍正常運作

## Risks and Mitigations

### 風險 1: 重疊判定不準確

**描述**：某些功能可能被錯誤判定為重疊。

**緩解措施**：
- `overlaps.yaml` 人工審查後再提交
- `/upstream-compare` 提供建議，人工最終確認

### 風險 2: 停用項目過多

**描述**：切換 profile 可能停用太多功能。

**緩解措施**：
- Profile 定義只包含**重疊**項目，非重疊的自然保留
- 提供 `ai-dev standards show <profile>` 預覽影響

### 風險 3: disabled.yaml 衝突

**描述**：使用者手動停用的項目與 profile 衝突。

**緩解措施**：
- 在 disabled.yaml 中區分 `manual` 和 `profile` 來源
- 切換時保留 `manual` 項目

## Alternative Approaches

### 方案 1: 保持原設計（複製檔案）

**為何不採用**：
- 違反 ECC 原生格式（Markdown）
- 複雜度高，需要維護 `profiles/standards/` 目錄
- 不符合「功能重疊」的本質

### 方案 2: 完全獨立的體系目錄

**描述**：`skills-uds/`, `skills-ecc/` 完全分開。

**為何不採用**：
- 重複維護成本高
- 非重疊功能無法共用

## Open Questions

1. **overlap_preference 支援多值？**
   - **問題**：是否需要 `overlap_preference: [uds, ecc]` 混合模式？
   - **建議**：Phase 1 只支援單一值，未來可擴展

2. **disabled.yaml 來源標記**
   - **問題**：如何區分手動停用 vs profile 停用？
   - **建議**：新增 `_source` 欄位（需更新 resource-disable spec）

3. **共用 skill 的行為調整**
   - **問題**：`commit-standards` 共用，但 UDS 要繁中、ECC 要英文？
   - **建議**：透過 `active-profile.yaml` 讓 skill 讀取當前 profile 調整行為

## Dependencies

- **前置依賴**：
  - `resource-disable` spec（disabled.yaml 機制）
  - `upstream-sync` 和 `upstream-compare` skills

- **下游影響**：
  - TUI Profile Selector 需更新
  - 相關 skills 需能讀取 active profile

## Approval

此提案取代原有的 `implement-profile-system` 和 `dynamic-profile-loading`。

核准標準：
- [ ] 重疊定義格式合理
- [ ] 保留各體系原生格式
- [ ] 切換邏輯簡潔
- [ ] 與現有工具整合順暢
