from html2md import main


def test_webpage_url_writes_to_results_using_url_filename(tmp_path, monkeypatch):
    from io import BytesIO

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "html2md.convert.urlopen",
        lambda request, timeout: BytesIO(b"<h1>Online</h1>"),
    )

    assert main(["https://example.com/articles/page.html"]) == 0
    assert "Online" in (tmp_path / "results" / "page.md").read_text(encoding="utf-8")


def test_single_file_into_an_existing_directory_uses_the_file_stem(tmp_path):
    src = tmp_path / "page.html"
    src.write_text("<h1>Hi</h1>", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    assert main([str(src), str(out)]) == 0
    assert "Hi" in (out / "page.md").read_text(encoding="utf-8")


def test_directory_run_returns_nonzero_and_reports_failures(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    (src / "good.html").write_text("<h1>Good</h1>", encoding="utf-8")
    (src / "bad.html").mkdir()

    code = main([str(src), str(tmp_path / "out")])

    assert code == 1
    assert "FAILED" in capsys.readouterr().err
    assert (tmp_path / "out" / "good.md").exists()


def test_dest_defaults_to_results_in_the_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.html").write_text("<h1>A</h1>", encoding="utf-8")

    assert main([str(tmp_path / "a.html")]) == 0
    assert (tmp_path / "results" / "a.md").exists()
