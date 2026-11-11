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


NAMES = ['00-cover.png', '01-inside-1.png', '11-part1-01-hero.png', '12-part2-01-hero.png', '13-part3-01-hero.png', '14-part4-01-hero.png', '15-part5-01-hero.png', '16-part6-01-hero.png']


def up_images(ST, state_path, langs, budget=140, workers=12):
    """uploads the 8 gallery pictures per language (JPEG); ST[l]['imgs'] = [file ids]; resumable"""
    import time
    t0 = time.time(); jobs = [(l, i, n) for l in langs for i, n in enumerate(NAMES) if not (ST[l].get('imgs') or [None] * 8)[i]]

    def w(j):
        l, i, n = j
        if time.time() - t0 > budget: return None
        r = requests.get(PACK + f'images/{l}/{n}', timeout=120); r.raise_for_status()
        fid, _ = upload(to_jpeg(r.content), f'ac-{l}-{i + 1}.jpg')
        return l, i, fid
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(w, j) for j in jobs]
        done, _ = cf.wait(futs, timeout=budget + 20)
    for f in done:
        try:
            r = f.result()
            if r:
                l, i, fid = r; ST[l].setdefault('imgs', [None] * 8)[i] = fid
        except Exception as e:
            print('ERR', str(e)[:200])
    json.dump(ST, open(state_path, 'w'))
    return {l: sum(1 for x in ST[l].get('imgs') or [] if x) for l in langs}


def finish_products(ST, state_path, LST, langs, visibility='visible'):
    out = {}
    for l in langs:
        L = LST[l]
        desc = L['description'].split('\n\n')[0] + '\n\n' + '\n'.join('• ' + x for x in L['features'])
        if len(desc) > 1500: desc = desc[:1497].rsplit('\n', 1)[0]
        r = wt('WHOP_UPDATE_PRODUCT', {'id': ST[l]['pid'], 'gallery_images': [{'id': i} for i in ST[l]['imgs']], 'description': desc, 'visibility': visibility})
        r = r.get('data', r)
        gi = r.get('gallery_images') or []
        ST[l]['img_urls'] = [g.get('url') or (g.get('file') or {}).get('url') for g in gi] if isinstance(gi, list) else gi
        ST[l]['visible'] = visibility
        out[l] = len(ST[l]['img_urls'] or [])
    json.dump(ST, open(state_path, 'w'))
    return out
