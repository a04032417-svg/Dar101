#!/usr/bin/env python3
"""Check the Therapy suite English copy and picture texts: limits, banned words, counts equal the real counts."""
import json, re
W='/home/claude/work/'
c=json.load(open(W+'copy/th/en.json',encoding='utf8')); m=json.load(open(W+'copy/wd/en.json',encoding='utf8'))
fin=json.load(open(W+'th/listing/final/en.json',encoding='utf8'))
bad=[]
def chk(ok,msg):
    if not ok: bad.append(msg)
chk(set(c)==set(m),'keys differ from wd: %s'%sorted(set(c)^set(m)))
chk(c==fin,'listing/final/en.json is not a copy')
for k,l in [('name',40),('title',140),('headline',80),('seo_title',70),('seo_description',160)]: chk(len(c[k])<=l,f'{k} {len(c[k])}>{l}')
chk(len(c['description'])<=2500,'description >2500 (%d)'%len(c['description']))
t=c['tags']; chk(len(t)==13 and len(set(x.lower() for x in t))==13 and max(map(len,t))<=20,'tags')
chk(len(c['features'])==12 and max(map(len,c['features']))<=90,'features')
chk(len(c['faq'])==6,'faq count')
chk('{files}' in c['stats_note'] and '{pages}' in c['stats_note'],'stats_note placeholders')
# real counts
parts=[json.load(open(W+f'th/th{n}.en.json',encoding='utf8')) for n in range(1,9)]
def cnt(d): return dict(tables=len(d['tables']),tools=len(d['tools']),forms=len(d['forms']),documents=len(d['documents']),checklists=len(d['checklists']),**{'message texts':len(d['messages']),'dashboard numbers':len(d['dashboard']['kpis']),'charts':len(d['insights']['charts']),'gauges':len(d['insights']['gauges'])})
per=[cnt(d) for d in parts]
for k in per[0]: chk(all(p[k]==per[0][k] for p in per),'counts differ between parts: '+k)
tot={k:sum(p[k] for p in per) for k in per[0]}
txt=c['description']+' '+' '.join(c['features'])+' '+' '.join(q['q']+' '+q['a'] for q in c['faq'])
found=0
for num,noun in re.findall(r'(\d+) (tables|tools|forms|documents|checklists|message texts|ready message texts|dashboard numbers|charts|gauges)',txt):
    noun=noun.replace('ready ',''); n=int(num); found+=1
    chk(n in (per[0][noun],tot[noun]),f'count {n} {noun} is not real (per workbook {per[0][noun]}, total {tot[noun]})')
chk(re.search(r'\b8 (Excel )?workbooks',c['description']) and len(parts)==8,'8 workbooks')
chk('144 ready tools' in txt and tot['tools']==144,'144 tools')
# banned
allt=json.dumps(c,ensure_ascii=False)
pic=' '.join(d['tagline']+' '+' '.join(s['name']+' '+s['why'] for s in d['signature']) for d in parts)
for label,s in (('copy',allt),('pictures',pic)):
    for pat in [r'compatib',r'\b15 languages\b',r'languages?\b',r'translat',r'\bconnected\b',r'\blinked\b',r'\blinks?\b',r'Excel\s*(20\d\d|365|97|2007|2010|2013|2016|2019|2021)',r'\bsimple ?practice\b',r'therapynotes',r'\betsy\b',r'gumroad',r'\bzoom\b',r'stripe',r'paypal',r'quickbooks',r'xero',r'hipaa',r'\bcpt\b',r'\bnhs\b',r'bacp',r'\bicd\b',r'\bdsm\b',r'medicare',r'\bwhop\b',r'shopify',r'calendly','[$€£]',r'diagnos',r'\bcure\b',r'\btreat(ment)?\b.*\bheal',r'bestseller',r'trusted by',r'limited time',r'last chance',r'only today']:
        if re.search(pat,s,re.I) and not (pat=='diagnos' and False): bad.append(f'{label}: banned pattern {pat}: '+re.search(pat,s,re.I).group(0))
    for g in re.findall(r'\b(Google|Microsoft)\b ?(\w+)?',s):
        if g not in (('Google','Sheets'),('Microsoft','Excel')): bad.append(f'{label}: brand use {g}')
for k in ('tagline',):
    for i,d in enumerate(parts,1):
        chk(len(d[k])<=80 and d[k].lower()!=d['name'].lower(),f'part {i} tagline')
        chk(len(d['signature'])>=5 and all(len(s['name'])<=50 and len(s['why'])<=160 for s in d['signature']),f'part {i} signature limits')
taglines=[d['tagline'] for d in parts]; chk(len(set(taglines))==8,'taglines not unique')
chk(all(d['tagline'] not in (d['listing']['headline'],) for d in parts),'tagline equals listing headline')
print('real per workbook:',per[0]); print('real totals:',tot); print('count mentions checked:',found)
print('PROBLEMS',len(bad)); [print(' ',b) for b in bad]
print('RESULT','FAIL' if bad else 'PASS')
