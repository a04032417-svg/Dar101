#!/usr/bin/env python3
"""Check the Nonprofit suite English copy and picture texts: limits, banned words, counts equal the real counts."""
import json, re
W='/home/claude/work/'
c=json.load(open(W+'copy/np/en.json',encoding='utf8')); m=json.load(open(W+'copy/wd/en.json',encoding='utf8'))
fin=json.load(open(W+'np/listing/final/en.json',encoding='utf8'))
bad=[]
def chk(ok,msg):
    if not ok: bad.append(msg)
chk(set(c)==set(m),'keys differ from wd: %s'%sorted(set(c)^set(m)))
chk(c==fin,'listing/final/en.json is not a copy')
for k,l in [('name',40),('title',140),('headline',80),('seo_title',70),('seo_description',160)]: chk(len(c[k])<=l,f'{k} {len(c[k])}>{l}')
chk(900<=len(c['description'])<=2500,'description length %d'%len(c['description']))
t=c['tags']; chk(len(t)==13 and len(set(x.lower() for x in t))==13 and max(map(len,t))<=20,'tags')
chk(len(c['features'])==12 and max(map(len,c['features']))<=90,'features')
chk(len(c['faq'])==6,'faq count')
chk('{files}' in c['stats_note'] and '{pages}' in c['stats_note'],'stats_note placeholders')
chk('{pages}' in c['description'],'description lacks {pages}')
parts=[json.load(open(W+f'np/np{n}.en.json',encoding='utf8')) for n in range(1,9)]
def cnt(d): return {'tables':len(d['tables']),'tools':len(d['tools']),'forms':len(d['forms']),'documents':len(d['documents']),'checklists':len(d['checklists']),'message texts':len(d['messages']),'dashboard numbers':len(d['dashboard']['kpis']),'charts':len(d['insights']['charts']),'gauges':len(d['insights']['gauges'])}
per=[cnt(d) for d in parts]
for k in per[0]: chk(all(p[k]==per[0][k] for p in per),'counts differ between parts: '+k)
tot={k:sum(p[k] for p in per) for k in per[0]}
txt=c['description']+' '+' '.join(c['features'])+' '+' '.join(q['q']+' '+q['a'] for q in c['faq'])
found=0
for num,noun in re.findall(r'(\d+) (tables|tools|forms|documents|checklists|message texts|ready message texts|dashboard numbers|charts|gauges)',txt):
    noun=noun.replace('ready ',''); n=int(num); found+=1
    chk(n in (per[0][noun],tot[noun]),f'count {n} {noun} is not real (per workbook {per[0][noun]}, total {tot[noun]})')
chk(re.search(r'\b8 (Excel )?workbooks',c['description']) and len(parts)==8,'8 workbooks')
chk('144 tools' in txt and tot['tools']==144 and '160 tables' in txt and tot['tables']==160,'totals')
names=[d['name'] for d in parts]; chk(all(n in c['description'] for n in names),'part names missing in description')
allt=json.dumps(c,ensure_ascii=False)
pic=' '.join(d['tagline']+' '+' '.join(s['name']+' '+s['why'] for s in d['signature']) for d in parts)
brands=r'bloomerang|capterra|donorperfect|\bneon\b|virtuous|zeffy|little green light|keela|softr|donorsnap|grantwatch|jmco|nonprofitpro|nonprofit times|independent sector|360matchpro|costbench|payhip|etsy|canva|gumroad|shopify|whop|reconciledbooks|trackerpro|drtracker|readyfile|reddit|quickbooks|xero|stripe|paypal|\bword\b|calendly|\bzoom\b'
laws=r'gift aid|501\(?c|form 990|\b990\b|\birs\b|hmrc|quid pro quo|\bafp\b|\bfep\b|hipaa|gaap|fasb|charity commission|1099|\bgdpr\b|\bw-?9\b'
for label,s in (('copy',allt),('pictures',pic)):
    for pat in [r'compatib',r'15 languages',r'languages?\b',r'translat',r'\bconnected\b',r'\blinked\b',r'\blinks?\b',r'Excel\s*(20\d\d|365|97)',brands,laws,r'[$€£]',r'bestseller',r'trusted by',r'limited time',r'last chance',r'only today',r'\bperfect\b',r'\bultimate\b',r'guarantee[sd]? (grant|donat|result)']:
        mm=re.search(pat,s,re.I)
        if mm: bad.append(f'{label}: banned pattern {pat[:30]}: {mm.group(0)}')
    for g in re.findall(r'\b(Google|Microsoft)\b ?(\w+)?',s):
        if g not in (('Google','Sheets'),('Microsoft','Excel')): bad.append(f'{label}: brand use {g}')
for i,d in enumerate(parts,1):
    chk(len(d['tagline'])<=80 and d['tagline'].lower()!=d['name'].lower(),f'part {i} tagline')
    chk(5<=len(d['signature'])<=16 and all(len(s['name'])<=50 and len(s['why'])<=160 for s in d['signature']),f'part {i} signature limits')
    chk(d['tagline']!=d['listing']['headline'],f'part {i} tagline equals listing headline')
    chk(len({s['name'].lower() for s in d['signature']})==len(d['signature']),f'part {i} duplicate signature names')
chk(len({d['tagline'] for d in parts})==8,'taglines not unique')
print('title %d, headline %d, seo_title %d, seo_description %d, description %d'%tuple(len(c[k]) for k in ('title','headline','seo_title','seo_description','description')))
print('real per workbook:',per[0]); print('real totals:',tot); print('count mentions checked:',found)
print('PROBLEMS',len(bad)); [print(' ',b) for b in bad]
print('RESULT','FAIL' if bad else 'PASS')
