
# conv-C-0602 helper for the shared Composio workbench (names prefixed to avoid clashes)
# bootstrap in a fresh sandbox: r,e=proxy_execute('GET','https://api.github.com/repos/a04032417-svg/Dar101/contents/tools/ghh_cc.py?ref=pipeline','github',query_params={}); import base64; open('/mnt/files/ghh.py','w').write(base64.b64decode((r.get('data',r))['content']).decode())
import json, base64, datetime, time, io, contextlib, hashlib, tarfile, requests
CC_O, CC_R = 'a04032417-svg', 'Dar101'
CC_TR = '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_012y1TEpcvy5rZRS4BFUB2qa'
GH_LOG = []
def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)
q = quiet
def gh(method, ep, body=None):
    url = ep if ep.startswith('http') else 'https://api.github.com' + ep
    last = None
    for k in range(5):
        try:
            if body is None: r, e = proxy_execute(method, url, 'github', query_params={})
            else: r, e = proxy_execute(method, url, 'github', body=body, query_params={})
            if r is not None and not e: return r, e
            last = e
        except Exception as ex:
            last = ex
        GH_LOG.append((method, url[-60:], str(last)[:80])); time.sleep(2 + k * 2)
    return None, last
def _d(r): return r.get('data', r) if isinstance(r, dict) else r
def now(): return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def get_file(path, ref='pipeline'):
    r, e = gh('GET', f'/repos/{CC_O}/{CC_R}/contents/{path}?ref={ref}')
    if r is None: return None, None, e
    d = _d(r); c = base64.b64decode(d['content']).decode()
    return (json.loads(c) if path.endswith('.json') else c), d['sha'], None
def put_file(path, text, sha, msg, branch='pipeline'):
    body = {'message': msg + CC_TR, 'content': base64.b64encode(text.encode()).decode(), 'branch': branch}
    if sha: body['sha'] = sha
    return gh('PUT', f'/repos/{CC_O}/{CC_R}/contents/{path}', body)
def set_task(tid, worker, status, note=None):
    d, sha, e = get_file(f'tasks/{tid}.json')
    if d is None: return f'{tid}: read error {e}'
    if status == 'claimed':
        if d['status'] in ('done', 'blocked'): return f'{tid}: not free ({d["status"]})'
        if d['status'] == 'claimed' and d.get('by') != worker:
            try: age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.strptime(d['at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)).total_seconds() / 60
            except Exception: age = 1e9
            if age < 150: return f'{tid}: claimed by {d["by"]} {int(age)} min ago'
    elif d['status'] == 'claimed' and d.get('by') not in ('', worker):
        return f'{tid}: not your claim ({d.get("by")})'
    d.update(status=status, by=worker, at=now())
    if note is not None: d['note'] = note
    verb = {'claimed': 'claim', 'done': 'done', 'todo': 'release', 'blocked': 'release'}[status]
    r, e = put_file(f'tasks/{tid}.json', json.dumps(d, ensure_ascii=False, indent=1), sha, f'{verb} {tid} by {worker}' + (f': {note}' if note else ''))
    return f'{tid}: {status} OK' if r is not None else f'{tid}: FAILED {str(e)[:200]}'
def raw_at(path, commit):
    r, e = gh('GET', f'/repos/{CC_O}/{CC_R}/contents/{path}?ref={commit}')
    if r is None: return None
    return base64.b64decode(_d(r)['content']).decode()
def blob(b):
    r, e = gh('POST', f'/repos/{CC_O}/{CC_R}/git/blobs', {'content': base64.b64encode(b).decode(), 'encoding': 'base64'})
    return _d(r)['sha'] if r is not None else None
def done_commit(worker, tid, note, new_files=None, appends=None, replace=None, status='done', branch='pipeline', tries=6):
    new_files = new_files or {}; appends = appends or {}; replace = replace or {}
    e = None
    for i in range(tries):
        r, e = gh('GET', f'/repos/{CC_O}/{CC_R}/git/ref/heads/{branch}')
        if r is None: continue
        head = _d(r)['object']['sha']
        files = {}
        if tid:
            t = json.loads(raw_at(f'tasks/{tid}.json', head))
            if t.get('by') != worker and status != 'claimed': return f'{tid}: not your claim ({t.get("by")})'
            t.update(status=status, by=worker, at=now())
            if note is not None: t['note'] = note
            files[f'tasks/{tid}.json'] = json.dumps(t, ensure_ascii=False, indent=1)
        for p, txt in appends.items():
            cur = raw_at(p, head) or ''
            files[p] = cur.rstrip('\n') + '\n' + txt.strip('\n') + '\n'
        for p, pairs in replace.items():
            cur = files.get(p) or raw_at(p, head)
            for a, b in pairs:
                if a not in cur: return f'replace anchor not found in {p}: {a[:60]}'
                cur = cur.replace(a, b, 1)
            files[p] = cur
        files.update(new_files)
        shas = {}
        for p, txt in files.items():
            s = blob(txt.encode() if isinstance(txt, str) else txt)
            if not s: return f'blob error {p}'
            shas[p] = s
        rr, e = gh('GET', f'/repos/{CC_O}/{CC_R}/git/commits/{head}')
        base_tree = _d(rr)['tree']['sha']
        rr, e = gh('POST', f'/repos/{CC_O}/{CC_R}/git/trees', {'base_tree': base_tree, 'tree': [{'path': p, 'mode': '100644', 'type': 'blob', 'sha': s} for p, s in shas.items()]})
        if rr is None: return f'tree error {str(e)[:200]}'
        verb = {'done': 'done', 'claimed': 'claim', 'todo': 'release', 'blocked': 'release'}[status]
        msg = (f'{verb} {tid} by {worker}' + (f': {note}' if note else '')) if tid else note
        rr, e = gh('POST', f'/repos/{CC_O}/{CC_R}/git/commits', {'message': msg + CC_TR, 'tree': _d(rr)['sha'], 'parents': [head]})
        if rr is None: return f'commit error {str(e)[:200]}'
        c = _d(rr)['sha']
        rr, e = gh('PATCH', f'/repos/{CC_O}/{CC_R}/git/refs/heads/{branch}', {'sha': c, 'force': False})
        if rr is not None and (_d(rr).get('object') or {}).get('sha') == c: return f'pushed {c[:7]}: {sorted(files)}'
        time.sleep(2)
    return f'push failed: {str(e)[:300]}'
def drive_get(fid):
    s = requests.Session()
    for url in [f'https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t', f'https://drive.google.com/uc?export=download&id={fid}&confirm=t']:
        r = s.get(url, timeout=120)
        if r.status_code == 200 and not r.headers.get('Content-Type', '').startswith('text/html'): return r.content
    return None
def drive_tar(fid, sha):
    b = drive_get(fid)
    if b is None: return None, 'download failed'
    h = hashlib.sha256(b).hexdigest()
    if h != sha: return None, f'sha mismatch {h}'
    files = {}
    with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
        for m in t.getmembers():
            if m.isfile(): files[m.name.lstrip('./')] = t.extractfile(m).read()
    return files, 'ok'
