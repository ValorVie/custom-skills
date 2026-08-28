from script.dev_tools.generate_skills_inventory import _skill_entries


def test_inventory_reads_explicit_first_party_npx_manifest():
    skills = _skill_entries()

    assert len(skills) == 19
    assert "simplify" in skills
    assert "custom-simplify" not in skills
    assert len(skills) == len(set(skills))
