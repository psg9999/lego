#!/usr/bin/env python3
"""Refresh rebrickable_cache.json for all unique set numbers.

Usage:
  .venv/bin/python refresh_cache.py [--update-products]

Options:
  --update-products  Persist refreshed image_url into products.json (overwrites products.json after backing up)

This script iterates unique set ids in products.json and calls the Rebrickable set endpoint to refresh name, set_num_found, and image_url in the cache.
"""
import json, time, sys
from pathlib import Path
try:
    import requests
except Exception:
    print('requests required: .venv/bin/python -m pip install requests')
    raise

HERE = Path(__file__).resolve().parent
PROD = HERE / 'products.json'
CACHE = HERE / 'rebrickable_cache.json'
API_KEY = '10d0ebdfd8363511ead159b19b0e978f'

def refresh_one(setnum, session):
    url = f'https://rebrickable.com/api/v3/lego/sets/{setnum}/'
    try:
        r = session.get(url, headers={'Authorization':f'key {API_KEY}'}, timeout=10)
    except Exception:
        return None
    if r.status_code == 200:
        d = r.json()
        name = d.get('name')
        img = d.get('set_img_url') or d.get('set_img') or None
        # set_num_found may be same as setnum or include -1, use returned set_num if present
        sfn = d.get('set_num') or setnum
        return {'name': name, 'image_url': img, 'set_num_found': sfn, 'fetched': int(time.time())}
    return None

def main():
    update_products = '--update-products' in sys.argv
    if not PROD.exists():
        print('products.json not found')
        sys.exit(1)
    prods = json.loads(PROD.read_text(encoding='utf-8'))
    cache = json.loads(CACHE.read_text(encoding='utf-8')) if CACHE.exists() else {}

    # gather unique set ids
    seen = set()
    unique = []
    for p in prods:
        sid = str(p.get('id','')).strip()
        if sid and sid not in seen:
            seen.add(sid); unique.append(sid)

    print(f'Refreshing {len(unique)} unique set ids')
    session = requests.Session()
    updated = 0
    for i,s in enumerate(unique, start=1):
        try:
            info = refresh_one(s, session)
        except Exception:
            info = None
        if info:
            cache[s] = info
            updated += 1
        if i % 40 == 0:
            print(f'Progress: {i}/{len(unique)}')
        time.sleep(0.7)

    # backup
    CACHE.with_suffix('.backup.json').write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding='utf-8')

    CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Refreshed cache entries: {updated}')

    if update_products:
        # backup products
        PROD.with_suffix('.backup.json').write_text(json.dumps(prods, indent=2, ensure_ascii=False), encoding='utf-8')
        # apply image_url into products
        changed = 0
        for p in prods:
            sid = str(p.get('id','')).strip()
            info = cache.get(sid, {})
            img = info.get('image_url')
            if not img and info.get('set_num_found'):
                setnum = info.get('set_num_found')
                prefix = setnum.split('-')[0][:3]
                img = f'https://cdn.rebrickable.com/media/sets/{prefix}/{setnum}.jpg'
            if img and p.get('imageUrl') != img:
                p['imageUrl'] = img; changed += 1
        if changed:
            PROD.write_text(json.dumps(prods, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'Updated products.json with imageUrl for {changed} items')

if __name__ == '__main__':
    main()
