"""Async client for the edutap.pass_builder REST service."""

from typing import Any

import httpx

from .exceptions import raise_for_problem
from .models import (
    ApplePassResult,
    CreatePassRequest,
    DeactivatePassRequest,
    DeactivatePassResponse,
    GooglePassResponse,
    PreviewRequest,
    PreviewResponse,
    SaveLinkRequest,
    SaveLinkResponse,
    UpdatePassRequest,
    WalletType,
)
from .settings import PassBuilderSettings
from .validation import validate_pass_id, validate_person_uid

API_PREFIX = "/builder/v1"
"""The server's business path, mirroring `edutap.pass_builder.app.API_PREFIX`.

The mount point in front of it (`/internal-api/wallet` by default) is a
deployment concern and belongs in `base_url`, not here.
"""


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

    @staticmethod
    def _int_or_none(value: str | None) -> int | None:
        return int(value) if value is not None else None

    def _parse_pass_response(
        self, response: httpx.Response
    ) -> ApplePassResult | GooglePassResponse:
        """Parse a create/update-pass response by its actual content type.

        The response shape is determined by what the server sent back
        (an Apple pkpass body vs. a Google JSON body), not by which
        wallet type the caller requested — this lets typed wrappers such
        as ``create_google_pass`` detect a request/response mismatch and
        raise instead of silently mis-parsing the body.
        """
        content_type = response.headers.get("content-type", "")
        if "vnd.apple.pkpass" in content_type:
            return ApplePassResult(
                content=response.content,
                template_version=self._int_or_none(
                    response.headers.get("X-Template-Version")
                ),
                variant=response.headers.get("X-Variant"),
                credential_set=response.headers.get("X-Credential-Set"),
            )
        return GooglePassResponse.model_validate_json(response.content)

    async def create_pass(
        self,
        *,
        pass_id: str,
        template: str,
        wallet_type: WalletType,
        person_uid: str,
        variant: str | None = None,
        template_version: int | None = None,
        request_id: str | None = None,
    ) -> ApplePassResult | GooglePassResponse:
        """Create a pass, returning an Apple result or a Google response."""
        validate_pass_id(pass_id)
        validate_person_uid(person_uid)
        payload = CreatePassRequest(
            pass_id=pass_id,
            template=template,
            wallet_type=wallet_type,
            person_uid=person_uid,
            variant=variant,
            template_version=template_version,
        ).model_dump(mode="json", exclude_none=True)
        headers = {"x-request-id": request_id} if request_id else None
        response = await self._request(
            "POST", f"{API_PREFIX}/passes", json=payload, headers=headers
        )
        return self._parse_pass_response(response)

    async def create_apple_pass(
        self,
        *,
        pass_id: str,
        template: str,
        person_uid: str,
        variant: str | None = None,
        template_version: int | None = None,
        request_id: str | None = None,
    ) -> ApplePassResult:
        """Create an Apple pass and return the typed Apple result."""
        result = await self.create_pass(
            pass_id=pass_id,
            template=template,
            wallet_type=WalletType.APPLE_VAS,
            person_uid=person_uid,
            variant=variant,
            template_version=template_version,
            request_id=request_id,
        )
        if not isinstance(result, ApplePassResult):  # pragma: no cover - defensive
            raise TypeError("expected an Apple pass result")
        return result

    async def create_google_pass(
        self,
        *,
        pass_id: str,
        template: str,
        person_uid: str,
        variant: str | None = None,
        template_version: int | None = None,
        request_id: str | None = None,
    ) -> GooglePassResponse:
        """Create a Google pass and return the typed Google response."""
        result = await self.create_pass(
            pass_id=pass_id,
            template=template,
            wallet_type=WalletType.GOOGLE_ST,
            person_uid=person_uid,
            variant=variant,
            template_version=template_version,
            request_id=request_id,
        )
        if not isinstance(result, GooglePassResponse):
            raise TypeError("expected a Google pass response")
        return result

    async def update_pass(
        self,
        pass_id: str,
        *,
        template: str,
        wallet_type: WalletType,
        person_uid: str,
        variant: str | None = None,
        template_version: int | None = None,
        request_id: str | None = None,
    ) -> ApplePassResult | GooglePassResponse:
        """Update an existing pass, returning an Apple result or Google response."""
        validate_pass_id(pass_id)
        validate_person_uid(person_uid)
        payload = UpdatePassRequest(
            template=template,
            wallet_type=wallet_type,
            person_uid=person_uid,
            variant=variant,
            template_version=template_version,
        ).model_dump(mode="json", exclude_none=True)
        headers = {"x-request-id": request_id} if request_id else None
        response = await self._request(
            "PUT", f"{API_PREFIX}/passes/{pass_id}", json=payload, headers=headers
        )
        return self._parse_pass_response(response)

    async def save_link(
        self,
        pass_id: str,
        *,
        template: str,
        variant: str | None = None,
        template_version: int | None = None,
    ) -> str:
        """Request a save-to-wallet link (signed JWT) for an existing pass."""
        validate_pass_id(pass_id)
        payload = SaveLinkRequest(
            template=template, variant=variant, template_version=template_version
        ).model_dump(mode="json", exclude_none=True)
        response = await self._request(
            "POST", f"{API_PREFIX}/passes/{pass_id}/save-link", json=payload
        )
        return SaveLinkResponse.model_validate_json(response.content).save_link

    async def deactivate_pass(
        self,
        pass_id: str,
        *,
        template: str,
        wallet_type: WalletType = WalletType.GOOGLE_ST,
        variant: str | None = None,
        template_version: int | None = None,
        request_id: str | None = None,
    ) -> DeactivatePassResponse:
        """Withdraw an issued pass. Google only -- Apple answers `501`.

        `POST` rather than `DELETE`, because nothing is deleted: the builder
        keeps no register of issued passes. What happens is a state change on
        the Google object, `state -> EXPIRED`.

        Idempotent -- withdrawing an already withdrawn pass answers `200`
        again, so a caller that did not see the first answer can simply repeat
        the call.
        """
        validate_pass_id(pass_id)
        payload = DeactivatePassRequest(
            template=template,
            wallet_type=wallet_type,
            variant=variant,
            template_version=template_version,
        ).model_dump(mode="json", exclude_none=True)
        headers = {"x-request-id": request_id} if request_id else None
        response = await self._request(
            "POST",
            f"{API_PREFIX}/passes/{pass_id}/deactivate",
            json=payload,
            headers=headers,
        )
        return DeactivatePassResponse.model_validate_json(response.content)

    async def preview(
        self,
        *,
        template: str,
        wallet_type: WalletType,
        variant: str | None = None,
        template_version: int | None = None,
        sample_data: dict[str, Any] | None = None,
    ) -> PreviewResponse:
        """Render a preview of a pass without persisting it."""
        payload = PreviewRequest(
            template=template,
            wallet_type=wallet_type,
            variant=variant,
            template_version=template_version,
            sample_data=sample_data,
        ).model_dump(mode="json", exclude_none=True)
        response = await self._request(
            "POST", f"{API_PREFIX}/passes/preview", json=payload
        )
        return PreviewResponse.model_validate_json(response.content)
