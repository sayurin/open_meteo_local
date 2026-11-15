"""Tests for Conventional Commit validation."""

import pytest

from scripts.check_commit_messages import valid_subject


@pytest.mark.parametrize(
    ("subject", "valid"),
    [
        ("fix: handle timeout", True),
        ("chore(deps): update actions", True),
        ("feat!: remove legacy support", True),
        ("docs(readme): clarify usage", True),
        ("Fix timeout", False),
        ("fix: ", False),
        ("fix(scope: missing delimiter", False),
    ],
)
def test_subject(subject, valid):
    assert valid_subject(subject) is valid
