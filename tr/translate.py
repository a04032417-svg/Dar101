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
KEEP = {'WhatsApp', 'Excel', 'LibreOffice', 'Airbnb', 'Booking.com', 'Vrbo', 'IBAN', 'VAT', 'ID', 'm²', 'PDF', 'OK', 'xlsx', 'Microsoft'}
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')
BUDGET = 2000 if NONLATIN else 2800          # English characters per request (output stays under 4000 tokens)

todo = json.load(open(f'tr/{SUITE}/todo.json', encoding='utf8'))
done = json.load(open(f'tr/{SUITE}/done/{LANG}.json', encoding='utf8')) if os.path.exists(f'tr/{SUITE}/done/{LANG}.json') else {}
if os.path.exists(OUT): done.update(json.load(open(OUT, encoding='utf8')))
G = json.load(open(f'tr/glossary/{LANG}.json', encoding='utf8'))
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
        lat = [w for w in re.findall(r'[A-Za-z][A-Za-z.²]+', PH.sub('', v)) if w not in KEEP]
        if lat: return 'English/Latin words left: ' + ' '.join(lat[:4])
    if re.search(r'compat|متوافق|kompatib|совмест|兼容|संगत|uyumlu|سازگار|مطابقت', v, re.I): return 'never use the word for "compatible"'
    if v.strip() == en.strip() and re.search(r'[A-Za-z]{4}', en) and en not in KEEP: return 'not translated'
    return None


def call(model, items, notes=None):
    body = [{'id': str(i), 'en': x['en'], 'kind': x['kind'], **({'max': x['max']} if x.get('max') else {}), **({'fix': notes[i]} if notes and i in notes else {})}
            for i, x in items]
    req = urllib.request.Request('https://models.github.ai/inference/chat/completions', method='POST', data=json.dumps({
        'model': model, 'temperature': 0.2, 'max_tokens': 4000, 'response_format': {'type': 'json_object'},
        'messages': [{'role': 'system', 'content': SYSTEM},
                     {'role': 'user', 'content': f'Translate into {NAMES[LANG]}. Items with "fix" were rejected before for that reason: correct them.\n' + json.dumps(body, ensure_ascii=False)}]}).encode(),
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json', 'Accept': 'application/vnd.github+json'})
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


if SUITE == 'probe':
    import subprocess
    body = json.dumps({'model': 'openai/gpt-4.1-mini', 'messages': [{'role': 'user', 'content': 'Say hi in Arabic as JSON {"t": ...}'}]})
    for url in ('https://models.github.ai/inference/chat/completions', 'https://models.inference.ai.azure.com/chat/completions'):
        r = subprocess.run(['curl', '-sS', '-i', '-X', 'POST', url, '-H', 'Authorization: Bearer ' + TOKEN, '-H', 'Content-Type: application/json',
                            '-H', 'Accept: application/vnd.github+json', '-H', 'X-GitHub-Api-Version: 2022-11-28', '-d', body], capture_output=True, text=True)
        print('PROBE', url, (r.stdout + r.stderr)[:1200], flush=True)
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
