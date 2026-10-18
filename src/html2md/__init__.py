from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence, Union

from pyhtml2md import Converter, Options

PathLike = Union[str, Path]


def _iter_html_files(src_path: Path, recursive: bool = False) -> Iterable[Path]:
    if recursive:
        yield from sorted(src_path.rglob("*.html"))
    else:
        yield from sorted(src_path.glob("*.html"))


def convert_html_file(html_file: PathLike) -> str:
    """Read an HTML file and return its Markdown content."""
    html_path = Path(html_file)
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    html_content = html_path.read_text(encoding="utf-8")
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
    parser.add_argument("dest", help="Destination Markdown file or directory")
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

__all__ = ["convert_html", "convert_html_file", "convert_file", "convert_dir", "main"]
