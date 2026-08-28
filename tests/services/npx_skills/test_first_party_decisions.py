from script.services.npx_skills.first_party_overlay import FilePlan
from script.services.npx_skills.first_party_reconcile import (
    Decision,
    DecisionResolver,
    FileConflict,
)


def _conflict(*, binary: bool = False) -> FileConflict:
    base = b"\x00base" if binary else b"base\n"
    source = b"\x00source" if binary else b"source\n"
    local = b"\x00local" if binary else b"local\n"
    return FileConflict(
        plan=FilePlan(
            path="SKILL.md",
            classification="both-changed",
            base_hash="base-hash",
            source_hash="source-hash",
            local_hash="local-hash",
            overlay_hash=None,
            effective_hash="local-hash",
        ),
        base_content=base,
        source_content=source,
        local_content=local,
    )


def _no_base_conflict() -> FileConflict:
    return FileConflict(
        plan=FilePlan(
            path="scripts/improve_description.py",
            classification="no-base",
            base_hash=None,
            source_hash="source-hash",
            local_hash="local-hash",
            overlay_hash=None,
            effective_hash="local-hash",
        ),
        base_content=None,
        source_content=b"upstream\n",
        local_content=b"local\n",
    )


def test_noninteractive_resolver_skips_unresolved_skill():
    resolution = DecisionResolver(interactive=False).resolve((_conflict(),))

    assert resolution.decisions == {}
    assert resolution.unresolved == ("SKILL.md",)
    assert not resolution.aborted


def test_resolver_auto_accepts_clean_and_keeps_local_only():
    clean = FileConflict(
        plan=FilePlan("a.md", "clean", "b", "s", "b", None, "s"),
        base_content=b"base",
        source_content=b"source",
        local_content=b"base",
    )
    local = FileConflict(
        plan=FilePlan("b.md", "local-only", "b", "b", "l", None, "l"),
        base_content=b"base",
        source_content=b"base",
        local_content=b"local",
    )

    resolution = DecisionResolver(interactive=False).resolve((clean, local))

    assert resolution.decisions == {
        "a.md": Decision.USE_UPSTREAM,
        "b.md": Decision.KEEP_LOCAL,
    }
    assert resolution.unresolved == ()


def test_interactive_resolver_shows_requested_diff_then_keeps_local():
    answers = iter(("Ds", "K"))
    output: list[str] = []
    resolver = DecisionResolver(
        interactive=True,
        input_func=lambda _prompt: next(answers),
        output_func=output.append,
    )

    resolution = resolver.resolve((_conflict(),))

    assert resolution.decisions == {"SKILL.md": Decision.KEEP_LOCAL}
    assert any("--- base/SKILL.md" in line for line in output)
    assert any("+++ upstream/SKILL.md" in line for line in output)


def test_interactive_resolver_explains_actions_before_prompting():
    prompts: list[str] = []
    output: list[str] = []

    resolution = DecisionResolver(
        interactive=True,
        input_func=lambda prompt: prompts.append(prompt) or "K",
        output_func=output.append,
    ).resolve((_conflict(),))

    rendered = "\n".join(output)
    assert resolution.decisions == {"SKILL.md": Decision.KEEP_LOCAL}
    assert "衝突：SKILL.md" in rendered
    assert "上游與本機都已修改（both-changed）" in rendered
    assert "[Ds] 比較上游版本與上次共同基準" in rendered
    assert "[Dl] 比較本機版本與上次共同基準" in rendered
    assert "[Dc] 比較上游版本與本機版本" in rendered
    assert "[K] 保留本機內容／刪除狀態" in rendered
    assert "後續更新仍會套用" in rendered
    assert "[O] 採用上游內容／刪除狀態" in rendered
    assert "先備份目前本機內容" in rendered
    assert "[A] 中止本次第一方 skills 更新" in rendered
    assert "目前尚未寫入任何變更" in rendered
    assert prompts == ["請選擇 [Ds/Dl/Dc/K/O/A]: "]


def test_no_base_menu_marks_base_diffs_unavailable():
    answers = iter(("Ds", "Dc", "K"))
    prompts: list[str] = []
    output: list[str] = []
    resolver = DecisionResolver(
        interactive=True,
        input_func=lambda prompt: prompts.append(prompt) or next(answers),
        output_func=output.append,
    )

    resolution = resolver.resolve((_no_base_conflict(),))

    rendered = "\n".join(output)
    assert resolution.decisions == {
        "scripts/improve_description.py": Decision.KEEP_LOCAL
    }
    assert "沒有可信的共同基準（no-base）" in rendered
    assert rendered.count("無法使用：沒有可信的共同基準") >= 3
    assert "--- upstream/scripts/improve_description.py" in rendered
    assert "+++ local/scripts/improve_description.py" in rendered
    assert prompts == [
        "請選擇 [Dc/K/O/A]: ",
        "請選擇 [Dc/K/O/A]: ",
        "請選擇 [Dc/K/O/A]: ",
    ]


def test_invalid_interactive_choice_is_explained_before_reprompt():
    answers = iter(("?", "O"))
    output: list[str] = []

    resolution = DecisionResolver(
        interactive=True,
        input_func=lambda _prompt: next(answers),
        output_func=output.append,
    ).resolve((_conflict(),))

    assert resolution.decisions == {"SKILL.md": Decision.USE_UPSTREAM}
    assert "無效選項：?" in output


def test_interactive_resolver_can_use_upstream_or_abort():
    upstream = DecisionResolver(
        interactive=True,
        input_func=lambda _prompt: "O",
        output_func=lambda _line: None,
    ).resolve((_conflict(),))
    aborted = DecisionResolver(
        interactive=True,
        input_func=lambda _prompt: "A",
        output_func=lambda _line: None,
    ).resolve((_conflict(),))

    assert upstream.decisions == {"SKILL.md": Decision.USE_UPSTREAM}
    assert aborted.aborted
    assert aborted.decisions == {}


def test_binary_conflict_shows_metadata_without_content():
    answers = iter(("Dc", "K"))
    output: list[str] = []
    resolution = DecisionResolver(
        interactive=True,
        input_func=lambda _prompt: next(answers),
        output_func=output.append,
    ).resolve((_conflict(binary=True),))

    assert resolution.decisions == {"SKILL.md": Decision.KEEP_LOCAL}
    assert any("binary" in line for line in output)
    assert all("source" not in line for line in output)
