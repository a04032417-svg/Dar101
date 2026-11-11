#!/usr/bin/env python3
"""verifier.py — Dar's verification worker (GitHub Actions, 2026-11-07; the owner: «يجب ان تتأكد منظومة دار ان القوالب ستعمل فعليا بعد ذلك
انت تتأكد — لا مجال للخطأ»). Every run: read the feed Dar publishes (its specs encrypted for this worker), build every file of each ready suite
in all 15 languages, recalculate each workbook in LibreOffice and verify it (no formula error, demo numbers equal an independent
recalculation, charts that show something, gauges that hold a share, numbers that fit their columns), draw the pictures, and post the
result on branch fx: the suite's package encrypted for Dar, or each failing file with its errors — Dar's architect repairs it and learns the
lesson. Claude only looks at what passed, publishes it and reports.
env: FX_VERIFY_KEY (this worker's private key, PEM — an Actions secret), FX_FEED (the feed's address). usage: verifier.py <repo dir> | verifier.py --plan <repo dir> (prints how many suites to build)"""
import os, sys, json, hashlib, subprocess, base64, urllib.request, datetime, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
# 2026-11-09: cryptography is imported where it is used, so `verifier.py --plan` runs before the tools are installed (the workflow
# skips LibreOffice and the build when there is nothing to build, and can run every hour for free). After each built suite,
# xlcheck.py checks the shipped ZIP against the rules Excel enforces and LibreOffice does not (fx/xlcheck/<suite>.json).


def unpack(blob, key):
    """FXP1 · u16 N · RSA-OAEP(SHA-1) wrapped AES key · iv12 · tag16 · ciphertext (the package format of SPEC.md, here for the specs)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if blob[:4] != b'FXP1': raise ValueError('not FXP1')
    n = int.from_bytes(blob[4:6], 'big'); wk = blob[6:6 + n]; p = 6 + n
    k = key.decrypt(wk, padding.OAEP(mgf=padding.MGF1(hashes.SHA1()), algorithm=hashes.SHA1(), label=None))
    iv, tag, ct = blob[p:p + 12], blob[p + 12:p + 28], blob[p + 28:]
    return AESGCM(k).decrypt(iv, ct + tag, None)


def get(url, tries=3):
    last = None
    for _ in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'dar-fx-verifier'}), timeout=60) as r: return r.read()
        except Exception as x: last = x
    raise last


def man(repo):
    p = os.path.join(repo, 'fx', 'manifest.json')
    return json.load(open(p)) if os.path.exists(p) else {'items': []}


def todo(idx, M):
    """The suites to build now: listing done, every live file ready, not built with these files, no unrepaired failed file."""
    out = []
    for su in idx.get('suites', []):
        k = su['key']; parts = [p for p in su['parts'] if p.get('status') != 'dropped']  # [{id, sha, part}] (a dropped file is not in the suite)
        if not su.get('listing') or not parts or any(p.get('status') not in ('ready', 'published') or not p.get('sha') for p in parts): continue
        shas = {p['id']: p['sha'] for p in parts}; e = M.get(k, {})
        if e.get('status') in ('built', 'published') and e.get('parts_sha') == shas: continue
        if any(M.get(p['id'], {}).get('status') == 'failed' and M[p['id']].get('spec_sha') == p['sha'] for p in parts): continue  # (Dar repairs it first)
        out.append((su, parts, shas))
    return out


def now(): return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def gate_parts(repo, idx, feed, key, work, pub, budget=2):
    """2026-11-09 quality gate (the owner: «لا يجب أن تكرر المنظومة عدم الاتقان هذا»). EVERY ready file is checked the moment it is ready, not only when its
    whole suite is listed: (1) validate.validate = the spec contract + depth.py (>= 6 profession-specific services, tools, messages, a document, a
    checklist, realistic demo spread over a year, names, picture texts translated in 14 languages); (2) a strict build of the file alone (at most
    `budget` per run, the cost is minutes of free Actions time). A file that fails goes to the manifest as `failed` with the exact errors — the same
    path a failed suite build uses — so Dar's architect repairs it and learns the lesson. Results are recorded in fx/gate.json."""
    sys.path.insert(0, os.path.join(ROOT, 'engine'))
    import validate
    gp = os.path.join(repo, 'fx', 'gate.json')
    try: G = json.load(open(gp))
    except Exception: G = {}
    M = {x['id']: x for x in man(repo)['items']}; res = {'checked': [], 'failed': [], 'ok': [], 'pending': []}; built = 0
    for su in idx.get('suites', []):
        for p in su.get('parts', []):
            if p.get('status') not in ('ready', 'published') or not p.get('sha'): continue
            pid = p['id']
            if G.get(pid, {}).get('sha') == p['sha'] and G[pid].get('ok'): continue          # proven at this version
            if G.get(pid, {}).get('sha') == p['sha'] and not G[pid].get('ok') and M.get(pid, {}).get('status') == 'failed': continue  # already sent back
            try: raw = unpack(get(f'{feed}/{pid}.bin'), key)
            except Exception as x: res['pending'].append((pid, str(x)[:80])); continue
            if hashlib.sha256(raw).hexdigest()[:16] != p['sha'][:16]: res['pending'].append((pid, 'sha mismatch')); continue
            spec = json.loads(raw); errs = validate.validate(spec); stage = 'spec+depth'
            if not errs:
                if built >= budget: res['pending'].append((pid, 'build budget')); continue
                built += 1; w = os.path.join(work, 'gate-' + pid); shutil.rmtree(w, ignore_errors=True); os.makedirs(w)
                sp = os.path.join(w, 'spec.json'); open(sp, 'wb').write(raw)
                r = subprocess.run([sys.executable, os.path.join(ROOT, 'engine', 'run.py'), sp, os.path.join(w, 'out'), '--pubkey', pub], capture_output=True, text=True, env=dict(os.environ, FX_STRICT='1'))
                try: rj = json.load(open(os.path.join(w, 'out', 'result.json')))
                except Exception: rj = {'ok': False, 'errors': ['run.py: ' + (r.stderr or r.stdout)[-1500:]]}
                errs = [] if rj.get('ok') else (rj.get('errors') or ['strict build failed']); stage = 'strict build'
                shutil.rmtree(w, ignore_errors=True)
            res['checked'].append(pid)
            if errs:
                G[pid] = {'sha': p['sha'], 'ok': False, 'stage': stage, 'at': now(), 'errors': errs[:12]}
                M[pid] = {'id': pid, 'status': 'failed', 'error': ('QUALITY GATE (' + stage + ') — fix every item, then the file is rebuilt:\n' + '\n'.join(errs[:30]))[:6000], 'at': now(), 'spec_sha': p['sha'], 'gate': stage}
                res['failed'].append((pid, stage, len(errs)))
            else:
                G[pid] = {'sha': p['sha'], 'ok': True, 'stage': 'spec+depth+strict build', 'at': now()}; res['ok'].append(pid)
    os.makedirs(os.path.join(repo, 'fx'), exist_ok=True)
    json.dump(G, open(gp, 'w'), ensure_ascii=False, indent=1)
    json.dump({'items': list(M.values())}, open(os.path.join(repo, 'fx', 'manifest.json'), 'w'), ensure_ascii=False, indent=1)
    print('gate', json.dumps(res, ensure_ascii=False)[:1500])
    return res


def gate_todo(repo, idx):
    """Ready files the quality gate has not yet judged at their current version (so the hourly run does not sleep through a new ready file)."""
    gp = os.path.join(repo, 'fx', 'gate.json')
    try: G = json.load(open(gp))
    except Exception: G = {}
    M = {x['id']: x for x in man(repo)['items']}; n = 0
    for su in idx.get('suites', []):
        for p in su.get('parts', []):
            if p.get('status') not in ('ready', 'published') or not p.get('sha'): continue
            g = G.get(p['id'], {})
            if g.get('sha') == p['sha'] and (g.get('ok') or M.get(p['id'], {}).get('status') == 'failed'): continue
            n += 1
    return n


def plan(repo):
    """How many suites a run would build now + how many ready files the gate has yet to judge (no key, no tools needed)."""
    idx = json.loads(get(os.environ['FX_FEED'].rstrip('/') + '/index.json'))
    return len(todo(idx, {x['id']: x for x in man(repo)['items']})) + gate_todo(repo, idx)


def main(repo):
    from cryptography.hazmat.primitives import serialization
    key = serialization.load_pem_private_key(os.environ['FX_VERIFY_KEY'].encode(), password=None)
    feed = os.environ['FX_FEED'].rstrip('/'); idx = json.loads(get(feed + '/index.json'))
    work = os.path.join(repo, '..', 'fxwork'); os.makedirs(work, exist_ok=True)
    pub = os.path.join(work, 'pub.pem'); open(pub, 'w').write(idx['pubkey_pem'])
    try: gate_parts(repo, idx, feed, key, work, pub)
    except Exception as x: print('gate error', type(x).__name__, str(x)[:300])
    M = {x['id']: x for x in man(repo)['items']}; done = []
    for su, parts, shas in todo(idx, M):
        k = su['key']
        w = os.path.join(work, k); shutil.rmtree(w, ignore_errors=True); os.makedirs(w); shutil.copy(pub, os.path.join(w, 'pub.pem'))
        specs = []
        for p in sorted(parts, key=lambda x: x.get('part', 1)):
            raw = unpack(get(f'{feed}/{p["id"]}.bin'), key)
            if hashlib.sha256(raw).hexdigest()[:16] != p['sha'][:16]: print('sha mismatch', p['id']); specs = []; break
            sp = os.path.join(w, p['id'] + '.json'); open(sp, 'wb').write(raw); specs.append(sp)
        if not specs: continue
        sj = os.path.join(w, 'suite.json'); open(sj, 'wb').write(unpack(get(f'{feed}/{k}.suite.bin'), key))
        r = subprocess.run([sys.executable, os.path.join(HERE, 'fx.py'), 'suite', sj, w, repo] + specs, capture_output=True, text=True, env=dict(os.environ, FX_STRICT='1'))
        print(k, r.stdout[-1500:], r.stderr[-800:])
        m2 = {x['id']: x for x in man(repo)['items']}
        if m2.get(k, {}).get('status') == 'built':
            m2[k]['parts_sha'] = shas
            zips = sorted(os.path.join(d, f) for d, _, fs in os.walk(w) for f in fs if f.endswith('.zip'))
            if zips:
                x = subprocess.run([sys.executable, os.path.join(HERE, 'xlcheck.py')] + zips + ['--json', os.path.join(repo, 'fx', 'xlcheck', k + '.json')], capture_output=True, text=True)
                print(k, 'xlcheck', x.stdout[-700:], x.stderr[-300:])
        for p in parts:
            if m2.get(p['id'], {}).get('status') == 'failed': m2[p['id']]['spec_sha'] = p['sha']
        json.dump({'items': list(m2.values())}, open(os.path.join(repo, 'fx', 'manifest.json'), 'w'), ensure_ascii=False, indent=1)
        done.append(k)
    print(json.dumps({'suites_checked': done}))
    return done


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--plan':
        print(plan(sys.argv[2] if len(sys.argv) > 2 else ROOT)); sys.exit(0)
    d = main(sys.argv[1] if len(sys.argv) > 1 else ROOT)
    sys.exit(0)
