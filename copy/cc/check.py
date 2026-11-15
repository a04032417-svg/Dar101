import json,re,sys
W='/home/claude/work/'
d=json.load(open(W+'copy/cc/en.json',encoding='utf8')); wd=json.load(open(W+'copy/wd/en.json',encoding='utf8'))
parts=[json.load(open(f'{W}cc/cc{i}.en.json',encoding='utf8')) for i in range(1,9)]
errs=[]
def chk(c,m):
    if not c: errs.append(m)
chk(set(d)==set(wd),'keys differ from model: %s'%(set(d)^set(wd)))
chk(len(d['name'])<=40,'name'); chk(len(d['title'])<=140,'title %d'%len(d['title'])); chk(len(d['headline'])<=80,'headline')
chk(len(d['seo_title'])<=70,'seo_title %d'%len(d['seo_title'])); chk(len(d['seo_description'])<=160,'seo_description %d'%len(d['seo_description']))
chk(len(d['tags'])==13 and len(set(d['tags']))==13 and all(len(t)<=20 for t in d['tags']),'tags')
chk(len(d['features'])==12 and all(len(f)<=90 for f in d['features']),'features')
chk(len(d['faq'])==6,'faq')
chk(900<=len(d['description'])<=2500,'description length %d'%len(d['description']))
chk('{pages}' in d['stats_note'] and '{files}' in d['stats_note'],'stats_note placeholders')
chk(d['title'].lower().find('home daycare')<40,'key phrase in first 40')
real={}
def c(k,f): real[k]=[f(p) for p in parts]
c('tables',lambda p:len(p['tables'])); c('calculators',lambda p:len(p['tools'])); c('forms',lambda p:len(p['forms']))
c('documents',lambda p:len(p['documents'])); c('checklists',lambda p:len(p['checklists'])); c('messages',lambda p:len(p['messages']))
c('figures',lambda p:len(p['dashboard']['kpis'])); c('charts',lambda p:len(p['insights']['charts'])); c('gauges',lambda p:len(p['insights']['gauges']))
for k,v in real.items(): chk(len(set(v))==1,'counts differ across parts: '+k)
per={k:v[0] for k,v in real.items()}
chk(len(parts)==8,'8 parts')
txt=d['description']
pat={'tables':'tables','calculators':'calculators','forms':'forms','documents':'documents','checklists':'checklists','messages':r'ready text messages','figures':r'dashboard figures','charts':'charts','gauges':'gauges'}
for k,p in pat.items():
    m=re.search(r'(\d+) '+p,txt); chk(m and int(m.group(1))==per[k],f'{k}: copy {m and m.group(1)} real {per[k]}')
chk('8 workbooks' in txt.lower() or '8 Excel workbooks' in txt,'8 workbooks')
for p in parts: chk(p['name'] in txt,'part name missing: '+p['name'])
allt=json.dumps(d,ensure_ascii=False).lower()
for w in ['compatible','15 languages','languages','connected','linked','procare','brightwheel','himama','kangarootime','jackrabbit','lillio','xplor','capterra','etsy','canva','quickbooks','zoom','wordpress','shopify','whop','naeyc','excel 20','excel 365','office 365']:
    chk(not re.search(r'\b'+re.escape(w)+r'\b',allt),'banned word: '+w)
chk(re.search(r'excel (19|20)\d\d|excel \d+',allt) is None,'excel version')
for w in ['microsoft excel','google sheets','libreoffice']: chk(w in allt,'missing '+w)
chk('14 days' in allt,'guarantee'); chk('29 dollars' in allt,'price')
for p in parts:
    chk(len(p['tagline'])<=80 and p['tagline']!=p['name'],'tagline '+p['name'])
    for s in p['signature']: chk(len(s['name'])<=50 and len(s['why'])<=160,'sig '+s['name'])
a=json.load(open(W+'cc/listing/final/en.json',encoding='utf8')) if len(sys.argv)<2 else d
chk(a==d,'listing/final/en.json differs')
print('lengths: name',len(d['name']),'title',len(d['title']),'headline',len(d['headline']),'seo_title',len(d['seo_title']),'seo_desc',len(d['seo_description']),'description',len(d['description']),'max feature',max(map(len,d['features'])))
print('real per-workbook counts',per)
print('CHECK','OK' if not errs else 'FAILED'); [print(' -',e) for e in errs]
