import json

import httpx
import pytest

from edutap.pass_builder_api.client import API_PREFIX, PassBuilderClient
from edutap.pass_builder_api.exceptions import PassBuilderError
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
        assert request.url.path == f"{API_PREFIX}/passes"
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
            wallet_type=WalletType.GOOGLE_ST,
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
            wallet_type=WalletType.APPLE_VAS,
            person_uid="abc@lmu.de",
        )
    assert isinstance(result, ApplePassResult)
    assert result.content == b"PKPASSBYTES"
    assert result.template_version == 2
    assert result.credential_set == "cs-1"


@pytest.mark.anyio
async def test_save_link_returns_jwt_string():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"{API_PREFIX}/passes/p-1/save-link"
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
            template="student-id", wallet_type=WalletType.GOOGLE_ST
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


@pytest.mark.anyio
async def test_deactivate_pass_posts_and_returns_the_new_state():
    """`POST`, not `DELETE` -- the builder deletes nothing, it expires an object."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == f"{API_PREFIX}/passes/p-1/deactivate"
        return httpx.Response(
            200,
            json={
                "pass_id": "p-1",
                "object_id": "iss.p-1.object",
                "state": "EXPIRED",
            },
        )

    async with _client(handler) as client:
        result = await client.deactivate_pass("p-1", template="student-id")

    assert result.object_id == "iss.p-1.object"
    assert result.state == "EXPIRED"


@pytest.mark.anyio
async def test_deactivate_pass_sends_no_person_uid():
    """Withdrawing re-renders nothing, so no person data may travel with it.

    Asserted on the wire rather than on the model: a field added to the request
    model later would reach the server whether or not anyone meant it to.
    """
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={"pass_id": "p-1", "object_id": "iss.p-1", "state": "EXPIRED"},
        )

    async with _client(handler) as client:
        await client.deactivate_pass("p-1", template="student-id", variant="v2")

    assert "person_uid" not in seen
    assert seen == {"template": "student-id", "wallet_type": "GOOGLE_ST", "variant": "v2"}


@pytest.mark.anyio
async def test_deactivate_pass_defaults_to_google_smart_tap():
    """The only wallet type the server can withdraw, so the caller need not say it."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["wallet_type"] == "GOOGLE_ST"
        return httpx.Response(
            200,
            json={"pass_id": "p-1", "object_id": "iss.p-1", "state": "EXPIRED"},
        )

    async with _client(handler) as client:
        await client.deactivate_pass("p-1", template="student-id")


@pytest.mark.anyio
async def test_deactivate_pass_surfaces_the_501_as_an_error():
    """An Apple pass cannot be withdrawn here, and the caller has to notice.

    The server answers a problem document; the client turns it into an
    exception rather than a response object nobody inspects.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            501,
            json={
                "type": "urn:edutap:pass-builder:wallet_type_not_supported",
                "title": "Withdrawing is only implemented for Google Wallet passes",
                "status": 501,
            },
            headers={"content-type": "application/problem+json"},
        )

    async with _client(handler) as client:
        with pytest.raises(PassBuilderError) as caught:
            await client.deactivate_pass(
                "p-1", template="student-id", wallet_type=WalletType.APPLE_VAS
            )

    assert caught.value.problem.status == 501


@pytest.mark.anyio
async def test_deactivate_pass_rejects_a_malformed_pass_id():
    """Validated before the request, like every other pass-scoped call."""

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("no request should be sent")

    async with _client(handler) as client:
        with pytest.raises(ValueError):
            await client.deactivate_pass("", template="student-id")
