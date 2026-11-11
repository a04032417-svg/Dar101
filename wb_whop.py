# Workbench: publish a Dar suite on Whop (15 products, one per language), images and ZIP from GitHub raw
import requests, json, os, time, concurrent.futures as cf
BIZ = 'biz_EPdES7EEpWl9qp'
GH = 'https://raw.githubusercontent.com/a04032417-svg/Dar101/'


def wt(slug, args):
    r = run_composio_tool(slug, args)
    d = r[0] if isinstance(r, tuple) else r
    if isinstance(d, dict) and d.get('error'): raise RuntimeError(f'{slug}: {d.get("error")}')
    return d.get('data', d) if isinstance(d, dict) else d


def upload(content, filename):
    f = wt('WHOP_CREATE_FILE', {'filename': filename})
    f = f.get('data', f) if isinstance(f, dict) else f
    url = f.get('upload_url') or f.get('presigned_url') or (f.get('upload') or {}).get('url')
    hdr = f.get('upload_headers') or {}
    r = requests.put(url, data=content, headers=hdr, timeout=600)
    if r.status_code >= 300: raise RuntimeError(f'PUT {r.status_code} {r.text[:200]}')
    return f['id'], f


def make_product(lang, L, gallery_ids, route, extra_lines):
    desc = L['description'].split('\n\n')[0] + '\n\n' + '\n'.join('• ' + x for x in extra_lines + L['features'])
    if len(desc) > 1500: desc = desc[:1497].rsplit('\n', 1)[0]
    p = wt('WHOP_CREATE_PRODUCT', {'account_id': BIZ, 'title': L['seo_title'][:80], 'headline': L['headline'][:80], 'description': desc, 'route': route,
                                   'visibility': 'visible', 'gallery_images': [{'id': i} for i in gallery_ids[:8]], 'metadata': {'suite': 'accounting-bookkeeping', 'lang': lang},
                                   'labels': ['accounting-bookkeeping'], 'idempotency_key': 'ac-prod-' + lang + '-' + route})
    p = p.get('data', p)
    v = wt('WHOP_CREATE_VARIANT', {'account_id': BIZ, 'product_id': p['id'], 'plan_type': 'one_time', 'release_method': 'buy_now', 'initial_price': 29, 'currency': 'usd',
                                   'visibility': 'visible', 'unlimited_stock': True, 'idempotency_key': 'ac-var-' + lang + '-' + route})
    v = v.get('data', v)
    return p['id'], v['id'], desc


PACK = GH + 'out/ac/pack/'


def to_jpeg(png_bytes):
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(png_bytes)).convert('RGB').resize((1920, 1440), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=88, optimize=True); return b.getvalue()


def gallery(lang, names):
    ids = []
    for i, n in enumerate(names):
        r = requests.get(PACK + f'images/{lang}/{n}', timeout=120); r.raise_for_status()
        fid, _ = upload(to_jpeg(r.content), f'ac-{lang}-{i + 1}.jpg')
        ids.append(fid)
    return ids
