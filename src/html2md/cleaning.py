from __future__ import annotations

import re
from html import escape as _escape
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup, Comment

_ZERO_WIDTH = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff\U000e0000-\U000e007f]")
_HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0(?![.\d])", re.I)
_EXTRA_SPACES = re.compile(r"(?<=\S)[ \t]{2,}")

_DROP_TAGS = ["script", "style", "noscript", "iframe", "svg", "template", "link", "meta"]
_DROP_SELECTORS = [
    ".navbox",
    ".toc",
    "#toc",
    ".mw-editsection",
    ".sidebar",
    "#mw-navigation",
    "#left-navigation",
    "#p-navigation",
    "#p-personal",
]
_BOILERPLATE = ["nav", "footer", "aside", "header"]
_TABLE_PARTS = ["thead", "tbody", "tfoot", "tr", "td", "th", "caption"]
_MAX_SPAN = 100


def decode_html(raw: bytes) -> str:
    """Decode as UTF-8, dropping invalid bytes and turning NBSP into a plain space."""
    text = raw.decode("utf-8", errors="replace")
    return text.replace("\ufffd", "").replace("\u00a0", " ")


def _is_noise_image(img) -> bool:
    src = img.get("src") or ""
    tiny = any(str(img.get(attr, "")).strip() in {"0", "1"} for attr in ("width", "height"))
    return tiny or src.startswith("data:") or not (img.get("alt") or "").strip()


def _strip_noise(soup: BeautifulSoup) -> None:
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()

    for tag in soup(_DROP_TAGS):
        if not tag.decomposed:
            tag.decompose()

    for selector in _DROP_SELECTORS:
        for tag in soup.select(selector):
            if not tag.decomposed:
                tag.decompose()

    for tag in soup.find_all(True):
        if tag.decomposed:
            continue
        hidden = tag.has_attr("hidden") or tag.get("aria-hidden") == "true"
        if hidden or _HIDDEN_STYLE.search(tag.get("style") or ""):
            tag.decompose()
        elif tag.name == "img" and _is_noise_image(tag):
            tag.decompose()

    for tag in soup.find_all("a"):
        if not tag.decomposed and not tag.get_text(strip=True) and tag.find("img") is None:
            tag.decompose()

    for tag in soup(_BOILERPLATE):
        if tag.decomposed or tag.find_parent(["article", "main"]) is not None:
            continue
        if tag.name == "header" and tag.find(["h1", "h2"]) is not None:
            continue
        tag.decompose()


def _select_roots(soup: BeautifulSoup) -> list:
    roots = soup.select("main") or soup.select("article") or [soup.body or soup]
    ids = {id(root) for root in roots}
    return [root for root in roots if not any(id(parent) in ids for parent in root.parents)]


def _span(cell, name: str) -> int:
    try:
        return max(1, min(int(cell.get(name, 1)), _MAX_SPAN))
    except ValueError:
        return 1


def _table_to_markdown(table) -> str:
    grid: Dict[Tuple[int, int], str] = {}
    for r, tr in enumerate(table.find_all("tr")):
        c = 0
        for cell in tr.find_all(["th", "td"], recursive=False):
            while (r, c) in grid:
                c += 1
            rowspan, colspan = _span(cell, "rowspan"), _span(cell, "colspan")
            text = " ".join(cell.get_text(" ", strip=True).split()).replace("|", "\\|")
            for dr in range(rowspan):
                for dc in range(colspan):
                    grid[(r + dr, c + dc)] = text if (dr, dc) == (0, 0) else ""
            c += colspan

    if not grid:
        return ""

    height = 1 + max(r for r, _ in grid)
    width = 1 + max(c for _, c in grid)
    lines = ["| " + " | ".join(grid.get((r, c), "") for c in range(width)) + " |" for r in range(height)]
    lines.insert(1, "|" + " --- |" * width)
    return "\n".join(lines)


def _code_to_markdown(pre) -> str:
    code = pre.find("code") or pre
    classes = list(code.get("class") or []) + list(pre.get("class") or [])
    lang = next((c.split("-", 1)[1] for c in classes if c.startswith(("language-", "lang-"))), "")
    text = code.get_text().strip("\n")
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}{lang}\n{text}\n{fence}"


def _unwrap_layout_table(table) -> None:
    for part in table.find_all(_TABLE_PARTS):
        if part.find_parent("table") is table:
            part.name = "div"
    table.name = "div"


def _protect_blocks(soup: BeautifulSoup, root, blocks: Dict[str, str]) -> None:
    for tag in root.find_all(["table", "pre"]):
        if not any(parent is root for parent in tag.parents):
            continue  # already replaced together with an enclosing block

        if tag.name == "table":
            if tag.get("role") == "presentation" or tag.find("table") is not None:
                _unwrap_layout_table(tag)
                continue
            markdown = _table_to_markdown(tag)
        else:
            markdown = _code_to_markdown(tag)

        if not markdown:
            tag.decompose()
            continue

        token = f"HTML2MDBLOCK{len(blocks)}X"
        blocks[token] = markdown
        placeholder = soup.new_tag("p")
        placeholder.string = token
        tag.replace_with(placeholder)


def _render(soup: BeautifulSoup, roots: List) -> str:
    body = "".join(str(root) for root in roots)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if title and not any(root.find("h1") is not None for root in roots):
        body = f"<h1>{_escape(title)}</h1>{body}"
    return body


def clean_html(html_text: str) -> Tuple[str, Dict[str, str]]:
    """Return noise-free HTML plus tables and code blocks to restore after conversion."""
    soup = BeautifulSoup(html_text, "lxml")
    _strip_noise(soup)
    roots = _select_roots(soup)

    blocks: Dict[str, str] = {}
    for root in roots:
        _protect_blocks(soup, root, blocks)

    cleaned = _render(soup, roots)
    soup.decompose()
    return cleaned, blocks


def finalize_markdown(markdown: str, blocks: Dict[str, str]) -> str:
    markdown = _EXTRA_SPACES.sub(" ", markdown.replace("\u00a0", " "))
    for token, block in blocks.items():
        markdown = markdown.replace(token, block)
    return _ZERO_WIDTH.sub("", markdown)
