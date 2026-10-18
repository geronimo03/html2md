import pytest

from html2md import convert_html_file


@pytest.fixture
def convert(tmp_path):
    def _convert(html: str) -> str:
        src = tmp_path / "input.html"
        src.write_text(html, encoding="utf-8")
        return convert_html_file(src)

    return _convert
