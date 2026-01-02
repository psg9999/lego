#!/usr/bin/env python3
"""Set placeholder images for any products listed in image_check_report.json failures.

Backs up `products.json` to `products.json.backup.placeholder` then writes updated `products.json`.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROD = HERE / 'products.json'
REPORT = HERE / 'image_check_report.json'

PLACEHOLDER = 'https://via.placeholder.com/420x320?text=No+Image+Available'

def main():
    if not PROD.exists():
        print('products.json not found'); sys.exit(1)
    if not REPORT.exists():
        print('image_check_report.json not found; nothing to do'); sys.exit(1)
    prods = json.loads(PROD.read_text(encoding='utf-8'))
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    failures = report.get('failures', [])
    ids = set(str(f.get('id')) for f in failures if f.get('id'))
    if not ids:
        print('No failures listed; nothing to do')
        return

    # backup
    backup = PROD.with_suffix('.backup.placeholder.json')
    backup.write_text(json.dumps(prods, indent=2, ensure_ascii=False), encoding='utf-8')

    changed = 0
    for p in prods:
        if str(p.get('id')) in ids:
            if p.get('imageUrl') != PLACEHOLDER:
                p['imageUrl'] = PLACEHOLDER
                changed += 1

    PROD.write_text(json.dumps(prods, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Set placeholder for {changed} products. Backup at {backup}')

if __name__ == '__main__':
    main()
