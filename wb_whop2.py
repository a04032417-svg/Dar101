# Workbench: Whop gallery images + visibility for a Dar suite (15 products, one per language). Generic version of ac/tr/wb_whop.py.
# ST = {lang: {'pid': product_id, 'imgs': [file ids]}}, resumable. G = gallery.json['gallery'] ({lang: ['images/<lang>/00-cover.png', ...]}).
import requests, json, os, time, io, concurrent.futures as cf, sys
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


def to_jpeg(png_bytes):
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes)).convert('RGB').resize((1920, 1440), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=88, optimize=True); return b.getvalue()


def up_images(ST, state_path, langs, G, pack_ref, prefix, budget=140, workers=12):
    """uploads the 8 gallery pictures per language (JPEG); resumable; returns {lang: count}. pack_ref = commit SHA of branch out/<suite>/pack"""
    t0 = time.time()
    jobs = [(l, i, n) for l in langs for i, n in enumerate(G[l]) if not (ST[l].get('imgs') or [None] * 8)[i]]

    def w(j):
        l, i, n = j
        if time.time() - t0 > budget: return None
        r = requests.get(GH + pack_ref + '/' + n, timeout=120); r.raise_for_status()
        fid, _ = upload(to_jpeg(r.content), f'{prefix}-{l}-{i + 1}.jpg')
        return l, i, fid
    ex = cf.ThreadPoolExecutor(workers)
    futs = [ex.submit(w, j) for j in jobs]
    done, _ = cf.wait(futs, timeout=budget + 20)
    ex.shutdown(wait=False)
    for f in done:
        try:
            r = f.result()
            if r:
                l, i, fid = r; ST[l].setdefault('imgs', [None] * len(G[l]))[i] = fid
        except Exception as e:
            print('ERR', str(e)[:200], file=sys.stderr)
    json.dump(ST, open(state_path, 'w'))
    return {l: sum(1 for x in ST[l].get('imgs') or [] if x) for l in langs}


def finish_products(ST, state_path, langs, visibility='visible'):
    """sets the gallery and the visibility of each language's product"""
    out = {}
    for l in langs:
        if len([x for x in ST[l].get('imgs') or [] if x]) < 2: out[l] = 'no images'; continue
        r = wt('WHOP_UPDATE_PRODUCT', {'id': ST[l]['pid'], 'gallery_images': [{'id': i} for i in ST[l]['imgs'] if i], 'visibility': visibility})
        r = r.get('data', r)
        gi = r.get('gallery_images') or []
        ST[l]['img_urls'] = [g.get('url') or (g.get('file') or {}).get('url') for g in gi] if isinstance(gi, list) else gi
        ST[l]['visible'] = visibility
        out[l] = len(ST[l]['img_urls'] or [])
    json.dump(ST, open(state_path, 'w'))
    return out
