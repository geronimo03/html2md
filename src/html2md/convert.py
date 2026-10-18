from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, List, Tuple, Union
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from pyhtml2md import Converter, Options

from .cleaning import clean_html, decode_html, finalize_markdown

PathLike = Union[str, Path]
_HTTP_TIMEOUT = 30


def _is_http_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def _read_html_source(source: PathLike) -> bytes:
    source_text = os.fspath(source)
    parsed = urlsplit(source_text)

    if parsed.scheme.lower() in {"http", "https"}:
        if not parsed.netloc:
            raise ValueError(f"Invalid webpage URL: {source_text}")
        request = Request(source_text, headers={"User-Agent": "html2md/0.1.0"})
        with urlopen(request, timeout=_HTTP_TIMEOUT) as response:
            return response.read()

    html_path = Path(source_text)
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")
    return html_path.read_bytes()


def _iter_html_files(src_path: Path, recursive: bool = False) -> Iterable[Path]:
    search = src_path.rglob if recursive else src_path.glob
    yield from sorted(path for pattern in ("*.html", "*.htm") for path in search(pattern))


def convert_html_file(html_file: PathLike) -> str:
    """Read a local HTML file or HTTP(S) webpage and return its Markdown content."""
    html_content, blocks = clean_html(decode_html(_read_html_source(html_file)))

    options = Options()
    options.splitLines = False

    markdown = Converter(html_content, options).convert()
    return finalize_markdown(markdown, blocks)


def convert_file(src_file: PathLike, dest_file: PathLike) -> Path:
    """Convert a single HTML file into a Markdown file."""
    dest_path = Path(dest_file)

    markdown = convert_html_file(src_file)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_path.with_name(dest_path.name + ".tmp")
    tmp_path.write_text(markdown, encoding="utf-8")
    os.replace(tmp_path, dest_path)
    return dest_path


ConvertResult = Tuple[List[Path], List[Tuple[Path, Exception]]]


def convert_dir(
    src_dir: PathLike, dest_dir: PathLike, recursive: bool = False, workers: int = 1
) -> ConvertResult:
    """Convert every HTML file in a directory; per-file failures are collected, not raised."""
    src_path = Path(src_dir)
    dest_path = Path(dest_dir)

    if not src_path.exists():
        raise FileNotFoundError(f"Source directory not found: {src_path}")

    dest_path.mkdir(parents=True, exist_ok=True)
    jobs = [
        (src_file, dest_path / src_file.relative_to(src_path).with_suffix(".md"))
        for src_file in _iter_html_files(src_path, recursive=recursive)
    ]

    converted: List[Path] = []
    failed: List[Tuple[Path, Exception]] = []

    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(convert_file, src, dest): src for src, dest in jobs}
            for future in as_completed(futures):
                try:
                    converted.append(future.result())
                except Exception as exc:
                    failed.append((futures[future], exc))
        converted.sort()
    else:
        for src, dest in jobs:
            print(f"Converting {src} -> {dest}")
            try:
                converted.append(convert_file(src, dest))
            except Exception as exc:
                failed.append((src, exc))

    return converted, failed
