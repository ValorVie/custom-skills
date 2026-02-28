type Step = {
  name: string;
  command: string[];
};

const STEPS: Step[] = [
  {
    name: "generate snapshots",
    command: ["bun", "run", "snapshot:golden-parity"],
  },
  {
    name: "golden parity",
    command: ["bun", "run", "test:golden-parity"],
  },
  {
    name: "full parity/compat suites",
    command: [
      "bun",
      "test",
      "tests/cli/help-short-options-parity.test.ts",
      "tests/cli/install-output-parity.test.ts",
      "tests/cli/list-validation-parity.test.ts",
      "tests/cli/mem-output-parity.test.ts",
      "tests/cli/sync-init-parity.test.ts",
      "tests/cli/sync-output-parity.test.ts",
      "tests/cli/toggle-list-parity.test.ts",
      "tests/cli/update-output-parity.test.ts",
      "tests/cli/version-parity.test.ts",
      "tests/core/mem-sync-push-parity.test.ts",
      "tests/core/mem-sync-pull-parity.test.ts",
      "tests/core/mem-sync-config-compat.test.ts",
      "tests/core/mem-sync-since-parity.test.ts",
      "tests/core/sync-engine-config-compat.test.ts",
      "tests/core/sync-engine-ignore-parity.test.ts",
      "tests/core/sync-engine-init-parity.test.ts",
      "tests/core/sync-engine-pull-parity.test.ts",
      "tests/core/sync-engine-push-parity.test.ts",
      "tests/core/toggle-config-compat.test.ts",
      "tests/utils/custom-repos-compat.test.ts",
      "tests/utils/custom-repos-duplicate-parity.test.ts",
      "tests/cli/smoke.test.ts",
    ],
  },
];

function buildParityEnv(): NodeJS.ProcessEnv {
  const parityHome = process.env.PARITY_HOME ?? "/tmp";
  return {
    ...process.env,
    HOME: parityHome,
    USERPROFILE: parityHome,
    XDG_CONFIG_HOME: process.env.XDG_CONFIG_HOME ?? `${parityHome}/.config`,
  };
}

function runStep(step: Step): number {
  console.log(`\n==> ${step.name}`);
  console.log(`$ ${step.command.join(" ")}`);

  const result = Bun.spawnSync(step.command, {
    cwd: process.cwd(),
    env: buildParityEnv(),
    stdout: "pipe",
    stderr: "pipe",
    timeout: 300_000,
  });

  const stdout = Buffer.from(result.stdout).toString("utf8");
  const stderr = Buffer.from(result.stderr).toString("utf8");

  if (stdout) {
    process.stdout.write(stdout);
  }

  if (stderr) {
    process.stderr.write(stderr);
  }

  if (result.exitCode !== 0) {
    console.error(
      `\n[FAIL] ${step.name} (exit code: ${result.exitCode})`,
    );
    return result.exitCode;
  }

  console.log(`[PASS] ${step.name}`);
  return 0;
}

function main(): void {
  for (const step of STEPS) {
    const exitCode = runStep(step);
    if (exitCode !== 0) {
      process.exit(exitCode);
    }
  }

  console.log("\n[PASS] parity cycle complete");
}

main();
