from pathlib import Path

from script.cli.command_manifest import build_command_manifest


DOC_PATH = Path("docs/ai-dev指令與資料流參考.md")


def test_reference_doc_lists_manifest_top_level_commands() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8")
    manifest = build_command_manifest()

    for spec in manifest.commands:
        if len(spec.path) == 1:
            assert f"`ai-dev {spec.path[0]}`" in doc


def test_reference_doc_mentions_default_phase_strings() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8")
    manifest = build_command_manifest()

    for spec in manifest.commands:
        if len(spec.path) == 1:
            phase_text = ",".join(spec.default_phases)
            assert phase_text in doc
