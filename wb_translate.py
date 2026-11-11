# Workbench translator for Dar suites (runs inside the Composio workbench; uses the free invoke_llm). Loaded with exec(requests.get(RAW+'wb_translate.py').text)
import requests, json, re, time, os, concurrent.futures as cf, threading
RAW = 'https://raw.githubusercontent.com/a04032417-svg/Dar101/tr-out/ac-in/'
OUT = os.path.expanduser('~/ac_out'); os.makedirs(OUT, exist_ok=True)
LANGS = {'ar': 'Modern Standard Arabic (neutral, understood in every Arab country)', 'fa': 'Persian (Farsi, Iran)', 'ur': 'Urdu (Pakistan)', 'hi': 'Hindi (Devanagari)',
         'zh': 'Simplified Chinese', 'ru': 'Russian', 'tr': 'Turkish', 'id': 'Indonesian', 'fr': 'French (international)', 'es': 'Spanish (international, neutral)',
         'de': 'German', 'it': 'Italian', 'pt': 'Brazilian Portuguese', 'nl': 'Dutch'}
PH = re.compile(r'\{[a-z_]+(?::[a-z0-9_.]+)?\}')
KEEP = {'whatsapp', 'excel', 'libreoffice', 'iban', 'vat', 'id', 'pdf', 'ok', 'xlsx', 'kpi', 'swift', 'sku', 'fifo', 'ebitda', 'usd', 'gst', 'pos', 'qr', 'sms', 'bic', 'ytd', 'mtd', 'dscr', 'roi', 'cogs', 'pbc', 'ocr', 'pdf', 'csv', 'wip', 'ar', 'ap', 'tds', 'eoy', 'eos', 'gl', 'jv', 'rpa', 'ifrs', 'gaap', 'sepa', 'ach'}
LATIN_LANGS = ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')
_lock = threading.Lock()


def get_todo(name='todo.json'):
    items = requests.get(RAW + name, timeout=60).json(); by = {}
    for x in items:
        e = by.get(x['en'])
        if not e: by[x['en']] = dict(x)
        else:
            if x.get('max') and (not e.get('max') or x['max'] < e['max']): e['max'] = x['max']
            if x['kind'] == 'sheet': e['kind'] = 'sheet'
    return list(by.values())


def check(x, v, lang):
    en = x['en']
    if not isinstance(v, str) or not v.strip(): return 'empty'
    if sorted(PH.findall(en)) != sorted(PH.findall(v)): return 'placeholders must be kept exactly: ' + ' '.join(PH.findall(en))
    if x.get('max') and len(v) > x['max']: return f'too long {len(v)}>{x["max"]}: shorten it'
    if x['kind'] == 'sheet' and re.search(r'[\[\]:*?/\\]', v): return 'sheet name must not contain [ ] : * ? / \\'
    if lang in LATIN_LANGS:
        vv = re.sub(r'\{[^}]*\}', '', v)
        lat = [w for w in re.findall(r'[A-Za-z][A-Za-z.²]+', vv) if w.strip('.').lower() not in KEEP]
        if lat: return 'Latin letters left: ' + ' '.join(lat[:4]) + ' (write in the native script)'
    if re.search(r'compat|متوافق|kompatib|совмест|兼容|संगत|uyumlu|سازگار', v, re.I): return 'never use the word compatible'
    if v.strip() == en.strip() and re.search(r'[A-Za-z]{4}', en) and lang not in ('fr', 'es', 'de', 'it', 'pt', 'nl', 'id', 'tr'): return 'not translated'
    return None


RULES = """You are a senior professional translator for Excel templates that are sold worldwide to accountants and bookkeepers (independent practices serving small-business clients).
Translate from English into {lang}. Every line must read as if a native accountant wrote it: the standard, widely understood professional term of the language, not word-for-word, not a rare regional word.
Rules: 1) Placeholders such as {{name}}, {{amount}}, {{col:invoices.due}} stay exactly as written, in a natural position. 2) kind=sheet: a short sheet name, at most 31 characters, none of [ ] : * ? / \\ . 3) Respect max (characters). 4) People words are gender-neutral or the standard generic form (never a feminine job title unless the English says so). 5) Native script only (Arabic, Persian, Urdu, Hindi, Chinese, Russian); keep Latin only for WhatsApp, Excel, LibreOffice, IBAN, VAT, PDF, KPI, ID codes. 6) Labels and titles: concise, no full stop. Sentences, documents and WhatsApp messages: natural, polite, professional. List values are short drop-down choices. 7) Never write the word for 'compatible' and never an Excel version. 8) Numbers, %, dates and codes stay as they are. 9) Context: accounting and bookkeeping practice (clients, engagements, invoices, ledgers, tax returns, payroll, year-end), NOT other fields.
Glossary to use consistently:
{glossary}
When an item lists [sheet names inside], the sentence refers to those sheets: write exactly the given translated sheet name. Do not copy the bracket note itself.
Output exactly one line per item in the form: index|translation . No other text, no quotes, no explanations."""

GLOSS_TERMS = ['client', 'engagement', 'invoice', 'credit note', 'receivable', 'payable', 'ledger', 'journal entry', 'trial balance', 'bank reconciliation', 'chart of accounts',
 'balance sheet', 'profit and loss', 'cash flow', 'budget', 'forecast', 'sales tax or VAT', 'income tax', 'tax return', 'filing deadline', 'payroll', 'payslip', 'timesheet',
 'work in progress', 'retainer', 'write-off', 'overdue', 'ageing', 'depreciation', 'fixed asset', 'accrual', 'prepayment', 'year-end', 'annual accounts', 'audit', 'month-end close',
 'bookkeeper', 'accountant', 'staff member', 'partner', 'fee', 'quote', 'proposal', 'engagement letter', 'onboarding', 'renewal', 'lead', 'referral', 'utilisation', 'realisation',
 'margin', 'gross margin', 'net profit', 'break-even', 'working capital', 'equity', 'liability', 'asset', 'expense', 'income', 'supplier', 'customer', 'petty cash', 'owner drawings',
 'dividend', 'loan', 'interest', 'penalty', 'extension', 'withholding tax', 'deduction', 'overtime', 'end-of-service payment', 'pension', 'leave balance', 'dashboard', 'checklist']


def llm(q, tries=3):
    for i in range(tries):
        try:
            r = invoke_llm(q)
            t = r[0] if isinstance(r, tuple) else r
            if t: return str(t)
        except Exception as e:
            time.sleep(2 + i * 3)
    return ''


def make_gloss(lang):
    p = f'{OUT}/gloss_{lang}.json'
    if os.path.exists(p): return json.load(open(p, encoding='utf8'))
    q = f"Translate these accounting and bookkeeping terms into {LANGS[lang]} using the standard professional term accountants use. Output one line per term: term|translation . No other text.\n" + '\n'.join(GLOSS_TERMS)
    g = {}
    for line in llm(q).split('\n'):
        if '|' in line:
            a, b = line.split('|', 1); g[a.strip()] = b.strip()
    json.dump(g, open(p, 'w', encoding='utf8'), ensure_ascii=False)
    return g


def parse(txt, n0, n):
    out = {}
    for line in txt.split('\n'):
        m = re.match(r'\s*(\d+)\s*\|(.*)$', line)
        if m: out[int(m[1])] = m[2].strip()
    return out


SHEETS = {}  # lang -> {english sheet name: translated sheet name}


def sheet_refs(en, lang):
    m = SHEETS.get(lang) or {}
    return [(s, m[s]) for s in sorted(m, key=len, reverse=True) if len(s) > 3 and s != en and re.search(r'(?<![A-Za-z])' + re.escape(s) + r'(?![A-Za-z])', en)][:6]


def do_batch(lang, batch, gl, extra=''):
    lines = []
    for i, x in enumerate(batch):
        refs = sheet_refs(x['en'], lang) if x['kind'] != 'sheet' else []
        note = (' [sheet names inside: ' + '; '.join(f'"{a}" = "{b}"' for a, b in refs) + ' (use exactly these)]') if refs else ''
        lines.append(f"{i}|kind={x['kind']}" + (f"|max={x['max']}" if x.get('max') else '') + '|' + x['en'] + note)
    q = RULES.format(lang=LANGS[lang], glossary='\n'.join(f'{k} = {v}' for k, v in gl.items())) + extra + '\nItems (index|kind|max|text):\n' + '\n'.join(lines)
    got = parse(llm(q), 0, len(batch))
    return {batch[i]['en']: got[i] for i in got if i < len(batch)}


def load_state(lang):
    p = f'{OUT}/{lang}.json'
    return json.load(open(p, encoding='utf8')) if os.path.exists(p) else {}


def save_state(lang, d):
    with _lock: json.dump(d, open(f'{OUT}/{lang}.json', 'w', encoding='utf8'), ensure_ascii=False)


def run(items, langs=None, budget=140, size=60, workers=14):
    """translate every missing/invalid string; returns after `budget` seconds (call again until done)"""
    t0 = time.time(); langs = langs or list(LANGS); by_en = {x['en']: x for x in items}
    jobs = []
    with cf.ThreadPoolExecutor(len(langs)) as gp: gls = dict(zip(langs, gp.map(make_gloss, langs)))
    for l in langs:
        gl = gls[l]; st = load_state(l)
        todo = [x for x in items if x['en'] not in st]
        # long items first so batches have similar size
        for i in range(0, len(todo), size): jobs.append((l, todo[i:i + size], gl))
    pool = cf.ThreadPoolExecutor(workers)
    res = {}

    def work(j):
        l, batch, gl = j
        if time.time() - t0 > budget: return
        r = do_batch(l, batch, gl); st = load_state(l)
        bad = []
        for x in batch:
            v = r.get(x['en'])
            w = check(x, v, l) if v is not None else 'missing'
            if w is None: st[x['en']] = v
            else: bad.append((x, w, v))
        # retry the bad ones in small groups with the exact complaint
        for k in range(0, len(bad), 8):
            if time.time() - t0 > budget + 25: break
            grp = bad[k:k + 8]
            note = '\nPrevious attempt problems (fix them):\n' + '\n'.join(f"{i}: {w}" for i, (x, w, v) in enumerate(grp))
            r2 = do_batch(l, [g[0] for g in grp], gl, note)
            for i, (x, w, v) in enumerate(grp):
                v2 = r2.get(x['en'])
                if v2 is not None and check(x, v2, l) is None: st[x['en']] = v2
        with _lock:
            cur = load_state(l); cur.update(st); json.dump(cur, open(f'{OUT}/{l}.json', 'w', encoding='utf8'), ensure_ascii=False)
    futs = [pool.submit(work, j) for j in jobs]
    cf.wait(futs, timeout=budget + 30)
    pool.shutdown(wait=False, cancel_futures=True)
    return status(items, langs)


def status(items, langs=None):
    langs = langs or list(LANGS); out = {}
    for l in langs:
        st = load_state(l); out[l] = sum(1 for x in items if x['en'] in st)
    return {'total': len(items), 'done': out}


def sheet_map(items, lang):
    st = load_state(lang)
    SHEETS[lang] = {x['en']: st[x['en']] for x in items if x['kind'] == 'sheet' and x['en'] in st}


def dup_sheets(items, lang):
    st = load_state(lang); bad = []
    wbs = {}
    for x in items:
        if x['kind'] == 'sheet' and x['en'] in st:
            for wb in x.get('wbs') or [x['where'].split(':')[0]]:
                wbs.setdefault(wb, {}).setdefault(st[x['en']].casefold().strip(), []).append(x)
    for wb, m in wbs.items():
        for v, xs in m.items():
            if len({y['en'] for y in xs}) > 1: bad.append((wb, v, [y['en'] for y in xs]))
    return bad


def fix_dups(items, lang, gl):
    bad = dup_sheets(items, lang); st = load_state(lang); by = {x['en']: x for x in items}
    for wb, v, ens in bad:
        grp = [by[e] for e in ens[1:]]
        note = '\nThese sheet names must be DIFFERENT from "' + v + '" (another sheet already uses it) and different from each other; keep the meaning, at most 31 characters.'
        r = do_batch(lang, grp, gl, note)
        for x in grp:
            w = r.get(x['en'])
            if w and check(x, w, lang) is None and w.casefold().strip() != v: st[x['en']] = w
    save_state(lang, st)
    return len(bad)


def run_all(items, langs=None, budget=140, size=30, workers=48):
    """phase 1 sheet names, phase 2 everything else (with the sheet map), then duplicate sheet names; call again until done"""
    t0 = time.time(); langs = langs or list(LANGS)
    sh = [x for x in items if x['kind'] == 'sheet']
    s = run(sh, langs, budget=min(60, budget), size=size, workers=workers)
    need = [l for l in langs if s['done'][l] < len(sh)]
    for l in langs: sheet_map(items, l)
    with cf.ThreadPoolExecutor(len(langs)) as gp: gls = dict(zip(langs, gp.map(make_gloss, langs)))
    ndup = {l: fix_dups(items, l, gls[l]) for l in langs if l not in need}
    for l in langs: sheet_map(items, l)
    rest = [x for x in items if x['kind'] != 'sheet']
    left = budget - (time.time() - t0)
    if left > 20: run(rest, [l for l in langs if l not in need], budget=left, size=size, workers=workers)
    out = status(items, langs); out['dup_sheets_fixed'] = ndup; out['dups_left'] = {l: len(dup_sheets(items, l)) for l in langs}
    return out


def bundle(items, name):
    data = {l: {x['en']: load_state(l)[x['en']] for x in items if x['en'] in load_state(l)} for l in LANGS}
    p = os.path.expanduser(f'~/{name}.json'); json.dump(data, open(p, 'w', encoding='utf8'), ensure_ascii=False)
    return upload_local_file(p)
