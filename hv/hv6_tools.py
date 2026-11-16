"""HVAC suite part 6: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv6_lists import *
from hv6_tables import WS, WSL, WIN_DONE, WIN_EXP, WIN_PLANNED, WIN_DONEN, WIN_END, WEEKS_LEFT
import hv6_data as D
import datetime as _dt

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
ACT, RD, LAP, CAN = (tok('agrstatus', s) for s in ('Active', 'Renewal due', 'Lapsed', 'Cancelled'))
DONE, DUE, BOOKED, MISSED = (tok('visitstatus', s) for s in ('Done', 'Due', 'Booked', 'Missed'))
LAST, PREV = tok('period', 'Last 12 months'), tok('period', 'Previous 12 months')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
M12 = '{range:book_month.month},">="&EDATE(%s,-12),{range:book_month.month},"<"&%s' % (MS, MS)
AVGP = 'IFERROR(SUMIFS({range:agreements.price},{range:agreements.running},1)/COUNTIFS({range:agreements.running},1),0)'
COSTAVG = 'IFERROR(SUM({range:plan_profit.w_cost})/SUM({range:plan_profit.agreements}),0)'
FOLLOWAVG = 'IFERROR(SUM({range:plan_profit.w_follow})/SUM({range:plan_profit.agreements}),0)'
VISITAVG = 'IFERROR(SUM({range:plan_profit.w_visit})/SUM({range:plan_profit.agreements}),0)'
END12 = '{range:agreements.end_date},">="&EDATE(%s,-12),{range:agreements.end_date},"<"&%s' % (MS, MS)

tools = []
# 1 aged equipment lead list
TOPV = 'SUMIFS({range:equipment.replace_value},{range:equipment.lead_score},">="&IFERROR(LARGE({range:equipment.lead_score},{set:lead_quota}),0))'
OUT1 = []
for k in range(1, 5):
    OUT1 += [O('%d. Lead: equipment, type and site reference' % k, 'text', 'IFERROR(INDEX({range:aged.equipment_id},%d)&" "&INDEX({range:aged.type},%d)&" "&INDEX({range:aged.site_ref},%d),"")' % (k, k, k)),
             O('%d. Age in years' % k, 'num', 'IFERROR(INDEX({range:aged.age_years},%d)+0,0)' % k), O('%d. Replacement value' % k, 'money', 'IFERROR(INDEX({range:aged.replace_value},%d)+0,0)' % k)]
tools.append(TOOL('aged_leads', 'Aged Equipment Lead List', 'Aged equipment as replacement leads: who to call this week',
  'Type the age that makes a lead and the share of calls you expect to turn into a replacement: aged records, those never serviced by the shop, the replacement value, the top leads of the week and a call now, mail or hold verdict.', [
    I('min_age', 'Equipment older than, years', 12, 'int'), I('win', 'Share of calls that become a replacement', 0.12, 'pct')], [
    O('Equipment records at or over this age', 'int', 'COUNTIFS({range:equipment.age_years},">="&{in:min_age})'),
    O('Of them never serviced by the shop', 'int', 'COUNTIFS({range:equipment.age_years},">="&{in:min_age},{range:equipment.never_serviced},1)'),
    O('Replacement value of those records', 'money', 'SUMIFS({range:equipment.replace_value},{range:equipment.age_years},">="&{in:min_age})'),
    O('Leads to call each week', 'int', '{set:lead_quota}'), O('Replacement value of the top leads', 'money', TOPV), O('Expected revenue from the top leads at your share', 'money', TOPV + '*{in:win}'),
    O('Verdict', 'text', 'IF(COUNTIFS({range:equipment.age_years},">="&{in:min_age})=0,%s,IF(COUNTIFS({range:equipment.age_years},">="&{in:min_age})>={set:lead_quota},%s,%s))' % (ck('Hold'), ck('Call now'), ck('Mail')))] + OUT1,
  GR('What if', ('Over 10 years', {'min_age': 10}), ('Over 15 years', {'min_age': 15}), ('Win 20 percent', {'win': 0.2}), ('Win 5 percent', {'win': 0.05}))))
# 2 site and equipment lookup
SID = 'IFERROR(INDEX({range:sites.site_id},MATCH({in:site},{range:sites.site_ref},0)),"")'
def SL(c): return 'IFERROR(INDEX({range:sites.%s},MATCH({in:site},{range:sites.site_ref},0))&"","")' % c
def SN(c): return 'IFERROR(INDEX({range:sites.%s},MATCH({in:site},{range:sites.site_ref},0))+0,0)' % c
def AGS(c): return 'IFERROR(INDEX({range:agreements.%s},MATCH(%s,{range:agreements.site_id},0))&"","")' % (c, SID)
tools.append(TOOL('site_lookup', 'Site and Equipment Lookup', 'Everything on one site: equipment, age, service, agreement and jobs',
  'Type a site reference: the area, site type and phone, the equipment records with the oldest age and the last service, the agreement plan and renewal date, and the jobs and revenue to date. No personal data is shown.', [
    I('site', 'Site reference', D.DEF['site'], 'text')], [
    O('Site', 'text', SID), O('Area', 'text', SL('area')), O('Site type', 'text', SL('site_type')), O('Phone', 'text', SL('phone')), O('Landlord or business account', 'text', SL('account')),
    O('Equipment records', 'int', 'COUNTIFS({range:equipment.site_id},%s)' % SID), O('Oldest equipment, years', 'num', SN('oldest_age')),
    O('Last service', 'date', 'IFERROR(IF(INDEX({range:sites.last_service},MATCH({in:site},{range:sites.site_ref},0))=0,"",INDEX({range:sites.last_service},MATCH({in:site},{range:sites.site_ref},0))),"")'),
    O('Records never serviced by the shop', 'int', 'COUNTIFS({range:equipment.site_id},%s,{range:equipment.never_serviced},1)' % SID), O('Aged records', 'int', 'COUNTIFS({range:equipment.site_id},%s,{range:equipment.aged},1)' % SID),
    O('Agreement plan', 'text', 'IF(%s="",%s,%s)' % (AGS('plan'), ck('No agreement'), AGS('plan'))), O('Agreement status', 'text', AGS('status')),
    O('Renewal date', 'date', 'IFERROR(IF(INDEX({range:agreements.renewal_date},MATCH(%s,{range:agreements.site_id},0))=0,"",INDEX({range:agreements.renewal_date},MATCH(%s,{range:agreements.site_id},0))),"")' % (SID, SID)),
    O('Jobs to date', 'int', SN('jobs')), O('Revenue to date', 'money', SN('revenue')),
    O('Last job', 'date', 'IFERROR(IF(INDEX({range:sites.last_job},MATCH({in:site},{range:sites.site_ref},0))=0,"",INDEX({range:sites.last_job},MATCH({in:site},{range:sites.site_ref},0))),"")'),
    O('Verdict', 'text', 'IF(%s="",%s,IF(COUNTIFS({range:agreements.site_id},%s,{range:agreements.running},1)>0,%s,IF(COUNTIFS({range:equipment.site_id},%s,{range:equipment.aged},1)>0,%s,%s)))' % (SID, ck('Site not found'), SID, ck('Member: offer the next tune-up'), SID, ck('Offer a replacement review'), ck('Offer an agreement')))]))
# 3 equipment by age band
def BANDN(b): return 'SUMIFS({range:age_bands.records},{range:age_bands.band},%s)' % tok('ageband', b)
BASE3, BASEV3 = 'SUM({range:age_bands.expected})', 'SUM({range:age_bands.value})'
tools.append(TOOL('age_band_view', 'Replacements by Age Band', 'Equipment by age band and the replacements to expect next year',
  'Type the best and worst case spread and the replacements a month your install crew can do: records in each age band, the replacements expected next year from the shares on the Equipment by Age Band sheet and the revenue at your average replacement ticket, base, best and worst.', [
    I('spread', 'Best and worst case spread', 0.25, 'pct'), I('crew', 'Replacements a month the install crew can do', 12, 'int')], [
    O('Records, 0 to 5 years', 'int', BANDN('Up to 5 years')), O('Records, 6 to 10 years', 'int', BANDN('From 6 to 10 years')), O('Records, 11 to 15 years', 'int', BANDN('From 11 to 15 years')), O('Records, over 15 years', 'int', BANDN('Over 15 years')),
    O('Share of records over 15 years', 'pct', 'IFERROR(%s/SUM({range:age_bands.records}),0)' % BANDN('Over 15 years')),
    O('Base: replacements expected next year', 'int', BASE3), O('Best: replacements expected next year', 'int', BASE3 + '*(1+{in:spread})'), O('Worst: replacements expected next year', 'int', BASE3 + '*(1-{in:spread})'),
    O('Base: replacement revenue', 'money', BASEV3), O('Best: replacement revenue', 'money', BASEV3 + '*(1+{in:spread})'), O('Worst: replacement revenue', 'money', BASEV3 + '*(1-{in:spread})'),
    O('Base: replacements a month', 'num', BASE3 + '/12'), O('Best: replacements a month', 'num', BASE3 + '*(1+{in:spread})/12'),
    O('Expected revenue, Furnace', 'money', 'SUMIFS({range:age_bands.value},{range:age_bands.type},%s)' % tok('equiptype', 'Furnace')), O('Expected revenue, Air conditioner', 'money', 'SUMIFS({range:age_bands.value},{range:age_bands.type},%s)' % tok('equiptype', 'Air conditioner')),
    O('Expected revenue, Water heater', 'money', 'SUMIFS({range:age_bands.value},{range:age_bands.type},%s)' % tok('equiptype', 'Water heater')),
    O('Verdict', 'text', 'IF(%s*(1+{in:spread})/12>{in:crew},%s,IF(%s/12>{in:crew}*0.8,%s,%s))' % (BASE3, ck('Plan extra install capacity'), BASE3, ck('Crew is nearly full in the best case'), ck('Crew can cover it')))],
  GR('What if', ('Spread 40 percent', {'spread': 0.4}), ('Spread 10 percent', {'spread': 0.1}), ('Crew does 8 a month', {'crew': 8}), ('Crew does 20 a month', {'crew': 20}))))
# 4 agreement book health
def BM(col, m): return 'SUMIFS({range:book_month.%s},{range:book_month.month},%s)' % (col, m)
RR12 = 'IFERROR(SUMIFS({range:book_month.renewed},%s)/(SUMIFS({range:book_month.renewed},%s)+SUMIFS({range:book_month.renew_lapsed},%s)),0)' % (M12, M12, M12)
GROW = 'IFERROR(%s/%s-1,0)' % (BM('running', MS), BM('running', 'EDATE(%s,-12)' % MS))
tools.append(TOOL('book_health', 'Agreement Book Health', 'Is the agreement book growing, flat or shrinking?',
  'Type the change in running agreements you call flat: running now against 12 months ago, new and ended agreements, monthly recurring revenue, the renewal rate of the last 12 months against your target and a growing, flat or shrinking verdict.', [
    I('flat', 'Change in running agreements that counts as flat', 0.02, 'pct')], [
    O('Running agreements now', 'int', BM('running', MS)), O('Running agreements 12 months ago', 'int', BM('running', 'EDATE(%s,-12)' % MS)), O('Change in 12 months', 'pct', GROW),
    O('New agreements, last 12 months', 'int', 'SUMIFS({range:book_month.new},%s)' % M12), O('Agreements ended, last 12 months', 'int', 'SUMIFS({range:book_month.lapsed},%s)' % M12),
    O('Monthly recurring revenue now', 'money', BM('mrr', MS)), O('Monthly recurring revenue 12 months ago', 'money', BM('mrr', 'EDATE(%s,-12)' % MS)),
    O('Renewal rate, last 12 months', 'pct', RR12), O('Renewal rate target', 'pct', '{set:renewal_target}'), O('Gap to the target, points', 'pct', RR12 + '-{set:renewal_target}'),
    O('Renewal rate, this month to date', 'pct', BM('renew_rate', MS)), O('Renewals still open this month', 'int', 'COUNTIFS({range:renewals.month},%s,{range:renewals.outcome},%s)' % (MS, tok('renewout', 'Open'))),
    O('Yearly agreement revenue now', 'money', BM('mrr', MS) + '*12'),
    O('Verdict', 'text', 'IF(%s>{in:flat},%s,IF(%s<-{in:flat},%s,%s))' % (GROW, ck('Growing'), GROW, ck('Shrinking'), ck('Flat')))],
  GR('What if', ('Flat is 5 percent', {'flat': 0.05}), ('Flat is 10 percent', {'flat': 0.1}), ('Flat is 0 percent', {'flat': 0}))))
# 5 renewals due this month
OUT5 = []
for k in range(1, 11):
    OUT5.append(O('%d. Agreement, site, plan, price, days left' % k, 'text', 'IFERROR(INDEX({range:renew_due.agreement_id},%d)&" "&INDEX({range:renew_due.site_ref},%d)&" "&INDEX({range:renew_due.plan},%d)&" "&INDEX({range:renew_due.price},%d)&" "&INDEX({range:renew_due.days_left},%d),"")' % ((k,) * 5)))
tools.append(TOOL('renew_calls', 'Renewals Due This Month', 'Which renewals to call first this month',
  'Type the share of due renewals you expect to keep: agreements due this month and not yet renewed, the yearly fees at risk, those past the date and in the red days, the ten to call first ranked by value then days left and a call-by date for each.', [
    I('keep', 'Share of due renewals you expect to keep', D.DEF['rate'], 'pct')], [
    O('Renewals due this month, not yet renewed', 'int', 'SUM({range:agreements.due_month})'), O('Yearly fees at risk', 'money', 'SUMIFS({range:agreements.price},{range:agreements.due_month},1)'),
    O('Expected loss at your keep share', 'money', 'SUMIFS({range:agreements.price},{range:agreements.due_month},1)*(1-{in:keep})'), O('Past the renewal date', 'int', 'COUNTIFS({range:agreements.due_month},1,{range:agreements.days_left},"<0")'),
    O('Due inside the red days', 'int', 'COUNTIFS({range:agreements.due_month},1,{range:agreements.days_left},"<="&{set:renewal_warn_days})'), O('Fees of the ten to call first', 'money', 'SUMIFS({range:renew_due.price},{range:renew_due.rank_no},"<=10")'),
    O('Verdict', 'text', 'IF(SUM({range:agreements.due_month})=0,%s,IF(COUNTIFS({range:agreements.due_month},1,{range:agreements.days_left},"<0")>0,%s,IF(COUNTIFS({range:agreements.due_month},1,{range:agreements.days_left},"<="&{set:renewal_warn_days})>0,%s,%s)))' % (ck('Nothing due'), ck('Call now: some are past the date'), ck('Call this week'), ck('Plan the calls')))] + OUT5,
  GR('What if', ('Keep 95 percent', {'keep': 0.95}), ('Keep 70 percent', {'keep': 0.7}), ('Keep 50 percent', {'keep': 0.5}))))
# 6 lapse analyser
LREAS = ['Ended for: %s' % r for r in LAPSE_REASONS]
MAINR = 'IFERROR(INDEX({range:agreements.lapse_reason},MATCH(MAX({range:agreements.reason_n}),{range:agreements.reason_n},0))&"","")'
tools.append(TOOL('lapse_analyser', 'Lapse Analyser', 'Why agreements end and what it costs a year',
  'Pick a plan and the share you hope to win back: agreements ended in the last 12 months, the yearly fees lost, the reasons noted, the plan with the highest lapse rate and a verdict on what to fix first.', [
    IN('plan', 'Plan', 'list', key('plan', 'Basic comfort'), list='plan'), I('winback', 'Share you expect to win back', 0.15, 'pct')], [
    O('Agreements ended, last 12 months', 'int', 'COUNTIFS(%s)' % END12), O('Yearly fees lost', 'money', 'SUMIFS({range:agreements.price},%s)' % END12),
    O('Ended, chosen plan', 'int', 'COUNTIFS(%s,{range:agreements.plan},{in:plan})' % END12), O('Yearly fees lost, chosen plan', 'money', 'SUMIFS({range:agreements.price},%s,{range:agreements.plan},{in:plan})' % END12),
    O('Average months as a member before ending', 'num', 'IFERROR(AVERAGEIFS({range:agreements.months_member},%s),0)' % END12),
    O('Lapse rate of the chosen plan, all time', 'pct', 'IFERROR(INDEX({range:plan_status.lapse_rate},MATCH({in:plan},{range:plan_status.plan},0)),0)'),
    O('Plan with the highest lapse rate', 'text', 'IFERROR(INDEX({range:plan_status.plan},MATCH(MAX({range:plan_status.lapse_rate}),{range:plan_status.lapse_rate},0))&"","")'), O('Highest lapse rate', 'pct', 'MAX({range:plan_status.lapse_rate})')] +
    [O(l, 'int', 'COUNTIFS(%s,{range:agreements.lapse_reason},%s)' % (END12, tok('lapsereason', r))) for l, r in zip(LREAS, LAPSE_REASONS)] + [
    O('Main reason, last 12 months', 'text', MAINR), O('Yearly fees you could win back', 'money', 'SUMIFS({range:agreements.price},%s)*{in:winback}' % END12),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)=0,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s)))' % (END12, ck('No lapses to study'), MAINR, tok('lapsereason', 'Price too high'), ck('Main reason is price: test a lower plan'), MAINR, tok('lapsereason', 'Service not as expected'), ck('Main reason is service: review visits'), ck('Life events: send the win-back letter')))],
  GR('Every plan', *[(p, {'plan': '=' + tok('plan', p)}) for p in PLAN_NAMES])))
# 7 agreement attach rate
def AT(col, per=LAST): return 'SUMIFS({range:attach.%s},{range:attach.technician},{in:tech},{range:attach.period},%s)' % (col, per)
ATR = 'IFERROR(%s/%s,0)' % (AT('sold'), AT('eligible'))
tools.append(TOOL('attach_rate', 'Agreement Attach Rate', 'Which technician needs coaching on selling agreements',
  'Pick a technician: agreements sold over the eligible jobs of the last 12 months against your attach target, the bonus cost, the shop rate, the best technician and the agreements to sell to reach the target, with a coach or on target verdict.', [
    IN('tech', 'Technician', 'list', key('tech', 'Jamal Whitfield'), list='tech')], [
    O('Eligible jobs, last 12 months', 'int', AT('eligible')), O('Agreements sold, last 12 months', 'int', AT('sold')), O('Attach rate', 'pct', ATR), O('Attach target', 'pct', '{set:attach_target}'), O('Gap to the target, points', 'pct', ATR + '-{set:attach_target}'),
    O('Attach rate, previous 12 months', 'pct', 'IFERROR(%s/%s,0)' % (AT('sold', PREV), AT('eligible', PREV))), O('Bonus cost of the agreements sold', 'money', AT('spiff_cost')),
    O('Shop attach rate, last 12 months', 'pct', 'IFERROR(SUMIFS({range:attach.sold},{range:attach.period},%s)/SUMIFS({range:attach.eligible},{range:attach.period},%s),0)' % (LAST, LAST)),
    O('Best technician, last 12 months', 'text', 'IFERROR(INDEX({range:attach.technician},MATCH(MAX({range:attach.rate_last}),{range:attach.rate_last},0))&"","")'), O('Best attach rate', 'pct', 'MAX({range:attach.rate_last})'),
    O('Rank of this technician, 1 is highest', 'int', '1+COUNTIFS({range:attach.rate_last},">"&%s)' % ATR),
    O('Agreements to sell to reach the target', 'int', 'MAX(0,ROUNDUP({set:attach_target}*%s,0)-%s)' % (AT('eligible'), AT('sold'))),
    O('Bonus cost to get there', 'money', 'MAX(0,ROUNDUP({set:attach_target}*%s,0)-%s)*{set:spiff_agreement}' % (AT('eligible'), AT('sold'))),
    O('Verdict', 'text', 'IF(%s>={set:attach_target},%s,%s)' % (ATR, ck('On target'), ck('Coach on the offer')))],
  GR('Every technician', *[(t, {'tech': '=' + tok('tech', t)}) for t in TECH6])))
# 8 plan sign-ups needed
CONTR = '(%s*(1+{in:rise})-%s+%s*{set:follow_margin})' % (AVGP, COSTAVG, FOLLOWAVG)
NEED8 = 'IF(%s<=0,0,ROUNDUP({in:fixed}/%s,0))' % (CONTR, CONTR)
GOALN = 'ROUNDUP({in:goal}*12/(%s*(1+{in:rise})),0)' % AVGP
RUNN = 'COUNTIFS({range:agreements.running},1)'
NEW6 = 'SUMIFS({range:book_month.new},{range:book_month.month},">="&EDATE(%s,-6),{range:book_month.month},"<"&%s)/6' % (MS, MS)
tools.append(TOOL('signups_needed', 'Plan Sign-Ups Needed', 'How many agreements to sign to cover the visit program',
  'Type the fixed cost of the visit program a year, the recurring revenue you want and the months you give yourself: the profit of an average agreement with its follow-on work, the agreements needed to cover the fixed cost and to reach the goal, and the sign-ups a month against your own recent pace.', [
    I('fixed', 'Fixed cost of the visit program a year', 96000), I('goal', 'Monthly recurring revenue you want', 8000), I('months', 'Months to get there', 12, 'int'), I('rise', 'Price change on agreements', 0, 'pct')], [
    O('Running agreements now', 'int', RUNN), O('Average price a year', 'money', AVGP + '*(1+{in:rise})'), O('Visit, travel and discount cost a year, per agreement', 'money', COSTAVG),
    O('Follow-on profit a year, per agreement', 'money', FOLLOWAVG + '*{set:follow_margin}'), O('Profit of an average agreement a year', 'money', CONTR),
    O('Agreements needed to cover the fixed cost', 'int', NEED8), O('Agreements still to sign for the fixed cost', 'int', 'MAX(0,%s-%s)' % (NEED8, RUNN)),
    O('Agreements needed for the recurring revenue goal', 'int', GOALN), O('Agreements still to sign for the goal', 'int', 'MAX(0,%s-%s)' % (GOALN, RUNN)),
    O('Sign-ups a month needed for the goal', 'num', 'MAX(0,%s-%s)/{in:months}' % (GOALN, RUNN)), O('Sign-ups a month, last 6 months', 'num', NEW6),
    O('Monthly recurring revenue now', 'money', BM('mrr', MS)),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s<%s,%s,IF(MAX(0,%s-%s)/{in:months}<=%s,%s,%s)))' % (CONTR, ck('Agreements lose money: fix the price'), RUNN, NEED8, ck('Fixed cost not covered yet'), GOALN, RUNN, NEW6, ck('On pace for the goal'), ck('Behind: raise sign-ups')))],
  GR('Sensitivity', ('Price up 5 percent', {'rise': 0.05}), ('Price up 10 percent', {'rise': 0.1}), ('Price down 5 percent', {'rise': -0.05}), ('Goal 10,000 a month', {'goal': 10000}), ('Fixed cost 150,000', {'fixed': 150000}), ('Give it 24 months', {'months': 24}))))
# 9 tune-up window tracker
WTXT = 'IF(MONTH(%s)=8,%s,%s)' % (WS, tok('visitseason', 'Autumn heating check'), tok('visitseason', 'Spring cooling check'))
GAP9 = '(%s-%s)' % (WIN_DONE(), WIN_EXP())
tools.append(TOOL('window_tracker', 'Tune-Up Window Tracker', 'Is the open tune-up window on pace?',
  'Type the points behind last year that count as amber and red: the open window (or the one that ended last), visits planned, done, booked and behind, the share done against the same point last year, the visits to book this week and a traffic light.', [
    I('amber', 'Points behind last year that count as amber', 0.05, 'pct'), I('red', 'Points behind last year that count as red', 0.15, 'pct')], [
    O('Open window', 'text', WTXT), O('Window starts', 'date', WS), O('Window ends', 'date', WIN_END), O('Days left in the window', 'int', 'MAX(0,%s-{today})' % WIN_END),
    O('Visits planned in the window', 'int', WIN_PLANNED()), O('Visits done', 'int', WIN_DONEN()), O('Visits booked, not yet done', 'int', 'COUNTIFS({range:visits.window_start},%s,{range:visits.status},%s)' % (WS, BOOKED)),
    O('Visits still to book', 'int', 'COUNTIFS({range:visits.window_start},%s,{range:visits.status},%s)' % (WS, DUE)), O('Visits behind their planned date', 'int', 'COUNTIFS({range:visits.window_start},%s,{range:visits.behind},1)' % WS),
    O('Share done now', 'pct', WIN_DONE()), O('Share done at this point last year', 'pct', WIN_EXP()), O('Gap to last year, points', 'pct', GAP9),
    O('Visits short of last year pace', 'int', 'MAX(0,ROUND(%s*%s,0)-%s)' % (WIN_EXP(), WIN_PLANNED(), WIN_DONEN())),
    O('Visits to book this week', 'int', 'ROUNDUP(MAX(0,%s-%s)/%s,0)' % (WIN_PLANNED(), WIN_DONEN(), WEEKS_LEFT)),
    O('Visit value still to do', 'money', 'SUMIFS({range:visits.visit_value},{range:visits.window_start},%s,{range:visits.status},%s)+SUMIFS({range:visits.visit_value},{range:visits.window_start},%s,{range:visits.status},%s)' % (WS, DUE, WS, BOOKED)),
    O('Verdict', 'text', 'IF(%s<-{in:red},%s,IF(%s<-{in:amber},%s,%s))' % (GAP9, ck('Red: behind the pace of last year'), GAP9, ck('Amber: slightly behind'), ck('Green: on pace')))],
  GR('What if', ('Amber at 10 points', {'amber': 0.1}), ('Red at 30 points', {'red': 0.3}), ('Red at 5 points', {'red': 0.05}))))
# 10 tune-up scheduling by season
def VM(c, k): return 'INDEX({range:visits_month.%s},%d)' % (c, k)
def SLK(k): return '({in:techs}*%s-%s*{in:vh})' % (VM('hours_per_tech', k), VM('visits_due', k))
LIM = '({in:techs}/{in:vh})'
OUT10 = [O('Load, month %d' % k, 'pct', 'IFERROR(%s*{in:vh}/{in:techs}/1,0)' % VM('visits_per_hour', k)) for k in range(1, 13)]
OVER10 = 'COUNTIFS({range:visits_month.visits_per_hour},">"&%s)' % LIM
EMPTY10 = 'COUNTIFS({range:visits_month.visits_per_hour},"<"&({in:empty}*%s),{range:visits_month.demand_index},"<0.9",{range:visits_month.month},">0")' % LIM
tools.append(TOOL('tuneup_schedule', 'Tune-Up Scheduling by Season', 'Which months are over capacity and which are too empty',
  'Type the technicians who run tune-ups, the hours of a visit and the load under which a month counts as empty: for 12 months the visits due against the free technician hours after the other work of the season, the slack and a verdict for each month.', [
    I('techs', 'Technicians who run tune-ups', 4, 'int'), I('vh', 'Hours of one tune-up visit, drive included', 1.8, 'num'), I('empty', 'Load under which a month is too empty', 0.5, 'pct')], [
    O('Months over capacity', 'int', OVER10), O('Months too empty in a slow season', 'int', EMPTY10), O('First month of the plan', 'date', VM('month', 1)),
    O('Busiest month', 'date', 'IFERROR(INDEX({range:visits_month.month},MATCH(MAX({range:visits_month.visits_per_hour}),{range:visits_month.visits_per_hour},0)),"")'), O('Load of the busiest month', 'pct', 'MAX({range:visits_month.visits_per_hour})*{in:vh}/{in:techs}'),
    O('Emptiest month', 'date', 'IFERROR(INDEX({range:visits_month.month},MATCH(MIN({range:visits_month.visits_per_hour}),{range:visits_month.visits_per_hour},0)),"")'), O('Load of the emptiest month', 'pct', 'MIN({range:visits_month.visits_per_hour})*{in:vh}/{in:techs}'),
    O('Verdict', 'text', 'IF(%s>0,%s,IF(%s>0,%s,%s))' % (OVER10, ck('Move visits out of the busy months'), EMPTY10, ck('Book more tune-ups into the slow months'), ck('Schedule fits')))] + OUT10,
  GR('What if', ('Five technicians', {'techs': 5}), ('Three technicians', {'techs': 3}), ('Longer visits, 2.5 hours', {'vh': 2.5}), ('Empty under 30 percent', {'empty': 0.3}))))
# 11 visit overdue list
def MV(k): return 'MATCH(LARGE({range:visits.overdue_score},%d),{range:visits.overdue_score},0)' % k
OUT11 = [O('%d. Visit, site, plan, plan price, days past the window end' % k, 'text', 'IFERROR(INDEX({range:visits.visit_id},%s)&" "&INDEX({range:visits.site_ref},%s)&" "&INDEX({range:visits.plan},%s)&" "&INDEX({range:visits.plan_price},%s)&" "&INDEX({range:visits.days_past_end},%s),"")' % ((MV(k),) * 5)) for k in range(1, 11)]
tools.append(TOOL('visit_overdue', 'Visit Overdue List', 'Missed tune-up visits to rebook first, ranked by plan value',
  'Type the share of missed visits you expect to rebook: visits whose window ended without a visit in the look-back days, the value of those visits, the expected recovery and the eight to call first ranked by plan value.', [
    I('win', 'Share of missed visits you expect to rebook', 0.6, 'pct')], [
    O('Visits overdue', 'int', 'COUNTIFS({range:visits.overdue_score},">0")'), O('Value of the overdue visits', 'money', 'SUMIFS({range:visits.visit_value},{range:visits.overdue_score},">0")'),
    O('Plan fees on those agreements', 'money', 'SUMIFS({range:visits.plan_price},{range:visits.overdue_score},">0")'), O('Expected recovery at your share', 'money', 'SUMIFS({range:visits.visit_value},{range:visits.overdue_score},">0")*{in:win}'),
    O('Look-back days', 'int', '{set:overdue_back_days}'),
    O('Verdict', 'text', 'IF(COUNTIFS({range:visits.overdue_score},">0")=0,%s,IF(COUNTIFS({range:visits.overdue_score},">0")>=10,%s,%s))' % (ck('Nothing overdue'), ck('Call the list today'), ck('Call this week')))] + OUT11,
  GR('What if', ('Rebook 80 percent', {'win': 0.8}), ('Rebook 40 percent', {'win': 0.4}))))
# 12 slow-season filler
SLOWC = '{range:visits_month.demand_index},"<0.9",{range:visits_month.visits_per_hour},"<"&({in:techs}/{in:vh}),{range:visits_month.month},">0"'
SLOWH = '({in:techs}*SUMIFS({range:visits_month.hours_per_tech},%s)-{in:vh}*SUMIFS({range:visits_month.visits_due},%s))' % (SLOWC, SLOWC)
SLOWN = 'COUNTIFS({range:visits_month.demand_index},"<0.9",{range:visits_month.month},">0")'
FIT = 'ROUNDDOWN(%s*{in:share}/{in:vh},0)' % SLOWH
tools.append(TOOL('slow_filler', 'Slow-Season Filler', 'Free hours in the slow months that tune-ups could fill',
  'Type the technicians, the hours of a visit, the share of free hours you can really book and the value of one visit: the free hours of the slow months, the tune-ups that fit, the revenue added and a verdict.', [
    I('techs', 'Technicians who run tune-ups', 4, 'int'), I('vh', 'Hours of one tune-up visit, drive included', 1.8, 'num'), I('share', 'Share of free hours you can book', 0.7, 'pct'), I('price', 'Value of one tune-up visit', D.DEF['avg_visit']),
    I('minimum', 'Revenue that makes the effort worth it', 3000)], [
    O('Slow months in the 12 months', 'int', SLOWN), O('Free hours in the slow months', 'num', SLOWH), O('Hours you can fill', 'num', SLOWH + '*{in:share}'),
    O('Tune-ups that fit', 'int', FIT), O('Revenue added', 'money', FIT + '*{in:price}'), O('Revenue added a slow month', 'money', 'IFERROR(%s*{in:price}/%s,0)' % (FIT, SLOWN)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s*{in:price}>={in:minimum},%s,%s))' % (FIT, ck('No room in the slow months'), FIT, ck('Fill the slow months with tune-ups'), ck('A small gain: fill when convenient')))],
  GR('What if', ('Book 90 percent', {'share': 0.9}), ('Book 40 percent', {'share': 0.4}), ('Visit worth 150', {'price': 150}), ('Five technicians', {'techs': 5}))))
# 13 agreement profit by plan
def PP(c): return 'IFERROR(AVERAGEIFS({range:plan_profit.%s},{range:plan_profit.plan},{in:plan}),0)' % c
PRICE13 = 'IFERROR(INDEX({range:plans.price},MATCH({in:plan},{range:plans.plan},0)),0)*(1+{in:rise})'
COST13 = '(%s+%s+%s)' % (PP('visit_total'), PP('travel_total'), PP('discount_given'))
MARG13 = 'IFERROR((%s-%s)/(%s),0)' % (PRICE13, COST13, PRICE13)
FP13 = PP('follow_on') + '*{set:follow_margin}'
tools.append(TOOL('plan_profit_tool', 'Agreement Profit by Plan', 'Price up, hold or add a visit',
  'Pick a plan and a price change: the price, the cost of the visits, the travel and the member discount, the profit and margin on the plan, the profit on the follow-on repairs and replacements of members, and a price up, hold or add a visit verdict.', [
    IN('plan', 'Plan', 'list', key('plan', 'Basic comfort'), list='plan'), I('rise', 'Price change', 0, 'pct'), I('floor', 'Margin you want on a plan', 0.2, 'pct')], [
    O('Price a year', 'money', PRICE13), O('Visits a year', 'int', 'IFERROR(INDEX({range:plans.visits_per_year},MATCH({in:plan},{range:plans.plan},0)),0)'), O('Cost of the visits a year', 'money', PP('visit_total')),
    O('Travel cost a year', 'money', PP('travel_total')), O('Member discount given a year', 'money', PP('discount_given')), O('Cost a year', 'money', COST13),
    O('Profit on the plan', 'money', PRICE13 + '-' + COST13), O('Margin on the plan', 'pct', MARG13), O('Follow-on revenue a year, per agreement', 'money', PP('follow_on')),
    O('Profit on follow-on work', 'money', FP13), O('Plan and follow-on profit', 'money', PRICE13 + '-' + COST13 + '+' + FP13),
    O('Running agreements on the plan', 'int', 'SUMIFS({range:plan_profit.agreements},{range:plan_profit.plan},{in:plan})'),
    O('Plan and follow-on profit, all agreements of the plan', 'money', '(%s-%s+%s)*SUMIFS({range:plan_profit.agreements},{range:plan_profit.plan},{in:plan})' % (PRICE13, COST13, FP13)),
    O('Verdict', 'text', 'IF(%s<{in:floor},%s,IF(AND(%s>={in:floor}+0.25,%s>=2*(%s)),%s,%s))' % (MARG13, ck('Price up'), MARG13, FP13, PRICE13, ck('Add a visit'), ck('Hold')))],
  GR('Every plan', *[(p, {'plan': '=' + tok('plan', p)}) for p in PLAN_NAMES])))
# 14 member value
SM, SN_ = 'SUMIFS({range:member_rev.sites},{range:member_rev.member},%s)', 'SUMIFS({range:member_rev.sites},{range:member_rev.member},%s)'
def RV(col, who): return 'SUMIFS({range:member_rev.%s},{range:member_rev.member},%s)' % (col, who)
RM = 'IFERROR(%s/%s,0)' % (RV('total_revenue', YES), RV('sites', YES)); RNN = 'IFERROR(%s/%s,0)' % (RV('total_revenue', NO), RV('sites', NO))
FEE = 'IFERROR(%s/%s,0)' % (RV('agreement_fees', YES), RV('sites', YES))
EXTRA = '(%s-%s-%s)' % (RM, FEE, RNN)
VAL14 = '(%s-%s+%s*{in:margin})' % (FEE, VISITAVG, EXTRA)
BE14 = 'MAX(0,%s-%s*{in:margin})' % (VISITAVG, EXTRA)
tools.append(TOOL('member_value', 'Member Value', 'What a member is worth against a non-member, and the break-even price',
  'Type the margin on repair and replacement work: revenue per member site against revenue per non-member site over the last 12 months, the yearly value of a member after the cost of the visits, and the break-even plan price against your average price.', [
    I('margin', 'Margin on repair and replacement work', 0.45, 'pct')], [
    O('Member sites', 'int', RV('sites', YES)), O('Non-member sites', 'int', RV('sites', NO)), O('Revenue per member site, last 12 months', 'money', RM), O('Revenue per non-member site, last 12 months', 'money', RNN),
    O('Difference per site', 'money', RM + '-' + RNN), O('Agreement fees per member site', 'money', FEE), O('Work revenue per member above a non-member', 'money', EXTRA),
    O('Cost of the visits and travel per member', 'money', VISITAVG), O('Yearly value of a member', 'money', VAL14), O('Break-even plan price', 'money', BE14), O('Average plan price now', 'money', AVGP),
    O('Room above break-even', 'money', AVGP + '-' + BE14),
    O('Verdict', 'text', 'IF(%s<%s,%s,IF(%s<%s*1.1,%s,%s))' % (AVGP, BE14, ck('Below break-even: raise price or cost'), AVGP, BE14, ck('Close to break-even: watch the cost'), ck('Members pay their way')))],
  GR('What if', ('Margin 35 percent', {'margin': 0.35}), ('Margin 55 percent', {'margin': 0.55}), ('Margin 25 percent', {'margin': 0.25}))))
# 15 agreement price test
NP = 'COUNTIFS({range:agreements.plan},{in:plan},{range:agreements.running},1)'
RV0 = 'SUMIFS({range:agreements.price},{range:agreements.plan},{in:plan},{range:agreements.running},1)'
LOSTN = '%s*{in:lapse}' % NP
SAVED = '%s*(%s+%s)' % (LOSTN, PP('visit_total'), PP('travel_total'))
LOSTFP = '%s*%s' % (LOSTN, FP13)
DREV = '%s*((1+{in:rise})*(1-{in:lapse})-1)' % RV0
tools.append(TOOL('price_test', 'Agreement Price Test', 'Raise the agreement price? Revenue, lapses and the break-even lapse',
  'Pick a plan, a price rise and the extra lapses you fear: running agreements, the revenue change, the visit cost you save, the follow-on profit you lose with each lapse, the break-even lapse increase and a raise or hold verdict.', [
    IN('plan', 'Plan', 'list', key('plan', 'Standard comfort'), list='plan'), I('rise', 'Price rise', 0.08, 'pct'), I('lapse', 'Extra lapse rate caused by the rise', 0.03, 'pct')], [
    O('Running agreements on the plan', 'int', NP), O('Price now', 'money', 'IFERROR(INDEX({range:plans.price},MATCH({in:plan},{range:plans.plan},0)),0)'),
    O('New price', 'money', 'IFERROR(INDEX({range:plans.price},MATCH({in:plan},{range:plans.plan},0)),0)*(1+{in:rise})'), O('Yearly revenue now', 'money', RV0),
    O('Yearly revenue after the rise and the extra lapses', 'money', RV0 + '*(1+{in:rise})*(1-{in:lapse})'), O('Change in yearly revenue', 'money', DREV),
    O('Agreements lost to the rise', 'num', LOSTN), O('Visit and travel cost you save', 'money', SAVED), O('Follow-on profit you lose', 'money', LOSTFP),
    O('Change in profit', 'money', '%s+%s-%s' % (DREV, SAVED, LOSTFP)), O('Break-even lapse increase on revenue alone', 'pct', '{in:rise}/(1+{in:rise})'),
    O('Agreements you can lose before revenue falls', 'num', NP + '*{in:rise}/(1+{in:rise})'),
    O('Verdict', 'text', 'IF(%s+%s-%s>0,%s,%s)' % (DREV, SAVED, LOSTFP, ck('Raise the price'), ck('Hold the price')))],
  GR('Sensitivity', ('Rise 2 percent', {'rise': 0.02}), ('Rise 5 percent', {'rise': 0.05}), ('Rise 12 percent', {'rise': 0.12}), ('Lapse 1 percent', {'lapse': 0.01}), ('Lapse 6 percent', {'lapse': 0.06}))))
# 16 pre-season campaign planner
CH_COST = 'IF({in:channel}=%s,{set:cost_text},IF({in:channel}=%s,{set:cost_letter},{set:cost_call}))' % (tok('channel', 'Text message'), tok('channel', 'Mailed letter'))
NSITES = 'COUNTIFS({range:sites.oldest_age},">="&{in:min_age},{range:sites.gap_months},">="&{in:months})'
RATE_OLD = 'IFERROR(COUNTIFS({range:campaign.equip_age},">="&{in:min_age},{range:campaign.booked},%s)/COUNTIFS({range:campaign.equip_age},">="&{in:min_age}),0)' % YES
RATE_ALL = 'IFERROR(COUNTIFS({range:campaign.booked},%s)/COUNTA({range:campaign.campaign_id}),0)' % YES
CONV = 'IFERROR(COUNTIFS({range:campaign.converted},%s)/COUNTIFS({range:campaign.booked},%s),0)' % (YES, YES)
tools.append(TOOL('campaign_plan', 'Pre-Season Campaign Planner', 'Who to remind before the season, and what it will cost',
  'Type the equipment age, the months since the last service and the channel: the sites to remind, the booked rate from your own campaign history, the tune-ups and agreements you can expect, the cost per booked tune-up and per agreement sold, and a send or limit to older equipment verdict.', [
    I('min_age', 'Oldest equipment at the site at least, years', 8, 'num'), I('months', 'Months since the last service at least', 12, 'int'), IN('channel', 'Channel', 'list', key('channel', 'Mailed letter'), list='channel')], [
    O('Sites to remind', 'int', NSITES), O('Of them never serviced by the shop', 'int', 'COUNTIFS({range:sites.oldest_age},">="&{in:min_age},{range:sites.gap_months},999)'), O('Cost of one reminder', 'money', CH_COST),
    O('Cost of the reminders', 'money', NSITES + '*' + CH_COST), O('Booked rate from history, sites with older equipment', 'pct', RATE_OLD), O('Booked rate from history, all reminders', 'pct', RATE_ALL),
    O('Booked rate you want', 'pct', '{set:booked_target}'), O('Tune-ups you can expect to book', 'int', NSITES + '*' + RATE_OLD), O('Agreements you can expect to sell', 'num', NSITES + '*' + RATE_OLD + '*' + CONV),
    O('Cost per booked tune-up', 'money', 'IFERROR(%s/%s,0)' % (CH_COST, RATE_OLD)), O('Cost per booked tune-up, all ages', 'money', 'IFERROR(%s/%s,0)' % (CH_COST, RATE_ALL)),
    O('Cost per agreement sold', 'money', 'IFERROR(%s/(%s*%s),0)' % (CH_COST, RATE_OLD, CONV)),
    O('Verdict', 'text', 'IF(NOT(%s>0),%s,IF(IFERROR(%s/%s,0)>{set:cost_booked_target},%s,IF(IFERROR(%s/%s,0)<={set:cost_booked_target},%s,%s)))' % (NSITES, ck('No sites match: widen the filter'), CH_COST, RATE_OLD, ck('Cost too high: change the channel'), CH_COST, RATE_ALL, ck('Send'), ck('Limit to older equipment')))],
  GR('What if', ('Phone calls', {'channel': '=' + tok('channel', 'Phone call')}), ('Text messages', {'channel': '=' + tok('channel', 'Text message')}), ('Only equipment over 12 years', {'min_age': 12}), ('Not serviced in 24 months', {'months': 24}), ('Over 5 years', {'min_age': 5}))))
# 17 campaign results
CWIN = '{range:campaign.reminder_sent},">="&({today}-{in:days})'
def CC(ch, extra=''): return 'COUNTIFS(%s,{range:campaign.channel},%s%s)' % (CWIN, tok('channel', ch), extra)
def CPB(ch): return 'IFERROR(SUMIFS({range:campaign.cost},%s,{range:campaign.channel},%s)/%s,9999)' % (CWIN, tok('channel', ch), CC(ch, ',{range:campaign.booked},%s' % YES))
CPBS = [CPB(c) for c in CHANNELS]
CPB_ALL = 'IFERROR(SUMIFS({range:campaign.cost},%s)/COUNTIFS(%s,{range:campaign.booked},%s),0)' % (CWIN, CWIN, YES)
CPB_SEL = 'IFERROR(SUMIFS({range:campaign.cost},%s,{range:campaign.channel},{in:channel})/COUNTIFS(%s,{range:campaign.channel},{in:channel},{range:campaign.booked},%s),0)' % (CWIN, CWIN, YES)
CPB_SELX = 'IFERROR(SUMIFS({range:campaign.cost},%s,{range:campaign.channel},{in:channel})/COUNTIFS(%s,{range:campaign.channel},{in:channel},{range:campaign.booked},%s),9999)' % (CWIN, CWIN, YES)
OUT17 = []
for c in CHANNELS:
    OUT17 += [O('%s: reminders' % c, 'int', CC(c)), O('%s: tune-ups booked' % c, 'int', CC(c, ',{range:campaign.booked},%s' % YES)), O('%s: cost per booked tune-up' % c, 'money', 'IF(%s=9999,0,%s)' % (CPB(c), CPB(c)))]
tools.append(TOOL('campaign_results', 'Campaign Channel Results', 'Which reminder channel books tune-ups at the lowest cost',
  'Pick a channel and the days back: reminders, tune-ups booked, agreements sold, cost and cost per booked tune-up for the channel against the shop average, the three channels ranked by cost per booked tune-up and the cheapest channel.', [
    IN('channel', 'Channel', 'list', key('channel', 'Mailed letter'), list='channel'), I('days', 'Days back', 365, 'int')], [
    O('Reminders, chosen channel', 'int', 'COUNTIFS(%s,{range:campaign.channel},{in:channel})' % CWIN), O('Tune-ups booked', 'int', 'COUNTIFS(%s,{range:campaign.channel},{in:channel},{range:campaign.booked},%s)' % (CWIN, YES)),
    O('Agreements sold', 'int', 'COUNTIFS(%s,{range:campaign.channel},{in:channel},{range:campaign.converted},%s)' % (CWIN, YES)), O('Cost of the reminders', 'money', 'SUMIFS({range:campaign.cost},%s,{range:campaign.channel},{in:channel})' % CWIN),
    O('Booked rate', 'pct', 'IFERROR(COUNTIFS(%s,{range:campaign.channel},{in:channel},{range:campaign.booked},%s)/COUNTIFS(%s,{range:campaign.channel},{in:channel}),0)' % (CWIN, YES, CWIN)),
    O('Cost per booked tune-up', 'money', CPB_SEL), O('Shop average cost per booked tune-up', 'money', CPB_ALL),
    O('Rank of the channel by cost, 1 is cheapest', 'int', '1+IF(%s<%s,1,0)+IF(%s<%s,1,0)+IF(%s<%s,1,0)' % (CPBS[0], CPB_SELX, CPBS[1], CPB_SELX, CPBS[2], CPB_SELX)),
    O('Cheapest channel', 'text', 'IF(AND(%s<=%s,%s<=%s),%s,IF(%s<=%s,%s,%s))' % (CPBS[0], CPBS[1], CPBS[0], CPBS[2], tok('channel', 'Text message'), CPBS[1], CPBS[2], tok('channel', 'Mailed letter'), tok('channel', 'Phone call'))),
    O('Verdict', 'text', 'IF(%s<=%s,%s,%s)' % (CPB_SEL, CPB_ALL, ck('Keep this channel'), ck('Shift to the cheapest channel')))] + OUT17,
  GR('Every channel', *[(c, {'channel': '=' + tok('channel', c)}) for c in CHANNELS])))
# 18 agreement revenue forecast
def RM_(m, r, s): return '({R0}*POWER(POWER(%s,1/12),%d)+%s*(1-POWER(POWER(%s,1/12),%d))/(1-POWER(%s,1/12)))' % (r, m, s, r, m, r)
def RSUM(r, s):
    q = 'POWER(%s,1/12)' % r
    S = '(%s*(1-POWER(%s,12))/(1-%s))' % (q, q, q)
    return '({R0}*%s+%s*(12-%s)/(1-%s))' % (S, s, S, q)
R0 = 'COUNTIFS({range:agreements.running},1)'
RB, SB = '{in:rate}', '{in:signups}'
RBEST, SBEST = 'MIN(0.99,{in:rate}+{in:step})', '{in:signups}*(1+{in:spread})'
RWORST, SWORST = 'MAX(0.5,{in:rate}-{in:step})', '{in:signups}*(1-{in:spread})'
def SC(name, r, s):
    o = [O('%s: agreements in 6 months' % name, 'int', RM_(6, r, s).replace('{R0}', R0)), O('%s: agreements in 12 months' % name, 'int', RM_(12, r, s).replace('{R0}', R0)),
         O('%s: monthly recurring revenue in 12 months' % name, 'money', RM_(12, r, s).replace('{R0}', R0) + '*{in:price}/12'), O('%s: recurring revenue over the next 12 months' % name, 'money', RSUM(r, s).replace('{R0}', R0) + '*{in:price}/12')]
    return o
MRR12B = RM_(12, RB, SB).replace('{R0}', R0) + '*{in:price}/12'
tools.append(TOOL('agr_forecast', 'Agreement Revenue Forecast', 'Recurring revenue for the next 12 months: base, best and worst',
  'Type the renewal rate, the sign-ups a month and the average price (your own last months are the defaults): running agreements and the recurring revenue 6 and 12 months ahead and over the next 12 months, base, best and worst, and the sign-ups a month that hold the book flat.', [
    I('rate', 'Renewal rate you expect', D.DEF['rate'], 'pct'), I('signups', 'New agreements a month', D.DEF['signups'], 'num'), I('price', 'Average price a year', D.DEF['avg_price']), I('step', 'Renewal rate step for best and worst', 0.05, 'pct'), I('spread', 'Sign-up spread for best and worst', 0.25, 'pct')], [
    O('Running agreements now', 'int', R0), O('Monthly recurring revenue now', 'money', BM('mrr', MS)), O('Sign-ups a month that hold the book flat', 'num', '%s*(1-POWER({in:rate},1/12))' % R0)] +
    SC('Base', RB, SB) + SC('Best', RBEST, SBEST) + SC('Worst', RWORST, SWORST) + [
    O('Verdict', 'text', 'IF(%s>%s*1.02,%s,IF(%s<%s*0.98,%s,%s))' % (MRR12B, BM('mrr', MS), ck('Growing'), MRR12B, BM('mrr', MS), ck('Shrinking'), ck('Flat')))],
  GR('What if', ('Renewals at 80 percent', {'rate': 0.8}), ('Renewals at 95 percent', {'rate': 0.95}), ('Sign-ups 8 a month', {'signups': 8}), ('Sign-ups 2 a month', {'signups': 2}), ('Price 260', {'price': 260}))))
assert len(tools) == 18, len(tools)
