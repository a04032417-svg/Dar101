"""Home care agency suite part 1: the 18 decision tools (each ends with a verdict and a what-if table)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc1_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
YES = '{list:yesno.yes}'
B, TM = '{set:payroll_burden}', '{set:target_margin}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def D90(c): return '{range:%s},">="&({today}-90),{range:%s},"<="&{today}' % (c, c)
def RC(col, svc, band): return 'SUMIFS({range:rate_card.%s},{range:rate_card.service},%s,{range:rate_card.band},%s)' % (col, svc, band)
def BT(b): return tok('band', b)
SH = lambda p: 'SUMIFS({range:payers.rate_share},{range:payers.payer},%s)' % p
VERDICT_OK, VERDICT_BAD = None, None

# ---------------- 1 can I take this client
SKILL = ['sk_companion', 'sk_personal', 'sk_home', 'sk_respite', 'sk_overnight', 'sk_livein']
SK1 = '(' + '+'.join('({in:svc}=%s)*({range:capacity.%s}=%s)' % (tok('svc', s), c, YES) for s, c in zip(SERVICES, SKILL)) + ')'
CAP1 = '(({range:capacity.hours_limit}<{set:overtime_hours})*{range:capacity.hours_limit}+({range:capacity.hours_limit}>={set:overtime_hours})*{set:overtime_hours})'
FREE1 = '(%s-{range:capacity.hours_next_week})' % CAP1
WK1 = '({range:capacity.working}=%s)*%s' % (YES, SK1)
EL1 = '(%s*(%s>={in:hrs}))' % (WK1, FREE1)
SC1 = '(1+3*({range:capacity.area}={in:area})+2*((({range:capacity.language_1}={in:lang})+({range:capacity.language_2}={in:lang}))>0))'
KEY1 = 'SUMPRODUCT(MAX(%s*(%s*1000+(999-{range:capacity.no}))))' % (EL1, SC1)
NO1 = '(999-MOD(%s,1000))' % KEY1
PAY1 = 'IF(%s=0,%s,INDEX({range:capacity.pay_rate},%s))' % (KEY1, RC('pay_rate', '{in:svc}', '{in:band}'), NO1)
COST1 = '(%s*(1+%s)*(1+{in:trav}/60/({in:hrs}/{in:days}))+{in:km}*{set:mileage_rate}/({in:hrs}/{in:days}))' % (PAY1, B)
# ---------------- 2 minimum rate
def PM(svc, band): return '(%s/%s)' % (RC('pay_rate', svc, BT(band)), RC('pay_rate', svc, BT('Weekday')))
WP2 = '({in:pay}*((1-{in:se}-{in:sw}-{in:sn})+{in:se}*%s+{in:sw}*%s+{in:sn}*%s))' % (PM('{in:svc}', 'Evening'), PM('{in:svc}', 'Weekend'), PM('{in:svc}', 'Night'))
COST2 = '(%s*(1+%s)*(1+{in:trav}/60/{in:vis})+{in:km}*{in:mil}/{in:vis})' % (WP2, B)
BILL2 = '((1-{in:se}-{in:sw}-{in:sn})*%s+{in:se}*%s+{in:sw}*%s+{in:sn}*%s)' % (RC('bill_rate', '{in:svc}', BT('Weekday')), RC('bill_rate', '{in:svc}', BT('Evening')), RC('bill_rate', '{in:svc}', BT('Weekend')), RC('bill_rate', '{in:svc}', BT('Night')))
# ---------------- 3 card checker
def M3(b): return '(1-(%s+{in:payup})*(1+%s)/(%s*(1+{in:raise})))' % (RC('pay_rate', '{in:svc}', BT(b)), B, RC('bill_rate', '{in:svc}', BT(b)))
M3ALL = '(1-({range:rate_card.pay_rate}+{in:payup})*(1+%s)/({range:rate_card.bill_rate}*(1+{in:raise})+({range:rate_card.bill_rate}=0)))' % B
SV3 = '({range:rate_card.service}={in:svc})'
# ---------------- 4 card builder
def BR4(b): return 'ROUND({in:base}*%s,2)' % {'Weekday': '1', 'Evening': '(1+{in:eve})', 'Weekend': '(1+{in:wkd})', 'Night': '(1+{in:ngt})', 'Holiday': '{in:hol}'}[b]
def PY4(b): return '({in:pay}*%s)' % {'Weekday': '1', 'Evening': '(1+{in:pe})', 'Weekend': '(1+{in:pw})', 'Night': '(1+{in:pn})', 'Holiday': '{in:ph}'}[b]
def MG4(b): return '(1-%s*(1+%s)/%s)' % (PY4(b), B, BR4(b))
MULT4 = {'Weekday': '1', 'Evening': '(1+{in:eve})', 'Weekend': '(1+{in:wkd})', 'Night': '(1+{in:ngt})', 'Holiday': '{in:hol}'}
# ---------------- 5 quote builder
HRS5 = [('wk', 'Weekday'), ('ev', 'Evening'), ('we', 'Weekend'), ('nt', 'Night')]
WK5 = '(%s)' % '+'.join('{in:h_%s}*%s' % (k, RC('bill_rate', '{in:svc}', BT(b))) for k, b in HRS5)
PAYC5 = '(%s)' % '+'.join('{in:h_%s}*%s' % (k, RC('pay_rate', '{in:svc}', BT(b))) for k, b in HRS5)
HT5 = '({in:h_wk}+{in:h_ev}+{in:h_we}+{in:h_nt})'
# ---------------- 10 source value
M12 = 'DATE(YEAR({today}),MONTH({today})-11,1)'
def V10(src): return 'IFERROR(100*SUMIFS({range:sources.hours_started},{range:sources.source},%s,{range:sources.month},">="&%s)/SUMIFS({range:sources.cost},{range:sources.source},%s,{range:sources.month},">="&%s),0)' % (src, M12, src, M12)
def S10(col, src='{in:src}'): return 'SUMIFS({range:sources.%s},{range:sources.source},%s,{range:sources.month},">="&%s)' % (col, src, M12)
RANK10 = 'INDEX({range:sources.rank_12m},MATCH({in:src},{range:sources.source},0))'
VSEL10 = 'INDEX({range:sources.value_12m},MATCH({in:src},{range:sources.source},0))'
# ---------------- 14 forecast
L3 = 'SUMIFS({range:funnel.enquiries},{range:funnel.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:funnel.month},"<"&%s)/3' % MS
P3 = 'SUMIFS({range:funnel.enquiries},{range:funnel.month},">="&DATE(YEAR({today}),MONTH({today})-6,1),{range:funnel.month},"<"&DATE(YEAR({today}),MONTH({today})-3,1))/3'
TR14 = 'MAX(0.85,MIN(1.15,(%s)/(%s)))' % (L3, P3)
SCN14 = 'IF({in:sc}=%s,1.15,IF({in:sc}=%s,0.85,1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
def FC14(k): return '(%s)*(1+(%s-1)*%d/3)*%s' % (L3, TR14, k, SCN14)
AVGH = 'IFERROR(SUM({range:starts.hours_added})/SUM({range:starts.clients_started}),0)'

tools = [
 TOOL('can_take', 'Can I Take This Client', 'Can I take this client?',
  'Type the hours, area, language, service and quoted rate; see who could cover without overtime, the best match, the margin and the lowest rate that reaches the target.', [
  IL('svc', 'Service', 'svc', 'Personal care help'), IL('area', 'Client area', 'area', 'Riverside'), I('hrs', 'Hours a week', 20, 'num'), I('days', 'Days a week', 4), IN('lang', 'Language wanted', 'text', 'English'),
  IL('band', 'Main time band', 'band', 'Weekday'), I('rate', 'Quoted bill rate per hour', 37, 'money'), I('trav', 'Paid travel minutes per visit', 12), I('km', 'Km driven per visit', 6, 'num')], [
  O('Caregivers who could cover all the hours without overtime', 'int', 'SUMPRODUCT(%s)' % EL1),
  O('Skilled caregivers with some free hours next week', 'int', 'SUMPRODUCT(%s*(%s>0))' % (WK1, FREE1)),
  O('Free hours next week across skilled caregivers', 'num', 'SUMPRODUCT(%s*(%s>0)*%s)' % (WK1, FREE1, FREE1)),
  O('Best match', 'text', 'IF(%s=0,%s,INDEX({range:capacity.caregiver},%s))' % (KEY1, vd('No free caregiver'), NO1)),
  O('Match points of the best caregiver (area 3, language 2)', 'int', 'IF(%s=0,0,INT(%s/1000)-1)' % (KEY1, KEY1)),
  O('Pay rate used per hour', 'money', PAY1), O('Average visit hours', 'num', '{in:hrs}/{in:days}'),
  O('Loaded cost per client hour (pay, burden, travel, mileage)', 'money', COST1), O('Margin per hour at the quoted rate', 'money', '{in:rate}-%s' % COST1),
  O('Margin share at the quoted rate', 'pct', '1-%s/{in:rate}' % COST1), O('Weekly margin', 'money', '({in:rate}-%s)*{in:hrs}' % COST1),
  O('Lowest rate that reaches the target margin', 'money', '%s/(1-%s)' % (COST1, TM)), O('Rate card rate for this service and band', 'money', RC('bill_rate', '{in:svc}', '{in:band}')),
  O('Verdict', 'text', 'IF(SUMPRODUCT(%s)=0,%s,IF(1-%s/{in:rate}>=%s,%s,%s))' % (EL1, vd('Decline'), COST1, TM, vd('Accept'), vd('Quote higher')))],
  GR('What if', ('Quote higher: 41', {'rate': 41}), ('Quote lower: 33', {'rate': 33}), ('Big case: 45 hours a week', {'hrs': 45, 'days': 6}), ('Overnight care in South Valley', {'svc': '=' + tok('svc', 'Overnight care'), 'area': '=' + tok('area', 'South Valley'), 'rate': 38, 'hrs': 30, 'days': 3}))),
 TOOL('min_rate', 'Minimum Rate for Target', 'Minimum rate for the target margin',
  'Type the service, the band mix, caregiver pay, paid travel and mileage; see the lowest bill rate that reaches the target margin and the gap to the rate card.', [
  IL('svc', 'Service', 'svc', 'Companion care'), I('se', 'Share of hours in the evening', 0.2, 'pct'), I('sw', 'Share of hours at the weekend', 0.15, 'pct'), I('sn', 'Share of hours at night', 0.05, 'pct'),
  I('pay', 'Caregiver pay per hour, weekday', 18, 'money'), I('trav', 'Paid travel minutes per visit', 15), I('vis', 'Visit hours', 3, 'num'), I('km', 'Km driven per visit', 6, 'num'), I('mil', 'Mileage rate per km', 0.4, 'money')], [
  O('Weighted pay per hour for this mix', 'money', WP2), O('Loaded cost per client hour (burden, travel, mileage)', 'money', COST2),
  O('Break-even bill rate (0% margin)', 'money', COST2), O('Lowest bill rate for the red margin line', 'money', '%s/(1-{set:margin_red})' % COST2),
  O('Lowest bill rate that reaches the target margin', 'money', '%s/(1-%s)' % (COST2, TM)), O('Rate card rate for this mix', 'money', BILL2),
  O('Gap: rate card minus the lowest rate (negative = too low)', 'money', '%s-%s/(1-%s)' % (BILL2, COST2, TM)), O('Margin share at the rate card', 'pct', '1-%s/%s' % (COST2, BILL2)),
  O('Verdict', 'text', 'IF(%s>=%s/(1-%s),%s,%s)' % (BILL2, COST2, TM, vd('Rate card is enough'), vd('Raise the rate')))],
  GR('What if', ('Pay 21 an hour', {'pay': 21}), ('Long travel: 30 minutes', {'trav': 30}), ('Short visits: 1.5 hours', {'vis': 1.5}), ('Live-in day', {'svc': '=' + tok('svc', 'Live-in day'), 'pay': 14.5, 'vis': 12, 'trav': 0, 'km': 0}), ('Mostly evenings and weekends', {'se': 0.4, 'sw': 0.3}))),
 TOOL('card_check', 'Rate Card Margin Checker', 'Rate card margin checker by time band',
  'Pick a service and type a possible rate rise and caregiver pay rise; see the margin share of each time band on your rate card, how many bands fall below the target and whether to publish or raise.', [
  IL('svc', 'Service', 'svc', 'Personal care help'), I('raise', 'Rise in the bill rates', 0.03, 'pct'), I('payup', 'Rise in caregiver pay per hour', 0.5, 'money')], [
  O('Weekday margin share', 'pct', M3('Weekday')), O('Evening margin share', 'pct', M3('Evening')), O('Weekend margin share', 'pct', M3('Weekend')), O('Night margin share', 'pct', M3('Night')), O('Holiday margin share', 'pct', M3('Holiday')),
  O('Lowest margin share for the service', 'pct', 'SUMPRODUCT(MIN(%s*%s+(1-%s)*9))' % (SV3, M3ALL, SV3)),
  O('Bands below the target for this service', 'int', 'SUMPRODUCT(%s*(%s<%s))' % (SV3, M3ALL, TM)), O('Bands below the target on the whole card', 'int', 'SUMPRODUCT((%s<%s)*({range:rate_card.bill_rate}>0))' % (M3ALL, TM)),
  O('Verdict', 'text', 'IF(SUMPRODUCT(%s*(%s<%s))=0,%s,%s)' % (SV3, M3ALL, TM, vd('Publish'), vd('Raise')))],
  GR('What if', ('No rise', {'raise': 0, 'payup': 0}), ('Pay rise only: 1.50', {'raise': 0, 'payup': 1.5}), ('Bill rise 6%', {'raise': 0.06}), ('Live-in day', {'svc': '=' + tok('svc', 'Live-in day')}), ('Overnight care', {'svc': '=' + tok('svc', 'Overnight care')}))),
 TOOL('card_builder', 'Rate Card Builder', 'Rate card builder: five time band rates and their margin',
  'Type the weekday rate, the uplifts, the holiday multiplier and the caregiver pay for each band; see the five bill rates, the margin of each band and which bands to publish or raise.', [
  I('base', 'Weekday bill rate per hour', 34, 'money'), I('eve', 'Evening uplift', 0.06, 'pct'), I('wkd', 'Weekend uplift', 0.12, 'pct'), I('ngt', 'Night uplift', 0.18, 'pct'), I('hol', 'Holiday multiplier', 1.5, 'num'),
  I('pay', 'Weekday caregiver pay per hour', 17.5, 'money'), I('pe', 'Evening pay uplift', 0.04, 'pct'), I('pw', 'Weekend pay uplift', 0.05, 'pct'), I('pn', 'Night pay uplift', 0.1, 'pct'), I('ph', 'Holiday pay multiplier', 1.5, 'num')], [
  O('Weekday bill rate', 'money', BR4('Weekday')), O('Evening bill rate', 'money', BR4('Evening')), O('Weekend bill rate', 'money', BR4('Weekend')), O('Night bill rate', 'money', BR4('Night')), O('Holiday bill rate', 'money', BR4('Holiday')),
  O('Weekday margin share', 'pct', MG4('Weekday')), O('Evening margin share', 'pct', MG4('Evening')), O('Weekend margin share', 'pct', MG4('Weekend')), O('Night margin share', 'pct', MG4('Night')), O('Holiday margin share', 'pct', MG4('Holiday')),
  O('Weekday verdict', 'text', 'IF(%s>=%s,%s,%s)' % (MG4('Weekday'), TM, vd('Publish'), vd('Raise'))), O('Evening verdict', 'text', 'IF(%s>=%s,%s,%s)' % (MG4('Evening'), TM, vd('Publish'), vd('Raise'))),
  O('Weekend verdict', 'text', 'IF(%s>=%s,%s,%s)' % (MG4('Weekend'), TM, vd('Publish'), vd('Raise'))), O('Night verdict', 'text', 'IF(%s>=%s,%s,%s)' % (MG4('Night'), TM, vd('Publish'), vd('Raise'))),
  O('Holiday verdict', 'text', 'IF(%s>=%s,%s,%s)' % (MG4('Holiday'), TM, vd('Publish'), vd('Raise'))),
  O('Lowest weekday rate at which every band meets the target', 'money', 'MAX(%s)/(1-%s)' % (','.join('%s*(1+%s)/%s' % (PY4(b), B, MULT4[b]) for b in BANDS), TM))],
  GR('What if', ('Weekday rate 38', {'base': 38}), ('Bigger weekend uplift 15%', {'wkd': 0.15}), ('Holiday 1.75 times', {'hol': 1.75}), ('Pay 20 an hour', {'pay': 20}))),
 TOOL('quote_builder', 'Quote Builder', 'Quote builder: weekly cost, monthly estimate and deposit',
  'Pick the service and payer and type weekly hours by band; see the weekly cost, monthly estimate, holiday allowance, deposit and margin check.', [
  IL('svc', 'Service', 'svc', 'Companion care'), IL('payer', 'Payer', 'payer', 'Private pay'), I('h_wk', 'Weekday hours a week', 16, 'num'), I('h_ev', 'Evening hours a week', 4, 'num'), I('h_we', 'Weekend hours a week', 6, 'num'),
  I('h_nt', 'Night hours a week', 0, 'num'), I('hol', 'Holiday hours in a year', 16, 'num')], [
  O('Hours a week', 'num', HT5), O('Weekly cost to the client', 'money', '%s*%s' % (SH('{in:payer}'), WK5)), O('Average rate per hour', 'money', '%s*%s/%s' % (SH('{in:payer}'), WK5, HT5)),
  O('Monthly estimate (weekly cost x 52 / 12)', 'money', '%s*%s*52/12' % (SH('{in:payer}'), WK5)),
  O('Holiday allowance per month', 'money', '{in:hol}*(%s-%s)*%s/12' % (RC('bill_rate', '{in:svc}', BT('Holiday')), RC('bill_rate', '{in:svc}', BT('Weekday')), SH('{in:payer}'))),
  O('Deposit to take', 'money', 'IF({in:payer}=%s,%s*%s*{set:deposit_weeks},0)' % (tok('payer', 'Private pay'), SH('{in:payer}'), WK5)), O('Quote valid until', 'date', '{today}+{set:quote_valid_days}'),
  O('Margin share at standard pay', 'pct', '1-%s*(1+%s)/(%s*%s)' % (PAYC5, B, SH('{in:payer}'), WK5)),
  O('Verdict', 'text', 'IF(1-%s*(1+%s)/(%s*%s)>=%s,%s,%s)' % (PAYC5, B, SH('{in:payer}'), WK5, TM, ck('Quote on target'), ck('Quote below target')))],
  GR('What if', ('Care insurer', {'payer': '=' + tok('payer', 'Care insurer')}), ('Third-party payer B', {'payer': '=' + tok('payer', 'Third-party payer B')}), ('Mostly evenings', {'h_wk': 6, 'h_ev': 14}), ('Weekend care', {'h_wk': 4, 'h_we': 16}), ('Personal care help', {'svc': '=' + tok('svc', 'Personal care help')}))),
 TOOL('deposit_size', 'Deposit and Prepayment', 'Deposit and prepayment sizing',
  'Type the hours, rate, weeks held and payer; see the weekly charge, the deposit, how many weeks of hours it covers and how much money would be owed before the first payment arrives.', [
  I('hrs', 'Hours a week', 18, 'num'), I('rate', 'Bill rate per hour', 36, 'money'), I('weeks', 'Weeks of hours held as a deposit', 1), IL('payer', 'Payer', 'payer', 'Private pay')], [
  O('Weekly charge', 'money', '{in:hrs}*{in:rate}'), O('Deposit to hold', 'money', 'IF({in:payer}=%s,{in:hrs}*{in:rate}*{in:weeks},0)' % tok('payer', 'Private pay')),
  O('Weeks of hours covered by the deposit', 'num', 'IF({in:payer}=%s,{in:weeks},0)' % tok('payer', 'Private pay')), O('Usual days to be paid', 'int', 'SUMIFS({range:payers.pay_days},{range:payers.payer},{in:payer})'),
  O('Money owed before the first payment arrives', 'money', '{in:hrs}*{in:rate}*(SUMIFS({range:payers.pay_days},{range:payers.payer},{in:payer})+IF({in:payer}=%s,14,30))/7' % tok('payer', 'Private pay')),
  O('Share of that exposure the deposit covers', 'pct', 'IF({in:payer}=%s,{in:hrs}*{in:rate}*{in:weeks}/({in:hrs}*{in:rate}*(SUMIFS({range:payers.pay_days},{range:payers.payer},{in:payer})+14)/7),0)' % tok('payer', 'Private pay')),
  O('Average deposit of your active clients who paid one', 'money', 'IFERROR(AVERAGEIFS({range:clients.deposit},{range:clients.status},%s,{range:clients.deposit},">0"),0)' % tok('clstatus', 'Active')),
  O('Verdict', 'text', 'IF({in:payer}=%s,%s,%s)' % (tok('payer', 'Private pay'), vd('Take a deposit'), vd('No deposit needed')))],
  GR('What if', ('Two weeks held', {'weeks': 2}), ('Care insurer', {'payer': '=' + tok('payer', 'Care insurer')}), ('Big case: 40 hours', {'hrs': 40}), ('Low rate: 30', {'rate': 30}))),
 TOOL('short_visit', 'Short Visit Surcharge', 'Short-visit surcharge solver',
  'Type the visit length, the minimum visit billed, paid travel and the rates; see the true margin of a short visit and the surcharge or minimum visit that reaches the target.', [
  I('vis', 'Hours the visit lasts', 1, 'num'), I('minv', 'Minimum visit hours billed', 2, 'num'), I('trav', 'Paid travel minutes to the visit', 20), I('km', 'Km driven to the visit', 8, 'num'),
  I('rate', 'Bill rate per hour', 34, 'money'), I('pay', 'Caregiver pay per hour', 17.5, 'money')], [
  O('Hours billed', 'num', 'MAX({in:vis},{in:minv})'), O('Charge for the visit', 'money', 'MAX({in:vis},{in:minv})*{in:rate}'),
  O('Cost of the visit (pay, burden, paid travel, mileage)', 'money', '{in:pay}*(1+%s)*({in:vis}+{in:trav}/60)+{in:km}*{set:mileage_rate}' % B),
  O('Margin of the visit', 'money', 'MAX({in:vis},{in:minv})*{in:rate}-({in:pay}*(1+%s)*({in:vis}+{in:trav}/60)+{in:km}*{set:mileage_rate})' % B),
  O('Margin share of the visit', 'pct', '1-({in:pay}*(1+%s)*({in:vis}+{in:trav}/60)+{in:km}*{set:mileage_rate})/(MAX({in:vis},{in:minv})*{in:rate})' % B),
  O('Margin per hour worked and travelled', 'money', '(MAX({in:vis},{in:minv})*{in:rate}-({in:pay}*(1+%s)*({in:vis}+{in:trav}/60)+{in:km}*{set:mileage_rate}))/({in:vis}+{in:trav}/60)' % B),
  O('Surcharge per visit to reach the target margin', 'money', 'MAX(0,({in:pay}*(1+%s)*({in:vis}+{in:trav}/60)+{in:km}*{set:mileage_rate})/(1-%s)-MAX({in:vis},{in:minv})*{in:rate})' % (B, TM)),
  O('Minimum visit hours that reaches the target', 'num', '({in:pay}*(1+%s)*({in:vis}+{in:trav}/60)+{in:km}*{set:mileage_rate})/(1-%s)/{in:rate}' % (B, TM)),
  O('Verdict', 'text', 'IF(1-({in:pay}*(1+%s)*({in:vis}+{in:trav}/60)+{in:km}*{set:mileage_rate})/(MAX({in:vis},{in:minv})*{in:rate})>=%s,%s,%s)' % (B, TM, vd('Short visit pays'), vd('Add a surcharge')))],
  GR('What if', ('Three-hour visit', {'vis': 3, 'minv': 2}), ('Minimum of 3 hours', {'minv': 3}), ('Long travel: 40 minutes', {'trav': 40}), ('Nearby: 5 minutes', {'trav': 5, 'km': 2}))),
 TOOL('reply_speed', 'Reply Speed Check', 'Reply speed check: enquiries at risk and starts lost',
  'Type your average hours to a first reply, the target and enquiries a week; see the share replied to in time, the enquiries at risk and the starts you would gain from your own start rates.', [
  I('avg', 'Average hours to the first reply', 5.5, 'num'), I('tgt', 'Target hours to the first reply', 4), I('wk', 'Enquiries a week', 8, 'num')], [
  O('Share replied within the target, your last 90 days', 'pct', 'IFERROR(COUNTIFS({range:enquiries.first_reply_hours},"<="&{in:tgt},%s)/COUNTIFS(%s),0)' % (D90('enquiries.received_on'), D90('enquiries.received_on'))),
  O('Share replied within the target at the typed average', 'pct', '1-POWER(2.718281828,-{in:tgt}/{in:avg})'), O('Enquiries a week at risk', 'num', '{in:wk}*POWER(2.718281828,-{in:tgt}/{in:avg})'),
  O('Start rate when replied in time, all your enquiries', 'pct', 'IFERROR(COUNTIFS({range:enquiries.first_reply_hours},"<="&{in:tgt},{range:enquiries.status},%s)/COUNTIFS({range:enquiries.first_reply_hours},"<="&{in:tgt}),0)' % tok('enqst', 'Started')),
  O('Start rate when replied late, all your enquiries', 'pct', 'IFERROR(COUNTIFS({range:enquiries.first_reply_hours},">"&{in:tgt},{range:enquiries.status},%s)/COUNTIFS({range:enquiries.first_reply_hours},">"&{in:tgt}),0)' % tok('enqst', 'Started')),
  O('Extra starts a month if every reply were in time', 'num', 'MAX(0,{in:wk}*4.33*POWER(2.718281828,-{in:tgt}/{in:avg})*(IFERROR(COUNTIFS({range:enquiries.first_reply_hours},"<="&{in:tgt},{range:enquiries.status},%s)/COUNTIFS({range:enquiries.first_reply_hours},"<="&{in:tgt}),0)-IFERROR(COUNTIFS({range:enquiries.first_reply_hours},">"&{in:tgt},{range:enquiries.status},%s)/COUNTIFS({range:enquiries.first_reply_hours},">"&{in:tgt}),0)))' % (tok('enqst', 'Started'), tok('enqst', 'Started'))),
  O('Verdict against the wanted share', 'text', 'IF(1-POWER(2.718281828,-{in:tgt}/{in:avg})>={set:reply_share_target},%s,%s)' % (vd('Reply speed is on target'), vd('Reply faster')))],
  GR('What if', ('Reply in 2 hours on average', {'avg': 2}), ('Slow replies: 10 hours', {'avg': 10}), ('Busy week: 14 enquiries', {'wk': 14}), ('Target of 2 hours', {'tgt': 2}))),
 TOOL('funnel_calc', 'Funnel Conversion Calculator', 'Funnel conversion: weakest step and hours gained',
  'Type the enquiries, assessments, agreements and first visits of a period; see the conversion at each step, the weakest step and the weekly hours gained if it rose by 5 points.', [
  I('enq', 'Enquiries', 60), I('ass', 'Assessments done', 38), I('agr', 'Agreements signed', 26), I('vis', 'First visits', 24)], [
  O('Enquiry to assessment', 'pct', '{in:ass}/{in:enq}'), O('Assessment to agreement', 'pct', '{in:agr}/{in:ass}'), O('Agreement to first visit', 'pct', '{in:vis}/{in:agr}'), O('Enquiry to first visit', 'pct', '{in:vis}/{in:enq}'),
  O('Enquiries lost on the way', 'int', '{in:enq}-{in:vis}'),
  O('Weakest step', 'text', 'IF(MIN({in:ass}/{in:enq},{in:agr}/{in:ass},{in:vis}/{in:agr})={in:ass}/{in:enq},%s,IF(MIN({in:ass}/{in:enq},{in:agr}/{in:ass},{in:vis}/{in:agr})={in:agr}/{in:ass},%s,%s))' % (vd('Weakest: assessment'), vd('Weakest: agreement'), vd('Weakest: first visit'))),
  O('Extra first visits if the weakest step rose 5 points', 'num', '{in:vis}*0.05/MIN({in:ass}/{in:enq},{in:agr}/{in:ass},{in:vis}/{in:agr})'),
  O('Average weekly hours per new client, your own history', 'num', AVGH), O('Weekly hours gained if the weakest step rose 5 points', 'num', '{in:vis}*0.05/MIN({in:ass}/{in:enq},{in:agr}/{in:ass},{in:vis}/{in:agr})*%s' % AVGH),
  O('Your enquiry-to-client conversion, last 90 days', 'pct', 'IFERROR(COUNTIFS({range:enquiries.status},%s,%s)/COUNTIFS(%s),0)' % (tok('enqst', 'Started'), D90('enquiries.received_on'), D90('enquiries.received_on'))),
  O('Verdict against your own last 90 days', 'text', 'IF({in:vis}/{in:enq}>=IFERROR(COUNTIFS({range:enquiries.status},%s,%s)/COUNTIFS(%s),0),%s,%s)' % (tok('enqst', 'Started'), D90('enquiries.received_on'), D90('enquiries.received_on'), vd('Within target'), vd('Over target')))],
  GR('What if', ('Better assessments: 45', {'ass': 45}), ('More signed: 32', {'agr': 32}), ('Busy period: 90 enquiries', {'enq': 90, 'ass': 57, 'agr': 39, 'vis': 36}), ('Weak start: 18 first visits', {'vis': 18}))),
 TOOL('source_value', 'Source Value Ranking', 'Source value ranking: cost per start',
  'Pick an enquiry source and an extra spend to test; the Source by Month page gives its cost, enquiries, starts and hours for the last 12 months, its rank among the sources and the source to grow.', [
  IL('src', 'Enquiry source', 'enqsrc', 'Online directory'), I('extra', 'Extra spend to test', 600, 'money')], [
  O('Cost, last 12 months', 'money', S10('cost')), O('Enquiries, last 12 months', 'int', S10('enquiries')), O('Clients started, last 12 months', 'int', S10('started')), O('Weekly hours started, last 12 months', 'num', S10('hours_started')),
  O('Cost per client started', 'money', 'IFERROR(%s/%s,0)' % (S10('cost'), S10('started'))), O('Weekly hours started per 100 of cost', 'num', VSEL10),
  O('Rank among the 7 sources (1 = best hours per cost)', 'int', RANK10),
  O('Source to grow', 'text', 'INDEX({range:sources.source},MATCH(MAX({range:sources.value_12m}),{range:sources.value_12m},0))&""'),
  O('Extra clients the extra spend could bring', 'num', 'IFERROR({in:extra}/(%s/%s),0)' % (S10('cost'), S10('started'))),
  O('Verdict', 'text', 'IF(%s<=2,%s,IF(%s>=6,%s,%s))' % (RANK10, vd('Grow this source'), RANK10, vd('Cut or fix this source'), vd('Keep as is')))],
  GR('Source', ('Agency website', {'src': '=' + tok('enqsrc', 'Agency website')}), ('Community event', {'src': '=' + tok('enqsrc', 'Community event')}), ('Past client', {'src': '=' + tok('enqsrc', 'Past client')}), ('Local clinic', {'src': '=' + tok('enqsrc', 'Local clinic')}), ('Family or friend', {'src': '=' + tok('enqsrc', 'Family or friend')}))),
 TOOL('time_to_start', 'Time from First Call to Start', 'Time from first call to start of care',
  'Type the enquiry date and the days each step takes; see the assessment, signature, introduction and start dates, the days against your target, the slowest step and your own average.', [
  I('enq', 'First call date', 'today-3', 'date'), I('d_ass', 'Days to the assessment visit', 3), I('d_sig', 'Days from the assessment to a signed agreement', 4), I('d_int', 'Days from signing to the caregiver introduction', 3), I('d_vis', 'Days from the introduction to the first visit', 2)], [
  O('Assessment date', 'date', '{in:enq}+{in:d_ass}'), O('Agreement signed on', 'date', '{in:enq}+{in:d_ass}+{in:d_sig}'), O('Introduction visit on', 'date', '{in:enq}+{in:d_ass}+{in:d_sig}+{in:d_int}'), O('First visit on', 'date', '{in:enq}+{in:d_ass}+{in:d_sig}+{in:d_int}+{in:d_vis}'),
  O('Days from first call to start', 'int', '{in:d_ass}+{in:d_sig}+{in:d_int}+{in:d_vis}'), O('Target days', 'int', '{set:start_days_target}'), O('Days over (+) or under (-) the target', 'int', '{in:d_ass}+{in:d_sig}+{in:d_int}+{in:d_vis}-{set:start_days_target}'),
  O('Latest first visit date that meets the target', 'date', '{in:enq}+{set:start_days_target}'),
  O('Slowest step', 'text', 'IF(MAX({in:d_ass},{in:d_sig},{in:d_int},{in:d_vis})={in:d_ass},%s,IF(MAX({in:d_ass},{in:d_sig},{in:d_int},{in:d_vis})={in:d_sig},%s,%s))' % (vd('Slowest: assessment'), vd('Slowest: agreement'), vd('Slowest: introduction'))),
  O('Your average days to start, last 90 days of starts', 'num', 'IFERROR(AVERAGEIFS({range:enquiries.days_to_start},{range:enquiries.first_visit_on},">="&({today}-90),{range:enquiries.first_visit_on},"<="&{today}),0)'),
  O('Verdict', 'text', 'IF({in:d_ass}+{in:d_sig}+{in:d_int}+{in:d_vis}<={set:start_days_target},%s,%s)' % (ck('Fast start'), ck('Slow start')))],
  GR('What if', ('Assessment next day', {'d_ass': 1}), ('Slow signature: 9 days', {'d_sig': 9}), ('Slow introduction: 7 days', {'d_int': 7}), ('Fast track', {'d_ass': 1, 'd_sig': 1, 'd_int': 1, 'd_vis': 1}))),
 TOOL('notice_terms', 'Notice and Cancellation Terms', 'Notice and cancellation terms',
  'Type visit hours, rate, the late-cancellation share and days to refill; see the charge, what you keep after the caregiver guarantee and the break-even notice.', [
  I('hrs', 'Visit hours', 4, 'num'), I('rate', 'Bill rate per hour', 36, 'money'), I('share', 'Share of the visit charged for a late cancellation', 0.5, 'pct'), I('pay', 'Caregiver pay per hour', 18, 'money'),
  I('guar', 'Share of the visit pay guaranteed to the caregiver', 0.5, 'pct'), I('notice', 'Notice given by the client, days', 1), I('refill', 'Days normally needed to refill a visit', 2), I('cxl', 'Late cancellations a month', 4)], [
  O('Full charge of the visit', 'money', '{in:hrs}*{in:rate}'), O('Charge for a late cancellation', 'money', 'IF({in:notice}>={set:notice_days},0,{in:hrs}*{in:rate}*{in:share})'),
  O('Guarantee paid to the caregiver (with burden)', 'money', '{in:hrs}*{in:pay}*(1+%s)*{in:guar}' % B), O('Kept after the guarantee, per late cancellation', 'money', 'IF({in:notice}>={set:notice_days},0,{in:hrs}*{in:rate}*{in:share})-{in:hrs}*{in:pay}*(1+%s)*{in:guar}' % B),
  O('Charge needed to cover the guarantee', 'pct', '{in:pay}*(1+%s)*{in:guar}/{in:rate}' % B), O('Break-even notice, days (days to refill the visit)', 'int', '{in:refill}'),
  O('Kept in a month after guarantees', 'money', '{in:cxl}*(IF({in:notice}>={set:notice_days},0,{in:hrs}*{in:rate}*{in:share})-{in:hrs}*{in:pay}*(1+%s)*{in:guar})' % B),
  O('Verdict', 'text', 'IF({in:share}>={in:pay}*(1+%s)*{in:guar}/{in:rate},%s,%s)' % (B, vd('Charge covers cost'), vd('Raise the cancellation share')))],
  GR('What if', ('Charge 25%', {'share': 0.25}), ('Charge the full visit', {'share': 1}), ('Three days of notice', {'notice': 3}), ('Guarantee the full pay', {'guar': 1}))),
 TOOL('price_test', 'Price Test for a Lost Enquiry', 'Price test: hold or match a competitor rate',
  'Type your quoted rate, the rate the enquirer was offered, the hours and your cost; see the margin you give up to win the client, the weekly profit at each rate and whether to hold or match.', [
  I('rate', 'Your quoted rate per hour', 37, 'money'), I('comp', 'Competitor rate per hour', 33, 'money'), I('hrs', 'Hours a week', 20, 'num'), I('pay', 'Caregiver pay per hour', 18.5, 'money'), I('ext', 'Travel and mileage cost per client hour', 1.8, 'money')], [
  O('Loaded cost per client hour', 'money', '{in:pay}*(1+%s)+{in:ext}' % B), O('Margin per hour at your rate', 'money', '{in:rate}-{in:pay}*(1+%s)-{in:ext}' % B), O('Margin per hour at the competitor rate', 'money', '{in:comp}-{in:pay}*(1+%s)-{in:ext}' % B),
  O('Weekly profit at your rate', 'money', '({in:rate}-{in:pay}*(1+%s)-{in:ext})*{in:hrs}' % B), O('Weekly profit at the competitor rate', 'money', '({in:comp}-{in:pay}*(1+%s)-{in:ext})*{in:hrs}' % B),
  O('Weekly margin given up to win', 'money', '({in:rate}-{in:comp})*{in:hrs}'), O('Margin share at the competitor rate', 'pct', '1-({in:pay}*(1+%s)+{in:ext})/{in:comp}' % B),
  O('Hours at the competitor rate that equal your profit', 'num', 'IFERROR({in:hrs}*({in:rate}-{in:pay}*(1+%s)-{in:ext})/({in:comp}-{in:pay}*(1+%s)-{in:ext}),0)' % (B, B)),
  O('Verdict', 'text', 'IF(1-({in:pay}*(1+%s)+{in:ext})/{in:comp}>={set:margin_red},%s,%s)' % (B, vd('Match the rate'), vd('Hold the rate')))],
  GR('What if', ('Competitor at 29', {'comp': 29}), ('Competitor at 35', {'comp': 35}), ('Small case: 10 hours', {'hrs': 10}), ('Higher pay: 21', {'pay': 21}))),
 TOOL('hours_forecast', 'Hours to Fill Forecast', 'Hours to fill forecast, 3 months',
  'Pick a scenario and type conversion and average hours; your last 6 months give the next 3 months, hours to start and caregivers needed.', [
  IL('sc', 'Scenario', 'scen', 'Base'), I('conv', 'Enquiry-to-client conversion', 0.25, 'pct'), I('avg', 'Average weekly hours per new client', 16, 'num'), I('cg', 'Weekly hours one new caregiver can take', 22, 'num')], [
  O('Enquiries a month, last 3 months', 'num', L3), O('Trend factor from the 3 months before', 'num', TR14), O('Enquiries next month', 'num', FC14(1)), O('Enquiries in 2 months', 'num', FC14(2)), O('Enquiries in 3 months', 'num', FC14(3)),
  O('Clients starting in 3 months', 'num', '(%s+%s+%s)*{in:conv}' % (FC14(1), FC14(2), FC14(3))), O('Weekly hours started in 3 months', 'num', '(%s+%s+%s)*{in:conv}*{in:avg}' % (FC14(1), FC14(2), FC14(3))),
  O('Caregivers needed for those hours', 'num', '(%s+%s+%s)*{in:conv}*{in:avg}/{in:cg}' % (FC14(1), FC14(2), FC14(3))), O('Free hours next week across caregivers', 'num', 'SUM({range:capacity.free_hours})'),
  O('Verdict', 'text', 'IF((%s+%s+%s)*{in:conv}*{in:avg}>SUM({range:capacity.free_hours}),%s,%s)' % (FC14(1), FC14(2), FC14(3), vd('Hire ahead'), vd('Capacity is enough')))],
  GR('Scenario', ('Best case', {'sc': '=' + tok('scen', 'Best')}), ('Worst case', {'sc': '=' + tok('scen', 'Worst')}), ('Better conversion 35%', {'conv': 0.35}), ('Bigger cases: 24 hours', {'avg': 24}))),
 TOOL('one_person', 'One-Person Capacity Check', 'One-person capacity check for a start-up agency',
  'For an owner who also works visits: type your hours, booked hours and a new client; see income, free hours after travel and admin, and Take or Full.', [
  I('own', 'Your own working hours a week', 45, 'num'), I('booked', 'Care hours already booked a week', 22, 'num'), I('new', 'Hours of the new client a week', 8, 'num'), I('vis', 'Average visit hours', 3, 'num'), I('trav', 'Travel minutes between visits', 20),
  I('admin', 'Admin hours a week', 6, 'num'), I('rate', 'Bill rate per hour', 34, 'money'), I('km', 'Km driven per visit', 7, 'num'), I('mil', 'Mileage rate per km', 0.4, 'money')], [
  O('Visits a week with the new client', 'num', '({in:booked}+{in:new})/{in:vis}'), O('Travel hours a week', 'num', '({in:booked}+{in:new})/{in:vis}*{in:trav}/60'),
  O('Hours used: care, travel and admin', 'num', '{in:booked}+{in:new}+({in:booked}+{in:new})/{in:vis}*{in:trav}/60+{in:admin}'), O('Hours still free', 'num', '{in:own}-({in:booked}+{in:new}+({in:booked}+{in:new})/{in:vis}*{in:trav}/60+{in:admin})'),
  O('Weekly income after mileage', 'money', '({in:booked}+{in:new})*{in:rate}-({in:booked}+{in:new})/{in:vis}*{in:km}*{in:mil}'), O('Income per hour of your own time', 'money', '(({in:booked}+{in:new})*{in:rate}-({in:booked}+{in:new})/{in:vis}*{in:km}*{in:mil})/({in:booked}+{in:new}+({in:booked}+{in:new})/{in:vis}*{in:trav}/60+{in:admin})'),
  O('Most hours of a new client you could still take', 'num', 'MAX(0,{in:own}-{in:admin}-{in:booked}*(1+{in:trav}/60/{in:vis}))/(1+{in:trav}/60/{in:vis})'),
  O('Verdict', 'text', 'IF({in:own}-({in:booked}+{in:new}+({in:booked}+{in:new})/{in:vis}*{in:trav}/60+{in:admin})>=0,%s,%s)' % (vd('Take'), vd('Full')))],
  GR('What if', ('Big client: 16 hours', {'new': 16}), ('Short visits: 1.5 hours', {'vis': 1.5}), ('Work 55 hours', {'own': 55}), ('Less admin: 3 hours', {'admin': 3}))),
 TOOL('holiday_quote', 'Holiday Visit Quote', 'Holiday visit quote: charge, pay with premium and margin',
  'Type a holiday date, the hours and the service; see the client charge at the holiday rate, the caregiver cost with the holiday premium, the margin and the extra charged over a weekday visit.', [
  I('hdate', 'Holiday date', 'today+40', 'date'), I('hrs', 'Hours', 6, 'num'), IL('svc', 'Service', 'svc', 'Companion care')], [
  O('Holiday on that date', 'text', 'IFERROR(INDEX({range:holidays.holiday},MATCH({in:hdate},{range:holidays.date},0))&"","")'),
  O('Bill multiplier used', 'num', 'IF(SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate})=0,{set:holiday_bill_mult},SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate}))'),
  O('Client charge at the holiday rate', 'money', '{in:hrs}*%s*IF(SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate})=0,{set:holiday_bill_mult},SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate}))' % RC('bill_rate', '{in:svc}', BT('Weekday'))),
  O('Caregiver cost with the holiday premium and burden', 'money', '{in:hrs}*%s*IF(SUMIFS({range:holidays.pay_mult},{range:holidays.date},{in:hdate})=0,{set:holiday_pay_mult},SUMIFS({range:holidays.pay_mult},{range:holidays.date},{in:hdate}))*(1+%s)' % (RC('pay_rate', '{in:svc}', BT('Weekday')), B)),
  O('Margin on the visit', 'money', '{in:hrs}*(%s*IF(SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate})=0,{set:holiday_bill_mult},SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate}))-%s*IF(SUMIFS({range:holidays.pay_mult},{range:holidays.date},{in:hdate})=0,{set:holiday_pay_mult},SUMIFS({range:holidays.pay_mult},{range:holidays.date},{in:hdate}))*(1+%s))' % (RC('bill_rate', '{in:svc}', BT('Weekday')), RC('pay_rate', '{in:svc}', BT('Weekday')), B)),
  O('Margin share', 'pct', '1-%s*IF(SUMIFS({range:holidays.pay_mult},{range:holidays.date},{in:hdate})=0,{set:holiday_pay_mult},SUMIFS({range:holidays.pay_mult},{range:holidays.date},{in:hdate}))*(1+%s)/(%s*IF(SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate})=0,{set:holiday_bill_mult},SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate})))' % (RC('pay_rate', '{in:svc}', BT('Weekday')), B, RC('bill_rate', '{in:svc}', BT('Weekday')))),
  O('Extra charged over a weekday visit', 'money', '{in:hrs}*%s*(IF(SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate})=0,{set:holiday_bill_mult},SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate}))-1)' % RC('bill_rate', '{in:svc}', BT('Weekday'))),
  O('Days until the holiday', 'int', '{in:hdate}-{today}'),
  O('Verdict', 'text', 'IF(1-%s*IF(SUMIFS({range:holidays.pay_mult},{range:holidays.date},{in:hdate})=0,{set:holiday_pay_mult},SUMIFS({range:holidays.pay_mult},{range:holidays.date},{in:hdate}))*(1+%s)/(%s*IF(SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate})=0,{set:holiday_bill_mult},SUMIFS({range:holidays.bill_mult},{range:holidays.date},{in:hdate})))>=%s,%s,%s)' % (RC('pay_rate', '{in:svc}', BT('Weekday')), B, RC('bill_rate', '{in:svc}', BT('Weekday')), TM, vd('Holiday rate pays'), vd('Holiday rate is thin')))],
  GR('What if', ('Overnight care', {'svc': '=' + tok('svc', 'Overnight care'), 'hrs': 10}), ('Live-in day', {'svc': '=' + tok('svc', 'Live-in day'), 'hrs': 12}), ('Short holiday visit: 2 hours', {'hrs': 2}), ('Personal care help', {'svc': '=' + tok('svc', 'Personal care help')}))),
 TOOL('sensitivity', 'Quote Sensitivity', 'Quote sensitivity: the same quote at five rates',
  'Type the hours, your rate and your cost; see the margin per hour and the weekly profit if the rate were 10 or 5 percent lower or higher, and the lowest step that still meets the target.', [
  I('hrs', 'Hours a week', 20, 'num'), I('rate', 'Quoted bill rate per hour', 40, 'money'), I('pay', 'Caregiver pay per hour', 18.5, 'money'), I('ext', 'Travel and mileage cost per client hour', 1.8, 'money')], [
  O('Margin per hour at minus 10%', 'money', '{in:rate}*0.9-{in:pay}*(1+%s)-{in:ext}' % B), O('Margin per hour at minus 5%', 'money', '{in:rate}*0.95-{in:pay}*(1+%s)-{in:ext}' % B), O('Margin per hour at the quoted rate', 'money', '{in:rate}-{in:pay}*(1+%s)-{in:ext}' % B),
  O('Margin per hour at plus 5%', 'money', '{in:rate}*1.05-{in:pay}*(1+%s)-{in:ext}' % B), O('Margin per hour at plus 10%', 'money', '{in:rate}*1.1-{in:pay}*(1+%s)-{in:ext}' % B),
  O('Weekly profit at minus 10%', 'money', '({in:rate}*0.9-{in:pay}*(1+%s)-{in:ext})*{in:hrs}' % B), O('Weekly profit at minus 5%', 'money', '({in:rate}*0.95-{in:pay}*(1+%s)-{in:ext})*{in:hrs}' % B), O('Weekly profit at the quoted rate', 'money', '({in:rate}-{in:pay}*(1+%s)-{in:ext})*{in:hrs}' % B),
  O('Weekly profit at plus 5%', 'money', '({in:rate}*1.05-{in:pay}*(1+%s)-{in:ext})*{in:hrs}' % B), O('Weekly profit at plus 10%', 'money', '({in:rate}*1.1-{in:pay}*(1+%s)-{in:ext})*{in:hrs}' % B),
  O('Largest discount that still meets the target margin', 'pct', 'MAX(0,1-({in:pay}*(1+%s)+{in:ext})/(1-%s)/{in:rate})' % (B, TM)),
  O('Verdict', 'text', 'IF(1-({in:pay}*(1+%s)+{in:ext})/{in:rate}>=%s,%s,%s)' % (B, TM, ck('Quote on target'), vd('Quote lower')))],
  GR('What if', ('Pay 21 an hour', {'pay': 21}), ('Rate 36', {'rate': 36}), ('Rate 44', {'rate': 44}), ('Big case: 40 hours', {'hrs': 40}))),
 TOOL('hours_grid', 'Hours and Rate What-if Grid', 'What-if grid: weekly margin by hours and bill rate',
  'Type your cost per hour and a rate; see the weekly margin at 10, 20, 30 and 40 hours for the rate minus 2, the rate and the rate plus 2, and the hours needed to earn a weekly margin goal.', [
  I('rate', 'Bill rate per hour', 36, 'money'), I('pay', 'Caregiver pay per hour', 18.5, 'money'), I('ext', 'Travel and mileage cost per client hour', 1.8, 'money'), I('goal', 'Weekly margin goal', 300, 'money')], [
  O('Weekly margin: 10 hours at the rate minus 2', 'money', '10*({in:rate}-2-{in:pay}*(1+%s)-{in:ext})' % B), O('Weekly margin: 10 hours at the rate', 'money', '10*({in:rate}-{in:pay}*(1+%s)-{in:ext})' % B), O('Weekly margin: 10 hours at the rate plus 2', 'money', '10*({in:rate}+2-{in:pay}*(1+%s)-{in:ext})' % B),
  O('Weekly margin: 20 hours at the rate minus 2', 'money', '20*({in:rate}-2-{in:pay}*(1+%s)-{in:ext})' % B), O('Weekly margin: 20 hours at the rate', 'money', '20*({in:rate}-{in:pay}*(1+%s)-{in:ext})' % B), O('Weekly margin: 20 hours at the rate plus 2', 'money', '20*({in:rate}+2-{in:pay}*(1+%s)-{in:ext})' % B),
  O('Weekly margin: 30 hours at the rate minus 2', 'money', '30*({in:rate}-2-{in:pay}*(1+%s)-{in:ext})' % B), O('Weekly margin: 30 hours at the rate', 'money', '30*({in:rate}-{in:pay}*(1+%s)-{in:ext})' % B), O('Weekly margin: 30 hours at the rate plus 2', 'money', '30*({in:rate}+2-{in:pay}*(1+%s)-{in:ext})' % B),
  O('Weekly margin: 40 hours at the rate minus 2', 'money', '40*({in:rate}-2-{in:pay}*(1+%s)-{in:ext})' % B), O('Weekly margin: 40 hours at the rate', 'money', '40*({in:rate}-{in:pay}*(1+%s)-{in:ext})' % B), O('Weekly margin: 40 hours at the rate plus 2', 'money', '40*({in:rate}+2-{in:pay}*(1+%s)-{in:ext})' % B),
  O('Hours a week needed for the margin goal', 'num', '{in:goal}/({in:rate}-{in:pay}*(1+%s)-{in:ext})' % B),
  O('Verdict', 'text', 'IF(30*({in:rate}-{in:pay}*(1+%s)-{in:ext})>={in:goal},%s,%s)' % (B, vd('Pays'), vd('Thin')))],
  GR('What if', ('Rate 40', {'rate': 40}), ('Pay 21', {'pay': 21}), ('Goal 600 a week', {'goal': 600}), ('Low cost: travel 0.8', {'ext': 0.8}))),
]
assert len(tools) == 18, len(tools)
