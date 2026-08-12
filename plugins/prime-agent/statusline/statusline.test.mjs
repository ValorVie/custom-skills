import assert from "node:assert/strict";
import test from "node:test";

import {
	buildStatusSegments,
	compactNumber,
	formatCost,
	registerStatusline,
	summarizeBranch,
	truncatePlainText,
	visibleWidth,
} from "./statusline.ts";

const assistantEntry = (usage) => ({
	type: "message",
	message: { role: "assistant", usage },
});

test("summarizes active branch usage, model, and fast mode without double-counting child attribution", () => {
	const snapshot = summarizeBranch(
		[
			{ type: "model_change", modelId: "model-a" },
			assistantEntry({
				input: 1_000,
				output: 250,
				cacheRead: 500,
				cacheWrite: 25,
				cost: { total: 0.0123 },
			}),
			{ type: "child_usage_attributed", childUsage: { totalTokens: 99_999 } },
			{ type: "service_tier_change", serviceTier: "priority" },
			{ type: "model_change", modelId: "model-b" },
			assistantEntry({
				input: 200,
				output: 50,
				cacheRead: 0,
				cacheWrite: 10,
				cost: { total: 0.02 },
			}),
		],
		"fallback",
	);

	assert.deepEqual(snapshot, {
		modelId: "model-b",
		fast: true,
		usage: {
			input: 1_200,
			output: 300,
			cacheRead: 500,
			cacheWrite: 35,
			cost: 0.0323,
		},
	});
});

test("formats fields in the requested order", () => {
	const segments = buildStatusSegments({
		rlmDepth: 2,
		modelId: "model-b",
		thinkingLevel: "high",
		fast: true,
		project: "custom-skills",
		branch: "main",
		contextPercent: 49.6,
		usage: {
			input: 1_200,
			output: 300,
			cacheRead: 500,
			cacheWrite: 35,
			cost: 0.0323,
		},
		idle: false,
		pending: false,
		activeTools: ["ipython", "edit", "ipython"],
		extensionStatuses: ["\u001b[32mguard:ok\u001b[0m", " multi\nline "],
	});

	assert.deepEqual(segments, [
		"rlm:2",
		"model:model-b",
		"eff:high/fast",
		"custom-skills:main",
		"ctx:50%",
		"sess:↑1.2k/↓300/$0.03",
		"work:ipython,edit",
		"ext:guard:ok,multi line",
		"cache:R500/W35",
		"total:2.0k",
		"cost:~$0.03",
	]);
});

test("truncates plain status text by terminal width without splitting wide graphemes", () => {
	assert.equal(visibleWidth("abc中文🙂"), 9);
	assert.equal(truncatePlainText("abc中文🙂", 7), "abc中…");
	assert.equal(visibleWidth(truncatePlainText("abc中文🙂", 7)), 6);
	assert.equal(truncatePlainText("abc", 3), "abc");
	assert.equal(truncatePlainText("abc", 1), "…");
});

test("uses compact, stable fallbacks for unknown and idle state", () => {
	assert.equal(compactNumber(Number.NaN), "0");
	assert.equal(compactNumber(1_500_000), "1.5m");
	assert.equal(formatCost(0.00004), "$0.000040");

	const segments = buildStatusSegments({
		rlmDepth: -1,
		modelId: "",
		thinkingLevel: "low",
		fast: false,
		project: "repo",
		branch: null,
		contextPercent: null,
		usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, cost: 0 },
		idle: true,
		pending: true,
		activeTools: [],
		extensionStatuses: [],
	});

	assert.deepEqual(segments, [
		"rlm:0",
		"model:no-model",
		"eff:low",
		"repo",
		"ctx:?",
		"sess:↑0/↓0/$0.00",
		"idle:+queued",
		"ext:-",
		"cache:R0/W0",
		"total:0",
		"cost:~$0.00",
	]);
});

function createHarness({ footerSupported = true, readBranch = async () => "main" } = {}) {
	const handlers = new Map();
	const entries = [
		{ type: "model_change", modelId: "test-model" },
		{ type: "service_tier_change", serviceTier: "default" },
		assistantEntry({
			input: 10,
			output: 5,
			cacheRead: 3,
			cacheWrite: 2,
			cost: { total: 0.004 },
		}),
	];
	let footerFactory;
	let footerComponent;
	let widget;
	let idle = true;
	let pending = false;
	let thinkingLevel = "medium";
	let renderRequests = 0;
	let branchListener;
	let unsubscribed = false;

	const pi = {
		on(event, handler) {
			handlers.set(event, handler);
		},
		getThinkingLevel() {
			return thinkingLevel;
		},
	};
	const footerData = {
		getGitBranch: () => "main",
		getExtensionStatuses: () => new Map([["guard", "guard:ok"]]),
		onBranchChange(callback) {
			branchListener = callback;
			return () => {
				unsubscribed = true;
			};
		},
	};
	const tui = { requestRender: () => renderRequests++ };
	const theme = { fg: (_name, text) => text };
	const ctx = {
		hasUI: true,
		cwd: "/workspace/custom-skills",
		model: { id: "fallback-model" },
		getContextUsage() {
			return { tokens: 50, contextWindow: 100, percent: 50 };
		},
		isIdle() {
			return idle;
		},
		hasPendingMessages() {
			return pending;
		},
		sessionManager: {
			getBranch: () => entries,
			getCwd: () => "/workspace/custom-skills",
			getHeader: () => ({ rlmDepth: 1 }),
		},
		ui: {
			setFooter(factory) {
				footerFactory = factory;
				if (footerSupported) footerComponent = factory(tui, theme, footerData);
			},
			setWidget(key, content, options) {
				widget = { key, content, options };
			},
		},
	};
	const truncate = (text, width) => text.slice(0, width);

	registerStatusline(pi, truncate, readBranch);

	return {
		ctx,
		entries,
		footerData,
		handlers,
		theme,
		tui,
		getFooterFactory: () => footerFactory,
		getFooterComponent: () => footerComponent,
		getWidget: () => widget,
		getRenderRequests: () => renderRequests,
		getUnsubscribed: () => unsubscribed,
		setIdle: (value) => {
			idle = value;
		},
		setPending: (value) => {
			pending = value;
		},
		setThinkingLevel: (value) => {
			thinkingLevel = value;
		},
		triggerBranchChange: () => branchListener(),
	};
}

test("registers a reactive footer and tracks tools, branch, model, effort, and session changes", async () => {
	const harness = createHarness();
	await harness.handlers.get("session_start")({}, harness.ctx);
	const component = harness.getFooterComponent();

	const initial = component.render(1_000)[0];
	assert.match(initial, /^rlm:1 · model:test-model · eff:medium · custom-skills:main · ctx:50%/);
	assert.match(initial, /sess:↑10\/↓5\/\$0\.0040/);
	assert.match(initial, /idle · ext:guard:ok · cache:R3\/W2 · total:20 · cost:~\$0\.0040$/);

	harness.setIdle(false);
	await harness.handlers.get("agent_start")({}, harness.ctx);
	await harness.handlers.get("tool_execution_start")(
		{ toolCallId: "t1", toolName: "ipython" },
		harness.ctx,
	);
	assert.match(component.render(1_000)[0], /work:ipython/);

	harness.entries.push({ type: "model_change", modelId: "next-model" });
	harness.entries.push({ type: "service_tier_change", serviceTier: "priority" });
	harness.setThinkingLevel("high");
	await harness.handlers.get("model_select")({}, harness.ctx);
	await harness.handlers.get("thinking_level_select")({}, harness.ctx);
	assert.match(component.render(1_000)[0], /model:next-model · eff:high\/fast/);

	await harness.handlers.get("tool_execution_end")(
		{ toolCallId: "t1", toolName: "ipython" },
		harness.ctx,
	);
	harness.setIdle(true);
	harness.setPending(true);
	await harness.handlers.get("agent_end")({}, harness.ctx);
	assert.match(component.render(1_000)[0], /idle:\+queued/);

	const beforeBranch = harness.getRenderRequests();
	harness.triggerBranchChange();
	assert.equal(harness.getRenderRequests(), beforeBranch + 1);
	assert.ok(harness.getRenderRequests() >= 7);

	component.dispose();
	assert.equal(harness.getUnsubscribed(), true);
});

test("falls back to a visible widget when daemon mode ignores footer factories", async () => {
	let branch = "main";
	const harness = createHarness({ footerSupported: false, readBranch: async () => branch });
	await harness.handlers.get("session_start")({}, harness.ctx);
	await new Promise((resolve) => setImmediate(resolve));

	const widget = harness.getWidget();
	assert.equal(widget.key, "prime-agent-statusline");
	assert.deepEqual(widget.options, { placement: "belowEditor" });
	assert.match(widget.content[0], /^rlm:1 · model:test-model · eff:medium · custom-skills:main · ctx:50%/);
	assert.match(widget.content[0], /idle · ext:\? · cache:R3\/W2 · total:20 · cost:~\$0\.0040$/);

	harness.setIdle(false);
	await harness.handlers.get("tool_execution_start")(
		{ toolCallId: "t1", toolName: "ipython" },
		harness.ctx,
	);
	assert.match(harness.getWidget().content[0], /work:ipython/);

	branch = "feature/daemon";
	await harness.handlers.get("turn_end")({}, harness.ctx);
	await new Promise((resolve) => setImmediate(resolve));
	assert.match(harness.getWidget().content[0], /custom-skills:feature\/daemon/);
});

test("does not install a footer without an interactive UI", async () => {
	const harness = createHarness();
	harness.ctx.hasUI = false;
	await harness.handlers.get("session_start")({}, harness.ctx);
	assert.equal(harness.getFooterFactory(), undefined);
});
