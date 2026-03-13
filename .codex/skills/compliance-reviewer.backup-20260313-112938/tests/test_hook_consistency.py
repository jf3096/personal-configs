from __future__ import annotations

import hashlib

import pytest

from conftest import compliance_receipt_block, run_hook


@pytest.mark.parametrize(
    'body',
    [
        '这里是进度更新，不是完成结论。\n',
        '这个任务已完成。\n验证：测试通过。\n',
        compliance_receipt_block() + '状态：完成（已验证：pytest -q 全部通过）\n',
        compliance_receipt_block() + '受环境限制无法联网下载依赖。\n状态：修改（未验证：网络隔离，无法拉取包）\n',
        compliance_receipt_block() + '本次改动 should work。\n状态：完成（已验证：pytest -q）\n',
    ],
)
def test_global_and_skill_hook_behavior_is_identical(body: str, global_hook_path, skill_hook_path) -> None:
    global_result = run_hook(body, global_hook_path)
    skill_result = run_hook(body, skill_hook_path)

    assert global_result.exit_code == skill_result.exit_code
    assert global_result.stdout == skill_result.stdout
    assert global_result.stderr == skill_result.stderr


def test_global_and_skill_hook_file_hash_identical(global_hook_path, skill_hook_path) -> None:
    global_hash = hashlib.sha256(global_hook_path.read_bytes()).hexdigest()
    skill_hash = hashlib.sha256(skill_hook_path.read_bytes()).hexdigest()
    assert global_hash == skill_hash


def test_hooks_are_executable(global_hook_path, skill_hook_path) -> None:
    assert global_hook_path.stat().st_mode & 0o111
    assert skill_hook_path.stat().st_mode & 0o111
