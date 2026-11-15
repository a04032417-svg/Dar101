import json,re,sys
W='/home/claude/work/'
a=json.load(open(W+'copy/au/en.json')); b=json.load(open(W+'au/listing/final/en.json'))
wd=json.load(open(W+'copy/wd/en.json'))
bad=[]
def ck(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: bad.append(m)
ck(a==b,'final copy equals copy/au')
ck(list(a)==list(wd),'same keys as wd model')
ck(len(a['name'])<=40,f"name {len(a['name'])}")
ck(len(a['title'])<=140,f"title {len(a['title'])}")
ck(len(a['headline'])<=80,f"headline {len(a['headline'])}")
ck(len(a['seo_title'])<=70,f"seo_title {len(a['seo_title'])}")
ck(len(a['seo_description'])<=160,f"seo_desc {len(a['seo_description'])}")
ck(900<=len(a['description'])<=2500,f"description {len(a['description'])}")
ck(len(a['tags'])==13 and len(set(t.lower() for t in a['tags']))==13 and all(len(t)<=20 for t in a['tags']),'13 unique tags <=20')
ck(len(a['features'])==12 and all(len(f)<=90 for f in a['features']),'12 features <=90: '+str(max(map(len,a['features']))))
ck(len(a['faq'])==6,'6 faq')
ck('{files}' in a['stats_note'] and '{pages}' in a['stats_note'],'stats_note placeholders')
txt=json.dumps(a,ensure_ascii=False)
t2=txt
for ok in ['Microsoft Excel','Google Sheets','LibreOffice','WhatsApp']: t2=t2.replace(ok,'')
brands=['compatible','15 languages','languages','translation claim','connected','linked','KDP','ISBN','ASIN','Amazon','Kindle','Apple','Kobo','Draft2Digital','Smashwords','Audible','ACX','Findaway','IngramSpark','Ingram','Barnes','BookBub','BookFunnel','Goodreads','Mailchimp','MailerLite','ScribeCount','PublishDrive','Abacus','MetaComet','Capterra','TrueRoyalties','Scrivy','Publisher Champ','Inkario','DashBook','Publishwide','Kindlepreneur','Page Publishing','Etsy','Payhip','Gumroad','Fourthwall','SelfPubHub','Vappingo','Squarespace','Shopify','Whop','PayPal','Stripe','Facebook','Instagram','TikTok','Google','Microsoft','bestseller','best-seller','make money','guarantee income','import','sync','automatic','testimonial','limited time','hurry','only today','$','Dar Templates']
for w in brands:
    ck(not re.search(re.escape(w),t2,re.I),'no '+w)
ck(not re.search(r'Excel\s*(\d|20\d\d|365)',t2),'no Excel version')
d=a['description']
counts={'tables':20,'tools':18,'forms':12,'documents':12,'checklists':12,'message texts':34,'dashboard numbers':30,'charts':22,'gauges':6}
real={}
for i in range(1,9):
    p=json.load(open(W+f'au/au{i}.en.json'))
    for k,v in {'tables':len(p['tables']),'tools':len(p['tools']),'forms':len(p['forms']),'documents':len(p['documents']),'checklists':len(p['checklists']),'message texts':len(p['messages']),'dashboard numbers':len(p['dashboard']['kpis']),'charts':len(p['insights']['charts']),'gauges':len(p['insights']['gauges'])}.items():
        real.setdefault(k,set()).add(v)
for k,n in counts.items():
    ck(real[k]=={n},f'real {k} per part = {n} in all 8 parts ({real[k]})')
    m=re.search(rf'(\d+) (?:ready-to-send )?{k}',d); ck(m and int(m.group(1))==n,f'copy per-part {k}')
    m=re.search(rf'(\d+) (?:ready-to-send )?{k}',d[d.index('In all'):]) ; ck(m and int(m.group(1))==8*n,f'copy total {k} = {8*n}')
names=[json.load(open(W+f'au/au{i}.en.json'))['name'] for i in range(1,9)]
for i,n in enumerate(names,1): ck(f'{i} {n}' in d,f'part name {i} in description')
for i in range(1,9):
    p=json.load(open(W+f'au/au{i}.en.json'))
    ck(len(p['tagline'])<=80 and p['tagline']!=p['name'],f'tagline {i} {len(p["tagline"])}')
    for s in p['signature']:
        ck(len(s['name'])<=50 and len(s['why'])<=160,f'sig {i} {s["name"][:25]} {len(s["why"])}') if (len(s['name'])>50 or len(s['why'])>160) else None
    pt=json.dumps([p['tagline']]+[(s['name'],s['why']) for s in p['signature']])
    for w in ['compatible','connected','KDP','ISBN','ASIN','Amazon','Kindle','bestseller','import','sync','Google']:
        ck(not re.search(w,pt,re.I),f'part {i} picture text no {w}')
print('RESULT','ALL CHECKS PASS' if not bad else f'{len(bad)} FAIL')
sys.exit(1 if bad else 0)
