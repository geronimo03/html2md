# html2md

A lightweight utility for converting HTML files into Markdown.

## Features

- convert a single HTML file to Markdown
- convert every HTML file in a directory
- optionally recurse into subdirectories
- works as a CLI or Python API
- removes scripts, styles, navigation, hidden content and tracking pixels while keeping links, tables and code blocks

## Installation

```bash
python3 -m pip install -e .
```

## Usage

### Python API

```python
from html2md import convert_html_file, convert_file, convert_dir

markdown = convert_html_file("example.html")
convert_file("example.html", "example.md")
converted, failed = convert_dir("pages", "markdown", recursive=True)  # failures are collected, not raised
```

### Command line

```bash
html2md input.html output.md
html2md input_dir output_dir
html2md input_dir output_dir --recursive --workers 4
```

## Example

```bash
printf '<h1>Hello</h1><p>World</p>' > sample.html
html2md sample.html sample.md
cat sample.md
```

Result:

```md
# Hello

World
```
