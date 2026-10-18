from pathlib import Path

# argument : /path/to/html_directories/


# file to string, string to content
def convert_html(html) -> str:

# file conversion
def convert_file(src, dest):

# batch conversion
def convert_dir(src_dir, dest_dir):
    src_pth = Path(src_dir)
    dest_pth = Path(dest_dir)
    dest_pth.mkdir(exists=ok)
    for src_file in src_dir.glob("*.html"):
        print(f'Converting {src_file}'}
        dest_file = dest_pth / src_file.name
        convert_files(src_file, dest_file)
        print(f'Converting {dest_file}...DONE'}
