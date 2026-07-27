from edutap.pass_builder_api.models import (
    CreatePassRequest,
    GooglePassResponse,
    WalletType,
)


def test_wallet_type_values_are_lowercase():
    assert WalletType.APPLE == "apple"
    assert WalletType.GOOGLE == "google"
    assert WalletType.SAMSUNG == "samsung"


def test_create_pass_request_serializes_with_server_field_names():
    req = CreatePassRequest(
        pass_id="p-1",  # noqa: S106
        template="student-id",
        wallet_type=WalletType.GOOGLE,
        person_uid="abc@lmu.de",
    )
    payload = req.model_dump(mode="json", exclude_none=True)
    assert payload == {
        "pass_id": "p-1",
        "template": "student-id",
        "wallet_type": "google",
        "person_uid": "abc@lmu.de",
    }


def test_google_pass_response_parses_server_json():
    resp = GooglePassResponse.model_validate_json(
        b'{"pass_id":"p-1","object_id":"iss.p-1.object",'
        b'"class_id":"iss.student.class","template_version":3,"variant":"default"}'
    )
    assert resp.object_id == "iss.p-1.object"
    assert resp.template_version == 3
