import json, re, sys
C='/home/claude/work/'
d=json.load(open(C+'copy/cr/en.json')); fin=json.load(open(C+'cr/listing/final/en.json'))
parts=[json.load(open(C+f'cr/cr{i}.en.json')) for i in range(1,9)]
ok=True
def bad(m):
    global ok; ok=False; print('FAIL',m)
# limits
for k,n in [('name',40),('title',140),('headline',80),('seo_title',70),('seo_description',160)]:
    if len(d[k])>n: bad(f'{k} {len(d[k])}>{n}')
if len(d['tags'])!=13 or len({t.lower() for t in d['tags']})!=13 or any(len(t)>20 for t in d['tags']): bad('tags')
if len(d['features'])!=12 or any(len(f)>90 for f in d['features']): bad('features')
if len(d['faq'])!=6: bad('faq')
for p in ('{pages}','{files}'):
    if p not in d['stats_note']: bad('stats_note '+p)
if len(d['description'])>2500: bad('description >2500')
if d!=fin: bad('listing/final differs')
m=json.load(open(C+'copy/wd/en.json'))
if set(m)!=set(d): bad('keys differ from model')
blob=json.dumps(d,ensure_ascii=False)
for p in parts: blob+=' '+p['tagline']+' '+' '.join(s['name']+' '+s['why'] for s in p['signature'])
for i,p in enumerate(parts,1):
    if not p['tagline'] or len(p['tagline'])>80 or p['tagline'].lower()==p['name'].lower(): bad(f'tagline {i}')
tl=[p['tagline'] for p in parts]
if len(set(tl))!=8: bad('taglines not unique')
# banned
low=blob.lower()
banned=['compatible','15 languages','languages','connected','linked','live ','real-time','telematics app','sync','mot ','vat','gst']
brands=['rentsyst','capterra','invers','coastr','spreadsheetshub','etsy','readysheetgo','serenatasjourney','exxceladdiction','flevy','sharpsheets','quadratic','oak business','vital dollar','vitaldollar','qoreups','autorentalnews','finmodelslab','carrentalsolutions','simplyfleet','levyelectric','nrma','gumroad','whop','shopify','payhip','turo','getaround','airbnb','toyota','tesla','ford','bmw','hertz','avis','enterprise','visa','mastercard','paypal','stripe']
for w in banned+brands:
    if re.search(r'(?<![a-z])'+re.escape(w.strip())+(r'(?![a-z])' if w.endswith(' ') or True else ''),low): bad('banned word: '+w)
if re.search(r'google(?! sheets)',low): bad('Google outside Google Sheets')
if re.search(r'excel \d|20\d\d|\$|€|£',blob.replace('2026','')): bad('version/currency symbol/year')
# counts
def tot(k): return sum(len(p[k]) for p in parts)
def per(k): return {len(p[k]) for p in parts}
real={'tables':20,'tools':18,'forms':12,'documents':12,'checklists':12,'message texts':34,'dashboard numbers':30,'charts':22,'gauges':6,'workbooks':8}
tots={'tables':tot('tables'),'tools':tot('tools'),'forms':tot('forms'),'documents':tot('documents'),'checklists':tot('checklists'),'message texts':tot('messages'),'dashboard numbers':sum(len(p['dashboard']['kpis']) for p in parts),'charts':sum(len(p['insights']['charts']) for p in parts),'gauges':sum(len(p['insights']['gauges']) for p in parts),'workbooks':8}
perreal={'tables':{20},'tools':{18},'forms':{12},'documents':{12},'checklists':{12},'message texts':{34},'dashboard numbers':{30},'charts':{22},'gauges':{6}}
for i,p in enumerate(parts):
    assert len(p['tables'])==20 and len(p['insights']['charts'])==22 and len(p['insights']['gauges'])==6
text=d['description']+' '+' '.join(f['q']+' '+f['a'] for f in d['faq'])+' '+' '.join(d['features'])
found=0
for n,noun in re.findall(r'(\d+) (tables|tools|forms|documents|checklists|ready message texts|message texts|dashboard numbers|charts|gauges|workbooks)',text):
    noun=noun.replace('ready ',''); n=int(n); found+=1
    if n not in (real[noun],tots[noun]): bad(f'count {n} {noun}')
# ensure the 8 workbook names listed equal real names
for i,p in enumerate(parts,1):
    if p['name'] not in d['description']: bad('part name missing '+p['name'])
print('counts checked:',found,'| totals',tots)
print('lengths: name',len(d['name']),'title',len(d['title']),'headline',len(d['headline']),'seo_title',len(d['seo_title']),'seo_desc',len(d['seo_description']),'tags',len(d['tags']),'features',len(d['features']),'faq',len(d['faq']),'desc',len(d['description']))
print('taglines max',max(map(len,tl)))
print('RESULT','PASS' if ok else 'FAIL')
