"""Therapy practice suite part 7: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th7_lists import *
import th7_data as D

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
M0 = 'DATE(YEAR({today}),MONTH({today}),1)'
S12 = 'DATE(YEAR({today}),MONTH({today})-11,1)'
M3 = 'DATE(YEAR({today}),MONTH({today})-3,1)'
CAN = tok('grpst', 'Cancelled')
def WDN(x):
    return 'IF(%s=%s,1,IF(%s=%s,2,IF(%s=%s,3,IF(%s=%s,4,IF(%s=%s,5,6)))))' % (x, tok('wday', 'Monday'), x, tok('wday', 'Tuesday'), x, tok('wday', 'Wednesday'), x, tok('wday', 'Thursday'), x, tok('wday', 'Friday'))
def NEXTWD(base, wd): return '(%s+MOD(%s-WEEKDAY(%s,2),7))' % (base, WDN(wd), base)
def SM(col, src, frm, to=None):
    c = '{range:sourcemonths.%s},{range:sourcemonths.source},%s,{range:sourcemonths.month},">="&%s' % (col, src, frm)
    if to: c += ',{range:sourcemonths.month},"<"&%s' % to
    return 'SUMIFS(%s)' % c
def FUT(): return '({range:groups.start_date}>{today})*({range:groups.status}<>%s)' % CAN
def NEXTPROG(p):
    f = '({range:groups.program}=%s)*%s' % (p, FUT())
    return 'SUMPRODUCT(MIN(%s*{range:groups.start_date}+(1-%s)*99999))' % (f, f)
def KR(kind_label): return 'IFERROR(INDEX({range:campaigns.kind_return},MATCH(%s,{range:campaigns.kind},0)),0)' % tok('mkind', kind_label)

# ---- 1 referral source value
VPE = 'IFERROR(INDEX({range:sourcemonths.val_enq_12m},MATCH({in:src},{range:sourcemonths.source},0)),0)'
# ---- 8 budget split
KINDS = MARKETING_KINDS
SHARES = ['{in:s%d}' % (i + 1) for i in range(len(KINDS))]
PLAN8 = '+'.join('{in:budget}*%s*%s/100' % (SHARES[i], KR(k)) for i, k in enumerate(KINDS))
MINR = 'MIN({range:campaigns.kind_return})'; MAXR = 'MAX({range:campaigns.kind_return})'
SHW8 = '(%s)' % '+'.join('IF(%s=%s,%s,0)' % (KR(k), MINR, SHARES[i]) for i, k in enumerate(KINDS))
MOVED8 = 'MIN({in:move}*{in:budget},{in:budget}*%s)' % SHW8
# ---- 18 forecast
def SRC6(name):
    cnt = D.collections.Counter((e['date'][:7]) for e in D.ENQ if e['source'] == name)
    return [cnt[iso(month_start(k))[:7]] for k in range(6, 0, -1)]
F18 = '(({in:m4}+{in:m5}+{in:m6})/3)'
P18 = '(({in:m1}+{in:m2}+{in:m3})/3)'
SC18 = 'CHOOSE({in:sc},1,1.15,0.85)'
def FC18(k): return 'ROUND(%s*POWER({in:trend},%d)*%s,0)' % (F18, k, SC18)
ALLB3 = 'SUMIFS({range:sourcemonths.booked},{range:sourcemonths.month},">="&%s,{range:sourcemonths.month},"<"&%s)/3' % (M3, M0)
EXTRA18 = '(%s-%s)*{in:share}' % (FC18(3), F18)

d6 = SRC6('Doctor referral')

tools = [
 TOOL('source_value', 'Referral Source Value', 'Referral Source Value: invest, hold or cut a source',
  'Choose a referral source and type its enquiries, booked share, sessions per client and charge; see the value per enquiry and per client, your own 12-month value, the rank among sources and a verdict.', [
  IL('src', 'Referral source', 'src', 'Doctor referral'), I('enq', 'Enquiries a year from this source', 60), I('share', 'Booked share of enquiries', 0.5, 'pct'), I('sess', 'Sessions per client', 12, 'num'), I('charge', 'Average charge per session', 105, 'money')], [
  O('Booked clients a year', 'num', '{in:enq}*{in:share}'), O('Value per client (revenue)', 'money', '{in:sess}*{in:charge}'), O('Value per enquiry (revenue)', 'money', '{in:share}*{in:sess}*{in:charge}'),
  O('Revenue from this source in a year', 'money', '{in:enq}*{in:share}*{in:sess}*{in:charge}'),
  O('Your own value per enquiry, last 12 months', 'money', VPE),
  O('Your own value per client, last 12 months', 'money', 'IFERROR(INDEX({range:sourcemonths.val_client_12m},MATCH({in:src},{range:sourcemonths.source},0)),0)'),
  O('Rank among the 9 sources by value per enquiry (1 = best)', 'int', '1+COUNTIFS({range:sourcemonths.val_enq_12m},">"&%s)/COUNTIFS({range:sourcemonths.source},{in:src})' % VPE),
  O('Best source by value per enquiry', 'text', 'INDEX({range:sourcemonths.source},MATCH(MAX({range:sourcemonths.val_enq_12m}),{range:sourcemonths.val_enq_12m},0))'),
  O('Average value per enquiry, all sources', 'money', 'AVERAGE({range:sourcemonths.val_enq_12m})'),
  O('Verdict', 'text', 'IF({in:share}*{in:sess}*{in:charge}>=1.1*AVERAGE({range:sourcemonths.val_enq_12m}),%s,IF({in:share}*{in:sess}*{in:charge}<0.9*AVERAGE({range:sourcemonths.val_enq_12m}),%s,%s))' % (vd('Invest'), vd('Cut'), vd('Hold')))],
  GR('What if', ('Booked share 35%', {'share': 0.35}), ('Booked share 65%', {'share': 0.65}), ('Short stays: 6 sessions', {'sess': 6}), ('Employer program', {'src': '=' + tok('src', 'Employer program')}), ('Online directory', {'src': '=' + tok('src', 'Online directory')}))),
 TOOL('cost_per', 'Cost per Client Won', 'Cost per Enquiry and per Client Won',
  'Choose an activity kind and type its cost, enquiries and clients won; see the cost per enquiry and per client won against the value of one client and against your own history for that kind.', [
  IL('kind', 'Activity kind', 'mkind', 'School talk'), I('cost', 'Cost of the activity', 90, 'money'), I('enq', 'Enquiries', 6), I('won', 'Clients won', 3), I('sess', 'Sessions per client', 14, 'num')], [
  O('Cost per enquiry', 'money', '{in:cost}/{in:enq}'), O('Cost per client won', 'money', '{in:cost}/{in:won}'), O('Clients won per enquiry', 'pct', '{in:won}/{in:enq}'),
  O('Margin value of one client', 'money', '{in:sess}*{set:avg_charge}*{set:margin_pct}'), O('Profit after the cost', 'money', '{in:won}*{in:sess}*{set:avg_charge}*{set:margin_pct}-{in:cost}'),
  O('Most you accept to pay to win a client', 'money', '{set:max_cost_client}'),
  O('Your own cost per client won for this kind, all history', 'money', 'IFERROR(SUMIFS({range:campaigns.cost},{range:campaigns.kind},{in:kind})/SUMIFS({range:campaigns.clients_won},{range:campaigns.kind},{in:kind}),0)'),
  O('Verdict', 'text', 'IF({in:cost}/{in:won}<=MIN({set:max_cost_client},{in:sess}*{set:avg_charge}*{set:margin_pct}),%s,%s)' % (vd('Profitable'), vd('Losing')))],
  GR('What if', ('Cost doubles: 180', {'cost': 180}), ('Only 1 client won', {'won': 1}), ('Flyers: 610, 9 enquiries, 1 client', {'kind': '=' + tok('mkind', 'Printed flyers'), 'cost': 610, 'enq': 9, 'won': 1}),
     ('Newsletter: 20, 6 enquiries, 3 clients', {'kind': '=' + tok('mkind', 'Newsletter'), 'cost': 20, 'enq': 6, 'won': 3}), ('Short stays: 4 sessions', {'sess': 4}))),
 TOOL('marketing_return', 'Marketing Return', 'Marketing Return with Base, Best and Worst',
  'Type the cost, clients you expect, sessions per client, charge and margin, and a scenario (1 Base, 2 Best, 3 Worst); see the return on spend, months to pay back and whether to repeat it.', [
  I('cost', 'Cost of the activity', 600, 'money'), I('won', 'Clients expected', 4), I('sess', 'Sessions per client', 14, 'num'), I('charge', 'Average charge per session', 105, 'money'), I('margin', 'Share of each charge left as margin', 0.4, 'pct'),
  I('sc', 'Scenario: 1 Base, 2 Best, 3 Worst', 1)], [
  O('Clients won in this scenario', 'num', '{in:won}*CHOOSE({in:sc},1,1.3,0.6)'), O('Revenue from those clients', 'money', '{in:won}*CHOOSE({in:sc},1,1.3,0.6)*{in:sess}*{in:charge}'),
  O('Margin from those clients', 'money', '{in:won}*CHOOSE({in:sc},1,1.3,0.6)*{in:sess}*{in:charge}*{in:margin}'),
  O('Profit after the cost', 'money', '{in:won}*CHOOSE({in:sc},1,1.3,0.6)*{in:sess}*{in:charge}*{in:margin}-{in:cost}'),
  O('Return on spend, %', 'pct', '({in:won}*CHOOSE({in:sc},1,1.3,0.6)*{in:sess}*{in:charge}*{in:margin}-{in:cost})/{in:cost}'),
  O('Months of client sessions to pay the cost back', 'num', '{in:cost}/({in:won}*CHOOSE({in:sc},1,1.3,0.6)*{in:charge}*{set:client_sessions_month}*{in:margin})'),
  O('Clients needed to break even', 'num', '{in:cost}/({in:sess}*{in:charge}*{in:margin})'),
  O('Your cost per client won, last 12 months, all activities', 'money', 'IFERROR(SUMIFS({range:campaigns.cost},{range:campaigns.date},">="&({today}-365))/SUMIFS({range:campaigns.clients_won},{range:campaigns.date},">="&({today}-365)),0)'),
  O('Verdict', 'text', 'IF({in:won}*CHOOSE({in:sc},1,1.3,0.6)*{in:sess}*{in:charge}*{in:margin}>{in:cost},%s,%s)' % (vd('Worth repeating'), vd('Stop')))],
  GR('What if', ('1 client only', {'won': 1}), ('2 clients', {'won': 2}), ('Worst scenario', {'sc': 3}), ('Best scenario', {'sc': 2}), ('Costly: 1,500 for 4 clients', {'cost': 1500}))),
 TOOL('client_value', 'Client Lifetime Value', 'Client Lifetime Value and Most to Spend',
  'Type sessions per client, charge, margin per session and the share of the client margin you keep; see the value of one client, the most you can spend to win one and your cost per client now.', [
  I('sess', 'Sessions per client', 14, 'num'), I('charge', 'Average charge per session', 105, 'money'), I('margin', 'Margin per session', 42, 'money'), I('keep', 'Share of the client margin you want to keep', 0.5, 'pct')], [
  O('Revenue per client', 'money', '{in:sess}*{in:charge}'), O('Margin per client', 'money', '{in:sess}*{in:margin}'), O('Most you can spend to win one client', 'money', '{in:sess}*{in:margin}*(1-{in:keep})'),
  O('Average revenue per client in your data', 'money', 'AVERAGE({range:clientvalue.revenue})'),
  O('Your cost per client won, last 12 months', 'money', 'IFERROR(SUMIFS({range:campaigns.cost},{range:campaigns.date},">="&({today}-365))/SUMIFS({range:campaigns.clients_won},{range:campaigns.date},">="&({today}-365)),0)'),
  O('Headroom per client (most to spend minus your cost)', 'money', '{in:sess}*{in:margin}*(1-{in:keep})-IFERROR(SUMIFS({range:campaigns.cost},{range:campaigns.date},">="&({today}-365))/SUMIFS({range:campaigns.clients_won},{range:campaigns.date},">="&({today}-365)),0)'),
  O('Months of margin to pay back cost per client', 'num', 'IFERROR(SUMIFS({range:campaigns.cost},{range:campaigns.date},">="&({today}-365))/SUMIFS({range:campaigns.clients_won},{range:campaigns.date},">="&({today}-365))/({in:margin}*{set:client_sessions_month}),0)'),
  O('Verdict', 'text', 'IF({in:sess}*{in:margin}*(1-{in:keep})>=IFERROR(SUMIFS({range:campaigns.cost},{range:campaigns.date},">="&({today}-365))/SUMIFS({range:campaigns.clients_won},{range:campaigns.date},">="&({today}-365)),0),%s,%s)' % (vd('Spend more'), vd('Spend less')))],
  GR('What if', ('Short stays: 6 sessions', {'sess': 6}), ('Long stays: 24 sessions', {'sess': 24}), ('Keep 80% of the margin', {'keep': 0.8}), ('Margin 25 a session', {'margin': 25}), ('Lower charge: 90', {'charge': 90, 'margin': 34}))),
 TOOL('directory_check', 'Directory Listing Check', 'Directory Listing Check: keep, renegotiate or drop a listing',
  'Choose a listing and type its monthly fee, enquiries, clients won per enquiry and a client\'s monthly margin; see the months to pay back a year\'s fee, the highest fee that pays back and a verdict.', [
  IL('listing', 'Directory listing', 'listing', 'Directory listing 1'), I('fee', 'Monthly fee', 45, 'money'), I('enq', 'Enquiries a month', 6, 'num'), I('share', 'Clients won per enquiry', 0.5, 'pct'), I('margin', 'Margin per client per month', 84, 'money')], [
  O('Clients won a month', 'num', '{in:enq}*{in:share}'), O('Cost per client won', 'money', '{in:fee}/({in:enq}*{in:share})'), O('Fee for a year', 'money', '12*{in:fee}'),
  O('Months to pay back one listing (a year\'s fee)', 'num', '12*{in:fee}/({in:enq}*{in:share}*{in:margin})'), O('Most months you accept', 'num', '{set:max_payback_months}'),
  O('Highest monthly fee that pays back in time', 'money', '{in:enq}*{in:share}*{in:margin}*{set:max_payback_months}/12'),
  O('Your own average months to pay back, this listing', 'num', 'IFERROR(AVERAGEIFS({range:directory.payback_months},{range:directory.listing},{in:listing}),0)'),
  O('Months with no client won, this listing', 'int', 'COUNTIFS({range:directory.listing},{in:listing},{range:directory.clients_won},0)'),
  O('Verdict', 'text', 'IF(12*{in:fee}/({in:enq}*{in:share}*{in:margin})<={set:max_payback_months},%s,IF(12*{in:fee}/({in:enq}*{in:share}*{in:margin})<=2*{set:max_payback_months},%s,%s))' % (vd('Keep'), vd('Renegotiate'), vd('Drop')))],
  GR('What if', ('Fee doubles: 90', {'fee': 90}), ('Few enquiries: 2 a month', {'enq': 2}), ('Weak booking: 20%', {'share': 0.2}), ('Fee 150, 4 enquiries', {'fee': 150, 'enq': 4}), ('Second listing', {'listing': '=' + tok('listing', 'Directory listing 2'), 'fee': 30}))),
 TOOL('workshop_planner', 'Workshop Planner', 'Workshop Planner: run it or skip it',
  'Type the room hours, materials, expected attendees, any fee, expected enquiries and the booked share; see the cost, the expected value, the fee that covers the cost and a verdict.', [
  I('hrs', 'Room hours', 2.5, 'num'), I('mat', 'Materials and printing', 30, 'money'), I('att', 'Expected attendees', 20), I('fee', 'Fee per attendee (0 if free)', 0, 'money'), I('enq', 'Expected enquiries', 3, 'num'),
  I('share', 'Booked share of enquiries', 0.5, 'pct'), I('value', 'Margin value of one client', 588, 'money')], [
  O('Room cost', 'money', '{in:hrs}*{set:room_cost_hour}'), O('Total cost', 'money', '{in:hrs}*{set:room_cost_hour}+{in:mat}'), O('Income from fees', 'money', '{in:att}*{in:fee}'),
  O('Net cost after fees', 'money', '{in:hrs}*{set:room_cost_hour}+{in:mat}-{in:att}*{in:fee}'), O('Net cost per attendee', 'money', '({in:hrs}*{set:room_cost_hour}+{in:mat}-{in:att}*{in:fee})/{in:att}'),
  O('Clients expected', 'num', '{in:enq}*{in:share}'), O('Expected value of those clients', 'money', '{in:enq}*{in:share}*{in:value}'),
  O('Expected net benefit', 'money', '{in:enq}*{in:share}*{in:value}-({in:hrs}*{set:room_cost_hour}+{in:mat}-{in:att}*{in:fee})'),
  O('Fee per attendee that covers the total cost', 'money', '({in:hrs}*{set:room_cost_hour}+{in:mat})/{in:att}'), O('Enquiries needed to cover the net cost', 'num', '({in:hrs}*{set:room_cost_hour}+{in:mat}-{in:att}*{in:fee})/({in:share}*{in:value})'),
  O('Your own enquiries per 100 attendees, past events', 'num', 'SUM({range:workshops.enquiries})*100/SUM({range:workshops.attendees})'),
  O('Verdict', 'text', 'IF({in:enq}*{in:share}*{in:value}>({in:hrs}*{set:room_cost_hour}+{in:mat}-{in:att}*{in:fee}),%s,%s)' % (vd('Run it'), vd('Skip it')))],
  GR('What if', ('Only 1 enquiry', {'enq': 1}), ('No enquiries', {'enq': 0}), ('Fee 10 a head', {'fee': 10}), ('Small room, 10 people', {'hrs': 1.5, 'att': 10}), ('Big hall, 8 hours', {'hrs': 8, 'mat': 120}))),
 TOOL('referrer_schedule', 'Referrer Contact Schedule', 'Referrer Contact Schedule: who to contact first',
  'Type when you last contacted a referrer, how often you want to, their referrals and a client value; see the next contact date, the value of this referrer and the three referrers to contact first.', [
  I('last', 'Last contact date', 'today-100', 'date'), I('every', 'Contact every (days)', 90), I('refs', 'Referrals in the last 12 months', 9), I('share', 'Booked share of referrals', 0.5, 'pct'), I('value', 'Value of one client (revenue)', 1470, 'money')], [
  O('Next contact date', 'date', '{in:last}+{in:every}'), O('Days left (plus) or overdue (minus)', 'int', '{in:last}+{in:every}-{today}'), O('Booked clients a year from this referrer', 'num', '{in:refs}*{in:share}'),
  O('Value of this referrer in a year (revenue)', 'money', '{in:refs}*{in:share}*{in:value}'), O('Referrers past their contact rhythm now', 'int', 'COUNTIFS({range:referrers.contact_check},%s)' % ck('Contact due')),
  O('Contact first: rank 1', 'text', 'IFERROR(INDEX({range:referrers.name},MATCH(1,{range:referrers.act_rank},0)),%s)' % vd('No referrer is overdue')),
  O('Value of rank 1, last 12 months', 'money', 'IFERROR(INDEX({range:referrers.value_12m},MATCH(1,{range:referrers.act_rank},0)),0)'),
  O('Contact second: rank 2', 'text', 'IFERROR(INDEX({range:referrers.name},MATCH(2,{range:referrers.act_rank},0)),"")'),
  O('Contact third: rank 3', 'text', 'IFERROR(INDEX({range:referrers.name},MATCH(3,{range:referrers.act_rank},0)),"")'),
  O('Verdict', 'text', 'IF({in:last}+{in:every}<={today},%s,%s)' % (vd('Contact now'), vd('On rhythm now')))],
  GR('What if', ('Last contact 30 days ago', {'last': '={today}-30'}), ('Contact every 60 days', {'every': 60}), ('A top referrer: 20 referrals', {'refs': 20}), ('Last contact 200 days ago', {'last': '={today}-200'}))),
 TOOL('budget_split', 'Marketing Budget Split', 'Marketing Budget Split: move money to the strongest channel',
  'Type the yearly budget and the share for each activity kind; see the amount per month, the clients the plan should win, your strongest and weakest kind and how much to move.', [
  I('budget', 'Yearly marketing budget', 4800, 'money')] + [I('s%d' % (i + 1), 'Share: ' + k, v, 'pct') for i, (k, v) in enumerate(zip(KINDS, [0.20, 0.20, 0.08, 0.08, 0.10, 0.12, 0.14, 0.08]))] + [
  I('move', 'Share of the budget to move', 0.1, 'pct'), I('keep', 'Share of the strongest return kept on extra money', 0.3, 'pct')], [
  O('%s: amount a month' % k, 'money', '{in:budget}*%s/12' % SHARES[i]) for i, k in enumerate(KINDS)] + [
  O('Shares add up to', 'pct', '+'.join(SHARES)),
  O('Strongest kind by clients won per 100 spent', 'text', 'INDEX({range:campaigns.kind},MATCH(%s,{range:campaigns.kind_return},0))' % MAXR), O('Clients won per 100 spent, strongest', 'num', MAXR),
  O('Weakest kind by clients won per 100 spent', 'text', 'INDEX({range:campaigns.kind},MATCH(%s,{range:campaigns.kind_return},0))' % MINR), O('Clients won per 100 spent, weakest', 'num', MINR),
  O('Clients the plan should win in a year, at your past returns', 'num', PLAN8), O('Amount to move from the weakest to the strongest kind', 'money', MOVED8),
  O('Extra clients a year if the best kind keeps its return', 'num', '%s*(%s*{in:keep}-%s)/100' % (MOVED8, MAXR, MINR)),
  O('Verdict', 'text', 'IF(AND(%s>0,%s>%s),%s,%s)' % (MOVED8, MAXR, MINR, vd('Move budget to the strongest channel'), vd('Budget is balanced')))],
  GR('What if', ('Move 5%', {'move': 0.05}), ('Move 20%', {'move': 0.2}), ('Bigger budget: 7,200', {'budget': 7200}), ('Strongest keeps 10%', {'keep': 0.1}))),
 TOOL('group_pricing', 'Group Program Pricing', 'Group Program Pricing: is the fee right',
  'Choose a program and type the fee, sign-ups, weeks, facilitator pay share and costs; see the profit per person and per facilitator hour and the fee that meets your profit target.', [
  IL('prog', 'Program', 'prog', 'Stress skills'), I('fee', 'Fee per person', 210, 'money'), I('ppl', 'Sign-ups', 8), I('weeks', 'Weeks', 6), I('share', 'Facilitator pay share of fees', 0.3, 'pct'), I('room', 'Room cost', 144, 'money'),
  I('mat', 'Materials', 60, 'money'), I('mkt', 'Marketing', 90, 'money')], [
  O('Revenue', 'money', '{in:fee}*{in:ppl}'), O('Facilitator pay', 'money', '{in:fee}*{in:ppl}*{in:share}'), O('Room, materials and marketing', 'money', '{in:room}+{in:mat}+{in:mkt}'),
  O('Profit', 'money', '{in:fee}*{in:ppl}*(1-{in:share})-{in:room}-{in:mat}-{in:mkt}'), O('Profit per person', 'money', '({in:fee}*{in:ppl}*(1-{in:share})-{in:room}-{in:mat}-{in:mkt})/{in:ppl}'),
  O('Profit per facilitator hour', 'money', '({in:fee}*{in:ppl}*(1-{in:share})-{in:room}-{in:mat}-{in:mkt})/({in:weeks}*{set:meeting_hours})'),
  O('Profit share of fees, %', 'pct', '({in:fee}*{in:ppl}*(1-{in:share})-{in:room}-{in:mat}-{in:mkt})/({in:fee}*{in:ppl})'), O('Wanted profit share', 'pct', '{set:group_margin_target}'),
  O('Fee that meets the profit target', 'money', 'IFERROR(ROUNDUP(({in:room}+{in:mat}+{in:mkt})/({in:ppl}*(1-{in:share}-{set:group_margin_target}))/5,0)*5,0)'),
  O('Your profit per person, this program', 'money', 'IFERROR(SUMIFS({range:groups.profit},{range:groups.program},{in:prog},{range:groups.counted},1)/SUMIFS({range:groups.signups},{range:groups.program},{in:prog},{range:groups.counted},1),0)'),
  O('Verdict', 'text', 'IF({in:fee}*{in:ppl}*(1-{in:share})-{in:room}-{in:mat}-{in:mkt}>={set:group_margin_target}*{in:fee}*{in:ppl},%s,%s)' % (vd('Price is right'), vd('Raise the fee')))],
  GR('What if', ('Only 3 sign-ups', {'ppl': 3}), ('Only 5 sign-ups', {'ppl': 5}), ('Fee 150', {'fee': 150}), ('Contract facilitator, 60% pay share', {'share': 0.6}), ('Full group: 10 sign-ups', {'ppl': 10}))),
 TOOL('group_breakeven', 'Group Break-even', 'Group Break-even: sign-ups needed and profit at each step',
  'Type the fixed costs, fee, facilitator pay share, capacity and sign-ups so far; see the break-even sign-ups and the profit at 2, 4, 6, 8 and 10 sign-ups.', [
  I('fixed', 'Fixed costs: room, materials and marketing', 322, 'money'), I('fee', 'Fee per person', 320, 'money'), I('share', 'Facilitator pay share of fees', 0.6, 'pct'), I('cap', 'Capacity (places)', 6), I('ppl', 'Sign-ups so far', 2)], [
  O('Contribution per person after facilitator pay', 'money', '{in:fee}*(1-{in:share})'), O('Break-even sign-ups', 'int', 'ROUNDUP({in:fixed}/({in:fee}*(1-{in:share})),0)'),
  O('Places left above break-even', 'int', '{in:cap}-ROUNDUP({in:fixed}/({in:fee}*(1-{in:share})),0)'), O('Break-even as a share of capacity', 'pct', 'ROUNDUP({in:fixed}/({in:fee}*(1-{in:share})),0)/{in:cap}'),
  O('Profit at 2 sign-ups', 'money', 'MIN(2,{in:cap})*{in:fee}*(1-{in:share})-{in:fixed}'), O('Profit at 4 sign-ups', 'money', 'MIN(4,{in:cap})*{in:fee}*(1-{in:share})-{in:fixed}'),
  O('Profit at 6 sign-ups', 'money', 'MIN(6,{in:cap})*{in:fee}*(1-{in:share})-{in:fixed}'), O('Profit at 8 sign-ups', 'money', 'MIN(8,{in:cap})*{in:fee}*(1-{in:share})-{in:fixed}'),
  O('Profit at 10 sign-ups', 'money', 'MIN(10,{in:cap})*{in:fee}*(1-{in:share})-{in:fixed}'), O('Profit with your sign-ups so far', 'money', '{in:ppl}*{in:fee}*(1-{in:share})-{in:fixed}'),
  O('Sign-ups still needed to break even', 'int', 'MAX(0,ROUNDUP({in:fixed}/({in:fee}*(1-{in:share})),0)-{in:ppl})'),
  O('Verdict', 'text', 'IF({in:ppl}>=ROUNDUP({in:fixed}/({in:fee}*(1-{in:share})),0),%s,%s)' % (vd('Run it'), vd('Wait for sign-ups')))],
  GR('What if', ('Owner-led, no pay share', {'share': 0}), ('3 sign-ups', {'ppl': 3}), ('Lower fee: 240', {'fee': 240}), ('Costs up: 480', {'fixed': 480}), ('Full group: 6 sign-ups', {'ppl': 6}))),
 TOOL('group_fill', 'Group Fill and Attendance', 'Group Fill and Attendance: run or postpone',
  'Type the places, sign-ups, drop-outs, meetings held and the total meetings attended; see the fill rate, the sign-ups needed for the minimum fill, attendance and a verdict.', [
  I('cap', 'Capacity (places)', 10), I('ppl', 'Sign-ups', 8), I('drop', 'Drop-outs', 1), I('meets', 'Meetings held so far', 3), I('attended', 'Meetings attended, all people together', 20)], [
  O('Fill rate', 'pct', '{in:ppl}/{in:cap}'), O('Wanted minimum fill', 'pct', '{set:min_group_fill}'), O('Sign-ups needed for the minimum fill', 'int', 'ROUNDUP({in:cap}*{set:min_group_fill},0)'),
  O('Places left', 'int', '{in:cap}-{in:ppl}'), O('Drop-out rate', 'pct', '{in:drop}/{in:ppl}'), O('People still coming', 'int', '{in:ppl}-{in:drop}'),
  O('Attendance at meetings held', 'pct', '{in:attended}/({in:ppl}*{in:meets})'), O('Wanted attendance', 'pct', '{set:min_attendance}'),
  O('Attendance check', 'text', 'IF({in:attended}/({in:ppl}*{in:meets})>={set:min_attendance},%s,%s)' % (ck('Attendance at target'), ck('Attendance low'))),
  O('Your own attendance, all groups held', 'pct', 'SUM({range:attendance.attended})/SUM({range:attendance.expected})'),
  O('Verdict', 'text', 'IF({in:ppl}/{in:cap}>={set:min_group_fill},%s,%s)' % (vd('Run it'), vd('Postpone')))],
  GR('What if', ('Only 5 sign-ups', {'ppl': 5}), ('Full: 10 sign-ups', {'ppl': 10}), ('3 drop-outs', {'drop': 3}), ('Low attendance: 12 attended', {'attended': 12}), ('Small group: 6 places, 4 sign-ups', {'cap': 6, 'ppl': 4}))),
 TOOL('group_case', 'New Group Business Case', 'New Group Business Case: start the group or wait',
  'Type the people interested, the expected sign-up share, fee, weeks, costs, runs a year and a scenario (1 Base, 2 Best, 3 Worst); see the profit per run and per year, the sign-ups needed and a verdict.', [
  I('people', 'People interested', 14), I('share', 'Expected sign-up share of those interested', 0.55, 'pct'), I('cap', 'Capacity (places)', 10), I('fee', 'Fee per person', 240, 'money'), I('weeks', 'Weeks', 8),
  I('pay', 'Facilitator pay share of fees', 0.3, 'pct'), I('mat', 'Materials', 60, 'money'), I('mkt', 'Marketing', 90, 'money'), I('runs', 'Runs a year', 3), I('sc', 'Scenario: 1 Base, 2 Best, 3 Worst', 1)], [
  O('Expected sign-ups', 'int', 'MIN({in:cap},ROUND({in:people}*{in:share}*CHOOSE({in:sc},1,1.25,0.7),0))'), O('Expected fill rate', 'pct', 'MIN({in:cap},ROUND({in:people}*{in:share}*CHOOSE({in:sc},1,1.25,0.7),0))/{in:cap}'),
  O('Revenue per run', 'money', 'MIN({in:cap},ROUND({in:people}*{in:share}*CHOOSE({in:sc},1,1.25,0.7),0))*{in:fee}'),
  O('Room cost per run', 'money', '{in:weeks}*{set:meeting_hours}*{set:room_cost_hour}'),
  O('Profit per run', 'money', 'MIN({in:cap},ROUND({in:people}*{in:share}*CHOOSE({in:sc},1,1.25,0.7),0))*{in:fee}*(1-{in:pay})-{in:weeks}*{set:meeting_hours}*{set:room_cost_hour}-{in:mat}-{in:mkt}'),
  O('Profit per year', 'money', '{in:runs}*(MIN({in:cap},ROUND({in:people}*{in:share}*CHOOSE({in:sc},1,1.25,0.7),0))*{in:fee}*(1-{in:pay})-{in:weeks}*{set:meeting_hours}*{set:room_cost_hour}-{in:mat}-{in:mkt})'),
  O('Profit per facilitator hour', 'money', '(MIN({in:cap},ROUND({in:people}*{in:share}*CHOOSE({in:sc},1,1.25,0.7),0))*{in:fee}*(1-{in:pay})-{in:weeks}*{set:meeting_hours}*{set:room_cost_hour}-{in:mat}-{in:mkt})/({in:weeks}*{set:meeting_hours})'),
  O('Break-even sign-ups', 'int', 'ROUNDUP(({in:weeks}*{set:meeting_hours}*{set:room_cost_hour}+{in:mat}+{in:mkt})/({in:fee}*(1-{in:pay})),0)'),
  O('People interested needed for the minimum fill', 'int', 'ROUNDUP({in:cap}*{set:min_group_fill}/{in:share},0)'),
  O('Your own average profit per completed or running group', 'money', 'IFERROR(SUMIFS({range:groups.profit},{range:groups.counted},1)/SUMIFS({range:groups.counted},{range:groups.counted},1),0)'),
  O('Verdict', 'text', 'IF(AND(MIN({in:cap},ROUND({in:people}*{in:share}*CHOOSE({in:sc},1,1.25,0.7),0))/{in:cap}>={set:min_group_fill},MIN({in:cap},ROUND({in:people}*{in:share}*CHOOSE({in:sc},1,1.25,0.7),0))*{in:fee}*(1-{in:pay})>{in:weeks}*{set:meeting_hours}*{set:room_cost_hour}+{in:mat}+{in:mkt}),%s,%s)' % (vd('Run it'), vd('Wait for sign-ups')))],
  GR('What if', ('Worst scenario', {'sc': 3}), ('Best scenario', {'sc': 2}), ('Only 8 interested', {'people': 8}), ('Fee 180', {'fee': 180}), ('Two runs a year', {'runs': 2}))),
 TOOL('interest_start', 'Interest to Start Date', 'Interest to Start Date: when to announce the group',
  'Choose a program and type the people on the interest list, capacity, minimum fill, earliest start, weekday, weeks and closure weeks; see the meeting dates, the last meeting and when to announce.', [
  IL('prog', 'Program', 'prog', 'Parenting skills'), I('list', 'People on the interest list', 7), I('cap', 'Capacity (places)', 10), I('minfill', 'Minimum fill', 0.6, 'pct'), I('start', 'Earliest start date', 'today+21', 'date'),
  IL('wd', 'Weekday of the group', 'wday', 'Wednesday'), I('weeks', 'Weeks in the program', 8), I('closure', 'Closure weeks inside the run', 1)], [
  O('People needed for the minimum fill', 'int', 'ROUNDUP({in:cap}*{in:minfill},0)'), O('People still needed', 'int', 'MAX(0,ROUNDUP({in:cap}*{in:minfill},0)-{in:list})'),
  O('First meeting date', 'date', NEXTWD('{in:start}', '{in:wd}')), O('Second meeting date', 'date', NEXTWD('{in:start}', '{in:wd}') + '+7'), O('Third meeting date', 'date', NEXTWD('{in:start}', '{in:wd}') + '+14'),
  O('Last meeting date', 'date', NEXTWD('{in:start}', '{in:wd}') + '+7*({in:weeks}-1+{in:closure})'), O('Announce the start date by', 'date', NEXTWD('{in:start}', '{in:wd}') + '-21'),
  O('Waiting on your interest list for this program, now', 'int', 'COUNTIFS({range:interest.program},{in:prog},{range:interest.signed_up},%s)' % NO),
  O('Next planned group of this program in your data', 'date', 'IF(%s>=99999,"",%s)' % (NEXTPROG('{in:prog}'), NEXTPROG('{in:prog}'))),
  O('Verdict', 'text', 'IF({in:list}>=ROUNDUP({in:cap}*{in:minfill},0),%s,%s)' % (vd('Announce the start date'), vd('Keep collecting interest')))],
  GR('What if', ('Only 4 on the list', {'list': 4}), ('Full list: 10 people', {'list': 10}), ('Saturday group', {'wd': '=' + tok('wday', 'Saturday')}), ('No closure week', {'closure': 0}), ('Short program: 4 weeks', {'weeks': 4}))),
 TOOL('website_conversion', 'Website Enquiry Conversion', 'Website Enquiry Conversion against your own history',
  'Type the visits, enquiry forms and bookings for a month; see the conversion at each step against your last 3 months and the same month last year, with a verdict.', [
  I('visits', 'Website visits', 330), I('forms', 'Enquiry forms', 11), I('book', 'Bookings', 6)], [
  O('Visits to enquiry form, %', 'pct', '{in:forms}/{in:visits}'), O('Enquiry forms to booking, %', 'pct', '{in:book}/{in:forms}'), O('Visits to booking, %', 'pct', '{in:book}/{in:visits}'), O('Visits needed for one booking', 'int', 'ROUNDUP({in:visits}/{in:book},0)'),
  O('Your last 3 months: visits to form, %', 'pct', 'IFERROR(SUMIFS({range:website.enquiry_forms},{range:website.month},">="&%s,{range:website.month},"<"&%s)/SUMIFS({range:website.visits},{range:website.month},">="&%s,{range:website.month},"<"&%s),0)' % (M3, M0, M3, M0)),
  O('Your last 3 months: forms to booking, %', 'pct', 'IFERROR(SUMIFS({range:website.bookings},{range:website.month},">="&%s,{range:website.month},"<"&%s)/SUMIFS({range:website.enquiry_forms},{range:website.month},">="&%s,{range:website.month},"<"&%s),0)' % (M3, M0, M3, M0)),
  O('Same month last year: visits to form, %', 'pct', 'IFERROR(SUMIFS({range:website.enquiry_forms},{range:website.month},DATE(YEAR({today})-1,MONTH({today}),1))/SUMIFS({range:website.visits},{range:website.month},DATE(YEAR({today})-1,MONTH({today}),1)),0)'),
  O('Change in visits to form against your last 3 months, points', 'pct', '{in:forms}/{in:visits}-IFERROR(SUMIFS({range:website.enquiry_forms},{range:website.month},">="&%s,{range:website.month},"<"&%s)/SUMIFS({range:website.visits},{range:website.month},">="&%s,{range:website.month},"<"&%s),0)' % (M3, M0, M3, M0)),
  O('Verdict', 'text', 'IF({in:forms}/{in:visits}>=IFERROR(SUMIFS({range:website.enquiry_forms},{range:website.month},">="&%s,{range:website.month},"<"&%s)/SUMIFS({range:website.visits},{range:website.month},">="&%s,{range:website.month},"<"&%s),0),%s,%s)' % (M3, M0, M3, M0, vd('Improving'), vd('Falling')))],
  GR('What if', ('Fewer forms: 6', {'forms': 6}), ('More visits: 600', {'visits': 600}), ('More bookings: 9', {'book': 9}), ('Poor month: 250 visits, 5 forms', {'visits': 250, 'forms': 5, 'book': 2}))),
 TOOL('feedback_summary', 'Feedback Summary', 'Feedback Summary against your history',
  'Type the answers in a batch, their average score and how many would recommend; see the recommend share, the gap to your wanted score, your own last 90 days and your weakest topic.', [
  I('ppl', 'Survey answers in the batch', 24), I('avg', 'Average score of the batch (1 to 10)', 8.6, 'num'), I('rec', 'Would recommend (count)', 20)], [
  O('Would recommend share', 'pct', '{in:rec}/{in:ppl}'), O('Gap to the wanted score', 'num', '{in:avg}-{set:target_rating}'), O('Gap to the wanted recommend share', 'pct', '{in:rec}/{in:ppl}-{set:target_recommend}'),
  O('Your average score, last 90 days', 'num', 'IFERROR(AVERAGEIFS({range:feedback.rating},{range:feedback.date},">="&({today}-90),{range:feedback.date},"<="&{today}),0)'),
  O('Your average score, the 90 days before', 'num', 'IFERROR(AVERAGEIFS({range:feedback.rating},{range:feedback.date},">="&({today}-180),{range:feedback.date},"<"&({today}-90)),0)'),
  O('Your recommend share, last 90 days', 'pct', 'IFERROR(COUNTIFS({range:feedback.would_recommend},%s,{range:feedback.date},">="&({today}-90),{range:feedback.date},"<="&{today})/COUNTIFS({range:feedback.date},">="&({today}-90),{range:feedback.date},"<="&{today}),0)' % YES),
  O('Weakest topic, last 12 months', 'text', 'INDEX({range:feedback.topic},MATCH(MIN({range:feedback.topic_avg_12m}),{range:feedback.topic_avg_12m},0))'),
  O('Average score of the weakest topic', 'num', 'MIN({range:feedback.topic_avg_12m})'),
  O('Verdict', 'text', 'IF({in:avg}>=IFERROR(AVERAGEIFS({range:feedback.rating},{range:feedback.date},">="&({today}-90),{range:feedback.date},"<="&{today}),0),%s,%s)' % (vd('Improving'), vd('Falling')))],
  GR('What if', ('Lower batch score: 7.2', {'avg': 7.2}), ('Fewer would recommend: 12', {'rec': 12}), ('Large batch: 60 answers', {'ppl': 60, 'rec': 50}), ('High score: 9.4', {'avg': 9.4}))),
 TOOL('enquiry_target', 'Enquiry Target Planner', 'Enquiry Target Planner',
  'Type the extra sessions wanted a month, sessions a new client has, the booked share and the enquiries so far this month; see the enquiries needed, the pace so far and your own history.', [
  I('extra', 'Extra sessions wanted a month', 60), I('spm', 'Sessions a new client has in a month', 2, 'num'), I('share', 'Booked share of enquiries', 0.5, 'pct'), I('sofar', 'Enquiries so far this month', 36)], [
  O('New clients needed', 'num', '{in:extra}/{in:spm}'), O('Enquiries needed in the month', 'num', '{in:extra}/{in:spm}/{in:share}'), O('Enquiries still needed', 'num', 'MAX(0,{in:extra}/{in:spm}/{in:share}-{in:sofar})'),
  O('Enquiries needed by today to be on pace', 'num', '{in:extra}/{in:spm}/{in:share}*DAY({today})/DAY(DATE(YEAR({today}),MONTH({today})+1,0))'),
  O('Enquiries needed per day for the rest of the month', 'num', 'MAX(0,{in:extra}/{in:spm}/{in:share}-{in:sofar})/(DAY(DATE(YEAR({today}),MONTH({today})+1,0))-DAY({today})+1)'),
  O('Your enquiries last month, all sources', 'int', 'SUMIFS({range:sourcemonths.enquiries},{range:sourcemonths.month},DATE(YEAR({today}),MONTH({today})-1,1))'),
  O('Your average enquiries a month, last 3 months', 'num', 'SUMIFS({range:sourcemonths.enquiries},{range:sourcemonths.month},">="&%s,{range:sourcemonths.month},"<"&%s)/3' % (M3, M0)),
  O('Same month last year, all sources', 'int', 'SUMIFS({range:sourcemonths.enquiries},{range:sourcemonths.month},DATE(YEAR({today})-1,MONTH({today}),1))'),
  O('Verdict', 'text', 'IF({in:sofar}>={in:extra}/{in:spm}/{in:share}*DAY({today})/DAY(DATE(YEAR({today}),MONTH({today})+1,0)),%s,%s)' % (vd('On track'), vd('Need more enquiries')))],
  GR('What if', ('Only 20 enquiries so far', {'sofar': 20}), ('Wanted 100 extra sessions', {'extra': 100}), ('Booked share 35%', {'share': 0.35}), ('Clients come weekly: 4 sessions', {'spm': 4}))),
 TOOL('newsletter_reach', 'Newsletter Reach', 'Newsletter Reach: send or not worth the time',
  'Type the people on the list, the reply rate, the share of replies that become enquiries, the booked share, your minutes and the value of a client; see the enquiries and clients expected and a verdict.', [
  I('list', 'People on the newsletter list', 480), I('reply', 'Reply rate', 0.045, 'pct'), I('conv', 'Share of replies that become enquiries', 0.15, 'pct'), I('share', 'Booked share of enquiries', 0.5, 'pct'),
  I('mins', 'Minutes to write and send', 90), I('value', 'Margin value of one client', 588, 'money')], [
  O('Replies expected', 'num', '{in:list}*{in:reply}'), O('Enquiries expected', 'num', '{in:list}*{in:reply}*{in:conv}'), O('Clients expected', 'num', '{in:list}*{in:reply}*{in:conv}*{in:share}'),
  O('Expected value of those clients', 'money', '{in:list}*{in:reply}*{in:conv}*{in:share}*{in:value}'), O('Time cost at the coordinator\'s hourly rate', 'money', '{in:mins}/60*INDEX({range:team.hourly_rate},7)'),
  O('Net value of one issue', 'money', '{in:list}*{in:reply}*{in:conv}*{in:share}*{in:value}-{in:mins}/60*INDEX({range:team.hourly_rate},7)'),
  O('Your own reply rate, all issues', 'pct', 'SUM({range:newsletter.replies})/SUM({range:newsletter.sent_to})'), O('Your own enquiries per 1,000 sent', 'num', 'SUM({range:newsletter.enquiries})*1000/SUM({range:newsletter.sent_to})'),
  O('Your own enquiries per issue', 'num', 'SUM({range:newsletter.enquiries})/COUNTA({range:newsletter.issue_id})'),
  O('Verdict', 'text', 'IF({in:list}*{in:reply}*{in:conv}*{in:share}*{in:value}>{in:mins}/60*INDEX({range:team.hourly_rate},7),%s,%s)' % (vd('Send'), vd('Not worth the time')))],
  GR('What if', ('Small list: 120 people', {'list': 120}), ('Low reply rate: 1%', {'reply': 0.01}), ('Quick issue: 30 minutes', {'mins': 30}), ('Few become enquiries: 3%', {'conv': 0.03}))),
 TOOL('source_forecast', 'Source Forecast', 'Source Forecast for the next 3 months',
  'Choose a source and type its last 6 months of enquiries (oldest first), a trend factor, a scenario, the booked share and the clients a month you can take; see 3 months and a verdict.', [
  IL('src', 'Referral source', 'src', 'Doctor referral')] + [I('m%d' % (i + 1), 'Enquiries, month %d of the last 6' % (i + 1), d6[i]) for i in range(6)] + [
  I('trend', 'Trend factor a month', 1.05, 'num'), I('sc', 'Scenario: 1 Base, 2 Best, 3 Worst', 1), I('share', 'Booked share of enquiries', 0.5, 'pct'), I('cap', 'New clients a month the practice can take', 40)], [
  O('Average of the last 3 months', 'num', F18), O('Average of the 3 months before', 'num', P18), O('Trend in your own 6 months', 'num', 'MAX(0.85,MIN(1.15,%s/%s))' % (F18, P18)),
  O('Enquiries, next month', 'int', FC18(1)), O('Enquiries, month 2', 'int', FC18(2)), O('Enquiries, month 3', 'int', FC18(3)), O('Enquiries, next 3 months', 'int', '%s+%s+%s' % (FC18(1), FC18(2), FC18(3))),
  O('Booked clients a month by month 3 from this source', 'num', '%s*{in:share}' % FC18(3)),
  O('Your last 3 months of this source in your data', 'int', SM('enquiries', '{in:src}', M3, M0)),
  O('All sources: new clients a month, last 3 months', 'num', ALLB3), O('All sources: clients in month 3 with this forecast', 'num', '%s+%s' % (ALLB3, EXTRA18)),
  O('Verdict', 'text', 'IF(%s+%s>{in:cap},%s,IF(%s+%s>0.9*{in:cap},%s,%s))' % (ALLB3, EXTRA18, vd('Waiting list risk'), ALLB3, EXTRA18, vd('Capacity needed'), vd('Enough capacity')))],
  GR('What if', ('Best scenario', {'sc': 2}), ('Worst scenario', {'sc': 3}), ('Falling trend: 0.9', {'trend': 0.9}), ('Strong trend: 1.15', {'trend': 1.15}), ('Capacity 30 a month', {'cap': 30}))),
]
assert len(tools) == 18, len(tools)
