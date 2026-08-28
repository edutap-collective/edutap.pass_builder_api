from edutap.pass_builder_api.models import (
    CreatePassRequest,
    GooglePassResponse,
    WalletType,
)


def test_wallet_type_is_the_shared_vocabulary():
    """The wire value is the member name, and it distinguishes the technologies.

    It was `apple` / `google` / `samsung` until 2026-08-28 -- the coarse provider
    axis, which cannot say whether an Apple pass is VAS, Access or Identity. This
    package no longer defines the enum at all; it re-exports the one from
    `edutap.data_models` that the rest of the estate already speaks.
    """
    assert WalletType.APPLE_VAS == "APPLE_VAS"
    assert WalletType.GOOGLE_ST == "GOOGLE_ST"

    # Und der Unterschied, den die alte Achse verschluckt hat:
    assert WalletType.APPLE_ACCESS != WalletType.APPLE_VAS


def test_create_pass_request_serializes_with_server_field_names():
    req = CreatePassRequest(
        pass_id="p-1",  # noqa: S106
        template="student-id",
        wallet_type=WalletType.GOOGLE_ST,
        person_uid="abc@lmu.de",
    )
    payload = req.model_dump(mode="json", exclude_none=True)
    assert payload == {
        "pass_id": "p-1",
        "template": "student-id",
        "wallet_type": "GOOGLE_ST",
        "person_uid": "abc@lmu.de",
    }


def test_google_pass_response_parses_server_json():
    resp = GooglePassResponse.model_validate_json(
        b'{"pass_id":"p-1","object_id":"iss.p-1.object",'
        b'"class_id":"iss.student.class","template_version":3,"variant":"default"}'
    )
    assert resp.object_id == "iss.p-1.object"
    assert resp.template_version == 3
