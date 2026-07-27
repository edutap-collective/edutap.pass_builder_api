"""RFC 9457 problem+json decoding into a typed exception hierarchy."""

import json

from pydantic import BaseModel


class ProblemDetail(BaseModel):
    """RFC 9457 Problem Details for HTTP APIs."""

    type: str = "about:blank"
    title: str = ""
    status: int
    detail: str | None = None
    instance: str | None = None


class PassBuilderError(Exception):
    """Base error carrying the server ProblemDetail."""

    def __init__(self, problem: ProblemDetail) -> None:
        self.problem = problem
        super().__init__(f"{problem.status} {problem.title}: {problem.detail}")


class PassBuilderAuthError(PassBuilderError):
    """401 — missing or invalid bearer token."""


class PassBuilderForbiddenError(PassBuilderError):
    """403 — token lacks the required scope."""


class PassBuilderNotFoundError(PassBuilderError):
    """404 — unknown resource (incl. foreign-tenant objects)."""


class PassBuilderConflictError(PassBuilderError):
    """409 — state conflict."""


class PassBuilderValidationError(PassBuilderError):
    """422 — request failed server-side validation."""


class PassBuilderServerError(PassBuilderError):
    """5xx — server-side failure."""


_STATUS_MAP: dict[int, type[PassBuilderError]] = {
    401: PassBuilderAuthError,
    403: PassBuilderForbiddenError,
    404: PassBuilderNotFoundError,
    409: PassBuilderConflictError,
    422: PassBuilderValidationError,
}


def raise_for_problem(status_code: int, body: bytes) -> None:
    """Decode a problem+json body and raise the mapped exception."""
    try:
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError
        data.setdefault("status", status_code)
        problem = ProblemDetail.model_validate(data)
    except (ValueError, json.JSONDecodeError):
        problem = ProblemDetail(
            title="error",
            status=status_code,
            detail=body.decode("utf-8", errors="replace") or None,
        )

    if status_code in _STATUS_MAP:
        raise _STATUS_MAP[status_code](problem)
    if status_code >= 500:
        raise PassBuilderServerError(problem)
    raise PassBuilderError(problem)
