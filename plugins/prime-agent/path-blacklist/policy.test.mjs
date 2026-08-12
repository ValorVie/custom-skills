import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Worker } from "node:worker_threads";

import {
	AccessGate,
	appendAccessLog,
	buildAccessKey,
	buildAccessLocation,
	compileBlacklist,
	findBlacklistMatches,
} from "./policy.ts";

const config = compileBlacklist({
	version: 2,
	softBlock: { confirmWithinSeconds: 3600, allowForSeconds: 3600 },
	pathPatterns: [
		{
			id: "home-sensitive",
			level: "warn",
			pattern: "(?:^|/)home/tester/private(?:/|$)",
			flags: "i",
			message: "請先確認高風險路徑規範。",
		},
		{
			id: "ssh-state",
			level: "block",
			pattern: "(?:^|/)\\.ssh(?:/|$)",
			flags: "i",
			message: "SSH 狀態受限制。",
		},
	],
	fileNamePatterns: [
		{
			id: "dotenv",
			level: "block",
			pattern: "^\\.env(?:$|\\..+)$",
			flags: "i",
			message: "dotenv 可能包含秘密。",
		},
	],
});

assert.equal(config.softBlock.confirmWithinMs, 3_600_000);
assert.equal(config.softBlock.allowForMs, 3_600_000);
assert.equal(
	compileBlacklist({
		version: 2,
		softBlock: { confirmWithinSeconds: 10, allowForSeconds: 20 },
		pathPatterns: [{ id: "legacy", pattern: "secret" }],
		fileNamePatterns: [],
	}).pathPatterns[0].level,
	"block",
);
assert.throws(
	() =>
		compileBlacklist({
			version: 2,
			softBlock: { confirmWithinSeconds: 1, allowForSeconds: 1 },
			pathPatterns: [{ id: "bad-level", level: "allow", pattern: "x" }],
			fileNamePatterns: [],
		}),
	/action.*warn.*block/,
);
assert.throws(
	() =>
		compileBlacklist({
			version: 2,
			softBlock: { confirmWithinSeconds: 0, allowForSeconds: 1 },
			pathPatterns: [],
			fileNamePatterns: [],
		}),
	/confirmWithinSeconds/,
);
assert.throws(
	() =>
		compileBlacklist({
			version: 2,
			softBlock: { confirmWithinSeconds: 1, allowForSeconds: 1 },
			pathPatterns: [{ id: "bad-regex", pattern: "[" }],
			fileNamePatterns: [],
		}),
	/bad-regex.*正規表達式無效/,
);

const deployedConfig = compileBlacklist(
	JSON.parse(readFileSync(new URL("./blacklist.json", import.meta.url), "utf8")),
);

const deployedEnvCases = [
	{ path: "/tmp/.env" },
	{ path: "/tmp/.env.local" },
	{ path: "/tmp/.env.example" },
	{ path: "/tmp/app.env" },
	{ path: "/tmp/app.env.backup" },
	{ path: "C:\\tmp\\.ENV" },
	{ options: { source: "/tmp/nested.env.production" } },
	{ uri: "file:///tmp/.env" },
	{ code: 'open("/tmp/app.env").read()' },
	{ code: 'Path.home() / ".env"' },
	{ code: '"/tmp/.e" + "nv.local"' },
	{ path: "/tmp/%2eenv.local" },
	{ code: `command = 'node -e \"fs.readFileSync(\\\"/tmp/.env.node\\\")\"'; print(command)` },
	{ code: 'open("/tmp/." "env.local")' },
	{ code: 'open("/tmp/\\x2eenv.local")' },
	{ code: 'fs.readFileSync("/tmp/\\u002eenv.node")' },
	{ command: `cat /tmp/$'\\x2eenv.ansi'` },
	{ command: 'cat "/tmp/.""env.adjacent"' },
];
for (const input of deployedEnvCases) {
	const matches = findBlacklistMatches(input, deployedConfig, "/home/tester");
	const warning = matches.find((match) => match.rule.id === "dotenv-read-warning");
	assert.equal(warning?.rule.level, "warn", JSON.stringify(input));
	assert.match(warning?.rule.message ?? "", /非必要請勿讀取/);
	assert.match(warning?.rule.message ?? "", /除非使用者核准/);
	assert.match(warning?.rule.message ?? "", /不要將內容顯示在畫面上/);
}

const multipleTargets = findBlacklistMatches(
	{ paths: ["/tmp/.env", "/tmp/app.env.backup"] },
	deployedConfig,
	"/home/tester",
);
assert.deepEqual(
	[...new Set(multipleTargets.map((match) => match.target))].sort(),
	["/tmp/.env", "/tmp/app.env.backup"],
);
assert.equal(buildAccessLocation(multipleTargets), "/tmp/.env\n/tmp/app.env.backup");
assert.doesNotThrow(() => buildAccessKey(multipleTargets));
const sameRuleTargets = findBlacklistMatches(
	{ command: 'cat "/home/tester/private/a.txt" /home/tester/private/b.txt' },
	config,
	"/home/tester",
);
assert.deepEqual(
	[...new Set(sameRuleTargets.map((match) => match.target))].sort(),
	["/home/tester/private/a.txt", "/home/tester/private/b.txt"],
);
{
	let wallNow = 1_000;
	let monotonicNow = 10;
	const appended = [];
	const multiGate = new AccessGate({
		clock: { wallNow: () => wallNow, monotonicNow: () => monotonicNow },
		randomUUID: () => "multi-target-access",
		appendRecord: (entry) => appended.push(entry),
		home: "/home/tester",
	});
	const decision = multiGate.check(multipleTargets, deployedConfig.softBlock);
	assert.equal(decision.kind, "blocked");
	assert.equal(decision.request.location, buildAccessLocation(multipleTargets));
	multiGate.record({
		accessId: decision.request.accessId,
		accessTime: new Date(wallNow).toISOString(),
		location: decision.request.location,
		reason: "multi target test",
	});
	assert.equal(appended[0].location, decision.request.location);
	assert.equal(multiGate.check(multipleTargets, deployedConfig.softBlock).kind, "allowed");
	wallNow += 1;
	monotonicNow += 1;
}

const staticPathCases = [
	{ command: 'cat "$HOME"/"private"/"report.txt"' },
	{ command: 'ROOT="$HOME" && DIR="private" && cat "$ROOT/$DIR/report.txt"' },
	{ command: 'cat "${HOME%/}/private/report.txt"' },
	{ code: 'Path.home()/"private"/"report.txt"' },
	{ code: 'Path.home().joinpath("private", "report.txt")' },
	{ code: 'open("/home/tester/" "private/report.txt")' },
	{ code: 'open("/home/tester/\\x70\\x72\\x69\\x76\\x61\\x74\\x65/report.txt")' },
	{ code: 'segment="private"; target=f"{Path.home()}/{segment}/report.txt"' },
	{ code: 'target=("/home/tester/"\n"private/report.txt")' },
	{ code: 'target=Path.home(); target/="private"; target/="report.txt"' },
	{ code: 'path.resolve(os.homedir(), "private", "report.txt")' },
	{ code: 'Path(os.environ["HOME"]) / "private" / "report.txt"' },
	{ code: 'process.env.HOME + "/private/report.txt"' },
	{ path: "/home/tester/tmp/../private/report.txt" },
	{ path: "/home/tester/./private/report.txt" },
	{ path: "/home/tester/tmp/%2e%2e/private/report.txt" },
	{ uri: "file:///home/tester/tmp/../private/report.txt" },
	{ command: `cat /home/tester/$'\\x70\\x72\\x69\\x76\\x61\\x74\\x65'/report.txt` },
	{ command: 'cat /home/tester/p\\r\\i\\v\\a\\t\\e/report.txt' },
];
for (const input of staticPathCases) {
	const matches = findBlacklistMatches(input, config, "/home/tester");
	assert.ok(matches.some((match) => match.rule.id === "home-sensitive"), JSON.stringify(input));
}
const commandSubstitution = findBlacklistMatches(
	{ command: `segment=$(printf '\\160\\162\\151\\166\\141\\164\\145'); cat "$HOME/$segment/report.txt"` },
	config,
	"/home/tester",
);
assert.ok(commandSubstitution.every((match) => match.rule.id !== "home-sensitive"));

const overlapping = findBlacklistMatches(
	{ code: 'open("/home/tester/private/.env").read()' },
	config,
	"/home/tester",
);
assert.deepEqual(
	overlapping.map((match) => [match.rule.id, match.rule.level]),
	[
		["dotenv", "block"],
		["home-sensitive", "warn"],
	],
);
assert.ok(overlapping.every((match) => match.target === "/home/tester/private/.env"));
const overlappingViaShell = findBlacklistMatches(
	{ command: "cat /home/tester/private/.env" },
	config,
	"/home/tester",
);
assert.equal(buildAccessKey(overlappingViaShell), buildAccessKey(overlapping));

const firstEnv = findBlacklistMatches({ path: "/workspace/a/.env" }, config, "/home/tester");
const secondEnv = findBlacklistMatches({ path: "/workspace/b/.env" }, config, "/home/tester");
assert.notEqual(buildAccessKey(firstEnv), buildAccessKey(secondEnv));
assert.equal(
	findBlacklistMatches({ path: "~/private/report.txt" }, config, "/home/tester")[0].target,
	"/home/tester/private/report.txt",
);
assert.equal(
	findBlacklistMatches({ path: "C:\\Users\\tester\\private\\.env" }, config, "C:/Users/tester")[0].rule.id,
	"dotenv",
);
assert.equal(
	findBlacklistMatches({ code: 'Path.home() / ".ssh" / "config"' }, config, "/home/tester")[0].rule.id,
	"ssh-state",
);
assert.equal(
	findBlacklistMatches({ command: "cat /home/tester/private/report.txt" }, config, "/home/tester")[0].rule.id,
	"home-sensitive",
);

const staticCompositionCases = [
	'Path.home() / "private" / "report.txt"',
	'os.path.join("/home/tester", "private", "report.txt")',
	'"/home/tester/" + "private/" + "report.txt"',
	'f"{Path.home()}/private/report.txt"',
	'base = Path.home(); target = base / "private" / "report.txt"; target.read_text()',
	'ROOT="$HOME"; cat "$ROOT/private/report.txt"',
	'join(homedir(), "private", "report.txt")',
	'cat "${HOME:-/tmp}/private/report.txt"',
	'cat "/home/tester/%70%72%69%76%61%74%65/report.txt"',
	'd=pri; cat "$HOME/${d}vate/report.txt"',
	`command = 'ROOT="$HOME"; cat "$ROOT/private/report.txt"'; print(command)`,
];
for (const code of staticCompositionCases) {
	const matches = findBlacklistMatches({ code }, config, "/home/tester");
	assert.equal(matches[0]?.rule.id, "home-sensitive", code);
	assert.equal(matches[0]?.target, "/home/tester/private/report.txt", code);
}

let wallNow = Date.parse("2026-08-11T12:00:00.000Z");
let monotonicNow = 10_000;
let nextId = 1;
const records = [];
const gate = new AccessGate({
	clock: {
		wallNow: () => wallNow,
		monotonicNow: () => monotonicNow,
	},
	randomUUID: () => `access-${nextId++}`,
	appendRecord: (entry) => records.push(entry),
});

const firstDecision = gate.check(overlapping, config.softBlock);
assert.equal(firstDecision.kind, "blocked");
assert.equal(firstDecision.request.accessId, "access-1");
assert.equal(gate.check(overlapping, config.softBlock).request.accessId, "access-1");

const recorded = gate.record({
	accessId: "access-1",
	accessTime: new Date(wallNow).toISOString(),
	location: "/home/tester/private/.env",
	reason: "確認測試環境設定規範",
});
assert.equal(recorded.access_id, "access-1");
assert.equal(records.length, 1);
assert.equal(gate.check(overlapping, config.softBlock).kind, "allowed");
const originalAllowedUntil = gate.snapshot().allowed[0].allowedUntilMonotonic;

wallNow += 30 * 60 * 1000;
monotonicNow += 30 * 60 * 1000;
assert.equal(gate.check(overlapping, config.softBlock).kind, "allowed");
assert.equal(gate.snapshot().allowed[0].allowedUntilMonotonic, originalAllowedUntil);

wallNow += 31 * 60 * 1000;
monotonicNow += 31 * 60 * 1000;
const expiredDecision = gate.check(overlapping, config.softBlock);
assert.equal(expiredDecision.kind, "blocked");
assert.equal(expiredDecision.request.accessId, "access-2");

const pendingGate = new AccessGate({
	clock: {
		wallNow: () => wallNow,
		monotonicNow: () => monotonicNow,
	},
	randomUUID: (() => {
		let id = 1;
		return () => `pending-${id++}`;
	})(),
	appendRecord: () => {},
});
const pendingOne = pendingGate.check(firstEnv, config.softBlock);
wallNow += 3_600_001;
monotonicNow += 3_600_001;
const pendingTwo = pendingGate.check(firstEnv, config.softBlock);
assert.notEqual(pendingOne.request.accessId, pendingTwo.request.accessId);

pendingGate.reset();
assert.deepEqual(pendingGate.snapshot(), { pending: [], allowed: [] });

const validationRecords = [];
const validationGate = new AccessGate({
	clock: {
		wallNow: () => wallNow,
		monotonicNow: () => monotonicNow,
	},
	randomUUID: () => "validation-id",
	appendRecord: (entry) => validationRecords.push(entry),
});
validationGate.check(firstEnv, config.softBlock);
const validRecord = {
	accessId: "validation-id",
	accessTime: new Date(wallNow).toISOString(),
	location: "/workspace/a/.env",
	reason: "確認規範",
};
assert.throws(() => validationGate.record({ ...validRecord, accessId: "wrong" }), /ACCESS_ID_INVALID/);
assert.throws(() => validationGate.record({ ...validRecord, location: "/workspace/b/.env" }), /LOCATION_MISMATCH/);
assert.throws(() => validationGate.record({ ...validRecord, accessTime: "not-a-time" }), /ACCESS_TIME_INVALID/);
assert.throws(
	() => validationGate.record({ ...validRecord, accessTime: new Date(wallNow - 600_000).toISOString() }),
	/ACCESS_TIME_NOT_CURRENT/,
);
assert.throws(
	() => validationGate.record({ ...validRecord, accessTime: new Date(wallNow + 600_000).toISOString() }),
	/ACCESS_TIME_NOT_CURRENT/,
);
assert.throws(() => validationGate.record({ ...validRecord, reason: "" }), /REASON_LENGTH/);
assert.throws(() => validationGate.record({ ...validRecord, reason: "字".repeat(31) }), /REASON_LENGTH/);
assert.throws(() => validationGate.record({ ...validRecord, reason: "第一行\n第二行" }), /REASON_INVALID/);
assert.throws(() => validationGate.record({ ...validRecord, reason: undefined }), /REASON_INVALID/);
assert.equal(validationGate.snapshot().pending[0].accessId, "validation-id");
assert.equal(validationRecords.length, 0);

const failingGate = new AccessGate({
	clock: {
		wallNow: () => wallNow,
		monotonicNow: () => monotonicNow,
	},
	randomUUID: () => "write-failure",
	appendRecord: () => {
		throw new Error("simulated disk full");
	},
});
failingGate.check(firstEnv, config.softBlock);
assert.throws(
	() =>
		failingGate.record({
			...validRecord,
			accessId: "write-failure",
		}),
	/simulated disk full/,
);
assert.equal(failingGate.snapshot().pending[0].accessId, "write-failure");
assert.equal(failingGate.snapshot().allowed.length, 0);

const concurrentDir = mkdtempSync(join(tmpdir(), "path-access-log-"));
const concurrentLog = join(concurrentDir, "access.log");
const workerUrl = new URL("./append-worker.mjs", import.meta.url);
const workerResults = await Promise.all(
	Array.from({ length: 8 }, (_, index) =>
		new Promise((resolve, reject) => {
			const entry = {
				access_id: `worker-${index}`,
				logged_at: "2026-08-11T12:00:00.000Z",
				access_time: "2026-08-11T12:00:00.000Z",
				location: `/tmp/target-${index}`,
				reason: "並行追加測試",
				level: "warn",
				rule_ids: ["worker-test"],
			};
			const worker = new Worker(workerUrl, {
				workerData: { path: concurrentLog, entry },
			});
			worker.once("message", resolve);
			worker.once("error", reject);
		}),
	),
);
assert.ok(workerResults.every((result) => result.ok));
const concurrentLines = readFileSync(concurrentLog, "utf8").trim().split("\n");
assert.equal(concurrentLines.length, 8);
assert.equal(new Set(concurrentLines.map((line) => JSON.parse(line).access_id)).size, 8);
assert.equal(statSync(concurrentLog).mode & 0o777, 0o600);

const directLog = join(concurrentDir, "single.log");
appendAccessLog(directLog, {
	access_id: "single",
	logged_at: "2026-08-11T12:00:00.000Z",
	access_time: "2026-08-11T12:00:00.000Z",
	location: "/tmp/single",
	reason: "單筆測試",
	level: "block",
	rule_ids: ["single"],
});
assert.equal(JSON.parse(readFileSync(directLog, "utf8")).access_id, "single");

console.log("path-blacklist policy: red/green contract checks passed");
