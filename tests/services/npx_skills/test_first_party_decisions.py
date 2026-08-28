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
