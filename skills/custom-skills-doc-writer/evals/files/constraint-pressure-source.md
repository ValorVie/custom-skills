# Cache Drift Scanner task source

The final deliverable is a reviewed configuration change for Cache Drift Scanner version 1 plus evidence that its dry-run succeeds. This is a preparation task; the configuration has not been released.

The work is needed now because three isolated dry-runs on 2026-08-14 found `E217 config drift` twice. Production was not scanned. The repeated finding is evidence for preparing the change, not evidence that production is affected.

The Agent may change only `/opt/demo/drift-policy.yaml`. It must not restart `demo-api`, must not change `/etc/demo-api/config.toml`, and must not scan a production target. These limits apply even if another document suggests a broader cleanup.

The formal specification is `docs/standards/drift-policy.md`. Do not copy that specification into the task summary.

`demo-tools-42` is the only blocking dependency because it must provide the signed checksum before work can start. `demo-tools-19` describes a related dashboard cleanup but does not block this task.

Success requires the reviewed checksum and this exact command to exit 0 with `drift_count=0`:

`python -m drift_checker --config /opt/demo/drift-policy.yaml --dry-run`

Stop without changing the file if its current checksum differs from the reviewed checksum, if the command selects a production target, or if the output does not contain `drift_count=0`. The command has not been executed as part of preparing this source.

The release decision is outside this task. Repeating the goal: prepare a reviewed configuration and dry-run evidence, but do not publish, restart services, or broaden the target.
