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
