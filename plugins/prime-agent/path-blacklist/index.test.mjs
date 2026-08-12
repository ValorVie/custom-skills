import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const primeAgentRoot =
	process.env.PRIME_AGENT_ROOT ??
	join(execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim(), "prime-agent");
const { loadExtensions } = await import(
	pathToFileURL(join(primeAgentRoot, "dist/core/extensions/loader.js")).href
);

const temp = mkdtempSync(join(tmpdir(), "path-blacklist-extension-"));
const configPath = join(temp, "blacklist.json");
const accessLogPath = join(temp, ".prime", "access.log");
const wrapperPath = join(temp, "extension.ts");
const indexUrl = pathToFileURL(join(import.meta.dirname, "index.ts")).href;
const wallNow = Date.parse("2026-08-11T12:00:00.000Z");

writeFileSync(
	configPath,
	JSON.stringify({
		version: 2,
		softBlock: { confirmWithinSeconds: 3600, allowForSeconds: 3600 },
		pathPatterns: [
			{
				id: "private-path",
				level: "warn",
				pattern: "(?:^|/)home/tester/private(?:/|$)",
				message: "[警告] 請先閱讀 AGENTS.md 與開發文件。",
			},
		],
		fileNamePatterns: [
			{
				id: "dotenv",
				level: "block",
				pattern: "^\\.env$",
				message: "[禁止] dotenv 可能包含秘密。",
			},
		],
	}),
);
writeFileSync(
	wrapperPath,
	`import { createPathBlacklistExtension } from ${JSON.stringify(indexUrl)};
let nextId = 1;
export default createPathBlacklistExtension({
  configPath: ${JSON.stringify(configPath)},
  accessLogPath: ${JSON.stringify(accessLogPath)},
  home: "/home/tester",
  clock: { wallNow: () => ${wallNow}, monotonicNow: () => 1000 },
  randomUUID: () => \`access-\${nextId++}\`,
});
`,
);

const loaded = await loadExtensions([wrapperPath], process.cwd());
assert.deepEqual(loaded.errors, []);
assert.equal(loaded.extensions.length, 1);
const extension = loaded.extensions[0];
assert.ok(extension.tools.has("record_path_access"));
assert.ok(extension.handlers.has("tool_call"));
assert.ok(extension.handlers.has("session_compact"));

const notices = [];
const uiContext = {
	hasUI: true,
	ui: { notify: (message, level) => notices.push({ message, level }) },
};
const noUiContext = {
	hasUI: false,
	ui: { notify: () => assert.fail("無 UI 模式不應呼叫 notify") },
};
const toolCall = extension.handlers.get("tool_call")[0];
const sessionStart = extension.handlers.get("session_start")[0];
const sessionCompact = extension.handlers.get("session_compact")[0];
await sessionStart({ type: "session_start", reason: "startup" }, noUiContext);

const protectedEvent = {
	type: "tool_call",
	toolName: "ipython",
	toolCallId: "read-1",
	input: { code: 'open("/home/tester/private/.env").read()' },
};
const firstBlock = await toolCall(protectedEvent, uiContext);
assert.equal(firstBlock.block, true);
assert.match(firstBlock.reason, /PATH_ACCESS_SOFT_BLOCKED/);
assert.match(firstBlock.reason, /\[禁止\]\[dotenv\]/);
assert.match(firstBlock.reason, /\[警告\]\[private-path\]/);
assert.match(firstBlock.reason, /access ID：access-1/);
assert.match(firstBlock.reason, /record_path_access/);
assert.equal(notices[0].level, "warning");

const repeatedBlock = await toolCall(protectedEvent, noUiContext);
assert.match(repeatedBlock.reason, /access ID：access-1/);

const recordTool = extension.tools.get("record_path_access").definition;
const recordResult = await recordTool.execute(
	"record-1",
	{
		accessId: "access-1",
		accessTime: "2026-08-11T12:00:00.000Z",
		location: "/home/tester/private/.env",
		reason: "確認測試環境存取規範",
	},
	undefined,
	undefined,
	{},
);
assert.match(recordResult.content[0].text, /PATH_ACCESS_RECORDED/);
const logLines = readFileSync(accessLogPath, "utf8").trim().split("\n");
assert.equal(logLines.length, 1);
const logEntry = JSON.parse(logLines[0]);
assert.equal(logEntry.location, "/home/tester/private/.env");
assert.equal(logEntry.level, "block");
assert.deepEqual(logEntry.rule_ids, ["dotenv", "private-path"]);
assert.equal(statSync(accessLogPath).mode & 0o777, 0o600);

assert.equal(await toolCall(protectedEvent, noUiContext), undefined);

const multiTargetEvent = {
	type: "tool_call",
	toolName: "read",
	toolCallId: "multi-target",
	input: { paths: ["/tmp/.env", "/home/tester/private/report.txt"] },
};
const multiBlock = await toolCall(multiTargetEvent, noUiContext);
assert.equal(multiBlock.block, true);
assert.equal((multiBlock.reason.match(/\[禁止\]\[dotenv\]/g) ?? []).length, 1);
assert.equal((multiBlock.reason.match(/\[警告\]\[private-path\]/g) ?? []).length, 1);
assert.match(multiBlock.reason, /存取位置：\/home\/tester\/private\/report\.txt\n\/tmp\/\.env/);
await recordTool.execute(
	"record-multi",
	{
		accessId: "access-2",
		accessTime: "2026-08-11T12:00:00.000Z",
		location: "/home/tester/private/report.txt\n/tmp/.env",
		reason: "確認多目標測試規範",
	},
	undefined,
	undefined,
	{},
);
assert.equal(await toolCall(multiTargetEvent, noUiContext), undefined);

const childLoaded = await loadExtensions([wrapperPath], process.cwd());
assert.deepEqual(childLoaded.errors, []);
const childExtension = childLoaded.extensions[0];
await childExtension.handlers.get("session_start")[0](
	{ type: "session_start", reason: "startup" },
	noUiContext,
);
const childDecision = await childExtension.handlers.get("tool_call")[0](protectedEvent, noUiContext);
assert.equal(childDecision.block, true);
assert.match(childDecision.reason, /PATH_ACCESS_SOFT_BLOCKED/);

const documentationMention = await toolCall(
	{
		type: "tool_call",
		toolName: "ipython",
		toolCallId: "docs-edit",
		input: {
			code:
				'const note = "Rollback keeps ~/.prime/access.log"; tasks_path.read_text(); editTask(note.replace("- [ ]", "- [x]"));',
		},
	},
	noUiContext,
);
assert.equal(documentationMention, undefined);
const exactTextMention = await toolCall(
	{
		type: "tool_call",
		toolName: "edit",
		toolCallId: "docs-exact-text",
		input: { path: "/tmp/readme.md", old_str: accessLogPath, new_str: accessLogPath },
	},
	noUiContext,
);
assert.equal(exactTextMention, undefined);
const structuredLogAccess = await toolCall(
	{
		type: "tool_call",
		toolName: "edit",
		toolCallId: "log-edit-structured",
		input: { path: accessLogPath, old_str: "before", new_str: "after" },
	},
	noUiContext,
);
assert.match(structuredLogAccess.reason, /ACCESS_LOG_PROTECTED/);
const shellLogAccess = await toolCall(
	{
		type: "tool_call",
		toolName: "bash",
		toolCallId: "log-read-shell",
		input: { command: `cat ${accessLogPath}` },
	},
	noUiContext,
);
assert.match(shellLogAccess.reason, /ACCESS_LOG_PROTECTED/);

const dynamicLogAccess = await toolCall(
	{
		type: "tool_call",
		toolName: "ipython",
		toolCallId: "log-read-dynamic",
		input: {
			code:
				'const logPath = Path.home() / ".prime" / "access.log"; logPath.read_text();',
		},
	},
	noUiContext,
);
assert.match(dynamicLogAccess.reason, /ACCESS_LOG_PROTECTED/);

const directLogAccess = await toolCall(
	{
		type: "tool_call",
		toolName: "ipython",
		toolCallId: "log-read",
		input: { code: `open(${JSON.stringify(accessLogPath)}).read()` },
	},
	noUiContext,
);
assert.match(directLogAccess.reason, /ACCESS_LOG_PROTECTED/);

await sessionCompact(
	{ type: "session_compact", compactionEntry: {}, fromExtension: false },
	noUiContext,
);
const afterCompact = await toolCall(protectedEvent, noUiContext);
assert.match(afterCompact.reason, /access ID：access-3/);
await assert.rejects(
	() =>
		recordTool.execute(
			"record-old",
			{
				accessId: "access-1",
				accessTime: "2026-08-11T12:00:00.000Z",
				location: "/home/tester/private/.env",
				reason: "嘗試使用壓縮前舊紀錄",
			},
			undefined,
			undefined,
			{},
		),
	/ACCESS_ID_INVALID/,
);

await assert.rejects(
	() =>
		recordTool.execute(
			"record-invalid",
			{
				accessId: "access-3",
				accessTime: "2026-08-11T12:00:00.000Z",
				location: "/home/tester/private/.env",
				reason: "這是一段刻意超過三十個Unicode字元的存取理由用來驗證限制確實有效",
			},
			undefined,
			undefined,
			{},
		),
	/REASON_LENGTH/,
);
assert.match((await toolCall(protectedEvent, noUiContext)).reason, /access ID：access-3/);

await sessionStart({ type: "session_start", reason: "new", previousSessionFile: "old.jsonl" }, noUiContext);
const newSessionDecision = await toolCall(protectedEvent, noUiContext);
assert.match(newSessionDecision.reason, /access ID：access-4/);

const sessionShutdown = extension.handlers.get("session_shutdown")[0];
await sessionShutdown({ type: "session_shutdown", reason: "reload" }, noUiContext);
const afterReloadBoundary = await toolCall(protectedEvent, noUiContext);
assert.match(afterReloadBoundary.reason, /access ID：access-5/);

console.log("path-blacklist extension: integration checks passed");
