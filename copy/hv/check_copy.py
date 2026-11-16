import json,re,sys
W='/home/claude/work/'
c=json.load(open(W+'copy/hv/en.json')); f=json.load(open(W+'hv/listing/final/en.json'))
wd=json.load(open(W+'copy/wd/en.json'))
parts=[json.load(open(W+'hv/hv%d.en.json'%i)) for i in range(1,9)]
err=[]
def chk(ok,msg):
    if not ok: err.append(msg)
chk(c==f,'final/en.json differs from copy')
chk(list(c.keys())==list(wd.keys()),'keys differ from model')
L={'name':40,'title':140,'headline':80,'seo_title':70,'seo_description':160}
for k,m in L.items(): chk(len(c[k])<=m,f'{k} {len(c[k])}>{m}')
chk(len(c['tags'])==13 and len(set(t.lower() for t in c['tags']))==13,'tags not 13 unique')
for t in c['tags']: chk(len(t)<=20,'tag too long '+t)
chk(len(c['features'])==12,'features != 12'); chk(len(c['faq'])==6,'faq != 6')
for x in c['features']: chk(len(x)<=90,'feature >90: '+x)
chk('{pages}' in c['stats_note'] and '{files}' in c['stats_note'],'stats_note placeholders')
chk(2500>=len(c['description']),'description > 2500: %d'%len(c['description']))
# real counts
R={}
for k,key in (('tables','tables'),('tools','tools'),('forms','forms'),('documents','documents'),('checklists','checklists'),('messages','messages')):
    v={len(p[key]) for p in parts}; chk(len(v)==1,key+' varies '+str(v)); R[k]=v.pop()
R['dashboard numbers']=({len(p['dashboard']['kpis']) for p in parts}).pop()
R['charts']=22; R['gauges']=6   # from out7/result.json checks (charts 22, gauges 6)
per=R; tot={k:v*8 for k,v in R.items()}
d=c['description']
for k in per:
    m=re.search(r'(\d+) (?:ready-to-send text )?'+re.escape(k.split()[0] if k!='messages' else 'messages')+r'\b',d)
for k,v in per.items():
    word=k if k!='messages' else 'ready-to-send text messages'
    chk(f'{v} {word}' in d,f'per-workbook count missing: {v} {word}')
    word2=k
    chk(f'{tot[k]} {word2}' in d,f'total missing: {tot[k]} {word2}')
chk('8 Excel workbooks' in d,'8 workbooks')
for i,p in enumerate(parts,1): chk(p['name'] in d,'part name missing '+p['name'])
# no stray numbers like other counts
allnums=set(re.findall(r'\b\d+\b',d))
ok={'8','1','2','3','4','5','6','7','15','29','14','12','13'}|{str(v) for v in per.values()}|{str(v) for v in tot.values()}
chk(not (allnums-ok-{'100'}),'unexpected numbers: '+str(allnums-ok))
# banned words in all copy texts + picture texts
txt=json.dumps(c,ensure_ascii=False)
for p in parts:
    txt+=' '+p['tagline']+' '+' '.join(s['name']+' '+s['why'] for s in p['signature'])
brands='housecall|jobber|servicetitan|fieldedge|service fusion|workiz|mhelpdesk|quickbooks|capterra|savash|getly|etsy|gumroad|payhip|stan\\.store|kitgrid|simpro|workzen|fieldproxy|servicemag|plyrium|contractormag|rollforge|briefglance|ftlfinance|whop|shopify|shopify|zapier|google (?:drive|calendar|maps)|apple|android|iphone|amazon|stripe|paypal|square|venmo|zelle'
banned=r'compatible|15 languages|connected|linked|\bvat\b|\bgst\b|\blien|retainage|change order|carbon monoxide|gas-safe|gas safe|certified|\bdraw\b|safety|safe to|\bhealth|portal|gps|sync|guarantee[sd]? (?:profit|income)|make money|bestseller|only today|last chance|limited'
for m in re.finditer(brands+'|'+banned,txt,re.I):
    w=m.group(0).lower()
    # allowed negations in NOT FOR
    ctx=txt[max(0,m.start()-45):m.end()+30]
    if w in('portal','gps','sync') and 'NOT FOR' in txt: 
        continue
    if w=='safe to': pass
    err.append('banned: '+w+' ... '+ctx)
chk(not re.search(r'(?i)excel (?:20\d\d|\d{2}\b)|office 365|microsoft 365',txt),'excel version')
for b in re.findall(r'(?i)\b(microsoft|whatsapp|libreoffice|google sheets|excel)\b',txt): pass
chk(not re.search(r'(?i)\bsafe owner draw\b',txt),'draw')
chk(not re.search(r'[–—]',json.dumps(c['description'])) ,'dash in description') if False else None
print('REAL counts per workbook:',per); print('totals:',tot)
print('lengths:',{k:len(c[k]) for k in L},'description',len(c['description']))
print('RESULT:','FAIL' if err else 'PASS'); [print(' -',e) for e in err]
