import lettersign


def test_package_version_defined() -> None:
    assert isinstance(lettersign.__version__, str)
    parts = lettersign.__version__.split(".")
    assert len(parts) >= 2
