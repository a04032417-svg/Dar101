import json,re
W='/home/claude/work/'
c=json.load(open(W+'copy/wp/en.json',encoding='utf8'))
ref=json.load(open(W+'copy/wd/en.json',encoding='utf8'))
fin=json.load(open(W+'wp/listing/final/en.json',encoding='utf8'))
err=[]
def E(m): err.append(m)
if c!=fin: E('final copy differs')
if set(c)!=set(ref): E(f'keys differ {set(c)^set(ref)}')
for k,m in [('name',40),('title',140),('headline',80),('seo_title',70),('seo_description',160)]:
    if len(c[k])>m: E(f'{k} {len(c[k])}>{m}')
t=c['tags']
if len(t)!=13 or len(set(x.lower() for x in t))!=13 or any(len(x)>20 for x in t): E('tags')
if len(c['features'])!=12 or any(len(f)>90 for f in c['features']): E('features')
if len(c['faq'])!=6: E('faq count')
if not 900<=len(c['description'])<=2500: E(f'description {len(c["description"])}')
for ph in ('{pages}','{files}'):
    if ph not in c['stats_note']: E('placeholder '+ph)
# real counts
parts=[json.load(open(W+f'wp/wp{i}.en.json',encoding='utf8')) for i in range(1,9)]
cnt=lambda k:[len(p[k]) for p in parts]
real={'tables':cnt('tables'),'tools':cnt('tools'),'forms':cnt('forms'),'documents':cnt('documents'),'checklists':cnt('checklists'),'messages':cnt('messages'),
 'kpis':[len(p['dashboard']['kpis']) for p in parts],'charts':[len(p['insights']['charts']) for p in parts],'gauges':[len(p['insights']['gauges']) for p in parts]}
for k,v in real.items():
    if len(set(v))!=1: E(f'{k} differs by part {v}')
per={k:v[0] for k,v in real.items()}; tot={k:sum(v) for k,v in real.items()}
D=c['description']
m=re.search(r'Each workbook has (.*?)\. Over the eight: (.*?)\.\n',D)
exp1=f"{per['tables']} tables, {per['tools']} tools, {per['forms']} forms, {per['documents']} documents, {per['checklists']} checklists, {per['messages']} message texts, {per['kpis']} dashboard numbers, {per['charts']} charts and {per['gauges']} gauges"
exp2=f"{tot['tables']} tables, {tot['tools']} tools, {tot['forms']} forms, {tot['documents']} documents, {tot['checklists']} checklists, {tot['messages']} message texts, {tot['kpis']} dashboard numbers, {tot['charts']} charts and {tot['gauges']} gauges"
if not m or m.group(1)!=exp1: E('per-workbook counts wrong: '+str(m and m.group(1)))
if not m or m.group(2)!=exp2: E('total counts wrong')
if len(parts)!=8 or '8 Excel workbooks' not in D: E('8 workbooks')
for i,p in enumerate(parts,1):
    if f'{i} {p["name"].replace("Decor","Decor")}' not in D: E(f'part name {i} missing: {p["name"]}')
# banned
txt=json.dumps(c,ensure_ascii=False).lower()
brands=['zola','the knot','theknot','weddingwire','trustpilot','petapixel','bridebook','unstar','etsy','fiverr','tiller','canva','priori','mydigitaldarling','opulent','desklark','findniche','minted','sbs.com','planning.wedding','gumroad','payhip','shopify','whop','pinterest','google','excel','libreoffice','whatsapp','microsoft']
banned=['compatible','15 languages','languages','translat','connected','linked','save money','perfect wedding','stress-free','stress free','bestseller','guarantee your','registry','macro-enabled']
for b in banned:
    if b in txt: E('banned: '+b)
allowed={'google sheets','microsoft excel','excel','libreoffice','whatsapp'}
for b in ['zola','the knot','theknot','weddingwire','trustpilot','petapixel','bridebook','unstar','etsy','fiverr','tiller','canva','priori','mydigitaldarling','opulent','desklark','findniche','minted','gumroad','payhip','shopify','whop','pinterest']:
    if b in txt: E('brand: '+b)
g=re.findall(r'google \w+',txt)
if any(x!='google sheets' for x in g): E('google other '+str(g))
if re.search(r'excel \d|20\d\d',txt): E('version/year number')
for w in ['app ','website','sync','automatic']:
    for m2 in re.finditer(w,txt): 
        print('note:',w,'in',txt[max(0,m2.start()-40):m2.end()+30].replace('\\n',' '))
# picture texts
for i,p in enumerate(parts,1):
    if len(p['tagline'])>80 or p['tagline'].lower()==p['name'].lower(): E(f'tagline {i}')
    if p['tagline'].strip().lower() in (p['listing']['headline'].lower(),): E(f'tagline=listing headline {i}')
    for s in p['signature']:
        if len(s['name'])>50 or len(s['why'])>160: E(f'sig {i} {s["name"]}')
        for b in ['compatible','connected','linked','perfect','stress','save money']:
            if b in (s['name']+s['why']).lower(): E(f'sig banned {b} {i}')
print('title',len(c['title']),'headline',len(c['headline']),'seo_title',len(c['seo_title']),'seo_desc',len(c['seo_description']),'desc',len(D),'maxfeat',max(len(f) for f in c['features']),'name',len(c['name']))
print('taglines',[len(p['tagline']) for p in parts])
print('maxsig why',max(len(s['why']) for p in parts for s in p['signature']))
print('RESULT:', 'OK, 0 problems' if not err else err)
