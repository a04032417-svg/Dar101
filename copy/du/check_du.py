#!/usr/bin/env python3
"""Check the Doula Business suite English copy and picture texts: limits, banned words, counts equal the real counts."""
import json, re
W = '/home/claude/work/'
c = json.load(open(W + 'copy/du/en.json', encoding='utf8')); m = json.load(open(W + 'copy/wd/en.json', encoding='utf8'))
fin = json.load(open(W + 'du/listing/final/en.json', encoding='utf8'))
bad = []
def chk(ok, msg):
    if not ok: bad.append(msg)
chk(set(c) == set(m), 'keys differ from wd: %s' % sorted(set(c) ^ set(m)))
chk(c == fin, 'listing/final/en.json is not a copy')
for k, l in [('name', 40), ('title', 140), ('headline', 80), ('seo_title', 70), ('seo_description', 160)]:
    chk(len(c[k]) <= l, f'{k} {len(c[k])}>{l}')
chk(900 <= len(c['description']) <= 2500, 'description length %d' % len(c['description']))
chk(len(c['description'].split('\n')[0]) <= 200, 'hook line too long')
t = c['tags']; chk(len(t) == 13 and len({x.lower() for x in t}) == 13 and max(map(len, t)) <= 20, 'tags')
chk(len(c['features']) == 12 and max(map(len, c['features'])) <= 90, 'features')
chk(len(c['faq']) == 6, 'faq count')
fq = ' '.join(q['q'] + ' ' + q['a'] for q in c['faq'])
for need in ('Google Sheets', 'currency', 'solo doula', 'backup', 'agency split', '14 days'):
    chk(need.lower() in fq.lower(), 'faq lacks ' + need)
chk('{files}' in c['stats_note'] and '{pages}' in c['stats_note'], 'stats_note placeholders')
for need in ('regional format', 'one cell', 'locked', 'no password', 'first sheet', '14 days', 'Google Sheets', 'LibreOffice', 'no macros', 'no subscription', '29 dollars', 'usually billed every month'):
    chk(need.lower() in c['description'].lower(), 'description lacks ' + need)
chk('1 Enquiries' in c['description'] and '8 Money' in c['description'], 'eight workbook names')
# real counts
parts = [json.load(open(W + f'du/du{n}.en.json', encoding='utf8')) for n in range(1, 9)]
def cnt(d): return {'tables': len(d['tables']), 'tools': len(d['tools']), 'forms': len(d['forms']), 'documents': len(d['documents']), 'checklists': len(d['checklists']),
                    'message texts': len(d['messages']), 'dashboard numbers': len(d['dashboard']['kpis']), 'charts': len(d['insights']['charts']), 'gauges': len(d['insights']['gauges'])}
per = [cnt(d) for d in parts]
for k in per[0]: chk(all(p[k] == per[0][k] for p in per), 'counts differ between parts: ' + k)
tot = {k: sum(p[k] for p in per) for k in per[0]}
txt = c['description'] + ' ' + ' '.join(c['features']) + ' ' + fq
found = 0
for num, noun in re.findall(r'(\d+) (?:ready )?(tables|tools|forms|documents|checklists|message texts|dashboard numbers|charts|gauges)', txt):
    n = int(num); found += 1
    chk(n in (per[0][noun], tot[noun]), f'count {n} {noun} is not real (per workbook {per[0][noun]}, total {tot[noun]})')
chk(len(parts) == 8 and re.search(r'\b8 (Excel )?workbooks', c['description']), '8 workbooks')
chk('144 ready tools' in txt and tot['tools'] == 144, '144 tools')
chk('160 tables' in txt and tot['tables'] == 160 and '96 forms' in txt and tot['forms'] == 96 and '272 message texts' in txt and tot['message texts'] == 272, 'totals')
# the sample-data facts (BLUEPRINT.md): 6 contracted doulas, 2 backup doulas
chk('six contracted doulas and two backup doulas' in fq, 'sample team sentence')
# banned
BRANDS = ['moderndoula', 'birthworkco', 'agiled', 'capterra', 'doulado', 'doulaflow', r'\bdona\b', 'cappa', 'beancount', r'\bwave\b', 'national baby', 'medicaid', r'asc ?606', '280a',
          'squarespace', r'\betsy\b', 'gumroad', 'canva', 'instagram', 'facebook', 'thrivecart', 'morning ?light', 'mumsnet', 'bornbir', 'truejoy', 'kaely', 'chikorell', r'\bwhop\b', 'shopify',
          r'\bzoom\b', 'stripe', 'paypal', 'quickbooks', 'xero', 'hipaa', r'\bnhs\b', r'\bhsa\b', r'\bfsa\b', 'superbill', 'notion', 'airtable', 'calendly', 'google drive', 'docusign']
BANNED = [r'compatib', r'\b15 languages\b', r'languages?\b', r'translat', r'\bconnected\b', r'\blinked\b', r'\blinks?\b', r'\bsync', r'Excel\s*(20\d\d|365|97|2007|2010|2013|2016|2019|2021)',
          '[$€£]', r'diagnos', r'symptom', r'safe birth', r'\bsafe(ly|st)?\b', r'guarantee a birth', r'better births?', r'bestseller', r'trusted by', r'limited time', r'last chance', r'only today',
          r'make money', r'earn more', r'extra income', r'\bapps?\b(?! )' if False else r'\bmobile app', r'\bportal\b(?<!client portal)', r'pregnan', r'contractions?', r'\bhealth advice']
def scan(label, s):
    for pat in BRANDS + BANNED:
        mm = re.search(pat, s, re.I)
        if mm and not (pat.startswith(r'\bportal') and False): bad.append(f'{label}: banned {pat}: {mm.group(0)}')
    for g in re.findall(r'\b(Google|Microsoft)\b ?(\w+)?', s):
        if g not in (('Google', 'Sheets'), ('Microsoft', 'Excel')): bad.append(f'{label}: brand use {g}')
    for mm in re.finditer(r'\b(medical|clinical)\b', s, re.I):
        pre = s[max(0, mm.start() - 5):mm.start()].lower()
        if not (pre.endswith('non-') or pre.endswith('not ')): bad.append(f'{label}: "{mm.group(0)}" outside a not-medical boundary line')
    for mm in re.finditer(r'\bportal\b', s, re.I):
        ctx = s[max(0, mm.start() - 12):mm.start()].lower()
        if 'client' not in ctx or not re.search(r'(not for|no )', s[max(0, mm.start() - 60):mm.start()].lower()): bad.append(f'{label}: portal outside a "not for" line')
    for mm in re.finditer(r'\bapps?\b', s, re.I):
        if 'not a web service or an app' not in s[max(0, mm.start() - 30):mm.end()].lower(): bad.append(f'{label}: app claim')
scan('copy', json.dumps(c, ensure_ascii=False))
pic = ' '.join(d['tagline'] + ' ' + ' '.join(s['name'] + ' ' + s['why'] for s in d['signature']) for d in parts)
scan('pictures', pic)
for i, d in enumerate(parts, 1):
    chk(len(d['tagline']) <= 80 and d['tagline'].lower() != d['name'].lower(), f'part {i} tagline')
    chk(d['tagline'].lower() != d['listing']['headline'].lower(), f'part {i} tagline equals the listing headline')
    chk(len(d['name']) <= 40, f'part {i} name')
    chk(5 <= len(d['signature']) <= 16 and all(len(s['name']) <= 50 and len(s['why']) <= 160 for s in d['signature']), f'part {i} signature limits')
    names = [s['name'].lower() for s in d['signature']]; chk(len(set(names)) == len(names), f'part {i} signature names repeat')
    for s in d['signature']:
        chk(s['why'].lower() != s['name'].lower(), f'part {i} signature name equals why')
    chk(d['i18n'] == {}, f'part {i} i18n not empty')
taglines = [d['tagline'] for d in parts]; chk(len(set(taglines)) == 8, 'taglines not unique')
print('real per workbook:', per[0]); print('real totals:', tot); print('count mentions checked:', found)
print('lengths:', {k: len(c[k]) for k in ('name', 'title', 'headline', 'seo_title', 'seo_description', 'description')}, 'longest feature', max(map(len, c['features'])))
print('PROBLEMS', len(bad)); [print(' ', b) for b in bad]
print('RESULT', 'FAIL' if bad else 'PASS')
