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
