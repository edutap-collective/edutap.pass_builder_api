def test_package_imports_and_exposes_version():
    import edutap.pass_builder_api as pkg

    assert isinstance(pkg.__version__, str)
    assert pkg.__version__ != ""
