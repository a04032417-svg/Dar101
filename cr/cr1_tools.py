"""Car rental suite part 1: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr1_lists import *
import cr1_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c): return '{range:%s.%s}' % (t, c)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'
OPEN = tok('estatus', 'Open'); QUOTED = tok('estatus', 'Quoted'); BOOKED = tok('estatus', 'Booked'); LOST = tok('estatus', 'Lost')
D90 = '%s,">="&({today}-90)' % R('enquiries', 'date')
DAILY = tok('plan', 'Daily'); WEEKLY = tok('plan', 'Weekly'); MONTHLY = tok('plan', 'Monthly')
def CLS_RATE(cls): return 'SUMIFS(%s,%s,%s)' % (R('classes', 'daily_rate'), R('classes', 'class'), cls)
def PLAN_RATE(cls, plan): return 'SUMIFS(%s,%s,%s,%s,%s)' % (R('rates', 'rate'), R('rates', 'class'), cls, R('rates', 'plan'), plan)
def FLOOR(cls): return 'SUMIFS(%s,%s,%s)' % (R('cost_floor', 'floor_price'), R('cost_floor', 'class'), cls)
def COSTD(cls): return 'SUMIFS(%s,%s,%s)' % (R('cost_floor', 'cost_day'), R('cost_floor', 'class'), cls)
def CT(c): return tok('class', c)
tools = []

# 1 ------------------------------------------------------------ instant quote builder
SEAS1 = 'INDEX(%s,MATCH(MONTH({in:pickup}),%s,0))' % (R('month_season', 'season'), R('month_season', 'month_no'))
MULT1 = 'SUMIFS(%s,%s,%s)' % (R('seasons', 'multiplier'), R('seasons', 'season'), SEAS1)
FRI1 = 'AND(WEEKDAY({in:pickup},2)=5,{in:days}<=3)'
DAYR1 = 'ROUND(%s*%s*IF(%s,1+{set:weekend_uplift},1),2)' % (CLS_RATE('{in:cls}'), MULT1, FRI1)
PERD1 = 'ROUND(IF({in:days}>=30,%s/30*(1+0.3*(%s-1)),IF({in:days}>=7,%s/7*(1+0.5*(%s-1)),%s)),2)' % (PLAN_RATE('{in:cls}', MONTHLY), MULT1, PLAN_RATE('{in:cls}', WEEKLY), MULT1, DAYR1)
def AP(a): return 'SUMIFS(%s,%s,%s)' % (R('addons', 'price_day'), R('addons', 'addon'), tok('addon', a))
ADD1 = ('{in:seat}*%s*MIN({in:days},7)+{in:driver}*%s*MIN({in:days},7)+{in:nav}*%s*MIN({in:days},7)+IF({in:cover}=1,%s*MIN({in:days},30),IF({in:cover}=2,%s*MIN({in:days},30),0))'
        '+{in:roof}*%s*MIN({in:days},7)+{in:young}*%s*MIN({in:days},30)') % (AP('Child seat'), AP('Extra driver'), AP('Navigation unit'), AP('Cover option basic'), AP('Cover option plus'), AP('Roof box'), AP('Young-driver fee'))
DEL1 = '2*SUMIFS(%s,%s,{in:loc})' % (R('zones', 'fee_leg'), R('zones', 'location'))
REN1 = 'ROUND(%s*{in:days},2)' % PERD1
tools.append(TOOL('quote_builder', 'Instant Quote Builder', 'Which price do I quote for these dates',
    'Pick the class, pickup date, days, delivery place and add-ons; the season, day rate, total, deposit and the floor price check appear with a verdict.', [
    IL('cls', 'Class', 'class', 'Midsize SUV'), I('pickup', 'Pickup date', 'today+40', 'date'), I('days', 'Days', 3, 'int'), IL('loc', 'Pickup place', 'location', 'Airport delivery'),
    I('seat', 'Child seat, 1 for yes', 1, 'int'), I('driver', 'Extra driver, 1 for yes', 0, 'int'), I('nav', 'Navigation unit, 1 for yes', 0, 'int'), I('cover', 'Cover option, 0 none, 1 basic, 2 plus', 1, 'int'),
    I('roof', 'Roof box, 1 for yes', 0, 'int'), I('young', 'Young driver, 1 for yes', 0, 'int')], [
    O('Season of the pickup month', 'text', SEAS1), O('Season multiplier', 'num', MULT1), O('Day rate with season and weekend uplift', 'money', DAYR1), O('Price per day used', 'money', PERD1),
    O('Rental', 'money', REN1), O('Add-ons', 'money', ADD1), O('Delivery, both ways', 'money', DEL1), O('Total before any sales tax', 'money', '%s+%s+%s' % (REN1, ADD1, DEL1)),
    O('Deposit held at pickup', 'money', 'SUMIFS(%s,%s,{in:cls})' % (R('classes', 'deposit'), R('classes', 'class'))), O('Floor price for the stay', 'money', 'ROUND(%s*{in:days},2)' % FLOOR('{in:cls}')),
    O('Margin of the rental over the floor', 'money', '%s-ROUND(%s*{in:days},2)' % (REN1, FLOOR('{in:cls}'))), O('Lowest price a day to quote', 'money', 'ROUNDUP(%s,0)' % FLOOR('{in:cls}')),
    O('Quote valid until', 'date', '{today}+{set:quote_valid_days}'),
    O('Verdict', 'text', 'IF(%s<%s,%s,%s)' % (PERD1, FLOOR('{in:cls}'), kb('Below the floor price'), kb('Quote ready')))],
    GR('What if', ('Premium class', {'cls': '=' + CT('Premium')}), ('Electric class', {'cls': '=' + CT('Electric')}), ('A week', {'days': 7}), ('A month', {'days': 30}), ('Young driver added', {'young': 1}),
       ('Home delivery', {'loc': '=' + tok('location', 'Home delivery')}))))

# 2 ------------------------------------------------------------ cost-based floor price
CA2 = '(%s*{in:cur_util})' % COSTD('{in:cls}')
FL2 = '(%s/{in:util}*(1+{in:margin}))' % CA2
def FLU(u): return 'ROUND(%s/%s*(1+{in:margin}),2)' % (CA2, u)
tools.append(TOOL('floor_tool', 'Cost-Based Floor Price', 'Is my price above the cost floor',
    'Pick a class, the utilisation you really get now and the one you plan for; the lowest price that still covers cost appears with five utilisation steps and a verdict.', [
    IL('cls', 'Class', 'class', 'Electric'), I('cur_util', 'Utilisation you get now', 0.56, 'pct'), I('util', 'Utilisation you plan for', 0.56, 'pct'), I('margin', 'Margin on top of cost', 0.10, 'pct'),
    I('days', 'Days of the rental', 3, 'int')], [
    O('Cost per rented day now', 'money', COSTD('{in:cls}')), O('Cost per available day', 'money', CA2), O('Floor price a day at your planned utilisation', 'money', 'ROUND(%s,2)' % FL2),
    O('Daily rate of the class', 'money', CLS_RATE('{in:cls}')), O('Rate over the floor', 'pct', 'IFERROR(%s/%s-1,0)' % (CLS_RATE('{in:cls}'), FL2)), O('Floor price for the rental', 'money', 'ROUND(%s*{in:days},2)' % FL2),
    O('Utilisation that makes the daily rate break even', 'pct', 'IFERROR(%s*(1+{in:margin})/%s,0)' % (CA2, CLS_RATE('{in:cls}')), ),
    O('Floor at 50% utilisation', 'money', FLU('0.5')), O('Floor at 60% utilisation', 'money', FLU('0.6')), O('Floor at 70% utilisation', 'money', FLU('0.7')),
    O('Floor at 80% utilisation', 'money', FLU('0.8')), O('Floor at 90% utilisation', 'money', FLU('0.9')),
    O('Daily rate to set', 'money', 'MAX(%s,ROUNDUP(%s,0))' % (CLS_RATE('{in:cls}'), FL2)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (CLS_RATE('{in:cls}'), FL2, kb('Price above floor'), kb('Raise the price')))],
    GR('What if', ('Premium class', {'cls': '=' + CT('Premium'), 'cur_util': 0.5, 'util': 0.5}), ('Plan 70% utilisation', {'util': 0.7}), ('Margin 20%', {'margin': 0.2}), ('Economy class', {'cls': '=' + CT('Economy'), 'cur_util': 0.72, 'util': 0.72}),
       ('Midsize SUV', {'cls': '=' + CT('Midsize SUV'), 'cur_util': 0.76, 'util': 0.76}))))

# 3 ------------------------------------------------------------ seasonal rate card checker
MU3 = 'SUMIFS(%s,%s,{in:season})' % (R('seasons', 'multiplier'), R('seasons', 'season'))
RS3 = '(%s*%s)' % (CLS_RATE('{in:cls}'), MU3)
QC3 = '%s,{in:cls},%s,{in:season}' % (R('enquiries', 'class'), R('enquiries', 'season'))
ACH3 = 'IFERROR(SUMIFS(%s,%s,%s,%s)/SUMIFS(%s,%s,%s,%s),0)' % (R('enquiries', 'quote_amount'), R('enquiries', 'class'), '{in:cls}', '%s,{in:season},%s,%s' % (R('enquiries', 'season'), R('enquiries', 'status'), BOOKED),
                                                              R('enquiries', 'days'), R('enquiries', 'class'), '{in:cls}', '%s,{in:season},%s,%s' % (R('enquiries', 'season'), R('enquiries', 'status'), BOOKED))
N3 = 'COUNTIFS(%s,{in:cls},%s,{in:season},%s,%s)' % (R('enquiries', 'class'), R('enquiries', 'season'), R('enquiries', 'status'), BOOKED)
tools.append(TOOL('season_checker', 'Seasonal Rate Checker', 'Should this class rate rise, hold or fall in this season',
    'Pick a class and a season; the rate card price is set against the cost floor and what booked quotes in that season paid a day.', [
    IL('cls', 'Class', 'class', 'Electric'), IL('season', 'Season', 'season', 'Peak')], [
    O('Daily rate of the class', 'money', CLS_RATE('{in:cls}')), O('Season multiplier', 'num', MU3), O('Rate in this season', 'money', 'ROUND(%s,2)' % RS3), O('Floor price a day', 'money', FLOOR('{in:cls}')),
    O('Season rate over the floor', 'money', 'ROUND(%s-%s,2)' % (RS3, FLOOR('{in:cls}')), ), O('Paid a day on booked quotes in this season', 'money', 'ROUND(%s,2)' % ACH3), O('Booked quotes in the log', 'int', N3),
    O('Paid over the season rate', 'pct', 'IFERROR(%s/%s-1,0)' % (ACH3, RS3)),
    O('Seasons below the floor', 'int', 'SUMPRODUCT((%s>0)*(%s*%s<%s))' % (R('seasons', 'multiplier'), CLS_RATE('{in:cls}'), R('seasons', 'multiplier'), FLOOR('{in:cls}'))),
    O('Verdict', 'text', 'IF(%s<%s,%s,IF(%s<3,%s,IF(%s>%s*1.05,%s,IF(%s<%s*0.9,%s,%s))))' % (RS3, FLOOR('{in:cls}'), kb('Raise'), N3, kb('Hold'), ACH3, RS3, kb('Raise'), ACH3, RS3, kb('Lower'), kb('Hold')))],
    GR('What if', ('Off-peak', {'season': '=' + tok('season', 'Off-peak')}), ('Shoulder', {'season': '=' + tok('season', 'Shoulder')}), ('Holiday', {'season': '=' + tok('season', 'Holiday')}),
       ('Electric in peak', {'cls': '=' + CT('Electric')}), ('Economy in peak', {'cls': '=' + CT('Economy')}))))

# 4 ------------------------------------------------------------ weekend and event uplift planner
RU4 = '({in:rate}*(1+{in:uplift}))'
LEFT4 = 'MAX(0,ROUND({in:cars}*{in:fill}-{in:booked},0))'
NEED4 = 'MAX(0,{in:goal}-{in:booked}*{in:days}*%s)' % RU4
RN4 = 'IFERROR(%s/(%s*{in:days}),0)' % (NEED4, LEFT4)
tools.append(TOOL('event_planner', 'Event Uplift Planner', 'What weekend or event rate fills the rest of the cars',
    'Type the cars, the cars already booked, the event days, your average day rate and the revenue you want; the uplift needed on the cars still free appears.', [
    I('cars', 'Cars you can rent out', 26, 'int'), I('booked', 'Cars already booked', 14, 'int'), I('days', 'Event days', 3, 'int'), I('rate', 'Average day rate', 78), I('uplift', 'Uplift you planned', 0.25, 'pct'),
    I('fill', 'Share of cars you want rented', 0.85, 'pct'), I('goal', 'Revenue you want from the event', 6800)], [
    O('Share of cars booked', 'pct', 'IFERROR({in:booked}/{in:cars},0)'), O('Day rate with your uplift', 'money', 'ROUND(%s,2)' % RU4), O('Cars still to book for your target', 'int', LEFT4),
    O('Revenue booked at the uplifted rate', 'money', 'ROUND({in:booked}*{in:days}*%s,2)' % RU4), O('Revenue still needed', 'money', 'ROUND(%s,2)' % NEED4),
    O('Day rate the free cars need', 'money', 'ROUND(%s,2)' % RN4), O('Uplift the free cars need', 'pct', 'IFERROR(%s/{in:rate}-1,0)' % RN4),
    O('Weekend rate to set', 'money', 'ROUND(MAX(%s,%s),2)' % (RU4, RN4)), O('Rate of one extra uplift step of 5 points', 'money', 'ROUND({in:rate}*(1+{in:uplift}+0.05),2)'),
    O('Verdict', 'text', 'IF(%s>%s,%s,%s)' % (RN4, RU4, kc('Raise the weekend rate'), kc('Hold the weekend rate')))],
    GR('What if', ('Uplift 15%', {'uplift': 0.15}), ('Uplift 35%', {'uplift': 0.35}), ('Only 8 cars booked', {'booked': 8}), ('22 cars booked', {'booked': 22}), ('Lower goal', {'goal': 5200}))))

# 5 ------------------------------------------------------------ weekly and monthly discount tester
A5 = '({in:d}*{in:short}/({in:short}+{in:idle_short}))'
B5 = '(%s/(7+{in:idle_week}))' % PLAN_RATE('{in:cls}', WEEKLY)
C5 = '(%s/(30+{in:idle_month}))' % PLAN_RATE('{in:cls}', MONTHLY)
A5 = '(%s*{in:short}/({in:short}+{in:idle_short}))' % CLS_RATE('{in:cls}')
tools.append(TOOL('step_tester', 'Discount Step Tester', 'Is my weekly and monthly discount right',
    'Pick a class and the idle days that follow a short rental, a week and a month; net revenue per available day of each plan is compared and the step is judged.', [
    IL('cls', 'Class', 'class', 'Compact'), I('short', 'Days of a short rental', 3, 'int'), I('idle_short', 'Idle days after a short rental', 1.5, 'num'), I('idle_week', 'Idle days after a week', 0.8, 'num'),
    I('idle_month', 'Idle days after a month', 1.2, 'num')], [
    O('Daily rate', 'money', CLS_RATE('{in:cls}')), O('Weekly rate', 'money', PLAN_RATE('{in:cls}', WEEKLY)), O('Monthly rate', 'money', PLAN_RATE('{in:cls}', MONTHLY)),
    O('Weekly step below seven days at the daily rate', 'pct', 'IFERROR(1-%s/(7*%s),0)' % (PLAN_RATE('{in:cls}', WEEKLY), CLS_RATE('{in:cls}'))),
    O('Monthly step below 30 days at the daily rate', 'pct', 'IFERROR(1-%s/(30*%s),0)' % (PLAN_RATE('{in:cls}', MONTHLY), CLS_RATE('{in:cls}'))),
    O('Short rentals, revenue per available day', 'money', 'ROUND(%s,2)' % A5), O('Weekly plan, revenue per available day', 'money', 'ROUND(%s,2)' % B5), O('Monthly plan, revenue per available day', 'money', 'ROUND(%s,2)' % C5),
    O('Weekly price that matches short rentals', 'money', 'ROUND(%s*(7+{in:idle_week}),2)' % A5), O('Monthly price that matches short rentals', 'money', 'ROUND(%s*(30+{in:idle_month}),2)' % A5),
    O('Verdict for the weekly plan', 'text', 'IF(%s>=%s*1.05,%s,IF(%s<%s,%s,%s))' % (B5, A5, kb('Lower the step'), B5, A5, kb('Raise the step'), kb('Keep'))),
    O('Verdict for the monthly plan', 'text', 'IF(%s>=%s*1.05,%s,IF(%s<%s,%s,%s))' % (C5, A5, kb('Lower the step'), C5, A5, kb('Raise the step'), kb('Keep')))],
    GR('What if', ('More idle after a week', {'idle_week': 2.5}), ('No idle after a short rental', {'idle_short': 0}), ('Premium class', {'cls': '=' + CT('Premium')}), ('Economy class', {'cls': '=' + CT('Economy')}),
       ('Two-day rentals', {'short': 2}))))

# 6 ------------------------------------------------------------ add-on profit ranker
PPL = R('addon_profit', 'profit_per_line'); APN = R('addon_profit', 'addon')
def NTH6(k, col=APN): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (col, PPL, k, PPL)
tools.append(TOOL('addon_ranker', 'Add-on Profit Ranker', 'Which add-on should I push first',
    'Add-ons are ranked by profit per line; type the stock you buy and the bookings a year to see the uptake that pays for it.', [
    I('stock', 'Yearly cost of stock for the add-on', 900), I('bookings', 'Bookings a year', 1300, 'int')], [
    O('Best add-on by profit per line', 'text', NTH6(1)), O('Profit per line of the best', 'money', 'IFERROR(LARGE(%s,1),0)' % PPL), O('Second add-on', 'text', NTH6(2)), O('Profit per line of the second', 'money', 'IFERROR(LARGE(%s,2),0)' % PPL),
    O('Third add-on', 'text', NTH6(3)), O('Profit per line of the third', 'money', 'IFERROR(LARGE(%s,3),0)' % PPL), O('Weakest add-on', 'text', 'IFERROR(INDEX(%s,MATCH(SMALL(%s,1),%s,0)),"")' % (APN, PPL, PPL)),
    O('Profit per line of the weakest', 'money', 'IFERROR(SMALL(%s,1),0)' % PPL), O('Lines a year that pay for the stock of the best', 'int', 'IFERROR(ROUNDUP({in:stock}/LARGE(%s,1),0),0)' % PPL),
    O('Uptake that pays for the stock of the best', 'pct', 'IFERROR({in:stock}/(LARGE(%s,1)*{in:bookings}),0)' % PPL), O('Share of bookings with the best add-on now', 'pct', 'IFERROR(COUNTIFS(%s,%s)/COUNTIFS(%s,%s),0)' % (R('addon_lines', 'addon'), NTH6(1), R('addon_lines', 'first_line'), YES)),
    O('Verdict', 'text', 'IF(LARGE(%s,1)>0,%s,%s)' % (PPL, kb('Push the top add-on'), kb('Hold')))],
    GR('What if', ('Stock 400', {'stock': 400}), ('Stock 1500', {'stock': 1500}), ('900 bookings', {'bookings': 900}), ('1800 bookings', {'bookings': 1800}), ('Stock 2500, 900 bookings', {'stock': 2500, 'bookings': 900}))))

# 7 ------------------------------------------------------------ upsell target per booking
CUR7 = 'IFERROR(SUMIFS(%s,%s,">="&EDATE(%s,-2))/SUMIFS(%s,%s,">="&EDATE(%s,-2)),0)' % (R('addon_lines', 'amount'), R('addon_lines', 'month'), MS, R('funnel', 'bookings_all'), R('funnel', 'month'), MS)
tools.append(TOOL('upsell_target', 'Upsell Target', 'Are add-ons on target per booking',
    'Add-on revenue per booking in the last three months is set against your target; the extra yearly revenue if the target is met appears.', [
    I('target', 'Add-on revenue per booking you aim for', 42), I('bookings', 'Bookings a year', 1300, 'int')], [
    O('Add-on revenue per booking, last 3 months', 'money', 'ROUND(%s,2)' % CUR7), O('Add-on revenue, last 3 months', 'money', 'SUMIFS(%s,%s,">="&EDATE(%s,-2))' % (R('addon_lines', 'amount'), R('addon_lines', 'month'), MS)),
    O('Bookings, last 3 months', 'int', 'SUMIFS(%s,%s,">="&EDATE(%s,-2))' % (R('funnel', 'bookings_all'), R('funnel', 'month'), MS)),
    O('Short of the target per booking', 'money', 'ROUND(MAX(0,{in:target}-%s),2)' % CUR7), O('Extra revenue a year if the target is met', 'money', 'ROUND(MAX(0,{in:target}-%s)*{in:bookings},0)' % CUR7),
    O('Bookings with an add-on, last 3 months', 'pct', 'IFERROR(COUNTIFS(%s,%s,%s,">="&EDATE(%s,-2))/SUMIFS(%s,%s,">="&EDATE(%s,-2)),0)' % (R('addon_lines', 'first_line'), YES, R('addon_lines', 'month'), MS, R('funnel', 'bookings_all'), R('funnel', 'month'), MS)),
    O('Share of the target reached', 'pct', 'IFERROR(%s/{in:target},0)' % CUR7), O('Verdict', 'text', 'IF(%s>={in:target},%s,%s)' % (CUR7, kb('On target'), kb('Below target')))],
    GR('What if', ('Target 25', {'target': 25}), ('Target 35', {'target': 35}), ('Target 40', {'target': 40}), ('Target 50', {'target': 50}), ('1800 bookings', {'bookings': 1800}))))

# 8 ------------------------------------------------------------ young-driver and extra-driver price check
EXP8 = '({in:share}*{in:claim}+{in:days}*{set:young_damage_day})'
FEE8 = '({in:fee}*MIN({in:days},30))'
tools.append(TOOL('driver_fee_check', 'Driver Fee Check', 'Does the young-driver fee cover the extra cost',
    'Type the fee a day, the days, the share of rentals with a claim and the average claim amount; the fee is set against the extra cost of the segment.', [
    I('fee', 'Young-driver fee a day', 15), I('days', 'Days of the rental', 4, 'int'), I('share', 'Share of these rentals with a claim', 0.10, 'pct'), I('claim', 'Average claim amount', 380)], [
    O('Fee for the rental', 'money', 'ROUND(%s,2)' % FEE8), O('Extra wear and cleaning cost', 'money', 'ROUND({in:days}*{set:young_damage_day},2)'), O('Expected claim cost', 'money', 'ROUND({in:share}*{in:claim},2)'),
    O('Extra cost of the segment', 'money', 'ROUND(%s,2)' % EXP8), O('Fee over the extra cost', 'money', 'ROUND(%s-%s,2)' % (FEE8, EXP8)),
    O('Fee a day that covers the cost', 'money', 'ROUND(%s/MIN({in:days},30),2)' % EXP8), O('Raise the fee a day by', 'money', 'ROUND(MAX(0,%s/MIN({in:days},30)-{in:fee}),2)' % EXP8),
    O('Days of rental at which the fee covers', 'num', 'IFERROR(ROUNDUP({in:share}*{in:claim}/({in:fee}-{set:young_damage_day}),0),0)'),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (FEE8, EXP8, kb('Price covers'), kb('Raise the surcharge')))],
    GR('What if', ('One-day rental', {'days': 1}), ('Seven days', {'days': 7}), ('Claims 20%', {'share': 0.2}), ('Fee 20', {'fee': 20}), ('Average claim 600', {'claim': 600}))))

# 9 ------------------------------------------------------------ enquiry funnel conversion tool
def FS(col, a, b): return 'SUMIFS(%s,%s,">="&EDATE(%s,%s),%s,"<"&EDATE(%s,%s))' % (R('funnel', col), R('funnel', 'month'), MS, a, R('funnel', 'month'), MS, b)
EL, QL, BL, RL = FS('enquiries', -1, 0), FS('quoted', -1, 0), FS('booked', -1, 0), FS('avg_reply_hours', -1, 0)
EB, QB, BB = FS('enquiries', '-1-{in:months}', -1), FS('quoted', '-1-{in:months}', -1), FS('booked', '-1-{in:months}', -1)
RB = '(%s/{in:months})' % FS('avg_reply_hours', '-1-{in:months}', -1)
QR = '(IFERROR((%s/%s)/(%s/%s),1))' % (QL, EL, QB, EB); CR = '(IFERROR((%s/%s)/(%s/%s),1))' % (BL, QL, BB, QB); RR = '(IFERROR(%s/%s,1))' % (RB, RL)
tools.append(TOOL('funnel_tool', 'Funnel Conversion Tool', 'Which step of my enquiry funnel is weakest',
    'The last full month is set against your own average of the months before it: replying, quoting and closing; the weakest step is named.', [
    I('months', 'Months before it to average', 6, 'int')], [
    O('Enquiries, last full month', 'int', EL), O('Quoted, last full month', 'int', QL), O('Booked, last full month', 'int', BL), O('Average reply hours, last full month', 'num', 'ROUND(%s,2)' % RL),
    O('Enquiry to quote, last month', 'pct', 'IFERROR(%s/%s,0)' % (QL, EL)), O('Enquiry to quote, earlier months', 'pct', 'IFERROR(%s/%s,0)' % (QB, EB)),
    O('Quote to booking, last month', 'pct', 'IFERROR(%s/%s,0)' % (BL, QL)), O('Quote to booking, earlier months', 'pct', 'IFERROR(%s/%s,0)' % (BB, QB)),
    O('Enquiry to booking, last month', 'pct', 'IFERROR(%s/%s,0)' % (BL, EL)), O('Enquiry to booking, earlier months', 'pct', 'IFERROR(%s/%s,0)' % (BB, EB)),
    O('Reply hours, earlier months average', 'num', 'ROUND(%s,2)' % RB), O('Quoting against own history', 'pct', QR), O('Closing against own history', 'pct', CR), O('Replying against own history', 'pct', RR),
    O('Verdict', 'text', 'IF(AND(%s<=%s,%s<=%s),%s,IF(%s<=%s,%s,%s))' % (RR, QR, RR, CR, kc('Weakest step: reply'), QR, CR, kc('Weakest step: quote'), kc('Weakest step: close')))],
    GR('What if', ('Average the last 3 months', {'months': 3}), ('Average the last 9 months', {'months': 9}), ('Average the last 12 months', {'months': 12}), ('Average the last 2 months', {'months': 2}))))

# 10 ----------------------------------------------------------- lost-enquiry cause analyser
def LR(r): return 'SUMIFS(%s,%s,%s)' % (R('lost_reasons', 'revenue_lost'), R('lost_reasons', 'reason'), tok('lostreason', r))
REC = {'ra': ('No car free', 'win_car'), 'rb': ('Price', 'win_price'), 'rc': ('Dates', 'win_dates'), 'rd': ('No reply', 'win_reply'), 're': ('Other', 'win_other')}
def RC(i): r, v = REC[i]; return '(%s*{in:%s})' % (LR(r), v)
MX10 = 'MAX(%s)' % ','.join(RC(i) for i in REC)
tools.append(TOOL('lost_analyser', 'Lost Enquiry Analyser', 'Which lost-enquiry cause is worth fixing first',
    'The quote value lost in 90 days by cause is multiplied by the share you think you could win back; the cause with the most to win is named.', [
    I('win_car', 'Share you can win back: no car free', 0.25, 'pct'), I('win_price', 'Share you can win back: price', 0.30, 'pct'), I('win_dates', 'Share you can win back: dates', 0.15, 'pct'),
    I('win_reply', 'Share you can win back: no reply', 0.80, 'pct'), I('win_other', 'Share you can win back: other', 0.05, 'pct')], [
    O('Quote value lost, no car free', 'money', LR('No car free')), O('Quote value lost, price', 'money', LR('Price')), O('Quote value lost, dates', 'money', LR('Dates')), O('Quote value lost, no reply', 'money', LR('No reply')),
    O('Quote value lost, other', 'money', LR('Other')), O('Total quote value lost, 90 days', 'money', 'SUM(%s)' % R('lost_reasons', 'revenue_lost')),
    O('To win back: no car free', 'money', 'ROUND(%s,0)' % RC('ra')), O('To win back: price', 'money', 'ROUND(%s,0)' % RC('rb')), O('To win back: dates', 'money', 'ROUND(%s,0)' % RC('rc')),
    O('To win back: no reply', 'money', 'ROUND(%s,0)' % RC('rd')), O('To win back: other', 'money', 'ROUND(%s,0)' % RC('re')), O('Most to win back', 'money', 'ROUND(%s,0)' % MX10),
    O('Verdict', 'text', 'IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s))))' % (RC('ra'), MX10, kc('Fix availability'), RC('rb'), MX10, kc('Fix price'), RC('rc'), MX10, kc('Fix dates'), RC('rd'), MX10, kc('Fix replies'), kc('Fix other reasons')))],
    GR('What if', ('Price talks win 60% back', {'win_price': 0.6}), ('Replies win 50% back', {'win_reply': 0.5}), ('Extra car wins 60% back', {'win_car': 0.6}), ('Nothing wins back', {'win_car': 0, 'win_price': 0, 'win_dates': 0, 'win_reply': 0, 'win_other': 0.01}))))

# 11 ----------------------------------------------------------- reply-time impact
REP = '%s,"<>"&%s' % (R('enquiries', 'status'), OPEN)
F11 = 'COUNTIFS(%s,"<="&{in:hours},%s,%s)' % (R('enquiries', 'first_reply_hours'), REP, D90)
FB11 = 'COUNTIFS(%s,"<="&{in:hours},%s,%s,%s,%s)' % (R('enquiries', 'first_reply_hours'), REP, R('enquiries', 'status'), BOOKED, D90)
T11 = 'COUNTIFS(%s,%s)' % (REP, D90); TB11 = 'COUNTIFS(%s,%s,%s,%s)' % (R('enquiries', 'status'), BOOKED, D90, '%s,"<>"' % R('enquiries', 'first_reply_hours'))
CF11 = 'IFERROR(%s/%s,0)' % (FB11, F11); CS11 = 'IFERROR((%s-%s)/(%s-%s),0)' % (TB11, FB11, T11, F11)
LOST11 = 'ROUND(MAX(0,%s-%s)*(%s-%s)*{in:periods},0)' % (CF11, CS11, T11, F11)
tools.append(TOOL('reply_impact', 'Reply Time Impact', 'How many bookings do slow replies cost me',
    'Type the hours you aim to reply within; conversion of fast and slow replies in the last 90 days gives the bookings a year lost to slow replies.', [
    I('hours', 'Reply within hours', 4, 'int'), I('periods', '90-day periods in a year', 4.05, 'num')], [
    O('Replied enquiries, 90 days', 'int', T11), O('Replied within the target', 'int', F11), O('Replied slower than the target', 'int', '%s-%s' % (T11, F11)), O('Share replied slower', 'pct', 'IFERROR((%s-%s)/%s,0)' % (T11, F11, T11)),
    O('Conversion of fast replies', 'pct', CF11), O('Conversion of slow replies', 'pct', CS11), O('Conversion gap in points', 'pct', '%s-%s' % (CF11, CS11)),
    O('Bookings lost to slow replies, 90 days', 'int', 'ROUND(MAX(0,%s-%s)*(%s-%s),0)' % (CF11, CS11, T11, F11)), O('Bookings lost a year to slow replies', 'int', LOST11),
    O('Revenue lost a year, at your average quote', 'money', 'ROUND(%s*IFERROR(AVERAGEIFS(%s,%s,">0",%s),0),0)' % (LOST11, R('enquiries', 'quote_amount'), R('enquiries', 'quote_amount'), D90)),
    O('Verdict', 'text', 'IF(AND((%s-%s)/%s>0.1,%s-%s>0.02),%s,%s)' % (T11, F11, T11, CF11, CS11, kc('Reply sooner'), kc('Reply time on target')))],
    GR('What if', ('Reply within 1 hour', {'hours': 1}), ('Reply within 2 hours', {'hours': 2}), ('Reply within 8 hours', {'hours': 8}), ('Reply within 24 hours', {'hours': 24}))))

# 12 ----------------------------------------------------------- source conversion ranker
SRC = [('Website', 'a'), ('Phone', 'b'), ('Corporate account', 'c'), ('Hotel partner', 'd')]
def S_N(s): return 'COUNTIFS(%s,%s,%s)' % (R('enquiries', 'source'), tok('source', s), D90)
def S_B(s): return 'COUNTIFS(%s,%s,%s,%s,%s)' % (R('enquiries', 'source'), tok('source', s), R('enquiries', 'status'), BOOKED, D90)
def S_V(s): return 'SUMIFS(%s,%s,%s,%s,%s,%s)' % (R('enquiries', 'quote_amount'), R('enquiries', 'source'), tok('source', s), R('enquiries', 'status'), BOOKED, D90)
def S_Y(s): return '(%s*{in:periods})' % S_V(s)
MXY = 'MAX(%s)' % ','.join(S_Y(s) for s, _ in SRC)
def S_VER(s): return 'IF(%s=%s,%s,IF(IFERROR(%s/%s,0)<{in:cut_below},%s,%s))' % (S_Y(s), MXY, kc('Feed'), S_V(s), S_N(s), kc('Cut'), kc('Hold source'))
BEST12 = 'INDEX({list:source.website},1)'
def NAME12(): return 'IF(%s=%s,{list:source.website},IF(%s=%s,{list:source.phone},IF(%s=%s,{list:source.corporate_account},{list:source.hotel_partner})))' % (S_Y('Website'), MXY, S_Y('Phone'), MXY, S_Y('Corporate account'), MXY)
tools.append(TOOL('source_ranker', 'Source Ranker', 'Which source should I feed, hold or cut',
    'Each source is ranked by yearly booked quote value, not by counts; revenue per enquiry against your cut-off sets feed, hold or cut.', [
    I('cut_below', 'Cut a source below this revenue per enquiry', 230), I('periods', '90-day periods in a year', 4.05, 'num')], [
    O('Website, yearly booked value', 'money', 'ROUND(%s,0)' % S_Y('Website')), O('Website, value per enquiry', 'money', 'ROUND(IFERROR(%s/%s,0),2)' % (S_V('Website'), S_N('Website'))), O('Website', 'text', S_VER('Website')),
    O('Phone, yearly booked value', 'money', 'ROUND(%s,0)' % S_Y('Phone')), O('Phone, value per enquiry', 'money', 'ROUND(IFERROR(%s/%s,0),2)' % (S_V('Phone'), S_N('Phone'))), O('Phone', 'text', S_VER('Phone')),
    O('Corporate account, yearly booked value', 'money', 'ROUND(%s,0)' % S_Y('Corporate account')), O('Corporate account, value per enquiry', 'money', 'ROUND(IFERROR(%s/%s,0),2)' % (S_V('Corporate account'), S_N('Corporate account'))),
    O('Corporate account', 'text', S_VER('Corporate account')), O('Hotel partner, yearly booked value', 'money', 'ROUND(%s,0)' % S_Y('Hotel partner')),
    O('Hotel partner, value per enquiry', 'money', 'ROUND(IFERROR(%s/%s,0),2)' % (S_V('Hotel partner'), S_N('Hotel partner'))), O('Hotel partner', 'text', S_VER('Hotel partner')),
    O('Best source by yearly value', 'text', NAME12()), O('Yearly booked value of the best', 'money', 'ROUND(%s,0)' % MXY),
    O('Enquiries from all four sources, 90 days', 'int', 'COUNTIFS(%s)' % D90), O('Verdict for the best source', 'text', kc('Feed'))],
    GR('What if', ('Cut-off 150', {'cut_below': 150}), ('Cut-off 300', {'cut_below': 300}), ('Cut-off 350', {'cut_below': 350}), ('Cut-off 100', {'cut_below': 100}))))

# 13 ----------------------------------------------------------- quote follow-up list
SC13 = R('open_quotes', 'score')
def NTH13(k, col): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (R('open_quotes', col), SC13, k, SC13)
tools.append(TOOL('followup_list', 'Quote Follow-up List', 'Which open quote do I chase first',
    'Open quotes are ranked by value after a decay for each day they wait; the top three are named and the value of the first few you can call today is added.', [
    I('top_n', 'Quotes you can call today', 5, 'int')], [
    O('Open quotes on the list', 'int', 'COUNT(%s)' % SC13), O('Value of the open quotes', 'money', 'SUM(%s)' % R('open_quotes', 'quote_amount')), O('Chase first', 'text', NTH13(1, 'enquiry')),
    O('Contact of the first', 'text', NTH13(1, 'contact')), O('Class of the first', 'text', NTH13(1, 'class')), O('Quote amount of the first', 'money', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0)),0)' % (R('open_quotes', 'quote_amount'), SC13, SC13)),
    O('Chase second', 'text', NTH13(2, 'enquiry')), O('Contact of the second', 'text', NTH13(2, 'contact')), O('Chase third', 'text', NTH13(3, 'enquiry')), O('Contact of the third', 'text', NTH13(3, 'contact')),
    O('Value after decay of the calls you can make today', 'money', 'IFERROR(SUMIFS(%s,%s,">="&LARGE(%s,MIN({in:top_n},COUNT(%s)))),0)' % (SC13, SC13, SC13, SC13)),
    O('Quote amount of those calls', 'money', 'IFERROR(SUMIFS(%s,%s,">="&LARGE(%s,MIN({in:top_n},COUNT(%s)))),0)' % (R('open_quotes', 'quote_amount'), SC13, SC13, SC13)),
    O('Quotes waiting 3 days or more', 'int', 'COUNTIFS(%s,">=3")' % R('open_quotes', 'days_waiting')),
    O('Verdict', 'text', 'IF(COUNT(%s)=0,%s,%s)' % (SC13, kc('No open quotes'), kc('Chase this quote first')))],
    GR('What if', ('Call 3 quotes', {'top_n': 3}), ('Call 8 quotes', {'top_n': 8}), ('Call 12 quotes', {'top_n': 12}), ('Call 1 quote', {'top_n': 1}))))

# 14 ----------------------------------------------------------- price match test
ACH14 = 'IFERROR(SUMIFS(%s,%s,{in:cls},%s,%s)/SUMIFS(%s,%s,{in:cls},%s,%s),0)' % (R('enquiries', 'quote_amount'), R('enquiries', 'class'), R('enquiries', 'status'), BOOKED, R('enquiries', 'days'), R('enquiries', 'class'), R('enquiries', 'status'), BOOKED)
tools.append(TOOL('price_match', 'Price Match Test', 'Do I match this rival price',
    'Type a rival price a day for a class; it is set against your floor price, your rate and what booked quotes of the class paid a day.', [
    IL('cls', 'Class', 'class', 'Midsize SUV'), I('rival', 'Rival price a day', 70), I('days', 'Days of the rental', 3, 'int')], [
    O('Your daily rate', 'money', CLS_RATE('{in:cls}')), O('Floor price a day', 'money', FLOOR('{in:cls}')), O('Paid a day on booked quotes of the class', 'money', 'ROUND(%s,2)' % ACH14),
    O('Rival price over the floor', 'money', 'ROUND({in:rival}-%s,2)' % FLOOR('{in:cls}')), O('Rival price against your rate', 'pct', 'IFERROR({in:rival}/%s-1,0)' % CLS_RATE('{in:cls}')),
    O('Price you would give for the stay', 'money', 'ROUND(MAX({in:rival},%s)*{in:days},2)' % FLOOR('{in:cls}')), O('Revenue you give away for the stay', 'money', 'ROUND(MAX(0,%s-MAX({in:rival},%s))*{in:days},2)' % (CLS_RATE('{in:cls}'), FLOOR('{in:cls}'))),
    O('Extra rented days to keep the same revenue', 'num', 'IFERROR({in:days}*(%s/MAX({in:rival},%s)-1),0)' % (CLS_RATE('{in:cls}'), FLOOR('{in:cls}'))),
    O('Price a day to offer', 'money', 'ROUND(IF({in:rival}<%s,%s,MIN({in:rival},%s)),2)' % (FLOOR('{in:cls}'), FLOOR('{in:cls}'), CLS_RATE('{in:cls}'))),
    O('Verdict', 'text', 'IF({in:rival}<%s,%s,IF({in:rival}>=%s,%s,%s))' % (FLOOR('{in:cls}'), kb('Decline'), CLS_RATE('{in:cls}'), kb('Hold'), kb('Match')))],
    GR('What if', ('Rival at 40', {'rival': 40}), ('Rival at 78', {'rival': 78}), ('Electric class, rival 85', {'cls': '=' + CT('Electric'), 'rival': 85}), ('Economy, rival 36', {'cls': '=' + CT('Economy'), 'rival': 36}),
       ('Premium, rival 110', {'cls': '=' + CT('Premium'), 'rival': 110}))))

# 15 ----------------------------------------------------------- rate rise planner
LY15 = 'SUMIFS(%s,%s,{in:cls},%s,%s)' % (R('rates', 'last_year_rate'), R('rates', 'class'), R('rates', 'plan'), DAILY)
NEED15 = 'MAX(0,%s*(1+{in:target})/%s-1)' % (COSTD('{in:cls}'), CLS_RATE('{in:cls}'))
tools.append(TOOL('rise_planner', 'Rate Rise Planner', 'Do I raise the rate now or later',
    'Pick a class and the margin you want over cost; the rise needed, what waiting costs each month and the date of your planned rise are shown.', [
    IL('cls', 'Class', 'class', 'Electric'), I('target', 'Margin you want over cost', 0.10, 'pct'), I('rented', 'Rented days a year of the class', 800, 'int')], [
    O('Daily rate now', 'money', CLS_RATE('{in:cls}')), O('Daily rate last year', 'money', LY15), O('Rise this year', 'pct', 'IFERROR(%s/%s-1,0)' % (CLS_RATE('{in:cls}'), LY15)),
    O('Cost per rented day', 'money', COSTD('{in:cls}')), O('Rate that restores your margin', 'money', 'ROUND(%s*(1+{in:target}),2)' % COSTD('{in:cls}')), O('Rise needed', 'pct', NEED15),
    O('Revenue given away each month of waiting', 'money', 'ROUND(%s*%s*{in:rented}/12,0)' % (NEED15, CLS_RATE('{in:cls}'))), O('Revenue given away until the planned rise', 'money', 'ROUND(%s*%s*{in:rented}/12*MAX(0,({set:rise_date}-{today})/30),0)' % (NEED15, CLS_RATE('{in:cls}'))),
    O('Planned rise', 'pct', '{set:planned_rise}'), O('Planned rise starts on', 'date', '{set:rise_date}'), O('Days until the planned rise', 'int', 'MAX(0,{set:rise_date}-{today})'),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s>{set:planned_rise},%s,%s))' % (NEED15, kb('No rise needed'), NEED15, kb('Rise now'), kb('Rise at the set date')))],
    GR('What if', ('Premium class', {'cls': '=' + CT('Premium')}), ('Economy class', {'cls': '=' + CT('Economy')}), ('Margin 20%', {'target': 0.2}), ('Margin 5%', {'target': 0.05}), ('Van class', {'cls': '=' + CT('7-seat Van'), 'rented': 400}))))

# 16 ----------------------------------------------------------- long-hire quote
MP16 = 'ROUND(%s/30*{in:days},2)' % PLAN_RATE('{in:cls}', MONTHLY)
FT16 = 'ROUND(%s*{in:days},2)' % FLOOR('{in:cls}')
tools.append(TOOL('longhire_quote', 'Long-hire Quote', 'Do I offer the monthly plan at this price',
    'Pick a class, the days and the miles a renter expects; the monthly plan price, the discount against daily rentals, extra-mile fees and the floor check appear.', [
    IL('cls', 'Class', 'class', 'Compact'), I('days', 'Days of the hire', 45, 'int'), I('miles', 'Miles a day the renter expects', 140, 'int'), I('incl', 'Miles a day included in the plan', 120, 'int')], [
    O('Monthly plan price a day', 'money', 'ROUND(%s/30,2)' % PLAN_RATE('{in:cls}', MONTHLY)), O('Plan price for the hire', 'money', MP16), O('Same days at the daily rate', 'money', 'ROUND(%s*{in:days},2)' % CLS_RATE('{in:cls}')),
    O('Discount against daily rentals', 'pct', 'IFERROR(1-%s/(%s*{in:days}),0)' % (MP16, CLS_RATE('{in:cls}'))), O('Floor price for the hire', 'money', FT16),
    O('Extra miles the renter will drive', 'int', 'MAX(0,{in:miles}-{in:incl})*{in:days}'), O('Extra-mile fees expected', 'money', 'ROUND(MAX(0,{in:miles}-{in:incl})*{in:days}*{set:extra_mile_fee},2)'),
    O('Plan price with the extra-mile fees', 'money', 'ROUND(%s+MAX(0,{in:miles}-{in:incl})*{in:days}*{set:extra_mile_fee},2)' % MP16), O('Margin over the floor', 'money', 'ROUND(%s-%s,2)' % (MP16, FT16)),
    O('Price to counter at', 'money', 'MAX(%s,%s)' % (MP16, FT16)), O('Counter price a day', 'money', 'ROUND(MAX(%s,%s)/{in:days},2)' % (MP16, FT16)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (MP16, FT16, kb('Offer'), kb('Counter at the floor')))],
    GR('What if', ('Midsize SUV', {'cls': '=' + CT('Midsize SUV')}), ('Premium', {'cls': '=' + CT('Premium')}), ('Economy', {'cls': '=' + CT('Economy')}), ('Sixty days', {'days': 60}), ('Light driver, 90 miles', {'miles': 90}))))

# 17 ----------------------------------------------------------- minimum rental days solver
H17 = '({set:prep_cost}+{in:clean_share}*{set:cleaning_fee}+{in:deliv_share}*2*AVERAGEIFS(%s,%s,">0")/60*{in:driver_rate})' % (R('zones', 'run_minutes'), R('zones', 'run_minutes'))
M17 = '(%s-{in:var_cost})' % CLS_RATE('{in:cls}')
def MD17(f): return 'IF(%s*%s<=0,99,ROUNDUP(%s/(%s*%s),0))' % (M17, f, H17, M17, f)
tools.append(TOOL('min_days', 'Minimum Days Solver', 'Should I accept one-day rentals',
    'Type the share of pickups with a delivery and a cleaning and the cost of a rented day; the days a rental must last to cover the work of the pickup are solved.', [
    IL('cls', 'Class', 'class', 'Economy'), I('clean_share', 'Share of rentals needing extra cleaning', 0.5, 'pct'), I('deliv_share', 'Share of pickups delivered', 0.4, 'pct'),
    I('driver_rate', 'Driver pay an hour', 16), I('var_cost', 'Cost of one rented day (energy, upkeep)', 12)], [
    O('Daily rate of the class', 'money', CLS_RATE('{in:cls}')), O('Preparation and cleaning cost of a pickup', 'money', 'ROUND({set:prep_cost}+{in:clean_share}*{set:cleaning_fee},2)'),
    O('Delivery driver cost of a pickup', 'money', 'ROUND({in:deliv_share}*2*AVERAGEIFS(%s,%s,">0")/60*{in:driver_rate},2)' % (R('zones', 'run_minutes'), R('zones', 'run_minutes'))),
    O('Cost of handling one rental', 'money', 'ROUND(%s,2)' % H17), O('Margin of one rented day', 'money', 'ROUND(%s,2)' % M17), O('Days that cover the handling cost', 'num', 'IFERROR(ROUND(%s/%s,2),0)' % (H17, M17)),
    O('Minimum days to set', 'int', MD17('1')), O('Minimum days if the rate falls 20%', 'int', MD17('0.8')), O('Minimum days if the rate falls 10%', 'int', MD17('0.9')),
    O('Minimum days if the rate rises 10%', 'int', MD17('1.1')), O('Minimum days if the rate rises 20%', 'int', MD17('1.2')),
    O('Verdict', 'text', 'IF(%s<=1,%s,%s)' % (MD17('1'), kb('Accept 1-day rentals'), kb('Set a minimum stay')))],
    GR('What if', ('Premium class', {'cls': '=' + CT('Premium'), 'var_cost': 25}), ('Everything delivered', {'deliv_share': 1}), ('No delivery or cleaning', {'deliv_share': 0, 'clean_share': 0}), ('Van class', {'cls': '=' + CT('7-seat Van'), 'var_cost': 20}),
       ('High upkeep', {'var_cost': 32}))))

# 18 ----------------------------------------------------------- four-week quote forecast
def FV18(c, m): return 'SUMIFS(%s,%s,%s)' % (R('funnel', c), R('funnel', 'month'), m)
E3 = '(3*%s)' % FV18('enq_avg3', MS)
TR18 = FV18('trend', 'EDATE(%s,-1)' % MS)
CV18 = FV18('conv_avg3', MS)
AQ18 = FV18('quote_avg3', MS)
SC18 = 'IF({in:scen}=%s,1+{in:best},IF({in:scen}=%s,1-{in:worst},1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
WK18 = '(%s/3/4.33*%s*%s)' % (E3, TR18, SC18)
def BK(k): return '(%s*%s*(1+(%s-1)*%d/4))' % (WK18, CV18, TR18, k)
tools.append(TOOL('forecast4', 'Four-Week Forecast', 'How many bookings and how much revenue in four weeks',
    'Enquiries and conversion of the last three full months, a trend factor and a Base, Best or Worst switch give bookings and revenue per week and a capacity check.', [
    IL('scen', 'Scenario', 'scen', 'Base'), I('best', 'Best case change', 0.10, 'pct'), I('worst', 'Worst case change', 0.15, 'pct'), I('cars', 'Cars you can rent out', 26, 'int'), I('avg_days', 'Average days of a rental', 3.9, 'num')], [
    O('Enquiries a week from your own history', 'num', 'ROUND(%s/3/4.33,1)' % E3), O('Trend factor, last month against the 3-month average', 'num', 'ROUND(%s,2)' % TR18), O('Enquiry to booking conversion, 3 months', 'pct', CV18),
    O('Average quote, 3 months', 'money', 'ROUND(%s,2)' % AQ18), O('Bookings, week 1', 'num', 'ROUND(%s,1)' % BK(1)), O('Bookings, week 2', 'num', 'ROUND(%s,1)' % BK(2)), O('Bookings, week 3', 'num', 'ROUND(%s,1)' % BK(3)), O('Bookings, week 4', 'num', 'ROUND(%s,1)' % BK(4)),
    O('Revenue, week 1', 'money', 'ROUND(%s*%s,0)' % (BK(1), AQ18)), O('Revenue, week 2', 'money', 'ROUND(%s*%s,0)' % (BK(2), AQ18)), O('Revenue, week 3', 'money', 'ROUND(%s*%s,0)' % (BK(3), AQ18)), O('Revenue, week 4', 'money', 'ROUND(%s*%s,0)' % (BK(4), AQ18)),
    O('Bookings in four weeks', 'num', 'ROUND(%s+%s+%s+%s,1)' % (BK(1), BK(2), BK(3), BK(4))), O('Revenue in four weeks', 'money', 'ROUND((%s+%s+%s+%s)*%s,0)' % (BK(1), BK(2), BK(3), BK(4), AQ18)),
    O('Car-days these bookings need', 'int', 'ROUND((%s+%s+%s+%s)*{in:avg_days},0)' % (BK(1), BK(2), BK(3), BK(4))), O('Car-days you can fill at your planned utilisation', 'int', 'ROUND({in:cars}*28*{set:util_target},0)'),
    O('Verdict', 'text', 'IF((%s+%s+%s+%s)*{in:avg_days}>{in:cars}*28*{set:util_target},%s,%s)' % (BK(1), BK(2), BK(3), BK(4), kb('Capacity short'), kb('Enough cars')))],
    GR('What if', ('Best case', {'scen': '=' + tok('scen', 'Best')}), ('Worst case', {'scen': '=' + tok('scen', 'Worst')}), ('Twenty cars', {'cars': 20}), ('Longer rentals, 6 days', {'avg_days': 6}), ('Best case, 18 cars', {'scen': '=' + tok('scen', 'Best'), 'cars': 18}))))
assert len(tools) == 18
