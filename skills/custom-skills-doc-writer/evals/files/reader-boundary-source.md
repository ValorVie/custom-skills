# Local checker source notes

## Reader contract

The reader is a document author who directly runs an existing CLI. The reader supplies an absolute document path, an absolute standard PDF path, and an absolute checker executable path.

The exact command is:

`<checker> check --document <absolute-document-path> --standard-pdf <absolute-pdf-path> --format json`

Report these four result states and next actions:

- `未執行機器檢查`: a PDF or checker is missing. Complete the principle-based review and state that the machine check was not run.
- `已執行且無提醒`: the command succeeds and `findings` is empty. State only that the tool returned no findings; do not claim formal compliance.
- `已執行且有提醒`: the command succeeds and `findings` is not empty. Review every finding before changing the document.
- `工具執行失敗`: the path is invalid, the exit code is nonzero, or the JSON schema is invalid. Report the reason and stop if the machine check is required acceptance.

## Maintainer implementation notes

The wrapper builds an argv array and must not use eval. It calls subprocess.run, captures stdout, keeps stderr for diagnostics, and validates the JSON schema before reading findings. These notes maintain the wrapper implementation; document authors do not implement or change the wrapper.
