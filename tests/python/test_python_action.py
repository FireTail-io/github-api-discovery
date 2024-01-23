import os
import pytest
import responses

from main_githubaction import findings_breach_threshold, handler
from static_analysis.python.analyse_python import analyse_python
from unittest import mock


@responses.activate
def test_findings_breach_call():
    responses.add(
        responses.GET,
        "https://api.saas.eu-west-1.prod.firetail.app/organisations/org_uuid/events/external-id/some-id",
        json={},
        status=200,
    )
    try:
        findings_breach_threshold("some-id", "org_uuid", "api_token")
    except Exception:
        raise Exception("Should not raise exception")


@responses.activate
def test_findings_call_breach():
    responses.add(
        responses.GET,
        "https://api.saas.eu-west-1.prod.firetail.app/organisations/org_uuid/events/external-id/some-id",
        json={"initialFindingSeverities": {"CRITICAL": 200}},
        status=200,
    )
    with pytest.raises(Exception):
        findings_breach_threshold("some-id", "org_uuid", "api_token")


@responses.activate
def test_findings_call_non_200():
    responses.add(
        responses.GET,
        "https://api.saas.eu-west-1.prod.firetail.app/organisations/org_uuid/events/external-id/some-id",
        json={"initialFindingSeverities": {"CRITICAL": 200}},
        status=401,
    )
    try:
        findings_breach_threshold("some-id", "org_uuid", "api_token")
    except Exception:
        raise Exception("Should not raise exception")


def test_run_handler():
    with pytest.raises(Exception):
        handler()


def fake_analyser():
    return set(), {}


@mock.patch("main_githubaction.LANGUAGE_ANALYSERS", return_value={"Python": [fake_analyser]})
def test_base_env_var_set_no_context(_):
    os.environ["FIRETAIL_API_TOKEN"] = "token-token-token"
    os.environ["STATIC_ANALYSIS_ROOT_DIR"] = "src"
    handler()