from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence
from urllib.parse import unquote, urlsplit

from .convert import _is_http_url, convert_dir, convert_file


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Convert HTML files to Markdown.")
    parser.add_argument("src", help="Source HTML file or directory")
    parser.add_argument("dest", nargs="?", default="results", help="Destination Markdown file or directory")
    parser.add_argument("--recursive", action="store_true", help="Recursively search subdirectories for HTML files")
    parser.add_argument("--workers", type=int, default=1, help="Parallel processes for directory conversion")
    args = parser.parse_args(argv)

    src_path = Path(args.src)
    dest_path = Path(args.dest)

    if _is_http_url(args.src):
        url_path = unquote(urlsplit(args.src).path).rstrip("/")
        filename = Path(url_path).name or "index"
        if dest_path.is_dir() or dest_path.suffix == "":
            dest_path = dest_path / f"{Path(filename).stem}.md"
        convert_file(args.src, dest_path)
        return 0

    if src_path.is_file():
        if dest_path.is_dir() or dest_path.suffix == "":
            dest_path = dest_path / f"{src_path.stem}.md"
        convert_file(src_path, dest_path)
        return 0

    if not src_path.is_dir():
        parser.error(f"Path does not exist: {src_path}")

    _, failed = convert_dir(src_path, dest_path, recursive=args.recursive, workers=args.workers)
    for path, exc in failed:
        print(f"FAILED {path}: {exc}", file=sys.stderr)
    return 1 if failed else 0
