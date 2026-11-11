#!/usr/bin/env python3
"""Translation on GitHub's free models (the owner, 2026-11-11: «قلل حد الاستخدام وارفع الانتاج» — no Claude usage for bulk translation).
usage: translate.py <suite> <lang> <out.json>
  tr/<suite>/todo.json        = [{"en","where","kind","max"}]  every text the suite prints
  tr/<suite>/done/<lang>.json = {"en": "translation"}           already approved (kept, never sent)
  tr/glossary/<lang>.json     = {"glossary": {...}, "examples": {...}}
  tr/RULES.md                 = the owner's translation rules
Writes <out.json> = done + new translations after every batch (so a stop keeps the work). Every answer is checked
(placeholders, length limits, sheet-name characters, leftover Latin in non-Latin scripts, the word 'compatible');
failures are retried with the reason, then on the next model."""
import sys, os, json, re, time, urllib.request, urllib.error

SUITE, LANG, OUT = sys.argv[1:4]
NAMES = {'ar': 'Arabic', 'fr': 'French', 'es': 'Spanish', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese (neutral, understood in Brazil and Portugal)',
         'tr': 'Turkish', 'nl': 'Dutch', 'ru': 'Russian', 'fa': 'Persian (Farsi)', 'ur': 'Urdu', 'hi': 'Hindi', 'zh': 'Simplified Chinese', 'id': 'Indonesian'}
MODELS = [m for m in os.environ.get('TR_MODELS', 'openai/gpt-4.1-mini,openai/gpt-4o-mini,openai/gpt-4.1,openai/gpt-4o,mistral-ai/mistral-medium-2505,deepseek/DeepSeek-V3-0324').split(',') if m]
TOKEN = os.environ['GITHUB_TOKEN']
PH = re.compile(r'\{[a-z_]+(?::[a-z0-9_.]+)?\}')
KEEP = {'WhatsApp', 'Excel', 'LibreOffice', 'Airbnb', 'Booking.com', 'Vrbo', 'IBAN', 'VAT', 'ID', 'm²', 'PDF', 'OK', 'xlsx', 'Microsoft', 'Windows', 'Mac', 'Calc'}
KEEPL = {k.lower() for k in KEEP}
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')
BUDGET = 2000 if NONLATIN else 2800          # English characters per request (output stays under 4000 tokens)

todo = json.load(open(f'tr/{SUITE}/todo.json', encoding='utf8'))
done = json.load(open(f'tr/{SUITE}/done/{LANG}.json', encoding='utf8')) if os.path.exists(f'tr/{SUITE}/done/{LANG}.json') else {}
if os.path.exists(OUT): done.update(json.load(open(OUT, encoding='utf8')))
G = json.load(open(next(f for f in (f'tr/{SUITE}/glossary/{LANG}.json', f'tr/glossary/{LANG}.json') if os.path.exists(f)), encoding='utf8'))  # a suite may carry its own glossary
rules = open('tr/RULES.md', encoding='utf8').read()

SYSTEM = (f"You are a senior native {NAMES[LANG]} localiser of business software (Excel templates for professionals, sold worldwide). "
          f"Translate English UI strings into {NAMES[LANG]}.\n\nThe owner's rules (obey all):\n{rules}\n\n"
          "Extra rules: answer ONLY with a JSON object mapping each input id (string) to its translation. Keep every {placeholder} exactly. "
          "\"max\" = hard character limit. kind \"sheet\" = Excel sheet name: at most the max, none of [ ] : * ? / \\ characters. "
          "kind \"list\" = short drop-down value. kind \"message\" = a warm, polite WhatsApp text. kind \"document\" = formal letter/contract text. "
          "Use exactly these approved terms (glossary, English → " + NAMES[LANG] + "):\n" + json.dumps(G['glossary'], ensure_ascii=False) +
          "\n\nApproved earlier translations of the same product (match their style and terms):\n" + json.dumps(G['examples'], ensure_ascii=False))


def check(x, v):
    en = x['en']
    if not isinstance(v, str) or not v.strip(): return 'empty'
    if sorted(PH.findall(en)) != sorted(PH.findall(v)): return 'placeholders must be exactly: ' + ' '.join(PH.findall(en)) or 'none'
    if x.get('max') and len(v) > x['max']: return f'too long: {len(v)} characters, the limit is {x["max"]}'
    if x['kind'] == 'sheet' and re.search(r'[\[\]:*?/\\]', v): return 'sheet names cannot contain [ ] : * ? / \\'
    if NONLATIN:
        lat = [w for w in re.findall(r'[A-Za-z][A-Za-z.²]+', PH.sub('', v)) if w.strip('.').lower() not in KEEPL]
        if lat: return 'English/Latin words left: ' + ' '.join(lat[:4])
    if re.search(r'compat|متوافق|kompatib|совмест|兼容|संगत|uyumlu|سازگار|مطابقت', v, re.I): return 'never use the word for "compatible"'
    if v.strip() == en.strip() and re.search(r'[A-Za-z]{4}', en) and en not in KEEP: return 'not translated'
    return None


def call(model, items, notes=None):
    body = [{'id': str(i), 'en': x['en'], 'kind': x['kind'], **({'max': x['max']} if x.get('max') else {}), **({'fix': notes[i]} if notes and i in notes else {})}
            for i, x in items]
    URL = os.environ.get('TR_URL') or 'https://models.github.ai/inference/chat/completions'
    req = urllib.request.Request(URL, method='POST', data=json.dumps({**json.loads(os.environ.get('TR_EXTRA') or '{}'),
        'model': model, 'temperature': 0.2, 'max_tokens': int(json.loads(os.environ.get('TR_EXTRA') or '{}').get('max_tokens', 4000)), **({} if os.environ.get('TR_URL') else {'response_format': {'type': 'json_object'}}),
        'messages': [{'role': 'system', 'content': SYSTEM},
                     {'role': 'user', 'content': f'Translate into {NAMES[LANG]}. Items with "fix" were rejected before for that reason: correct them.\n' + json.dumps(body, ensure_ascii=False)}]}).encode(),
        headers={**({} if os.environ.get('TR_URL') else {'Authorization': 'Bearer ' + TOKEN}), 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read().decode('utf8', 'replace')
        hdr = {k: v for k, v in r.headers.items() if 'ratelimit' in k.lower()}
    try:
        d = json.loads(raw)
        txt = d['choices'][0]['message']['content'].strip()
        txt = re.sub(r'^```(?:json)?|```$', '', txt).strip()
        return json.loads(txt)
    except Exception:
        print('  RAW', r.status, hdr, repr(raw[:400]), flush=True); raise


GL = {'zh': 'zh-CN', 'pt': 'pt'}
GTERMS = sorted([(k, v) for k, v in G.get('glossary', {}).items() if isinstance(v, str) and k.strip() and not re.search(r'[/()]', k + v)
                 and LANG not in ('ru',) and len(k) >= 4], key=lambda kv: -len(kv[0]))


def google(items):
    """Google's free web translator (no key). Placeholders become {0} {1} … and come back; one item per line."""
    import urllib.parse
    lines, maps = [], []
    for x in items:
        t = x.get('src') or x['en']; ph = PH.findall(t)
        for k, p_ in enumerate(ph): t = t.replace(p_, '{%d}' % k, 1)
        for en_t, tr_t in GTERMS:          # approved multi-word terms go through untouched (terminology, not literal MT)
            def sub(m, tr_t=tr_t):
                ph.append(tr_t[0].upper() + tr_t[1:] if m.group(0)[0].isupper() and tr_t[:1].isalpha() and tr_t[:1].lower() != tr_t[:1].upper() else tr_t)
                return '{%d}' % (len(ph) - 1)
            t = re.sub(r'(?<![A-Za-z{])' + re.escape(en_t) + r'(?:e?s)?(?![A-Za-z}])', sub, t, flags=re.I)
        lines.append(t.replace('\n', ' ¶ ')); maps.append(ph)
    data = urllib.parse.urlencode({'q': '\n'.join(lines)}).encode()
    url = f'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={GL.get(LANG, LANG)}&dt=t'
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode('utf8'))
    out = ''.join(seg[0] for seg in d[0] if seg and seg[0]).split('\n')
    if len(out) != len(items): raise ValueError(f'lines {len(out)} != {len(items)}')
    res = {}
    for i, (x, t, ph) in enumerate(zip(items, out, maps)):
        t = t.replace(' ¶ ', '\n').replace('¶', '\n').strip()
        t = re.sub(r'\{\s*(\d+)\s*\}', lambda m: ph[int(m.group(1))] if int(m.group(1)) < len(ph) else m.group(0), t)
        res[str(i)] = t
    return res


EDGE_L = {'zh': 'zh-Hans', 'pt': 'pt'}
_TOK = {}


def edge(items):
    """Microsoft Edge's free web translator (no account). Glossary terms go in as <mstrans:dictionary> so the engine keeps grammar and word order
    around them (plain placeholders broke the order: «Client Carte»); {placeholders} are protected with a notranslate span."""
    import html as _h
    if 'jwt' not in _TOK:
        try: _TOK['jwt'] = urllib.request.urlopen(urllib.request.Request('https://edge.microsoft.com/translate/auth', headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode().strip()
        except urllib.error.HTTPError as e: print('  auth HTTP', e.code, flush=True); raise
    texts = []
    for x in items:
        t = _h.escape(x.get('src') or x['en'], quote=False)
        toks = []
        def hold(m):
            toks.append('<span class="notranslate">' + m.group(0) + '</span>'); return '\x01%d\x01' % (len(toks) - 1)
        t = PH.sub(hold, t)
        for en_t, tr_t in GTERMS:
            def sub(m, tr_t=tr_t):
                v = tr_t[0].upper() + tr_t[1:] if m.group(0)[0].isupper() and tr_t[:1].isalpha() and tr_t[:1].lower() != tr_t[:1].upper() else tr_t
                toks.append('<mstrans:dictionary translation="' + _h.escape(v, quote=True) + '">' + m.group(0) + '</mstrans:dictionary>'); return '\x01%d\x01' % (len(toks) - 1)
            t = re.sub(r'(?<![A-Za-z\x01])' + re.escape(_h.escape(en_t, quote=False)) + r'(?:e?s)?(?![A-Za-z\x01])', sub, t, flags=re.I)
        t = re.sub('\x01(\\d+)\x01', lambda m: toks[int(m.group(1))], t)
        texts.append({'Text': t})
    url = 'https://api-edge.cognitive.microsofttranslator.com/translate?api-version=3.0&from=en&to=' + EDGE_L.get(LANG, LANG) + '&textType=html'
    req = urllib.request.Request(url, data=json.dumps(texts).encode(), headers={'Authorization': 'Bearer ' + _TOK['jwt'], 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: d = json.loads(r.read().decode('utf8'))
    except urllib.error.HTTPError as e:
        print('  translate HTTP', e.code, e.read()[:200], flush=True)
        if e.code == 401: _TOK.clear()
        raise
    res = {}
    for i, e in enumerate(d):
        v = e['translations'][0]['text']
        v = re.sub(r'</?(?:span|mstrans:dictionary|b|i)[^>]*>', '', v)
        res[str(i)] = _h.unescape(v).replace('\u00a0', ' ').strip()
    return res


TRAINER = {'ar', 'fa', 'ur', 'hi', 'zh', 'id', 'ru', 'es', 'de'}     # languages where «trainer» (not «coach») gives the right word
_RW = {}
_LASTREQ = [0.0]


def pre_build(x, sheetT):
    """English pre-edit (tr/<suite>/rewrite.py): ambiguous words replaced, sheet names inside texts held as placeholders that are filled with the
    translated sheet name, {placeholders} protected. Returns (text sent, list of values to put back)."""
    import importlib.util
    if 'rw' not in _RW:
        f = f'tr/{SUITE}/rewrite.py'
        spec = importlib.util.spec_from_file_location('rw', f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); _RW['rw'] = m.rewrite
        _RW['sheets'] = sorted({y['en'] for y in todo if y['kind'] == 'sheet' and ' ' in y['en']}, key=lambda s_: -len(s_))
    en, kind, t, toks = x['en'], x['kind'], x['en'], []
    if sheetT and kind != 'sheet':
        for sn in _RW['sheets']:
            if sn in t and sn in sheetT:
                def rp(m, sn=sn): toks.append(sheetT[sn]); return '\x02%d\x02' % (len(toks) - 1)
                t = re.sub(r'(?<![A-Za-z])' + re.escape(sn) + r'(?![A-Za-z])', rp, t)
    t = _RW['rw'](t, kind, LANG in TRAINER)
    ph = []
    def tk(m): ph.append(toks[int(m.group(1))]); return '{%d}' % (len(ph) - 1)
    t = re.sub('\x02(\\d+)\x02', tk, t)
    for p_ in PH.findall(t):
        ph.append(p_); t = t.replace(p_, '{%d}' % (len(ph) - 1), 1)
    return t, ph


def google2(items, sheetT=None):
    import urllib.parse
    lines, maps = [], []
    for x in items:
        t, ph = pre_build(x, sheetT); lines.append(t.replace('\n', ' ¶ ')); maps.append(ph)
    w = _LASTREQ[0] + float(os.environ.get('TR_SPACING', '8')) - time.time()
    if w > 0: time.sleep(w)
    _LASTREQ[0] = time.time()
    data = urllib.parse.urlencode({'q': '\n'.join(lines)}).encode()
    url = f'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={GL.get(LANG, LANG)}&dt=t'
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode('utf8'))
    out = ''.join(seg[0] for seg in d[0] if seg and seg[0]).split('\n')
    if len(out) != len(items): raise ValueError(f'lines {len(out)} != {len(items)}')
    res = {}
    for i, (t, ph) in enumerate(zip(out, maps)):
        t = t.replace(' ¶ ', '\n').replace('¶', '\n').strip()
        t = re.sub(r'\{\s*(\d+)\s*\}', lambda m: ph[int(m.group(1))] if int(m.group(1)) < len(ph) else m.group(0), t)
        res[str(i)] = t
    return res


if os.environ.get('TR_ENGINE') == 'google2':
    miss = [x for x in todo if x['en'] not in done]
    print(LANG, 'google2: todo', len(todo), 'done', len(done), 'missing', len(miss), flush=True)
    time.sleep(abs(hash(LANG)) % 60)
    bad, n = [], 0
    def batch(part, sheetT):
        global n
        for attempt in range(400):
            try: res = google2(part, sheetT); break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    if attempt % 10 == 0: print('  HTTP 429, waiting', attempt, flush=True)
                    time.sleep(120)
                else: print('  HTTP', e.code, flush=True); time.sleep(20)
                res = None
            except Exception as e:
                print('  error', repr(e)[:200], flush=True); res = None; time.sleep(20)
        for j, x in enumerate(part):
            v = (res or {}).get(str(j)); why = check(x, v)
            if why: bad.append({'en': x['en'], 'kind': x['kind'], 'max': x['max'], 'mt': v, 'why': why})
            done[x['en']] = v if v else done.get(x['en'], ''); n += 1 if not why else 0
            if not v: done.pop(x['en'], None)
        json.dump(done, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    sh = [x for x in miss if x['kind'] == 'sheet']
    for k in range(0, len(sh), 30): batch(sh[k:k + 30], None)
    sheetT = {x['en']: done[x['en']] for x in todo if x['kind'] == 'sheet' and x['en'] in done}
    rest = [x for x in miss if x['kind'] != 'sheet']
    for k in range(0, len(rest), 30): batch(rest[k:k + 30], sheetT)
    json.dump(bad, open(OUT.replace('.json', '.bad.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    print(LANG, 'google2 done', n, 'bad', len(bad), flush=True)
    sys.exit(0)


if os.environ.get('TR_ENGINE') in ('google', 'edge'):
    ENG = edge if os.environ.get('TR_ENGINE') == 'edge' else google
    miss = [x for x in todo if x['en'] not in done]
    print(LANG, 'google: todo', len(todo), 'done', len(done), 'missing', len(miss), flush=True)
    bad, n = [], 0
    for k in range(0, len(miss), 30 if ENG is google else 20):
        part = miss[k:k + (30 if ENG is google else 20)]
        for attempt in range(5):
            try: res = ENG(part); break
            except urllib.error.HTTPError as e:
                print('  HTTP', e.code, flush=True); time.sleep(60 if e.code == 429 else 10); res = None
            except Exception as e:
                print('  error', repr(e)[:200], flush=True); res = None
                if 'lines' in repr(e) and len(part) > 1:          # line split failed: go one by one
                    res = {}
                    for j, x in enumerate(part):
                        try: res[str(j)] = ENG([x])['0']
                        except Exception as e2: print('   single', repr(e2)[:100])
                        time.sleep(0.5)
                    break
                time.sleep(10)
        for j, x in enumerate(part):
            v = (res or {}).get(str(j)); why = check(x, v)
            if why: bad.append({'en': x['en'], 'kind': x['kind'], 'max': x['max'], 'mt': v, 'why': why})
            else: done[x['en']] = v; n += 1
        json.dump(done, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=0)
        time.sleep(1.5)
    json.dump(bad, open(OUT.replace('.json', '.bad.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    print(LANG, 'google done', n, 'bad', len(bad), flush=True)
    sys.exit(0)

miss = [x for x in todo if x['en'] not in done]
print(LANG, 'todo', len(todo), 'done', len(done), 'missing', len(miss), flush=True)
batches, cur, size = [], [], 0
for x in miss:
    if cur and size + len(x['en']) > BUDGET: batches.append(cur); cur, size = [], 0
    cur.append(x); size += len(x['en'])
if cur: batches.append(cur)

dead = set()          # models out of quota today
stats = {'ok': 0, 'retry': 0, 'failed': 0}
for bi, batch in enumerate(batches):
    pend = list(enumerate(batch)); notes = {}
    for attempt in range(4):
        if not pend: break
        live = [m for m in MODELS if m not in dead]
        if not live: print('all models out of quota — stopping; the work so far is saved', flush=True); break
        model = live[0] if attempt < 2 else live[min(1, len(live) - 1)]
        try:
            res = call(model, pend, notes)
        except urllib.error.HTTPError as e:
            msg = e.read().decode('utf8', 'replace')[:300]
            ra = int(e.headers.get('retry-after') or 0)
            print(f'  {model} HTTP {e.code} retry-after {ra}: {msg}', flush=True)
            if e.code == 429 and ra > 600: dead.add(model)
            elif e.code in (429, 500, 502, 503, 504): time.sleep(max(ra, 20))
            elif e.code in (400, 413): time.sleep(2)
            else: dead.add(model)
            continue
        except Exception as e:
            print(f'  {model} error {e!r}', flush=True); time.sleep(10); continue
        left = []
        for i, x in pend:
            v = res.get(str(i))
            why = check(x, v)
            if why: left.append((i, x)); notes[i] = why
            else: done[x['en']] = v.strip(); stats['ok'] += 1
        stats['retry'] += len(left); pend = left
        time.sleep(4)          # stay under the per-minute limit
    stats['failed'] += len(pend)
    for i, x in pend: print('  FAILED', repr(x['en'][:70]), notes.get(i), flush=True)
    json.dump(done, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    print(f'batch {bi + 1}/{len(batches)} {stats}', flush=True)
    if not [m for m in MODELS if m not in dead]: break
miss = [x for x in todo if x['en'] not in done]
print(LANG, 'FINAL missing', len(miss), stats, flush=True)
