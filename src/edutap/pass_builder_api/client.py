"""Async client for the edutap.pass_builder REST service."""

from typing import Any

import httpx

from .exceptions import raise_for_problem
from .settings import PassBuilderSettings


class PassBuilderClient:
    """Thin async transport over the pass_builder REST API."""

    def __init__(
        self,
        settings: PassBuilderSettings | None = None,
        *,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = settings or PassBuilderSettings()
        resolved_base = str(
            base_url if base_url is not None else settings.base_url
        ).rstrip("/")
        resolved_token = token
        if resolved_token is None and settings.token is not None:
            resolved_token = settings.token.get_secret_value()
        headers = {}
        if resolved_token:
            headers["Authorization"] = f"Bearer {resolved_token}"
        self._client = httpx.AsyncClient(
            base_url=resolved_base,
            timeout=timeout if timeout is not None else settings.timeout,
            headers=headers,
            transport=transport,
        )

    async def __aenter__(self) -> "PassBuilderClient":
        """Enter the async context manager, returning this client."""
        return self

    async def __aexit__(self, *exc: object) -> None:
        """Exit the async context manager, closing the transport."""
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP transport."""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        headers: dict[str, str] | None = None,
        raise_on_error: bool = True,
    ) -> httpx.Response:
        response = await self._client.request(method, path, json=json, headers=headers)
        if raise_on_error and response.status_code >= 400:
            raise_for_problem(response.status_code, response.content)
        return response

    async def healthz(self) -> dict[str, Any]:
        """Call GET /healthz and return the decoded JSON body."""
        response = await self._request("GET", "/healthz")
        return response.json()

    async def readyz(self) -> dict[str, Any]:
        """Call GET /readyz and return the decoded JSON body.

        A 503 "not ready" response is a valid answer, not a transport
        error, so it is returned rather than raised.
        """
        response = await self._request("GET", "/readyz", raise_on_error=False)
        return response.json()
