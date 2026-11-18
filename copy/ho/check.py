import json,re,sys
D='/home/claude/work/'
en=json.load(open(D+'copy/ho/en.json')); fin=json.load(open(D+'ho/listing/final/en.json'))
bad=[]
def e(m): bad.append(m)
ref=json.load(open(D+'copy/wd/en.json'))
if set(en)!=set(ref): e(f'keys differ {set(en)^set(ref)}')
if en!=fin: e('final copy differs')
if len(en['name'])>40: e('name')
if len(en['title'])>140: e('title')
if len(en['headline'])>80: e('headline')
if len(en['seo_title'])>70: e('seo_title')
if len(en['seo_description'])>160: e('seo_description')
t=en['tags']
if len(t)!=13 or len(set(x.lower() for x in t))!=13 or any(len(x)>20 for x in t): e('tags')
if len(en['features'])!=12 or any(len(x)>90 for x in en['features']): e('features '+str([len(x) for x in en['features']]))
if len(en['faq'])!=6: e('faq')
for ph in ('{pages}','{files}'):
    if ph not in en['stats_note']: e('stats_note '+ph)
if '{pages}' not in en['description']: e('desc pages')
desc=en['description']
if not (900<=len(desc)<=4000): e('desc len')
# counts
real={}
parts=[json.load(open(D+f'ho/ho{i}.en.json')) for i in range(1,9)]
for k,f in [('tables',lambda d:len(d['tables'])),('tools',lambda d:len(d['tools'])),('forms',lambda d:len(d['forms'])),('documents',lambda d:len(d['documents'])),('checklists',lambda d:len(d['checklists'])),('messages',lambda d:len(d['messages'])),('kpis',lambda d:len(d['dashboard']['kpis'])),('charts',lambda d:len(d['insights']['charts'])),('gauges',lambda d:len(d['insights']['gauges']))]:
    per=[f(d) for d in parts]; real[k]=(per[0],sum(per)); 
    if len(set(per))!=1: e(f'{k} differ per part {per}')
want=[(20,'tables'),(18,'tools'),(12,'forms'),(12,'documents'),(12,'checklists'),(34,'message texts'),(30,'dashboard numbers'),(22,'charts'),(6,'gauges')]
keymap={'message texts':'messages','dashboard numbers':'kpis'}
alltext=json.dumps(en,ensure_ascii=False)
for n,w in want:
    k=keymap.get(w,w); r=real[k]
    if r[0]!=n: e(f'per-part {w} {r[0]}!={n}')
    if f'{n} {w}' not in desc: e(f'missing "{n} {w}"')
    if f'{r[1]} {w}' not in desc: e(f'missing total "{r[1]} {w}"')
# any "N noun" mismatch
for m in re.finditer(r'(\d+) (tables|tools|forms|documents|checklists|message texts|dashboard numbers|charts|gauges|workbooks)',desc):
    n=int(m.group(1)); w=m.group(2)
    if w=='workbooks': ok=n==8
    else:
        k=keymap.get(w,w); ok=n in real[k]
    if not ok: e('wrong count '+m.group(0))
nparts=len(parts)
if nparts!=8: e('parts')
# banned
low=alltext.lower()
banned=['compatible','15 languages','languages','translat','connected','linked','save time','saves time','save money','never forget','notification','reduce waste','reduce food waste','guaranteed','automatic','excel 20','excel 365','office 365','allerg','diet','nutrition','calori','medical','veterinar','legal advice','macro-enabled']
banned+=['cozi','plantoeat','plan to eat','freddie','angi','kimola','optimumplanners','lizaraco','ezspreadsheets','thegoatedplanner','littlehomestead','spreadsheetdaddy','mayaprint','gumroad','etsy','notion','trustpilot','technology review','foodsafety','usda','shopify','payhip','whop','amazon','apple','numbers app','tesco','walmart','ikea','mot ','hmrc','irs','gdpr']
def scan(txt,label,allow_sync=False):
    l=txt.lower()
    for b in banned:
        if re.search(r'\b'+re.escape(b.strip()),l) and (len(b)>4 or re.search(r'\b'+re.escape(b.strip())+r'\b',l)): e(f'{label}: banned "{b}"')
    l2=re.sub(r'google sheets','',l); l2=re.sub(r'microsoft excel','',l2)
    for b in ['google','microsoft','sync']:
        if b in l2 and not (b=='sync' and allow_sync): e(f'{label}: "{b}"')
    if not allow_sync and 'remind' in l2: e(f'{label}: "remind"')
for k,v in en.items():
    if k=='faq':
        for x in v:
            scan(x['q']+' '+x['a'],'faq',allow_sync=True)
    elif k=='description':
        scan(re.sub(r'reminder service|reminders','',v),'description',allow_sync=True)
    else: scan(json.dumps(v,ensure_ascii=False),k)
if 'refund' not in alltext.lower() or '14 days' not in alltext: e('guarantee')
for q in ['Google Sheets','currency','couple','several people','reminders','refund']:
    if not any(q.lower() in (x['q']+x['a']).lower() for x in en['faq']): e('faq lacks '+q)
# parts
for i,d in enumerate(parts,1):
    tg=d['tagline']
    if len(tg)>80: e(f'tagline {i} len')
    if tg.strip().lower()==d['name'].strip().lower() or tg==d['listing']['headline']: e(f'tagline {i} equals name/headline')
    scan(tg,f'tagline{i}')
    for s in d['signature']:
        if len(s['name'])>50 or len(s['why'])>160: e(f'sig {i} {s["name"]}')
        scan(s['name']+' '+s['why'],f'sig{i}')
if len({d['tagline'] for d in parts})!=8: e('taglines not unique')
print('title',len(en['title']),'headline',len(en['headline']),'seo_title',len(en['seo_title']),'seo_desc',len(en['seo_description']),'desc',len(desc),'features max',max(len(x) for x in en['features']))
print('taglines',[len(d['tagline']) for d in parts],'sig why max',max(len(s['why']) for d in parts for s in d['signature']))
print('real counts (per part,total):',real)
print('ERRORS',len(bad)); print('\n'.join(bad)); print('CHECK','OK' if not bad else 'FAIL')
