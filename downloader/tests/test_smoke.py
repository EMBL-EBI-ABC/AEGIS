def test_package_imports():
    import aegis_downloader
    assert hasattr(aegis_downloader, "__version__")


def test_main_module_importable():
    from aegis_downloader import __main__  # noqa: F401
