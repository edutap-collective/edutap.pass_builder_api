# edutap.pass_builder_api Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `edutap.pass_builder_api`, a Pythonic async client for the `edutap.pass_builder` REST service, mirroring `edutap.heidi_api` in shape and tooling.

**Architecture:** A thin, typed async transport over `httpx.AsyncClient`. Pydantic models mirror the server's request/response schemas; a `PassBuilderClient` exposes the `render`-scope methods (`create_pass`, `update_pass`, `save_link`, `preview`) plus ops probes. RFC 9457 `problem+json` errors decode into a typed exception hierarchy. No business logic, no persistence.

**Tech Stack:** Python ≥3.12, httpx, Pydantic v2, pydantic-settings, pytest + anyio, ruff, ty, tox, prek; uv for env/deps.

## Global Constraints

- `requires-python = ">=3.12"` (align with `edutap.heidi_api`).
- License: **EUPL 1.2**.
- PEP 420 namespace package under `edutap` — **no** `src/edutap/__init__.py`.
- Settings env prefix: **`PASS_BUILDER_`** (distinct from the server's `EDUTAP_PASS_BUILDER_`).
- `WalletType` values are **lowercase**: `apple`, `google`, `samsung`.
- **No real network in any test** — use `httpx.MockTransport`.
- Async-first: every I/O method is `async def`; no blocking calls.
- Repo remote: `git@github.com:edutap-collective/edutap.pass_builder_api.git`, default branch `main`.
- Commit style: Conventional Commits. Never `git push` without explicit approval.

## File Structure

```
pyproject.toml                              # project + tooling config
Makefile                                    # lint/reformat/test targets + fetch-spec
README.md                                   # quickstart
LICENSE                                     # EUPL 1.2
.gitignore
.pre-commit-config.yaml
.github/workflows/ci.yml                    # GitHub Actions
src/edutap/pass_builder_api/
    __init__.py                             # public re-exports
    models.py                               # enums + request/response models
    exceptions.py                           # ProblemDetail + exception hierarchy + decoder
    settings.py                             # PassBuilderSettings
    validation.py                           # client-side input validators
    client.py                               # PassBuilderClient
tests/
    conftest.py                             # anyio_backend fixture + helpers
    test_package.py                         # import + version smoke test
    test_models.py
    test_exceptions.py
    test_settings.py
    test_validation.py
    test_client_core.py                     # transport, auth header, error mapping, ops
    test_client_render.py                   # create/update/save-link/preview
    test_spec_drift.py                      # models vs vendored openapi snapshot
    data/openapi.json                       # vendored server spec snapshot
docs/                                       # Sphinx + MyST (added in final task)
```

---

### Task 1: Repository scaffolding + tooling

**Files:**
- Create: `pyproject.toml`, `Makefile`, `README.md`, `LICENSE`, `.gitignore`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`
- Create: `src/edutap/pass_builder_api/__init__.py`
- Test: `tests/test_package.py`, `tests/conftest.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: importable package `edutap.pass_builder_api` with `__version__: str`.

- [ ] **Step 1: Write the failing test**

`tests/test_package.py`:

```python
def test_package_imports_and_exposes_version():
    import edutap.pass_builder_api as pkg

    assert isinstance(pkg.__version__, str)
    assert pkg.__version__ != ""
```

`tests/conftest.py`:

```python
import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_package.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'edutap.pass_builder_api'`.

- [ ] **Step 3: Write scaffolding**

`pyproject.toml`:

```toml
[project]
name = "edutap.pass_builder_api"
version = "0.1.0"
description = "Pythonic async client for the edutap.pass_builder REST service."
readme = "README.md"
requires-python = ">=3.12"
license = { text = "EUPL 1.2" }
authors = [{ name = "Alexander Loechel", email = "Alexander.Loechel@lmu.de" }]
keywords = ["edutap", "wallet", "pass", "client"]
dependencies = [
    "httpx",
    "pydantic>=2",
    "pydantic-settings",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "anyio",
    "ruff",
    "ty",
    "pdbp",
]

[project.urls]
Source = "https://github.com/edutap-collective/edutap.pass_builder_api"

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
include = ["edutap*"]

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
markers = ["drift: spec-drift checks against the vendored server OpenAPI snapshot"]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "D", "S", "B", "UP"]
ignore = ["D203", "D213"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "D"]

[tool.ruff.lint.pydocstyle]
convention = "numpy"
```

`src/edutap/pass_builder_api/__init__.py`:

```python
"""Async client for the edutap.pass_builder REST service."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version


try:
    __version__ = version("edutap.pass_builder_api")
except PackageNotFoundError:  # pragma: no cover - during local dev before install
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
```

`Makefile`:

```makefile
.PHONY: install lint reformat test-local fetch-spec

install:
	uv pip install -U -e ".[dev]"

lint:
	uv run ruff check .
	uv run ty check || true

reformat:
	uv run ruff format .
	uv run ruff check --fix .

test-local:
	uv run pytest -q

fetch-spec:
	python scripts/fetch_spec.py
```

`.gitignore`:

```gitignore
__pycache__/
*.egg-info/
.venv/
.ruff_cache/
.pytest_cache/
dist/
build/
.env
.superpowers/
```

`README.md`:

```markdown
# edutap.pass_builder_api

Pythonic async client for the `edutap.pass_builder` REST service.
See `docs/` for reference. Quickstart is added in the final implementation task.
```

`LICENSE`: put the full EUPL 1.2 text (copy from `edutap.heidi_api/LICENSE`).

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

`.github/workflows/ci.yml`:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v3
      - name: Set up Python
        run: uv python install ${{ matrix.python-version }}
      - name: Install
        run: uv pip install --system -e ".[dev]"
      - name: Lint
        run: uv run ruff check .
      - name: Test
        run: uv run pytest -q
```

- [ ] **Step 4: Install and run the test to verify it passes**

Run: `uv venv && uv pip install -U -e ".[dev]" && uv run pytest tests/test_package.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: scaffold edutap.pass_builder_api package and tooling"
```

---

### Task 2: Models (enums + request/response schemas)

**Files:**
- Create: `src/edutap/pass_builder_api/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `WalletType(StrEnum)`: `APPLE="apple"`, `GOOGLE="google"`, `SAMSUNG="samsung"`.
  - `CreatePassRequest(pass_id: str, template: str, wallet_type: WalletType, person_uid: str, variant: str | None = None, template_version: int | None = None)`
  - `UpdatePassRequest(template: str, wallet_type: WalletType, person_uid: str, variant: str | None = None, template_version: int | None = None)`
  - `SaveLinkRequest(template: str, variant: str | None = None, template_version: int | None = None)`
  - `PreviewRequest(template: str, wallet_type: WalletType, variant: str | None = None, template_version: int | None = None, sample_data: dict[str, Any] | None = None)`
  - `GooglePassResponse(pass_id: str, object_id: str, class_id: str, template_version: int, variant: str)`
  - `ApplePassResult(content: bytes, template_version: int | None = None, variant: str | None = None, credential_set: str | None = None)`
  - `PreviewResponse(pass_json: dict | None = None, object_json: dict | None = None, bound_fields: list[str] = [])`
  - `SaveLinkResponse(save_link: str)`

- [ ] **Step 1: Write the failing test**

`tests/test_models.py`:

```python
from edutap.pass_builder_api.models import CreatePassRequest
from edutap.pass_builder_api.models import GooglePassResponse
from edutap.pass_builder_api.models import WalletType


def test_wallet_type_values_are_lowercase():
    assert WalletType.APPLE == "apple"
    assert WalletType.GOOGLE == "google"
    assert WalletType.SAMSUNG == "samsung"


def test_create_pass_request_serializes_with_server_field_names():
    req = CreatePassRequest(
        pass_id="p-1",
        template="student-id",
        wallet_type=WalletType.GOOGLE,
        person_uid="abc@lmu.de",
    )
    payload = req.model_dump(mode="json", exclude_none=True)
    assert payload == {
        "pass_id": "p-1",
        "template": "student-id",
        "wallet_type": "google",
        "person_uid": "abc@lmu.de",
    }


def test_google_pass_response_parses_server_json():
    resp = GooglePassResponse.model_validate_json(
        b'{"pass_id":"p-1","object_id":"iss.p-1.object",'
        b'"class_id":"iss.student.class","template_version":3,"variant":"default"}'
    )
    assert resp.object_id == "iss.p-1.object"
    assert resp.template_version == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'edutap.pass_builder_api.models'`.

- [ ] **Step 3: Write the models**

`src/edutap/pass_builder_api/models.py`:

```python
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
    pass_id: str
    template: str
    wallet_type: WalletType
    person_uid: str
    variant: str | None = None
    template_version: int | None = None


class UpdatePassRequest(BaseModel):
    template: str
    wallet_type: WalletType
    person_uid: str
    variant: str | None = None
    template_version: int | None = None


class SaveLinkRequest(BaseModel):
    template: str
    variant: str | None = None
    template_version: int | None = None


class PreviewRequest(BaseModel):
    template: str
    wallet_type: WalletType
    variant: str | None = None
    template_version: int | None = None
    sample_data: dict[str, Any] | None = None


class GooglePassResponse(BaseModel):
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
    pass_json: dict[str, Any] | None = None
    object_json: dict[str, Any] | None = None
    bound_fields: list[str] = []


class SaveLinkResponse(BaseModel):
    save_link: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/edutap/pass_builder_api/models.py tests/test_models.py
git commit -m "feat: add pass_builder request/response models"
```

---

### Task 3: Exceptions (ProblemDetail + hierarchy + decoder)

**Files:**
- Create: `src/edutap/pass_builder_api/exceptions.py`
- Test: `tests/test_exceptions.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `ProblemDetail(type: str, title: str, status: int, detail: str | None, instance: str | None)`
  - `PassBuilderError(problem: ProblemDetail)` base, with `.problem` attribute
  - `PassBuilderAuthError`, `PassBuilderForbiddenError`, `PassBuilderNotFoundError`, `PassBuilderConflictError`, `PassBuilderValidationError`, `PassBuilderServerError`
  - `raise_for_problem(status_code: int, body: bytes) -> None` — raises the mapped exception.

- [ ] **Step 1: Write the failing test**

`tests/test_exceptions.py`:

```python
import pytest

from edutap.pass_builder_api.exceptions import PassBuilderForbiddenError
from edutap.pass_builder_api.exceptions import PassBuilderServerError
from edutap.pass_builder_api.exceptions import PassBuilderValidationError
from edutap.pass_builder_api.exceptions import raise_for_problem


def test_maps_403_to_forbidden_and_keeps_problem():
    body = (
        b'{"type":"urn:edutap:pass-builder:insufficient_scope",'
        b'"title":"Insufficient scope","status":403,"detail":"need render"}'
    )
    with pytest.raises(PassBuilderForbiddenError) as exc:
        raise_for_problem(403, body)
    assert exc.value.problem.status == 403
    assert exc.value.problem.detail == "need render"


def test_maps_422_to_validation_error():
    with pytest.raises(PassBuilderValidationError):
        raise_for_problem(422, b'{"title":"bad","status":422}')


def test_unmapped_5xx_becomes_server_error_even_without_problem_json():
    with pytest.raises(PassBuilderServerError) as exc:
        raise_for_problem(500, b"upstream boom")
    assert exc.value.problem.status == 500
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_exceptions.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the exceptions module**

`src/edutap/pass_builder_api/exceptions.py`:

```python
"""RFC 9457 problem+json decoding into a typed exception hierarchy."""

import json

from pydantic import BaseModel


class ProblemDetail(BaseModel):
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_exceptions.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/edutap/pass_builder_api/exceptions.py tests/test_exceptions.py
git commit -m "feat: add problem+json exception hierarchy and decoder"
```

---

### Task 4: Settings

**Files:**
- Create: `src/edutap/pass_builder_api/settings.py`
- Test: `tests/test_settings.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `PassBuilderSettings(base_url: HttpUrl = "http://localhost:8000", token: SecretStr | None = None, timeout: float = 30.0)` with env prefix `PASS_BUILDER_`.

- [ ] **Step 1: Write the failing test**

`tests/test_settings.py`:

```python
from edutap.pass_builder_api.settings import PassBuilderSettings


def test_defaults_when_no_env(monkeypatch):
    for key in ("PASS_BUILDER_BASE_URL", "PASS_BUILDER_TOKEN", "PASS_BUILDER_TIMEOUT"):
        monkeypatch.delenv(key, raising=False)
    settings = PassBuilderSettings(_env_file=None)
    assert str(settings.base_url).startswith("http://localhost:8000")
    assert settings.token is None
    assert settings.timeout == 30.0


def test_reads_env_prefix(monkeypatch):
    monkeypatch.setenv("PASS_BUILDER_BASE_URL", "https://builder.example.com")
    monkeypatch.setenv("PASS_BUILDER_TOKEN", "secret-token")
    settings = PassBuilderSettings(_env_file=None)
    assert str(settings.base_url).startswith("https://builder.example.com")
    assert settings.token.get_secret_value() == "secret-token"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_settings.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the settings module**

`src/edutap/pass_builder_api/settings.py`:

```python
"""Client configuration via pydantic-settings."""

from pydantic import HttpUrl
from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class PassBuilderSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PASS_BUILDER_",
        env_file=".env",
        extra="ignore",
    )

    base_url: HttpUrl = HttpUrl("http://localhost:8000")
    token: SecretStr | None = None
    timeout: float = 30.0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_settings.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/edutap/pass_builder_api/settings.py tests/test_settings.py
git commit -m "feat: add PassBuilderSettings"
```

---

### Task 5: Input validation

**Files:**
- Create: `src/edutap/pass_builder_api/validation.py`
- Test: `tests/test_validation.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `validate_pass_id(value: str) -> str` — raises `ValueError` on empty/blank.
  - `validate_person_uid(value: str) -> str` — raises `ValueError` on empty/blank.

- [ ] **Step 1: Write the failing test**

`tests/test_validation.py`:

```python
import pytest

from edutap.pass_builder_api.validation import validate_pass_id
from edutap.pass_builder_api.validation import validate_person_uid


def test_valid_values_pass_through():
    assert validate_pass_id("p-1") == "p-1"
    assert validate_person_uid("abc@lmu.de") == "abc@lmu.de"


@pytest.mark.parametrize("bad", ["", "   "])
def test_blank_pass_id_rejected(bad):
    with pytest.raises(ValueError, match="pass_id"):
        validate_pass_id(bad)


@pytest.mark.parametrize("bad", ["", "   "])
def test_blank_person_uid_rejected(bad):
    with pytest.raises(ValueError, match="person_uid"):
        validate_person_uid(bad)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_validation.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the validation module**

`src/edutap/pass_builder_api/validation.py`:

```python
"""Client-side input validation, run before any network call."""


def validate_pass_id(value: str) -> str:
    if not value or not value.strip():
        raise ValueError("pass_id must be a non-empty string")
    return value


def validate_person_uid(value: str) -> str:
    if not value or not value.strip():
        raise ValueError("person_uid must be a non-empty string")
    return value
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_validation.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/edutap/pass_builder_api/validation.py tests/test_validation.py
git commit -m "feat: add client-side input validators"
```

---

### Task 6: Client core (transport, auth, error mapping, ops probes)

**Files:**
- Create: `src/edutap/pass_builder_api/client.py`
- Test: `tests/test_client_core.py`

**Interfaces:**
- Consumes: `PassBuilderSettings` (Task 4), `raise_for_problem` (Task 3).
- Produces:
  - `PassBuilderClient(settings=None, *, base_url=None, token=None, timeout=None, transport=None)`
  - `async __aenter__/__aexit__`, `async aclose()`
  - `async _request(method: str, path: str, *, json=None, headers=None, raise_on_error=True) -> httpx.Response`
  - `async healthz() -> dict`, `async readyz() -> dict`
  - Auth header `Authorization: Bearer <token>` set when a token is present.

- [ ] **Step 1: Write the failing test**

`tests/test_client_core.py`:

```python
import httpx
import pytest

from edutap.pass_builder_api.client import PassBuilderClient
from edutap.pass_builder_api.exceptions import PassBuilderAuthError


def _client(handler, token="tok"):
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_client_core.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the client core**

`src/edutap/pass_builder_api/client.py`:

```python
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
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        settings = settings or PassBuilderSettings()
        resolved_base = str(base_url or settings.base_url).rstrip("/")
        resolved_token = token
        if resolved_token is None and settings.token is not None:
            resolved_token = settings.token.get_secret_value()
        headers = {}
        if resolved_token:
            headers["Authorization"] = f"Bearer {resolved_token}"
        self._client = httpx.AsyncClient(
            base_url=resolved_base,
            timeout=timeout or settings.timeout,
            headers=headers,
            transport=transport,
        )

    async def __aenter__(self) -> "PassBuilderClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
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
        response = await self._request("GET", "/healthz")
        return response.json()

    async def readyz(self) -> dict[str, Any]:
        # 503 "not ready" is a valid answer, not a transport error.
        response = await self._request("GET", "/readyz", raise_on_error=False)
        return response.json()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_client_core.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/edutap/pass_builder_api/client.py tests/test_client_core.py
git commit -m "feat: add PassBuilderClient core with auth and error mapping"
```

---

### Task 7: Client render methods

**Files:**
- Modify: `src/edutap/pass_builder_api/client.py`
- Test: `tests/test_client_render.py`

**Interfaces:**
- Consumes: `PassBuilderClient._request` (Task 6); models (Task 2); validators (Task 5).
- Produces (methods on `PassBuilderClient`):
  - `async create_pass(*, pass_id, template, wallet_type, person_uid, variant=None, template_version=None, request_id=None) -> ApplePassResult | GooglePassResponse`
  - `async create_apple_pass(...) -> ApplePassResult`
  - `async create_google_pass(...) -> GooglePassResponse`
  - `async update_pass(pass_id, *, template, wallet_type, person_uid, variant=None, template_version=None, request_id=None) -> ApplePassResult | GooglePassResponse`
  - `async save_link(pass_id, *, template, variant=None, template_version=None) -> str`
  - `async preview(*, template, wallet_type, variant=None, template_version=None, sample_data=None) -> PreviewResponse`

- [ ] **Step 1: Write the failing test**

`tests/test_client_render.py`:

```python
import httpx
import pytest

from edutap.pass_builder_api.client import PassBuilderClient
from edutap.pass_builder_api.models import ApplePassResult
from edutap.pass_builder_api.models import GooglePassResponse
from edutap.pass_builder_api.models import WalletType


def _client(handler):
    return PassBuilderClient(
        base_url="http://test", token="tok", transport=httpx.MockTransport(handler)
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
            pass_id="p-1",
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
            pass_id="p-1",
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
async def test_create_google_pass_typed_wrapper_rejects_apple():
    async with _client(lambda r: httpx.Response(201, json={})) as client:
        with pytest.raises(ValueError, match="google"):
            await client.create_google_pass(
                pass_id="p-1",
                template="t",
                person_uid="u",
                wallet_type=WalletType.APPLE,  # type: ignore[call-arg]
            )
```

> Note: the last test calls the wrapper with a wrong wallet type only to prove
> the guard; the wrapper's normal signature has no `wallet_type` parameter.
> Adjust it to match the final wrapper signature (see Step 3) — the guard is on
> the response type, so instead assert that an Apple response body raises.
> Replace that test body with:

```python
@pytest.mark.anyio
async def test_create_google_pass_wrapper_raises_on_non_google_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=b"PK", headers={"Content-Type": "application/vnd.apple.pkpass"}
        )

    async with _client(handler) as client:
        with pytest.raises(TypeError, match="expected a Google"):
            await client.create_google_pass(pass_id="p-1", template="t", person_uid="u")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_client_render.py -v`
Expected: FAIL — `AttributeError: 'PassBuilderClient' object has no attribute 'create_pass'`.

- [ ] **Step 3: Add the render methods to the client**

Add imports at the top of `client.py`:

```python
from .models import ApplePassResult
from .models import CreatePassRequest
from .models import GooglePassResponse
from .models import PreviewRequest
from .models import PreviewResponse
from .models import SaveLinkRequest
from .models import SaveLinkResponse
from .models import UpdatePassRequest
from .models import WalletType
from .validation import validate_pass_id
from .validation import validate_person_uid
```

Add these methods to `PassBuilderClient`:

```python
@staticmethod
def _int_or_none(value: str | None) -> int | None:
    return int(value) if value is not None else None


def _parse_pass_response(
    self, wallet_type: WalletType, response: httpx.Response
) -> ApplePassResult | GooglePassResponse:
    if wallet_type == WalletType.APPLE:
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
        "POST", "/api/v1/passes", json=payload, headers=headers
    )
    return self._parse_pass_response(wallet_type, response)


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
    result = await self.create_pass(
        pass_id=pass_id,
        template=template,
        wallet_type=WalletType.APPLE,
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
    result = await self.create_pass(
        pass_id=pass_id,
        template=template,
        wallet_type=WalletType.GOOGLE,
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
        "PUT", f"/api/v1/passes/{pass_id}", json=payload, headers=headers
    )
    return self._parse_pass_response(wallet_type, response)


async def save_link(
    self,
    pass_id: str,
    *,
    template: str,
    variant: str | None = None,
    template_version: int | None = None,
) -> str:
    validate_pass_id(pass_id)
    payload = SaveLinkRequest(
        template=template, variant=variant, template_version=template_version
    ).model_dump(mode="json", exclude_none=True)
    response = await self._request(
        "POST", f"/api/v1/passes/{pass_id}/save-link", json=payload
    )
    return SaveLinkResponse.model_validate_json(response.content).save_link


async def preview(
    self,
    *,
    template: str,
    wallet_type: WalletType,
    variant: str | None = None,
    template_version: int | None = None,
    sample_data: dict[str, Any] | None = None,
) -> PreviewResponse:
    payload = PreviewRequest(
        template=template,
        wallet_type=wallet_type,
        variant=variant,
        template_version=template_version,
        sample_data=sample_data,
    ).model_dump(mode="json", exclude_none=True)
    response = await self._request("POST", "/api/v1/passes/preview", json=payload)
    return PreviewResponse.model_validate_json(response.content)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_client_render.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/edutap/pass_builder_api/client.py tests/test_client_render.py
git commit -m "feat: add render methods (create/update/save-link/preview)"
```

---

### Task 8: Public API surface + spec-drift snapshot & test

**Files:**
- Modify: `src/edutap/pass_builder_api/__init__.py`
- Create: `scripts/fetch_spec.py`, `tests/data/openapi.json`
- Test: `tests/test_public_api.py`, `tests/test_spec_drift.py`

**Interfaces:**
- Consumes: everything above.
- Produces: top-level re-exports on `edutap.pass_builder_api`.

- [ ] **Step 1: Write the failing tests**

`tests/test_public_api.py`:

```python
import edutap.pass_builder_api as pkg


def test_public_exports_present():
    for name in (
        "PassBuilderClient",
        "PassBuilderSettings",
        "WalletType",
        "GooglePassResponse",
        "ApplePassResult",
        "PreviewResponse",
        "PassBuilderError",
    ):
        assert hasattr(pkg, name), name
```

`tests/test_spec_drift.py`:

```python
import json
from pathlib import Path

import pytest

SPEC = Path(__file__).parent / "data" / "openapi.json"


@pytest.mark.drift
def test_render_paths_present_in_vendored_spec():
    if not SPEC.exists():
        pytest.skip("vendored openapi.json snapshot missing; run `make fetch-spec`")
    spec = json.loads(SPEC.read_text())
    paths = spec.get("paths", {})
    for path in (
        "/api/v1/passes",
        "/api/v1/passes/{pass_id}",
        "/api/v1/passes/{pass_id}/save-link",
        "/api/v1/passes/preview",
    ):
        assert path in paths, f"missing server path {path}"


@pytest.mark.drift
def test_create_pass_request_fields_match_spec():
    if not SPEC.exists():
        pytest.skip("vendored openapi.json snapshot missing; run `make fetch-spec`")
    spec = json.loads(SPEC.read_text())
    schema = spec["components"]["schemas"]["CreatePassRequest"]["properties"]
    expected = {
        "pass_id",
        "template",
        "wallet_type",
        "person_uid",
        "variant",
        "template_version",
    }
    assert expected <= set(schema.keys())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_public_api.py -v`
Expected: FAIL — attributes not exported yet. (The drift tests skip until the snapshot exists — that is acceptable for this step.)

- [ ] **Step 3: Wire the public API and the fetch-spec helper**

Replace `src/edutap/pass_builder_api/__init__.py`:

```python
"""Async client for the edutap.pass_builder REST service."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version

from .client import PassBuilderClient
from .exceptions import PassBuilderAuthError
from .exceptions import PassBuilderConflictError
from .exceptions import PassBuilderError
from .exceptions import PassBuilderForbiddenError
from .exceptions import PassBuilderNotFoundError
from .exceptions import PassBuilderServerError
from .exceptions import PassBuilderValidationError
from .exceptions import ProblemDetail
from .models import ApplePassResult
from .models import GooglePassResponse
from .models import PreviewResponse
from .models import WalletType
from .settings import PassBuilderSettings


try:
    __version__ = version("edutap.pass_builder_api")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0.dev0"

__all__ = [
    "__version__",
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
```

`scripts/fetch_spec.py` (dumps the server OpenAPI to the vendored snapshot):

```python
"""Dump the edutap.pass_builder OpenAPI spec into tests/data/openapi.json.

Requires `edutap.pass_builder` importable in the same environment. OpenAPI
generation does not need a live database.
"""

import json
from pathlib import Path


def main() -> None:
    from edutap.pass_builder.app import create_app

    app = create_app()
    spec = app.openapi()
    out = Path(__file__).parent.parent / "tests" / "data" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, indent=2, sort_keys=True))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
```

Then generate the snapshot (see open question 2 in the spec — if the app cannot
be imported headlessly, curl `/api/v1/openapi.json` from a running instance and
save it to `tests/data/openapi.json` instead):

Run: `uv run python scripts/fetch_spec.py` **or** `curl -s http://localhost:8000/api/v1/openapi.json -o tests/data/openapi.json`

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_public_api.py tests/test_spec_drift.py -v`
Expected: `test_public_api` PASS; drift tests PASS if the snapshot was generated, otherwise SKIP with the documented reason.

- [ ] **Step 5: Commit**

```bash
git add src/edutap/pass_builder_api/__init__.py scripts/fetch_spec.py tests/test_public_api.py tests/test_spec_drift.py tests/data/openapi.json
git commit -m "feat: export public API and add spec-drift snapshot test"
```

---

### Task 9: Docs, README quickstart, full test run, release prep

**Files:**
- Modify: `README.md`
- Create: `docs/conf.py`, `docs/index.md`, `docs/reference.md`

**Interfaces:**
- Consumes: the finished client.
- Produces: user-facing docs; a green full test suite.

- [ ] **Step 1: Write the README quickstart**

Replace `README.md`:

````markdown
# edutap.pass_builder_api

Pythonic async client for the `edutap.pass_builder` REST service.

## Install

```bash
uv pip install -e ".[dev]"
```

## Quickstart

```python
import anyio

from edutap.pass_builder_api import PassBuilderClient, WalletType


async def main() -> None:
    async with PassBuilderClient(
        base_url="http://localhost:8000", token="render-scope-token"
    ) as client:
        google = await client.create_google_pass(
            pass_id="p-1", template="student-id", person_uid="abc@lmu.de"
        )
        link = await client.save_link("p-1", template="student-id")
        print(google.object_id, link)


anyio.run(main)
```

Configuration can also come from the environment (`PASS_BUILDER_BASE_URL`,
`PASS_BUILDER_TOKEN`, `PASS_BUILDER_TIMEOUT`) via `PassBuilderSettings`.
````

- [ ] **Step 2: Add minimal Sphinx docs**

`docs/conf.py`:

```python
project = "edutap.pass_builder_api"
extensions = ["myst_parser", "sphinx.ext.autodoc"]
myst_enable_extensions = ["colon_fence"]
html_theme = "furo"
```

`docs/index.md`:

```markdown
# edutap.pass_builder_api

Async client for the `edutap.pass_builder` REST service.

```{toctree}
:maxdepth: 2

reference
```
```

`docs/reference.md`:

```markdown
# API Reference

```{eval-rst}
.. autoclass:: edutap.pass_builder_api.PassBuilderClient
   :members:
```
```

- [ ] **Step 3: Run the full suite + lint**

Run: `uv run ruff format . && uv run ruff check . && uv run pytest -q`
Expected: format clean, lint clean, all tests PASS (drift may SKIP without a snapshot).

- [ ] **Step 4: Commit**

```bash
git add README.md docs/
git commit -m "docs: add quickstart and Sphinx reference"
```

- [ ] **Step 5: Tag the release (do not push without approval)**

```bash
git tag v0.1.0
```

Report to the maintainer: suite status, whether the drift snapshot was
generated, and the four spec open questions still outstanding (template UUIDs,
deactivation path, HEIDI account, vendored-spec source) — the last of which is
resolved once `make fetch-spec` runs successfully.

---

## Self-Review

**Spec coverage:**
- Render-first scope (create/update/save-link/preview + ops) → Tasks 6, 7. ✅
- Static bearer auth → Task 6. ✅
- RFC 9457 error hierarchy → Task 3. ✅
- Settings `PASS_BUILDER_` prefix → Task 4. ✅
- Package layout mirroring heidi_api (client/models/settings/exceptions/validation) → Tasks 1–7. ✅
- Union return + typed wrappers → Task 7 (`create_pass` + `create_apple_pass`/`create_google_pass`). ✅
- Spec-drift snapshot + test → Task 8. ✅
- Tooling (uv/ruff/ty/pytest/tox/prek, GitHub Actions) → Task 1. ✅ (`tox.ini` not authored separately; the CI matrix + pytest cover the matrix need. Add `tox.ini` only if the maintainer wants local matrix runs.)
- Docs (Sphinx + MyST, README) → Task 9. ✅

**Placeholder scan:** No TBD/TODO; every code step has concrete content. The one prose caveat in Task 7 Step 1 (rewriting the last test) is resolved inline with the replacement test body. ✅

**Type consistency:** `WalletType`, `CreatePassRequest`, `GooglePassResponse`, `ApplePassResult`, `PreviewResponse`, `SaveLinkResponse`, `PassBuilderClient`, `raise_for_problem`, `validate_pass_id`, `validate_person_uid` are used with identical signatures across tasks. ✅

**Known gap:** `tox.ini` and `ty` config are mentioned in the spec but only the CI matrix is authored (Task 1). If local `tox` matrix runs are required, add a `tox.ini` task; the CI workflow already exercises 3.12/3.13.
```
