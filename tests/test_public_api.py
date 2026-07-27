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
