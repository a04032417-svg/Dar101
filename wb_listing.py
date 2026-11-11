# Workbench: translate the suite listing (store pages) into 14 languages with the free invoke_llm; validated limits
import json, re, os, concurrent.futures as cf
LIMITS = {'name': 40, 'title': 140, 'headline': 80, 'seo_title': 70, 'seo_description': 160}
FIELD = {'ar': 'المحاسبة ومسك الدفاتر'}


def lcheck(en, d, lang):
    p = []
    for k, m in LIMITS.items():
        if not isinstance(d.get(k), str) or not d[k].strip(): p.append(f'{k} missing')
        elif len(d[k]) > m: p.append(f'{k} is {len(d[k])} characters, must be at most {m}')
    t = d.get('tags')
    if not isinstance(t, list) or len(t) != 13: p.append('tags must be a list of exactly 13')
    elif any(len(x) > 20 for x in t): p.append('every tag at most 20 characters: ' + ', '.join(x for x in t if len(x) > 20))
    elif len({x.casefold() for x in t}) != 13: p.append('tags must be all different')
    ds = d.get('description') or ''
    if not (900 <= len(ds) <= 2500): p.append(f'description is {len(ds)} characters, must be 900 to 2500')
    if not isinstance(d.get('features'), list) or len(d['features']) != len(en['features']): p.append(f'features must be a list of exactly {len(en["features"])}')
    elif any(len(x) > 80 for x in d['features']): p.append('every feature at most 80 characters')
    if not isinstance(d.get('faq'), list) or len(d['faq']) != len(en['faq']) or any(not isinstance(x, dict) or set(x) != {'q', 'a'} for x in d['faq']): p.append('faq must keep the same items with keys q and a')
    if '{files}' not in (d.get('stats_note') or '') or '{pages}' not in (d.get('stats_note') or ''): p.append('stats_note must keep {files} and {pages}')
    blob = json.dumps([d.get(k) for k in d if k not in ('stats_note',)] + [re.sub(r'\{[a-z]+\}', '', d.get('stats_note') or '')], ensure_ascii=False)
    if re.search(r'compat|متوافق|kompatib|совмест|兼容|संगत|uyumlu|سازگار', blob, re.I): p.append('never use the word compatible')
    if re.search(r'Excel\s*(19|20)\d\d|365', blob): p.append('never write an Excel version or 365')
    if lang in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru'):
        lat = set(w for w in re.findall(r'[A-Za-z]{3,}', re.sub(r'\{[^}]*\}', '', blob)) if w.lower() not in {'whatsapp', 'excel', 'libreoffice', 'microsoft', 'windows', 'mac', 'calc', 'xlsx', 'vat', 'pdf'})
        if lat: p.append('Latin words left: ' + ' '.join(sorted(lat)[:8]))
    return p


def listing_one(en, lang, tries=4):
    base = (f"Translate this store listing of an Excel product for accountants and bookkeepers into {LANGS[lang]}, as a native professional copywriter of that language would write it "
            "(natural, persuasive, precise accounting terms, gender-neutral words for people). Keep the JSON structure and keys exactly; translate only the values. "
            "The 'name' and 'title' must name the FIELD 'accounting and bookkeeping' itself in the target language (like 'Accounting and Bookkeeping Excel Suite'), not the people ('for accountants'). Keep {files} and {pages} as they are. "
            "Never write the word for 'compatible' and never an Excel version. Limits: name<=40, title<=140, headline<=80, seo_title<=70, seo_description<=160 characters, "
            "exactly 13 tags each <=20 characters (search words a buyer of that language would type), description 900-2500 characters (keep the paragraphs), features <=80 characters each. "
            + (f"Use the field name '{FIELD[lang]}'. " if lang in FIELD else '') + "Return only the JSON.\n")
    note = ''
    for i in range(tries):
        t = llm(base + note + json.dumps(en, ensure_ascii=False))
        m = re.search(r'\{.*\}', t, re.S)
        try: d = json.loads(m[0]) if m else None
        except Exception: d = None
        if not isinstance(d, dict): note = 'Previous answer was not valid JSON. '; continue
        p = lcheck(en, d, lang)
        if not p: return d, []
        note = 'Fix these problems of your previous answer: ' + '; '.join(p) + '. '
    return d, p


def listings(en, langs=None):
    langs = langs or list(LANGS)
    with cf.ThreadPoolExecutor(len(langs)) as ex: res = dict(zip(langs, ex.map(lambda l: listing_one(en, l), langs)))
    out = {l: r[0] for l, r in res.items()}; probs = {l: r[1] for l, r in res.items() if r[1]}
    json.dump(out, open(os.path.expanduser('~/ac_listing.json'), 'w', encoding='utf8'), ensure_ascii=False)
    return out, probs
