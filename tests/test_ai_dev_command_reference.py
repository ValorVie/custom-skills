from pathlib import Path

from script.cli.command_manifest import build_command_manifest


DOC_PATH = Path("docs/ai-dev指令與資料流參考.md")
TAXONOMY_PATH = Path("docs/ai-dev命令分類與設計壓力參考.md")
ASSESSMENT_PATH = Path("docs/report/2026-03-13-ai-dev-command-classification-assessment.md")


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


def test_taxonomy_and_assessment_docs_exist() -> None:
    assert TAXONOMY_PATH.exists()
    assert ASSESSMENT_PATH.exists()


def test_taxonomy_doc_mentions_design_pressure_groups() -> None:
    doc = TAXONOMY_PATH.read_text(encoding="utf-8")
    for phrase in ("keep", "clarify", "needs_scope_fix", "split"):
        assert phrase in doc


def test_reference_doc_mentions_top_level_semantic_sections() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8")
    for command in ("`ai-dev status`", "`ai-dev list`", "`ai-dev toggle`", "`ai-dev init-from`"):
        assert command in doc


def test_reference_doc_mentions_final_scope_contracts() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8")
    assert "不再自動同步任何 target" in doc
    assert "`--target` 必填" in doc
    assert "目前僅支援 `claude`" in doc
    assert "`ai-dev init-from update`" in doc
