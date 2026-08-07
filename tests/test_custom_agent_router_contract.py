import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "custom-agent-router" / "SKILL.md"
CODEX_PROFILE = REPO_ROOT / "skills" / "custom-agent-router" / "profiles" / "codex.md"
CODEX_ONBOARDING = (
    REPO_ROOT
    / "skills"
    / "custom-agent-router"
    / "references"
    / "codex-project-onboarding.md"
)


def test_router_keeps_policy_and_codex_binding_separate():
    skill = SKILL.read_text(encoding="utf-8")
    profile = CODEX_PROFILE.read_text(encoding="utf-8")

    assert "profiles/codex.md" in skill
    assert "gpt-5.6-sol" not in skill
    assert "gpt-5.6-terra" not in skill
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


def test_router_requires_consent_before_creating_codex_project_config():
    skill = SKILL.read_text(encoding="utf-8")
    onboarding = CODEX_ONBOARDING.read_text(encoding="utf-8")

    assert "references/codex-project-onboarding.md" in skill
    assert "在 Codex runtime 套用本 Skill 時" in skill
    assert "未取得使用者選擇前，不得建立或修改設定" in skill

    for choice in ("建立建議設定", "只顯示建議", "暫不設定"):
        assert choice in onboarding

    for path in (
        ".codex/config.toml",
        ".codex/agents/terra-worker.toml",
        ".codex/agents/terra-builder.toml",
        ".codex/agents/sol-reviewer.toml",
    ):
        assert path in onboarding

    assert "不要自動建立" in onboarding
    assert "未信任的專案不會載入專案層設定" in onboarding
    assert "保留抽象 tier" in onboarding


def test_codex_onboarding_toml_examples_are_valid():
    onboarding = CODEX_ONBOARDING.read_text(encoding="utf-8")
    toml_examples = re.findall(r"```toml\n(.*?)```", onboarding, flags=re.DOTALL)

    assert len(toml_examples) == 4
    config, *roles = (tomllib.loads(example) for example in toml_examples)

    assert config == {
        "agents": {"enabled": True, "max_concurrent_threads_per_session": 15}
    }
    assert [role["name"] for role in roles] == [
        "terra_worker",
        "terra_builder",
        "sol_reviewer",
    ]
    for role in roles:
        assert role["description"]
        assert role["developer_instructions"]

    assert all("config_file" not in example for example in toml_examples)
