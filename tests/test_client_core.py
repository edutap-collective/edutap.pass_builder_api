import httpx
import pytest

from edutap.pass_builder_api.client import PassBuilderClient
from edutap.pass_builder_api.exceptions import PassBuilderAuthError


def _client(handler, token="tok"):  # noqa: S107
    return PassBuilderClient(
        base_url="http://test",
        token=token,
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.anyio
async def test_sends_bearer_token():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"status": "ok"})

    async with _client(handler) as client:
        await client.healthz()
    assert seen["auth"] == "Bearer tok"


@pytest.mark.anyio
async def test_healthz_returns_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok"})

    async with _client(handler) as client:
        assert await client.healthz() == {"status": "ok"}


@pytest.mark.anyio
async def test_readyz_returns_body_on_503_without_raising():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503, json={"status": "not_ready", "checks": {"db": False}}
        )

    async with _client(handler) as client:
        body = await client.readyz()
    assert body["status"] == "not_ready"


@pytest.mark.anyio
async def test_error_response_raises_mapped_exception():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"title": "nope", "status": 401})

    async with _client(handler, token=None) as client:
        with pytest.raises(PassBuilderAuthError):
            await client.healthz()
