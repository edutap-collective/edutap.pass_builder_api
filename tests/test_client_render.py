import httpx
import pytest

from edutap.pass_builder_api.client import PassBuilderClient
from edutap.pass_builder_api.models import (
    ApplePassResult,
    GooglePassResponse,
    WalletType,
)


def _client(handler):
    return PassBuilderClient(
        base_url="http://test",
        token="tok",  # noqa: S106
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.anyio
async def test_create_google_pass_returns_model():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/passes"
        assert request.headers.get("x-request-id") == "req-1"
        return httpx.Response(
            201,
            json={
                "pass_id": "p-1",
                "object_id": "iss.p-1.object",
                "class_id": "iss.student.class",
                "template_version": 3,
                "variant": "default",
            },
        )

    async with _client(handler) as client:
        result = await client.create_pass(
            pass_id="p-1",  # noqa: S106
            template="student-id",
            wallet_type=WalletType.GOOGLE,
            person_uid="abc@lmu.de",
            request_id="req-1",
        )
    assert isinstance(result, GooglePassResponse)
    assert result.object_id == "iss.p-1.object"


@pytest.mark.anyio
async def test_create_apple_pass_returns_bytes_and_headers():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"PKPASSBYTES",
            headers={
                "Content-Type": "application/vnd.apple.pkpass",
                "X-Template-Version": "2",
                "X-Variant": "default",
                "X-Credential-Set": "cs-1",
            },
        )

    async with _client(handler) as client:
        result = await client.create_pass(
            pass_id="p-1",  # noqa: S106
            template="student-id",
            wallet_type=WalletType.APPLE,
            person_uid="abc@lmu.de",
        )
    assert isinstance(result, ApplePassResult)
    assert result.content == b"PKPASSBYTES"
    assert result.template_version == 2
    assert result.credential_set == "cs-1"


@pytest.mark.anyio
async def test_save_link_returns_jwt_string():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/passes/p-1/save-link"
        return httpx.Response(200, json={"save_link": "eyJhbGciOi.jwt.sig"})

    async with _client(handler) as client:
        link = await client.save_link("p-1", template="student-id")
    assert link == "eyJhbGciOi.jwt.sig"


@pytest.mark.anyio
async def test_preview_returns_model():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"pass_json": None, "object_json": {"a": 1}, "bound_fields": ["name"]},
        )

    async with _client(handler) as client:
        preview = await client.preview(
            template="student-id", wallet_type=WalletType.GOOGLE
        )
    assert preview.bound_fields == ["name"]
    assert preview.object_json == {"a": 1}


@pytest.mark.anyio
async def test_create_google_pass_wrapper_raises_on_non_google_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"PK",
            headers={"Content-Type": "application/vnd.apple.pkpass"},
        )

    async with _client(handler) as client:
        with pytest.raises(TypeError, match="expected a Google"):
            await client.create_google_pass(
                pass_id="p-1",  # noqa: S106
                template="t",
                person_uid="u",
            )
