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

`PASS_BUILDER_BASE_URL` is the service's mount point **without** its business
path: `client.API_PREFIX` (`/builder/v1`) is appended by every call, so a
deployment behind a gateway sets
`https://traefik-internal:8090/internal-api/wallet`.

The token may also arrive as a mounted file. `PassBuilderSettings` declares
`secrets_dir=/run/secrets`, and pydantic-settings looks for the field name with
the prefix in front of it — `/run/secrets/PASS_BUILDER_token`, never
`.../token`, and there is no `_FILE` convention. A token mounted under the wrong
name is silently ignored, and a client with no token sends none: the mistake
then shows up as a `401` far from its cause.

The case of the field half is not load-bearing — `PASS_BUILDER_TOKEN` is read
just as well, pydantic-settings matching case-insensitively by default. The
lower-case spelling is what the rest of the estate uses.
