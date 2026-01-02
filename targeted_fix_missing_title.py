#!/usr/bin/env python3
"""Targeted fix: lookup missing product title(s) via Rebrickable and persist to cache/products.

This script looks for products in `products.json` with empty or placeholder titles
and tries to enrich them by calling the same refresh logic used in `refresh_cache.py`.
It backs up `products.json` and `rebrickable_cache.json` before writing changes.

Usage: python3 targeted_fix_missing_title.py
"""
import json
import sys
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
PROD = HERE / 'products.json'
CACHE = HERE / 'rebrickable_cache.json'

def load_json(p):
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding='utf-8'))

def save_json(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')

def find_missing_title_products(prods):
    missing = []
    for p in prods:
        t = p.get('title')
        if t is None or str(t).strip() == '' or str(t).strip() == str(p.get('id')).strip():
            missing.append(p)
    return missing

def apply_info_to_product(p, info):
    # info: dict with name, image_url, set_num_found, fetched
    if not info:
        return p
    newp = dict(p)
    name = info.get('name')
    if name:
        newp['title'] = name
    img = info.get('image_url')
    if not img and info.get('set_num_found'):
        setnum = info.get('set_num_found')
        prefix = setnum.split('-')[0][:3]
        img = f'https://cdn.rebrickable.com/media/sets/{prefix}/{setnum}.jpg'
    if img:
        newp['imageUrl'] = img
    return newp

def main():
    prods = load_json(PROD)
    if prods is None:
        print('products.json not found in project root')
        sys.exit(1)

    cache = load_json(CACHE) or {}

    missing = find_missing_title_products(prods)
    if not missing:
        print('No products with missing titles found.')
        return

    print(f'Found {len(missing)} product(s) with missing titles. Will attempt to enrich each.')

    # implement a lightweight refresh_one here so we don't need to import refresh_cache
    import re
    import requests
    session = requests.Session()

    # try to extract API_KEY from refresh_cache.py if present
    API_KEY = None
    rc_path = HERE / 'refresh_cache.py'
    if rc_path.exists():
        txt = rc_path.read_text(encoding='utf-8')
        m = re.search(r"API_KEY\s*=\s*['\"]([0-9a-fA-F]+)['\"]", txt)
        if m:
            API_KEY = m.group(1)

    # fallback to a known key literal (present elsewhere in the repo)
    if not API_KEY:
        API_KEY = '10d0ebdfd8363511ead159b19b0e978f'

    def refresh_one_local(setnum, session, api_key):
        if not setnum:
            return None
        url = f'https://rebrickable.com/api/v3/lego/sets/{setnum}/'
        headers1 = {'Authorization': f'key {api_key}'}
        headers2 = {'X-Api-Key': api_key}

        try:
            r = session.get(url, headers=headers1, timeout=10)
        except Exception:
            return None
        if r.status_code == 401 or r.status_code == 403:
            try:
                r = session.get(url, headers=headers2, timeout=10)
            except Exception:
                return None

        if r.status_code == 200:
            d = r.json()
            name = d.get('name')
            img = d.get('set_img_url') or d.get('set_img') or d.get('set_img_url_preview') or d.get('set_img_url_full') or d.get('set_image')
            sfn = d.get('set_num') or setnum
            return {'name': name, 'image_url': img, 'set_num_found': sfn, 'fetched': int(time.time())}

        # try search fallback
        search_url = f'https://rebrickable.com/api/v3/lego/sets/?search={setnum}'
        try:
            r2 = session.get(search_url, headers=headers1, timeout=10)
        except Exception:
            return None
        if r2.status_code == 401 or r2.status_code == 403:
            try:
                r2 = session.get(search_url, headers=headers2, timeout=10)
            except Exception:
                return None

        if r2.status_code == 200:
            d2 = r2.json()
            results = d2.get('results') or []
            chosen = None
            for ritem in results:
                sn = ritem.get('set_num','')
                if sn.replace('-','').startswith(setnum):
                    chosen = ritem
                    break
            if not chosen and results:
                chosen = results[0]
            if chosen:
                name = chosen.get('name')
                setnum_found = chosen.get('set_num')
                image_url = chosen.get('set_img_url') or chosen.get('set_img') or None
                return {
                    'name': name,
                    'set_num_found': setnum_found,
                    'image_url': image_url,
                    'fetched': int(time.time())
                }
        # negative cache
        return None

    updated_cache = dict(cache)
    updated_products = list(prods)
    changed = 0

    for m in missing:
        sid = str(m.get('id','')).strip()
        if not sid:
            continue
        print(f'Processing set id: {sid}')
        info = updated_cache.get(sid)
        if info and info.get('name'):
            # use cached info if available
            print(f' - Using cached name for {sid}: {info.get("name")[:60]}')
        else:
            print(f' - No cached name for {sid}; attempting remote lookup')
            try:
                info = refresh_one_local(sid, session, API_KEY)
            except Exception as e:
                print(f'Lookup failed for {sid}:', e)
                info = None
            if info:
                updated_cache[sid] = info
            time.sleep(0.5)

        if info:
            # apply to all matching products with that id
            for i,p in enumerate(updated_products):
                if str(p.get('id','')).strip() == sid:
                    newp = apply_info_to_product(p, info)
                    if newp != p:
                        updated_products[i] = newp
                        changed += 1

    # backups
    if CACHE.exists():
        save_json(CACHE.with_suffix('.backup.json'), cache)
    save_json(CACHE, updated_cache)

    save_json(PROD.with_suffix('.backup.json'), prods)
    save_json(PROD, updated_products)

    print(f'Enrichment complete. Updated {changed} product entries. Cache saved to {CACHE}. Backups created.')

if __name__ == '__main__':
    main()
