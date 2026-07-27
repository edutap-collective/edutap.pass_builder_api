"""Dump the edutap.pass_builder OpenAPI spec into tests/data/openapi.json.

Requires `edutap.pass_builder` importable in the same environment. OpenAPI
generation does not need a live database.
"""

import json
from pathlib import Path


def main() -> None:
    """Generate the OpenAPI spec and write it to the vendored snapshot file."""
    from edutap.pass_builder.app import create_app

    app = create_app()
    spec = app.openapi()
    out = Path(__file__).parent.parent / "tests" / "data" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, indent=2, sort_keys=True))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
