from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence, Union

from bs4 import BeautifulSoup, UnicodeDammit
from pyhtml2md import Converter, Options

PathLike = Union[str, Path]


def _iter_html_files(src_path: Path, recursive: bool = False) -> Iterable[Path]:
    if recursive:
        yield from sorted(src_path.rglob("*.html"))
    else:
        yield from sorted(src_path.glob("*.html"))


def sanitize_html_file(html_file: PathLike) -> Path:
    """Replace malformed UTF-8 byte markers with spaces in an HTML file."""
    html_path = Path(html_file)
    raw_bytes = html_path.read_bytes()
    cleaned = raw_bytes.replace(b"\xc2\xa0", b" ").replace(b"\xc2", b" ").replace(b"\xa0", b" ")
    html_path.write_bytes(cleaned)
    return html_path


def sanitize_html_dir(src_dir: PathLike, recursive: bool = False) -> list[Path]:
    """Sanitize every HTML file in a directory."""
    src_path = Path(src_dir)
    if not src_path.exists():
        raise FileNotFoundError(f"Source directory not found: {src_path}")

    sanitized_files: list[Path] = []
    for html_file in _iter_html_files(src_path, recursive=recursive):
        sanitized_files.append(sanitize_html_file(html_file))
    return sanitized_files


def _decode_html_bytes(raw_bytes: bytes) -> str:
    """Decode HTML bytes while removing malformed UTF-8 sequences."""
    cleaned = raw_bytes.replace(b"\xc2\xa0", b" ").replace(b"\xc2", b" ").replace(b"\xa0", b" ")

    for encoding in ("utf-8", "cp1252", "latin-1", "cp949", "euc-kr"):
        try:
            return cleaned.decode(encoding)
        except UnicodeDecodeError:
            continue

    detected = UnicodeDammit(cleaned).unicode_markup
    if detected is not None:
        return detected

    return cleaned.decode("utf-8", errors="ignore")


def _strip_html_noise(html: str) -> str:
    """Remove script/style/navigation boilerplate while preserving meaningful content and links."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "iframe", "svg", "template"]):
        tag.decompose()

    for selector in [
        "nav",
        "header",
        "footer",
        "aside",
        ".toc",
        ".sidebar",
        "#mw-navigation",
        "#left-navigation",
        "#p-navigation",
        "#p-personal",
        ".navbox",
        ".page-header",
    ]:
        for element in soup.select(selector):
            element.decompose()

    main = (
        soup.select_one("article")
        or soup.select_one("main")
        or soup.select_one(".mw-body-content")
        or soup.select_one("#content")
        or soup
    )
    return str(main)


def convert_html_file(html_file: PathLike) -> str:
    """Read an HTML file and return its Markdown content."""
    html_path = Path(html_file)
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    raw_bytes = html_path.read_bytes()
    html_content = _decode_html_bytes(raw_bytes)
    html_content = _strip_html_noise(html_content)

    options = Options()
    options.splitLines = False

    converter = Converter(html_content, options)
    return converter.convert()


def convert_file(src_file: PathLike, dest_file: PathLike) -> Path:
    """Convert a single HTML file into a Markdown file."""
    src_path = Path(src_file)
    dest_path = Path(dest_file)

    markdown = convert_html_file(src_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(markdown, encoding="utf-8")
    return dest_path


def convert_dir(src_dir: PathLike, dest_dir: PathLike, recursive: bool = False) -> list[Path]:
    """Convert every HTML file in a directory into Markdown files."""
    src_path = Path(src_dir)
    dest_path = Path(dest_dir)

    if not src_path.exists():
        raise FileNotFoundError(f"Source directory not found: {src_path}")

    dest_path.mkdir(parents=True, exist_ok=True)
    converted_files: list[Path] = []

    for src_file in _iter_html_files(src_path, recursive=recursive):
        relative_name = src_file.relative_to(src_path)
        if recursive:
            output_file = dest_path / relative_name.parent / relative_name.name.replace(".html", ".md")
            output_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_file = dest_path / src_file.name.replace(".html", ".md")

        print(f"Converting {src_file} -> {output_file}")
        converted_files.append(convert_file(src_file, output_file))

    return converted_files


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Convert HTML files to Markdown.")
    parser.add_argument("src", help="Source HTML file or directory")
    parser.add_argument("dest", help="Destination Markdown file or directory", default="results")
    parser.add_argument("--recursive", action="store_true", help="Recursively search subdirectories for HTML files")
    args = parser.parse_args(argv)

    src_path = Path(args.src)
    dest_path = Path(args.dest)

    if src_path.is_file():
        if dest_path.exists() and dest_path.is_dir():
            final_dest = dest_path / f"{src_path.stem}.md"
        else:
            final_dest = dest_path
        convert_file(src_path, final_dest)
    elif src_path.is_dir():
        convert_dir(src_path, dest_path, recursive=args.recursive)
    else:
        parser.error(f"Path does not exist: {src_path}")

    return 0


convert_html = convert_html_file

__all__ = [
    "convert_html",
    "convert_html_file",
    "convert_file",
    "convert_dir",
    "sanitize_html_file",
    "sanitize_html_dir",
    "main",
]
