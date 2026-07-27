import json
from pathlib import Path

import pytest

SPEC = Path(__file__).parent / "data" / "openapi.json"


@pytest.mark.drift
def test_render_paths_present_in_vendored_spec():
    if not SPEC.exists():
        pytest.skip("vendored openapi.json snapshot missing; run `make fetch-spec`")
    spec = json.loads(SPEC.read_text())
    paths = spec.get("paths", {})
    for path in (
        "/api/v1/passes",
        "/api/v1/passes/{pass_id}",
        "/api/v1/passes/{pass_id}/save-link",
        "/api/v1/passes/preview",
    ):
        assert path in paths, f"missing server path {path}"


@pytest.mark.drift
def test_create_pass_request_fields_match_spec():
    if not SPEC.exists():
        pytest.skip("vendored openapi.json snapshot missing; run `make fetch-spec`")
    spec = json.loads(SPEC.read_text())
    schema = spec["components"]["schemas"]["CreatePassRequest"]["properties"]
    expected = {
        "pass_id",
        "template",
        "wallet_type",
        "person_uid",
        "variant",
        "template_version",
    }
    assert expected <= set(schema.keys())
