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
