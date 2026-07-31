import json
from pathlib import Path

import pytest

from edutap.pass_builder_api.client import API_PREFIX

SPEC = Path(__file__).parent / "data" / "openapi.json"


@pytest.mark.drift
def test_render_paths_present_in_vendored_spec():
    if not SPEC.exists():
        pytest.skip("vendored openapi.json snapshot missing; run `make fetch-spec`")
    spec = json.loads(SPEC.read_text())
    paths = spec.get("paths", {})
    for path in (
        f"{API_PREFIX}/passes",
        f"{API_PREFIX}/passes/{{pass_id}}",
        f"{API_PREFIX}/passes/{{pass_id}}/save-link",
        f"{API_PREFIX}/passes/preview",
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
