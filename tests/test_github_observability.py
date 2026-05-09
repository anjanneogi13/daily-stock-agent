from src.github_observability import (
    github_artifact_bundle_name,
    github_commit_url,
    github_observability_metadata,
    github_run_url,
)


def test_github_run_url_from_actions_env():
    env = {
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REPOSITORY": "anjanneogi13/daily-stock-agent",
        "GITHUB_RUN_ID": "123456",
    }

    assert github_run_url(env) == "https://github.com/anjanneogi13/daily-stock-agent/actions/runs/123456"


def test_github_commit_url_from_actions_env():
    env = {
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REPOSITORY": "anjanneogi13/daily-stock-agent",
        "GITHUB_SHA": "abcdef123456",
    }

    assert github_commit_url(env) == "https://github.com/anjanneogi13/daily-stock-agent/commit/abcdef123456"


def test_github_artifact_bundle_name_from_run_id():
    assert github_artifact_bundle_name(env={"GITHUB_RUN_ID": "123456"}) == "official-decision-artifacts-123456"


def test_github_metadata_is_empty_for_local_context():
    metadata = github_observability_metadata(
        env={
            "GITHUB_RUN_ID": "local",
            "GITHUB_SHA": "local",
        }
    )

    assert metadata == {
        "workflow_run_url": "",
        "commit_url": "",
        "artifact_bundle_name": "",
    }
