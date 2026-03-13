from __future__ import annotations

import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT_PATH = Path('/home/jf3096/.codex/skills/compliance-reviewer/scripts/recommendation_gate.py')
FIXTURE_DIR = Path('/home/jf3096/.codex/skills/compliance-reviewer/tests/fixtures')
ALLOWED_CHECKS = {'positive_case', 'negative_case', 'adversarial_case'}


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding='utf-8'))


def load_module():
    spec = spec_from_file_location('recommendation_gate', SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_skill_local_change_is_strongly_suggested() -> None:
    module = load_module()
    result = module.recommend_gate(load_fixture('recommend-pass-skill-local.json'))

    assert result['change_type'] == 'skill'
    assert result['impact_scope'] == 'local'
    assert result['severity'] == 'strongly_suggested'
    assert result['severity'] != 'suggest_blocking'
    assert set(result['recommended_checks']).issubset(ALLOWED_CHECKS)
    assert 'positive_case' in result['recommended_checks']
    assert 'negative_case' in result['recommended_checks']


def test_validator_global_change_escalates_to_suggest_blocking() -> None:
    module = load_module()
    result = module.recommend_gate(load_fixture('recommend-pass-validator-global.json'))

    assert result['change_type'] == 'validator_script'
    assert result['impact_scope'] == 'global-verdict-changing'
    assert result['severity'] == 'suggest_blocking'
    assert set(result['recommended_checks']) == ALLOWED_CHECKS


def test_other_local_change_stays_suggested() -> None:
    module = load_module()
    result = module.recommend_gate(load_fixture('recommend-pass-copy-local.json'))

    assert result['change_type'] == 'other'
    assert result['impact_scope'] == 'local'
    assert result['severity'] == 'suggested'
    assert set(result['recommended_checks']).issubset(ALLOWED_CHECKS)


def test_requires_user_confirmation_is_true_for_all_recommendations() -> None:
    module = load_module()

    for fixture_name in [
        'recommend-pass-skill-local.json',
        'recommend-pass-validator-global.json',
        'recommend-pass-copy-local.json',
    ]:
        result = module.recommend_gate(load_fixture(fixture_name))
        assert result['requires_user_confirmation'] is True


def test_non_string_change_objects_do_not_crash_and_normalize() -> None:
    module = load_module()
    result = module.recommend_gate(
        {
            'change_objects': ['skill', 1, None, {'type': 'template'}],
            'change_summary': '混合类型输入',
            'impact_scope': 'local',
        }
    )

    assert result['change_type'] == 'skill'
    assert result['severity'] == 'strongly_suggested'
