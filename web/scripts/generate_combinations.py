#!/usr/bin/env python3
import os
import re
import json
import random
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    raise SystemExit('This script requires `requests` and `beautifulsoup4`. Install with pip.')

URL = 'https://www.xn--9l4b4xi9r.com/pc-parts-ai/parts.html'
OUT_PATH = os.path.join('web', 'public', '한국인터넷.한국', '참소식.com', 'pc-parts-ai', 'nbData', 'manifest.json')


def fetch_page(url):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.text


def parse_price(text):
    if not text:
        return None
    m = re.search(r"([0-9][0-9,]+)", text.replace('\u00a0', ' '))
    if not m:
        return None
    return int(m.group(1).replace(',', ''))


def get_category(elem):
    # Find nearest previous heading
    heading = elem.find_previous(lambda t: t.name in ('h1', 'h2', 'h3', 'h4'))
    if heading and heading.get_text(strip=True):
        return heading.get_text(strip=True)
    return 'default'


def parse_products(html):
    soup = BeautifulSoup(html, 'html.parser')
    # find candidate product elements
    candidates = []
    selectors = ['.product', '.product-item', '.part', '.item', '.card', 'li', 'div.card']
    for sel in selectors:
        found = soup.select(sel)
        for f in found:
            # avoid adding very large containers
            if len(f.get_text(strip=True)) < 300:
                candidates.append(f)

    # fallback: look for anchors that look like product links
    if not candidates:
        candidates = soup.select('a')[:200]

    categories = {}
    for c in candidates:
        name = c.get_text(separator=' ', strip=True)
        if not name:
            continue
        cat = get_category(c)
        img = None
        a = c.find('a') if c.find('a') else (c if c.name == 'a' else None)
        if a and a.get('href'):
            url = a.get('href')
        else:
            url = None
        imgel = c.find('img')
        if imgel and imgel.get('src'):
            img = imgel.get('src')
        price = parse_price(name)

        prod = {
            'name': name,
            'price': price,
            'image': img,
            'url': url,
        }
        categories.setdefault(cat, []).append(prod)

    # remove empty categories
    categories = {k: v for k, v in categories.items() if v}
    return categories


def generate_combinations(categories, count):
    combos = []
    cats = list(categories.keys())
    # if only a single flat list, make combos of 3 distinct items
    single_list = False
    if len(cats) <= 1:
        single_list = True
        flat = categories.get(cats[0]) if cats else []
        if not flat:
            return []

    prices = []
    if single_list:
        prices = [p['price'] or 0 for p in flat]
    else:
        for lst in categories.values():
            prices.extend([p['price'] or 0 for p in lst])
    max_price = max(prices) if prices else 0

    for i in range(count):
        if single_list:
            chosen = random.sample(flat, k=min(3, len(flat)))
            combo_items = chosen
        else:
            combo_items = [random.choice(categories[k]) for k in cats]

        total_price = sum([p.get('price') or 0 for p in combo_items])
        price_score = ((max_price - total_price) / max_price) if max_price else 0
        score = random.random() + 0.5 * price_score
        combos.append({
            'items': combo_items,
            'total_price': total_price,
            'score': score,
        })

    combos.sort(key=lambda x: x['score'], reverse=True)
    return combos


def ensure_out_dir(path):
    d = os.path.dirname(path)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def main():
    counts = [100, 500, 1000]
    print('Fetching page...')
    html = fetch_page(URL)
    print('Parsing products...')
    categories = parse_products(html)
    if not categories:
        print('No products found; aborting.')
        return

    result = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'source_url': URL,
        'runs': []
    }

    for c in counts:
        print(f'Generating {c} random combinations...')
        combos = generate_combinations(categories, c)
        top3 = combos[:3]
        result['runs'].append({
            'count': c,
            'total_generated': len(combos),
            'top3': top3,
        })

    ensure_out_dir(OUT_PATH)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print('Wrote results to', OUT_PATH)


if __name__ == '__main__':
    main()
