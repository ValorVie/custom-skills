# Prime Agent statusline 可顯示資料指南

> 核對版本：Prime Agent 0.7.2，2026-08-12。
>
> 這份文件整理目前公開 Extension API 能安全取得的資料。本目錄同時包含可直接載入的試用版 Extension。

## 結論

Prime Agent 沒有 Claude Code `statusLine.command` 這類宣告式設定。statusline 要用 TypeScript Extension 實作。

目前版本還有一個容易誤判的地方：

- Prime Agent 的 `README.md` 明確說明內建 footer 預設為空。
- `FooterComponent.render()` 實際固定回傳 `[]`。
- `ctx.ui.setStatus()` 仍會把文字存入 `footerData`，但內建空 footer 不會把它畫出來。
- 要看見 statusline，應使用 `ctx.ui.setFooter()`；若要整合其他 Extension 的 `setStatus()`，再由 custom footer 呼叫 `footerData.getExtensionStatuses()`。

因此，單獨複製官方 `examples/extensions/status-line.ts` 在 Prime Agent 0.7.2 上可能沒有可見輸出。完整 custom footer 才是可靠做法。

## 可用的 UI 入口

| API | 顯示位置 | 目前行為 | 適用情境 |
|---|---|---|---|
| `ctx.ui.setFooter()` | 輸入框下方 | 完整取代內建 footer | 建立真正的 statusline，建議使用 |
| `ctx.ui.setStatus(key, text)` | 交由 footer 決定 | 只保存狀態；預設空 footer 不顯示 | 讓多個 Extension 提供狀態，再由 custom footer 彙整 |
| `ctx.ui.setWidget(..., { placement: "belowEditor" })` | 輸入框下方、footer 上方 | 可見，可多行 | 狀態內容太長、不適合塞成一行時 |
| `ctx.ui.setWorkingMessage()` | 回應生成中的 loader | 只在串流期間出現 | 顯示目前工作階段，不是常駐 statusline |
| `ctx.ui.setWorkingIndicator()` | 回應生成中的 loader | 可換圖示、動畫或隱藏 | 調整工作中提示，不承載 session 統計 |
| `ctx.ui.setTitle()` | Terminal 視窗或分頁標題 | 改 Terminal title | 顯示專案或 session 名稱的輔助位置 |

`setFooter()` 一次只能有一個生效。若多個 Extension 都呼叫它，最後設定者會取代前一個 footer。較好的組合方式是由其他 Extension 使用 `setStatus()`，再由單一 footer 統一渲染。

## 直接可取得的資料

### Extension context

每個事件 handler 都會收到 `ctx: ExtensionContext`。下列資料不需執行外部命令。

| 可顯示資訊 | API 或欄位 | 值與限制 |
|---|---|---|
| 工作目錄 | `ctx.cwd` 或 `ctx.sessionManager.getCwd()` | 可顯示完整路徑或只顯示最後一段；通常只顯示專案名稱較安全 |
| 是否有互動 UI | `ctx.hasUI` | print／部分 RPC 模式可能為 `false`；這些模式沒有可見 footer |
| 目前模型 | `ctx.model` | 沒有已選模型時為 `undefined` |
| Context 使用量 | `ctx.getContextUsage()` | 回傳 `tokens`、`contextWindow`、`percent` |
| Agent 是否閒置 | `ctx.isIdle()` | `false` 代表正在處理，但不等於能取得精確工作名稱 |
| 是否有待處理訊息 | `ctx.hasPendingMessages()` | 只有布林值，沒有公開的 queue 長度 |
| Session 名稱 | `ctx.sessionManager.getSessionName()` 或 `pi.getSessionName()` | 使用者尚未命名時為 `undefined` |
| Session ID | `ctx.sessionManager.getSessionId()` | 技術上可顯示；通常不值得占用狀態列空間 |
| Session 檔案 | `ctx.sessionManager.getSessionFile()` | in-memory session 可能為 `undefined`；不建議預設顯示完整私人路徑 |
| Session 目錄 | `ctx.sessionManager.getSessionDir()` | 可用，但同樣不建議顯示完整路徑 |
| 目前 branch leaf | `getLeafId()`、`getLeafEntry()` | 適合除錯 session tree，不適合一般狀態列 |
| Session header | `ctx.sessionManager.getHeader()` | 可取得原始 `cwd`、parent session、`rlmDepth` 與建立時 Git 快照 |
| Session branch／entries | `getBranch()`、`getEntries()` | 可衍生訊息、token、費用、工具與 compaction 統計 |
| Abort 狀態 | `ctx.signal?.aborted` | 只有 Agent 執行期間通常才有 signal；適合除錯，不等於一般 working 狀態 |
| Effective system prompt | `ctx.getSystemPrompt()` | 技術上可讀，但可能含規則、路徑與私人脈絡，禁止放進 statusline |

### Extension API 與 model registry

除了事件 context，Extension factory 的 `pi` 與 `ctx.modelRegistry` 也能提供摘要資料。

| 可顯示資訊 | API | 限制 |
|---|---|---|
| 目前 thinking level | `pi.getThinkingLevel()` | 最直接且會反映目前值 |
| Session 名稱 | `pi.getSessionName()` | 未命名時為 `undefined` |
| 已啟用工具名稱／數量 | `pi.getActiveTools()` | 是允許模型使用的工具清單，不是此刻正在執行的工具 |
| 所有已設定工具 | `pi.getAllTools()` | 含參數 schema 與來源 metadata，狀態列通常只需要數量 |
| Slash command 清單／數量 | `pi.getCommands()` | 適合除錯 Extension 載入，不建議常駐列出名稱 |
| 自訂 CLI flag | `pi.getFlag(name)` | 只能讀取已由 Extension 註冊的 flag |
| 所有模型／模型數 | `ctx.modelRegistry.getAll()` | 可能很多，只顯示數量或經篩選結果 |
| 有 auth 設定的模型 | `ctx.modelRegistry.getAvailable()` | 是快速本機檢查，不代表 provider 當下健康 |
| Provider 顯示名稱 | `ctx.modelRegistry.getProviderDisplayName()` | 可把內部 provider ID 轉成顯示名稱 |

不要為了 statusline 呼叫 `getApiKeyAndHeaders()`、`getApiKeyForProvider()` 或其他 credential 解析 API。這些方法不是顯示用途，也可能取得敏感值或觸發額外工作。

### 模型資料

`ctx.model` 的公開欄位如下。

| 欄位 | 可顯示內容 | 備註 |
|---|---|---|
| `id` | 模型 ID | statusline 最常用，通常比 `name` 短 |
| `name` | 顯示名稱 | 終端寬度足夠時使用 |
| `provider` | Provider 名稱 | 可與模型 ID 組成 `provider/model` |
| `api` | API 類型 | 例如 Anthropic Messages 或 OpenAI Responses 的內部識別值 |
| `reasoning` | 是否支援 reasoning | 只是能力，不代表目前 thinking level |
| `thinkingLevelMap` | 模型支援的 thinking level 映射 | 適合除錯，不建議整段顯示 |
| `input` | 支援 `text`／`image` | 可顯示是否支援圖片 |
| `contextWindow` | 模型 context window 上限 | 是模型容量，不是目前用量 |
| `maxTokens` | 單次最大輸出 token | 不是剩餘 context |
| `cost` | input／output／cache 費率 | 單位為每百萬 token；不是本 session 已花費金額 |
| `baseUrl` | Provider endpoint | 技術上可讀，但可能暴露內部服務位置，不建議顯示 |
| `headers` | 自訂 HTTP headers | 可能含 credential，禁止顯示或寫入 log |

目前 thinking level 應使用 `pi.getThinkingLevel()`，可能值為：

```text
minimal · low · medium · high · xhigh · max
```

模型不一定支援全部等級。Prime Agent 會依模型能力限制實際值。

### Context 使用量

`ctx.getContextUsage()` 回傳：

```typescript
interface ContextUsage {
  tokens: number | null;
  contextWindow: number;
  percent: number | null;
}
```

建議顯示 `percent`，例如 `ctx:37%`。需要注意：

- 沒有模型或 context window 無效時，整個結果可能是 `undefined`。
- compaction 完成後、下一個有效模型回應前，`tokens` 與 `percent` 會是 `null`。
- 這是目前送入模型的 context 估算，不是 session 累積 token。
- 互動模式會嘗試把正在串流的輸出加入估算，但仍應視為即時估計值。

### Footer 專用資料

`ctx.ui.setFooter()` 的第三個參數是 `ReadonlyFooterDataProvider`。

| API | 內容 | 反應方式 |
|---|---|---|
| `getGitBranch()` | Git branch；非 repo 為 `null`，detached HEAD 為 `"detached"` | 內建 cache |
| `onBranchChange(callback)` | branch 或工作目錄變化通知 | 回傳 unsubscribe，應在 `dispose()` 呼叫 |
| `getExtensionStatuses()` | 所有 `ctx.ui.setStatus(key, text)` 狀態 | `ReadonlyMap<string, string>` |
| `getAvailableProviderCount()` | 目前有可用模型的唯一 provider 數量 | 是 provider 數，不是模型數 |

`footerData` 只直接提供 Git branch，不提供 dirty、ahead、behind、stash 數或目前 commit。這些資訊需要另行執行 Git 命令。

## 可從 session 衍生的資料

`ctx.sessionManager.getBranch()` 回傳目前 branch 從 root 到 leaf 的 entries。statusline 可在 `render()` 時做輕量統計。

| 可衍生資訊 | 來源 | 計算注意事項 |
|---|---|---|
| User／assistant 訊息數 | `message` entries 的 `message.role` | Tool result 也是獨立 message role |
| Tool call 數 | assistant message 的 `content[type="toolCall"]` | 不要只算 tool result，失敗或中斷時可能不對稱 |
| Tool result 與錯誤數 | `toolResult` message 的 `isError` | 可顯示最近錯誤或總錯誤數 |
| 累積 input token | `assistantMessage.usage.input` | 對所有 assistant message 加總 |
| 累積 output token | `assistantMessage.usage.output` | 對所有 assistant message 加總 |
| Cache read／write token | `usage.cacheRead`、`usage.cacheWrite` | 可評估 prompt cache 使用情況 |
| Session 累積 token | input + output + cacheRead + cacheWrite | 這是 Prime Agent `SessionStats` 採用的算法；不要和 context 使用量混用 |
| Session 估算費用 | `assistantMessage.usage.cost.total` 加總 | 是 client 依模型費率計算的估值，不是帳單真相來源 |
| 目前模型紀錄 | 最後一個 `model_change` entry | 可避免 footer 捕捉舊 event context 後顯示舊模型 |
| Fast mode | 最後一個 `service_tier_change` entry | `serviceTier === "priority"` 代表目前 `/fast` 為開啟狀態 |
| Thinking level 歷史 | `thinking_level_change` entries | 目前值直接用 `pi.getThinkingLevel()` 較簡單 |
| Compaction 次數 | `compaction` entries | 可另顯示最後一次的 `tokensBefore` |
| Session tree 深度／分支 | `getTree()`、entry parent 關係 | 計算較重，通常不適合每次 render |
| Session label | `getLabel(entryId)` 或 tree node label | 適合顯示目前 bookmark |
| Agent 最近摘要 | 最後一個 `agent_status` entry | 有 `summary` 與 `taskState`，但不保證每個互動 session 都會產生 |
| RLM 深度 | `getHeader()?.rlmDepth` | 代表 spawn depth，不是目前活躍子 Agent 數量 |
| Parent session | `getHeader()?.parentSession` | 適合除錯；可能包含私人檔案路徑 |
| 最後停止原因 | 最後一個 assistant message 的 `stopReason` | `stop`、`length`、`toolUse`、`error`、`aborted` |

RLM child usage 已折入 parent assistant message 的 aggregate usage。若同時再把 `child_usage_attributed` entry 加到總數，會重複計算。

## 可透過事件自行追蹤的資料

以下資料不是單一 getter，但可以在 Extension 內維護少量 state，再要求 TUI 重新渲染。

| 可追蹤資訊 | 建議事件 |
|---|---|
| Agent working／idle | `agent_start`、`agent_end` |
| Turn 編號與耗時 | `turn_start`、`turn_end` |
| 目前執行中的工具名稱與數量 | `tool_execution_start`、`tool_execution_end`，用 `toolCallId` 維護 `Map` |
| Tool 是否失敗 | `tool_execution_end.isError` |
| 串流中的 partial usage | `message_update` 的 assistant message |
| 最後回應時間與 stop reason | `message_end` 或 `turn_end` |
| 模型切換 | `model_select` |
| Thinking level 切換 | `thinking_level_select` |
| Compaction 完成 | `session_compact` |
| Session reload／new／resume／fork | `session_start.reason` |

不要在 `render(width)` 裡執行 shell、網路請求或大量 tree traversal。`render()` 可能頻繁執行，應只讀取已快取資料並完成字串格式化。

## 可經外部命令補充的資料

這些資料可以顯示，但不是 Prime Agent statusline API 直接提供的。

| 資訊 | 取得方式 | 建議 |
|---|---|---|
| Git dirty／ahead／behind／commit | `git status --porcelain=v2 --branch` 等 | 在事件或低頻 timer 非同步更新；不要每次 render 執行 Git |
| Beads issue／工作狀態 | `bd show`、`bd ready` 等 | 只保存簡短摘要，不要把完整 issue 描述塞入 footer |
| 時鐘 | `Date` | 每秒更新會持續重繪；通常每 30–60 秒已足夠 |
| 主機名、CPU、load、memory | Node `os` 標準函式庫 | 先確認真的有操作需求，避免把 statusline 變成監控面板 |
| Prime Agent 版本 | package metadata 或 `prime-agent --version` | 啟動時查一次並快取 |
| 自訂工作模式 | Extension 自己的 state | 用 `setStatus()` 發布給共用 footer 最合適 |
| Provider quota／rate limit | Provider response headers 或額外 API | 沒有統一公開格式；不要假設所有 provider 都能取得 |

若使用 `pi.exec()` 查外部資料，應在事件 handler 或受控 timer 執行，設定 timeout，失敗時保留舊值或顯示未知。不要在狀態列暴露命令輸出原文。

## 目前沒有穩定公開 API 的資訊

Prime Agent 互動 UI 內部雖然持有更多狀態，但 Extension API 0.7.2 沒有正式暴露下列資料：

- 精確的 pending message queue 長度；公開 API 只有 `hasPendingMessages()`。
- 目前活躍子 Agent 數量、名稱與個別 context。
- Goal 的完整狀態與使用量。
- Heartbeat 清單與下一次執行時間。
- 自動 retry 次數與倒數。
- 內建 activity tracker 的精確分類與 in-flight token counter。
- Provider 帳戶剩餘 quota、信用額度或真實帳單。
- Git dirty、ahead／behind、stash 與 commit；`footerData` 只有 branch。

不建議直接 import `prime-agent/dist/...` 私有模組取得這些欄位。內部路徑與物件不是 Extension 相容性契約，升級後容易失效。若某項狀態很重要，優先使用公開事件自行追蹤，或等待 Prime Agent 提供正式 API。

## 不應顯示的內容

即使技術上可以讀取，也不應放進 statusline：

- API key、OAuth token、cookie、credential 或 `model.headers`。
- 完整 system prompt、使用者 prompt、工具參數或工具結果。
- 可能含帳號、店家、專案機密的完整絕對路徑。
- Provider response headers 原文。
- Session JSONL 內容、原始錯誤 payload 或環境變數全集。

狀態列會長時間留在畫面，也可能被 terminal scrollback、截圖或錄影保存。只顯示短、低敏感度、對當下操作有用的摘要。

## 目前試用版

本目錄的主要檔案：

| 檔案 | 用途 |
|---|---|
| `index.ts` | Prime Agent Extension 入口，只接上 renderer |
| `statusline.ts` | 狀態彙整、格式化、事件追蹤與寬度安全截斷 |
| `statusline.test.mjs` | 純 Node 測試，不需啟動 Prime Agent |
| `package.json` | ESM 與測試命令 |
| `README.md` | API 能力、限制與操作說明 |

### 顯示順序

試用版依指定順序輸出下列欄位：

| 順序 | 格式 | 資料來源 |
|---|---|---|
| 1 | `rlm:0` | `sessionManager.getHeader()?.rlmDepth` |
| 2 | `model:gpt-5.4` | active branch 最後一個 `model_change`，否則使用 `ctx.model.id` |
| 3 | `eff:high/fast` | `pi.getThinkingLevel()` 與最後一個 `service_tier_change` |
| 4 | `custom-skills:main` | 工作目錄 basename 與 `footerData.getGitBranch()` |
| 5 | `ctx:37%` | `ctx.getContextUsage()?.percent` |
| 6 | `sess:↑12k/↓3k/$0.12` | Session input token、output token與估算費用 |
| 7 | `work:ipython`／`work:-`／`idle` | Agent 狀態與 active tool event |
| 8 | `ext:guard:ok` | 所有 `ctx.ui.setStatus()` 值；沒有時為 `ext:-` |
| 9 | `cache:R4k/W1k` | Session cache read／write token |
| 10 | `total:20k` | input + output + cache read + cache write |
| 11 | `cost:~$0.12` | Session 累積估算費用 |

例如：

```text
rlm:0 · model:gpt-5.4 · eff:high/fast · custom-skills:main · ctx:37% · sess:↑12k/↓3k/$0.12 · idle · ext:- · cache:R4k/W1k · total:20k · cost:~$0.12
```

第 6 與第 11 欄都出現費用是刻意保留的。前者和 input／output token 放在一起，方便快速看 session；後者則保留指定的獨立估算費用欄位。`total` 也刻意和 input／output 分開，且包含 cache token。

### 更新時機

Extension 會在下列事件要求 TUI 重繪：

- `session_start`
- `agent_start`、`agent_end`
- `turn_end`
- `session_compact`
- `model_select`
- `thinking_level_select`
- `tool_execution_start`、`tool_execution_end`
- Git branch 變化

`setStatus()` 本身也會要求 Prime Agent 重繪，因此其他 Extension 的狀態會跟著更新。`/fast` 目前沒有公開的 Extension 專用事件，但 Prime Agent 會在切換後重繪 UI；renderer 每次都從 active branch 讀取最後的 service tier，因此仍會反映新狀態。

### 顯示與效能邊界

- 狀態列固定為一行，超過終端寬度時從右側截斷並加上 `…`。
- 截斷發生在加上 ANSI 顏色前，並以 grapheme 與常見 CJK／emoji 寬度計算，不會從 UTF-16 code unit 中間切斷文字。
- 因為欄位順序固定，窄終端可能看不到右側的 cache、total 與 cost。這是試用版刻意保留的效果，後續可依實際使用感受改成二行或 responsive priority。
- renderer 不執行 shell、網路或檔案掃描。
- usage 只累加 active branch 的 assistant message，不另外累加 `child_usage_attributed`，避免 RLM child usage 重複計算。
- 每次 render 會掃描 active branch。一般 session 成本很低；若超長 session 出現 UI 延遲，再改成事件增量快取。
- 費用來自 assistant message 的 `usage.cost.total`，是 client 估算，不是 provider 帳單。

## 安裝與驗證

在此目錄先執行單元測試：

```bash
node --no-warnings statusline.test.mjs
```

使用者層安裝位置：

```text
~/.prime/agent/extensions/statusline/
```

從 repo 根目錄同步試用版：

```bash
source_dir="plugins/prime-agent/statusline"
target_dir="$HOME/.prime/agent/extensions/statusline"
mkdir -p "$target_dir"
install -m 0644 "$source_dir/index.ts" "$target_dir/index.ts"
install -m 0644 "$source_dir/statusline.ts" "$target_dir/statusline.ts"
install -m 0644 "$source_dir/package.json" "$target_dir/package.json"
```

主要來源是 repo 內的 `index.ts`、`statusline.ts` 與 `package.json`。測試與 README 不必複製到 runtime 目錄。Prime Agent 透過 jiti 載入 TypeScript，不需事先編譯。

已開啟的互動 session 安裝後執行：

```text
/reload
```

手動驗證至少涵蓋：

1. 一般 session 能看見一行 footer，窄終端不破版。
2. 切換模型後 model ID 更新。
3. 執行 `/effort` 與 `/fast` 後狀態更新。
4. 完成一輪對話後 input、output、cache、total、費用與 context 更新。
5. 工具執行期間顯示 `work:<tool>`，完成後回到 `idle`。
6. `/compact` 後允許暫時顯示 `ctx:?`，下一次模型回應後恢復數值。
7. Git branch 切換後 footer 更新；非 Git 目錄不顯示 branch。
8. 其他 Extension 呼叫 `setStatus()` 後，文字出現在 `ext:` 欄位。
9. `/reload`、`/new`、resume 與 fork 後不殘留前一個 session 的 active tool state。
10. 離開 session 或 reload 時，branch watcher 已在 `dispose()` 清理。

需要核對 token、費用與 context 時，以 `/usage` 的輸出作為同一客戶端內的對照。真實費用仍以 provider 帳單為準。

### 移除

刪除或移走使用者層的 `statusline` Extension 目錄後執行 `/reload`，Prime Agent 就會恢復內建空 footer。移除前可先把目錄改名保存，方便復原。

## 來源

本文件以 Prime Agent 0.7.2 安裝包內的下列第一方檔案核對：

- `README.md`：內建 footer 預設為空，`/usage` 顯示 token、費用與 context。
- `docs/extensions.md`：Extension UI、事件、`setStatus()` 與 `setFooter()`。
- `docs/tui.md`：persistent status、custom footer 與 component pattern。
- `examples/extensions/status-line.ts`：官方 `setStatus()` 範例。
- `examples/extensions/custom-footer.ts`：官方 custom footer、usage 與 Git branch 範例。
- `dist/modes/interactive/components/footer.js`：Prime 品牌 footer 的 `render()` 固定回傳空陣列。
- `dist/core/extensions/types.d.ts`：`ExtensionAPI`、`ExtensionContext`、`ContextUsage` 與所有公開事件型別。
- `dist/core/footer-data-provider.d.ts`：custom footer 可讀取的 Git branch、Extension statuses 與 provider count。
- `dist/core/session-manager.d.ts`：read-only session manager、session entries 與 header 型別。
- `dist/core/agent-session.js`：`/session` token／費用加總及 context usage 算法。
- `@earendil-works/pi-ai/dist/types.d.ts`：`Model`、`Usage` 與 `AssistantMessage` 欄位。

Prime Agent 後續版本若恢復非空內建 footer，`setStatus()` 可能重新直接可見。升級後應先重查 `FooterComponent.render()` 與型別檔，再決定是否仍需要完整 custom footer。
