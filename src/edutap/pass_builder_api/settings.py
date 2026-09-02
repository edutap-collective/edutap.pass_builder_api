"""Client configuration via pydantic-settings."""

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SECRETS_DIR = "/run/secrets"
"""Where an orchestrator mounts secrets.

The bearer token this client presents is the only thing standing in front of a
service that signs passes. Read from a file, it is never in the process
environment at all -- which means never in `docker inspect`, and never in a
frame local an error tracker collects.

Two things worth knowing, and both are the reason this is a line of code rather
than a line of deployment documentation:

* **pydantic-settings has no `_FILE` convention.** It reads a secret file only
  where a `secrets_dir` says to look. Without this setting a deployment can
  mount the token perfectly and the client will never see it -- and a client
  with no token sends none, which is indistinguishable from a deployment that
  has none.
* **The file name carries the `env_prefix`**: `/run/secrets/PASS_BUILDER_token`,
  not `.../token`. A secret under the bare field name is silently ignored.

  The case of the field half does not matter -- `PASS_BUILDER_TOKEN` is read
  just as well, because pydantic-settings matches case-insensitively unless
  `case_sensitive=True`. Measured against pydantic-settings 2.x rather than
  assumed. The lower-case spelling is used here and in the deployment because
  every sibling package spells it that way (`EDUTAP_DB_password`,
  `IMAGE_SERVICE_DB_password`), and one odd one out invites somebody to
  "correct" the others.

A missing directory is harmless: pydantic-settings warns and falls back to the
environment, so a development machine without `/run/secrets` is unaffected.
"""


class PassBuilderSettings(BaseSettings):
    """Pass Builder API client settings."""

    model_config = SettingsConfigDict(
        env_prefix="PASS_BUILDER_",
        env_file=".env",
        secrets_dir=SECRETS_DIR,
        extra="ignore",
    )

    base_url: HttpUrl = HttpUrl("http://localhost:8000")
    """The service's mount point, WITHOUT its business path.

    `client.API_PREFIX` ("/builder/v1") is appended by every call. The zone in
    front of it is a deployment concern:
    `https://traefik-internal:8090/internal-api/wallet`.
    """

    token: SecretStr | None = None
    timeout: float = 30.0
