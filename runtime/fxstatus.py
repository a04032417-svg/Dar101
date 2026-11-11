#!/usr/bin/env python3
"""fxstatus.py — one small status file for Claude (2026-11-09; the owner: use as little of Claude's limit as possible).
Runs in the fxverify workflow after verifier.py. Reads Dar's public feed index and fx/manifest.json and writes fx/status.json:
whether there is work for Claude (a built suite not yet delivered, a failed file Dar has not repaired, or Dar has stalled), with
short reasons, the time of the last complete suite (3-hour alert) and the Excel check's problem counts. The file changes only when Dar's state changes, so the branch gets no empty commits. Claude's 3-hour watcher reads
only this file (one call) instead of Dar's whole index.  usage: fxstatus.py <repo dir>   env: FX_FEED"""
import os, sys, json, hashlib, datetime, urllib.request

def now(): return datetime.datetime.now(datetime.timezone.utc)
def iso(t): return t.strftime('%Y-%m-%dT%H:%M:%SZ')
def parse(s):
    try: return datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
    except Exception: return None

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'dar-fx-verifier'}), timeout=60) as r: return r.read()

def build(idx, man, old, t):
    M = {x['id']: x for x in man.get('items', [])}
    parts = {'ready': 0, 'work': 0, 'dropped': 0, 'other': 0}
    fp = hashlib.sha256(); complete, building, undelivered, failed = [], [], [], []
    for su in idx.get('suites', []):
        k = su.get('key', '?'); ps = su.get('parts', []); live = [p for p in ps if p.get('status') != 'dropped']
        for p in ps:
            s = p.get('status'); parts[s if s in parts else 'other'] += 1
            fp.update(f"{k}|{p.get('id')}|{s}|{p.get('sha', '')}\n".encode())
        if not live: continue
        prof = su.get('profession', k)
        unrepaired = any(M.get(p.get('id'), {}).get('status') == 'failed' and M[p.get('id')].get('spec_sha') == p.get('sha') for p in live)
        if su.get('listing') and not unrepaired and all(p.get('status') in ('ready', 'published') and p.get('sha') for p in live):
            e = M.get(k, {})
            if e.get('status') == 'built' and not (e.get('whop') or {}): undelivered.append(f"{k} ({prof})")
            elif e.get('status') not in ('built', 'published'): complete.append(f"{k} ({prof})")
        elif any(p.get('status') in ('ready', 'work') for p in live): building.append(f"{k} ({prof})")
        for p in live:
            e = M.get(p.get('id'), {})
            if e.get('status') == 'failed' and e.get('spec_sha') == p.get('sha'):
                at = parse(e.get('at', '')); age = round((t - at).total_seconds() / 3600, 1) if at else None
                failed.append({'id': p.get('id'), 'age_h': age, 'error': (e.get('error') or '')[:160]})
    f = fp.hexdigest()[:16]
    seen = dict(old.get('complete_seen') or {})  # suite -> first time it was complete (owner's target: 8 specialised products a day)
    for k in [x.split(' (')[0] for x in complete + undelivered] + [i['id'] for i in man.get('items', []) if i.get('status') in ('built', 'published') and i.get('suite')]:
        seen.setdefault(k, iso(t))
    day = [k for k, v in seen.items() if parse(v) and (t - parse(v)).total_seconds() < 86400]
    last_done = max((v for v in seen.values() if parse(v)), key=lambda v: parse(v), default=None)
    last = old.get('last_change_at') if old.get('fingerprint') == f else iso(t)
    reasons = []
    if undelivered: reasons.append(f"{len(undelivered)} built suite(s) not delivered")
    if complete: reasons.append(f"{len(complete)} complete suite(s) not built yet (fxverify)")
    old_fail = [x for x in failed if x['age_h'] is None or x['age_h'] >= 6]
    if old_fail: reasons.append(f"{len(old_fail)} failed file(s) not repaired by Dar for 6 h+")
    return {'fingerprint': f, 'last_change_at': last,
            'work': bool(reasons), 'reasons': reasons, 'parts': parts, 'suites_total': len(idx.get('suites', [])),
            'undelivered': undelivered[:20], 'complete_not_built': complete[:20], 'in_progress': building[:20], 'failed': failed[:20],
            'complete_seen': dict(sorted(seen.items(), key=lambda kv: kv[1])[-60:]), 'complete_last_24h': len(day), 'target_per_day': 8,
            'last_complete_at': last_done, 'counter_since': old.get('counter_since') or iso(t),
            'note': ('last_change_at = when any file of Dar last changed status; stalled if now minus last_change_at >= 12 h. '
                     '3-hour alert (the owner, 2026-11-09: one specialised product every 3 hours): now minus the later of last_complete_at '
                     'and counter_since >= 3 h. The watcher computes both, so this file changes only when Dar does.')}

def main(repo):
    t = now(); sp = os.path.join(repo, 'fx', 'status.json')
    old = json.load(open(sp)) if os.path.exists(sp) else {}
    mp = os.path.join(repo, 'fx', 'manifest.json'); man = json.load(open(mp)) if os.path.exists(mp) else {'items': []}
    try: idx = json.loads(get(os.environ['FX_FEED'].rstrip('/') + '/index.json'))
    except Exception as x:
        st = dict(old, work=True, reasons=[f"Dar's feed unreachable: {str(x)[:120]}"]); st.setdefault('last_change_at', iso(t))
    else:
        st = build(idx, man, old, t)
    xd = os.path.join(repo, 'fx', 'xlcheck'); ex = {}  # xlcheck.py results: the Excel rules LibreOffice does not enforce
    for fn in (sorted(os.listdir(xd)) if os.path.isdir(xd) else []):
        try: r = json.load(open(os.path.join(xd, fn))) if fn.endswith('.json') else {}
        except Exception: r = {}
        if r.get('problems'): ex[fn[:-5]] = r['problems']
    st['excel_problems'] = ex
    if st != old:
        os.makedirs(os.path.dirname(sp), exist_ok=True); json.dump(st, open(sp, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({'work': st['work'], 'reasons': st['reasons']}, ensure_ascii=False))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
