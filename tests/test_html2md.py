from pathlib import Path

import pytest


def test_package_exposes_conversion_functions():
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    from html2md import convert_html_file, convert_file, convert_dir

    assert callable(convert_html_file)
    assert callable(convert_file)
    assert callable(convert_dir)


def test_convert_html_file_turns_basic_html_into_markdown(tmp_path):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    from html2md import convert_html_file

    source = tmp_path / "sample.html"
    source.write_text("<h1>Hello</h1><p>World</p>", encoding="utf-8")

    result = convert_html_file(source)

    assert "Hello" in result
    assert "World" in result


def test_convert_file_writes_output(tmp_path):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    from html2md import convert_file

    src = tmp_path / "input.html"
    dst = tmp_path / "output.md"
    src.write_text("<h2>Title</h2>", encoding="utf-8")

    convert_file(src, dst)

    assert dst.exists()
    assert "Title" in dst.read_text(encoding="utf-8")


def test_convert_html_file_handles_non_utf8_html(tmp_path):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    from html2md import convert_html_file

    src = tmp_path / "input.html"
    src.write_bytes("<h1>Café</h1>".encode("cp1252"))

    result = convert_html_file(src)

    assert "Café" in result


def test_convert_html_file_ignores_invalid_utf8_bytes(tmp_path):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    from html2md import convert_html_file

    src = tmp_path / "input.html"
    src.write_bytes(b"<h1>Bad \xc2 bytes</h1>")

    result = convert_html_file(src)

    assert "Bad" in result
    assert "bytes" in result

def test_convert_html_file_removes_script_and_style_noise(tmp_path):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    from html2md import convert_html_file

    src = tmp_path / "input.html"
    src.write_text(
        """
        <html><head><style>body { color: red; }</style></head>
        <body>
          <script>var x = 1;</script>
          <nav>Menu</nav>
          <main>
            <h1>Title</h1>
            <a href="https://example.com">Example</a>
          </main>
        </body></html>
        """,
        encoding="utf-8",
    )

    result = convert_html_file(src)

    assert "Title" in result
    assert "Example" in result
    assert "https://example.com" in result
    assert "var x" not in result
    assert "color: red" not in result
