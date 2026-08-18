import math
import pathlib
import re
import subprocess
import sys

import pytest

PLA_DIR = pathlib.Path(__file__).resolve().parents[1] / "PLA-advanced"
sys.path.append(str(PLA_DIR))

import rest_api  # noqa: E402
from scenario_loader import load_scenario  # noqa: E402

MEDICAL = str(PLA_DIR / "scenario_context_aware_medical.json")
NESTED = str(PLA_DIR / "scenario_context_parallel.json")


@pytest.fixture()
def client():
    rest_api.scenario = None
    rest_api.app.config["TESTING"] = True
    with rest_api.app.test_client() as test_client:
        yield test_client


def api_probability(client, config_path, context_set, query):
    response = client.post(
        "/load", json={"config_path": config_path, "context_number": context_set}
    )
    assert response.status_code == 200, response.get_json()
    response = client.post("/query", json={"query": query})
    assert response.status_code == 200, response.get_json()
    return response.get_json()["probability"]


def cli_probability(config_path, context_set, query):
    result = subprocess.run(
        [sys.executable, "main.py", config_path, context_set],
        cwd=PLA_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    match = re.search(
        rf"Query: {re.escape(query)}\n-+\n\s*Probability: ([0-9.]+)", result.stdout
    )
    assert match, f"query {query} not found in CLI output:\n{result.stdout}"
    return float(match.group(1))


@pytest.mark.parametrize(
    "config_path,context_set,query",
    [
        (MEDICAL, "1", "LungCancerRisk"),
        (MEDICAL, "2", "LungCancerRisk"),
        (MEDICAL, "3", "BiopsyRequired"),
        (NESTED, "1", "LungCancerRisk"),
        (NESTED, "2", "BiopsyRequired"),
    ],
)
def test_api_matches_cli(client, config_path, context_set, query):
    api_prob = api_probability(client, config_path, context_set, query)
    cli_prob = cli_probability(config_path, context_set, query)
    # The CLI prints three decimals; compare at that resolution.
    assert math.isclose(round(api_prob, 3), cli_prob, abs_tol=5e-4)


def test_api_matches_loader_exactly(client):
    api_prob = api_probability(client, MEDICAL, "1", "LungCancerRisk")

    scenario = load_scenario(MEDICAL)
    scenario.activate("1")
    loader_prob, _ = scenario.kb.query("LungCancerRisk")

    assert math.isclose(api_prob, loader_prob, abs_tol=1e-12)
    assert math.isclose(api_prob, 0.84, abs_tol=1e-9)


def test_load_reports_active_context(client):
    response = client.post(
        "/load", json={"config_path": MEDICAL, "context_number": "2"}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["context_set"] == "2"
    assert body["active_variables"] == ["PatientAge>60", "SmokingHistory"]


def test_load_unknown_context_set_is_a_client_error(client):
    response = client.post(
        "/load", json={"config_path": MEDICAL, "context_number": "99"}
    )
    assert response.status_code == 400
    assert "available sets" in response.get_json()["error"]


def test_load_requires_config_path(client):
    response = client.post("/load", json={})
    assert response.status_code == 400


def test_query_without_loaded_scenario_is_a_client_error(client):
    response = client.post("/query", json={"query": "LungCancerRisk"})
    assert response.status_code == 400
