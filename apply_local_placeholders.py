#!/usr/bin/env python3
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
PROD = HERE / 'products.json'
REPORT = HERE / 'image_check_report.json'
LOCAL = 'http://127.0.0.1:8000/placeholder.svg'

if not PROD.exists():
    print('products.json not found'); sys.exit(1)
if not REPORT.exists():
    print('image_check_report.json not found'); sys.exit(1)
prods = json.loads(PROD.read_text(encoding='utf-8'))
report = json.loads(REPORT.read_text(encoding='utf-8'))
ids = set(str(f.get('id')) for f in report.get('failures', []))
if not ids:
    print('No failures to update'); sys.exit(0)
backup = PROD.with_suffix('.backup.localplace.json')
backup.write_text(json.dumps(prods, indent=2, ensure_ascii=False), encoding='utf-8')
changed = 0
for p in prods:
    if str(p.get('id')) in ids:
        if p.get('imageUrl') != LOCAL:
            p['imageUrl'] = LOCAL; changed += 1
PROD.write_text(json.dumps(prods, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Applied local placeholder to {changed} products; backup at {backup}')
