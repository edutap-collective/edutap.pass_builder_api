"""Pydantic request/response models mirroring the pass_builder server schemas."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class WalletType(StrEnum):
    """Wallet platform. Server expects lowercase values."""

    APPLE = "apple"
    GOOGLE = "google"
    SAMSUNG = "samsung"


class CreatePassRequest(BaseModel):
    """Request to create a new pass."""

    pass_id: str
    template: str
    wallet_type: WalletType
    person_uid: str
    variant: str | None = None
    template_version: int | None = None


class UpdatePassRequest(BaseModel):
    """Request to update an existing pass."""

    template: str
    wallet_type: WalletType
    person_uid: str
    variant: str | None = None
    template_version: int | None = None


class SaveLinkRequest(BaseModel):
    """Request to generate a save link for a pass."""

    template: str
    variant: str | None = None
    template_version: int | None = None


class DeactivatePassRequest(BaseModel):
    """Request to withdraw an issued pass.

    No `person_uid`: withdrawing re-renders nothing, so the service reads no
    person data. `template` and `variant` are still needed -- they are what
    resolves the credential set and the Google class the object belongs to.

    `wallet_type` is part of the body although only `GOOGLE` can be served. A
    caller holding an Apple pass has to be told so rather than answered with a
    guess; the service replies `501`, which arrives here as a
    `PassBuilderError`.
    """

    template: str
    wallet_type: WalletType
    variant: str | None = None
    template_version: int | None = None


class DeactivatePassResponse(BaseModel):
    """The withdrawn Google Wallet object and the state it now carries."""

    pass_id: str
    object_id: str
    state: str


class PreviewRequest(BaseModel):
    """Request to preview a pass rendering."""

    template: str
    wallet_type: WalletType
    variant: str | None = None
    template_version: int | None = None
    sample_data: dict[str, Any] | None = None


class GooglePassResponse(BaseModel):
    """Response from creating a Google Pass."""

    pass_id: str
    object_id: str
    class_id: str
    template_version: int
    variant: str


class ApplePassResult(BaseModel):
    """Result of an Apple pass render: raw bytes plus header metadata."""

    content: bytes
    template_version: int | None = None
    variant: str | None = None
    credential_set: str | None = None


class PreviewResponse(BaseModel):
    """Response from a pass preview request."""

    pass_json: dict[str, Any] | None = None
    object_json: dict[str, Any] | None = None
    bound_fields: list[str] = []


class SaveLinkResponse(BaseModel):
    """Response containing a save link for a pass."""

    save_link: str
