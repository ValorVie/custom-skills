from script.utils import shared


def test_disable_resource_rejects_npx_managed_skill(monkeypatch):
    monkeypatch.setattr(
        "script.services.npx_skills.get_npx_managed_skill_names",
        lambda: {"managed"},
    )

    assert shared.disable_resource("claude", "skills", "managed", quiet=True) is False


def test_enable_resource_rejects_npx_managed_skill(monkeypatch):
    monkeypatch.setattr(
        "script.services.npx_skills.get_npx_managed_skill_names",
        lambda: {"managed"},
    )

    assert shared.enable_resource("claude", "skills", "managed", quiet=True) is False
