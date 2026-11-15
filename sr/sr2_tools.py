"""Short-term rental host suite part 2: the 14 calculators."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr2_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
FE = lambda n: 'INDEX({range:channels.fee_pct},%d)' % n
BSN = '{range:bookings.status},"<>"&' + tok('bstatus', 'Cancelled')
PLAT = tok('taxby', 'Platform'); HST = tok('taxby', 'Host')

# 1 quote
GR1 = '({in:nights}*{in:rate}+{in:clean})'
# 4 cancellation
POL = {'f': tok('policy', 'Flexible'), 'm': tok('policy', 'Moderate')}
SH4 = 'IF({in:policy}=%s,IF({in:days}>=7,1,IF({in:days}>=2,0.5,0)),IF({in:policy}=%s,IF({in:days}>=14,1,IF({in:days}>=7,0.5,0)),IF({in:days}>=30,1,IF({in:days}>=14,0.5,0))))' % (POL['f'], POL['m'])
# 5 double booking
UN5 = 'INDEX({range:units.name},{in:row})'
CL5 = '({range:bookings.unit}=%s)*(%s)' % (UN5, '{range:bookings.status}<>' + tok('bstatus', 'Cancelled'))
# 6 period
PER = '{range:bookings.check_in},">="&{in:start},{range:bookings.check_in},"<="&{in:end},' + BSN
# 7 payout forecast weeks
def WK(n): return 'SUMIFS({range:bookings.net_payout},{range:bookings.payout_date},">="&({today}+%d),{range:bookings.payout_date},"<"&({today}+%d),%s)' % (7 * n, 7 * n + 7, BSN)
# 8 deposit
# 10 value per night
FEE10 = '({in:gross}*{in:fee})'; PR10 = '({in:gross}-%s-{in:clean_cost}-{in:supplies})' % FEE10
# 12 long stay
D12 = 'IF({in:nights}>=28,{in:md},IF({in:nights}>=7,{in:wd},0))'
# 14 grid
FEES14 = '({in:gross}*({in:share}*{in:dfee}+(1-{in:share})*{in:pfee}))'

tools = [
    TOOL('quote', 'Booking Quote Calculator', 'Guest total and host net on each channel',
         'Type the nights, the nightly rate, the cleaning fee and the local tax percent; see what the guest pays and what the host keeps on each channel, using the fees on your Channels sheet.', [
        I('nights', 'Nights', 4, 'int'), I('rate', 'Nightly rate', 140), I('clean', 'Cleaning fee', 55), I('tax', 'Local tax percent', 0.06, 'pct')], [
        O('Room revenue', 'money', '{in:nights}*{in:rate}'), O('Gross, room revenue and cleaning fee', 'money', GR1), O('Local tax on the room revenue', 'money', '{in:nights}*{in:rate}*{in:tax}'),
        O('Guest total with local tax', 'money', GR1 + '+{in:nights}*{in:rate}*{in:tax}'), O('Guest price per night, all in', 'money', '(%s+{in:nights}*{in:rate}*{in:tax})/{in:nights}' % GR1),
        O('Host keeps on Platform A', 'money', GR1 + '*(1-' + FE(1) + ')'), O('Host keeps on Platform B', 'money', GR1 + '*(1-' + FE(2) + ')'), O('Host keeps on Platform C', 'money', GR1 + '*(1-' + FE(3) + ')'),
        O('Host keeps on a direct booking', 'money', GR1 + '*(1-' + FE(4) + ')'), O('Direct gain over Platform A', 'money', GR1 + '*(' + FE(1) + '-' + FE(4) + ')'),
        O('Verdict', 'text', 'IF(%s*(1-%s)>%s*(1-%s),%s,%s)' % (GR1, FE(4), GR1, FE(1), ck2('Direct earns the host more'), ck2('Platform earns the host more')))],
         GR('What if', ('Weekend of 2 nights', {'nights': 2}), ('A week in peak season', {'nights': 7, 'rate': 190}), ('Premium unit', {'rate': 260, 'clean': 95}), ('Low season, cheap studio', {'rate': 72, 'clean': 30, 'nights': 3}), ('Higher local tax, 6 percent to 8', {'tax': 0.08}))),
    TOOL('reconcile', 'Payout Reconciliation', 'Payout in full, short or late',
         'Type the net payout you expected, the amount received and the days since the expected date; see the difference, the amount to claim and whether to wait, check the amount or chase now.', [
        I('expected', 'Expected net payout', 446.41), I('received', 'Amount received', 420), I('late', 'Days since the expected date', 2, 'int')], [
        O('Difference, expected less received', 'money', '{in:expected}-{in:received}'), O('Difference as a share of the payout', 'pct', 'IFERROR(({in:expected}-{in:received})/{in:expected},0)'),
        O('Days past the grace days', 'int', 'MAX(0,{in:late}-{set:payout_grace_days})'), O('Amount to claim', 'money', 'IF({in:received}=0,{in:expected},MAX(0,{in:expected}-{in:received}))'),
        O('Share of the platform fee the difference would be', 'pct', 'IFERROR(({in:expected}-{in:received})/({in:expected}/(1-AVERAGE({range:channels.fee_pct}))*AVERAGE({range:channels.fee_pct})),0)'),
        O('Verdict', 'text', 'IF({in:received}=0,IF({in:late}>{set:payout_grace_days},%s,%s),IF({in:expected}-{in:received}>{set:short_tolerance},%s,%s))' % (ck2('Payout late, chase now'), ck2('Payout not due yet'), ck2('Payout short, claim the difference'), ck2('Payout in full'))),
        O('Payouts to chase on the Payouts sheet', 'int', 'COUNTIFS({range:payouts.chase_flag},%s)' % ca('Chase now'))],
         GR('What if', ('Paid in full', {'received': 446.41}), ('Nothing received, 2 days late', {'received': 0}), ('Nothing received, 12 days late', {'received': 0, 'late': 12}), ('Short by a tenth', {'received': 400}), ('Large booking, short', {'expected': 1253.21, 'received': 1100}))),
    TOOL('fee_compare', 'Channel Fee Comparison', 'What the host keeps on each channel',
         'Type the gross of a booking, the fee of each platform and the direct fee, and the bookings a year; see what you keep on each route and what moving bookings to direct saves in a year.', [
        I('gross', 'Gross of the booking', 780), I('fa', 'Fee of Platform A', 0.15, 'pct'), I('fb', 'Fee of Platform B', 0.14, 'pct'), I('fc', 'Fee of Platform C', 0.12, 'pct'), I('fd', 'Direct fee', 0.03, 'pct'), I('moved', 'Bookings a year moved to direct', 40, 'int')], [
        O('Keep on Platform A', 'money', '{in:gross}*(1-{in:fa})'), O('Keep on Platform B', 'money', '{in:gross}*(1-{in:fb})'), O('Keep on Platform C', 'money', '{in:gross}*(1-{in:fc})'), O('Keep on a direct booking', 'money', '{in:gross}*(1-{in:fd})'),
        O('Direct gain over Platform A', 'money', '{in:gross}*({in:fa}-{in:fd})'), O('Direct gain over Platform B', 'money', '{in:gross}*({in:fb}-{in:fd})'), O('Direct gain over Platform C', 'money', '{in:gross}*({in:fc}-{in:fd})'),
        O('Average platform fee', 'pct', '({in:fa}+{in:fb}+{in:fc})/3'), O('Yearly saving, moved bookings', 'money', '{in:moved}*{in:gross}*(({in:fa}+{in:fb}+{in:fc})/3-{in:fd})'),
        O('Largest guest discount direct can pay for', 'pct', 'IFERROR(1-(1-({in:fa}+{in:fb}+{in:fc})/3)/(1-{in:fd}),0)'), O('Fees paid on the Bookings sheet, all bookings', 'money', 'SUMIFS({range:bookings.platform_fee},%s)' % BSN)],
         GR('What if', ('Large booking, 1,500', {'gross': 1500}), ('Short stay, 300', {'gross': 300}), ('Platform fees rise by 2 points', {'fa': 0.17, 'fb': 0.16, 'fc': 0.14}), ('Move 100 bookings', {'moved': 100}), ('Card fee of 4 percent', {'fd': 0.04}))),
    TOOL('cancel_kept', 'Cancellation Kept Amount', 'Refund and kept amount for a cancellation',
         'Type the days before check-in, the policy, the room revenue and the cleaning fee; see the share refunded, the amount kept and the refund. Sample policies: check your own contract terms.', [
        I('days', 'Days before check-in', 10, 'int'), IN('policy', 'Cancellation policy', 'list', key('policy', 'Moderate'), list='policy'), I('room', 'Room revenue', 600), I('clean', 'Cleaning fee', 55), I('fee', 'Platform fee', 0.14, 'pct')], [
        O('Share of the room revenue refunded', 'pct', SH4), O('Room revenue kept', 'money', '{in:room}*(1-%s)' % SH4), O('Room revenue refunded', 'money', '{in:room}*%s' % SH4), O('Cleaning fee refunded', 'money', '{in:clean}'),
        O('Total refund to the guest', 'money', '{in:room}*%s+{in:clean}' % SH4), O('Platform fee on the kept amount', 'money', '{in:room}*(1-%s)*{in:fee}' % SH4), O('Host keeps after the fee', 'money', '{in:room}*(1-%s)*(1-{in:fee})' % SH4),
        O('Days left to the full refund line', 'int', 'MAX(0,IF({in:policy}=%s,7,IF({in:policy}=%s,14,30))-{in:days})' % (POL['f'], POL['m'])),
        O('Verdict', 'text', 'IF(%s=1,%s,IF(%s=0,%s,%s))' % (SH4, ck2('Full refund'), SH4, ck2('No refund'), ck2('Part refund')))],
         GR('What if', ('Cancelled 3 days before, flexible', {'days': 3, 'policy': '=' + POL['f']}), ('Cancelled 20 days before, strict', {'days': 20, 'policy': '=' + tok('policy', 'Strict')}), ('Cancelled 1 day before, moderate', {'days': 1}), ('Cancelled 40 days before', {'days': 40}), ('Large booking, 1,400', {'room': 1400, 'days': 8}))),
    TOOL('clash', 'Double-Booking Check', 'Free or clash for new dates in a unit',
         'Type the row of the unit in your Units sheet and the new check-in and check-out dates; the Bookings sheet is searched for overlapping stays, the last check-out before and the next check-in after.', [
        I('row', 'Row number in the Units sheet, 1 to 12', 1, 'int'), I('din', 'New check-in', ahead(60), 'date'), I('dout', 'New check-out', ahead(63), 'date')], [
        O('Unit', 'text', UN5), O('Nights asked for', 'int', '{in:dout}-{in:din}'),
        O('Bookings that overlap the new dates', 'int', 'SUMPRODUCT(%s*({range:bookings.check_in}<{in:dout})*({range:bookings.check_out}>{in:din}))' % CL5),
        O('Free nights before the new check-in', 'int', 'IF(SUMPRODUCT(MAX(%s*({range:bookings.check_out}<={in:din})*{range:bookings.check_out}))>0,{in:din}-SUMPRODUCT(MAX(%s*({range:bookings.check_out}<={in:din})*{range:bookings.check_out})),0)' % (CL5, CL5)),
        O('Free nights after the new check-out', 'int', 'IF(SUMPRODUCT(MIN(%s*({range:bookings.check_in}>={in:dout})*{range:bookings.check_in}+(1-%s*({range:bookings.check_in}>={in:dout}))*100000))>=100000,0,SUMPRODUCT(MIN(%s*({range:bookings.check_in}>={in:dout})*{range:bookings.check_in}+(1-%s*({range:bookings.check_in}>={in:dout}))*100000))-{in:dout})' % (CL5, CL5, CL5, CL5)),
        O('Verdict', 'text', 'IF(SUMPRODUCT(%s*({range:bookings.check_in}<{in:dout})*({range:bookings.check_out}>{in:din}))=0,%s,%s)' % (CL5, ck2('Dates are free'), ck2('Clash with another booking')))],
         GR('What if', ('Another unit, row 4', {'row': 4}), ('Row 8', {'row': 8}), ('Longer stay of 10 nights', {'dout': '={today}+70'}), ('Stay starting in 10 days', {'din': '={today}+10', 'dout': '={today}+13'}))),
    TOOL('period', 'Occupancy and Revenue Period', 'Nights, ADR, RevPAR and revenue between two dates',
         'Type the first and last check-in date and the units; nights sold, occupancy, ADR (the average price of a night sold), RevPAR (revenue per available night) and revenue come from Bookings.', [
        I('start', 'First check-in date', ago(30), 'date'), I('end', 'Last check-in date', ago(0), 'date'), I('units', 'Units counted', 12, 'int')], [
        O('Bookings in the period', 'int', 'COUNTIFS(%s)' % PER), O('Nights sold', 'int', 'SUMIFS({range:bookings.nights},%s)' % PER), O('Nights available', 'int', '({in:end}-{in:start}+1)*{in:units}'),
        O('Occupancy', 'pct', 'IFERROR(SUMIFS({range:bookings.nights},%s)/(({in:end}-{in:start}+1)*{in:units}),0)' % PER), O('Room revenue', 'money', 'SUMIFS({range:bookings.room_revenue},%s)' % PER),
        O('ADR, average price of a night sold', 'money', 'IFERROR(SUMIFS({range:bookings.room_revenue},%s)/SUMIFS({range:bookings.nights},%s),0)' % (PER, PER)),
        O('RevPAR, revenue per available night', 'money', 'IFERROR(SUMIFS({range:bookings.room_revenue},%s)/(({in:end}-{in:start}+1)*{in:units}),0)' % PER), O('Gross with cleaning fees', 'money', 'SUMIFS({range:bookings.gross},%s)' % PER),
        O('Platform fees', 'money', 'SUMIFS({range:bookings.platform_fee},%s)' % PER), O('Net payouts', 'money', 'SUMIFS({range:bookings.net_payout},%s)' % PER), O('Average stay', 'num', 'IFERROR(SUMIFS({range:bookings.nights},%s)/COUNTIFS(%s),0)' % (PER, PER))],
         GR('What if', ('Only 6 units counted', {'units': 6}), ('Last 7 days', {'start': '={today}-7'}), ('Last 14 days', {'start': '={today}-14'}), ('Last 60 days', {'start': '={today}-60'}), ('All 12 units, 3 months ago', {'start': '={today}-90', 'end': '={today}-60'}))),
    TOOL('forecast', 'Payout Forecast by Week', 'Money expected each week for 8 weeks',
         'Booked stays that have not paid out yet are placed in the week of their payout date: the check-in plus the payout days of the channel. See the money expected in each of the next 8 weeks.', [
        I('extra', 'Share of bookings you expect to cancel', 0.07, 'pct')], [
        O('Week 1, next 7 days', 'money', WK(0) + '*(1-{in:extra})'), O('Week 2', 'money', WK(1) + '*(1-{in:extra})'), O('Week 3', 'money', WK(2) + '*(1-{in:extra})'), O('Week 4', 'money', WK(3) + '*(1-{in:extra})'),
        O('Week 5', 'money', WK(4) + '*(1-{in:extra})'), O('Week 6', 'money', WK(5) + '*(1-{in:extra})'), O('Week 7', 'money', WK(6) + '*(1-{in:extra})'), O('Week 8', 'money', WK(7) + '*(1-{in:extra})'),
        O('Total for 8 weeks', 'money', 'SUMIFS({range:bookings.net_payout},{range:bookings.payout_date},">="&{today},{range:bookings.payout_date},"<"&({today}+56),%s)*(1-{in:extra})' % BSN),
        O('Scheduled on the Payouts sheet, next 14 days', 'money', 'SUMIFS({range:payouts.expected_amount},{range:payouts.expected_date},">="&{today},{range:payouts.expected_date},"<="&({today}+14),{range:payouts.status},%s)' % tok('payst', 'Scheduled'))],
         GR('What if', ('No cancellations', {'extra': 0}), ('Cancellations at 15 percent', {'extra': 0.15}), ('Cancellations at 25 percent', {'extra': 0.25}))),
    TOOL('deposit', 'Direct Deposit Planner', 'Deposit, balance and dates for a direct booking',
         'Type the total, the deposit share, the days to check-in and the days before check-in the balance is due; see the deposit, the balance, both dates and whether the plan fits before arrival.', [
        I('total', 'Total price of the stay', 900), I('dpct', 'Deposit share', 0.30, 'pct'), I('ahead', 'Days from today to check-in', 45, 'int'), I('bdays', 'Days before check-in the balance is due', 7, 'int'), I('fee', 'Card or transfer fee', 0.03, 'pct')], [
        O('Deposit due now', 'money', '{in:total}*{in:dpct}'), O('Balance', 'money', '{in:total}-{in:total}*{in:dpct}'), O('Check-in date', 'date', '{today}+{in:ahead}'), O('Balance due date', 'date', '{today}+MAX(0,{in:ahead}-{in:bdays})'),
        O('Days between deposit and balance', 'int', 'MAX(0,{in:ahead}-{in:bdays})'), O('Fees on the whole payment', 'money', '{in:total}*{in:fee}'), O('Host keeps after fees', 'money', '{in:total}*(1-{in:fee})'),
        O('Deposit kept if the guest cancels (half of it)', 'money', '{in:total}*{in:dpct}/2'), O('Verdict', 'text', 'IF({in:ahead}>{in:bdays},%s,%s)' % (ck2('Schedule fits before check-in'), ck2('Pay the full amount now')))],
         GR('What if', ('Check-in in 5 days', {'ahead': 5}), ('Check-in in 120 days', {'ahead': 120}), ('Deposit 50 percent', {'dpct': 0.5}), ('Balance 14 days before', {'bdays': 14}), ('A week in peak season, 1,800', {'total': 1800}))),
    TOOL('local_tax', 'Local Tax Collected', 'Local occupancy tax and what the host remits',
         'Type the room revenue, city percent, nights and who collects the local tax (a tax on each night, collected from the guest); see what the host pays over. Check your own local rules.', [
        I('room', 'Room revenue', 700), I('pct', 'Local tax percent of the city', 0.06, 'pct'), I('nights', 'Nights', 5, 'int'), IN('by', 'Collected by', 'list', key('taxby', 'Host'), list='taxby')], [
        O('Local tax', 'money', '{in:room}*{in:pct}'), O('Tax per night', 'money', '{in:room}*{in:pct}/{in:nights}'), O('Tax the host remits', 'money', 'IF({in:by}=%s,{in:room}*{in:pct},0)' % HST),
        O('Tax the platform remits', 'money', 'IF({in:by}=%s,{in:room}*{in:pct},0)' % PLAT), O('Guest pays on top of the room revenue', 'pct', '{in:pct}'),
        O('Tax the host remits, last 90 days on Local Tax Lines', 'money', 'SUMIFS({range:tax_lines.host_remit},{range:tax_lines.check_in},">"&({today}-90),{range:tax_lines.check_in},"<="&{today})'),
        O('Tax collected on the Local Tax Lines sheet, last 90 days', 'money', 'SUMIFS({range:tax_lines.tax_collected},{range:tax_lines.check_in},">"&({today}-90),{range:tax_lines.check_in},"<="&{today})'),
        O('Verdict', 'text', 'IF({in:by}=%s,%s,%s)' % (HST, ck2('Host remits the tax'), ck2('Platform remits the tax')))],
         GR('What if', ('Collected by the platform', {'by': '=' + PLAT}), ('Cascais 5 percent', {'pct': 0.05}), ('Sintra 4 percent', {'pct': 0.04}), ('Long stay, 14 nights', {'nights': 14, 'room': 1800}))),
    TOOL('night_value', 'Booking Value per Night', 'Profit per night after fees and cleaning',
         'Type the gross of a booking, the platform fee, the nights, the cleaner cost and the supplies; see the profit of the stay and of each night, and whether the booking is worth its cleaning.', [
        I('gross', 'Gross of the booking', 483.5), I('fee', 'Platform fee', 0.14, 'pct'), I('nights', 'Nights', 3, 'int'), I('clean_cost', 'Cleaner cost of one turnover', 40), I('supplies', 'Supplies and laundry', 12)], [
        O('Platform fee', 'money', FEE10), O('Net after the fee', 'money', '{in:gross}-' + FEE10), O('Profit after fee, cleaning and supplies', 'money', PR10), O('Profit per night', 'money', PR10 + '/{in:nights}'),
        O('Profit share of the gross', 'pct', 'IFERROR(%s/{in:gross},0)' % PR10), O('Cleaning share of the gross', 'pct', 'IFERROR(({in:clean_cost}+{in:supplies})/{in:gross},0)'),
        O('Nights needed to cover one turnover at this profit', 'num', 'IFERROR(({in:clean_cost}+{in:supplies})/(({in:gross}-%s)/{in:nights}),0)' % FEE10),
        O('Verdict', 'text', 'IF(%s<0,%s,IF(%s/{in:nights}<35,%s,%s))' % (PR10, ck2('Loss on this stay'), PR10, ck2('Profit per night is thin'), ck2('Profit per night is healthy')))],
         GR('What if', ('One night only', {'nights': 1, 'gross': 195}), ('Two nights', {'nights': 2, 'gross': 340}), ('A week', {'nights': 7, 'gross': 1050}), ('Direct booking, 3 percent fee', {'fee': 0.03}), ('Cheap studio, 2 nights', {'nights': 2, 'gross': 190, 'clean_cost': 30}))),
    TOOL('reprice', 'Change of Dates Repricing', 'Price difference when a guest changes the dates',
         'Type the old and new nights, the old and new nightly rate, the cleaning fee and what the guest has paid; see the new total, the difference, the balance and whether the price rises or falls.', [
        I('on', 'Old nights', 4, 'int'), I('nn', 'New nights', 5, 'int'), I('orate', 'Old nightly rate', 140), I('nrate', 'New nightly rate', 150), I('clean', 'Cleaning fee', 55), I('paid', 'Paid so far', 300), I('tax', 'Local tax percent', 0.06, 'pct')], [
        O('Old room revenue', 'money', '{in:on}*{in:orate}'), O('New room revenue', 'money', '{in:nn}*{in:nrate}'), O('Difference in room revenue', 'money', '{in:nn}*{in:nrate}-{in:on}*{in:orate}'),
        O('Difference in local tax', 'money', '({in:nn}*{in:nrate}-{in:on}*{in:orate})*{in:tax}'), O('New total with cleaning and tax', 'money', '{in:nn}*{in:nrate}*(1+{in:tax})+{in:clean}'),
        O('Balance still to pay', 'money', '{in:nn}*{in:nrate}*(1+{in:tax})+{in:clean}-{in:paid}'), O('Change in nights', 'int', '{in:nn}-{in:on}'), O('Change in the average price of a night', 'money', '{in:nrate}-{in:orate}'),
        O('Verdict', 'text', 'IF({in:nn}*{in:nrate}>{in:on}*{in:orate},%s,IF({in:nn}*{in:nrate}<{in:on}*{in:orate},%s,%s))' % (ck2('Price rises'), ck2('Price falls'), ck2('Price unchanged')))],
         GR('What if', ('Stay shortened to 3 nights', {'nn': 3}), ('Moved into peak season', {'nrate': 190}), ('Moved into low season', {'nrate': 105}), ('Extended to a week', {'nn': 7}), ('Same dates, same price', {'nn': 4, 'nrate': 140}))),
    TOOL('long_stay', 'Long-Stay Discount', 'Price of a stay of 7 nights or more',
         'Type the nights, the nightly rate and the weekly and monthly discounts; see the discount that applies, the price per night and the total with the cleaning fee, and what the host keeps.', [
        I('nights', 'Nights', 10, 'int'), I('rate', 'Nightly rate', 140), I('wd', 'Weekly discount', 0.08, 'pct'), I('md', 'Monthly discount', 0.15, 'pct'), I('clean', 'Cleaning fee', 55), I('fee', 'Platform fee', 0.14, 'pct')], [
        O('Discount that applies', 'pct', D12), O('Price per night after the discount', 'money', '{in:rate}*(1-%s)' % D12), O('Room revenue after the discount', 'money', '{in:nights}*{in:rate}*(1-%s)' % D12),
        O('Total with the cleaning fee', 'money', '{in:nights}*{in:rate}*(1-%s)+{in:clean}' % D12), O('Saving for the guest', 'money', '{in:nights}*{in:rate}*%s' % D12),
        O('Host keeps after the platform fee', 'money', '({in:nights}*{in:rate}*(1-%s)+{in:clean})*(1-{in:fee})' % D12), O('Cleaning cost share of the total', 'pct', 'IFERROR({set:cleaning_cost}/({in:nights}*{in:rate}*(1-%s)+{in:clean}),0)' % D12),
        O('Nights left to the next discount step', 'int', 'IF({in:nights}>=28,0,IF({in:nights}>=7,28-{in:nights},7-{in:nights}))'),
        O('Verdict', 'text', 'IF(%s>={in:md},%s,IF(%s>0,%s,%s))' % (D12, ck2('Discount is generous'), D12, ck2('Discount is modest'), ck2('Price unchanged')))],
         GR('What if', ('6 nights, no discount', {'nights': 6}), ('7 nights', {'nights': 7}), ('14 nights', {'nights': 14}), ('30 nights', {'nights': 30}), ('Direct, 3 percent fee', {'fee': 0.03}))),
    TOOL('claim', 'Missing Payout Claim Helper', 'Amount and timing of a payout claim',
         'Type the expected amount, the amount received and the days since the expected date; see the amount to claim and whether to wait or send the claim. The Payouts sheet totals what is open.', [
        I('expected', 'Expected net payout', 835.10), I('received', 'Amount received', 0), I('late', 'Days since the expected date', 38, 'int')], [
        O('Amount to claim', 'money', 'MAX(0,{in:expected}-{in:received})'), O('Weeks late', 'num', '{in:late}/7'), O('Days past the grace days', 'int', 'MAX(0,{in:late}-{set:payout_grace_days})'),
        O('Share of the payout still missing', 'pct', 'IFERROR(MAX(0,{in:expected}-{in:received})/{in:expected},0)'),
        O('Verdict', 'text', 'IF({in:late}<={set:payout_grace_days},%s,IF({in:received}=0,%s,%s))' % (ck2('Wait for the grace days'), ck2('Claim the full amount'), ck2('Claim the difference'))),
        O('Payouts with the status missing on the Payouts sheet', 'int', 'COUNTIFS({range:payouts.status},%s)' % tok('payst', 'Missing')), O('Value of missing payouts on the Payouts sheet', 'money', 'SUMIFS({range:payouts.expected_amount},{range:payouts.status},%s)' % tok('payst', 'Missing')),
        O('Short amount on the Payouts sheet, all short payouts', 'money', 'SUMIFS({range:payouts.short_amount},{range:payouts.status},%s)' % tok('payst', 'Short paid'))],
         GR('What if', ('Short paid by a tenth', {'received': 750, 'late': 6}), ('Only 2 days late', {'late': 2}), ('A week late', {'late': 9}), ('Large payout, 1,900', {'expected': 1900, 'received': 0, 'late': 20}))),
    TOOL('direct_grid', 'Direct Share and Yearly Fees', 'Fees saved when more bookings come direct',
         'Type the yearly gross, the average platform fee, the direct fee and the direct share now; see the fees now and the saving for each ten extra points of direct share. The grid tries several shares.', [
        I('gross', 'Gross of the year', 480000), I('pfee', 'Average platform fee', 0.14, 'pct'), I('dfee', 'Direct fee', 0.03, 'pct'), I('share', 'Direct share of gross', 0.22, 'pct')], [
        O('Fees paid now', 'money', FEES14), O('Fees if every booking were on platforms', 'money', '{in:gross}*{in:pfee}'), O('Fees saved by the direct share now', 'money', '{in:gross}*{in:pfee}-' + FEES14),
        O('Saving per extra 10 points of direct share', 'money', '{in:gross}*0.1*({in:pfee}-{in:dfee})'), O('Fees at a share of 10 points more', 'money', '{in:gross}*(MIN(1,{in:share}+0.1)*{in:dfee}+(1-MIN(1,{in:share}+0.1))*{in:pfee})'),
        O('Fees as a share of gross now', 'pct', 'IFERROR(%s/{in:gross},0)' % FEES14), O('Direct share against the wanted share', 'pct', '{in:share}-{set:target_direct_share}'),
        O('Direct share of the Channel Months sheet, all months', 'pct', 'IFERROR(SUMIFS({range:channel_months.gross},{range:channel_months.channel},%s)/SUM({range:channel_months.gross}),0)' % tok('chan', 'Direct')),
        O('Gross to move to direct to save 5,000', 'money', 'IFERROR(5000/({in:pfee}-{in:dfee}),0)')],
         GR('Direct share against yearly fees', ('Direct share 10 percent', {'share': 0.10}), ('Direct share 20 percent', {'share': 0.20}), ('Direct share 30 percent', {'share': 0.30}), ('Direct share 40 percent', {'share': 0.40}), ('Direct share 50 percent', {'share': 0.50}),
            ('Direct share 22 percent, fees 15 percent', {'pfee': 0.15}), ('Direct share 40 percent, fees 15 percent', {'share': 0.40, 'pfee': 0.15}))),
]
assert len(tools) == 14, len(tools)
