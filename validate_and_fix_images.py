#!/usr/bin/env python3
"""Validate product image URLs and try alternate sources when broken.

Usage:
  .venv/bin/python validate_and_fix_images.py

What it does:
- Loads `products.json` and `rebrickable_cache.json`.
- For each product with an `imageUrl`, performs a lightweight GET (stream) to verify the URL returns an image (HTTP 200 and image/* content-type).
- If URL is broken, tries (in order): Rebrickable set endpoint, Rebrickable search, Brickset page, Bricklink page to find an image.
- If a replacement image is found, updates both cache and `products.json`.
- If none found, replaces `imageUrl` with a placeholder image URL.

This is conservative and throttled to avoid rate-limits. It writes backups before modifying files.
"""
import json
import time
import re
from pathlib import Path
import sys
try:
    import requests
except Exception:
    print('requests required: .venv/bin/python -m pip install requests')
    raise

HERE = Path(__file__).resolve().parent
PROD = HERE / 'products.json'
CACHE = HERE / 'rebrickable_cache.json'
API_KEY = '10d0ebdfd8363511ead159b19b0e978f'
PLACEHOLDER = 'https://via.placeholder.com/300x150?text=No+Image'

def is_image_url_ok(url, session):
    try:
        r = session.get(url, stream=True, timeout=10)
        ct = r.headers.get('content-type','')
        ok = (r.status_code == 200) and ct.startswith('image')
        r.close()
        return ok
    except Exception:
        return False

def try_rebrickable_for_set(setid, session):
    # try set endpoint with setid and setid-1
    for s in (setid, setid + '-1'):
        url = f'https://rebrickable.com/api/v3/lego/sets/{s}/'
        try:
            r = session.get(url, headers={'Authorization':f'key {API_KEY}'}, timeout=10)
        except Exception:
            r = None
        if r and r.status_code == 200:
            data = r.json()
            img = data.get('set_img_url') or data.get('set_img') or data.get('set_img_url_preview') or data.get('set_img_url_full') or None
            if img:
                return img
    return None

def try_rebrickable_search(setid, session):
    url = f'https://rebrickable.com/api/v3/lego/sets/?search={setid}'
    try:
        r = session.get(url, headers={'Authorization':f'key {API_KEY}'}, timeout=10)
    except Exception:
        return None
    if r.status_code == 200:
        data = r.json()
        for res in data.get('results', []):
            img = res.get('set_img_url') or res.get('set_img') or None
            if img:
                return img
    return None

def try_brickset(setid, session):
    url = f'https://brickset.com/sets/{setid}'
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            m = re.search(r'<meta property="og:image" content="([^"]+)"', r.text)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None

def try_bricklink(setid, session):
    for u in (f'https://www.bricklink.com/v2/catalog/catalogitem.page?S={setid}', f'https://www.bricklink.com/v2/catalog/catalogitem.page?S={setid}-1'):
        try:
            r = session.get(u, timeout=10)
            if r.status_code == 200:
                m = re.search(r'<meta property="og:image" content="([^"]+)"', r.text)
                if m:
                    return m.group(1)
        except Exception:
            pass
    return None

def main():
    if not PROD.exists():
        print('products.json not found')
        sys.exit(1)
    prods = json.loads(PROD.read_text(encoding='utf-8'))
    cache = json.loads(CACHE.read_text(encoding='utf-8')) if CACHE.exists() else {}

    # backup
    PROD.with_suffix('.backup.json').write_text(json.dumps(prods, indent=2, ensure_ascii=False), encoding='utf-8')
    CACHE.with_suffix('.backup.json').write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding='utf-8')

    session = requests.Session()
    updated = 0
    total = 0
    for prod in prods:
        total += 1
        img = prod.get('imageUrl')
        if not img:
            # attempt to find one
            sid = str(prod.get('id',''))
            found = try_rebrickable_for_set(sid, session) or try_rebrickable_search(sid, session) or try_brickset(sid, session) or try_bricklink(sid, session)
            if found:
                prod['imageUrl'] = found
                cache.setdefault(sid, {})['image_url'] = found
                updated += 1
            else:
                prod['imageUrl'] = PLACEHOLDER
                updated += 1
            time.sleep(0.5)
            continue

        # validate existing URL
        ok = is_image_url_ok(img, session)
        if ok:
            continue
        # try to find replacement
        sid = str(prod.get('id',''))
        found = try_rebrickable_for_set(sid, session) or try_rebrickable_search(sid, session) or try_brickset(sid, session) or try_bricklink(sid, session)
        if found:
            prod['imageUrl'] = found
            cache.setdefault(sid, {})['image_url'] = found
            updated += 1
        else:
            prod['imageUrl'] = PLACEHOLDER
            updated += 1
        time.sleep(0.5)

    # write back
    PROD.write_text(json.dumps(prods, indent=2, ensure_ascii=False), encoding='utf-8')
    CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f'Validated {total} products, updated {updated} image entries (replacements or placeholders).')

if __name__ == '__main__':
    main()
