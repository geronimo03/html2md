# html2md

A lightweight utility for converting HTML files into Markdown.

## Features

- convert a single HTML file to Markdown
- convert every HTML file in a directory
- optionally recurse into subdirectories
- works as a CLI script or Python API

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
convert_dir("pages", "markdown", recursive=True)
```

### Command line

```bash
python3 main.py input.html output.md
python3 main.py input_dir output_dir
python3 main.py input_dir output_dir --recursive
```

## Example

```bash
printf '<h1>Hello</h1><p>World</p>' > sample.html
python3 main.py sample.html sample.md
cat sample.md
```

Result:

```md
# Hello

World
```
