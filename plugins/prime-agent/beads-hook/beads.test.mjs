import assert from "node:assert/strict";
import test from "node:test";

import beadsExtension from "./beads.ts";

function createHarness(execImpl) {
	const handlers = new Map();
	const calls = [];
	const messages = [];
	const notifications = [];
	const pi = {
		on(event, handler) {
			handlers.set(event, handler);
		},
		async exec(command, args, options) {
			calls.push({ command, args, options });
			return execImpl();
		},
		sendMessage(message, options) {
			messages.push({ message, options });
		},
	};
	const ctx = {
		cwd: "/repo",
		signal: new AbortController().signal,
		ui: {
			notify(message, type) {
				notifications.push({ message, type });
			},
		},
	};

	beadsExtension(pi);

	return { calls, ctx, handlers, messages, notifications };
}

test("refreshes bd prime for every user prompt and records successful hooks", async () => {
	const harness = createHarness(async () => ({
		stdout: "# Beads context\nUse bd ready.",
		stderr: "",
		code: 0,
		killed: false,
	}));

	await harness.handlers.get("session_start")({}, harness.ctx);
	const result = await harness.handlers.get("before_agent_start")(
		{ systemPrompt: "base prompt" },
		harness.ctx,
	);

	assert.equal(harness.calls.length, 2);
	assert.equal(harness.calls[0].command, "bd");
	assert.deepEqual(harness.calls[0].args, ["prime"]);
	assert.equal(harness.calls[0].options.cwd, "/repo");
	assert.match(result.systemPrompt, /^base prompt/);
	assert.match(result.systemPrompt, /# Beads context\nUse bd ready\./);
	assert.deepEqual(result.message, {
		customType: "beads-context-loaded",
		content: "Beads hook 已觸發：已透過 `bd prime` 載入專案工作脈絡。",
		display: true,
	});
	assert.deepEqual(harness.messages, [
		{
			message: {
				customType: "beads-context-loaded",
				content: "Beads hook 已觸發：已透過 `bd prime` 載入專案工作脈絡。",
				display: true,
			},
			options: { triggerTurn: false },
		},
	]);

	const secondResult = await harness.handlers.get("before_agent_start")(
		{ systemPrompt: "second prompt" },
		harness.ctx,
	);
	assert.equal(harness.calls.length, 3);
	assert.equal(secondResult.message?.customType, "beads-context-loaded");
});

test("refreshes Beads context after compaction", async () => {
	let context = "first context";
	const harness = createHarness(async () => ({
		stdout: context,
		stderr: "",
		code: 0,
		killed: false,
	}));

	await harness.handlers.get("session_start")({}, harness.ctx);
	await harness.handlers.get("before_agent_start")({ systemPrompt: "base prompt" }, harness.ctx);
	context = "refreshed context";
	await harness.handlers.get("session_compact")({}, harness.ctx);
	const result = await harness.handlers.get("before_agent_start")(
		{ systemPrompt: "base prompt" },
		harness.ctx,
	);

	assert.match(result.systemPrompt, /refreshed context/);
	assert.doesNotMatch(result.systemPrompt, /first context/);
	assert.equal(harness.calls.length, 4);
	assert.equal(harness.messages.length, 2);
	assert.equal(harness.messages[1].message.customType, "beads-context-loaded");
	assert.equal(result.message?.customType, "beads-context-loaded");
});

test("does not block the agent outside a Beads workspace", async () => {
	const harness = createHarness(async () => ({
		stdout: "",
		stderr: "no beads workspace",
		code: 1,
		killed: false,
	}));

	const result = await harness.handlers.get("before_agent_start")(
		{ systemPrompt: "base prompt" },
		harness.ctx,
	);

	assert.equal(result, undefined);
	assert.deepEqual(harness.notifications, [
		{ message: "Beads 脈絡載入失敗：no beads workspace", type: "warning" },
	]);
});

test("does not block the agent when bd cannot be executed", async () => {
	const harness = createHarness(async () => {
		throw new Error("spawn bd ENOENT");
	});

	const result = await harness.handlers.get("before_agent_start")(
		{ systemPrompt: "base prompt" },
		harness.ctx,
	);

	assert.equal(result, undefined);
	assert.deepEqual(harness.notifications, [
		{ message: "Beads 脈絡載入失敗：spawn bd ENOENT", type: "warning" },
	]);
});
