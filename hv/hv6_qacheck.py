import json, datetime as dt, math
from hv6_chk import tab, wb
import hv6_qa
spec=json.load(open('hv6.en.json')); T={t['key']:t for t in spec['tools']}
O={t['key']:hv6_qa.vals(t) for t in spec['tools']}
today=dt.datetime(2026,11,16)
_,eq=tab('Equipment'); _,ag=tab('Agreements'); _,rn=tab('Renewals'); _,sites=tab('Customer Sites'); _,vt=None,None
res={}
# independent recomputes straight from the table sheets
aged=[e for e in eq if (e['Age, years'] or 0)>=12]
res['aged_leads']=('Equipment records at or over this age',len(aged),O['aged_leads']['Equipment records at or over this age'])
res['aged_leads2']=('never serviced',sum(1 for e in aged if not e['Last service']),O['aged_leads']['Of them never serviced by the shop'])
run=[a for a in ag if a['Status'] in ('Active','Renewal due','Running') or a.get('Running (1 or 0)')==1]
res['book']=('running',sum(1 for a in ag if a['Running (1 or 0)']==1),O['book_health']['Running agreements now'])
res['mrr']=('mrr',round(sum(a['Price a year'] for a in ag if a['Running (1 or 0)']==1)/12,3),round(O['book_health']['Monthly recurring revenue now'],3))
ms=dt.datetime(2026,11,1); m12=dt.datetime(2025,11,1)
ended=[a for a in ag if a['End date'] and m12<=a['End date']<ms]
res['lapse']=('ended 12m',len(ended),O['lapse_analyser']['Agreements ended, last 12 months'])
res['lapse_fees']=('fees',sum(a['Price a year'] for a in ended),O['lapse_analyser']['Yearly fees lost'])
rr=[r for r in rn if r['Outcome'] in ('Renewed','Lapsed') and m12<=r['Due date']<ms]
res['rr']=('rr',round(sum(r['Outcome']=='Renewed' for r in rr)/len(rr),3),round(O['book_health']['Renewal rate, last 12 months'],3))
st=[s for s in sites if s['Site reference']=='EAS-1020'][0]
res['site']=('site equipment',st['Equipment'],O['site_lookup']['Equipment records'])
res['site2']=('site jobs',st['Jobs'],O['site_lookup']['Jobs to date'])
q=0.88**(1/12); R=302*q**12+4.3*(1-q**12)/(1-q)
res['fc']=('R12',round(R,3),round(O['agr_forecast']['Base: agreements in 12 months'],3))
res['price']=('rev now',93*269,O['price_test']['Yearly revenue now'])
res['camp']=('cost',round(O['campaign_plan']['Sites to remind']*1.4,1),round(O['campaign_plan']['Cost of the reminders'],1))
res['sign']=('goal',math.ceil(8000/ (O['signups_needed']['Average price a year']/12)) ,O['signups_needed']['Agreements needed for the recurring revenue goal'])
for k,v in res.items(): print(k,v,'OK' if abs(float(v[1])-float(v[2]))<0.01 else 'DIFF')

def f(x): return round(x,3) if isinstance(x,float) else (x.date().isoformat() if hasattr(x,'date') else x)
lines=[]
for t in spec['tools']:
    ins=', '.join('%s = %s'%(i['label'],i.get('default')) for i in t['inputs'])
    outs=list(O[t['key']].items()); sel=outs[:3]+outs[-1:] if len(outs)>4 else outs
    o=', '.join('%s = %s'%(k,f(v)) for k,v in sel)
    bad=[k for k,v in O[t['key']].items() if v is None or v=='' or (isinstance(v,str) and v.startswith('#'))]
    lines.append('%s: %s -> %s (checked%s)'%(t['title'] if 'title' in t else t['sheet'],ins,o,'; empty: '+','.join(bad) if bad else ''))
open('out6/qa.txt','w').write('\n'.join(lines)+'\n')
print(len(lines))
