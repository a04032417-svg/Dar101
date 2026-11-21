#!/usr/bin/env python3
"""The 6-hour run's own steps, so each run needs few model turns (the owner: Claude's usage at its very least).
  fx.py spec   <out.json> <tool-result file or text file> [...]   — joins the pages Hostinger returned into spec.json
  fx.py pubkey <out.pem>  <tool-result file or text file>          — the same for Dar's public key
  fx.py build  <spec.json> <work>                                 — engine/run.py with Dar's key; prints a short JSON result
  fx.py stage  <spec.json> <work> <repo>                          — copies pkg + pictures into the repo, writes the manifest entry
  fx.py fail   <spec.json> <work> <repo>                          — the manifest entry «failed» with the build's errors (Dar repairs)
  fx.py links  <repo> <id> [whop_product whop_plan whop_checkout] [shopify_url] — records where it was published
  fx.py prune  <repo> <index.json>                                — drops the files of items Dar already took in
  fx.py push   <repo> <message>                                   — one orphan commit on branch fx (the branch never grows)
  fx.py texts  <spec.json> <id>                                   — the listing texts each platform takes, ready to paste
  fx.py suite  <suite.json> <work> <repo> <spec.json>...          — (Dar 3.34.0) a field's files built one by one, joined in ONE ZIP
                                                                    (a folder per file, 15 languages each), encrypted for Dar under the
                                                                    suite's key item; a file that fails goes back to Dar to repair
"""
import json, os, sys, shutil, subprocess, hashlib, datetime, re
HERE = os.path.dirname(os.path.abspath(__file__)); ENGINE = os.path.join(os.path.dirname(HERE), 'engine')
RAW = 'https://raw.githubusercontent.com/a04032417-svg/Dar101/fx/'


def _content(path):
    t = open(path, encoding='utf8').read()
    try:
        j = json.loads(t)
        if isinstance(j, dict) and isinstance(j.get('content'), str): return j['content'], j.get('from_line'), j.get('total_lines')
    except Exception: pass
    return t, None, None


def join_pages(files):
    parts = []
    for f in files:
        c, fr, tot = _content(f); parts.append((fr or 0, c))
    parts.sort(key=lambda x: x[0])
    return '\n'.join(c for _, c in parts)


def man_load(repo):
    p = os.path.join(repo, 'fx', 'manifest.json')
    try: return json.load(open(p))
    except Exception: return {'items': []}


def man_save(repo, m):
    os.makedirs(os.path.join(repo, 'fx'), exist_ok=True)
    json.dump(m, open(os.path.join(repo, 'fx', 'manifest.json'), 'w'), ensure_ascii=False, indent=1)


def man_put(repo, entry):
    m = man_load(repo); m['items'] = [x for x in m['items'] if x.get('id') != entry['id']] + [entry]; man_save(repo, m)


def now(): return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def main(a):
    cmd = a[0]
    if cmd == 'spec':
        txt = join_pages(a[2:]); s = json.loads(txt); json.dump(s, open(a[1], 'w'), ensure_ascii=False)
        print(json.dumps({'ok': True, 'id': s.get('id'), 'slug': s.get('slug'), 'name': s.get('name'), 'tables': len(s.get('tables', []))}))
    elif cmd == 'pubkey':
        t = join_pages(a[2:])
        try: t = json.loads(t).get('pubkey_pem') or t   # index.json carries the key as "pubkey_pem"
        except Exception: pass
        m = re.search(r'-----BEGIN PUBLIC KEY-----.+?-----END PUBLIC KEY-----', t, re.S)
        open(a[1], 'w').write(m.group(0) + '\n'); print('ok')
    elif cmd == 'build':
        spec, work = a[1], a[2]; os.makedirs(work, exist_ok=True)
        r = subprocess.run([sys.executable, os.path.join(ENGINE, 'run.py'), spec, work, '--pubkey', os.path.join(work, 'pub.pem')], capture_output=True, text=True)
        try: res = json.load(open(os.path.join(work, 'result.json')))
        except Exception: res = {'ok': False, 'errors': ['run.py: ' + (r.stderr or r.stdout)[-1500:]]}
        print(json.dumps({'ok': res.get('ok'), 'stage': res.get('stage'), 'errors': res.get('errors', [])[:15], 'images': len(res.get('files', {}).get('images', []))}, ensure_ascii=False))
    elif cmd in ('stage', 'fail'):
        s = json.load(open(a[1])); work, repo = a[2], a[3]; res = json.load(open(os.path.join(work, 'result.json'))) if os.path.exists(os.path.join(work, 'result.json')) else {}
        d = os.path.join(repo, 'fx', s['id']); shutil.rmtree(d, ignore_errors=True)
        if cmd == 'fail':
            man_put(repo, {'id': s['id'], 'status': 'failed', 'error': '\n'.join(res.get('errors', ['build failed'])[:30])[:6000], 'at': now()}); print('failed entry written'); return
        os.makedirs(d); f = res['files']; shutil.copy(f['fxp'], os.path.join(d, 'pkg.fxp')); imgs = []
        for p in f['images']: shutil.copy(p, os.path.join(d, os.path.basename(p))); imgs.append(f'fx/{s["id"]}/{os.path.basename(p)}')
        li = {}  # v1.4: each language's own pictures, fx/<id>/<lang>/<name>.png
        for l, ps in (f.get('images_i18n') or {}).items():
            os.makedirs(os.path.join(d, l), exist_ok=True)
            for p in ps: shutil.copy(p, os.path.join(d, l, os.path.basename(p))); li.setdefault(l, []).append(f'fx/{s["id"]}/{l}/{os.path.basename(p)}')
        sha = hashlib.sha256(open(os.path.join(d, 'pkg.fxp'), 'rb').read()).hexdigest()
        man_put(repo, {'id': s['id'], 'status': 'built', 'pkg': f'fx/{s["id"]}/pkg.fxp', 'sha256': sha, 'images': imgs, 'images_i18n': li, 'whop': {}, 'shopify': '', 'at': now()})
        print(json.dumps({'ok': True, 'image_urls': [RAW + i for i in imgs]}))
    elif cmd == 'suite':
        import zipfile
        sj = json.load(open(a[1], encoding='utf8')); work, repo, specs = a[2], a[3], a[4:]; key = sj['key']; os.makedirs(work, exist_ok=True)
        pub = os.path.join(work, 'pub.pem'); built = []; failed = []
        for sp in specs:
            s = json.load(open(sp, encoding='utf8')); w = os.path.join(work, s['id'])
            r = subprocess.run([sys.executable, os.path.join(ENGINE, 'run.py'), sp, w], capture_output=True, text=True)
            try: res = json.load(open(os.path.join(w, 'result.json')))
            except Exception: res = {'ok': False, 'errors': ['run.py: ' + (r.stderr or r.stdout)[-1500:]]}
            if res.get('ok'): built.append((s, res))
            else:
                failed.append(s['id']); shutil.rmtree(os.path.join(repo, 'fx', s['id']), ignore_errors=True)
                man_put(repo, {'id': s['id'], 'status': 'failed', 'error': '\n'.join(res.get('errors', ['build failed'])[:30])[:6000], 'at': now()})
        if not built or (failed and os.environ.get('FX_STRICT')): print(json.dumps({'ok': False, 'failed': failed, 'note': 'a suite is posted only when every file passed'})); return  # (the worker: never a suite with a failed file)
        built.sort(key=lambda x: (x[0].get('suite') or {}).get('part', 1))
        name = re.sub(r'[^A-Za-z0-9]+', '-', (sj.get('listing', {}).get('en', {}).get('name') or sj['profession'])).strip('-')[:60] or 'Suite'
        zp = os.path.join(work, f'{name}-{len(built)}-files-15-languages.zip')
        with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
            for s, res in built:
                part = (s.get('suite') or {}).get('part', 1); folder = f'{part:02d} - ' + re.sub(r'[\\/:*?"<>|]+', '-', s['name'])[:70]
                with zipfile.ZipFile(res['files']['zip']) as one:
                    for n in one.namelist():
                        if n.endswith('/'): continue
                        z.writestr(folder + '/' + n.split('/', 1)[-1] if '/' in n else folder + '/' + n, one.read(n))
        sys.path.insert(0, ENGINE); from package import encrypt
        d = os.path.join(repo, 'fx', key); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        open(os.path.join(d, 'pkg.fxp'), 'wb').write(encrypt(open(zp, 'rb').read(), open(pub, 'rb').read())); imgs = []
        li = {}
        for s, res in built:
            part = (s.get('suite') or {}).get('part', 1)
            for pth in res['files'].get('images', []):
                nm = f'p{part}-' + os.path.basename(pth); shutil.copy(pth, os.path.join(d, nm)); imgs.append(f'fx/{key}/{nm}')
            for l, ps in (res['files'].get('images_i18n') or {}).items():  # v1.4: each language's own pictures, fx/<suite>/<lang>/p<part>-<name>.png
                os.makedirs(os.path.join(d, l), exist_ok=True)
                for pth in ps: nm = f'p{part}-' + os.path.basename(pth); shutil.copy(pth, os.path.join(d, l, nm)); li.setdefault(l, []).append(f'fx/{key}/{l}/{nm}')
        sha = hashlib.sha256(open(os.path.join(d, 'pkg.fxp'), 'rb').read()).hexdigest()
        man_put(repo, {'id': key, 'status': 'built', 'pkg': f'fx/{key}/pkg.fxp', 'sha256': sha, 'images': imgs, 'images_i18n': li, 'whop': {}, 'shopify': '', 'suite': [s['id'] for s, _ in built], 'at': now()})
        for s, _ in built:
            if s['id'] != key: man_put(repo, {'id': s['id'], 'status': 'in_suite', 'suite': key, 'at': now()})
        print(json.dumps({'ok': True, 'zip': zp, 'zip_mb': round(os.path.getsize(zp) / 1e6, 2), 'files': len(built), 'failed': failed, 'image_urls': [RAW + i for i in imgs]}))
    elif cmd == 'links':
        repo, iid = a[1], a[2]; m = man_load(repo)
        for x in m['items']:
            if x.get('id') == iid:
                if len(a) >= 6 and a[3]: x['whop'] = {'product': a[3], 'plan': a[4], 'checkout': a[5]}
                if len(a) >= 7 and a[6]: x['shopify'] = a[6]
                x['at'] = now()
        man_save(repo, m); print('ok')
    elif cmd == 'prune':
        repo, idx = a[1], json.load(open(a[2])); done = {i['id'] for i in idx.get('items', []) if i.get('status') in ('published', 'dropped')}
        m = man_load(repo); keep = []
        for x in m['items']:
            if x.get('id') in done: shutil.rmtree(os.path.join(repo, 'fx', x['id']), ignore_errors=True); continue
            keep.append(x)
        m['items'] = keep; man_save(repo, m); print(json.dumps({'kept': [x['id'] for x in keep], 'dropped': sorted(done)}))
    elif cmd == 'push':
        repo, msg = a[1], a[2]; g = lambda *c: subprocess.run(['git', '-C', repo] + list(c), check=True, capture_output=True, text=True)
        g('checkout', '-q', '--orphan', 'fx-new'); g('add', '-A'); g('-c', 'user.name=Claude', '-c', 'user.email=noreply@anthropic.com', 'commit', '-q', '-m', msg)
        subprocess.run(['git', '-C', repo, 'branch', '-D', 'fx'], capture_output=True); g('branch', '-m', 'fx')
        r = subprocess.run(['git', '-C', repo, 'push', '-q', '-f', 'origin', 'fx'], capture_output=True, text=True)
        print(json.dumps({'ok': r.returncode == 0, 'err': r.stderr[-300:]}))
    elif cmd == 'texts':
        s = json.load(open(a[1])); L = s['listing']; feats = L.get('features', []); sig = s.get('signature', [])
        html = '<p>' + s.get('tagline', '') + '</p>' + ''.join('<p>' + p.strip() + '</p>' for p in L['description'].split('\n\n') if p.strip())
        html += '<p><strong>Built for this profession:</strong></p><ul>' + ''.join(f'<li><strong>{x["name"]}</strong> — {x["why"]}</li>' for x in sig) + '</ul>'
        html += '<p><strong>Inside:</strong></p><ul>' + ''.join(f'<li>{f}</li>' for f in feats) + '</ul>'
        html += '<p>15 languages in one purchase: English, Arabic, French, Spanish, German, Italian, Portuguese, Turkish, Dutch, Russian, Persian, Urdu, Hindi, Chinese and Indonesian. Instant download after purchase. Needs Excel 2019, 2021, Microsoft 365 or LibreOffice Calc.</p>'
        whop = (s.get('tagline', '') + '\n\n' + '\n'.join('• ' + x['name'] + ' — ' + x['why'] for x in sig) + '\n\n15 languages · instant download · Excel 2019+/365 or LibreOffice.')[:1490]
        out = {'title_whop': s['name'][:80], 'headline': L.get('headline', s.get('tagline', ''))[:80], 'whop_description': whop, 'price': s.get('price_usd', 20),
               'shopify_title': L['title'][:255], 'shopify_html': html, 'tags': L.get('tags', []), 'slug': s['slug'], 'deliver': f'https://dar.ink/dar-sync.php?fxd={s["slug"]}'}
        json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(a[1])), 'texts.json'), 'w'), ensure_ascii=False, indent=1); print(json.dumps({k: (v if k not in ('shopify_html', 'whop_description') else str(len(v)) + ' chars') for k, v in out.items()}, ensure_ascii=False))


if __name__ == '__main__': main(sys.argv[1:])
