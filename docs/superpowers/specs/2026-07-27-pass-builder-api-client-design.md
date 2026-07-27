[[_TOC_]]

# `edutap.pass_builder_api` — Client Library Design

## Purpose

`edutap.pass_builder_api` is a **Pythonic async client** for the
`edutap.pass_builder` REST service, built as a sibling to the existing
`edutap.heidi_api` client. It lets a caller (primarily `lmu_edutap_backend`)
issue and manage wallet passes without hand-rolling `httpx` calls, request
signing, error decoding, or model validation.

It mirrors `edutap.heidi_api` in shape and tooling so the two clients feel
identical from the outside: same package layout, same settings pattern, same
`AsyncClient` lifecycle, same spec-drift test discipline.

## Scope

The `edutap.pass_builder` server exposes several capability scopes: `render`
(issue/preview passes), `manage` (templates, variants, versions, mappings,
fields, audit) and `credentials` (signing material). A full client would cover
all of them.

**This design proposes a render-first client** — v0.x covers exactly the
`render`-scope surface the backend needs, with an architecture that extends
cleanly to `manage`/`credentials` later:

- **In scope (v0.1):** `POST /api/v1/passes`, `PUT /api/v1/passes/{pass_id}`,
  `POST /api/v1/passes/{pass_id}/save-link`, `POST /api/v1/passes/preview`,
  `GET /healthz`, `GET /readyz`.
- **Out of scope (v0.1, later):** templates/variants/versions/mappings/assets,
  credentials, fields, audit. The client is structured so these become
  additional method groups on the same `PassBuilderClient` without breaking
  changes.

> **Decision point for review:** render-first (recommended) vs. full client from
> the start. Render-first ships the backend's need fast and keeps the surface
> small; the management endpoints are administrative and rarely called from a
> credential-issuer backend.

## Non-Goals

- No business logic (no eligibility, no template selection) — that stays in the
  caller. The client is a thin, typed transport.
- No persistence, no caching of issued passes (the server is stateless w.r.t.
  issued passes; `pass_id` is caller-assigned).
- No CLI (matches `edutap.heidi_api`, which is a library only).

## Target server contract (reference)

Extracted from the `edutap.pass_builder` source (no static OpenAPI file is
checked into that repo; it is generated at runtime under
`/api/v1/openapi.json`). Relevant facts the client encodes:

- **Base:** all business endpoints under `/api/v1`; default server port `8000`.
- **Auth:** `Authorization: Bearer <token>` (static, DB-managed token; scope
  `render` required for the pass endpoints). No OAuth2 handshake (unlike HEIDI).
- **Errors:** RFC 9457 `application/problem+json`, `type =
  urn:edutap:pass-builder:<slug>`. Optional request header `x-request-id` is
  echoed into the server audit log.
- **Synchronous** issuing (unlike HEIDI's queued model): the response *is* the
  result.

### Endpoints and models

**`POST /api/v1/passes`** → create.
Request `CreatePassRequest`:
`pass_id: str` (caller-assigned), `template: str` (template key),
`wallet_type: WalletType`, `variant: str | None = None`,
`person_uid: str`, `template_version: int | None = None`.
Response is wallet-dependent:
- **Apple:** `200`, raw `.pkpass` bytes, `Content-Type:
  application/vnd.apple.pkpass`; metadata in headers `X-Template-Version`,
  `X-Variant`, `X-Credential-Set` (last only when a credential set is used).
- **Google:** `201`, JSON `GooglePassResponse`: `pass_id: str`,
  `object_id: str`, `class_id: str`, `template_version: int`, `variant: str`.

**`PUT /api/v1/passes/{pass_id}`** → re-render.
Request `UpdatePassRequest` = `CreatePassRequest` without `pass_id`. Same
wallet-dependent response as create (`200`).

**`POST /api/v1/passes/{pass_id}/save-link`** → Google save-link (JWT).
Request `SaveLinkRequest`: `template: str`, `variant: str | None`,
`template_version: int | None`. Response `{"save_link": "<jwt>"}` (`200`).
Google only (Apple raises server-side).

**`POST /api/v1/passes/preview`** → dry run (no signing, no data provider).
Request `PreviewRequest`: `template: str`, `wallet_type: WalletType`,
`variant: str | None`, `template_version: int | None`,
`sample_data: dict[str, Any] | None`.
Response `PreviewResponse`: `pass_json: dict | None`,
`object_json: dict | None`, `bound_fields: list[str]`.

**`GET /healthz`** → `{"status": "ok"}` (no auth).
**`GET /readyz`** → `{"status": "ready"}` / `503` with `checks` (no auth).

`WalletType` enum: `apple`, `google`, `samsung` (**lowercase**; `samsung`
reserved/unsupported).

## Package layout

Namespace package under the `edutap` namespace, mirroring `edutap.heidi_api`:

```
src/edutap/pass_builder_api/
    __init__.py        # re-exports Client, models, settings, exceptions
    client.py          # PassBuilderClient (async httpx)
    models.py          # Pydantic request/response models + enums
    settings.py        # pydantic-settings PassBuilderSettings
    exceptions.py      # ProblemDetail-based exception hierarchy
    validation.py      # input validators (e.g. person_uid format), like heidi_api
tests/
    test_client.py     # respx / httpx.MockTransport, no real network
    test_spec_drift.py # compares models to a vendored openapi.json snapshot
    data/openapi.json  # vendored server spec snapshot
docs/                  # Sphinx + MyST
pyproject.toml, tox.ini, Makefile, README.md, uv.lock
```

Import surface:

```python
from edutap.pass_builder_api import PassBuilderClient, PassBuilderSettings
from edutap.pass_builder_api.models import WalletType, GooglePassResponse
```

## Public API

```python
class PassBuilderClient:
    def __init__(
        self,
        settings: PassBuilderSettings | None = None,
        *,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float | None = None,
    ) -> None: ...

    async def __aenter__(self) -> "PassBuilderClient": ...
    async def __aexit__(self, *exc: object) -> None: ...

    # render scope
    async def create_pass(
        self, *, pass_id: str, template: str, wallet_type: WalletType,
        person_uid: str, variant: str | None = None,
        template_version: int | None = None,
        request_id: str | None = None,
    ) -> ApplePassResult | GooglePassResponse: ...

    async def update_pass(
        self, pass_id: str, *, template: str, wallet_type: WalletType,
        person_uid: str, variant: str | None = None,
        template_version: int | None = None,
        request_id: str | None = None,
    ) -> ApplePassResult | GooglePassResponse: ...

    async def save_link(
        self, pass_id: str, *, template: str, variant: str | None = None,
        template_version: int | None = None,
    ) -> str: ...

    async def preview(
        self, *, template: str, wallet_type: WalletType,
        variant: str | None = None, template_version: int | None = None,
        sample_data: dict[str, Any] | None = None,
    ) -> PreviewResponse: ...

    # ops
    async def healthz(self) -> dict[str, str]: ...
    async def readyz(self) -> dict[str, Any]: ...
```

`create_pass`/`update_pass` return a union because the server response differs
by wallet:

```python
class ApplePassResult(BaseModel):
    content: bytes                         # raw .pkpass
    template_version: int | None = None    # from X-Template-Version
    variant: str | None = None             # from X-Variant
    credential_set: str | None = None      # from X-Credential-Set

class GooglePassResponse(BaseModel):
    pass_id: str
    object_id: str
    class_id: str
    template_version: int
    variant: str
```

Callers that always know the wallet type may prefer the explicit helpers
`create_apple_pass(...) -> ApplePassResult` and
`create_google_pass(...) -> GooglePassResponse` (thin typed wrappers) to avoid
the union — to be decided during implementation.

## Settings

`pydantic-settings`, mirroring `HeidiSettings` (`env_prefix`, `.env`,
`extra="ignore"`). Distinct prefix from the *server's* `EDUTAP_PASS_BUILDER_`:

```python
class PassBuilderSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PASS_BUILDER_", env_file=".env")
    base_url: HttpUrl = "http://localhost:8000"
    token: SecretStr | None = None
    timeout: float = 30.0
```

Env vars: `PASS_BUILDER_BASE_URL`, `PASS_BUILDER_TOKEN`, `PASS_BUILDER_TIMEOUT`.

## Authentication

- Static bearer token via `Authorization: Bearer <token>`. The token is issued
  out of band (server-side DB row in `api_client`); the client does not mint or
  refresh it. Missing/invalid token surfaces as `PassBuilderAuthError` (401);
  missing scope as `PassBuilderForbiddenError` (403).
- No token endpoint, no username/password (this is the key difference from
  `edutap.heidi_api`, which does OAuth2 password → JWT).

## Error handling

Decode RFC 9457 `problem+json` into a typed exception hierarchy:

```python
class PassBuilderError(Exception):            # base; carries ProblemDetail
class PassBuilderAuthError(PassBuilderError)      # 401
class PassBuilderForbiddenError(PassBuilderError) # 403 insufficient_scope
class PassBuilderNotFoundError(PassBuilderError)  # 404 (incl. foreign tenant)
class PassBuilderConflictError(PassBuilderError)  # 409
class PassBuilderValidationError(PassBuilderError) # 422
class PassBuilderServerError(PassBuilderError)    # 5xx

class ProblemDetail(BaseModel):
    type: str; title: str; status: int
    detail: str | None = None; instance: str | None = None
```

The optional `request_id` argument is sent as `x-request-id` for
server-side audit correlation.

## Tooling & CI

Follows the eduTAP/uv stack (same as `edutap.heidi_api`):

- **uv** for env/deps; editable install with `[dev]` extra.
- **ruff** (format + check, rule groups `E,F,W,I,D,S,B,UP`), **ty** typecheck
  (mypy `--strict` as CI fallback), **pytest** (+ `anyio`/`pytest-asyncio`).
- **tox** matrix over all supported Python versions. Match `edutap.heidi_api`:
  `requires-python = ">=3.12"`.
- **prek** hook runner.
- HTTP tests use `respx` / `httpx.MockTransport` — **no real network**.
- **Spec-drift test** (`tests/test_spec_drift.py`, marker `drift`): compares the
  client's request/response models against a vendored
  `tests/data/openapi.json`. Because the server ships no static spec, the
  snapshot is produced from the server's app factory (`make fetch-spec`:
  dump `/api/v1/openapi.json` from a locally instantiated
  `edutap.pass_builder` app) and committed. Drift → test fails → update client.
- **CI:** GitHub Actions (repo lives on GitHub `edutap-collective`), mirroring
  the local checks.
- **Docs:** Sphinx + MyST, Diátaxis.

## Repository

- New repo `edutap.pass_builder_api`, remote
  `git@github.com:edutap-collective/edutap.pass_builder_api.git`, default branch
  `main`.
- License EUPL 1.2 (consistent with the ecosystem).
- Later registered as a submodule under `uses_libraries/` in
  `lmu_edutap_dev_setup` and as a pip dependency of `lmu_edutap_backend`.

## Test strategy

1. **Model round-trips:** every request/response model serializes to the exact
   field names/casing the server expects (`wallet_type` lowercase, etc.).
2. **`create_pass` branching:** Apple path returns `ApplePassResult` with bytes
   + parsed `X-*` headers; Google path returns `GooglePassResponse` — both via
   `MockTransport`.
3. **`save_link`:** returns the JWT string; Apple `save_link` maps the
   server error to `PassBuilderError`.
4. **Error mapping:** each `problem+json` status maps to its exception type.
5. **Spec drift:** models match the vendored snapshot.

## Milestones

1. Scaffold repo (pyproject, tooling, CI, namespace package).
2. `models.py` + `settings.py` + `exceptions.py`.
3. `client.py` render methods + ops.
4. Tests (mock transport) + vendored spec snapshot + drift test.
5. Docs (README quickstart + Sphinx reference).
6. Tag `v0.1.0`; wire into `lmu_edutap_backend` as the `pass_builder` adapter.

## Open questions

1. **Union vs. explicit wallet methods** for `create_pass`/`update_pass`
   (`ApplePassResult | GooglePassResponse` vs.
   `create_apple_pass`/`create_google_pass`). Recommendation: provide both — a
   low-level union method and typed convenience wrappers.
2. **Vendored spec source:** confirm the `edutap.pass_builder` app factory can
   dump `/api/v1/openapi.json` headlessly for `make fetch-spec` (it can be
   imported without a live DB for OpenAPI generation — to verify).
3. ~~**Supported Python range**~~ — resolved: `>=3.12`, matching
   `edutap.heidi_api`.
4. **Token provisioning:** document how a `render`-scope token is created on the
   server (migration/seed/DB) — needed for integration tests and the backend.
