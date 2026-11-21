#!/usr/bin/env python3
"""One spec -> one product.  python3 run.py spec.json outdir [--pubkey pub.pem]
validate -> build + recalculate all 15 languages (template and demo) and verify -> listing pictures -> ZIP (+ pkg.fxp when a public
key is given) -> outdir/result.json:
  {ok, stage, errors[], warnings[], files{zip, fxp, sha256, images[]}, stats{...}}
errors[] are written for the architect: each names the spec element, the cell, the error and the cause."""
import sys, os, json, time, shutil, datetime as dt, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import validate
from verify import verify
from common import LANGS, file_base


def run(spec_path, outdir, pubkey=None):
    t0 = time.time(); outdir = os.path.abspath(outdir); os.makedirs(outdir, exist_ok=True)
    res = {'ok': False, 'stage': 'load', 'errors': [], 'warnings': [], 'files': {}, 'stats': {}, 'at': dt.datetime.now().astimezone().isoformat(timespec='seconds')}
    def done(stage=None):
        if stage: res['stage'] = stage
        res['stats']['seconds_total'] = round(time.time() - t0, 1)
        json.dump(res, open(os.path.join(outdir, 'result.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
        return res
    try:
        spec = json.load(open(spec_path, encoding='utf8'))
    except Exception as x:
        res['errors'] = [f'spec.json: {x}']; return done()
    res['id'] = spec.get('id') if isinstance(spec, dict) else None
    # 1. contract
    res['stage'] = 'validate'; t = time.time()
    errs = validate(spec); res['stats']['seconds_validate'] = round(time.time() - t, 1)
    if errs: res['errors'] = errs; return done()
    # 2. build every language and verify
    res['stage'] = 'verify'; work = os.path.join(outdir, 'work')
    if os.path.isdir(work): shutil.rmtree(work)
    rep = verify(spec, work)
    res['errors'], res['warnings'] = rep['errors'], rep['warnings']
    res['stats'].update({'seconds_verify': rep['seconds'], 'checks': rep['checks'], 'compare': rep['compare'], 'today': rep['today'],
                         'formulas': {n: j.get('formulas') for n, j in rep['jobs'].items()},
                         'job_seconds_max': max((j.get('seconds', 0) for j in rep['jobs'].values()), default=0)})
    if not rep['ok']: return done()
    # 3. pictures from the recalculated English demo
    res['stage'] = 'images'; t = time.time()
    try: from pictures import make_images  # v1.3: the board design
    except Exception: from images import make_images
    meta = json.load(open(rep['files']['meta_demo_en'], encoding='utf8'))
    imgs = make_images(spec, rep['files']['demo_en_recalc'], meta, os.path.join(outdir, 'images'), workdir=os.path.join(work, 'img'))
    res['files']['images'] = imgs
    # v1.4: every other language gets its own pictures, shot from its own recalculated demo (FX_PIC_LANGS=none turns it off)
    li = {}
    if os.environ.get('FX_PIC_LANGS', 'all') != 'none':
        want = LANGS[1:] if os.environ.get('FX_PIC_LANGS', 'all') == 'all' else [l for l in os.environ['FX_PIC_LANGS'].split(',') if l in LANGS[1:]]
        for l in want:
            v = rep['files'].get('demo_recalc', {}).get(l); mp = rep['files'].get('meta_demo', {}).get(l)
            if not v or not os.path.exists(v) or not mp or not os.path.exists(mp): res['warnings'].append(f'pictures {l}: no recalculated demo'); continue
            try: li[l] = make_images(spec, v, json.load(open(mp, encoding='utf8')), os.path.join(outdir, 'images', l), workdir=os.path.join(work, 'img-' + l), lang=l)
            except Exception as x: res['warnings'].append(f'pictures {l}: {type(x).__name__}: {x}'[:300])
    res['files']['images_i18n'] = li
    res['stats']['seconds_images'] = round(time.time() - t, 1)
    # 4. package
    res['stage'] = 'package'; t = time.time()
    from package import make_zip, encrypt, sha256
    z = make_zip(spec, rep['files']['templates'], rep['files']['demo_en'], os.path.join(outdir, f'{file_base(spec)}-15-languages.zip'))
    res['files']['zip'] = z; res['files']['zip_sha256'] = sha256(z); res['stats']['zip_mb'] = round(os.path.getsize(z) / 1e6, 2)
    if pubkey:
        blob = encrypt(open(z, 'rb').read(), open(pubkey, 'rb').read())
        fxp = os.path.join(outdir, 'pkg.fxp'); open(fxp, 'wb').write(blob)
        res['files']['fxp'] = fxp; res['files']['sha256'] = sha256(fxp)
    else:
        res['files']['fxp'] = None; res['files']['sha256'] = res['files']['zip_sha256']
    res['stats']['seconds_package'] = round(time.time() - t, 1)
    res['ok'] = True
    return done('done')


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(2)
    pk = a[a.index('--pubkey') + 1] if '--pubkey' in a else None
    try: r = run(a[0], a[1], pk)
    except Exception as x:
        r = {'ok': False, 'stage': 'crash', 'errors': [f'{type(x).__name__}: {x}', traceback.format_exc()[-1500:]]}
        os.makedirs(a[1], exist_ok=True); json.dump(r, open(os.path.join(a[1], 'result.json'), 'w'), indent=1)
    print(json.dumps({k: r.get(k) for k in ('ok', 'stage')} | {'errors': r.get('errors', [])[:20], 'files': r.get('files'),
                      'seconds': (r.get('stats') or {}).get('seconds_total')}, ensure_ascii=False, indent=1))
    sys.exit(0 if r.get('ok') else 1)
