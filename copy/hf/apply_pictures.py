import json, sys
sys.path.insert(0, '/home/claude/work/copy/hf')
from picture import PIC
for n, p in PIC.items():
    f = f'/home/claude/work/hf/hf{n}.en.json'
    try:
        raw = open(f).read()
    except FileNotFoundError:
        json.dump(p, open('/home/claude/work/copy/hf/hf6_picture.json', 'w'), indent=1, ensure_ascii=False)
        print(n, 'file missing: picture texts saved to copy/hf/hf6_picture.json'); continue
    d = json.loads(raw)
    assert json.dumps(d, indent=1, ensure_ascii=False) == raw, f'format differs {n}'
    assert len(d['signature']) == len(p['sig']), (n, len(d['signature']), len(p['sig']))
    d['tagline'] = p['tagline']
    for s, (nm, why) in zip(d['signature'], p['sig']):
        s['name'], s['why'] = nm, why
    open(f, 'w').write(json.dumps(d, indent=1, ensure_ascii=False))
    print(n, 'ok')
