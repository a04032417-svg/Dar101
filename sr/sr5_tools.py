"""Short-term rental host suite part 5: the 14 calculators."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr5_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
YES = tok('yn', 'Yes'); NO = tok('yn', 'No')
PH, PN, PL = tok('prio', 'High'), tok('prio', 'Normal'), tok('prio', 'Low')

# 1 priority and due date
PRI1 = ('IF(OR({in:impact}=%s,{in:stay}=%s,{in:kind}=%s,{in:kind}=%s,{in:days}<={set:warn_days}),%s,IF(AND({in:days}>30,OR({in:kind}=%s,{in:kind}=%s,{in:kind}=%s)),%s,%s))'
        % (YES, YES, tok('tkind', 'Locks and keys'), tok('tkind', 'Electrical'), PH, tok('tkind', 'Furniture'), tok('tkind', 'Garden and exterior'), tok('tkind', 'Wi-Fi and TV'), PL, PN))
ALW1 = 'IF(%s=%s,{set:fix_days_high},IF(%s=%s,{set:fix_days_normal},{set:fix_days_low}))' % (PRI1, PH, PRI1, PN)
# 3 repair or replace
SH3 = '({in:repair}/{in:replace})'
# 4 claim builder
TOT4 = '({in:repair}+{in:hours}*{in:rate}+{in:nights}*{in:adr})'
# 12 guest impact
TOT12 = '({in:nights}*{in:adr}*(1-{in:fee})+{in:refund}+{in:credit}+{in:extra})'
# 14 spend grid
EX14 = '({in:spend}-{in:base})'
RA14 = 'MIN(5,{in:rating}+%s/100*{in:gain})' % EX14
NI14 = '{in:nights}*MAX(0,(%s-{in:rating})/0.1*{in:uplift})' % RA14

tools = [
    TOOL('priority_due', 'Ticket Priority and Due Date', 'Priority and fix-by date for a new ticket',
         'Type the kind of problem, the guest impact, whether a guest stays now and the days to the next check-in; see the priority, the days allowed, the fix-by date and when to start.', [
        IN('kind', 'Kind of problem', 'list', key('tkind', 'Plumbing'), list='tkind'), IN('impact', 'Guest affected now', 'list', key('yn', 'No'), list='yn'), IN('stay', 'A guest is staying now', 'list', key('yn', 'Yes'), list='yn'),
        I('days', 'Days to the next check-in', 9, 'int')], [
        O('Priority', 'text', PRI1), O('Days allowed to fix', 'int', ALW1), O('Fix-by date', 'date', '{today}+' + ALW1), O('Days left before the next check-in after the fix-by date', 'int', '{in:days}-' + ALW1),
        O('Last day to start for a one-day repair', 'date', '{today}+{in:days}-1'),
        O('Advice', 'text', 'IF({in:days}-%s<=1,%s,%s)' % (ALW1, ck2('Start now'), ck2('Start by the last safe day')))],
         GR('What if', ('Lock problem, guest arrives in 2 days', {'kind': '=' + tok('tkind', 'Locks and keys'), 'days': 2}), ('Garden fence, next check-in in 40 days', {'kind': '=' + tok('tkind', 'Garden and exterior'), 'days': 40, 'stay': '=' + NO}),
            ('Appliance, guest affected', {'kind': '=' + tok('tkind', 'Appliance'), 'impact': '=' + YES}), ('Pest control, empty unit', {'kind': '=' + tok('tkind', 'Pest control'), 'stay': '=' + NO, 'days': 14}), ('Next check-in in 3 days', {'days': 3}))),
    TOOL('workload', 'Handyperson Workload', 'Hours needed and spare capacity of a handyperson',
         'Type the open tickets, the hours each takes, the weekly capacity and the hours already booked; see the free hours, the weeks to clear the backlog and the cost of the hours.', [
        I('open', 'Open tickets', 7, 'int'), I('hpt', 'Hours per ticket', 2.5, 'num'), I('cap', 'Weekly capacity, hours', 24, 'int'), I('booked', 'Hours already booked this week', 15, 'int'), I('new', 'New tickets per week', 4, 'num'), I('rate', 'Hourly rate', 28)], [
        O('Hours needed for the open tickets', 'num', '{in:open}*{in:hpt}'), O('Free hours this week', 'num', 'MAX(0,{in:cap}-{in:booked})'), O('Load this week', 'pct', 'IFERROR({in:booked}/{in:cap},0)'),
        O('Hours the new tickets need each week', 'num', '{in:new}*{in:hpt}'), O('Free hours each week after the new tickets', 'num', '{in:cap}-{in:new}*{in:hpt}'),
        O('Weeks to clear the backlog', 'num', 'IF({in:cap}-{in:new}*{in:hpt}>0,{in:open}*{in:hpt}/({in:cap}-{in:new}*{in:hpt}),0)'), O('Labour cost of the open tickets', 'money', '{in:open}*{in:hpt}*{in:rate}'),
        O('Verdict', 'text', 'IF({in:cap}-{in:booked}>={in:hpt},%s,%s)' % (ck2('Handyperson has spare hours'), ck2('Handyperson is full')))],
         GR('What if', ('Ravi Menon, 24 hours', {'cap': 24, 'booked': 20}), ('Tariq Haddad, 18 hours', {'cap': 18, 'booked': 17}), ('Twelve open tickets', {'open': 12}), ('Longer jobs, 4 hours each', {'hpt': 4}), ('Quiet week', {'booked': 6, 'new': 2}))),
    TOOL('repair_replace', 'Repair or Replace', 'Repair or replace an appliance or furniture item',
         'Type the repair cost, the replacement cost, the age, the expected life, the repairs this year and the warranty left; see the cost of each choice per year and the cheaper choice.', [
        I('repair', 'Repair cost', 320), I('replace', 'Replacement cost', 780), I('age', 'Age in years', 6, 'num'), I('life', 'Expected life in years', 10, 'num'), I('extra', 'Years of life a repair adds', 2, 'num'),
        I('repairs', 'Repairs in the last 12 months', 2, 'int'), I('war', 'Warranty left, days', 0, 'int')], [
        O('Repair as a share of the replacement', 'pct', 'IFERROR(%s,0)' % SH3), O('Remaining life, years', 'num', 'MAX(0,{in:life}-{in:age})'), O('Cost per year of a new item', 'money', 'IFERROR({in:replace}/{in:life},0)'),
        O('Cost per extra year from the repair', 'money', 'IFERROR({in:repair}/{in:extra},0)'), O('Cost per year of the repair against a new item', 'money', 'IFERROR({in:repair}/{in:extra}-{in:replace}/{in:life},0)'),
        O('Warranty pays for the repair', 'money', 'IF({in:war}>0,{in:repair},0)'),
        O('Choice', 'text', 'IF({in:war}>0,%s,IF(%s>0.5,%s,IF(OR({in:repairs}>=3,{in:age}>=0.7*{in:life}),%s,%s)))' % (ck2('Repair it'), SH3, ck2('Replace it'), ck2('Repair now, plan a replacement'), ck2('Repair it')))],
         GR('What if', ('Old fridge, repair is 60 percent', {'repair': 470, 'replace': 780, 'age': 8}), ('Cheap repair on a young machine', {'repair': 90, 'age': 2}), ('Still in warranty', {'war': 200}), ('Third repair this year', {'repairs': 3, 'age': 5}), ('Sofa, replace for 1,200', {'replace': 1200, 'repair': 350, 'life': 7}))),
    TOOL('claim_builder', 'Damage Claim Builder', 'Amount to claim and the proof you need',
         'Type the repair cost, extra cleaning hours, nights lost, the deposit held and the channel; see the total to claim, the deposit used, the rest to claim and the proof items to collect.', [
        I('repair', 'Repair or replacement cost', 455), I('hours', 'Extra cleaning hours', 2, 'num'), I('rate', 'Cleaning cost per hour', 17), I('nights', 'Nights lost while repairing', 1, 'int'), I('adr', 'Average price of a night', 140),
        I('dep', 'Deposit held', 0), IN('chan', 'Booking channel', 'list', key('chan', 'Platform A'), list='chan')], [
        O('Repair cost to claim', 'money', '{in:repair}'), O('Extra cleaning to claim', 'money', '{in:hours}*{in:rate}'), O('Lost nights to claim', 'money', '{in:nights}*{in:adr}'), O('Total to claim', 'money', TOT4),
        O('Covered by the deposit', 'money', 'MIN({in:dep},%s)' % TOT4), O('Rest to claim after the deposit', 'money', 'MAX(0,%s-{in:dep})' % TOT4),
        O('Proof items to collect', 'int', '4+IF(%s>{set:repair_limit},2,0)+IF({in:chan}<>%s,1,0)' % (TOT4, tok('chan', 'Direct'))),
        O('Claim route', 'text', 'IF({in:dep}>=%s,%s,IF({in:dep}>0,%s,%s))' % (TOT4, ck2('Deposit covers the damage'), ck2('Claim the rest after the deposit'), ck2('Claim the full amount')))],
         GR('What if', ('Pending claim of 640, repair 455', {'repair': 455, 'nights': 1, 'hours': 4}), ('Direct booking with a deposit of 200', {'dep': 200, 'chan': '=' + tok('chan', 'Direct')}), ('Small damage, deposit covers it', {'repair': 80, 'hours': 0, 'nights': 0, 'dep': 200}),
            ('Two nights lost', {'nights': 2}), ('Party cleaning, 8 hours', {'hours': 8, 'repair': 120}))),
    TOOL('deposit_release', 'Deposit Release Check', 'Release or keep a damage deposit',
         'Type the deposit, the claim against it and the days since check-out; see how much to return, how much to keep and whether the release is overdue.', [
        I('dep', 'Deposit held', 250), I('claim', 'Damage found, amount', 0), I('days', 'Days since check-out', 3, 'int')], [
        O('Amount to keep', 'money', 'MIN({in:dep},{in:claim})'), O('Amount to return to the guest', 'money', '{in:dep}-MIN({in:dep},{in:claim})'), O('Damage above the deposit', 'money', 'MAX(0,{in:claim}-{in:dep})'),
        O('Days left to release', 'int', '{set:deposit_days}-{in:days}'), O('Days overdue', 'int', 'MAX(0,{in:days}-{set:deposit_days})'),
        O('Decision', 'text', 'IF({in:claim}<=0,%s,IF({in:claim}>={in:dep},%s,%s))' % (ck2('Release the deposit'), ck2('Keep the deposit'), ck2('Keep part of the deposit')))],
         GR('What if', ('No damage', {'claim': 0}), ('Damage of 90', {'claim': 90}), ('Damage above the deposit', {'claim': 400}), ('Ten days after check-out', {'days': 10}), ('Deposit of 150', {'dep': 150, 'claim': 40}))),
    TOOL('cost_night', 'Maintenance Cost per Night', 'Maintenance cost per booked night of a unit',
         'Type the maintenance cost, the nights booked and the average price of a night; see the cost per night, the share of revenue, the gap to your target and to the whole portfolio.', [
        I('cost', 'Maintenance cost, 12 months', 950), I('nights', 'Booked nights, 12 months', 240, 'int'), I('adr', 'Average price of a night', 140), I('stay', 'Average stay in nights', 3.2, 'num')], [
        O('Cost per booked night', 'money', 'IFERROR({in:cost}/{in:nights},0)'), O('Cost per stay', 'money', 'IFERROR({in:cost}/{in:nights}*{in:stay},0)'), O('Share of room revenue', 'pct', 'IFERROR({in:cost}/({in:nights}*{in:adr}),0)'),
        O('Wanted cost per night', 'money', '{set:cost_night_target}'), O('Gap to the wanted cost', 'money', 'IFERROR({in:cost}/{in:nights},0)-{set:cost_night_target}'),
        O('Portfolio cost per night', 'money', 'IFERROR(SUM({range:units.cost_12m})/SUM({range:units.nights_12m}),0)'), O('Cost above the target, in total', 'money', 'MAX(0,{in:cost}-{set:cost_night_target}*{in:nights})'),
        O('Verdict', 'text', 'IF(IFERROR({in:cost}/{in:nights},0)>{set:cost_night_target},%s,%s)' % (ck2('Cost per night is high'), ck2('Cost per night is fine')))],
         GR('What if', ('Studio with few repairs', {'cost': 420, 'nights': 260}), ('Old house with many repairs', {'cost': 1900, 'nights': 230}), ('Low occupancy year', {'nights': 150}), ('Longer stays of 5 nights', {'stay': 5}), ('Premium rate of 220', {'adr': 220}))),
    TOOL('service_planner', 'Preventive Service Planner', 'Next service date and yearly cost',
         'Type the cost of a service, how often it is done and when it was last done; see the next due date, the days left, the services a year and the yearly cost for one unit and for all.', [
        I('cost', 'Cost of one service', 120), I('every', 'Every how many months', 6, 'int'), I('since', 'Days since the last service', 150, 'int'), I('units', 'Units with this service', 12, 'int')], [
        O('Next due date', 'date', 'EDATE({today}-{in:since},{in:every})'), O('Days to the next service', 'int', 'EDATE({today}-{in:since},{in:every})-{today}'), O('Services per year', 'num', '12/{in:every}'),
        O('Yearly cost, one unit', 'money', '{in:cost}*12/{in:every}'), O('Yearly cost, all units', 'money', '{in:cost}*12/{in:every}*{in:units}'), O('Cost of a failure avoided at 4 times the service', 'money', '{in:cost}*4'),
        O('Status', 'text', 'IF(EDATE({today}-{in:since},{in:every})<{today},%s,IF(EDATE({today}-{in:since},{in:every})-{today}<={set:service_warn_days},%s,%s))' % (ck2('Overdue now'), ck2('Due soon'), ck2('Up to date')))],
         GR('What if', ('Done a year ago, every 12 months', {'every': 12, 'since': 365}), ('Done 20 days ago', {'since': 20}), ('Every 3 months', {'every': 3}), ('Only 5 units', {'units': 5}), ('Costly service of 260', {'cost': 260}))),
    TOOL('warranty_check', 'Warranty Check', 'Warranty cover left on an appliance',
         'Type the purchase date, the warranty months and the repair quote; see when the warranty ends, the days of cover left and whether the repair is covered.', [
        I('since', 'Days since it was bought', 500, 'int'), I('months', 'Warranty months', 24, 'int'), I('price', 'Purchase price', 480), I('quote', 'Repair quote', 260)], [
        O('Warranty ends on', 'date', 'EDATE({today}-{in:since},{in:months})'), O('Days of cover left', 'int', 'EDATE({today}-{in:since},{in:months})-{today}'), O('Months of cover left', 'num', 'MAX(0,(EDATE({today}-{in:since},{in:months})-{today})/30.4)'),
        O('Age in years', 'num', '{in:since}/365'), O('Repair cost covered by the warranty', 'money', 'IF(EDATE({today}-{in:since},{in:months})>={today},{in:quote},0)'),
        O('Repair as a share of the price', 'pct', 'IFERROR({in:quote}/{in:price},0)'), O('Status', 'text', 'IF(EDATE({today}-{in:since},{in:months})<{today},%s,%s)' % (ck2('Cover ended'), ck2('Cover left')))],
         GR('What if', ('Bought 2 years ago, 36 months', {'since': 730, 'months': 36}), ('Bought 3 months ago', {'since': 90}), ('5-year warranty', {'months': 60}), ('Quote of 90', {'quote': 90}), ('Expensive TV of 900', {'price': 900, 'quote': 400}))),
    TOOL('safety_due', 'Safety Check Due List', 'Next safety check and the time it takes',
         'Type the last check date, the months between checks, the units and the minutes a check takes; see the next date, the days left and the hours a year all the checks need.', [
        I('since', 'Days since the last check', 160, 'int'), I('every', 'Months between checks', 6, 'int'), I('units', 'Units to check', 12, 'int'), I('min', 'Minutes per check', 20, 'int')], [
        O('Next check date', 'date', 'EDATE({today}-{in:since},{in:every})'), O('Days to the next check', 'int', 'EDATE({today}-{in:since},{in:every})-{today}'), O('Days overdue', 'int', 'MAX(0,{today}-EDATE({today}-{in:since},{in:every}))'),
        O('Checks per year', 'num', '12/{in:every}'), O('Hours per year, all units', 'num', '{in:units}*{in:min}/60*12/{in:every}'),
        O('Status', 'text', 'IF(EDATE({today}-{in:since},{in:every})<{today},%s,IF(EDATE({today}-{in:since},{in:every})-{today}<={set:warn_days},%s,%s))' % (ck2('Overdue now'), ck2('Due soon'), ck2('Up to date')))],
         GR('What if', ('Smoke alarm, last check 200 days ago', {'since': 200}), ('Gas check, 12 months', {'every': 12, 'since': 340}), ('Lock check every 3 months', {'every': 3, 'since': 60}), ('Only 8 units', {'units': 8}), ('Longer checks, 40 minutes', {'min': 40}))),
    TOOL('capex_payback', 'Capex Payback', 'Months to pay back a spend on a unit',
         'Type the cost, the repairs saved a year, the extra nights a year and the rate; see the yearly gain, the months to pay back and the gain over five years.', [
        I('cost', 'Cost of the spend', 2200), I('save', 'Repairs and energy saved per year', 450), I('nights', 'Extra nights booked per year', 12, 'int'), I('adr', 'Average price of a night', 140), I('fee', 'Platform fee', 0.14, 'pct')], [
        O('Extra revenue per year after fees', 'money', '{in:nights}*{in:adr}*(1-{in:fee})'), O('Total gain per year', 'money', '{in:save}+{in:nights}*{in:adr}*(1-{in:fee})'),
        O('Months to pay back', 'num', 'IFERROR({in:cost}/({in:save}+{in:nights}*{in:adr}*(1-{in:fee}))*12,0)'), O('Return per year', 'pct', 'IFERROR(({in:save}+{in:nights}*{in:adr}*(1-{in:fee}))/{in:cost},0)'),
        O('Gain over 5 years after the cost', 'money', '5*({in:save}+{in:nights}*{in:adr}*(1-{in:fee}))-{in:cost}'),
        O('Verdict', 'text', 'IF(IFERROR({in:cost}/({in:save}+{in:nights}*{in:adr}*(1-{in:fee}))*12,999)<=24,%s,%s)' % (ck2('Pays back in time'), ck2('Slow payback')))],
         GR('What if', ('New mattresses, 20 extra nights', {'cost': 900, 'save': 0, 'nights': 20}), ('Heat pump of 4,800', {'cost': 4800, 'save': 900, 'nights': 8}), ('Smart lock of 260', {'cost': 260, 'save': 120, 'nights': 0}), ('No extra nights', {'nights': 0}), ('Higher rate of 180', {'adr': 180}))),
    TOOL('parts_order', 'Parts Order Total', 'Value of a parts order with delivery',
         'Type up to four parts with quantity and price, the supplier discount and the delivery fee; see each line, the order value and whether it is over the repair limit.', [
        I('q1', 'Part 1, quantity', 2, 'int'), I('p1', 'Part 1, price each', 24), I('q2', 'Part 2, quantity', 1, 'int'), I('p2', 'Part 2, price each', 65), I('q3', 'Part 3, quantity', 4, 'int'), I('p3', 'Part 3, price each', 8.5),
        I('q4', 'Part 4, quantity', 0, 'int'), I('p4', 'Part 4, price each', 0), I('disc', 'Supplier discount', 0.05, 'pct'), I('del', 'Delivery fee', 9)], [
        O('Part 1 total', 'money', '{in:q1}*{in:p1}'), O('Part 2 total', 'money', '{in:q2}*{in:p2}'), O('Part 3 total', 'money', '{in:q3}*{in:p3}'), O('Part 4 total', 'money', '{in:q4}*{in:p4}'),
        O('Items in the order', 'int', '{in:q1}+{in:q2}+{in:q3}+{in:q4}'), O('Subtotal', 'money', '{in:q1}*{in:p1}+{in:q2}*{in:p2}+{in:q3}*{in:p3}+{in:q4}*{in:p4}'),
        O('Discount', 'money', '({in:q1}*{in:p1}+{in:q2}*{in:p2}+{in:q3}*{in:p3}+{in:q4}*{in:p4})*{in:disc}'),
        O('Order value with delivery', 'money', '({in:q1}*{in:p1}+{in:q2}*{in:p2}+{in:q3}*{in:p3}+{in:q4}*{in:p4})*(1-{in:disc})+{in:del}'),
        O('Average price per item', 'money', 'IFERROR((({in:q1}*{in:p1}+{in:q2}*{in:p2}+{in:q3}*{in:p3}+{in:q4}*{in:p4})*(1-{in:disc})+{in:del})/({in:q1}+{in:q2}+{in:q3}+{in:q4}),0)'),
        O('Limit check', 'text', 'IF(({in:q1}*{in:p1}+{in:q2}*{in:p2}+{in:q3}*{in:p3}+{in:q4}*{in:p4})*(1-{in:disc})+{in:del}>{set:repair_limit},%s,%s)' % (cb('Over the repair limit'), cb('Within the repair limit')))],
         GR('What if', ('No discount', {'disc': 0}), ('Free delivery', {'del': 0}), ('Big order, part 3 times 20', {'q3': 20}), ('Add part 4, 3 times 120', {'q4': 3, 'p4': 120}), ('Single part', {'q1': 1, 'q2': 0, 'q3': 0}))),
    TOOL('guest_impact', 'Guest Impact Cost', 'Cost of a failure that affects a guest',
         'Type the nights lost, the rate, the refund, the credit and the extra cost; see the total cost of the failure and what a fix beforehand would have saved.', [
        I('nights', 'Nights lost or refunded', 2, 'int'), I('adr', 'Average price of a night', 140), I('fee', 'Platform fee on those nights', 0.14, 'pct'), I('refund', 'Refund given', 60), I('credit', 'Credit or gift given', 25),
        I('extra', 'Extra cost, cleaning or a hotel night', 30), I('fix', 'Cost of a fix beforehand', 150)], [
        O('Income lost after fees', 'money', '{in:nights}*{in:adr}*(1-{in:fee})'), O('Cost of the failure', 'money', TOT12), O('Cost per night lost', 'money', 'IFERROR(%s/{in:nights},0)' % TOT12),
        O('Cost against a normal night income', 'num', 'IFERROR(%s/({in:adr}*(1-{in:fee})),0)' % TOT12), O('Saved by fixing beforehand', 'money', TOT12 + '-{in:fix}'),
        O('Verdict', 'text', 'IF(%s>{in:fix},%s,%s)' % (TOT12, ck2('Spend more, it pays'), ck2('Spend is enough')))],
         GR('What if', ('One night, no refund', {'nights': 1, 'refund': 0, 'credit': 0}), ('Heating failed in winter, 3 nights', {'nights': 3, 'refund': 150}), ('Cheap fix of 40', {'fix': 40}), ('Peak season rate of 220', {'adr': 220}), ('Direct booking, fee 3 percent', {'fee': 0.03}))),
    TOOL('checkin_deadline', 'Next Check-in Deadline', 'Last safe day to start a repair',
         'Type the next check-in date, the repair days, the days for parts and a buffer; see the last safe day to start, the day to order parts and the days left.', [
        I('days', 'Days to the next check-in', 8, 'int'), I('rep', 'Days the repair takes', 2, 'int'), I('parts', 'Days for parts to arrive', 3, 'int'), I('buf', 'Buffer days before the guest arrives', 1, 'int')], [
        O('Next check-in date', 'date', '{today}+{in:days}'), O('Last safe day to start the repair', 'date', '{today}+{in:days}-{in:rep}-{in:buf}'), O('Last day to order the parts', 'date', '{today}+{in:days}-{in:rep}-{in:buf}-{in:parts}'),
        O('Days left before the parts must be ordered', 'int', '{today}+{in:days}-{in:rep}-{in:buf}-{in:parts}-{today}'), O('Days needed in total', 'int', '{in:rep}+{in:buf}+{in:parts}'),
        O('Advice', 'text', 'IF({today}+{in:days}-{in:rep}-{in:buf}-{in:parts}-{today}<0,%s,IF({today}+{in:days}-{in:rep}-{in:buf}-{in:parts}-{today}<=1,%s,%s))' % (ck2('Last safe day has passed'), ck2('Start now'), ck2('Start by the last safe day')))],
         GR('What if', ('Check-in tomorrow', {'days': 1}), ('Parts take 7 days', {'parts': 7}), ('Long repair of 5 days', {'rep': 5}), ('No buffer', {'buf': 0}), ('Check-in in 30 days', {'days': 30}))),
    TOOL('spend_grid', 'Repair Spend and Revenue Grid', 'Repair spend against rating and revenue effect',
         'Type the monthly spend, the rating you start from, the rating gained per extra 100 spent and the booking uplift per 0.1 rating; see the extra revenue and the net gain. The grid tries several spends.', [
        I('base', 'Spend now, per month', 300), I('spend', 'Spend to test, per month', 400), I('rating', 'Review rating now', 4.5, 'num'), I('gain', 'Rating gained per extra 100 spent', 0.02, 'num'), I('uplift', 'Booking uplift per 0.1 of rating', 0.015, 'pct'),
        I('nights', 'Booked nights per month, all units', 300, 'int'), I('adr', 'Average price of a night', 140), I('fee', 'Platform fee', 0.14, 'pct')], [
        O('Extra spend per month', 'money', EX14), O('Rating after the spend', 'num', RA14), O('Extra nights per month', 'num', NI14), O('Extra revenue per month after fees', 'money', NI14 + '*{in:adr}*(1-{in:fee})'),
        O('Net gain per month', 'money', NI14 + '*{in:adr}*(1-{in:fee})-' + EX14), O('Revenue earned for each extra 1 spent', 'num', 'IF(%s>0,%s*{in:adr}*(1-{in:fee})/%s,0)' % (EX14, NI14, EX14)),
        O('Net gain per year', 'money', '12*(' + NI14 + '*{in:adr}*(1-{in:fee})-' + EX14 + ')'),
        O('Verdict', 'text', 'IF(%s*{in:adr}*(1-{in:fee})>%s,%s,%s)' % (NI14, EX14, ck2('Spend more, it pays'), ck2('Spend is enough')))],
         GR('Spend per month', ('Spend 300, no change', {'spend': 300}), ('Spend 400', {'spend': 400}), ('Spend 600', {'spend': 600}), ('Spend 800', {'spend': 800}), ('Spend 1,200', {'spend': 1200}), ('Spend 600, stronger effect', {'spend': 600, 'gain': 0.04}))),
]
assert len(tools) == 14, len(tools)
for _t in tools: assert len(_t['hint']) <= 200 and len(_t['title']) <= 60 and len(_t['sheet']) <= 31, (_t['key'], len(_t['hint']))
