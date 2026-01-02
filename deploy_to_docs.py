#!/usr/bin/env python3
"""Copy web app files into `docs/` for GitHub Pages hosting.

Run: python3 deploy_to_docs.py

It will create a `docs/` directory, copy the important site files, write `.nojekyll`, and show a list of files copied.
"""
import shutil
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
DOCS = HERE / 'docs'

# Files and folders to copy if present
TO_COPY = [
    'index.html', 'styles.css', 'app.js', 'products.json', 'products_with_names.json',
    'rebrickable_cache.json', 'placeholder.svg', 'README.md'
]

def main():
    DOCS.mkdir(exist_ok=True)
    copied = []
    for name in TO_COPY:
        src = HERE / name
        if src.exists():
            dst = DOCS / name
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            copied.append(name)

    # Prevent Jekyll processing
    (DOCS / '.nojekyll').write_text('')

    if copied:
        print('Copied files to docs/:')
        for c in copied:
            print(' -', c)
        print('\nNext step: commit and push to GitHub. See README_GH_PAGES.md for commands.')
    else:
        print('No files found to copy. Check that your site files (index.html, app.js, etc.) are in the project root.')

if __name__ == '__main__':
    main()
