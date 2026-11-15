"""Short-term rental host suite part 7: the 14 calculators."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr7_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
NET1 = '({in:rev}-{in:fees})'; MF1 = 'ROUND({in:pct}*(%s),2)' % NET1; COST1 = '({in:clean}+{in:sup}+{in:maint}+{in:util})'; NET_OWN1 = '(%s-%s-%s)' % (NET1, COST1, MF1)
FN2 = '({in:pct}*({in:rev}-{in:fees}))'; FG2 = '({in:pct}*{in:rev})'; USE2 = 'IF({in:basis}=2,%s,%s)' % (FG2, FN2); CH2 = 'MAX(%s,{in:minfee}*{in:units})' % USE2
FEE3 = '({in:net}*{in:pct})'; AVGM3 = 'AVERAGE({range:cohost_fees.fee_per_message})'
COST4 = '({in:stays}*({in:clean}+{in:sup})+{in:util}+{in:maint})'; FEES4 = '({in:earned}*{in:feepct})'; MF4 = '(({in:earned}-%s)*{in:mpct})' % FEES4; NET4 = '({in:earned}-%s-%s-%s)' % (FEES4, COST4, MF4)
SEND5 = 'DATE(YEAR({today}),MONTH({today})+1,{in:sday})'; PAY5 = 'DATE(YEAR({today}),MONTH({today})+1,{in:pday})'; TOT5 = '({in:n1}+{in:n2}+{in:n3})'
TARGET6 = '(({in:costs}+{in:maint})*{in:months})'
PCT7 = 'IFERROR(INDEX({range:cities.tax_pct},MATCH({in:city},{range:cities.city},0)),0)'; DUE7 = '({in:rev}*%s)' % PCT7; PLAT7 = '(%s*{in:plat})' % DUE7; HOST7 = '(%s-%s+{in:adj})' % (DUE7, PLAT7)
THIS8 = 'DATE(YEAR({today}),MONTH({today}),{in:dday})'; ISTHIS8 = 'AND({in:filed}=0,%s>={today})' % THIS8
NEXT8 = 'IF(%s,%s,DATE(YEAR({today}),MONTH({today})+1,{in:dday}))' % (ISTHIS8, THIS8)
AFT8 = 'DATE(YEAR(%s),MONTH(%s)+1,{in:dday})' % (NEXT8, NEXT8)
EXP9 = '({in:rev}*{in:pct})'
CH10 = '({in:clean}+{in:sets}*{in:setcost})'; COST10 = '({in:sets}*{in:setcost}+{set:cleaner_rate}*1.5)'
BAND11 = 'IF({in:units}>=7,4,IF({in:units}>=4,3,IF({in:units}>=2,2,1)))'; ROW11 = '(({in:pkg}-1)*4+%s)' % BAND11; PCT11 = 'INDEX({range:tiers.fee_pct},%s)' % ROW11
RET12 = '({in:net}/{in:value})'
NETN13 = '({in:rev1}-{in:fee1}-{in:cost1}-ROUND({in:pct}*({in:rev1}-{in:fee1}),2))'; NETP13 = '({in:rev0}-{in:fee0}-{in:cost0}-ROUND({in:pct}*({in:rev0}-{in:fee0}),2))'
HF14 = '({in:pct}*({in:rev}-{in:fees}))'; NT14 = '({in:rev}-{in:fees}-{in:costs}-%s)' % HF14

tools = [
    TOOL('statement_builder', 'Owner Statement Builder', 'Net to owner and host fee for one month',
         'Type the revenue, platform fees, cleaning, supplies, maintenance, utilities and the management percent; see the management fee, the net to the owner, the margin and whether it clears your floor.', [
        I('rev', 'Revenue of the month', 6200), I('fees', 'Platform fees', 820), I('clean', 'Cleaning costs', 540), I('sup', 'Supplies', 95), I('maint', 'Maintenance', 210), I('util', 'Utilities', 330), I('pct', 'Management percent', 0.20, 'pct')], [
        O('Revenue after platform fees', 'money', NET1), O('Management fee, the host earns', 'money', MF1), O('Cleaning, supplies, maintenance and utilities', 'money', COST1), O('Net to the owner', 'money', NET_OWN1),
        O('Net to owner as a share of revenue', 'pct', 'IFERROR(%s/{in:rev},0)' % NET_OWN1), O('Costs and platform fees as a share of revenue', 'pct', 'IFERROR(({in:fees}+%s)/{in:rev},0)' % COST1),
        O('Management fee as a share of revenue', 'pct', 'IFERROR(%s/{in:rev},0)' % MF1), O('Net to the owner against the floor', 'pct', 'IFERROR(%s/{in:rev},0)-{set:margin_floor}' % NET_OWN1),
        O('Verdict', 'text', 'IF(%s<0,%s,IF(IFERROR(%s/{in:rev},0)<{set:margin_floor},%s,%s))' % (NET_OWN1, ck2('Net is negative'), NET_OWN1, ck2('Margin below the floor'), ck2('Margin above the floor')))],
         GR('What if', ('Quiet month, revenue 2,400', {'rev': 2400, 'fees': 320, 'clean': 260}), ('Big repair, maintenance 900', {'maint': 900}), ('Management percent 18', {'pct': 0.18}), ('Busy month, revenue 9,800', {'rev': 9800, 'fees': 1290, 'clean': 790}), ('Utilities up, 520', {'util': 520}))),
    TOOL('mgmt_fee', 'Management Fee Calculator', 'Management fee on the net or on the gross revenue',
         'Type the revenue, the platform fees, the percent, the lowest fee for a unit and the basis (1 = net after platform fees, 2 = gross revenue); see both fees, the fee charged and the fee share.', [
        I('rev', 'Revenue of the month', 6200), I('fees', 'Platform fees', 820), I('pct', 'Management percent', 0.20, 'pct'), I('minfee', 'Lowest fee for one unit', 90), I('units', 'Units', 1, 'int'), I('basis', 'Basis, 1 = net, 2 = gross', 1, 'int')], [
        O('Fee on the net revenue', 'money', FN2), O('Fee on the gross revenue', 'money', FG2), O('Difference between the two bases', 'money', FG2 + '-' + FN2), O('Fee on the chosen basis', 'money', USE2),
        O('Lowest fee for these units', 'money', '{in:minfee}*{in:units}'), O('Fee charged', 'money', CH2), O('Fee charged as a share of revenue', 'pct', 'IFERROR(%s/{in:rev},0)' % CH2),
        O('Fee charged per unit', 'money', 'IFERROR(%s/{in:units},0)' % CH2),
        O('Verdict', 'text', 'IF(%s<{in:minfee}*{in:units},%s,IF({in:basis}=2,%s,%s))' % (USE2, ck2('Minimum fee applies'), ck2('Fee on the gross'), ck2('Fee on the net')))],
         GR('What if', ('Fee on the gross', {'basis': 2}), ('Quiet month, revenue 600', {'rev': 600, 'fees': 80}), ('Three units', {'units': 3, 'rev': 18000, 'fees': 2400}), ('Percent 15', {'pct': 0.15}), ('Percent 22', {'pct': 0.22}))),
    TOOL('cohost_fee_tool', 'Co-host Fee Calculator', 'Co-host fee on net revenue and cost per message',
         'Type the net revenue of the units the co-host handles, the fee percent, the units and the messages answered; see the fee, the fee per message and per unit and whether the cost per message is high.', [
        I('net', 'Net revenue after platform fees', 4026), I('pct', 'Co-host fee percent', 0.10, 'pct'), I('units', 'Units handled', 5, 'int'), I('msgs', 'Messages answered', 24, 'int')], [
        O('Co-host fee', 'money', FEE3), O('Fee at the percent in your settings', 'money', '{in:net}*{set:cohost_fee_pct}'), O('Difference from the settings percent', 'money', FEE3 + '-{in:net}*{set:cohost_fee_pct}'),
        O('Fee per message', 'money', 'IFERROR(%s/{in:msgs},0)' % FEE3), O('Fee per unit', 'money', 'IFERROR(%s/{in:units},0)' % FEE3), O('Average fee per message in your history', 'money', AVGM3),
        O('Fee per message against your history', 'pct', 'IFERROR(%s/{in:msgs}/%s-1,0)' % (FEE3, AVGM3)), O('Messages per unit', 'num', 'IFERROR({in:msgs}/{in:units},0)'),
        O('Verdict', 'text', 'IF(IFERROR(%s/{in:msgs},0)>1.3*%s,%s,%s)' % (FEE3, AVGM3, ck2('Fee per message is high'), ck2('Fee per message is fine')))],
         GR('What if', ('Few messages, 8', {'msgs': 8}), ('Busy month, 60 messages', {'msgs': 60, 'net': 6200}), ('Fee 12 percent', {'pct': 0.12}), ('Quiet month, net 1,800', {'net': 1800, 'msgs': 11}), ('Three units', {'units': 3, 'net': 2400, 'msgs': 14}))),
    TOOL('unit_net', 'Owner Net per Unit', 'Net to owner, margin and net per night for one unit',
         'Type nights, earned amount, fee percent, stays, costs and the management percent; see occupancy, ADR (average price of a night sold), RevPAR (revenue per available night) and the net.', [
        I('nights', 'Nights booked', 21, 'int'), I('avail', 'Nights available', 30, 'int'), I('earned', 'Earned amount', 3150), I('feepct', 'Platform fee percent', 0.14, 'pct'), I('stays', 'Stays', 7, 'int'), I('clean', 'Cleaning cost per stay', 62),
        I('sup', 'Supplies per stay', 9), I('util', 'Utilities and internet', 190), I('maint', 'Maintenance', 60), I('mpct', 'Management percent', 0.20, 'pct')], [
        O('Occupancy', 'pct', 'IFERROR({in:nights}/{in:avail},0)'), O('ADR, the average price of a night sold', 'money', 'IFERROR({in:earned}/{in:nights},0)'), O('RevPAR, revenue per available night', 'money', 'IFERROR({in:earned}/{in:avail},0)'),
        O('Platform fees', 'money', FEES4), O('Cleaning, supplies, utilities and maintenance', 'money', COST4), O('Management fee', 'money', MF4), O('Net to the owner', 'money', NET4),
        O('Net as a share of revenue', 'pct', 'IFERROR(%s/{in:earned},0)' % NET4), O('Net per booked night', 'money', 'IFERROR(%s/{in:nights},0)' % NET4), O('Net over a year at this pace', 'money', NET4 + '*12'),
        O('Verdict', 'text', 'IF(%s<0,%s,IF(IFERROR(%s/{in:earned},0)<{set:margin_floor},%s,%s))' % (NET4, ck2('Net is negative'), NET4, ck2('Margin below the floor'), ck2('Margin above the floor')))],
         GR('What if', ('Low occupancy, 11 nights', {'nights': 11, 'earned': 1500, 'stays': 4}), ('High occupancy, 27 nights', {'nights': 27, 'earned': 4300, 'stays': 8}), ('Utilities 320', {'util': 320}), ('Cleaning cost 90 a stay', {'clean': 90}), ('Platform fee 15 percent', {'feepct': 0.15}))),
    TOOL('pay_schedule', 'Owner Payment Schedule', 'Statement and payment dates and the cash needed',
         'Type the net to owner of three owners, the send day, the payment day and your cash; see the dates, the total needed and whether cash covers it.', [
        I('n1', 'Net to owner 1', 4739), I('n2', 'Net to owner 2', 5514), I('n3', 'Net to owner 3', 4855), I('sday', 'Day statements are sent', 5, 'int'), I('pday', 'Day owners are paid', 10, 'int'), I('cash', 'Cash you can use for owner payments', 14000)], [
        O('Statements are sent on', 'date', SEND5), O('Payments are due on', 'date', PAY5), O('First working day for the transfer', 'date', 'WORKDAY(%s-1,1)' % PAY5), O('Days between sending and payment', 'int', PAY5 + '-' + SEND5),
        O('Total to pay the owners', 'money', TOT5), O('Largest single payment', 'money', 'MAX({in:n1},{in:n2},{in:n3})'), O('Cash left after the payments', 'money', '{in:cash}-' + TOT5),
        O('Share of cash used', 'pct', 'IFERROR(%s/{in:cash},0)' % TOT5), O('Verdict', 'text', 'IF({in:cash}>=%s,%s,%s)' % (TOT5, ck2('Cash covers the payments'), ck2('Cash is short')))],
         GR('What if', ('Pay on the 15th', {'pday': 15}), ('Send on the 3rd', {'sday': 3}), ('Cash is 9,000', {'cash': 9000}), ('Strong month, owners earn more', {'n1': 7800, 'n2': 8100, 'n3': 6900}), ('Quiet month', {'n1': 1400, 'n2': 900, 'n3': 1300}))),
    TOOL('reserve_planner', 'Reserve and Float Planner', 'Repair reserve to hold for an owner',
         'Type the fixed costs and usual repairs of the unit, the safety months, the reserve held and the top-up; see the reserve to hold, the gap and the months to fill it.', [
        I('costs', 'Fixed costs per month, utilities and internet', 260), I('maint', 'Usual repair cost per month', 120), I('months', 'Months of safety', 2, 'num'), I('held', 'Reserve held now', 900), I('topup', 'Top-up per month', 100)], [
        O('Reserve to hold', 'money', TARGET6), O('Gap to the reserve to hold', 'money', 'MAX(0,%s-{in:held})' % TARGET6), O('Share of the reserve funded', 'pct', 'IFERROR(MIN(1,{in:held}/%s),0)' % TARGET6),
        O('Months to fill the gap at this top-up', 'int', 'IF({in:topup}>0,ROUNDUP(MAX(0,%s-{in:held})/{in:topup},0),0)' % TARGET6), O('Lowest reserve from your settings', 'money', '{set:reserve_min}'),
        O('Held now against the lowest reserve', 'money', '{in:held}-{set:reserve_min}'), O('Reserve with the safety months of your settings', 'money', '({in:costs}+{in:maint})*{set:reserve_months}'),
        O('Verdict', 'text', 'IF(AND({in:held}>=%s,{in:held}>={set:reserve_min}),%s,%s)' % (TARGET6, ck2('Reserve is enough'), ck2('Top up the reserve')))],
         GR('What if', ('Reserve 400', {'held': 400}), ('Three months of safety', {'months': 3}), ('Costly unit, repairs 300', {'maint': 300}), ('Top-up 250', {'topup': 250}), ('Reserve 1,600', {'held': 1600}))),
    TOOL('local_tax_tool', 'Local Tax Calculator', 'Local tax to remit and tax already paid by the platform',
         'Pick the city, type the room revenue, the share of the tax the platforms collect and remit themselves and any adjustment; see the tax due, what the platforms paid and what the host must remit.', [
        I('rev', 'Room revenue of the month', 7800), IN('city', 'City', 'list', key('city', 'Lisbon'), list='city'), I('plat', 'Share of the tax collected by the platforms', 0.55, 'pct'), I('adj', 'Adjustment, plus or minus', 0), I('nights', 'Nights', 52, 'int')], [
        O('Local tax percent of the city', 'pct', PCT7), O('Local tax due on the room revenue', 'money', DUE7), O('Tax already paid by the platforms', 'money', PLAT7), O('Tax the host must remit', 'money', HOST7),
        O('Tax per night', 'money', 'IFERROR(%s/{in:nights},0)' % DUE7), O('Host share of the tax', 'pct', 'IFERROR(%s/%s,0)' % (HOST7, DUE7)), O('Next due date from your settings', 'date', 'DATE(YEAR({today}),MONTH({today})+1,{set:tax_due_day})'),
        O('Verdict', 'text', 'IF(%s<=0.01,%s,%s)' % (HOST7, ck2('Tax already paid by the platform'), cb('Still to remit')))],
         GR('What if', ('Porto', {'city': '=' + tok('city', 'Porto')}), ('Sintra', {'city': '=' + tok('city', 'Sintra')}), ('Platforms collect everything', {'plat': 1.0}), ('Refund adjustment of 30', {'adj': -30}), ('Direct bookings only', {'plat': 0.0}))),
    TOOL('tax_calendar', 'Tax Due Calendar', 'Next local tax dates and amounts',
         'Type the due day, the tax to remit for the next three returns and whether this month\'s return is already filed; see the next due date, the days to go, the amount and the following date.', [
        I('dday', 'Due day of the month', 20, 'int'), I('a1', 'Tax to remit, return due this month', 1210), I('a2', 'Tax to remit, return after that', 1085), I('a3', 'Tax to remit, third return', 1320), I('filed', 'This month\'s return is filed, 1 = yes, 0 = no', 0, 'int')], [
        O('Next due date', 'date', NEXT8), O('Days to the next due date', 'int', NEXT8 + '-{today}'), O('Amount due on that date', 'money', 'IF(%s,{in:a1},{in:a2})' % ISTHIS8), O('Following due date', 'date', AFT8),
        O('Amount due on the following date', 'money', 'IF(%s,{in:a2},{in:a3})' % ISTHIS8), O('Total over the next three returns', 'money', '{in:a1}+{in:a2}+{in:a3}'), O('Weekday of the next due date, 1 = Monday', 'int', 'WEEKDAY(%s,2)' % NEXT8),
        O('Verdict', 'text', 'IF(%s-{today}<={set:warn_days},%s,%s)' % (NEXT8, ca('Due soon'), ca('Not yet due')))],
         GR('What if', ('Return already filed', {'filed': 1}), ('Due day the 28th', {'dday': 28}), ('Due day the 5th', {'dday': 5}), ('Larger returns', {'a1': 2400, 'a2': 2300, 'a3': 2600}), ('Small returns', {'a1': 400, 'a2': 380, 'a3': 420}))),
    TOOL('tax_check_tool', 'Local Tax Check', 'Difference to explain between tax collected and tax expected',
         'Type the nights, the room revenue, the tax collected and the city percent; see the tax you expect, the difference, the revenue the tax implies and whether the difference is worth chasing.', [
        I('nights', 'Nights', 52, 'int'), I('rev', 'Room revenue', 7800), I('coll', 'Tax collected', 462), I('pct', 'Tax percent', 0.06, 'pct')], [
        O('Tax expected on the room revenue', 'money', EXP9), O('Difference, collected less expected', 'money', '{in:coll}-' + EXP9), O('Difference as a share of the tax expected', 'pct', 'IFERROR(({in:coll}-%s)/%s,0)' % (EXP9, EXP9)),
        O('Revenue the tax collected implies', 'money', 'IFERROR({in:coll}/{in:pct},0)'), O('Revenue gap, implied less reported', 'money', 'IFERROR({in:coll}/{in:pct},0)-{in:rev}'), O('Tax expected per night', 'money', 'IFERROR(%s/{in:nights},0)' % EXP9),
        O('Tax collected per night', 'money', 'IFERROR({in:coll}/{in:nights},0)'), O('Difference allowed in your settings', 'money', '{set:tax_tolerance}'),
        O('Verdict', 'text', 'IF(ABS({in:coll}-%s)>{set:tax_tolerance},%s,%s)' % (EXP9, ck2('Difference to explain'), ck2('Tax matches')))],
         GR('What if', ('Collected 20 short', {'coll': 442}), ('Collected 35 over', {'coll': 497}), ('Percent 5', {'pct': 0.05, 'coll': 390}), ('Revenue 5,000', {'rev': 5000, 'coll': 300, 'nights': 34}), ('Collected exactly', {'coll': 468}))),
    TOOL('stay_charge', 'Owner Stay Charge', 'What an owner pays for their own stay',
         'Type the nights, the cleaning fee, the linen sets and their cost and the usual nightly price; see the total charged, the charge per night and the revenue the unit gives up.', [
        I('nights', 'Nights', 4, 'int'), I('clean', 'Cleaning fee of the unit', 60), I('sets', 'Linen sets used', 2, 'int'), I('setcost', 'Linen cost per set', 9), I('adr', 'Usual price of a night', 120), I('mpct', 'Management percent', 0.20, 'pct')], [
        O('Linen charge', 'money', '{in:sets}*{in:setcost}'), O('Total charged to the owner', 'money', CH10), O('Charge per night', 'money', 'IFERROR(%s/{in:nights},0)' % CH10), O('Revenue the unit would have earned', 'money', '{in:nights}*{in:adr}'),
        O('Management fee given up', 'money', '{in:nights}*{in:adr}*{in:mpct}'), O('Charge as a share of the revenue given up', 'pct', 'IFERROR(%s/({in:nights}*{in:adr}),0)' % CH10),
        O('Cost of the clean and the linen for the host', 'money', COST10), O('Margin on the charge', 'money', CH10 + '-' + COST10),
        O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (CH10, COST10, ck2('Owner pays for the stay'), ck2('Charge below cost')))],
         GR('What if', ('One night', {'nights': 1, 'sets': 1}), ('A week, 7 nights', {'nights': 7, 'sets': 3}), ('Large unit, cleaning 95', {'clean': 95, 'sets': 4}), ('Linen cost 15', {'setcost': 15}), ('Peak price 220', {'adr': 220}))),
    TOOL('tier_finder', 'Fee Tier Finder', 'Fee tier and percent for the units managed',
         'Type the units an owner brings, the package (1 = Basic, 2 = Standard, 3 = Full) and the percent charged now; the tier and its percent come from the Fee Tiers sheet.', [
        I('units', 'Units managed for the owner', 3, 'int'), I('pkg', 'Package, 1 = Basic, 2 = Standard, 3 = Full', 3, 'int'), I('cur', 'Percent charged now', 0.20, 'pct'), I('rev', 'Owner revenue after platform fees per month', 7500)], [
        O('Tier band, 1 to 4', 'int', BAND11), O('Tier', 'text', 'INDEX({range:tiers.tier},%s)' % ROW11), O('Fee percent of the tier', 'pct', PCT11), O('Percent charged now against the tier', 'pct', '{in:cur}-' + PCT11),
        O('Fee on the tier per month', 'money', '{in:rev}*' + PCT11), O('Fee charged now per month', 'money', '{in:rev}*{in:cur}'), O('Units to the next tier', 'int', 'IF(%s=4,0,INDEX({range:tiers.units_from},%s+1)-{in:units})' % (BAND11, ROW11)),
        O('Percent at the next tier', 'pct', 'IF(%s=4,%s,INDEX({range:tiers.fee_pct},%s+1))' % (BAND11, PCT11, ROW11)), O('Verdict', 'text', 'IF({in:cur}>%s+0.0001,%s,%s)' % (PCT11, ck2('Fee above the tier'), ck2('Fee on the tier')))],
         GR('What if', ('One unit', {'units': 1}), ('Four units', {'units': 4}), ('Seven units', {'units': 7}), ('Basic package', {'pkg': 1, 'cur': 0.14}), ('Standard package, 2 units', {'pkg': 2, 'units': 2, 'cur': 0.16}))),
    TOOL('owner_return', 'Owner Return on the Unit', 'Yearly return on the value of the unit',
         'Type the net to the owner over 12 months, the value of the unit and the return the owner wants; see the yearly return, the net needed, the gap and the years to earn the value back.', [
        I('net', 'Net to the owner, last 12 months', 21500), I('value', 'Value of the unit', 280000), I('want', 'Return the owner wants', 0.07, 'pct'), I('rev', 'Revenue of the unit, last 12 months', 42000)], [
        O('Yearly return on the value', 'pct', RET12), O('Net per month', 'money', '{in:net}/12'), O('Net needed for the return wanted', 'money', '{in:value}*{in:want}'), O('Gap to the net needed', 'money', '{in:net}-{in:value}*{in:want}'),
        O('Years to earn the value back', 'num', 'IFERROR({in:value}/{in:net},0)'), O('Net as a share of revenue', 'pct', 'IFERROR({in:net}/{in:rev},0)'), O('Revenue needed at this margin', 'money', 'IFERROR({in:value}*{in:want}/({in:net}/{in:rev}),0)'),
        O('Verdict', 'text', 'IF(%s>={in:want},%s,%s)' % (RET12, ck2('Return is above target'), ck2('Return is below target')))],
         GR('What if', ('Net 14,000', {'net': 14000}), ('Net 30,000', {'net': 30000}), ('Value 450,000', {'value': 450000}), ('Return wanted 5 percent', {'want': 0.05}), ('Weak year, net 6,000', {'net': 6000, 'rev': 21000}))),
    TOOL('statement_compare', 'Statement Comparison', 'What changed between this month and last month',
         'Type revenue, platform fees and costs for this month and last month and the management percent; see the change in net to the owner, in the costs and in the host fee.', [
        I('rev1', 'Revenue this month', 8200), I('fee1', 'Platform fees this month', 1050), I('cost1', 'Costs this month, cleaning, supplies, maintenance, utilities', 1820), I('rev0', 'Revenue last month', 7400),
        I('fee0', 'Platform fees last month', 950), I('cost0', 'Costs last month', 1210), I('pct', 'Management percent', 0.20, 'pct')], [
        O('Net to owner this month', 'money', NETN13), O('Net to owner last month', 'money', NETP13), O('Change in net', 'money', NETN13 + '-' + NETP13), O('Change in net, percent', 'pct', 'IFERROR(%s/%s-1,0)' % (NETN13, NETP13)),
        O('Change in revenue', 'money', '{in:rev1}-{in:rev0}'), O('Change in costs', 'money', '{in:cost1}-{in:cost0}'), O('Change in the host fee', 'money', 'ROUND({in:pct}*({in:rev1}-{in:fee1}),2)-ROUND({in:pct}*({in:rev0}-{in:fee0}),2)'),
        O('Net margin this month', 'pct', 'IFERROR(%s/{in:rev1},0)' % NETN13), O('Net margin last month', 'pct', 'IFERROR(%s/{in:rev0},0)' % NETP13),
        O('Net verdict', 'text', 'IF(%s>=%s,%s,%s)' % (NETN13, NETP13, ck2('Net rose'), ck2('Net fell'))), O('Cost verdict', 'text', 'IF({in:cost1}>{in:cost0},%s,%s)' % (ck2('Costs rose'), ck2('Costs fell')))],
         GR('What if', ('Costs the same as last month', {'cost1': 1210}), ('Revenue flat', {'rev1': 7400, 'fee1': 950}), ('Big repair, costs 3,000', {'cost1': 3000}), ('Revenue falls to 5,000', {'rev1': 5000, 'fee1': 650}), ('Percent 18', {'pct': 0.18}))),
    TOOL('fee_grid', 'Management Percent Grid', 'Host fee and net to owner for each management percent',
         'Type the revenue, the platform fees and the costs of a month; the grid tries management percents from 10 to 30 and shows the host fee, the net to the owner and the owner margin.', [
        I('rev', 'Revenue of the month', 6200), I('fees', 'Platform fees', 820), I('costs', 'Cleaning, supplies, maintenance and utilities', 1175), I('pct', 'Management percent', 0.20, 'pct')], [
        O('Host fee', 'money', HF14), O('Net to the owner', 'money', NT14), O('Owner margin', 'pct', 'IFERROR(%s/{in:rev},0)' % NT14), O('Host fee as a share of revenue', 'pct', 'IFERROR(%s/{in:rev},0)' % HF14),
        O('Host fee over a year at this level', 'money', HF14 + '*12'), O('Net to the owner over a year', 'money', NT14 + '*12'), O('Percent that leaves the owner exactly the margin floor', 'pct', 'IFERROR(MAX(0,({in:rev}-{in:fees}-{in:costs}-{set:margin_floor}*{in:rev})/({in:rev}-{in:fees})),0)')],
         GR('Management percent against host fee and net to owner', ('10 percent', {'pct': 0.10}), ('12 percent', {'pct': 0.12}), ('15 percent', {'pct': 0.15}), ('18 percent', {'pct': 0.18}), ('20 percent', {'pct': 0.20}), ('22 percent', {'pct': 0.22}), ('25 percent', {'pct': 0.25}), ('30 percent', {'pct': 0.30}))),
]
assert len(tools) == 14, len(tools)
