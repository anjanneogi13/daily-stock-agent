"""Non-sensitive GitHub Actions observability metadata helpers.

Reporting-only:
- no provider calls,
- no alerts,
- no trading behavior,
- no secrets.
"""

from __future__ import annotations

import os
from collections.abc import Mapping


def _env_value(env: Mapping[str, str], key: str) -> str:
    return str(env.get(key) or "").strip()


def github_run_url(env: Mapping[str, str] | None = None) -> str:
    env = env or os.environ
    repo = _env_value(env, "GITHUB_REPOSITORY")
    run_id = _env_value(env, "GITHUB_RUN_ID")
    server_url = (_env_value(env, "GITHUB_SERVER_URL") or "https://github.com").rstrip("/")

    if not repo or not run_id or run_id == "local":
        return ""

    return f"{server_url}/{repo}/actions/runs/{run_id}"


def github_commit_url(env: Mapping[str, str] | None = None) -> str:
    env = env or os.environ
    repo = _env_value(env, "GITHUB_REPOSITORY")
    sha = _env_value(env, "GITHUB_SHA")
    server_url = (_env_value(env, "GITHUB_SERVER_URL") or "https://github.com").rstrip("/")

    if not repo or not sha or sha == "local":
        return ""

    return f"{server_url}/{repo}/commit/{sha}"


def github_artifact_bundle_name(
    prefix: str = "official-decision-artifacts",
    env: Mapping[str, str] | None = None,
) -> str:
    env = env or os.environ
    run_id = _env_value(env, "GITHUB_RUN_ID")

    if not run_id or run_id == "local":
        return ""

    return f"{prefix}-{run_id}"


def github_observability_metadata(
    *,
    artifact_bundle_prefix: str = "official-decision-artifacts",
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = env or os.environ
    return {
        "workflow_run_url": github_run_url(env),
        "commit_url": github_commit_url(env),
        "artifact_bundle_name": github_artifact_bundle_name(artifact_bundle_prefix, env),
    }
