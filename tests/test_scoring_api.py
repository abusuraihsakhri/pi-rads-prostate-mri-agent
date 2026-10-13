"""HTTP tests for scoring endpoints and validation."""
import pytest
from fastapi.testclient import TestClient
from pi_rads_prostate_mri_agent.server import create_app

client = TestClient(create_app())

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"

@pytest.mark.parametrize(
    "t2w,dwi,expected",
    [(2, 3, 2), (2, 4, 3), (2, 5, 3), (3, 4, 3), (3, 5, 4)],
)
def test_score_transition_rules(t2w, dwi, expected):
    response = client.post("/api/score", json={
        "zone": "transition", "t2w_score": t2w, "dwi_score": dwi
    })
    assert response.status_code == 200
    assert response.json()["pirads_score"] == expected

def test_assess_multiple_lesions():
    response = client.post("/api/assess", json={"lesions": [
        {"zone": "peripheral", "t2w_score": 2, "dwi_score": 3, "dce_positive": True},
        {"zone": "transition", "t2w_score": 2, "dwi_score": 4}
    ]})
    assert response.status_code == 200
    assert response.json()["max_pirads_score"] == 4

@pytest.mark.parametrize("payload", [
    {"zone": "central", "t2w_score": 3, "dwi_score": 5},
    {"zone": "transition", "t2w_score": 0, "dwi_score": 5},
    {"zone": "transition", "t2w_score": 3, "dwi_score": 5, "size_mm": -3},
    {"zone": "transition", "t2w_score": True, "dwi_score": 5},
])
def test_bad_score_payloads_rejected(payload):
    response = client.post("/api/score", json=payload)
    assert response.status_code == 422

def test_empty_assessment_rejected():
    assert client.post("/api/assess", json={"lesions": []}).status_code == 422
