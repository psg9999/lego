#!/usr/bin/env python3
"""Enrich products.json (sets) with names from Rebrickable.

Usage: run from project folder with your API key:
  .venv/bin/python enrich_rebrickable.py <REBRICKABLE_API_KEY>

This script caches lookups in rebrickable_cache.json and writes products_with_names.json
and updates products.json (backup saved as products.backup.json).
"""
import json
import sys
import time
from pathlib import Path
from typing import List

try:
    import requests
except Exception:
    print('requests not installed. Please run: .venv/bin/python -m pip install requests')
    raise

HERE = Path(__file__).resolve().parent
PRODUCTS = HERE / 'products.json'
OUT = HERE / 'products_with_names.json'
CACHE = HERE / 'rebrickable_cache.json'
BACKUP = HERE / 'products.backup.json'

def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding='utf-8'))
    return {}

def save_cache(c):
    CACHE.write_text(json.dumps(c, indent=2, ensure_ascii=False), encoding='utf-8')

def brickset(setNumbers:List[str]):
    key = "3-ox7x-YChK-FEBgV"
    params = json.dumps({"query": ','.join(setNumbers)})
    url = f'https://brickset.com/api/v3.asmx/getSets?apiKey={key}&userHash=&params={params}'
    print(url)
    result = requests.get(url).json()
    print(result)
    if result.get("status", "error") != "error":
        print(f"Brickset API returned {len(result.get('sets', []))} sets.")
        print(f"Brickset API returned {result.get('sets', [])}.")
        all_setnums = {legoSet.get('number'): legoSet.get("LEGOCom", {}).get("US", {}).get("retailPrice", "unknown") for legoSet in result.get("sets", [])}
        return all_setnums
    return {}


def normalize_setnum(s):
    if s is None:
        return ''
    ss = str(s).strip()
    # remove trailing .0 from numbers
    if ss.endswith('.0'):
        ss = ss[:-2]
    return ss

def lookup_set_name(setnum, api_key, session, cache):
    if not setnum:
        return None
    # if we have a positive cached name, return it; otherwise we'll try again (to allow search fallback)
    if setnum in cache and cache[setnum].get('name'):
        return cache[setnum].get('name')

    url = f'https://rebrickable.com/api/v3/lego/sets/{setnum}/'
    headers1 = {'Authorization': f'key {api_key}'}
    headers2 = {'X-Api-Key': api_key}

    resp = session.get(url, headers=headers1)
    if resp.status_code == 401 or resp.status_code == 403:
        resp = session.get(url, headers=headers2)

    if resp.status_code == 200:
        data = resp.json()
        name = data.get('name')
        # try common image fields returned by Rebrickable set endpoint
        img = data.get('set_img_url') or data.get('set_img') or data.get('set_img_url_preview') or data.get('set_img_url_full') or data.get('set_image')
        cache[setnum] = {'name': name, 'image_url': img, 'fetched': int(time.time())}
        save_cache(cache)
        return name
    else:
        # try search endpoint as a fallback
        search_url = f'https://rebrickable.com/api/v3/lego/sets/?search={setnum}'
        print(f"Url is {search_url}")
        resp2 = session.get(search_url, headers=headers1)
        if resp2.status_code == 401 or resp2.status_code == 403:
            resp2 = session.get(search_url, headers=headers2)

        if resp2.status_code == 200:
            data2 = resp2.json()
            results = data2.get('results') or []
            # try to pick the best match: prefer set_num that startswith the query
            chosen = None
            for r in results:
                sn = r.get('set_num','')
                if sn.replace('-','').startswith(setnum):
                    chosen = r
                    break
            if not chosen and results:
                chosen = results[0]

            if chosen:
                name = chosen.get('name')
                setnum_found = chosen.get('set_num')
                # search results may include a thumbnail field
                image_url = chosen.get('set_img_url') or chosen.get('set_img') or None
                cache[setnum] = {
                    'name': name,
                    'set_num_found': setnum_found,
                    'image_url': image_url,
                    'fetched': int(time.time())
                }
                save_cache(cache)
                return name

        # cache negative result to avoid retrying too often
        cache[setnum] = {'name': None, 'fetched': int(time.time()), 'status': resp.status_code}
        save_cache(cache)
        print(f'Warning: lookup {setnum} -> HTTP {resp.status_code} (and search fallback failed)')
        return None

def main():
    if len(sys.argv) < 2:
        print('Usage: enrich_rebrickable.py <API_KEY> [delay_seconds]')
        sys.exit(2)

    api_key = sys.argv[1].strip()
    try:
        delay = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
    except Exception:
        delay = 0.3
    if not PRODUCTS.exists():
        print(f'Error: {PRODUCTS} not found')
        sys.exit(1)

    prods = json.loads(PRODUCTS.read_text(encoding='utf-8'))
    cache = load_cache()

    unique = []
    seen = set()
    for p in prods:
        sid = normalize_setnum(p.get('id'))
        if sid and sid not in seen:
            seen.add(sid)
            unique.append(sid)

    print(f'Found {len(unique)} unique set numbers to lookup (will skip cached entries).')

    session = requests.Session()
    looked = 0
    for i,s in enumerate(unique, start=1):
        if s in cache and cache[s].get('name') is not None:
            continue
        name = lookup_set_name(s, api_key, session, cache)
        looked += 1
        # be polite — configurable delay to avoid rate limits
        time.sleep(delay)
        if looked % 50 == 0:
            print(f'Looked up {looked} so far...')

    # apply names
    backup_text = PRODUCTS.read_text(encoding='utf-8')
    BACKUP.write_text(backup_text, encoding='utf-8')

    updated = []
    all_setnums = [normalize_setnum(p.get('id')) for p in prods if normalize_setnum(p.get('id'))]
    brickset_sets = brickset(all_setnums)
    print("Brickset MSRP data retrieved for sets.", len(all_setnums))
    for sid in all_setnums:
        # sid = normalize_setnum(p.get('id'))
        name = cache.get(sid, {}).get('name') if sid else None
        newp = dict(p)
        if name:
            # only replace if title is empty or placeholder
            if not newp.get('title') or newp.get('title') == sid or newp.get('title').strip()=='':
                newp['title'] = name
        # persist imageUrl into the product if available in cache
        entry = cache.get(sid, {}) if sid else {}
        print(brickset_sets)
        newp['msrp'] = brickset_sets.get(sid, {})
        img = entry.get('image_url') or entry.get('set_img_url')
        if not img and entry.get('set_num_found'):
            setnum = entry.get('set_num_found')
            prefix = setnum.split('-')[0][:3]
            img = f'https://cdn.rebrickable.com/media/sets/{prefix}/{setnum}.jpg'
        if img:
            newp['imageUrl'] = img
        updated.append(newp)

    OUT.write_text(json.dumps(updated, indent=2, ensure_ascii=False), encoding='utf-8')
    # also overwrite products.json
    PRODUCTS.write_text(json.dumps(updated, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f'Wrote enriched products to {OUT} and updated {PRODUCTS}. Cache in {CACHE}.')

if __name__ == '__main__':
    main()
