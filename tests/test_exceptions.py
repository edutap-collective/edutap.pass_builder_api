import pytest

from edutap.pass_builder_api.exceptions import (
    PassBuilderForbiddenError,
    PassBuilderServerError,
    PassBuilderValidationError,
    raise_for_problem,
)


def test_maps_403_to_forbidden_and_keeps_problem():
    body = (
        b'{"type":"urn:edutap:pass-builder:insufficient_scope",'
        b'"title":"Insufficient scope","status":403,"detail":"need render"}'
    )
    with pytest.raises(PassBuilderForbiddenError) as exc:
        raise_for_problem(403, body)
    assert exc.value.problem.status == 403
    assert exc.value.problem.detail == "need render"


def test_maps_422_to_validation_error():
    with pytest.raises(PassBuilderValidationError):
        raise_for_problem(422, b'{"title":"bad","status":422}')


def test_unmapped_5xx_becomes_server_error_even_without_problem_json():
    with pytest.raises(PassBuilderServerError) as exc:
        raise_for_problem(500, b"upstream boom")
    assert exc.value.problem.status == 500
