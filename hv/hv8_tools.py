"""HVAC suite part 8: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv8_lists import *
import hv8_data as D
from hv8_tables import MS, EM, MEAS, _win, _num, _col, HM, LOWER

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
OPEN, COMPLETED = tok('rnstatus', 'Open'), tok('jobstatus', 'Completed')
P3, P12, PP12 = tok('period', 'Last 3 months'), tok('period', 'Last 12 months'), tok('period', 'Previous 12 months')
G, AM, RD = ck('Green'), ck('Amber'), ck('Red')
tools = []

def SRX(col, src, per=P12): return 'SUMIFS({range:src_results.%s},{range:src_results.source},%s,{range:src_results.period},%s)' % (col, src, per)
def SRT(col, per=P12): return 'SUMIFS({range:src_results.%s},{range:src_results.period},%s)' % (col, per)
def RTX(col, tech, per=P12): return 'SUMIFS({range:rev_tech.%s},{range:rev_tech.technician},%s,{range:rev_tech.period},%s)' % (col, tech, per)
def RTT(col, per=P12): return 'SUMIFS({range:rev_tech.%s},{range:rev_tech.period},%s)' % (col, per)
def BYRANK(col, key, k, fn='LARGE'): return 'IFERROR(INDEX({range:src_results.%s},MATCH(%s({range:src_results.%s},%d),{range:src_results.%s},0)),0)' % (col, fn, key, k, key)
def BYRANKT(col, key, k, fn='LARGE'): return 'IFERROR(INDEX({range:src_results.%s},MATCH(%s({range:src_results.%s},%d),{range:src_results.%s},0))&"","")' % (col, fn, key, k, key)
def SC(col, m='{in:measure}'): return 'IFERROR(INDEX({range:scorecard.%s},MATCH(%s,{range:scorecard.measure},0)),0)' % (col, m)
def SCT(col, m='{in:measure}'): return 'IFERROR(INDEX({range:scorecard.%s},MATCH(%s,{range:scorecard.measure},0))&"","")' % (col, m)

# 1 lead source ranker
W1 = 'MATCH(SMALL({range:src_results.rank_key},1),{range:src_results.rank_key},0)'
CUT = 'IFERROR(INDEX({range:src_results.spend},%s),0)-IFERROR(INDEX({range:src_results.revenue},%s),0)*(1-{in:kept})*{set:margin_target}' % (W1, W1)
tools.append(TOOL('lead_ranker', 'Lead Source Ranker', 'Lead sources ranked by revenue per spend: keep, renegotiate or drop',
  'Pick a source and the share of its jobs you expect to keep without spend: spend, calls, booked and sold jobs and revenue of the last 12 months, the best and weakest source and what cutting the weakest would move.', [
    IN('source', 'Lead source', 'list', key('source', 'Search ads'), list='source'), I('kept', 'Share of its booked jobs that still arrive without spend', 0.3, 'pct')], [
    O('Spend, last 12 months', 'money', SRX('spend', '{in:source}')), O('Calls', 'int', SRX('calls', '{in:source}')), O('Booked jobs', 'int', SRX('booked', '{in:source}')), O('Sold jobs', 'int', SRX('sold', '{in:source}')),
    O('Revenue', 'money', SRX('revenue', '{in:source}')), O('Revenue per spend', 'num', SRX('revenue_per_spend', '{in:source}')),
    O('Verdict for this source', 'text', 'IF(%s<=0,%s,IF(%s>={set:rps_keep},%s,IF(%s>={set:rps_drop},%s,%s)))' % (SRX('spend', '{in:source}'), ck('Free source'), SRX('revenue_per_spend', '{in:source}'), ck('Keep'), SRX('revenue_per_spend', '{in:source}'), ck('Renegotiate'), ck('Drop'))),
    O('Best source by revenue per spend', 'text', BYRANKT('source', 'rank_key', 1)), O('Its revenue per spend', 'num', BYRANK('revenue_per_spend', 'rank_key', 1)),
    O('Weakest source by revenue per spend', 'text', BYRANKT('source', 'rank_key', 1, 'SMALL')), O('Its revenue per spend', 'num', BYRANK('revenue_per_spend', 'rank_key', 1, 'SMALL')),
    O('Spend freed a year if the weakest is cut', 'money', 'IFERROR(INDEX({range:src_results.spend},%s),0)' % W1), O('Margin lost a year at your margin target', 'money', 'IFERROR(INDEX({range:src_results.revenue},%s),0)*(1-{in:kept})*{set:margin_target}' % W1),
    O('Net money moved a year', 'money', CUT), O('Verdict on the weakest', 'text', 'IF(%s>0,%s,%s)' % (CUT, ck('Cut or renegotiate the weakest'), ck('Keep the weakest: it earns its spend')))],
  GR('What if', ('Local listing', {'source': '=' + tok('source', 'Local listing')}), ('Website', {'source': '=' + tok('source', 'Website')}), ('Mailers', {'source': '=' + tok('source', 'Mailers')}), ('Half its jobs stay', {'kept': 0.5}), ('Few jobs stay', {'kept': 0.1}))))
# 2 cost per booked job
tools.append(TOOL('cpb_tool', 'Cost per Booked Job Tool', 'Cost per lead against cost per booked job by source',
  'Pick a source: its cost per lead and cost per booked job for 12 and 3 months against the shop figures and your target, with a note when a source is cheap per lead but costly per booked job.', [
    IN('source', 'Lead source', 'list', key('source', 'Search ads'), list='source')], [
    O('Cost per lead, 12 months', 'money', SRX('cost_per_lead', '{in:source}')), O('Cost per booked job, 12 months', 'money', SRX('cost_per_booked', '{in:source}')),
    O('Cost per booked job, last 3 months', 'money', SRX('cost_per_booked', '{in:source}', P3)), O('Your target', 'money', '{set:lead_cost_target}'),
    O('Gap to the target, last 3 months', 'money', SRX('cost_per_booked', '{in:source}', P3) + '-{set:lead_cost_target}'),
    O('Shop cost per lead', 'money', 'IFERROR(%s/%s,0)' % (SRT('spend'), SRT('calls'))), O('Shop cost per booked job', 'money', 'IFERROR(%s/%s,0)' % (SRT('spend'), SRT('booked'))),
    O('Booking rate of the source', 'pct', SRX('booking_rate', '{in:source}')),
    O('Verdict', 'text', 'IF(%s>{set:lead_cost_target},%s,IF(AND(%s<=IFERROR(%s/%s,0),%s>IFERROR(%s/%s,0)),%s,%s))' % (SRX('cost_per_booked', '{in:source}', P3), ck('Above your target'), SRX('cost_per_lead', '{in:source}'), SRT('spend'), SRT('calls'),
        SRX('cost_per_booked', '{in:source}'), SRT('spend'), SRT('booked'), ck('Cheap per lead, costly per booked job'), ck('Within your target')))],
  GR('What if', ('Local listing', {'source': '=' + tok('source', 'Local listing')}), ('Mailers', {'source': '=' + tok('source', 'Mailers')}), ('Referral', {'source': '=' + tok('source', 'Referral')}), ('Property manager', {'source': '=' + tok('source', 'Property manager')}))))
# 3 payback
NET3 = '({in:jobs}*{in:margin_job}-{in:spend})'
PB3 = '({in:lag}+({in:setup}+{in:lag}*{in:spend})/%s)' % NET3
tools.append(TOOL('payback', 'Source Payback Tool', 'Months to pay back a monthly spend from the margin of the jobs it brings',
  'Type the monthly spend, the booked jobs a month, the margin on a job, a one-off set-up cost and the months before the first job: the net a month, the break-even jobs and the months to pay back.', [
    I('spend', 'Spend a month', 1200), I('jobs', 'Booked jobs a month once it works', 12, 'int'), I('margin_job', 'Margin on one job', 175), I('setup', 'One-off set-up cost', 600), I('lag', 'Months before the first job', 2, 'int'), I('max_months', 'Months you accept to pay back', 6, 'int')], [
    O('Margin brought a month', 'money', '{in:jobs}*{in:margin_job}'), O('Net a month after the spend', 'money', NET3), O('Break-even jobs a month', 'num', 'IFERROR({in:spend}/{in:margin_job},0)'),
    O('Cost before the first job', 'money', '{in:setup}+{in:lag}*{in:spend}'), O('Months to pay back', 'num', 'IF(%s>0,%s,0)' % (NET3, PB3)),
    O('Margin over 12 months after all costs', 'money', '12*%s-{in:setup}-{in:lag}*{in:spend}' % NET3),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s<={in:max_months},%s,IF(%s<={in:max_months}+3,%s,%s)))' % (NET3, ck('Drop'), PB3, ck('Worth it'), PB3, ck('Test 3 more months'), ck('Drop')))],
  GR('What if', ('Only 8 jobs a month', {'jobs': 8}), ('20 jobs a month', {'jobs': 20}), ('Spend 2000', {'spend': 2000}), ('No set-up cost', {'setup': 0}), ('Four months to the first job', {'lag': 4}))))
# 4 budget split
BPS = lambda s: 'IFERROR(%s/%s,0)' % (SRX('booked', s), SRX('spend', s))
RPJ = lambda s: 'IFERROR(%s/%s,0)' % (SRX('revenue', s), SRX('booked', s))
LOST4 = '{in:move}*%s' % BPS('{in:from_source}'); GAIN4 = '{in:move}*%s*{in:effect}' % BPS('{in:to_source}')
EXTRA4 = '(%s*%s-%s*%s)' % (GAIN4, RPJ('{in:to_source}'), LOST4, RPJ('{in:from_source}'))
tools.append(TOOL('budget_split', 'Marketing Budget Split Planner', 'Move a monthly budget between two sources',
  'Pick the source to cut and the source to feed, the amount moved a month and how well extra spend works compared with the average: booked jobs lost and gained, the net and the revenue and margin it moves, with base, best and worst rows.', [
    IN('from_source', 'Take spend from', 'list', key('source', 'Search ads'), list='source'), IN('to_source', 'Move spend to', 'list', key('source', 'Local listing'), list='source'), I('move', 'Amount moved a month', 800),
    I('effect', 'How well extra spend works against the average', 0.5, 'pct')], [
    O('Booked jobs per 1 spent, source cut', 'num', BPS('{in:from_source}')), O('Booked jobs per 1 spent, source fed', 'num', BPS('{in:to_source}')), O('Revenue per booked job, source cut', 'money', RPJ('{in:from_source}')),
    O('Revenue per booked job, source fed', 'money', RPJ('{in:to_source}')), O('Booked jobs lost a month', 'num', LOST4), O('Booked jobs gained a month', 'num', GAIN4), O('Extra booked jobs a month', 'num', GAIN4 + '-' + LOST4),
    O('Extra revenue a month', 'money', EXTRA4), O('Extra margin a month at your margin target', 'money', EXTRA4 + '*{set:margin_target}'),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (EXTRA4, ck('Move the spend'), ck('Keep the split')))],
  GR('Base, best and worst', ('Base', {'effect': 0.5}), ('Best', {'effect': 0.9}), ('Worst', {'effect': 0.25}), ('Move 1500 at base', {'move': 1500, 'effect': 0.5}), ('Feed the website', {'to_source': '=' + tok('source', 'Website')}))))
# 5 source quality
JC = '{range:jobs.source},{in:source},{range:jobs.status},%s' % COMPLETED
SHOPMPJ = 'IFERROR(SUMIFS({range:jobs.margin},{range:jobs.status},%s)/COUNTIFS({range:jobs.status},%s),0)' % (COMPLETED, COMPLETED)
MPJ5 = SRX('s_margin_job', '{in:source}')
tools.append(TOOL('source_quality', 'Source Quality by Job Type', 'Which sources bring replacements and the best margin per job',
  'Pick a source and a job kind: its completed jobs on the Jobs sheet, the share that were this kind, its margin per job against the shop, and a verdict to buy more of or stop.', [
    IN('source', 'Lead source', 'list', key('source', 'Search ads'), list='source'), IN('kind', 'Job kind', 'list', key('jobkind', 'Replacement'), list='jobkind')], [
    O('Completed jobs of this source', 'int', 'COUNTIFS(%s)' % JC), O('Jobs of the chosen kind', 'int', 'COUNTIFS(%s,{range:jobs.kind},{in:kind})' % JC),
    O('Share of the source that is this kind', 'pct', 'IFERROR(COUNTIFS(%s,{range:jobs.kind},{in:kind})/COUNTIFS(%s),0)' % (JC, JC)), O('Margin per job of the source', 'money', MPJ5), O('Margin per job, whole shop', 'money', SHOPMPJ),
    O('Revenue per spend of the source', 'num', SRX('revenue_per_spend', '{in:source}')), O('Best source by margin per job', 'text', BYRANKT('source', 'mpj_key', 1)), O('Its margin per job', 'money', BYRANK('s_margin_job', 'mpj_key', 1)),
    O('Weakest source by margin per job', 'text', BYRANKT('source', 'mpj_key', 1, 'SMALL')), O('Its margin per job', 'money', BYRANK('s_margin_job', 'mpj_key', 1, 'SMALL')),
    O('Verdict', 'text', 'IF(AND(%s>=%s,%s>={set:rps_keep}),%s,IF(%s<0.8*%s,%s,%s))' % (MPJ5, SHOPMPJ, SRX('revenue_per_spend', '{in:source}'), ck('Buy more of'), MPJ5, SHOPMPJ, ck('Stop'), ck('Hold')))],
  GR('What if', ('Referral, repairs', {'source': '=' + tok('source', 'Referral'), 'kind': '=' + tok('jobkind', 'Repair')}), ('Website, installs', {'source': '=' + tok('source', 'Website'), 'kind': '=' + tok('jobkind', 'Install')}),
     ('Mailers, tune-ups', {'source': '=' + tok('source', 'Mailers'), 'kind': '=' + tok('jobkind', 'Tune-up')}), ('Property manager', {'source': '=' + tok('source', 'Property manager')}))))
# 6 seasonal lead forecast
WK = lambda k: '({today}-WEEKDAY({today},2)+1+%d)' % (7 * (k + 1))
def CALLS_W(k, src=True):
    w = WK(k)
    return 'SUMIFS({range:src_month.calls},{range:src_month.month},EDATE(DATE(YEAR(%s),MONTH(%s),1),-12)%s)/DAY(EOMONTH(%s,0))*7*(1+{in:growth})' % (w, w, ',{range:src_month.source},{in:source}' if src else '', w)
TOT6 = '(' + '+'.join(CALLS_W(k) for k in range(12)) + ')'
TOTA6 = '(' + '+'.join(CALLS_W(k, False) for k in range(12)) + ')'
tools.append(TOOL('lead_forecast', 'Seasonal Lead Forecast', 'Expected calls, booked jobs and spend for the next 12 weeks',
  'Pick a source and the growth over last year: calls for each of the next 12 weeks from the same months last year, the booked jobs at the source booking rate and the spend needed at its cost per call.', [
    IN('source', 'Lead source', 'list', key('source', 'Search ads'), list='source'), I('growth', 'Change against the same months last year', 0.05, 'pct')], [
    O('Expected calls, 12 weeks, this source', 'num', TOT6), O('Expected calls, 12 weeks, all sources', 'num', TOTA6), O('Expected booked jobs, this source', 'num', TOT6 + '*' + SRX('booking_rate', '{in:source}')),
    O('Spend needed at its cost per call', 'money', TOT6 + '*IFERROR(%s/%s,0)' % (SRX('spend', '{in:source}'), SRX('calls', '{in:source}'))), O('Average calls a week, last 12 months', 'num', SRX('calls', '{in:source}') + '/52'),
    O('Verdict', 'text', 'IF(%s>%s/52*1.15,%s,IF(%s<%s/52*0.85,%s,%s))' % (CALLS_W(5), SRX('calls', '{in:source}'), ck('Busy weeks ahead: plan technician hours'), CALLS_W(5), SRX('calls', '{in:source}'), ck('Slow weeks ahead: plan your marketing'), ck('A steady season ahead'))),
    ] + [O('Week %d, expected calls' % (k + 1), 'num', CALLS_W(k)) for k in range(12)],
  GR('What if', ('Growth 15 percent', {'growth': 0.15}), ('No growth', {'growth': 0}), ('Website', {'source': '=' + tok('source', 'Website')}), ('Repeat customers', {'source': '=' + tok('source', 'Repeat customer')}))))
# 7 review and referral tracker
TT = '{in:tech}'
tools.append(TOOL('review_tracker', 'Review and Referral Tracker', 'Requests, reviews and referrals by technician against your target',
  'Pick a technician: jobs, requests sent, reviews received and referrals for 12 months, the conversion of jobs to reviews against your target, the last 3 months and the 12 before. Counts only.', [
    IN('tech', 'Technician', 'list', key('tech', 'Kofi Mensah'), list='tech')], [
    O('Jobs, 12 months', 'int', RTX('jobs', TT)), O('Requests sent', 'int', RTX('requests', TT)), O('Reviews received', 'int', RTX('reviews', TT)), O('Referrals', 'int', RTX('referrals', TT)),
    O('Jobs to reviews', 'pct', RTX('conversion', TT)), O('Your review target', 'pct', '{set:review_target}'), O('Request rate', 'pct', RTX('request_rate', TT)), O('Reviews per request', 'pct', RTX('per_request', TT)),
    O('Jobs to reviews, last 3 months', 'pct', RTX('conversion', TT, P3)), O('Jobs to reviews, 12 months before', 'pct', RTX('conversion', TT, PP12)),
    O('Shop jobs to reviews, 12 months', 'pct', 'IFERROR(%s/%s,0)' % (RTT('reviews'), RTT('jobs'))),
    O('Verdict', 'text', 'IF(%s>={set:review_target},%s,IF(%s<0.8*{set:review_target},%s,%s))' % (RTX('conversion', TT), ck('On target'), RTX('conversion', TT), ck('Ask for a review after every job'), ck('Close to the target')))],
  GR('Every technician', *[(t, {'tech': '=' + tok('tech', t)}) for t in TECH6])))
# 8 review request gap finder
def GAPT(t): return 'COUNTIFS({range:jobs.status},%s,{range:jobs.request_sent},%s,{range:jobs.technician},%s,{range:jobs.date},">="&({today}-{in:days}),{range:jobs.date},"<="&{today})' % (COMPLETED, NO, tok('tech', t))
TOTG = 'COUNTIFS({range:jobs.status},%s,{range:jobs.request_sent},%s,{range:jobs.date},">="&({today}-{in:days}),{range:jobs.date},"<="&{today})' % (COMPLETED, NO)
MXG = 'MAX(%s)' % ','.join(GAPT(t) for t in TECH6)
WKG = lambda k: 'COUNTIFS({range:jobs.status},%s,{range:jobs.request_sent},%s,{range:jobs.week},{today}-WEEKDAY({today},2)+1-%d)' % (COMPLETED, NO, 7 * k)
tools.append(TOOL('review_gap', 'Review Request Gap Finder', 'Completed jobs with no review request, by technician and week',
  'Type how many days back to look: completed jobs with no request sent, by technician and by week, the number to send today and the extra reviews at your current conversion of requests to reviews.', [
    I('days', 'Days back', 14, 'int')], [
    O('Completed jobs with no request', 'int', TOTG), O('Extra reviews at the shop rate', 'num', TOTG + '*IFERROR(%s/%s,0)' % (RTT('reviews'), RTT('requests'))),
    O('Most jobs with no request, one technician', 'int', MXG),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (TOTG, ck('Send the requests today'), ck('No gap: every job was asked')))] +
    [O('Jobs with no request, %s' % t, 'int', GAPT(t)) for t in TECH6] + [O('Jobs with no request, week %d back' % k if k else 'Jobs with no request, this week', 'int', WKG(k)) for k in range(4)],
  GR('What if', ('Last 7 days', {'days': 7}), ('Last 30 days', {'days': 30}), ('Last 60 days', {'days': 60}))))
# 9 referral value
REF12 = 'SUMIFS({range:reviews.referrals},{range:reviews.month},">="&%s,{range:reviews.month},"<="&%s)' % (EM(-11), MS)
MJ9 = '({in:ticket}*{set:margin_target})'
tools.append(TOOL('referral_value', 'Referral Value Tool', 'What a referral is worth against the thank-you you give',
  'Type the average ticket, the cost of your thank-you and the most of a first-job margin you would spend on one: referrals of the last 12 months, their value and margin, the value of one referral and a verdict.', [
    I('ticket', 'Average ticket, the amount billed on one job', 350), I('thank', 'Cost of one thank-you', 25), I('share', 'Most of the first-job margin to spend on a thank-you', 0.15, 'pct')], [
    O('Referrals, last 12 months', 'int', REF12), O('Value of the referral jobs', 'money', REF12 + '*{in:ticket}'), O('Margin on those jobs', 'money', REF12 + '*' + MJ9), O('Cost of the thank-yous', 'money', REF12 + '*{in:thank}'),
    O('Value of one referral after the thank-you', 'money', MJ9 + '-{in:thank}'), O('Most you could spend on a thank-you', 'money', MJ9 + '*{in:share}'), O('Revenue per spend, referral source', 'num', SRX('revenue_per_spend', tok('source', 'Referral'))),
    O('Verdict', 'text', 'IF({in:thank}<=%s*{in:share},%s,%s)' % (MJ9, ck('Thank more'), ck('Fine as it is')))],
  GR('What if', ('Thank-you 10', {'thank': 10}), ('Thank-you 60', {'thank': 60}), ('Ticket 600', {'ticket': 600}), ('Spend up to 30 percent', {'share': 0.3}))))
# 10 renewal dates register
def BN(b): return 'SUMIFS({range:bands.items},{range:bands.band},%s)' % tok('band', b)
def BC(b): return 'SUMIFS({range:bands.cost},{range:bands.band},%s)' % tok('band', b)
NEXT10 = 'SUMPRODUCT(MIN(({range:dates.item}={in:item})*({range:dates.status}=%s)*({range:dates.due_date}>={today}-3650)*{range:dates.due_date}+(1-({range:dates.item}={in:item})*({range:dates.status}=%s))*1000000))' % (OPEN, OPEN)
def ACT(k, col): return 'IFERROR(INDEX({range:dates.%s},MATCH(SMALL({range:dates.act_key},%d),{range:dates.act_key},0)),%s)' % (col, k, '0' if col in ('cost', 'days_left') else '""')
tools.append(TOOL('renewal_register', 'Renewal Dates Register', 'Renewal dates by band: red under 30 days, amber under 60, green later',
  'Pick a kind of renewal: the number and cost of items overdue, red, amber and green, the open items of that kind and the next one due, and the first three items to act on.', [
    IN('item', 'Renewal item', 'list', key('renewal', 'Vehicle insurance'), list='renewal')], [
    O('Overdue', 'int', BN('Overdue')), O('Red, within 30 days', 'int', BN('Red, within 30 days')), O('Amber, within 60 days', 'int', BN('Amber, within 60 days')), O('Green, later', 'int', BN('Green, later')),
    O('Cost of overdue and red items', 'money', BC('Overdue') + '+' + BC('Red, within 30 days')), O('Open items of the chosen kind', 'int', 'COUNTIFS({range:dates.item},{in:item},{range:dates.status},%s)' % OPEN),
    O('Next due date of that kind', 'date', 'IF(%s>=1000000,"",%s)' % (NEXT10, NEXT10)),
    O('Verdict', 'text', 'IF(%s+%s>0,%s,IF(%s>0,%s,%s))' % (BN('Overdue'), BN('Red, within 30 days'), ck('Act now on the red items'), BN('Amber, within 60 days'), ck('Plan the amber items'), ck('All green')))] +
    sum([[O('%d. Item to act on' % k, 'text', 'IFERROR(INDEX({range:dates.item},MATCH(SMALL({range:dates.act_key},%d),{range:dates.act_key},0))&" - "&INDEX({range:dates.holder},MATCH(SMALL({range:dates.act_key},%d),{range:dates.act_key},0)),"")' % (k, k)),
          O('%d. Days left' % k, 'int', ACT(k, 'days_left')), O('%d. Cost' % k, 'money', ACT(k, 'cost'))] for k in (1, 2, 3)], []),
  GR('What if', ('Business licence', {'item': '=' + tok('renewal', 'Business licence')}), ('Trade licence', {'item': '=' + tok('renewal', 'Trade licence')}), ('Liability insurance', {'item': '=' + tok('renewal', 'Liability insurance')}), ('Technician training', {'item': '=' + tok('renewal', 'Technician training')}))))
# 11 renewal budget
TOT11 = 'SUM({range:ren_budget.cost})'
MAXC = 'MAX({range:ren_budget.cost})'
BUD = round((sum(r['cost'] for r in D.LIC if D.iso(D.MS0) <= r['due_date'] < D.iso(D.add_months(D.MS0, 12))) * 1.2) / 500) * 500 or 20000
tools.append(TOOL('renewal_budget', 'Renewal Budget Tool', 'Renewal cost by month with a yearly budget and a rise',
  'Type a yearly budget and a cost rise: the cost of renewals over the next 12 months, with the rise, the month with the highest outflow, its share of the year and the budget left. Enter that outflow in your cash forecast.', [
    I('budget', 'Yearly renewal budget', BUD), I('rise', 'Cost rise at renewal', 0.10, 'pct')], [
    O('Renewals due, next 12 months', 'int', 'SUM({range:ren_budget.due})'), O('Cost, next 12 months', 'money', TOT11), O('Cost with the rise', 'money', TOT11 + '*(1+{in:rise})'), O('Average a month with the rise', 'money', TOT11 + '*(1+{in:rise})/12'),
    O('Month with the highest outflow', 'date', 'IFERROR(INDEX({range:ren_budget.month},MATCH(%s,{range:ren_budget.cost},0)),"")' % MAXC), O('Its cost with the rise', 'money', MAXC + '*(1+{in:rise})'),
    O('Its share of the year', 'pct', 'IFERROR(%s/%s,0)' % (MAXC, TOT11)), O('Budget left after the rise', 'money', '{in:budget}-' + TOT11 + '*(1+{in:rise})'), O('Cost with a 10 percent rise', 'money', TOT11 + '*1.1'),
    O('Verdict', 'text', 'IF({in:budget}>=%s*(1+{in:rise}),%s,%s)' % (TOT11, ck('Within the budget'), ck('Over budget: raise it or move a renewal')))],
  GR('Sensitivity', ('No rise', {'rise': 0}), ('Rise 5 percent', {'rise': 0.05}), ('Rise 10 percent', {'rise': 0.10}), ('Rise 15 percent', {'rise': 0.15}), ('Rise 20 percent', {'rise': 0.20}))))
# 12 renewal action list
INW = '{range:dates.status},%s,{range:dates.due_date},"<="&({today}+{in:days})' % OPEN
def ACTK(k, col, fmt):
    return 'IFERROR(INDEX({range:dates.%s},MATCH(SMALL({range:dates.act_key},%d),{range:dates.act_key},0)),%s)' % (col, k, '""')
out12 = []
for k in range(1, 4):
    m = 'MATCH(SMALL({range:dates.act_key},%d),{range:dates.act_key},0)' % k
    out12 += [O('%d. Item and holder' % k, 'text', 'IFERROR(INDEX({range:dates.item},%s)&" - "&INDEX({range:dates.holder},%s),"")' % (m, m)), O('%d. Days left' % k, 'int', 'IFERROR(INDEX({range:dates.days_left},%s),0)' % m),
              O('%d. Cost' % k, 'money', 'IFERROR(INDEX({range:dates.cost},%s),0)' % m), O('%d. Handled by' % k, 'text', 'IFERROR(INDEX({range:dates.handled_by},%s),"")' % m),
              O('%d. Start by' % k, 'date', 'IFERROR(INDEX({range:dates.due_date},%s)-{in:lead},"")' % m)]
tools.append(TOOL('renewal_actions', 'Renewal Action List', 'The next renewals to handle, who handles them and when to start',
  'Type the days ahead to look and the days of notice you need: open renewals due in that time with their cost, and the first five by days left with who handles each and the date to start. Use the message links on Renewal Dates.', [
    I('days', 'Days ahead', 60, 'int'), I('lead', 'Days of notice you need to arrange a renewal', 14, 'int')], [
    O('Open renewals in the window', 'int', 'COUNTIFS(%s)' % INW), O('Cost of those renewals', 'money', 'SUMIFS({range:dates.cost},%s)' % INW),
    O('Verdict', 'text', 'IF(COUNTIFS({range:dates.status},%s,{range:dates.due_date},"<="&({today}+{in:lead}))>0,%s,IF(COUNTIFS(%s)>0,%s,%s))' % (OPEN, ck('Start now: one is inside your notice'), INW, ck('Plan these renewals this month'), ck('Nothing due in the window')))] + out12,
  GR('What if', ('30 days ahead', {'days': 30}), ('90 days ahead', {'days': 90}), ('Seven days of notice', {'lead': 7}), ('Thirty days of notice', {'lead': 30}))))
# 13 owner scorecard
def LC(c): return 'COUNTIFS({range:scorecard.light},%s)' % c
tools.append(TOOL('owner_scorecard', 'Owner Scorecard', 'Seven measures and five more against your targets and your own history',
  'Pick a measure: its value, your target, your own last 12 months, the period before and the same time last year, the light, the trend and the money behind the gap, with the green, amber and red counts of all twelve.', [
    IN('measure', 'Scorecard measure', 'list', key('measure', 'Job margin, %'), list='measure')], [
    O('Value', 'num', SC('value')), O('Target', 'num', SC('target')), O('Own last 12 months', 'num', SC('own12')), O('Before this period', 'num', SC('prev')), O('Same time last year', 'num', SC('ly')),
    O('Gap to target, % of target', 'num', SC('gap_pct')), O('Light', 'text', SCT('light')), O('Trend against own 12 months', 'text', SCT('trend')), O('Money behind the gap, a year', 'money', SC('money_at_stake')), O('Note', 'text', SCT('note')),
    O('Measures green', 'int', LC(G)), O('Measures amber', 'int', LC(AM)), O('Measures red', 'int', LC(RD)),
    O('Verdict', 'text', 'IF(%s<=2,%s,IF(%s>=%s,%s,%s))' % (LC(RD), ck('Healthy: few reds'), LC(RD), LC(G), ck('Weak: more reds than greens'), ck('Mixed: work the reds first')))],
  GR('Measures', *[(m, {'measure': '=' + tok('measure', m)}) for m in MEASURES[:6] + MEASURES[7:9] + MEASURES[10:11]])))
# 14 weakest link
WL = 'MATCH(LARGE({range:scorecard.rank_key},{in:rank}),{range:scorecard.rank_key},0)'
def WLX(c): return 'IFERROR(INDEX({range:scorecard.%s},%s),0)' % (c, WL)
def WLT(c): return 'IFERROR(INDEX({range:scorecard.%s},%s)&"","")' % (c, WL)
tools.append(TOOL('weakest_link', 'Scorecard Weakest Link', 'The measure furthest below its target as a share of the target',
  'Type 1 for the weakest measure, 2 for the second: its value and target, the gap as a share of the target, the money behind it, the action and who owns it, and a verdict that names the one thing to work on this week.', [
    I('rank', 'Rank of the gap (1 is the weakest)', 1, 'int')], [
    O('Measure', 'text', WLT('measure')), O('Value', 'num', WLX('value')), O('Target', 'num', WLX('target')), O('Gap to target, % of target', 'num', WLX('gap_pct')), O('Light', 'text', WLT('light')),
    O('Money behind the gap, a year', 'money', WLX('money_at_stake')), O('Action for the week', 'text', WLT('action')), O('Owner', 'text', WLT('owner')),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (WLX('gap_pct'), ck('Work on this measure this week'), ck('On target: pick the next measure')))],
  GR('Next weakest', ('Second weakest', {'rank': 2}), ('Third weakest', {'rank': 3}), ('Fourth weakest', {'rank': 4}), ('Fifth weakest', {'rank': 5}))))
# 15 monday actions builder
out15 = []
for k in range(1, 6):
    out15 += [O('%d. Action and owner' % k, 'text', 'IFERROR(INDEX({range:actions.action},%d)&" - "&INDEX({range:actions.owner},%d),"")' % (k, k)),
              O('%d. Due' % k, 'date', 'IF(IFERROR(INDEX({range:actions.gap_pct},%d),0)>0,WORKDAY({today},ROUND({in:days}*%d/5,0)),"")' % (k, k)), O('%d. Money at stake' % k, 'money', 'IFERROR(INDEX({range:actions.money},%d),0)' % k)]
TOP5 = 'SUMIFS({range:actions.money},{range:actions.rank},"<=5")'
tools.append(TOOL('monday_builder', 'Monday Actions Builder', 'The five largest gaps as actions with owner, date and money',
  'Type the working days you give the largest action and the share of the gap you close this week: the five actions with owner, due date and money at stake, the money recovered a year and a verdict. Print Monday Actions.', [
    I('days', 'Working days for the fifth action', 5, 'int'), I('fix_share', 'Share of the gap you close', 0.5, 'pct')], [
    O('Money behind the five actions, a year', 'money', TOP5), O('Money recovered a year at your share', 'money', TOP5 + '*{in:fix_share}'), O('Red measures', 'int', LC(RD)),
    O('Share of all gap money in the five', 'pct', 'IFERROR(%s/SUM({range:actions.money}),0)' % TOP5), O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (TOP5, ck('Monday meeting: five actions ready'), ck('No gaps: review targets instead')))] + out15,
  GR('What if', ('Close all of the gap', {'fix_share': 1}), ('Close a quarter', {'fix_share': 0.25}), ('Seven days for the fifth', {'days': 7}), ('Three days for the fifth', {'days': 3}))))
# 16 targets tool
def MONTHS_AT(m, i):
    num = _num(m[0])
    op = '<=' if m[3] == 0 else '>='
    return 'SUMPRODUCT(%s*((%s*%d)%s{in:trial}))' % (_win(), num, m[2], op)
tools.append(TOOL('targets_tool', 'Targets and Typical Ranges', 'Try a target against your own best and worst month',
  'Pick a measure and type a trial target: your current target, the typical range to check against your numbers, your own highest and lowest month, the months of the last 12 that would have met the trial and a check.', [
    IN('measure', 'Scorecard measure', 'list', key('measure', 'Close rate, %'), list='measure'), I('trial', 'Trial target (percent, amount or months)', 60, 'num')], [
    O('Current target', 'num', 'IFERROR(INDEX({range:targets.target},MATCH({in:measure},{range:targets.setting},0)),0)'), O('Typical range', 'text', 'IFERROR(INDEX({range:targets.typical_range},MATCH({in:measure},{range:targets.setting},0))&"","")'),
    O('Own highest, 12 months', 'num', 'IFERROR(INDEX({range:targets.own_high},MATCH({in:measure},{range:targets.setting},0)),0)'), O('Own lowest, 12 months', 'num', 'IFERROR(INDEX({range:targets.own_low},MATCH({in:measure},{range:targets.setting},0)),0)'),
    O('Own average, 12 months', 'num', SC('own12')),
    O('Months that would have met the trial', 'int', 'CHOOSE(MATCH({in:measure},{range:scorecard.measure},0),%s)' % ','.join(MONTHS_AT(m, i) for i, m in enumerate(MEAS))),
    O('Verdict', 'text', 'IF({in:trial}>IFERROR(INDEX({range:targets.own_high},MATCH({in:measure},{range:targets.setting},0)),0),IF(OR(%s),%s,%s),IF({in:trial}<IFERROR(INDEX({range:targets.own_low},MATCH({in:measure},{range:targets.setting},0)),0),IF(OR(%s),%s,%s),%s))' % (
        ','.join('MATCH({in:measure},{range:scorecard.measure},0)=%d' % i for i in LOWER), ck('Easier than your best: raise the bar'), ck('Harder than your best month: a stretch'),
        ','.join('MATCH({in:measure},{range:scorecard.measure},0)=%d' % i for i in LOWER), ck('Harder than your worst month: a stretch'), ck('Easier than your worst: raise the bar'), ck('Inside your own range')))],
  GR('What if', ('Close rate 70', {'trial': 70}), ('Close rate 50', {'trial': 50}), ('Job margin 55', {'measure': '=' + tok('measure', 'Job margin, %'), 'trial': 55}), ('Callbacks 3', {'measure': '=' + tok('measure', 'Callback rate, shop, %'), 'trial': 3}))))
# 17 own-history comparison
out17 = [O('%s' % m.replace(', %', '').replace(', amount', '').replace(', months of fixed costs', ''), 'text', 'IFERROR(INDEX({range:scorecard.trend},%d),"")' % (i + 1)) for i, m in enumerate(MEASURES)]
tools.append(TOOL('history_compare', 'Own-History Comparison', 'This period against the one before, the last 12 months and last year',
  'Pick a measure: its value now, the period before, your last 12 months and the same time last year, the change against each and whether it is improving or slipping; the trend of all twelve measures is listed below.', [
    IN('measure', 'Scorecard measure', 'list', key('measure', 'Technician utilisation, %'), list='measure')], [
    O('Now', 'num', SC('value')), O('Before this period', 'num', SC('prev')), O('Own last 12 months', 'num', SC('own12')), O('Same time last year', 'num', SC('ly')),
    O('Change against the period before', 'num', SC('value') + '-' + SC('prev')), O('Change against last year', 'num', SC('value') + '-' + SC('ly')), O('Change against own 12 months', 'num', SC('value') + '-' + SC('own12')),
    O('Verdict', 'text', SCT('trend'))] + out17,
  GR('Measures', ('Callbacks', {'measure': '=' + tok('measure', 'Callback rate, shop, %')}), ('Close rate', {'measure': '=' + tok('measure', 'Close rate, %')}), ('Cash cover', {'measure': '=' + tok('measure', 'Cash cover, months of fixed costs')}), ('Net profit', {'measure': '=' + tok('measure', 'Net profit, %')}))))
# 18 start walk-through
STEPS = [s['step'] for s in D.start_steps_d()]
ins18 = [IN('s%d' % (i + 1), '%d. %s done' % (i + 1, s), 'list', 'yes' if i < 4 else 'no', list='yesno') for i, s in enumerate(STEPS)]
DONE18 = '(' + '+'.join('({in:s%d}=%s)' % (i + 1, YES) for i in range(10)) + ')'
NEXT18 = '""'
for i in range(9, -1, -1): NEXT18 = 'IF({in:s%d}=%s,%s,INDEX({range:start_steps.step},%d))' % (i + 1, YES, NEXT18, i + 1)
tools.append(TOOL('start_walk', 'Start Here Walk-Through', 'The first-week steps with a progress cell',
  'Say yes or no for each of the ten first-week steps: how many are done, the progress, the next step to do and the tab to open. Replace the demo data first, then set your targets.', ins18, [
    O('Steps done', 'int', DONE18), O('Progress', 'pct', DONE18 + '/10'), O('Next step to do', 'text', 'IF(%s=10,%s,%s)' % (DONE18, ck('All ten steps are done'), NEXT18)),
    O('Verdict', 'text', 'IF(%s=10,%s,IF(%s>=5,%s,%s))' % (DONE18, ck('Ready: read the scorecard each Monday'), DONE18, ck('Half way: keep going'), ck('Start with demo data and targets')))],
  GR('What if', ('All done', {'s%d' % i: '=' + YES for i in range(1, 11)}), ('None done', {'s%d' % i: '=' + NO for i in range(1, 11)}))))
assert len(tools) == 18, len(tools)
