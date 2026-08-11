import { parentPort, workerData } from "node:worker_threads";

import { appendAccessLog } from "./policy.ts";

try {
	appendAccessLog(workerData.path, workerData.entry);
	parentPort.postMessage({ ok: true });
} catch (error) {
	parentPort.postMessage({ ok: false, error: error instanceof Error ? error.message : String(error) });
}
