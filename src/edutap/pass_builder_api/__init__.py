"""Async client for the edutap.pass_builder REST service."""

from importlib.metadata import PackageNotFoundError, version

from .client import API_PREFIX, PassBuilderClient
from .exceptions import (
    PassBuilderAuthError,
    PassBuilderConflictError,
    PassBuilderError,
    PassBuilderForbiddenError,
    PassBuilderNotFoundError,
    PassBuilderServerError,
    PassBuilderValidationError,
    ProblemDetail,
)
from .models import ApplePassResult, GooglePassResponse, PreviewResponse, WalletType
from .settings import PassBuilderSettings

try:
    __version__ = version("edutap.pass_builder_api")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0.dev0"

__all__ = [
    "__version__",
    "API_PREFIX",
    "PassBuilderClient",
    "PassBuilderSettings",
    "WalletType",
    "ApplePassResult",
    "GooglePassResponse",
    "PreviewResponse",
    "ProblemDetail",
    "PassBuilderError",
    "PassBuilderAuthError",
    "PassBuilderForbiddenError",
    "PassBuilderNotFoundError",
    "PassBuilderConflictError",
    "PassBuilderValidationError",
    "PassBuilderServerError",
]
