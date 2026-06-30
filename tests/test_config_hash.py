"""Task 9 / vision item #22: config_version must be a REAL content hash.

Before this, every artifact stamped config_version="config.yaml" (a constant
string), so two picks generated from DIFFERENT config weights were
indistinguishable. A content hash makes each pick traceable to the exact
config bytes that produced it.
"""
import os
import pytest

from src.official_pick_artifact import config_hash


def test_returns_prefixed_sha256_hex(tmp_path):
    f = tmp_path / "cfg.yaml"
    f.write_text("weights:\n  a: 1\n")
    h = config_hash(path=f)
    assert h.startswith("sha256:"), h
    hexpart = h.split(":", 1)[1]
    assert len(hexpart) == 64, f"expected 64-char sha256 hex, got {len(hexpart)}"
    int(hexpart, 16)  # must be valid hex


def test_stable_for_same_content(tmp_path):
    f1 = tmp_path / "a.yaml"; f1.write_text("x: 1\n")
    f2 = tmp_path / "b.yaml"; f2.write_text("x: 1\n")
    assert config_hash(path=f1) == config_hash(path=f2), "identical content => identical hash"


def test_changes_when_content_changes(tmp_path):
    f = tmp_path / "cfg.yaml"
    f.write_text("weights:\n  a: 1\n")
    h1 = config_hash(path=f)
    f.write_text("weights:\n  a: 2\n")  # change one value
    h2 = config_hash(path=f)
    assert h1 != h2, "different content must yield a different hash"


def test_missing_file_returns_safe_sentinel(tmp_path):
    missing = tmp_path / "nope.yaml"
    h = config_hash(path=missing)
    # Must not raise, must not pretend to be a real hash.
    assert h and "sha256:" not in h, f"missing file must return a non-hash sentinel, got {h!r}"


def test_env_override_wins(tmp_path, monkeypatch):
    f = tmp_path / "cfg.yaml"; f.write_text("x: 1\n")
    monkeypatch.setenv("CONFIG_VERSION", "ci-pinned-v3")
    # When CONFIG_VERSION is set explicitly, it must take precedence over the hash.
    assert config_hash(path=f, respect_env=True) == "ci-pinned-v3"


def test_env_ignored_when_respect_env_false(tmp_path, monkeypatch):
    f = tmp_path / "cfg.yaml"; f.write_text("x: 1\n")
    monkeypatch.setenv("CONFIG_VERSION", "ci-pinned-v3")
    h = config_hash(path=f, respect_env=False)
    assert h.startswith("sha256:"), "respect_env=False must always hash, ignoring env"
