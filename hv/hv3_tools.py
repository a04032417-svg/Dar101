"""Part 3: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv3_lists import *
import hv3_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def X(t, c, idx): return 'INDEX({range:%s.%s},%s)' % (t, c, idx)
def R(t, c): return '{range:%s.%s}' % (t, c)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
Y12 = 'DATE(YEAR({today}),MONTH({today})-12,1)'
SEASON = 'DATE(YEAR({today}),MONTH({today})-MOD(MONTH({today})-3,3),1)'
WHT = LV('jobtype', key('jobtype', 'Water heater replacement'))
P12 = tok('period', 'Last 12 months')

# ---- defaults taken from the demo data so each tool opens on a real case
_done = [j for j in D.JALL if D.shown(j) and j['status'] == 'Completed']
_wh = [j for j in _done if j['job_type'] == 'Water heater replacement' and not j['is_callback'] and j['date'] > ago(30) and j['hours'] > 0]
DEF_JOB = (_wh[-1] if _wh else [j for j in _done if not j['is_callback']][-1])['job_id']
_cbs = [b for b in callback_rows() if b['date'] > ago(80) and b['original_job'] in D.JD and D.shown(D.JD[b['original_job']]) and D.JD[b['original_job']]['price'] > 0]
DEF_CB = _cbs[-1]['callback_id']
_tm = [r for r in D.tick_month_d() if month_start(12).isoformat() <= r['month'] < month_start(0).isoformat()]
def _s(k): return sum(r[k] for r in _tm)
DEF_REV = round(_s('revenue') / 12); DEF_LAB = round(_s('labour_cost') / 12); DEF_PAR = round(_s('parts_cost') / 12)
_cb12 = sum(b['cost'] for b in callback_rows() if b['date'] >= month_start(12).isoformat() and b['date'] < month_start(0).isoformat())
DEF_OTH = round((_s('sub_cost') + _s('other_cost') + _cb12) / 12)
DEF_JOBS_M = round(_s('jobs') / 12)
_r90 = [j for j in D.BASE if j['date'] > D.D90 and j['price'] > 0]
DEF_JOBS_WEEK = round(len(_r90) / (90 / 7.0), 1)
DEF_MARGIN_JOB = round(sum(j['margin'] for j in _r90) / len(_r90))
LASTM = month_start(1).isoformat()

tools = [
    # 1
    TOOL('job_costing', 'Job Costing per Job', 'Job costing per job with a verdict',
         'Type a job id: price against parts, labour (hours times loaded rate), permit, disposal, subcontract and vehicle give margin and a one-line verdict; try an extra hour or dearer parts.', [
        I('job', 'Job ID', DEF_JOB, 'text'), I('extra_hours', 'Extra hours on site to test', 0, 'num'), I('parts_change', 'Parts cost change to test', 0, 'pct'), I('assistant_rate', 'Assistant pay per hour', 20.5)], [
        O('Job type', 'text', X('jobs', 'job_type', 'MATCH({in:job},%s,0)' % R('jobs', 'job_id'))), O('Technician', 'text', X('jobs', 'technician', 'MATCH({in:job},%s,0)' % R('jobs', 'job_id'))),
        O('Price', 'money', 'INDEX(%s,MATCH({in:job},%s,0))' % (R('jobs', 'price'), R('jobs', 'job_id'))), O('Hours on site', 'num', 'INDEX(%s,MATCH({in:job},%s,0))' % (R('jobs', 'hours'), R('jobs', 'job_id'))),
        O('Labour cost entered on the job', 'money', 'INDEX(%s,MATCH({in:job},%s,0))' % (R('jobs', 'labour_cost'), R('jobs', 'job_id'))),
        O('Labour from hours times loaded rate', 'money', 'INDEX(%s,MATCH({in:job},%s,0))*INDEX(%s,MATCH(INDEX(%s,MATCH({in:job},%s,0)),%s,0))*(1+{set:burden_pct})+INDEX(%s,MATCH({in:job},%s,0))*{in:assistant_rate}*(1+{set:burden_pct})' %
          (R('jobs', 'hours'), R('jobs', 'job_id'), R('technicians', 'hourly_rate'), R('jobs', 'technician'), R('jobs', 'job_id'), R('technicians', 'technician'), R('jobs', 'assistant_hours'), R('jobs', 'job_id'))),
        O('Parts cost', 'money', 'INDEX(%s,MATCH({in:job},%s,0))' % (R('jobs', 'parts_cost'), R('jobs', 'job_id'))),
        O('Permit and disposal', 'money', 'INDEX(%s,MATCH({in:job},%s,0))+INDEX(%s,MATCH({in:job},%s,0))' % (R('jobs', 'permit_fee'), R('jobs', 'job_id'), R('jobs', 'disposal'), R('jobs', 'job_id'))),
        O('Subcontract cost', 'money', 'INDEX(%s,MATCH({in:job},%s,0))' % (R('jobs', 'sub_cost'), R('jobs', 'job_id'))), O('Vehicle cost', 'money', 'INDEX(%s,MATCH({in:job},%s,0))' % (R('jobs', 'vehicle_cost'), R('jobs', 'job_id'))),
        O('Total cost', 'money', 'INDEX(%s,MATCH({in:job},%s,0))' % (R('jobs', 'total_cost'), R('jobs', 'job_id'))), O('Margin', 'money', 'INDEX(%s,MATCH({in:job},%s,0))' % (R('jobs', 'margin'), R('jobs', 'job_id'))),
        O('Margin percent', 'pct', 'INDEX(%s,MATCH({in:job},%s,0))' % (R('jobs', 'margin_pct'), R('jobs', 'job_id'))),
        O('Target margin of the job type', 'pct', 'IFERROR(INDEX(%s,MATCH(INDEX(%s,MATCH({in:job},%s,0)),%s,0)),0)' % (R('job_types', 'target_margin'), R('jobs', 'job_type'), R('jobs', 'job_id'), R('job_types', 'job_type'))),
        O('Verdict', 'text', 'INDEX(%s,MATCH({in:job},%s,0))' % (R('jobs', 'cause'), R('jobs', 'job_id'))),
        O('Margin after the test', 'money', 'INDEX(%s,MATCH({in:job},%s,0))-{in:extra_hours}*IFERROR(INDEX(%s,MATCH({in:job},%s,0))/INDEX(%s,MATCH({in:job},%s,0)),0)-INDEX(%s,MATCH({in:job},%s,0))*{in:parts_change}' %
          (R('jobs', 'margin'), R('jobs', 'job_id'), R('jobs', 'labour_cost'), R('jobs', 'job_id'), R('jobs', 'hours'), R('jobs', 'job_id'), R('jobs', 'parts_cost'), R('jobs', 'job_id'))),
        O('Price needed for the target margin', 'money', 'IFERROR(INDEX(%s,MATCH({in:job},%s,0))/(1-INDEX(%s,MATCH(INDEX(%s,MATCH({in:job},%s,0)),%s,0))),0)' % (R('jobs', 'total_cost'), R('jobs', 'job_id'), R('job_types', 'target_margin'), R('jobs', 'job_type'), R('jobs', 'job_id'), R('job_types', 'job_type')))],
         GR('What if', ('One more hour on site', {'extra_hours': 1}), ('Two more hours', {'extra_hours': 2}), ('Parts cost 10 percent higher', {'parts_change': 0.1}), ('Parts cost 10 percent lower', {'parts_change': -0.1}),
            ('One more hour, parts 10 percent higher', {'extra_hours': 1, 'parts_change': 0.1}))),
    # 2
    TOOL('est_vs_actual', 'Estimate versus Actual', 'Estimate versus actual cost by job, last 90 days',
         'Compares each job with the all-in cost of its price book task: the five jobs that ran furthest over, the hours and parts that caused it and the usual leak.', [
        I('min_over', 'Count jobs over the book by more than', 50)], [
        O('Jobs over the book, last 90 days', 'int', 'COUNTIFS(%s,">0")' % R('jobs', 'overrun')), O('Jobs over by more than the limit', 'int', 'COUNTIFS(%s,">"&{in:min_over})' % R('jobs', 'overrun')),
        O('Cost over the book, last 90 days', 'money', 'SUM(%s)' % R('jobs', 'overrun')), O('Hours over the book on those jobs', 'num', 'SUMIFS(%s,%s,">0")' % (R('jobs', 'hours_over'), R('jobs', 'overrun'))),
        O('Parts over the book on those jobs', 'money', 'SUMIFS(%s,%s,">0")' % (R('jobs', 'parts_over'), R('jobs', 'overrun'))),
        O('Labour value of the extra hours', 'money', 'IFERROR(SUMIFS(%s,%s,">0")*SUMIFS(%s,%s,">0")/SUMIFS(%s,%s,">0"),0)' % (R('jobs', 'hours_over'), R('jobs', 'overrun'), R('jobs', 'labour_cost'), R('jobs', 'overrun'), R('jobs', 'hours'), R('jobs', 'overrun'))),
        O('Usual leak', 'text', 'IF(SUMIFS(%s,%s,">0")>=IFERROR(SUMIFS(%s,%s,">0")*SUMIFS(%s,%s,">0")/SUMIFS(%s,%s,">0"),0),%s,%s)' %
          (R('jobs', 'parts_over'), R('jobs', 'overrun'), R('jobs', 'hours_over'), R('jobs', 'overrun'), R('jobs', 'labour_cost'), R('jobs', 'overrun'), R('jobs', 'hours'), R('jobs', 'overrun'), c6('Parts are the cost to watch'), c6('Hours are the cost to watch')))] +
        [O('Number %d job' % k, 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0))&" "&INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (R('jobs', 'job_id'), R('jobs', 'overkey'), k, R('jobs', 'overkey'), R('jobs', 'job_type'), R('jobs', 'overkey'), k, R('jobs', 'overkey'))) for k in range(1, 6)] +
        [O('Number %d cost over the book' % k, 'money', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),0)' % (R('jobs', 'overrun'), R('jobs', 'overkey'), k, R('jobs', 'overkey'))) for k in range(1, 6)],
         GR('What if', ('Limit 25', {'min_over': 25}), ('Limit 100', {'min_over': 100}), ('Limit 200', {'min_over': 200}), ('Limit 400', {'min_over': 400}))),
    # 3
    TOOL('margin_check', 'Margin by Job Type Check', 'Margin check of all 15 job types against their targets',
         'Compares the last 120 days of every job type with its own target and with the 12 months before; names the type that fell furthest and the type furthest under its target.', [
        I('fall_pts', 'A fall of this many points counts as falling', 0.03, 'pct')], [
        O('Job types under target', 'int', 'COUNTIFS(%s,%s)' % (R('margin_jt', 'status'), c2('Under target'))), O('Job types close to target', 'int', 'COUNTIFS(%s,%s)' % (R('margin_jt', 'status'), c2('Close to target'))),
        O('Job types on target', 'int', 'COUNTIFS(%s,%s)' % (R('margin_jt', 'status'), c2('On target'))), O('Job types falling', 'int', 'COUNTIFS(%s,"<"&-{in:fall_pts})' % R('margin_jt', 'change_pts')),
        O('Type that fell furthest', 'text', X('margin_jt', 'job_type', 'MATCH(MIN(%s),%s,0)' % (R('margin_jt', 'change_pts'), R('margin_jt', 'change_pts')))), O('Its change in points', 'pct', 'MIN(%s)' % R('margin_jt', 'change_pts')),
        O('Its margin, last 120 days', 'pct', X('margin_jt', 'margin_pct_120', 'MATCH(MIN(%s),%s,0)' % (R('margin_jt', 'change_pts'), R('margin_jt', 'change_pts')))),
        O('Its target margin', 'pct', X('margin_jt', 'target', 'MATCH(MIN(%s),%s,0)' % (R('margin_jt', 'change_pts'), R('margin_jt', 'change_pts')))),
        O('Second type that fell', 'text', 'IFERROR(' + X('margin_jt', 'job_type', 'MATCH(SMALL(%s,2),%s,0)' % (R('margin_jt', 'change_pts'), R('margin_jt', 'change_pts'))) + ',"")'), O('Its change in points', 'pct', 'SMALL(%s,2)' % R('margin_jt', 'change_pts')),
        O('Type furthest under its target', 'text', X('margin_jt', 'job_type', 'MATCH(MIN(%s),%s,0)' % (R('margin_jt', 'gap'), R('margin_jt', 'gap')))), O('Its gap to target', 'pct', 'MIN(%s)' % R('margin_jt', 'gap')),
        O('Shop margin, last 120 days', 'pct', 'IFERROR(SUM(%s)/SUM(%s),0)' % (R('margin_jt', 'margin_120'), R('margin_jt', 'revenue_120'))),
        O('Shop margin, 12 months before', 'pct', 'IFERROR((SUM(%s)-SUM(%s))/SUM(%s),0)' % (R('margin_jt', 'revenue_p12'), R('margin_jt', 'cost_p12'), R('margin_jt', 'revenue_p12'))),
        O('Verdict', 'text', 'IF(COUNTIFS(%s,%s)>0,%s,%s)' % (R('margin_jt', 'status'), c2('Under target'), c6('Re-price these types'), c6('Every type is on target')))],
         GR('What if', ('A fall of 1 point counts', {'fall_pts': 0.01}), ('A fall of 2 points counts', {'fall_pts': 0.02}), ('A fall of 5 points counts', {'fall_pts': 0.05}))),
    # 4
    TOOL('wh_watch', 'Water Heater Margin Watch', 'Water heater margin watch and price needed',
         'Margin of water heater replacements since the unit cost rose against the target: the flat price needed, the profit missed, and whether raising the price pays after the jobs it may lose.', [
        I('months', 'Recent months to look at', 4, 'int'), I('rise', 'Price rise to test', 0.08, 'pct'), I('lost', 'Share of jobs you could lose after the rise (set your own)', 0.10, 'pct')], [
        O('Margin percent, recent months', 'pct', 'IFERROR(1-SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))/SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1)),0)' %
          (R('wh_month', 'cost'), R('wh_month', 'month'), R('wh_month', 'revenue'), R('wh_month', 'month'))),
        O('Margin percent, the 6 months before', 'pct', 'IFERROR(1-SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}-5,1),%s,"<"&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))/SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}-5,1),%s,"<"&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1)),0)' %
          (R('wh_month', 'cost'), R('wh_month', 'month'), R('wh_month', 'month'), R('wh_month', 'revenue'), R('wh_month', 'month'), R('wh_month', 'month'))),
        O('Target margin', 'pct', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('job_types', 'target_margin'), WHT, R('job_types', 'job_type'))),
        O('Gap to target', 'pct', 'IFERROR(1-SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))/SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1)),0)-IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' %
          (R('wh_month', 'cost'), R('wh_month', 'month'), R('wh_month', 'revenue'), R('wh_month', 'month'), R('job_types', 'target_margin'), WHT, R('job_types', 'job_type'))),
        O('Average price per job, recent months', 'money', 'IFERROR(SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))/SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1)),0)' %
          (R('wh_month', 'revenue'), R('wh_month', 'month'), R('wh_month', 'jobs'), R('wh_month', 'month'))),
        O('Average cost per job, recent months', 'money', 'IFERROR(SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))/SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1)),0)' %
          (R('wh_month', 'cost'), R('wh_month', 'month'), R('wh_month', 'jobs'), R('wh_month', 'month'))),
        O('Flat price needed for the target', 'money', 'IFERROR(SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))/SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))/(1-INDEX(%s,MATCH(%s,%s,0))),0)' %
          (R('wh_month', 'cost'), R('wh_month', 'month'), R('wh_month', 'jobs'), R('wh_month', 'month'), R('job_types', 'target_margin'), WHT, R('job_types', 'job_type'))),
        O('Profit missed in the recent months', 'money', 'IFERROR(INDEX(%s,MATCH(%s,%s,0))*SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))-(SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))-SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))),0)' %
          (R('job_types', 'target_margin'), WHT, R('job_types', 'job_type'), R('wh_month', 'revenue'), R('wh_month', 'month'), R('wh_month', 'revenue'), R('wh_month', 'month'), R('wh_month', 'cost'), R('wh_month', 'month'))),
        O('Unit cost rise since the first month', 'pct', 'IFERROR(INDEX(%s,COUNT(%s))/INDEX(%s,1)-1,0)' % (R('wh_month', 'unit_cost'), R('wh_month', 'unit_cost'), R('wh_month', 'unit_cost'))),
        O('Jobs a month, recent months', 'num', 'IFERROR(SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))/{in:months},0)' % (R('wh_month', 'jobs'), R('wh_month', 'month'))),
        O('Profit a month at today price', 'money', 'IFERROR((SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))-SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1)))/{in:months},0)' %
          (R('wh_month', 'revenue'), R('wh_month', 'month'), R('wh_month', 'cost'), R('wh_month', 'month'))),
        O('Profit a month after the rise and the jobs lost', 'money', 'IFERROR((1-{in:lost})*(SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))*(1+{in:rise})-SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1)))/{in:months},0)' %
          (R('wh_month', 'revenue'), R('wh_month', 'month'), R('wh_month', 'cost'), R('wh_month', 'month'))),
        O('Break-even share of jobs lost for this rise', 'pct', 'IFERROR(1-(SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))-SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1)))/(SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))*(1+{in:rise})-SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))),0)' %
          (R('wh_month', 'revenue'), R('wh_month', 'month'), R('wh_month', 'cost'), R('wh_month', 'month'), R('wh_month', 'revenue'), R('wh_month', 'month'), R('wh_month', 'cost'), R('wh_month', 'month'))),
        O('Verdict', 'text', 'IF((1-{in:lost})*(SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))*(1+{in:rise})-SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1)))>SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1))-SUMIFS(%s,%s,">="&DATE(YEAR({today}),MONTH({today})-{in:months}+1,1)),%s,%s)' %
          (R('wh_month', 'revenue'), R('wh_month', 'month'), R('wh_month', 'cost'), R('wh_month', 'month'), R('wh_month', 'revenue'), R('wh_month', 'month'), R('wh_month', 'cost'), R('wh_month', 'month'), c6('Raise the price'), c6('Hold the price')))],
         GR('What if', ('Rise 5 percent, lose 5 percent of jobs', {'rise': 0.05, 'lost': 0.05}), ('Rise 8 percent, lose 10 percent', {'rise': 0.08, 'lost': 0.10}), ('Rise 10 percent, lose 15 percent', {'rise': 0.10, 'lost': 0.15}),
            ('Rise 12 percent, lose 25 percent', {'rise': 0.12, 'lost': 0.25}), ('Look at 3 months', {'months': 3}), ('Look at 6 months', {'months': 6}))),
    # 5
    TOOL('losing_finder', 'Losing-Money Job Finder', 'Losing-money job finder, last 90 days',
         'Ranks the jobs of the last 90 days by the money they lost, with the technician and the cause, and counts thin jobs; the four loss causes show what to fix first.', [
        I('min_loss', 'Count losses of at least', 25)], [
        O('Jobs that lost money', 'int', 'COUNTIFS(%s,">="&{in:min_loss},%s,">"&({today}-90))' % (R('jobs', 'lost'), R('jobs', 'date'))),
        O('Money lost', 'money', 'SUMIFS(%s,%s,">"&({today}-90))' % (R('jobs', 'lost'), R('jobs', 'date'))),
        O('Share of jobs that lost money', 'pct', 'IFERROR(COUNTIFS(%s,">="&{in:min_loss},%s,">"&({today}-90))/COUNTIFS(%s,">"&({today}-90)),0)' % (R('jobs', 'lost'), R('jobs', 'date'), R('jobs', 'date'))),
        O('Thin jobs, still making money', 'int', 'COUNTIFS(%s,%s,%s,">"&({today}-90))' % (R('jobs', 'cause'), c1('Thin margin'), R('jobs', 'date'))),
        O('Losses caused by callbacks', 'money', 'SUMIFS(%s,%s,%s,%s,">"&({today}-90))' % (R('jobs', 'lost'), R('jobs', 'cause'), c1('Lost money: callback'), R('jobs', 'date'))),
        O('Losses caused by parts', 'money', 'SUMIFS(%s,%s,%s,%s,">"&({today}-90))' % (R('jobs', 'lost'), R('jobs', 'cause'), c1('Lost money: parts'), R('jobs', 'date'))),
        O('Losses caused by hours', 'money', 'SUMIFS(%s,%s,%s,%s,">"&({today}-90))' % (R('jobs', 'lost'), R('jobs', 'cause'), c1('Lost money: hours'), R('jobs', 'date'))),
        O('Losses caused by price', 'money', 'SUMIFS(%s,%s,%s,%s,">"&({today}-90))' % (R('jobs', 'lost'), R('jobs', 'cause'), c1('Lost money: price'), R('jobs', 'date')))] +
        [O('Number %d job' % k, 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0))&" "&INDEX(%s,MATCH(LARGE(%s,%d),%s,0))&" "&INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' %
           (R('jobs', 'job_id'), R('jobs', 'lostkey'), k, R('jobs', 'lostkey'), R('jobs', 'technician'), R('jobs', 'lostkey'), k, R('jobs', 'lostkey'), R('jobs', 'cause'), R('jobs', 'lostkey'), k, R('jobs', 'lostkey'))) for k in range(1, 7)],
         GR('What if', ('Count losses of 10 or more', {'min_loss': 10}), ('Count losses of 50 or more', {'min_loss': 50}), ('Count losses of 100 or more', {'min_loss': 100}))),
    # 6
    TOOL('ticket_ranks', 'Ticket and Margin Ranks', 'Average ticket by technician, van, site type and month',
         'Ranks the last 12 months of each table against the shop average ticket: the highest and the lowest cell, and the largest gap in money.', [
        I('gap_alert', 'A gap of at least this is worth a look', 40)], [
        O('Shop average ticket, 12 months', 'money', 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s),0)' % (R('tick_tech', 'revenue'), R('tick_tech', 'period'), P12, R('tick_tech', 'jobs'), R('tick_tech', 'period'), P12)),
        O('Highest technician', 'text', X('tick_tech', 'technician', 'MATCH(LARGE(%s,1),%s,0)' % (R('tick_tech', 't12'), R('tick_tech', 't12')))), O('Its average ticket', 'money', 'LARGE(%s,1)' % R('tick_tech', 't12')),
        O('Lowest technician', 'text', X('tick_tech', 'technician', 'MATCH(SMALL(%s,1),%s,0)' % (R('tick_tech', 't12lo'), R('tick_tech', 't12lo')))), O('Its average ticket', 'money', 'SMALL(%s,1)' % R('tick_tech', 't12lo')),
        O('Highest van', 'text', X('tick_van', 'van', 'MATCH(LARGE(%s,1),%s,0)' % (R('tick_van', 't12'), R('tick_van', 't12')))), O('Its average ticket', 'money', 'LARGE(%s,1)' % R('tick_van', 't12')),
        O('Lowest van', 'text', X('tick_van', 'van', 'MATCH(SMALL(%s,1),%s,0)' % (R('tick_van', 't12lo'), R('tick_van', 't12lo')))), O('Its average ticket', 'money', 'SMALL(%s,1)' % R('tick_van', 't12lo')),
        O('Highest site type', 'text', X('tick_site', 'site_type', 'MATCH(LARGE(%s,1),%s,0)' % (R('tick_site', 't12'), R('tick_site', 't12')))), O('Its average ticket', 'money', 'LARGE(%s,1)' % R('tick_site', 't12')),
        O('Lowest site type', 'text', X('tick_site', 'site_type', 'MATCH(SMALL(%s,1),%s,0)' % (R('tick_site', 't12lo'), R('tick_site', 't12lo')))), O('Its average ticket', 'money', 'SMALL(%s,1)' % R('tick_site', 't12lo')),
        O('Highest month', 'date', X('tick_month', 'month', 'MATCH(LARGE(%s,1),%s,0)' % (R('tick_month', 't12'), R('tick_month', 't12')))), O('Its average ticket', 'money', 'LARGE(%s,1)' % R('tick_month', 't12')),
        O('Lowest month', 'date', X('tick_month', 'month', 'MATCH(SMALL(%s,1),%s,0)' % (R('tick_month', 't12lo'), R('tick_month', 't12lo')))), O('Its average ticket', 'money', 'SMALL(%s,1)' % R('tick_month', 't12lo')),
        O('Widest gap in money', 'money', 'MAX(LARGE(%s,1)-SMALL(%s,1),LARGE(%s,1)-SMALL(%s,1),LARGE(%s,1)-SMALL(%s,1),LARGE(%s,1)-SMALL(%s,1))' %
          (R('tick_tech', 't12'), R('tick_tech', 't12lo'), R('tick_van', 't12'), R('tick_van', 't12lo'), R('tick_site', 't12'), R('tick_site', 't12lo'), R('tick_month', 't12'), R('tick_month', 't12lo'))),
        O('Verdict', 'text', 'IF(MAX(LARGE(%s,1)-SMALL(%s,1),LARGE(%s,1)-SMALL(%s,1),LARGE(%s,1)-SMALL(%s,1),LARGE(%s,1)-SMALL(%s,1))>={in:gap_alert},%s,%s)' %
          (R('tick_tech', 't12'), R('tick_tech', 't12lo'), R('tick_van', 't12'), R('tick_van', 't12lo'), R('tick_site', 't12'), R('tick_site', 't12lo'), R('tick_month', 't12'), R('tick_month', 't12lo'), c5('Gap is worth a look'), c5('Even')))],
         GR('What if', ('Gap of 20', {'gap_alert': 20}), ('Gap of 100', {'gap_alert': 100}), ('Gap of 250', {'gap_alert': 250}))),
]

# ---- 7 to 18
KIND5 = ['Diagnostic', 'Repair', 'Tune-up', 'Replacement', 'Install']
def KX(col, kind): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('margin_jt', col), tok('jobkind', kind), R('margin_jt', 'kind'))
MPH = R('margin_jt', 'mph'); CBID = 'MATCH({in:callback},%s,0)' % R('callbacks', 'callback_id')
def CBX(col): return 'INDEX(%s,%s)' % (R('callbacks', col), CBID)
def RATE12(t): return 'IFERROR(SUMIFS(%s,%s,{in:technician},%s,%s)/SUMIFS(%s,%s,{in:technician},%s,%s),0)' % (R('cb_tech', 'callbacks'), R('cb_tech', 'technician'), R('cb_tech', 'period'), P12, R('cb_tech', 'jobs'), R('cb_tech', 'technician'), R('cb_tech', 'period'), P12)
SHOP12 = 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s),0)' % (R('cb_tech', 'callbacks'), R('cb_tech', 'period'), P12, R('cb_tech', 'jobs'), R('cb_tech', 'period'), P12)
RB = R('margin_jt', 'rise_buffer')
CBC = R('cb_reason', 'cost')
TM12 = '%s,">="&%s,%s,"<"&%s' % (R('tick_month', 'month'), Y12, R('tick_month', 'month'), MS)
def TMS(col): return 'SUMIFS(%s,%s)' % (R('tick_month', col), TM12)
TMA = '%s,">="&%s' % (R('tick_month', 'month'), Y12)
def TMSA(col): return 'SUMIFS(%s,%s)' % (R('tick_month', col), TMA)
CT = lambda col, per: 'SUMIFS(%s,%s,%s)' % (R('tick_tech', col), R('tick_tech', 'period'), per)
EQ = 'MATCH({in:job_type},%s,0)' % R('margin_jt', 'job_type')
def JX(col): return 'INDEX(%s,%s)' % (R('margin_jt', col), EQ)
RV = 'IF(AND(%s>0.8,%s<1.2),%s,0)'  # unused

tools += [
    # 7
    TOOL('ticket_mix', 'Ticket Mix Tool', 'Ticket mix: revenue, margin and margin per hour by job kind',
         'Shares of revenue and margin for diagnostic, repair, tune-up, replacement and install work over the last 120 days, and which kind earns the most per hour on site and on the road.', [
        I('move_hours', 'Hours a week you could move to the best kind', 10, 'num')], [
        O('%s share of revenue' % k, 'pct', KX('kind_rev_share', k)) for k in KIND5] + [O('%s share of margin' % k, 'pct', KX('kind_margin_share', k)) for k in KIND5] +
        [O('%s margin per hour' % k, 'money', KX('kind_mph', k)) for k in KIND5] + [
        O('Kind earning the most per hour', 'text', X('margin_jt', 'kind', 'MATCH(MAX(%s),%s,0)' % (R('margin_jt', 'kind_mph'), R('margin_jt', 'kind_mph')))), O('Its margin per hour', 'money', 'MAX(%s)' % R('margin_jt', 'kind_mph')),
        O('Kind earning the least per hour', 'text', X('margin_jt', 'kind', 'MATCH(MIN(%s),%s,0)' % (R('margin_jt', 'kind_mph'), R('margin_jt', 'kind_mph')))),
        O('Margin gained a week by moving those hours', 'money', '{in:move_hours}*(MAX(%s)-MIN(%s))' % (R('margin_jt', 'kind_mph'), R('margin_jt', 'kind_mph'))),
        O('Verdict', 'text', 'IF((MAX(%s)-MIN(%s))/MAX(%s)>0.3,%s,%s)' % (R('margin_jt', 'kind_mph'), R('margin_jt', 'kind_mph'), R('margin_jt', 'kind_mph'), c6('Spread is wide'), c6('Spread is small')))],
         GR('What if', ('Move 5 hours', {'move_hours': 5}), ('Move 20 hours', {'move_hours': 20}), ('Move 40 hours', {'move_hours': 40}))),
    # 8
    TOOL('mph_rank', 'Margin per Hour by Job Type', 'Margin per hour by job type, ranked',
         'Margin divided by hours on site plus drive hours for each job type over the last 120 days: the five best and three weakest types and what moving hours between them earns a week.', [
        I('shift_hours', 'Hours a week to move from the weakest to the best type', 10, 'num')], [
        O('Shop margin per hour', 'money', 'IFERROR(SUM(%s)/(SUM(%s)+SUM(%s)),0)' % (R('margin_jt', 'margin_120'), R('margin_jt', 'hours_120'), R('margin_jt', 'drive_120')))] +
        [O('Best number %d' % k, 'text', X('margin_jt', 'job_type', 'MATCH(LARGE(%s,%d),%s,0)' % (MPH, k, MPH))) for k in range(1, 6)] + [O('Best number %d margin per hour' % k, 'money', 'LARGE(%s,%d)' % (MPH, k)) for k in range(1, 6)] +
        [O('Weakest number %d' % k, 'text', X('margin_jt', 'job_type', 'MATCH(SMALL(%s,%d),%s,0)' % (MPH, k, MPH))) for k in range(1, 3)] + [O('Weakest number %d margin per hour' % k, 'money', 'SMALL(%s,%d)' % (MPH, k)) for k in range(1, 3)] + [
        O('Margin gained a week by moving the hours', 'money', '{in:shift_hours}*(LARGE(%s,1)-SMALL(%s,1))' % (MPH, MPH)),
        O('Verdict', 'text', 'IF(SMALL(%s,1)<0.8*SUM(%s)/(SUM(%s)+SUM(%s)),%s,%s)' % (MPH, R('margin_jt', 'margin_120'), R('margin_jt', 'hours_120'), R('margin_jt', 'drive_120'), c6('Re-price or book less'), c6('Margin looks fine')))],
         GR('What if', ('Move 5 hours', {'shift_hours': 5}), ('Move 20 hours', {'shift_hours': 20}), ('Move 40 hours', {'shift_hours': 40}))),
    # 9
    TOOL('callback_cost', 'Callback Cost Tool', 'Callback cost with who paid and the season to date',
         'Type a callback id: hours, parts and travel linked to the original job give the all-in cost, who paid and its share of the original price; the season to date shows the money these visits take.', [
        I('callback', 'Callback ID', DEF_CB, 'text'), I('cut', 'Fall in callbacks to test', 0.2, 'pct')], [
        O('Original job', 'text', CBX('original_job')), O('Technician of the original job', 'text', CBX('technician')), O('Reason', 'text', CBX('reason')), O('Date', 'date', CBX('date')), O('Hours', 'num', CBX('hours')),
        O('Drive hours', 'num', CBX('drive_hours')), O('Parts cost', 'money', CBX('parts_cost')), O('Labour and travel', 'money', CBX('labour_travel')), O('All-in cost', 'money', CBX('cost')), O('Who paid', 'text', CBX('paid_by')),
        O('Original job price', 'money', CBX('orig_price')), O('Cost as share of the original price', 'pct', 'IFERROR(%s/%s,0)' % (CBX('cost'), CBX('orig_price'))),
        O('Callbacks this season', 'int', 'COUNTIFS(%s,">="&%s)' % (R('callbacks', 'date'), SEASON)), O('Cost of callbacks this season', 'money', 'SUMIFS(%s,%s,">="&%s)' % (R('callbacks', 'cost'), R('callbacks', 'date'), SEASON)),
        O('Saved this season if callbacks fell', 'money', '{in:cut}*SUMIFS(%s,%s,">="&%s)' % (R('callbacks', 'cost'), R('callbacks', 'date'), SEASON)),
        O('Average callback cost, 12 months', 'money', 'IFERROR(SUMIFS(%s,%s,">="&%s)/COUNTIFS(%s,">="&%s),0)' % (R('callbacks', 'cost'), R('callbacks', 'date'), Y12, R('callbacks', 'date'), Y12)),
        O('Verdict', 'text', 'IF(%s>1.5*IFERROR(SUMIFS(%s,%s,">="&%s)/COUNTIFS(%s,">="&%s),0),%s,%s)' % (CBX('cost'), R('callbacks', 'cost'), R('callbacks', 'date'), Y12, R('callbacks', 'date'), Y12, c5('Watch'), c5('Fine')))],
         GR('What if', ('Callbacks fall by 10 percent', {'cut': 0.1}), ('Callbacks fall by 30 percent', {'cut': 0.3}), ('Callbacks fall by half', {'cut': 0.5}))),
    # 10
    TOOL('cb_rate_tool', 'Callback Rate Tool', 'Callback rate by technician and job type',
         'Pick a technician and a job type: the 12-month callback rate, the times the shop rate, the callbacks to cut to reach your target and a verdict (talk this week, watch, fine).', [
        IN('technician', 'Technician', 'list', key('tech', story()['callback_tech']), list='tech'), IN('job_type', 'Job type', 'list', key('jobtype', 'Heating repair'), list='jobtype')], [
        O('Technician callback rate, 12 months', 'pct', RATE12(1)), O('Shop callback rate, 12 months', 'pct', SHOP12), O('Times the shop rate', 'num', 'IFERROR(%s/%s,0)' % (RATE12(1), SHOP12)),
        O('Your callback target', 'pct', '{set:callback_target}'),
        O('Technician callbacks, 12 months', 'int', 'SUMIFS(%s,%s,{in:technician},%s,%s)' % (R('cb_tech', 'callbacks'), R('cb_tech', 'technician'), R('cb_tech', 'period'), P12)),
        O('Cost of those callbacks', 'money', 'SUMIFS(%s,%s,{in:technician},%s,%s)' % (R('cb_tech', 'cost'), R('cb_tech', 'technician'), R('cb_tech', 'period'), P12)),
        O('Rate in the 12 months before', 'pct', 'IFERROR(SUMIFS(%s,%s,{in:technician},%s,%s)/SUMIFS(%s,%s,{in:technician},%s,%s),0)' % (R('cb_tech', 'callbacks'), R('cb_tech', 'technician'), R('cb_tech', 'period'), tok('period', 'Previous 12 months'), R('cb_tech', 'jobs'), R('cb_tech', 'technician'), R('cb_tech', 'period'), tok('period', 'Previous 12 months'))),
        O('Callbacks to cut to reach the target', 'int', 'MAX(0,ROUNDUP(SUMIFS(%s,%s,{in:technician},%s,%s)-{set:callback_target}*SUMIFS(%s,%s,{in:technician},%s,%s),0))' % (R('cb_tech', 'callbacks'), R('cb_tech', 'technician'), R('cb_tech', 'period'), P12, R('cb_tech', 'jobs'), R('cb_tech', 'technician'), R('cb_tech', 'period'), P12)),
        O('Verdict', 'text', 'IF(AND(%s>{set:callback_target},%s>=1.5*%s),%s,IF(%s>{set:callback_target},%s,%s))' % (RATE12(1), RATE12(1), SHOP12, c5('Talk this week'), RATE12(1), c5('Watch'), c5('Fine'))),
        O('Technician with the highest rate', 'text', X('cb_tech', 'technician', 'MATCH(MAX(%s),%s,0)' % (R('cb_tech', 'rate12'), R('cb_tech', 'rate12')))), O('Highest rate', 'pct', 'MAX(%s)' % R('cb_tech', 'rate12')),
        O('Job type callback rate, 12 months', 'pct', 'IFERROR(INDEX(%s,MATCH({in:job_type},%s,0)),0)' % (R('cb_type', 'rate'), R('cb_type', 'job_type'))),
        O('Job type times the shop rate', 'num', 'IFERROR(INDEX(%s,MATCH({in:job_type},%s,0)),0)' % (R('cb_type', 'ratio'), R('cb_type', 'job_type'))),
        O('Job type callbacks', 'int', 'IFERROR(INDEX(%s,MATCH({in:job_type},%s,0)),0)' % (R('cb_type', 'callbacks'), R('cb_type', 'job_type'))),
        O('Job type margin points lost to callbacks', 'pct', 'IFERROR(INDEX(%s,MATCH({in:job_type},%s,0)),0)' % (R('cb_type', 'drop'), R('cb_type', 'job_type')))]),
    # 11
    TOOL('cb_reason_rank', 'Callback Reason Ranker', 'Callback reasons ranked by money',
         'Ranks the reasons for callbacks over the last 12 months by what they cost, shows the reason worth fixing first and what a fall in it would save.', [
        I('cut', 'Fall in the top reason to test', 0.3, 'pct')], [
        O('Number %d reason' % k, 'text', X('cb_reason', 'reason', 'MATCH(LARGE(%s,%d),%s,0)' % (CBC, k, CBC))) for k in range(1, 6)] + [O('Number %d cost' % k, 'money', 'LARGE(%s,%d)' % (CBC, k)) for k in range(1, 6)] + [
        O('Cost of all reasons, 12 months', 'money', 'SUM(%s)' % CBC), O('Share of the top reason', 'pct', 'IFERROR(LARGE(%s,1)/SUM(%s),0)' % (CBC, CBC)),
        O('Yearly cost if nothing changes', 'money', 'SUM(%s)' % CBC), O('Saved a year if the top reason falls', 'money', '{in:cut}*LARGE(%s,1)' % CBC),
        O('Verdict', 'text', 'IF(LARGE(%s,1)>0,%s,%s)' % (CBC, c6('Fix this cause first'), c6('No clear leak')))],
         GR('What if', ('Top reason falls by 15 percent', {'cut': 0.15}), ('Top reason falls by half', {'cut': 0.5}), ('Top reason is removed', {'cut': 1}))),
    # 12
    TOOL('cb_margin', 'Callback-Aware Margin', 'Job margin after the cost of callbacks',
         'Margin that looks good and is not: each technician and job type after the cost of its callbacks over the last 12 months, ranked by the points lost.', [
        I('drop_alert', 'Points lost that count as a problem', 0.02, 'pct')], [
        O('Shop margin before callbacks, 12 months', 'pct', 'IFERROR(%s/%s,0)' % (CT('margin', P12), CT('revenue', P12))),
        O('Shop margin after callbacks, 12 months', 'pct', 'IFERROR((%s-SUMIFS(%s,%s,%s))/%s,0)' % (CT('margin', P12), R('cb_tech', 'cost'), R('cb_tech', 'period'), P12, CT('revenue', P12)))] +
        [O('Technician number %d' % k, 'text', X('tick_tech', 'technician', 'MATCH(LARGE(%s,%d),%s,0)' % (R('tick_tech', 'drop12'), k, R('tick_tech', 'drop12')))) for k in range(1, 4)] +
        [O('Technician number %d points lost' % k, 'pct', 'LARGE(%s,%d)' % (R('tick_tech', 'drop12'), k)) for k in range(1, 4)] +
        [O('Technician number %d margin after callbacks' % k, 'pct', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),0)' % (R('tick_tech', 'after_pct'), R('tick_tech', 'drop12'), k, R('tick_tech', 'drop12'))) for k in range(1, 4)] +
        [O('Job type number %d' % k, 'text', X('cb_type', 'job_type', 'MATCH(LARGE(%s,%d),%s,0)' % (R('cb_type', 'drop'), k, R('cb_type', 'drop')))) for k in range(1, 3)] +
        [O('Job type number %d points lost' % k, 'pct', 'LARGE(%s,%d)' % (R('cb_type', 'drop'), k)) for k in range(1, 3)] + [
        O('Verdict', 'text', 'IF(LARGE(%s,1)>={in:drop_alert},%s,%s)' % (R('tick_tech', 'drop12'), c6('Margin falls after callbacks'), c6('Callbacks are under control')))],
         GR('What if', ('Problem from 1 point', {'drop_alert': 0.01}), ('Problem from 3 points', {'drop_alert': 0.03}), ('Problem from 5 points', {'drop_alert': 0.05}))),
    # 13
    TOOL('warranty_tracker', 'Warranty Cost Tracker', 'Warranty cost against a reserve, by month and equipment type',
         'Warranty callbacks of the last 12 months in money, as a share of revenue, against the reserve you would set from your own history, for a chosen equipment type and month.', [
        IN('equip', 'Equipment type', 'list', key('eqtype', 'Air conditioner'), list='eqtype'), I('month', 'Month to look at (first day)', LASTM, 'date'), I('reserve_pct', 'Reserve as share of revenue to test (set your own)', 0.01, 'pct')], [
        O('Warranty cost, last 12 months', 'money', TMSA('warranty_cost')), O('Warranty callbacks, last 12 months', 'int', 'COUNTIFS(%s,%s,%s,">="&%s)' % (R('callbacks', 'warranty'), YES, R('callbacks', 'date'), Y12)),
        O('Revenue, last 12 months', 'money', TMSA('revenue')), O('Warranty cost as share of revenue', 'pct', 'IFERROR(%s/%s,0)' % (TMSA('warranty_cost'), TMSA('revenue'))),
        O('Reserve at the tested share', 'money', '{in:reserve_pct}*%s' % TMSA('revenue')), O('Reserve left', 'money', '{in:reserve_pct}*%s-%s' % (TMSA('revenue'), TMSA('warranty_cost'))),
        O('Reserve share your history suggests', 'pct', 'IFERROR(ROUNDUP(%s/%s*1000,0)/1000,0)' % (TMSA('warranty_cost'), TMSA('revenue'))),
        O('Months over the reserve, last 12', 'int', 'COUNTIFS(%s,%s,%s)' % (R('tick_month', 'reserve_flag'), c5('Over reserve'), TMA)),
        O('Cost for the chosen equipment type', 'money', 'SUMIFS(%s,%s,%s,%s,{in:equip},%s,">="&%s)' % (R('callbacks', 'cost'), R('callbacks', 'warranty'), YES, R('callbacks', 'equip_type'), R('callbacks', 'date'), Y12)),
        O('Callbacks for the chosen type', 'int', 'COUNTIFS(%s,%s,%s,{in:equip},%s,">="&%s)' % (R('callbacks', 'warranty'), YES, R('callbacks', 'equip_type'), R('callbacks', 'date'), Y12)),
        O('Share of the warranty cost', 'pct', 'IFERROR(SUMIFS(%s,%s,%s,%s,{in:equip},%s,">="&%s)/%s,0)' % (R('callbacks', 'cost'), R('callbacks', 'warranty'), YES, R('callbacks', 'equip_type'), R('callbacks', 'date'), Y12, TMSA('warranty_cost'))),
        O('Warranty cost in the chosen month', 'money', 'SUMIFS(%s,%s,%s,%s,">="&{in:month},%s,"<"&EDATE({in:month},1))' % (R('callbacks', 'cost'), R('callbacks', 'warranty'), YES, R('callbacks', 'date'), R('callbacks', 'date'))),
        O('Chosen month and equipment type', 'money', 'SUMIFS(%s,%s,%s,%s,{in:equip},%s,">="&{in:month},%s,"<"&EDATE({in:month},1))' % (R('callbacks', 'cost'), R('callbacks', 'warranty'), YES, R('callbacks', 'equip_type'), R('callbacks', 'date'), R('callbacks', 'date'))),
        O('Warranty cost this season', 'money', 'SUMIFS(%s,%s,%s,%s,">="&%s)' % (R('callbacks', 'cost'), R('callbacks', 'warranty'), YES, R('callbacks', 'date'), SEASON)),
        O('Verdict', 'text', 'IF(%s<={in:reserve_pct}*%s,%s,%s)' % (TMSA('warranty_cost'), TMSA('revenue'), c5('Within reserve'), c5('Over reserve')))],
         GR('What if', ('Reserve 0.5 percent', {'reserve_pct': 0.005}), ('Reserve 1 percent', {'reserve_pct': 0.01}), ('Reserve 1.5 percent', {'reserve_pct': 0.015}), ('Reserve 2 percent', {'reserve_pct': 0.02}))),
    # 14
    TOOL('replace_repair', 'Replace versus Repair Sentence', 'Replace versus repair sentence for an estimate',
         'Type the age, the repair quote, the replacement price and the expected life you set: cost per year of each choice and a plain sentence for the estimate (check with the customer).', [
        I('age', 'Equipment age in years', 13, 'int'), I('quote', 'Repair quote', 1150), I('price', 'Replacement price', 5700), I('life', 'Expected life in years (your own number)', 15, 'int')], [
        O('Remaining life in years', 'int', 'MAX(0,{in:life}-{in:age})'), O('Repair cost per remaining year', 'money', 'IFERROR({in:quote}/MAX(MAX(0,{in:life}-{in:age}),1),0)'),
        O('Replacement cost per year', 'money', 'IFERROR({in:price}/{in:life},0)'), O('Repair per year over replacement per year', 'num', 'IFERROR(({in:quote}/MAX(MAX(0,{in:life}-{in:age}),1))/({in:price}/{in:life}),0)'),
        O('Repair quote as share of the replacement price', 'pct', 'IFERROR({in:quote}/{in:price},0)'), O('Years the repair must last to match replacement', 'num', 'IFERROR({in:quote}/({in:price}/{in:life}),0)'),
        O('Money a year saved by the cheaper choice', 'money', 'ABS(IFERROR({in:quote}/MAX(MAX(0,{in:life}-{in:age}),1),0)-IFERROR({in:price}/{in:life},0))'),
        O('Sentence for the estimate', 'text', 'IF(IFERROR(({in:quote}/MAX(MAX(0,{in:life}-{in:age}),1))/({in:price}/{in:life}),0)<0.8,%s,IF(IFERROR(({in:quote}/MAX(MAX(0,{in:life}-{in:age}),1))/({in:price}/{in:life}),0)>1.2,%s,IF({in:age}>={set:replace_age},%s,%s)))' %
          (c5('Repair costs less per year'), c5('Replacement costs less per year'), c5('Replace lead: age is past your limit'), c5('Close call, ask the customer')))],
         GR('What if', ('Younger unit, age 6', {'age': 6}), ('Cheaper repair, 600', {'quote': 600}), ('Dearer replacement, 7500', {'price': 7500}), ('Short expected life, 12 years', {'life': 12}), ('Old unit, age 17', {'age': 17}))),
    # 15
    TOOL('whatif', 'What-if on Labour and Parts', 'What-if on labour, parts and close rate for monthly profit',
         'Move labour, parts and the close rate (estimates won over estimates decided): effect on monthly profit and on the jobs a week to break even; the grid holds Base, Best, Worst and sensitivity.', [
        I('rev', 'Revenue a month', DEF_REV), I('lab', 'Labour cost a month', DEF_LAB), I('par', 'Parts cost a month', DEF_PAR), I('oth', 'Other job cost and callbacks a month', DEF_OTH), I('jobs', 'Jobs a month', DEF_JOBS_M, 'int'),
        I('oh', 'Overhead a month', D.OVERHEAD_MONTH), I('close', 'Close rate now', CLOSE_TARGET, 'pct'), I('dl', 'Labour cost change', 0.05, 'pct'), I('dp', 'Parts cost change', 0.08, 'pct'), I('dc', 'Close rate change in points', -0.03, 'pct')], [
        O('Monthly profit today', 'money', '{in:rev}-{in:lab}-{in:par}-{in:oth}-{in:oh}'),
        O('Monthly profit in the scenario', 'money', '({in:close}+{in:dc})/{in:close}*({in:rev}-{in:lab}*(1+{in:dl})-{in:par}*(1+{in:dp})-{in:oth})-{in:oh}'),
        O('Change in monthly profit', 'money', '({in:close}+{in:dc})/{in:close}*({in:rev}-{in:lab}*(1+{in:dl})-{in:par}*(1+{in:dp})-{in:oth})-({in:rev}-{in:lab}-{in:par}-{in:oth})'),
        O('Effect of labour alone', 'money', '-{in:lab}*{in:dl}'), O('Effect of parts alone', 'money', '-{in:par}*{in:dp}'), O('Effect of the close rate alone', 'money', '(({in:close}+{in:dc})/{in:close}-1)*({in:rev}-{in:lab}-{in:par}-{in:oth})'),
        O('Jobs a week today', 'num', '{in:jobs}/4.345'), O('Break-even jobs a week today', 'num', 'IFERROR({in:oh}/(({in:rev}-{in:lab}-{in:par}-{in:oth})/{in:jobs})/4.345,0)'),
        O('Break-even jobs a week in the scenario', 'num', 'IFERROR({in:oh}/(({in:rev}-{in:lab}*(1+{in:dl})-{in:par}*(1+{in:dp})-{in:oth})/{in:jobs})/4.345,0)'),
        O('Verdict', 'text', 'IF(({in:close}+{in:dc})/{in:close}*({in:rev}-{in:lab}*(1+{in:dl})-{in:par}*(1+{in:dp})-{in:oth})-{in:oh}>0,%s,%s)' % (c6('Profit is covered'), c6('Profit does not cover overhead')))],
         GR('Base, best, worst and sensitivity', ('Base, nothing changes', {'dl': 0, 'dp': 0, 'dc': 0}), ('Best: labour 3 less, parts 4 less', {'dl': -0.03, 'dp': -0.04, 'dc': 0.03}),
            ('Worst: labour 5 more, parts 8 more', {'dl': 0.05, 'dp': 0.08, 'dc': -0.03}), ('Labour plus 5 percent only', {'dl': 0.05, 'dp': 0, 'dc': 0}), ('Labour plus 10 percent only', {'dl': 0.10, 'dp': 0, 'dc': 0}),
            ('Labour minus 5 percent only', {'dl': -0.05, 'dp': 0, 'dc': 0}), ('Parts plus 4 percent only', {'dl': 0, 'dp': 0.04, 'dc': 0}), ('Parts plus 12 percent only', {'dl': 0, 'dp': 0.12, 'dc': 0}),
            ('Close rate minus 3 points only', {'dl': 0, 'dp': 0, 'dc': -0.03}), ('Close rate plus 3 points only', {'dl': 0, 'dp': 0, 'dc': 0.03}))),
    # 16
    TOOL('margin_recovery', 'Margin Recovery Planner', 'Margin recovery planner: which job types to re-price first',
         'Job types under or within a buffer of their target, ranked by the price rise needed, with the jobs a year, the money recovered and the net gain if some jobs are lost after the rise.', [
        I('loss_share', 'Share of jobs you could lose after the rise (set your own)', 0.05, 'pct')], [
        O('Re-price number %d' % k, 'text', 'IF(LARGE(%s,%d)>0,%s,"")' % (RB, k, X('margin_jt', 'job_type', 'MATCH(LARGE(%s,%d),%s,0)' % (RB, k, RB)))) for k in range(1, 4)] +
        [O('Number %d price rise needed' % k, 'pct', 'LARGE(%s,%d)' % (RB, k)) for k in range(1, 4)] +
        [O('Number %d jobs a year' % k, 'int', 'IF(LARGE(%s,%d)>0,%s,0)' % (RB, k, X('margin_jt', 'jobs_year', 'MATCH(LARGE(%s,%d),%s,0)' % (RB, k, RB)))) for k in range(1, 4)] +
        [O('Number %d money recovered a year' % k, 'money', 'IF(LARGE(%s,%d)>0,%s,0)' % (RB, k, X('margin_jt', 'recover_year', 'MATCH(LARGE(%s,%d),%s,0)' % (RB, k, RB)))) for k in range(1, 4)] + [
        O('Job types to re-price', 'int', 'COUNTIFS(%s,">0")' % RB), O('Money recovered a year, all of them', 'money', 'SUM(%s)' % R('margin_jt', 'recover_year')),
        O('Net gain a year after the jobs lost', 'money', '(1-{in:loss_share})*((SUMIFS(%s,%s,">0")+SUMIFS(%s,%s,">0")*0+SUM(%s)*120/365)-SUMIFS(%s,%s,">0"))*365/120-(SUMIFS(%s,%s,">0")-SUMIFS(%s,%s,">0"))*365/120' %
          (R('margin_jt', 'revenue_120'), RB, R('margin_jt', 'revenue_120'), RB, R('margin_jt', 'recover_year'), R('margin_jt', 'cost_120'), RB, R('margin_jt', 'revenue_120'), RB, R('margin_jt', 'cost_120'), RB)),
        O('Verdict', 'text', 'IF(COUNTIFS(%s,">0")>0,%s,%s)' % (RB, c6('Re-price these types'), c6('Hold, no type is under target')))],
         GR('What if', ('Lose 0 percent of jobs', {'loss_share': 0}), ('Lose 10 percent of jobs', {'loss_share': 0.1}), ('Lose 20 percent of jobs', {'loss_share': 0.2}))),
    # 17
    TOOL('cost_vs_ly', 'Job Costing against Last Year', 'Job costing against last year for one job type',
         'Pick a job type: price, cost and margin per job over the last 120 days against the same days last year, and whether the job type is improving or slipping.', [
        IN('job_type', 'Job type', 'list', key('jobtype', 'Water heater replacement'), list='jobtype')], [
        O('Jobs, last 120 days', 'int', JX('jobs_120')), O('Jobs, same days last year', 'int', JX('jobs_ly')),
        O('Price per job now', 'money', JX('price_job')), O('Price per job last year', 'money', 'IFERROR(%s/%s,0)' % (JX('revenue_ly'), JX('jobs_ly'))),
        O('Cost per job now', 'money', JX('cost_job')), O('Cost per job last year', 'money', 'IFERROR(%s/%s,0)' % (JX('cost_ly'), JX('jobs_ly'))),
        O('Margin per job now', 'money', 'IFERROR(%s/%s,0)' % (JX('margin_120'), JX('jobs_120'))), O('Margin per job last year', 'money', 'IFERROR((%s-%s)/%s,0)' % (JX('revenue_ly'), JX('cost_ly'), JX('jobs_ly'))),
        O('Margin percent now', 'pct', JX('margin_pct_120')), O('Margin percent last year', 'pct', JX('margin_pct_ly')), O('Change in points', 'pct', '%s-%s' % (JX('margin_pct_120'), JX('margin_pct_ly'))),
        O('Cost per job change', 'pct', 'IFERROR((%s/%s)/(%s/%s)-1,0)' % (JX('cost_120'), JX('jobs_120'), JX('cost_ly'), JX('jobs_ly'))),
        O('Verdict', 'text', JX('trend')), O('Job types slipping', 'int', 'COUNTIFS(%s,%s)' % (R('margin_jt', 'trend'), c3('Slipping'))), O('Job types improving', 'int', 'COUNTIFS(%s,%s)' % (R('margin_jt', 'trend'), c3('Improving')))]),
    # 18
    TOOL('profit_forecast', 'Monthly Job Profit Forecast', 'Job profit forecast with Base, Best and Worst',
         'Average margin per job times the jobs booked and your own seasonal index for the weeks ahead, with the callback cost deducted and the overhead of the same weeks; Base, Best and Worst.', [
        I('jobs_week', 'Jobs a week now', DEF_JOBS_WEEK, 'num'), I('margin_job', 'Average margin per job', DEF_MARGIN_JOB), I('weeks', 'Weeks to forecast', 8, 'int'),
        I('best_change', 'Best case change in margin per job', 0.08, 'pct'), I('worst_change', 'Worst case change in margin per job', -0.10, 'pct')], [
        O('Seasonal index of the weeks ahead', 'num', 'IFERROR((SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&EDATE(%s,-9))/3)/(%s/12),1)' % (R('tick_month', 'jobs'), R('tick_month', 'month'), MS, R('tick_month', 'month'), MS, TMS('jobs'))),
        O('Jobs expected', 'int', '{in:jobs_week}*{in:weeks}*IFERROR((SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&EDATE(%s,-9))/3)/(%s/12),1)' % (R('tick_month', 'jobs'), R('tick_month', 'month'), MS, R('tick_month', 'month'), MS, TMS('jobs'))),
        O('Callback cost per job, 12 months', 'money', 'IFERROR(%s/%s,0)' % (TMS('cb_cost'), TMS('jobs'))),
        O('Margin before callbacks, Base', 'money', '{in:jobs_week}*{in:weeks}*IFERROR((SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&EDATE(%s,-9))/3)/(%s/12),1)*{in:margin_job}' % (R('tick_month', 'jobs'), R('tick_month', 'month'), MS, R('tick_month', 'month'), MS, TMS('jobs'))),
        O('Callback cost deducted', 'money', '{in:jobs_week}*{in:weeks}*IFERROR((SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&EDATE(%s,-9))/3)/(%s/12),1)*IFERROR(%s/%s,0)' % (R('tick_month', 'jobs'), R('tick_month', 'month'), MS, R('tick_month', 'month'), MS, TMS('jobs'), TMS('cb_cost'), TMS('jobs'))),
        O('Gross profit, Base', 'money', '{in:jobs_week}*{in:weeks}*IFERROR((SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&EDATE(%s,-9))/3)/(%s/12),1)*({in:margin_job}-IFERROR(%s/%s,0))' % (R('tick_month', 'jobs'), R('tick_month', 'month'), MS, R('tick_month', 'month'), MS, TMS('jobs'), TMS('cb_cost'), TMS('jobs'))),
        O('Gross profit, Best', 'money', '{in:jobs_week}*{in:weeks}*IFERROR((SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&EDATE(%s,-9))/3)/(%s/12),1)*({in:margin_job}*(1+{in:best_change})-IFERROR(%s/%s,0))' % (R('tick_month', 'jobs'), R('tick_month', 'month'), MS, R('tick_month', 'month'), MS, TMS('jobs'), TMS('cb_cost'), TMS('jobs'))),
        O('Gross profit, Worst', 'money', '{in:jobs_week}*{in:weeks}*IFERROR((SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&EDATE(%s,-9))/3)/(%s/12),1)*({in:margin_job}*(1+{in:worst_change})-IFERROR(%s/%s,0))' % (R('tick_month', 'jobs'), R('tick_month', 'month'), MS, R('tick_month', 'month'), MS, TMS('jobs'), TMS('cb_cost'), TMS('jobs'))),
        O('Overhead of the same weeks', 'money', '{set:overhead_month}*{in:weeks}/4.345'),
        O('Left after overhead, Base', 'money', '{in:jobs_week}*{in:weeks}*IFERROR((SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&EDATE(%s,-9))/3)/(%s/12),1)*({in:margin_job}-IFERROR(%s/%s,0))-{set:overhead_month}*{in:weeks}/4.345' % (R('tick_month', 'jobs'), R('tick_month', 'month'), MS, R('tick_month', 'month'), MS, TMS('jobs'), TMS('cb_cost'), TMS('jobs'))),
        O('Left after overhead, Worst', 'money', '{in:jobs_week}*{in:weeks}*IFERROR((SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&EDATE(%s,-9))/3)/(%s/12),1)*({in:margin_job}*(1+{in:worst_change})-IFERROR(%s/%s,0))-{set:overhead_month}*{in:weeks}/4.345' % (R('tick_month', 'jobs'), R('tick_month', 'month'), MS, R('tick_month', 'month'), MS, TMS('jobs'), TMS('cb_cost'), TMS('jobs'))),
        O('Verdict', 'text', 'IF({in:jobs_week}*{in:weeks}*IFERROR((SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&EDATE(%s,-9))/3)/(%s/12),1)*({in:margin_job}*(1+{in:worst_change})-IFERROR(%s/%s,0))-{set:overhead_month}*{in:weeks}/4.345>0,%s,%s)' % (R('tick_month', 'jobs'), R('tick_month', 'month'), MS, R('tick_month', 'month'), MS, TMS('jobs'), TMS('cb_cost'), TMS('jobs'), c6('Profit is covered'), c6('Profit does not cover overhead')))],
         GR('What if', ('Four weeks', {'weeks': 4}), ('Twelve weeks', {'weeks': 12}), ('Ten percent fewer jobs', {'jobs_week': round(DEF_JOBS_WEEK * 0.9, 1)}), ('Ten percent more jobs', {'jobs_week': round(DEF_JOBS_WEEK * 1.1, 1)}))),
]
assert len(tools) == 18, len(tools)
