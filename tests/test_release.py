"""Verify release archives against their committed tag."""

import json
import os
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "build_release.py"


@pytest.fixture
def release_repo(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()

    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    integration = tmp_path / "custom_components" / "open_meteo_local"
    integration.mkdir(parents=True)
    (integration / "__init__.py").write_text('"""Integration."""\n')
    (integration / "manifest.json").write_text(json.dumps({"version": "0.1.5"}))
    (tmp_path / "version.txt").write_text("0.1.5\n")
    (tmp_path / "hacs.json").write_text(
        json.dumps({"filename": "open_meteo_local.zip", "zip_release": True})
    )
    (tmp_path / "LICENSE.md").write_text("Test license\n")
    return tmp_path, git


def build(repo, git, tag="v0.1.5", sha=None):
    env = os.environ | {
        "RELEASE_TAG": tag,
        "RELEASE_SHA": sha or git("rev-parse", "HEAD"),
    }
    return subprocess.run(
        [os.sys.executable, str(SCRIPT)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )


def commit_and_tag(git):
    git("add", ".")
    git("commit", "-qm", "test")
    git("tag", "v0.1.5")


def test_archive_is_deterministic_and_contains_only_release_content(release_repo):
    repo, git = release_repo
    commit_and_tag(git)
    assert build(repo, git).returncode == 0
    archive_path = repo / "dist" / "open_meteo_local.zip"
    original = archive_path.read_bytes()
    with ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == {"__init__.py", "manifest.json", "LICENSE.md"}
    assert build(repo, git).returncode == 0
    assert archive_path.read_bytes() == original


def test_rejects_mismatched_tag_and_preserves_existing_archive(release_repo):
    repo, git = release_repo
    commit_and_tag(git)
    assert build(repo, git).returncode == 0
    archive_path = repo / "dist" / "open_meteo_local.zip"
    original = archive_path.read_bytes()
    git("tag", "v0.1.6")
    result = build(repo, git, tag="v0.1.6")
    assert result.returncode != 0
    assert "versions disagree" in result.stderr
    assert archive_path.read_bytes() == original


def test_rejects_symlink_in_archive(release_repo):
    repo, git = release_repo
    (repo / "custom_components" / "open_meteo_local" / "link").symlink_to(
        "../../LICENSE.md"
    )
    commit_and_tag(git)
    result = build(repo, git)
    assert result.returncode != 0
    assert "Unexpected archive member" in result.stderr
