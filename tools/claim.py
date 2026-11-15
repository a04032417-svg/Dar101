#!/usr/bin/env python3
"""Task board for several Claude conversations/accounts working on the pipeline at the same time, with no duplicated work.
One file per task in tasks/<id>.json: {"id","slot","stage","part","deps":[ids],"needs":[caps],"status":"todo|claimed|done|blocked",
"by","at","note"}. A claim is a git commit pushed to branch `pipeline`: git rejects the second of two simultaneous claims.

  python3 tools/claim.py list                         # board summary
  python3 tools/claim.py next <worker> [--can web,whop,shopify,drive,chrome,ci] [--max 3]   # claim up to --max ready tasks, prints them
  python3 tools/claim.py beat <worker> <id>           # refresh the claim time of a long task (every ~45 min)
  python3 tools/claim.py done <worker> <id> [note]    # commit ALL your current changes + mark done, push (retries)
  python3 tools/claim.py release <worker> <id> [note] # give a task back (status todo) — or blocked: --blocked
A claim older than TTL minutes (150) without a beat can be taken over by another worker. Run from /home/claude/work (the clone of branch pipeline).
"""
import json, os, subprocess, sys, time, glob, datetime
TTL = 150
os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')
def sh(*a, check=True):
    r = subprocess.run(a, capture_output=True, text=True)
    if check and r.returncode: raise RuntimeError(' '.join(a) + '\n' + r.stdout + r.stderr)
    return r
def now(): return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def age_min(t):
    try: return (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)).total_seconds() / 60
    except Exception: return 1e9
def load():
    T = {}
    for f in glob.glob('tasks/*.json'):
        d = json.load(open(f)); T[d['id']] = d
    return T
def save(d): json.dump(d, open(f"tasks/{d['id']}.json", 'w'), ensure_ascii=False, indent=1)
def sync():
    sh('git', 'fetch', '-q', 'origin', 'pipeline')
    r = sh('git', 'rebase', '-q', '--autostash', 'origin/pipeline', check=False)
    if r.returncode:
        sh('git', 'rebase', '--abort', check=False); raise RuntimeError('rebase conflict\n' + r.stderr)
def push(msg, paths=None):
    sh('git', 'add', '-A', *(paths or ['.']))
    if sh('git', 'diff', '--cached', '--quiet', check=False).returncode:
        sh('git', 'commit', '-q', '-m', msg + '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: pipeline worker')
    for _ in range(6):
        if sh('git', 'push', '-q', 'origin', 'HEAD:pipeline', check=False).returncode == 0: return True
        sh('git', 'fetch', '-q', 'origin', 'pipeline')
        if sh('git', 'rebase', '-q', '--autostash', 'origin/pipeline', check=False).returncode:
            sh('git', 'rebase', '--abort', check=False); return False
        time.sleep(2)
    return False
def ready(t, T, caps):
    if t['status'] == 'done' or t['status'] == 'blocked': return False
    if t['status'] == 'claimed' and age_min(t.get('at', '')) < TTL: return False
    if any(T.get(d, {}).get('status') != 'done' for d in t.get('deps', [])): return False
    return all(n in caps for n in t.get('needs', []))
def main():
    a = sys.argv[1:]
    if not a or a[0] == 'list':
        T = load()
        for k in sorted(T, key=lambda k: (T[k]['slot'], k)):
            t = T[k]; print(f"{k:22} {t['status']:8} {t.get('by',''):18} {t.get('at','')}  {t.get('note','')[:60]}")
        return
    cmd, worker = a[0], a[1]
    if cmd == 'next':
        caps = set(); mx = 1
        if '--can' in a: caps = set(a[a.index('--can') + 1].split(','))
        if '--max' in a: mx = int(a[a.index('--max') + 1])
        got = []
        for _ in range(8):
            sync(); T = load()
            cand = [t for t in sorted(T.values(), key=lambda t: (t['slot'], t['id'])) if ready(t, T, caps)][:mx - len(got)]
            if not cand: break
            for t in cand: t.update(status='claimed', by=worker, at=now()); save(t)
            if push(f"claim {','.join(t['id'] for t in cand)} by {worker}", ['tasks']):
                got += [t['id'] for t in cand]
                if len(got) >= mx: break
            else:
                sh('git', 'reset', '-q', '--soft', 'origin/pipeline'); sh('git', 'checkout', 'origin/pipeline', '--', 'tasks')
        print(json.dumps([load()[i] for i in got], ensure_ascii=False, indent=1) if got else 'NO READY TASK')
        return
    tid = a[2]; note = ' '.join(x for x in a[3:] if not x.startswith('--'))
    T = load(); t = T[tid]
    if t.get('by') != worker and cmd != 'done': print('not your claim'); return
    if cmd == 'beat': t['at'] = now()
    elif cmd == 'done': t.update(status='done', by=worker, at=now(), note=note or t.get('note', ''))
    elif cmd == 'release': t.update(status='blocked' if '--blocked' in a else 'todo', at=now(), note=note)
    save(t)
    ok = push(f"{cmd} {tid} by {worker}" + (f": {note}" if note else ''))
    print('pushed' if ok else 'PUSH FAILED (conflict): fetch, fix by hand, push again')
if __name__ == '__main__': main()
