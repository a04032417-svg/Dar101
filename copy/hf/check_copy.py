import json, re, os
P = '/home/claude/work/copy/hf/en.json'
F = '/home/claude/work/hf/listing/final/en.json'
d = json.load(open(P)); raw = open(P).read()
errs = []
def chk(c, m):
    if not c: errs.append(m)
# structure and limits
model = json.load(open('/home/claude/work/copy/wd/en.json'))
chk(list(d) == list(model), 'keys differ from model')
chk(len(d['name']) <= 40, 'name'); chk(len(d['title']) <= 140, 'title'); chk(len(d['headline']) <= 80, 'headline')
chk(len(d['seo_title']) <= 70, 'seo_title'); chk(len(d['seo_description']) <= 160, 'seo_description')
chk(len(d['tags']) == 13 and len(set(t.lower() for t in d['tags'])) == 13 and all(len(t) <= 20 for t in d['tags']), 'tags')
chk(len(d['features']) == 12 and all(len(f) <= 90 for f in d['features']), 'features')
chk(len(d['faq']) == 6, 'faq count')
chk('{pages}' in d['stats_note'] and '{files}' in d['stats_note'], 'stats_note placeholders')
chk(len(d['description'].split('\n')[0]) <= 160, 'hook line over 160')
chk(open(F).read() == raw, 'listing/final/en.json is not a copy')
# banned words
text = raw.lower()
banned = ['compatible', '15 languages', 'connected', 'linked', 'save money', 'financial freedom', 'debt-free', 'debt free',
          'credit score', 'get rich', 'guaranteed savings', 'sync', 'bestseller', 'limited time', 'last chance']
brands = ['ynab', 'you need a budget', 'trustpilot', 'pocketclear', 'envelopebudgeting', 'monarch', 'tiller', 'nerdwallet',
          'etsy', 'thexton', 'weeklycrew', 'prioridigital', 'myproductivelife', 'findniche', 'nbc', 'c+r research',
          'federal reserve', 'cfpb', 'xyplanning', 'xy planning', 'gumroad', 'payhip', 'reddit', 'whatsapp', 'paypal', 'whop', 'shopify',
          'bls.gov', 'google drive', 'quickbooks', 'mint', 'superannuation', 'isa-type', ' ira', '401']
for w in banned + brands:
    chk(not re.search(r'(?<![a-z])' + re.escape(w.strip()) + r'(?![a-z])', text), 'banned/brand word: ' + w)
chk(not re.search(r'excel\s*(20\d\d|\d{2}|365)', text), 'excel version')
chk(not re.search(r'[$€£]', raw), 'currency symbol')
for w in ['microsoft excel', 'google sheets', 'libreoffice']: chk(w in text, 'missing ' + w)
# real counts from the 8 specs (part 6: the built spec, hf6.en.json is missing)
def spec(n):
    f = f'/home/claude/work/hf/hf{n}.en.json'
    if not os.path.exists(f): f = f'/home/claude/work/hf/out{n}/work/spec.json'
    return json.load(open(f)), f
per = {}; tot = {}
for n in range(1, 9):
    s, f = spec(n)
    c = {'tables': len(s['tables']), 'tools': len(s['tools']), 'forms': len(s['forms']), 'documents': len(s['documents']),
         'checklists': len(s['checklists']), 'message texts': len(s['messages']),
         'dashboard numbers': len(s['dashboard']['kpis']), 'charts': len(s['insights']['charts']), 'gauges': len(s['insights']['gauges'])}
    for k, v in c.items(): per.setdefault(k, set()).add(v); tot[k] = tot.get(k, 0) + v
    chk(s['price_usd'] == 29, f'price part {n}')
chk(all(len(v) == 1 for v in per.values()), 'parts differ in counts: ' + str(per))
perv = {k: next(iter(v)) for k, v in per.items()}
found = 0
for m in re.finditer(r'(\d+)\s+(tables|tools|forms|documents|checklists|message texts|dashboard numbers|charts|gauges|workbooks)', d['description']):
    n, k = int(m.group(1)), m.group(2); found += 1
    if k == 'workbooks': chk(n == 8, 'workbooks count'); continue
    chk(n in (perv[k], tot[k]), f'count mismatch {n} {k} (real {perv[k]} per workbook, {tot[k]} total)')
# every count must appear at least once
for k in perv: chk(f'{perv[k]} {k}' in d['description'] and f'{tot[k]} {k}' in d['description'], 'count missing for ' + k)
chk(re.search(r'\b29 dollars', d['description']) is not None, '29 dollars')
chk('14 days' in d['description'] and '14 days' in raw, 'guarantee')
# picture texts
for n in range(1, 9):
    s, f = spec(n)
    if 'out' in f:  # part 6 file missing: check the picture texts prepared for it
        pj = json.load(open('/home/claude/work/copy/hf/hf6_picture.json'))
        s = dict(s, tagline=pj['tagline'], signature=[{'name': a, 'why': b} for a, b in pj['sig']])
    chk(len(s['tagline']) <= 80 and s['tagline'].lower() != s['name'].lower(), f'tagline {n}')
    chk(s['tagline'] != s['listing']['headline'] if 'listing' in s else True, f'tagline {n} equals listing headline')
    chk(all(len(x['name']) <= 50 and len(x['why']) <= 160 for x in s['signature']), f'signature limits {n}')
    t = (s['tagline'] + ' ' + ' '.join(x['name'] + ' ' + x['why'] for x in s['signature'])).lower()
    for w in banned + brands:
        chk(not re.search(r'(?<![a-z])' + re.escape(w.strip()) + r'(?![a-z])', t), f'picture {n}: banned word {w}')
print('per workbook:', perv); print('suite totals:', tot)
print('lengths:', {k: len(d[k]) for k in ['name', 'title', 'headline', 'seo_title', 'seo_description', 'description']})
print('count phrases checked:', found)
print('RESULT:', 'PASS' if not errs else 'FAIL'); [print(' -', e) for e in errs]
