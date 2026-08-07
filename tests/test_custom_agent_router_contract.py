from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "custom-agent-router" / "SKILL.md"
CODEX_PROFILE = (
    REPO_ROOT / "skills" / "custom-agent-router" / "profiles" / "codex.md"
)


def test_router_keeps_policy_and_codex_binding_separate():
    skill = SKILL.read_text(encoding="utf-8")
    profile = CODEX_PROFILE.read_text(encoding="utf-8")

    assert "profiles/codex.md" in skill
    assert "gpt-5.6-sol" not in skill
    assert "gpt-5.6-terra" not in skill
    assert "QDM" not in skill
    assert "Beads" not in skill

    assert "| `light` | `terra_worker` | `gpt-5.6-terra max` |" in profile
    assert "| `standard` | `terra_builder` | `gpt-5.6-terra max` |" in profile
    assert "| `frontier` | Sol Lead | `gpt-5.6-sol xhigh` |" in profile
    assert "| fresh review | `sol_reviewer` | `gpt-5.6-sol xhigh` |" in profile
    assert "Luna | 不可用" in profile
    assert "read-only 主 session" in profile
    assert "profile=codex binding=terra_builder" in profile


def test_router_regression_cases_remain_explicit():
    skill = SKILL.read_text(encoding="utf-8")
    expected_routes = (
        "execute / light / low / direct / lead",
        "execute / standard / material / single_worker / lead",
        "execute / light / low / bounded_parallel / lead",
        "co_discover / frontier / direct",
        "explore_then_plan / frontier / material / direct",
        "explore_then_plan / frontier / critical / approval+fresh",
    )

    for route in expected_routes:
        assert route in skill
