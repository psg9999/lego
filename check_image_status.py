#!/usr/bin/env python3
"""Check that every product.imageUrl responds 200 and write a failures report.

Writes `image_check_report.json` with a list of failures.
"""
import json, sys
from pathlib import Path
try:
    import requests
except Exception:
    print('requests required: .venv/bin/python -m pip install requests')
    raise

HERE = Path(__file__).resolve().parent
PROD = HERE / 'products.json'
OUT = HERE / 'image_check_report.json'

def check_url(session, url):
    if not url:
        return False, 'empty'
    try:
        r = session.head(url, allow_redirects=True, timeout=8)
        if r.status_code == 200 and 'image' in (r.headers.get('Content-Type','')):
            return True, r.status_code
        # some servers block HEAD; try GET
        r = session.get(url, stream=True, timeout=10)
        ok = (r.status_code == 200 and 'image' in (r.headers.get('Content-Type','')))
        return ok, r.status_code
    except Exception as e:
        return False, str(e)

def main():
    if not PROD.exists():
        print('products.json not found'); sys.exit(1)
    prods = json.loads(PROD.read_text(encoding='utf-8'))
    session = requests.Session()
    # use a common browser User-Agent to avoid basic blocks/403s
    session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36'})
    failures = []
    total = len(prods)
    ok_count = 0
    for i,p in enumerate(prods, start=1):
        url = p.get('imageUrl')
        ok, info = check_url(session, url)
        if ok:
            ok_count += 1
        else:
            failures.append({'id': p.get('id'), 'title': p.get('title'), 'imageUrl': url, 'reason': info})
        if i % 100 == 0:
            print(f'Checked {i}/{total}...')

    report = {'total': total, 'ok': ok_count, 'failures': failures}
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Done. OK: {ok_count}/{total}. Failures: {len(failures)}. Report -> {OUT}")

if __name__ == '__main__':
    main()
