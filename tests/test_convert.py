import html2md
from html2md import convert_dir, convert_file, convert_html_file


def test_package_exposes_public_api():
    for name in ("convert_html_file", "convert_file", "convert_dir", "main"):
        assert callable(getattr(html2md, name))


def test_convert_html_file_turns_basic_html_into_markdown(tmp_path):
    source = tmp_path / "sample.html"
    source.write_text("<h1>Hello</h1><p>World</p>", encoding="utf-8")

    result = convert_html_file(source)

    assert "Hello" in result
    assert "World" in result


def test_convert_file_writes_output(tmp_path):
    src = tmp_path / "input.html"
    dst = tmp_path / "output.md"
    src.write_text("<h2>Title</h2>", encoding="utf-8")

    convert_file(src, dst)

    assert "Title" in dst.read_text(encoding="utf-8")
    assert not (tmp_path / "output.md.tmp").exists()


def test_convert_dir_continues_after_a_failing_file(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "good.html").write_text("<h1>Good</h1>", encoding="utf-8")
    (src / "page.html.backup.html").write_text("<h1>Backup</h1>", encoding="utf-8")
    (src / "bad.html").mkdir()

    converted, failed = convert_dir(src, dest)

    assert (dest / "good.md").exists()
    assert (dest / "page.html.backup.md").exists()
    assert [path.name for path, _ in failed] == ["bad.html"]
    assert len(converted) == 2
