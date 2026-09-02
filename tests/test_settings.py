from edutap.pass_builder_api.settings import SECRETS_DIR, PassBuilderSettings


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
    assert settings.token is not None
    assert settings.token.get_secret_value() == "secret-token"


def test_a_secrets_dir_is_declared():
    """The token can arrive as a file, so it stays out of the environment.

    This asserts the *declaration*, not the behaviour, and that is the point:
    without a `secrets_dir` there is no file that is read wrongly -- only one
    that is never read. A client with no token sends none, which looks exactly
    like a deployment that has none, and the mistake surfaces as a 401 far from
    its cause.

    pydantic-settings has no `_FILE` convention, and the file name it looks for
    carries the prefix: `/run/secrets/PASS_BUILDER_token`. The case of the
    field half does not matter -- see `test_the_file_name_is_matched_case_insensitively`.
    """
    assert PassBuilderSettings.model_config["secrets_dir"] == SECRETS_DIR


def test_a_mounted_token_is_read(tmp_path, monkeypatch):
    """And the behaviour, once, so the file name is pinned down too."""
    monkeypatch.delenv("PASS_BUILDER_TOKEN", raising=False)
    (tmp_path / "PASS_BUILDER_token").write_text("from-a-file\n")

    settings = PassBuilderSettings(_env_file=None, _secrets_dir=str(tmp_path))

    assert settings.token is not None
    assert settings.token.get_secret_value() == "from-a-file"


def test_the_file_name_is_matched_case_insensitively(tmp_path):
    """`PASS_BUILDER_TOKEN` is read as readily as `PASS_BUILDER_token`.

    Measured, because it was asked: pydantic-settings matches
    case-insensitively unless `case_sensitive=True`, so neither spelling is a
    deployment risk. What IS a risk is the prefix -- a file under the bare
    field name is ignored in every case, which the test above pins down.
    """
    (tmp_path / "PASS_BUILDER_TOKEN").write_text("upper-case-file\n")

    settings = PassBuilderSettings(_env_file=None, _secrets_dir=str(tmp_path))

    assert settings.token is not None
    assert settings.token.get_secret_value() == "upper-case-file"
