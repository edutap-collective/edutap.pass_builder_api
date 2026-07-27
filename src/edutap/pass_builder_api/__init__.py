"""Async client for the edutap.pass_builder REST service."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("edutap.pass_builder_api")
except PackageNotFoundError:  # pragma: no cover - during local dev before install
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
