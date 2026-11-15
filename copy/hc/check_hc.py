#!/usr/bin/env python3
"""Check the Home Care suite English copy and picture texts: limits, banned words, counts equal the real counts."""
import json, re
W='/home/claude/work/'
c=json.load(open(W+'copy/hc/en.json',encoding='utf8')); m=json.load(open(W+'copy/wd/en.json',encoding='utf8'))
fin=json.load(open(W+'hc/listing/final/en.json',encoding='utf8'))
parts=[json.load(open(W+f'hc/hc{n}.en.json',encoding='utf8')) for n in range(1,9)]
bad=[]
def chk(ok,msg):
    if not ok: bad.append(msg)
chk(set(c)==set(m),'keys differ from wd: %s'%sorted(set(c)^set(m)))
chk(c==fin,'listing/final/en.json is not a copy')
for k,l in [('name',40),('title',140),('headline',80),('seo_title',70),('seo_description',160)]: chk(len(c[k])<=l,f'{k} {len(c[k])}>{l}')
chk(900<=len(c['description'])<=2500,'description length %d'%len(c['description']))
t=c['tags']; chk(len(t)==13 and len(set(x.lower() for x in t))==13 and max(map(len,t))<=20,'tags')
chk(len(c['features'])==12 and max(map(len,c['features']))<=90,'features '+str(max(map(len,c['features']))))
chk(len(c['faq'])==6,'faq count')
chk('{files}' in c['stats_note'] and '{pages}' in c['stats_note'],'stats_note placeholders')
d0=c['description'].split('\n')[0]; chk('Excel' in d0 and 'home care' in d0.lower(),'hook line')
for w in ('Google Sheets','14 days','one cell','refund'): chk(w in json.dumps(c),'missing '+w)
chk(any('on my own' in q['q'] for q in c['faq']),'solo owner faq')
# real counts
def cnt(d): return {'tables':len(d['tables']),'tools':len(d['tools']),'forms':len(d['forms']),'documents':len(d['documents']),'checklists':len(d['checklists']),'message texts':len(d['messages']),'dashboard numbers':len(d['dashboard']['kpis']),'charts':len(d['insights']['charts']),'gauges':len(d['insights']['gauges'])}
per=[cnt(d) for d in parts]
for k in per[0]: chk(all(p[k]==per[0][k] for p in per),'counts differ between parts: '+k)
tot={k:sum(p[k] for p in per) for k in per[0]}
txt=c['description']+' '+' '.join(c['features'])+' '+' '.join(q['q']+' '+q['a'] for q in c['faq'])
found=0
for num,noun in re.findall(r'(\d+) (?:ready )?(tables|tools|forms|documents|checklists|message texts|dashboard numbers|charts|gauges)',txt):
    n=int(num); found+=1
    chk(n in (per[0][noun],tot[noun]),f'count {n} {noun} is not real (per workbook {per[0][noun]}, total {tot[noun]})')
chk(re.search(r'\b8 (Excel )?workbooks',c['description']) and len(parts)==8,'8 workbooks')
chk('144 tools' in txt and tot['tools']==144,'144 tools')
# brands from STUDY.md and payer-programme words
BRANDS=['caresmartz','auxo','inmyteam','axiscare','alayacare','shiftcare','phoebe','homecaremag','home care mag','beancount','capterra','birdie','careyaya','homecareatlas','payhip','etsy','gumroad','whop','shopify','wisecaregiving','bocaboca','ali78','realme','printableplanning','vickery','quickbooks','xero','stripe','paypal','zoom','calendly']
PAYER=['nhs','medicare','medicaid','local authority','council','government-funded','veterans','hipaa','cqc','ndis','osha','flsa','irs']
allt=json.dumps(c,ensure_ascii=False).replace('Business Health','Business H.')
pic=' '.join(d['tagline']+' '+' '.join(s['name']+' '+s['why'] for s in d['signature']) for d in parts)
for label,s in (('copy',allt),('pictures',pic)):
    low=s.lower()
    for b in BRANDS+PAYER:
        if re.search(r'(?<![a-z])'+re.escape(b)+r'(?![a-z])',low): bad.append(f'{label}: banned name {b}')
    for pat in [r'compatib',r'15 languages',r'translat',r'multilingual',r'\bconnected\b',r'\blinked\b',r'\blinks?\b',r'Excel\s*(20\d\d|365|97)',r'[$€£]',r'diagnos',r'clinical',r'(?<!non-)(?<!non )\bmedical',r'\bhealth',r'\bsafe',r'\bsafety',r'\bcure\b',r'bestseller',r'trusted by',r'limited time',r'last chance',r'only today',r'in minutes',r'whatsapp',r'review',r'testimonial',r'\bmacros?\b(?<!no macros)',r'\blicen[cs]e',r'\blaw\b',r'\bapp\b(?<!an app)(?<!no app)',r'perfect|ultimate|amazing|powerful']:
        mt=re.search(pat,s,re.I)
        if mt: bad.append(f'{label}: banned pattern {pat}: {mt.group(0)} ... '+s[max(0,mt.start()-40):mt.end()+30].replace("\n"," "))
    for g in re.findall(r'\b(Google|Microsoft)\b ?(\w+)?',s):
        if g not in (('Google','Sheets'),('Microsoft','Excel')): bad.append(f'{label}: brand use {g}')
for i,d in enumerate(parts,1):
    chk(len(d['tagline'])<=80 and d['tagline'].lower()!=d['name'].lower(),f'part {i} tagline')
    chk(all(len(s['name'])<=50 and len(s['why'])<=160 for s in d['signature']),f'part {i} signature lengths '+str(max(len(s['why']) for s in d['signature'])))
    chk(d['tagline']!=d['listing']['headline'],f'part {i} tagline equals listing headline')
    chk(d['tagline'] not in [s['why'] for s in d['signature']],'tagline repeats a line')
chk(len({d['tagline'] for d in parts})==8,'taglines not unique')
print('lengths: name',len(c['name']),'title',len(c['title']),'headline',len(c['headline']),'seo_title',len(c['seo_title']),'seo_desc',len(c['seo_description']),'description',len(c['description']),'max feature',max(map(len,c['features'])))
print('tagline lengths',[len(d['tagline']) for d in parts])
print('real per workbook:',per[0]); print('real totals:',tot); print('count mentions checked:',found)
print('PROBLEMS',len(bad)); [print(' ',b) for b in bad]
print('RESULT','FAIL' if bad else 'PASS')
