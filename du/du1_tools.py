"""Doula Business suite part 1: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du1_lists import *
import du1_data as D
import datetime as _dt


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
Y12 = '">="&({today}-365)'
LOST = tok('estatus', 'Lost'); SIGNED = tok('estatus', 'Signed'); NEWE = tok('estatus', 'New'); BOOKE = tok('estatus', 'Consultation booked'); HELDE = tok('estatus', 'Consultation held'); SENTE = tok('estatus', 'Contract sent')
O_SIGNED = tok('outcome', 'Signed'); O_NOSHOW = tok('outcome', 'No-show'); O_BOOKED = tok('outcome', 'Booked'); O_THINK = tok('outcome', 'Thinking'); O_DECL = tok('outcome', 'Declined')
D_COMM = tok('discount', 'Community rate'); D_RET = tok('discount', 'Returning client'); Q_OPEN = tok('qstatus', 'Open'); Q_SIGNED = tok('qstatus', 'Signed')
RB = lambda n: tok('rband', n)
def FUN6(col): return 'INDEX({range:funnel.%s},MATCH(%s,{range:funnel.month},0))' % (col, MS)
W6 = '{range:enquiries.date},">="&EDATE(%s,-6),{range:enquiries.date},"<"&%s' % (MS, MS)
D90 = '{range:enquiries.date},">="&({today}-90),{range:enquiries.date},"<="&{today}'
tools = []

# 1 ------------------------------------------------------------ quote builder
PKX = lambda c: 'INDEX({range:packages.%s},MATCH({in:pk},{range:packages.package},0))' % c
DPCT = 'IF({in:disc}=%s,{set:community_discount},IF({in:disc}=%s,{set:returning_discount},0))' % (D_COMM, D_RET)
DISC = 'ROUND(%s*%s,0)' % (PKX('price'), DPCT)
XH = 'IF({in:xh}>0,MAX({in:xh},{set:min_booking_hours}),0)'
XHA = '%s*{in:rate}' % XH
XVA = '{in:xv}*{in:vp}'
TRV = 'ROUND({in:miles}*SUMIFS({range:areas.mileage_rate},{range:areas.area},{in:area}),0)'
TOT = '(%s-%s+%s+%s+{in:oth}+%s)' % (PKX('price'), DISC, XHA, XVA, TRV)
DEP = 'ROUND(%s*%s,0)' % (TOT, PKX('deposit_pct'))
BAL = '(%s-%s)' % (TOT, DEP)
HRS = '(%s+%s+2*{in:xv})' % (PKX('plan_hours'), XH)
IPH = '((%s-%s)/%s)' % (TOT, TRV, HRS)
LASTI = '{in:edd}-{set:oncall_before_days}-2'
tools.append(TOOL('quote_builder', 'Quote Builder', 'What to quote: total, deposit, dates and income per hour',
    'Pick a package and type extra hours, extra prenatal visits, add-ons, extra miles, a discount and instalments; see the total, the deposit, the balance date, the instalment dates and the income per hour against your target.', [
    IL('pk', 'Package', 'package', 'Birth Plus'), I('edd', 'Estimated due date (a date the client gives)', ahead(150), 'date'), I('xh', 'Extra postpartum hours', 0, 'int'), I('rate', 'Rate per extra hour', 40),
    I('xv', 'Extra prenatal visits', 1, 'int'), I('vp', 'Price of an extra prenatal visit', 95), I('oth', 'Other add-ons amount', 0), IL('area', 'Service area', 'area', 'Northgate'),
    I('miles', 'Extra miles beyond the area', 24, 'num'), IL('disc', 'Discount', 'discount', 'None'), I('inst', 'Instalments (1 = pay the balance at once)', 3, 'int')], [
    O('List price', 'money', PKX('price')), O('Discount', 'money', DISC), O('Extra postpartum hours charge', 'money', XHA), O('Extra prenatal visits charge', 'money', XVA),
    O('Travel fee at the area mileage rate', 'money', TRV), O('Quote total', 'money', TOT), O('Deposit', 'money', DEP), O('Balance after the deposit', 'money', BAL),
    O('Balance due date', 'date', 'IF(%s>0,{in:edd}-7*{set:balance_weeks},"")' % BAL), O('Instalment amount', 'money', 'IF(%s>0,ROUND(%s/MAX(1,{in:inst}),0),0)' % (BAL, BAL)),
    O('First instalment due', 'date', 'IF(AND(%s>0,{in:inst}>1),%s-({in:inst}-1)*{set:instalment_days},"")' % (BAL, LASTI)), O('Last instalment due', 'date', 'IF(AND(%s>0,{in:inst}>1),%s,"")' % (BAL, LASTI)),
    O('On-call window opens', 'date', 'IF(%s>0,{in:edd}-{set:oncall_before_days},"")' % PKX('birth_hours')), O('On-call window closes', 'date', 'IF(%s>0,{in:edd}+{set:oncall_after_days},"")' % PKX('birth_hours')),
    O('Planned hours, all hours', 'num', HRS), O('Income per hour', 'money', IPH), O('Income per hour you want', 'money', '{set:target_income_hour}'),
    O('Quote total needed for your target', 'money', 'ROUND({set:target_income_hour}*%s+%s,0)' % (HRS, TRV)),
    O('Short of your target by', 'money', 'MAX(0,ROUND({set:target_income_hour}*%s+%s,0)-%s)' % (HRS, TRV, TOT)),
    O('Verdict', 'text', 'IF(%s>={set:target_income_hour},%s,%s)' % (IPH, c2('Above target, send the quote'), c2('Raise the price or cut hours')))],
    GR('What if', ('Complete Care Bundle', {'pk': '=' + tok('package', 'Complete Care Bundle'), 'xv': 0}), ('Birth Premier, community rate', {'pk': '=' + tok('package', 'Birth Premier'), 'disc': '=' + D_COMM}),
       ('Four instalments', {'inst': 4}), ('Ten extra postpartum hours', {'xh': 10}), ('Southbank, 40 extra miles', {'area': '=' + tok('area', 'Southbank'), 'miles': 40}),
       ('Combined Plus, no extra miles', {'pk': '=' + tok('package', 'Combined Plus'), 'xv': 0, 'miles': 0}))))

# 2 ------------------------------------------------------------ reply-time impact
SB = lambda n: 'SUMIFS({range:reply_bands.signed_share},{range:reply_bands.band},%s)' % RB(n)
BK = lambda n: 'IFERROR(COUNTIFS({range:enquiries.reply_band},%s,{range:enquiries.consult_date},">0",{range:enquiries.date},%s)/COUNTIFS({range:enquiries.reply_band},%s,{range:enquiries.date},%s),0)' % (RB(n), Y12, RB(n), Y12)
YOURS = 'IF({in:hrs}<=4,%s,IF({in:hrs}<=24,%s,IF({in:hrs}<=48,%s,%s)))' % (SB('Up to 4 hours'), SB('5 to 24 hours'), SB('25 to 48 hours'), SB('Over 48 hours'))
tools.append(TOOL('reply_impact', 'Reply-Time Impact', 'Does a faster first reply win more contracts',
    'Type your usual hours to a first reply, the enquiries a month and the value of a contract; see the share that booked a consultation and the share that signed after each reply speed, from your own last 12 months.', [
    I('hrs', 'Your usual hours to a first reply', 12, 'num'), I('enq', 'Enquiries a month', D.enq_month(), 'int'), I('val', 'Average quote value', D.avg_quote())], [
    O('Booked a consultation, reply within 4 hours', 'pct', BK('Up to 4 hours')), O('Booked a consultation, reply within 24 hours', 'pct', BK('5 to 24 hours')),
    O('Booked a consultation, reply within 48 hours', 'pct', BK('25 to 48 hours')), O('Booked a consultation, reply after 48 hours', 'pct', BK('Over 48 hours')),
    O('Signed, reply within 4 hours', 'pct', SB('Up to 4 hours')), O('Signed, reply within 24 hours', 'pct', SB('5 to 24 hours')), O('Signed, reply within 48 hours', 'pct', SB('25 to 48 hours')), O('Signed, reply after 48 hours', 'pct', SB('Over 48 hours')),
    O('Signed at your usual reply time', 'pct', YOURS), O('Contracts a month a reply within 4 hours adds', 'num', 'MAX(0,{in:enq}*(%s-%s))' % (SB('Up to 4 hours'), YOURS)),
    O('Value a month of those contracts', 'money', 'MAX(0,{in:enq}*(%s-%s))*{in:val}' % (SB('Up to 4 hours'), YOURS)), O('Your reply target, hours', 'int', '{set:reply_hours_target}'),
    O('Verdict', 'text', 'IF({in:hrs}>{set:reply_hours_target},%s,%s)' % (c2('Reply faster'), c2('Reply time on target')))],
    GR('What if', ('Reply in 2 hours', {'hrs': 2}), ('Reply in 30 hours', {'hrs': 30}), ('Reply in 60 hours', {'hrs': 60}), ('Twice the enquiries', {'enq': D.enq_month() * 2}))))

# 3 ------------------------------------------------------------ conversion funnel check
E3, CB3, CH3, SG3 = D.last3()
Q1 = 'IFERROR(({in:cb}/{in:enq})/%s,1)' % FUN6('own_book'); Q2 = 'IFERROR(({in:ch}/{in:cb})/%s,1)' % FUN6('own_held'); Q3 = 'IFERROR(({in:sg}/{in:ch})/%s,1)' % FUN6('own_sign')
QM = 'MIN(%s,%s,%s)' % (Q1, Q2, Q3)
tools.append(TOOL('funnel_tool', 'Conversion Funnel Check', 'Which step of the funnel leaks most',
    'Type the last 3 months from Funnel by Month (enquiries, consultations booked, held and contracts signed); each step is set against your own previous 6 months and the weakest step is named.', [
    I('enq', 'Enquiries, last 3 months', E3, 'int'), I('cb', 'Consultations booked', CB3, 'int'), I('ch', 'Consultations held', CH3, 'int'), I('sg', 'Contracts signed', SG3, 'int')], [
    O('Booked per enquiry', 'pct', 'IFERROR({in:cb}/{in:enq},0)'), O('Own booked per enquiry, 6 months', 'pct', FUN6('own_book')),
    O('Held per booked', 'pct', 'IFERROR({in:ch}/{in:cb},0)'), O('Own held per booked, 6 months', 'pct', FUN6('own_held')),
    O('Signed per consultation held', 'pct', 'IFERROR({in:sg}/{in:ch},0)'), O('Own signed per held, 6 months', 'pct', FUN6('own_sign')),
    O('Booking step against your own', 'num', Q1), O('Attendance step against your own', 'num', Q2), O('Signing step against your own', 'num', Q3),
    O('Contracts at your own 6-month rates', 'num', '{in:enq}*%s*%s*%s' % (FUN6('own_book'), FUN6('own_held'), FUN6('own_sign'))),
    O('Contracts you got less contracts at your own rates', 'num', '{in:sg}-{in:enq}*%s*%s*%s' % (FUN6('own_book'), FUN6('own_held'), FUN6('own_sign'))),
    O('Verdict', 'text', 'IF(%s>=0.95,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s)))' % (QM, c2('Funnel on track'), Q1, QM, c2('Fix consultation booking'), Q2, QM, c2('Fix consultation attendance'), c2('Fix signing after consultation')))],
    GR('What if', ('Fewer consultations booked', {'cb': round(CB3 * 0.7)}), ('More no-shows', {'ch': round(CH3 * 0.8)}), ('Fewer contracts signed', {'sg': round(SG3 * 0.6)}), ('Twice the enquiries, same bookings', {'enq': E3 * 2}))))

# 4 ------------------------------------------------------------ source conversion compare
N4 = 'COUNTIFS({range:enquiries.source},{in:src},%s)' % W6
S4 = 'COUNTIFS({range:enquiries.source},{in:src},%s,{range:enquiries.status},%s)' % (W6, SIGNED)
C4 = 'IFERROR(%s/%s,0)' % (S4, N4)
A4 = 'IFERROR(COUNTIFS(%s,{range:enquiries.status},%s)/COUNTIFS(%s),0)' % (W6, SIGNED, W6)
C12 = 'SUMIFS({range:source_conv.conversion},{range:source_conv.source},{in:src})'
tools.append(TOOL('source_compare', 'Source Conversion Compare', 'Is this source strong, average or weak',
    'Pick an enquiry source: its enquiries and contracts over the last 6 full months, set against all sources, with its 12-month conversion and rank; the verdict says strong, average or weak.', [
    IL('src', 'Enquiry source', 'source', 'Social media')], [
    O('Enquiries from this source, 6 months', 'int', N4), O('Contracts from this source', 'int', S4), O('Conversion of this source', 'pct', C4), O('Conversion of all sources', 'pct', A4),
    O('Difference from all sources', 'pct', '%s-%s' % (C4, A4)), O('Conversion over 12 months', 'pct', C12), O('Rank among the sources, 12 months', 'int', 'COUNTIFS({range:source_conv.conversion},">"&%s)+1' % C12),
    O('Enquiries over 12 months', 'int', 'SUMIFS({range:source_conv.enquiries},{range:source_conv.source},{in:src})'),
    O('Verdict', 'text', 'IF(%s<10,%s,IF(%s>=%s*1.1,%s,IF(%s<=%s*0.9,%s,%s)))' % (N4, c2('Average source'), C4, A4, c2('Strong source'), C4, A4, c2('Weak source'), c2('Average source')))],
    GR('What if', ('Care provider', {'src': '=' + tok('source', 'Care provider')}), ('Past client', {'src': '=' + tok('source', 'Past client')}), ('Class or workshop', {'src': '=' + tok('source', 'Class or workshop')}),
       ('Directory listing', {'src': '=' + tok('source', 'Directory listing')}), ('Support professional', {'src': '=' + tok('source', 'Support professional')}))))

# 5 ------------------------------------------------------------ lost-enquiry cause analyser
CNTR = lambda t: 'SUMIFS({range:lost_reasons.lost_enquiries},{range:lost_reasons.reason},%s)' % t
VALR = lambda t: 'SUMIFS({range:lost_reasons.quote_value_lost},{range:lost_reasons.reason},%s)' % t
RP, RF, RB_, RO, RN = (tok('lostreason', x) for x in ('Price', 'Date full', 'No backup', 'Chose someone else', 'No reply'))
MAXV = 'MAX(%s,%s,%s,%s,%s)' % (VALR(RP), VALR(RF), VALR(RB_), VALR(RO), VALR(RN))
DECL5 = 'IFERROR(SUMIFS({range:enquiries.declined},{range:enquiries.date},">="&({today}-{in:days}))/COUNTIFS({range:enquiries.date},">="&({today}-{in:days})),0)'
tools.append(TOOL('lost_cause', 'Lost-Enquiry Cause Analyser', 'Which lost-enquiry cause is worth fixing first',
    'Lost enquiries of the last 12 months by cause with the value of the quotes lost, side by side; type the days for the declined share and the share of the top cause you could win back; the verdict names the cause to fix first.', [
    I('days', 'Days for the declined share', 90, 'int'), I('fix', 'Share of the top cause you could win back', 0.25, 'pct')], [
    O('Lost to price, enquiries', 'int', CNTR(RP)), O('Lost to price, quote value', 'money', VALR(RP)), O('Lost to date full, enquiries', 'int', CNTR(RF)), O('Lost to date full, quote value', 'money', VALR(RF)),
    O('Lost to no backup, enquiries', 'int', CNTR(RB_)), O('Lost to no backup, quote value', 'money', VALR(RB_)), O('Chose someone else, enquiries', 'int', CNTR(RO)), O('Chose someone else, quote value', 'money', VALR(RO)),
    O('Lost to no reply, enquiries', 'int', CNTR(RN)), O('Total quote value lost, 12 months', 'money', 'SUM({range:lost_reasons.quote_value_lost})'),
    O('Quote value of the top cause', 'money', MAXV), O('Quote value won back a year', 'money', '{in:fix}*%s' % MAXV),
    O('Declined share of enquiries (date full or no backup)', 'pct', DECL5), O('Highest declined share you accept', 'pct', '{set:declined_max}'),
    O('Declined check', 'text', 'IF(%s>{set:declined_max},%s,%s)' % (DECL5, c2('Declined share above setting'), c2('Declined share within setting'))),
    O('Verdict', 'text', 'IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s))))' % (VALR(RP), MAXV, c2('Fix price first'), VALR(RF), MAXV, c2('Fix date capacity first'), VALR(RB_), MAXV, c2('Fix backup cover first'),
                                                                                     VALR(RO), MAXV, c2('Fix the pitch first'), c2('Fix reply time first')))],
    GR('What if', ('Declined share over 30 days', {'days': 30}), ('Declined share over 180 days', {'days': 180}), ('Win back half', {'fix': 0.5}), ('Win back a tenth', {'fix': 0.1}))))

# 6 ------------------------------------------------------------ price-lost break-even
LOSTP = 'SUMIFS({range:lost_reasons.lost_enquiries},{range:lost_reasons.reason},%s)' % RP
BE6 = 'ROUNDUP({in:disc}*{in:signed}/(1-{in:disc}),0)'
tools.append(TOOL('price_lost', 'Price-Lost Break-Even', 'Does a discount win back enough price-lost enquiries',
    'Type the discount, the contracts you sign in a year, the average quote and the share of price-lost enquiries you expect to win back; the break-even number is worked out in closed form against your price-lost enquiries of the last 12 months.', [
    I('disc', 'Discount', 0.05, 'pct'), I('signed', 'Contracts signed in a year', D.signed_12m(), 'int'), I('price', 'Average quote', D.avg_quote()), I('winback', 'Share of price-lost enquiries you expect to win back', 0.25, 'pct')], [
    O('Price given up a year by the discount', 'money', '{in:disc}*{in:signed}*{in:price}'), O('Value of one enquiry won back', 'money', '{in:price}*(1-{in:disc})'),
    O('Enquiries to win back to break even', 'int', BE6), O('Price-lost enquiries, last 12 months', 'int', LOSTP), O('Enquiries you expect to win back', 'num', '%s*{in:winback}' % LOSTP),
    O('Share of price-lost enquiries needed to break even', 'pct', 'IFERROR(%s/%s,0)' % (BE6, LOSTP)),
    O('Gained less given up, a year', 'money', '%s*{in:winback}*{in:price}*(1-{in:disc})-{in:disc}*{in:signed}*{in:price}' % LOSTP),
    O('Verdict', 'text', 'IF(%s*{in:winback}>=%s,%s,%s)' % (LOSTP, BE6, c2('Worth it'), c2('Not worth it')))],
    GR('What if', ('Discount of 10 percent', {'disc': 0.10}), ('Discount of 3 percent', {'disc': 0.03}), ('Win back a tenth', {'winback': 0.10}), ('Only new quotes get it', {'signed': 20}), ('Average quote 1,500', {'price': 1500}))))

# 7 ------------------------------------------------------------ consultation follow-up scheduler
DAYS7 = '({today}-{in:cd})'
tools.append(TOOL('follow_sched', 'Consult Follow-Up Scheduler', 'What to do after a consultation today',
    'Type the consultation date and the outcome; see the days since, the follow-up date and the next step (call, write, close or wait), with your own follow-up count for the next days.', [
    I('cd', 'Consultation date', ago(7), 'date'), IL('oc', 'Outcome', 'outcome', 'Thinking')], [
    O('Days since the consultation', 'int', DAYS7), O('Follow-up date', 'date', '{in:cd}+{set:follow_up_days}'), O('Days to the follow-up date', 'int', '{in:cd}+{set:follow_up_days}-{today}'),
    O('Consultations still thinking, last 30 days', 'int', 'COUNTIFS({range:consults.outcome},%s,{range:consults.date},">="&({today}-30),{range:consults.date},"<="&{today})' % O_THINK),
    O('Follow-ups due today', 'int', 'COUNTIFS({range:consults.follow_up_on},{today})'), O('Follow-ups due in the next 7 days', 'int', 'COUNTIFS({range:consults.follow_up_on},">"&{today},{range:consults.follow_up_on},"<="&({today}+7))'),
    O('Signed share of consultations held, 90 days', 'pct', 'IFERROR(COUNTIFS({range:consults.outcome},%s,{range:consults.date},">="&({today}-90),{range:consults.date},"<="&{today})/COUNTIFS({range:consults.held},1,{range:consults.date},">="&({today}-90),{range:consults.date},"<="&{today}),0)' % O_SIGNED),
    O('Verdict', 'text', 'IF({in:oc}=%s,%s,IF({in:oc}=%s,%s,IF({in:oc}=%s,%s,IF({in:oc}=%s,%s,IF(%s<{set:follow_up_days},%s,IF(%s<2*{set:follow_up_days},%s,IF(%s<6*{set:follow_up_days},%s,%s)))))))' % (
        O_SIGNED, ns('Welcome the new client'), O_DECL, ns('Close the enquiry'), O_NOSHOW, ns('Offer another time'), O_BOOKED, ns('Not due yet'), DAYS7, ns('Not due yet'), DAYS7, ns('Call today'), DAYS7, ns('Write today'), ns('Close the enquiry')))],
    GR('What if', ('Thinking for 3 days', {'cd': '={today}-3'}), ('Thinking for 12 days', {'cd': '={today}-12'}), ('Thinking for 40 days', {'cd': '={today}-40'}), ('Missed the consultation', {'oc': '=' + O_NOSHOW}), ('Signed', {'oc': '=' + O_SIGNED}))))

# 8 ------------------------------------------------------------ no-show impact
NSR = 'IFERROR(COUNTIFS({range:consults.date},">="&({today}-90),{range:consults.date},"<="&{today},{range:consults.outcome},%s)/COUNTIFS({range:consults.date},">="&({today}-90),{range:consults.date},"<="&{today},{range:consults.outcome},"<>"&%s),0)' % (O_NOSHOW, O_BOOKED)
tools.append(TOOL('noshow_tool', 'No-Show Impact', 'What consultation no-shows cost a month',
    'Type the consultations you book a month, the no-show rate to test, your signing rate after a consultation and the average quote; see the contracts and value lost, the extra slots to offer and the verdict against your no-show limit.', [
    I('booked', 'Consultations booked a month', D.booked_month(), 'int'), I('rate', 'No-show rate to test', 0.06, 'pct'), I('signrate', 'Signing rate after a consultation held', D.consult_sign_rate(), 'pct'), I('price', 'Average quote', D.avg_quote())], [
    O('Your no-show rate, last 90 days', 'pct', NSR), O('Highest no-show rate you accept', 'pct', '{set:noshow_max}'), O('No-shows a month at the tested rate', 'num', '{in:booked}*{in:rate}'),
    O('Contracts lost a month', 'num', '{in:booked}*{in:rate}*{in:signrate}'), O('Quote value lost a month', 'money', '{in:booked}*{in:rate}*{in:signrate}*{in:price}'),
    O('Slots to book for the same consultations held', 'int', 'ROUNDUP({in:booked}/(1-{in:rate}),0)'), O('Extra slots to offer a month', 'int', 'ROUNDUP({in:booked}/(1-{in:rate}),0)-{in:booked}'),
    O('Verdict', 'text', 'IF({in:rate}>{set:noshow_max},%s,%s)' % (c2('Overbook one slot'), c2('No-show rate is fine')))],
    GR('What if', ('No-show rate of 12 percent', {'rate': 0.12}), ('No-show rate of 20 percent', {'rate': 0.20}), ('Forty consultations a month', {'booked': 40}), ('Signing rate of 70 percent', {'signrate': 0.7}))))

# 9 ------------------------------------------------------------ consultation length vs signing
def BAND(lo, hi, sig=False):
    return 'COUNTIFS({range:consults.minutes},">"&%d,{range:consults.minutes},"<="&%d,{range:consults.held},1,{range:consults.date},%s%s)' % (lo, hi, Y12, (',{range:consults.outcome},%s' % O_SIGNED) if sig else '')
SH = lambda lo, hi: 'IFERROR(%s/%s,0)' % (BAND(lo, hi, True), BAND(lo, hi))
SH1, SH2, SH3, SH4 = SH(0, 25), SH(25, 35), SH(35, 45), SH(45, 999)
YOUR9 = 'IF({in:mins}<=25,%s,IF({in:mins}<=35,%s,IF({in:mins}<=45,%s,%s)))' % (SH1, SH2, SH3, SH4)
LONG9 = 'IF({in:mins}<=25,MAX(%s,%s,%s),IF({in:mins}<=35,MAX(%s,%s),IF({in:mins}<=45,%s,0)))' % (SH2, SH3, SH4, SH3, SH4, SH4)
tools.append(TOOL('length_tool', 'Consult Length vs Signing', 'Should consultations run longer',
    'Type the minutes you plan for a consultation; see the consultations held and the signed share in four length bands from your own last 12 months, and whether a longer band signs more.', [
    I('mins', 'Minutes you plan', 30, 'int')], [
    O('Held, up to 25 minutes', 'int', BAND(0, 25)), O('Signed share, up to 25 minutes', 'pct', SH1), O('Held, 26 to 35 minutes', 'int', BAND(25, 35)), O('Signed share, 26 to 35 minutes', 'pct', SH2),
    O('Held, 36 to 45 minutes', 'int', BAND(35, 45)), O('Signed share, 36 to 45 minutes', 'pct', SH3), O('Held, over 45 minutes', 'int', BAND(45, 999)), O('Signed share, over 45 minutes', 'pct', SH4),
    O('Signed share in your length band', 'pct', YOUR9), O('Best signed share in a longer band', 'pct', LONG9), O('Average minutes of consultations held', 'num', 'IFERROR(AVERAGEIFS({range:consults.minutes},{range:consults.held},1,{range:consults.date},%s),0)' % Y12),
    O('Verdict', 'text', 'IF(%s>%s+0.03,%s,%s)' % (LONG9, YOUR9, c2('Allow longer consultations'), c2('Keep your usual length')))],
    GR('What if', ('20 minutes', {'mins': 20}), ('40 minutes', {'mins': 40}), ('60 minutes', {'mins': 60}))))

# 10 ----------------------------------------------------------- due-month demand map
def _loads():
    out = {}
    for k in range(0, 18):
        m = add_months(month_start(0), k)
        cl = sum(1 for c in D.CLF if c['edd'].year == m.year and c['edd'].month == m.month and c['status'] != 'Cancelled' and c['kind'] != 'Postpartum')
        oq = sum(1 for e in D.ENF if e['edd_wanted'].year == m.year and e['edd_wanted'].month == m.month and e['service'] != 'Postpartum' and e['status'] in ('Consultation booked', 'Consultation held', 'Contract sent'))
        out[m] = cl + oq
    return out
LOADS = _loads()
PEAK = max(LOADS, key=lambda m: (LOADS[m], -m.toordinal()))
MM = 'DATE(YEAR({in:mth}),MONTH({in:mth}),1)'
DM = lambda c: 'SUMIFS({range:demand.%s},{range:demand.due_month},%s)' % (c, MM)
CAPX = '({set:agency_cap_month}+{in:extra})'
tools.append(TOOL('demand_map', 'Due-Month Demand Map', 'Can I take another due date in this month',
    'Pick a due month and the extra due dates you could take; see the enquiries wanting it, the clients booked, the open quotes and the spaces left against your monthly limit, with the verdict waitlist, open more dates or enough.', [
    I('mth', 'Due month', iso(PEAK), 'date'), I('extra', 'Extra due dates you could take', 0, 'int')], [
    O('Enquiries wanting this month', 'int', DM('enquiries_wanting')), O('Clients booked for this month', 'int', DM('clients_booked')), O('Open quotes for this month', 'int', DM('open_quotes')),
    O('Load, booked plus open quotes', 'int', DM('load')), O('Most due dates you take, with the extra', 'int', CAPX), O('Spaces left', 'int', '%s-%s' % (CAPX, DM('load'))),
    O('Months above your limit, next 18', 'int', 'COUNTIFS({range:demand.cap_flag},%s)' % c2('Waitlist these dates')), O('Months with room for more, next 18', 'int', 'COUNTIFS({range:demand.cap_flag},%s)' % c2('Open more dates')),
    O('Verdict', 'text', 'IF(%s>%s,%s,IF(%s<=0.6*%s,%s,%s))' % (DM('load'), CAPX, c2('Waitlist these dates'), DM('load'), CAPX, c2('Open more dates'), c2('Enough for now')))],
    GR('What if', ('Take 2 extra dates', {'extra': 2}), ('Take 4 extra dates', {'extra': 4}), ('Next month', {'mth': '=DATE(YEAR({today}),MONTH({today})+1,1)'}), ('Six months ahead', {'mth': '=DATE(YEAR({today}),MONTH({today})+6,1)'}), ('Twelve months ahead', {'mth': '=DATE(YEAR({today}),MONTH({today})+12,1)'}))))

# 11 ----------------------------------------------------------- discount cost tool
QS = lambda c, extra='': 'SUMIFS({range:quotes.%s},{range:quotes.status},%s,{range:quotes.quote_date},">="&EDATE(%s,-12)%s)' % (c, Q_SIGNED, MS, extra)
QC = lambda extra: 'COUNTIFS({range:quotes.status},%s,{range:quotes.quote_date},">="&EDATE(%s,-12)%s)' % (Q_SIGNED, MS, extra)
DK = lambda t: ',{range:quotes.discount},%s' % t
LISTS = QS('list_price')
tools.append(TOOL('discount_cost', 'Discount Cost Tool', 'What the community and returning-client discounts cost',
    'Type the discount rates to test and the most you accept to give up as a share of list price; see what contracts signed in the last 12 months gave up, per discounted contract, and what the tested rates would give up.', [
    I('comm', 'Community rate to test', 0.15, 'pct'), I('ret', 'Returning client discount to test', 0.10, 'pct'), I('cap', 'Most you accept to give up, share of list price', 0.04, 'pct')], [
    O('List price of contracts signed, 12 months', 'money', LISTS), O('Price given up, 12 months', 'money', QS('discount_amount')), O('Share of list price given up', 'pct', 'IFERROR(%s/%s,0)' % (QS('discount_amount'), LISTS)),
    O('Community rate contracts', 'int', QC(DK(D_COMM))), O('Returning client contracts', 'int', QC(DK(D_RET))),
    O('Price given up per discounted contract', 'money', 'IFERROR(%s/(%s+%s),0)' % (QS('discount_amount'), QC(DK(D_COMM)), QC(DK(D_RET)))),
    O('Price given up at the rates you typed', 'money', '%s*{in:comm}+%s*{in:ret}' % (QS('list_price', DK(D_COMM)), QS('list_price', DK(D_RET)))),
    O('Change against the rates now', 'money', '%s*{in:comm}+%s*{in:ret}-%s' % (QS('list_price', DK(D_COMM)), QS('list_price', DK(D_RET)), QS('discount_amount'))),
    O('Most you accept to give up', 'money', '{in:cap}*%s' % LISTS), O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)<={in:cap},%s,%s)' % (QS('discount_amount'), LISTS, c3('Keep the discounts'), c3('Cap the discounts')))],
    GR('What if', ('Limit of 2 percent', {'cap': 0.02}), ('Community rate of 10 percent', {'comm': 0.10}), ('Both discounts at 5 percent', {'comm': 0.05, 'ret': 0.05}), ('Limit of 8 percent', {'cap': 0.08}))))

# 12 ----------------------------------------------------------- enquiry pipeline forecast
R1_, R2_, R3_ = FUN6('own_book'), FUN6('own_held'), FUN6('own_sign')
PQ = lambda st: 'COUNTIFS({range:enquiries.quote},">0",{range:enquiries.status},%s,%s)' % (st, W6)
PS = 'IFERROR(%s/(%s+%s),0)' % (PQ(SIGNED), PQ(SIGNED), PQ(LOST))
NN, NB, NH, NS = ('COUNTIFS({range:enquiries.status},%s)' % s for s in (NEWE, BOOKE, HELDE, SENTE))
FAC = 'IF({in:scn}=%s,1.2,IF({in:scn}=%s,0.75,1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
EXP = '%s*(%s*%s*%s*%s+%s*%s*%s+%s*%s+%s*%s)' % (FAC, NN, R1_, R2_, R3_, NB, R2_, R3_, NH, R3_, NS, PS)
tools.append(TOOL('pipeline_fc', 'Enquiry Pipeline Forecast', 'How many contracts will the open enquiries give in 30 days',
    'Pick a Base, Best or Worst scenario: the open enquiries at each step are multiplied by your own rates of the last 6 months to give the expected contracts in the next 30 days, set against what you want from the open pipeline.', [
    IL('scn', 'Scenario', 'scen', 'Base'), I('need', 'Contracts you want from the open pipeline', 6, 'int')], [
    O('Open enquiries, new', 'int', NN), O('Open enquiries, consultation booked', 'int', NB), O('Open enquiries, consultation held', 'int', NH), O('Open enquiries, contract sent', 'int', NS),
    O('Chance a new enquiry signs', 'pct', '%s*%s*%s' % (R1_, R2_, R3_)), O('Chance a booked consultation signs', 'pct', '%s*%s' % (R2_, R3_)), O('Chance after a consultation held', 'pct', R3_), O('Chance a quote is signed', 'pct', PS),
    O('Expected contracts, next 30 days', 'num', EXP), O('Expected quote value of those contracts', 'money', '%s*IFERROR(AVERAGEIFS({range:quotes.quote_total},{range:quotes.quote_date},">="&({today}-90)),0)' % EXP),
    O('Your usual contracts in 30 days', 'num', 'COUNTIFS({range:enquiries.signed_on},">="&EDATE(%s,-6),{range:enquiries.signed_on},"<"&%s)/6' % (MS, MS)),
    O('Verdict', 'text', 'IF(%s>={in:need},%s,%s)' % (EXP, c3('Pipeline on pace'), c3('Quiet month ahead')))],
    GR('What if', ('Best scenario', {'scn': '=' + tok('scen', 'Best')}), ('Worst scenario', {'scn': '=' + tok('scen', 'Worst')}), ('You want 10 contracts', {'need': 10}), ('You want 3 contracts', {'need': 3}))))

# 13 ----------------------------------------------------------- quote expiry tracker
QEND = '{range:quotes.status},%s,{range:quotes.quote_date},">="&({today}-{in:valid}),{range:quotes.quote_date},"<="&({today}-{in:valid}+{in:win})' % Q_OPEN
QPAST = '{range:quotes.status},%s,{range:quotes.quote_date},"<"&({today}-{in:valid})' % Q_OPEN
tools.append(TOOL('expiry_tool', 'Quote Expiry Tracker', 'Which quotes end this week and what is at risk',
    'Type the days that count as ending soon and the days a quote stays valid; see the open quotes, the quotes ending in the window, the value at risk and the quotes already past their date, with the verdict chase now or let it lapse.', [
    I('win', 'Days that count as ending soon', 7, 'int'), I('valid', 'Days a quote stays valid', 14, 'int')], [
    O('Open quotes', 'int', 'COUNTIFS({range:quotes.status},%s)' % Q_OPEN), O('Value of open quotes', 'money', 'SUMIFS({range:quotes.quote_total},{range:quotes.status},%s)' % Q_OPEN),
    O('Quotes ending in the window', 'int', 'COUNTIFS(%s)' % QEND), O('Value at risk in the window', 'money', 'SUMIFS({range:quotes.quote_total},%s)' % QEND),
    O('Quotes already past their date', 'int', 'COUNTIFS(%s)' % QPAST), O('Value past its date', 'money', 'SUMIFS({range:quotes.quote_total},%s)' % QPAST),
    O('Expected value saved if you chase, at your quote win rate', 'money', 'SUMIFS({range:quotes.quote_total},%s)*IFERROR(COUNTIFS({range:enquiries.quote},">0",{range:enquiries.status},%s,%s)/(COUNTIFS({range:enquiries.quote},">0",{range:enquiries.status},%s,%s)+COUNTIFS({range:enquiries.quote},">0",{range:enquiries.status},%s,%s)),0)' % (QEND, SIGNED, W6, SIGNED, W6, LOST, W6)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)>0,%s,IF(COUNTIFS(%s)>0,%s,%s))' % (QEND, c3('Chase now'), QPAST, c3('Close lapsed quotes'), c3('No quote ending soon')))],
    GR('What if', ('Valid for 7 days', {'valid': 7}), ('Valid for 21 days', {'valid': 21}), ('Ending soon means 3 days', {'win': 3}), ('Ending soon means 14 days', {'win': 14}))))

# 14 ----------------------------------------------------------- package mix at quote
PM = lambda c: 'INDEX({range:packages.%s},MATCH({in:pk},{range:packages.package},0))' % c
WIN14 = PM('win_rate')
tools.append(TOOL('pkg_mix', 'Package Mix at Quote', 'Which package wins at the consultation',
    'Pick a package: its quotes and contracts of the last 12 months, its win rate against all packages with at least 10 quotes and its rank; the verdict says wins at consultation, keep in the lineup or rework.', [
    IL('pk', 'Package', 'package', 'Birth Plus')], [
    O('Quotes of this package, 12 months', 'int', PM('quotes_12m')), O('Contracts from this package', 'int', PM('signed_12m')), O('Win rate of this package', 'pct', WIN14),
    O('Win rate of all packages', 'pct', 'IFERROR(SUM({range:packages.signed_12m})/SUM({range:packages.quotes_12m}),0)'), O('Share of all quotes', 'pct', 'IFERROR(%s/SUM({range:packages.quotes_12m}),0)' % PM('quotes_12m')),
    O('Share of all contracts', 'pct', 'IFERROR(%s/SUM({range:packages.signed_12m}),0)' % PM('signed_12m')), O('Rank by win rate', 'int', 'COUNTIFS({range:packages.win_rate},">"&%s)+1' % WIN14),
    O('Package that wins most often', 'text', 'INDEX({range:packages.package},MATCH(MAX({range:packages.win_rate}),{range:packages.win_rate},0))'), O('Best win rate', 'pct', 'MAX({range:packages.win_rate})'),
    O('Verdict', 'text', 'IF(%s=MAX({range:packages.win_rate}),%s,IF(%s>=IFERROR(SUM({range:packages.signed_12m})/SUM({range:packages.quotes_12m}),0),%s,%s))' % (WIN14, c3('Wins at consultation'), WIN14, c3('Keep in the lineup'), c3('Rework or drop')))],
    GR('What if', ('Birth Essential', {'pk': '=' + tok('package', 'Birth Essential')}), ('Birth Premier', {'pk': '=' + tok('package', 'Birth Premier')}), ('Postpartum 40 Hours', {'pk': '=' + tok('package', 'Postpartum 40 Hours')}),
       ('Combined Plus', {'pk': '=' + tok('package', 'Combined Plus')}), ('Complete Care Bundle', {'pk': '=' + tok('package', 'Complete Care Bundle')}))))

# 15 ----------------------------------------------------------- service mix check
SVN = lambda s: 'COUNTIFS({range:enquiries.service},%s,{range:enquiries.area},{in:ar},{range:enquiries.date},%s)' % (tok('service', s), Y12)
SVS = lambda s: 'IFERROR(COUNTIFS({range:enquiries.service},%s,{range:enquiries.area},{in:ar},{range:enquiries.status},%s,{range:enquiries.date},%s)/%s,0)' % (tok('service', s), SIGNED, Y12, SVN(s))
PPSH = 'IFERROR(%s/(%s+%s+%s),0)' % (SVN('Postpartum'), SVN('Birth'), SVN('Postpartum'), SVN('Both'))
tools.append(TOOL('service_mix', 'Service Mix Check', 'Should I promote postpartum in this area',
    'Pick an area and the postpartum share of enquiries you want; see the enquiries and the signed share for birth, postpartum and both over the last 12 months, with the verdict promote postpartum or hold the mix.', [
    IL('ar', 'Service area', 'area', 'Northgate'), I('pps', 'Postpartum share of enquiries you want', 0.35, 'pct')], [
    O('Birth enquiries, 12 months', 'int', SVN('Birth')), O('Birth signed share', 'pct', SVS('Birth')), O('Postpartum enquiries, 12 months', 'int', SVN('Postpartum')), O('Postpartum signed share', 'pct', SVS('Postpartum')),
    O('Both-service enquiries, 12 months', 'int', SVN('Both')), O('Both-service signed share', 'pct', SVS('Both')), O('Postpartum share of enquiries', 'pct', PPSH),
    O('Postpartum enquiries to add to reach your share', 'int', 'MAX(0,ROUNDUP({in:pps}*(%s+%s+%s)/(1-{in:pps})-%s,0))' % (SVN('Birth'), SVN('Postpartum'), SVN('Both'), SVN('Postpartum'))),
    O('Verdict', 'text', 'IF(AND(%s>=%s,%s<{in:pps}),%s,%s)' % (SVS('Postpartum'), SVS('Birth'), PPSH, c3('Promote postpartum'), c3('Hold the mix')))],
    GR('What if', ('Southbank', {'ar': '=' + tok('area', 'Southbank')}), ('Share wanted 20 percent', {'pps': 0.20}), ('Share wanted 50 percent', {'pps': 0.50}))))

# 16 ----------------------------------------------------------- area demand and travel
AREAV = lambda c: 'SUMIFS({range:areas.%s},{range:areas.area},{in:ar})' % c
COSTV = '2*%s*%s*{in:visits}' % (AREAV('miles_one_way'), AREAV('mileage_rate'))
FEE = 'IFERROR(AVERAGEIFS({range:quotes.travel_fee},{range:quotes.area},{in:ar}),0)'
tools.append(TOOL('area_travel', 'Area Demand and Travel', 'Does this area need a travel fee in the quote',
    'Pick an area, the visits per client and the share of the mileage a travel fee should cover; see the enquiries from the area, the mileage cost per client and the travel fee you quote now, with the verdict add or hold.', [
    IL('ar', 'Service area', 'area', 'Northgate'), I('visits', 'Visits per client', 6, 'int'), I('cover', 'Share of the mileage a fee should cover', 0.5, 'pct')], [
    O('Enquiries from this area, 12 months', 'int', 'COUNTIFS({range:enquiries.area},{in:ar},{range:enquiries.date},%s)' % Y12), O('Share of all enquiries', 'pct', 'IFERROR(COUNTIFS({range:enquiries.area},{in:ar},{range:enquiries.date},%s)/COUNTIFS({range:enquiries.date},%s),0)' % (Y12, Y12)),
    O('Miles one way', 'int', AREAV('miles_one_way')), O('Mileage rate per mile', 'money', AREAV('mileage_rate')), O('Mileage cost of one round trip', 'money', '2*%s*%s' % (AREAV('miles_one_way'), AREAV('mileage_rate'))),
    O('Mileage cost per client', 'money', COSTV), O('Travel fee you quote now, average', 'money', FEE), O('Travel fee needed to cover your share', 'money', '{in:cover}*%s' % COSTV),
    O('Fee short by', 'money', 'MAX(0,{in:cover}*%s-%s)' % (COSTV, FEE)), O('Verdict', 'text', 'IF(%s>={in:cover}*%s,%s,%s)' % (FEE, COSTV, c3('Hold the travel fee'), c3('Add a travel fee')))],
    GR('What if', ('Southbank', {'ar': '=' + tok('area', 'Southbank')}), ('Ten visits per client', {'visits': 10}), ('Fee covers all the mileage', {'cover': 1.0}), ('Fee covers a quarter', {'cover': 0.25}))))

# 17 ----------------------------------------------------------- instalment offer test
IC = lambda cond, sig: 'COUNTIFS({range:quotes.instalments},"%s",{range:quotes.quote_total},">="&{in:from},{range:quotes.status},"<>"&%s%s)' % (cond, Q_OPEN, (',{range:quotes.status},%s' % Q_SIGNED) if sig else '')
RW = 'IFERROR(%s/%s,0)' % (IC('>1', True), IC('>1', False)); RN_ = 'IFERROR(%s/%s,0)' % (IC('<=1', True), IC('<=1', False))
tools.append(TOOL('inst_offer', 'Instalment Offer Test', 'From which price should I offer instalments',
    'Type the quote total to start from; see the closed quotes (signed or lapsed) with and without a payment plan, the signing rate of each and the share of all contracts on a plan, with the verdict offer a plan or not needed.', [
    I('from', 'Quote total from', 1900)], [
    O('Closed quotes with a plan', 'int', IC('>1', False)), O('Signed with a plan', 'int', IC('>1', True)), O('Signing rate with a plan', 'pct', RW),
    O('Closed quotes without a plan', 'int', IC('<=1', False)), O('Signed without a plan', 'int', IC('<=1', True)), O('Signing rate without a plan', 'pct', RN_),
    O('Difference in signing rate', 'pct', '%s-%s' % (RW, RN_)),
    O('Contracts on a plan, share of all signed quotes', 'pct', 'IFERROR(COUNTIFS({range:quotes.instalments},">1",{range:quotes.status},%s)/COUNTIFS({range:quotes.status},%s),0)' % (Q_SIGNED, Q_SIGNED)),
    O('Verdict', 'text', 'IF(AND(%s>=5,%s>%s+0.05),%s,%s)' % (IC('>1', False), RW, RN_, c3('Offer a plan'), c3('A plan is not needed')))],
    GR('What if', ('From 1,000', {'from': 1000}), ('From 1,500', {'from': 1500}), ('From 2,500', {'from': 2500}), ('From 3,500', {'from': 3500}))))

# 18 ----------------------------------------------------------- reply coverage by weekday
WN = 'COUNTIFS({range:enquiries.weekday},{in:wd},{range:enquiries.date},%s)' % Y12
WA = 'IFERROR(AVERAGEIFS({range:enquiries.first_reply_hours},{range:enquiries.weekday},{in:wd},{range:enquiries.date},%s),0)' % Y12
OA = 'IFERROR(AVERAGEIFS({range:enquiries.first_reply_hours},{range:enquiries.date},%s),0)' % Y12
tools.append(TOOL('reply_cover', 'Reply Coverage by Weekday', 'Which weekday needs reply cover',
    'Pick a weekday: the enquiries that arrived on it, the average hours to a first reply and the share replied within your target over the last 12 months, against all days; the verdict says cover this weekday or fine.', [
    IL('wd', 'Weekday', 'wday', 'Saturday')], [
    O('Enquiries that arrived on this weekday', 'int', WN), O('Average hours to a first reply on this weekday', 'num', WA), O('Average hours to a first reply, all days', 'num', OA),
    O('This weekday against all days', 'num', 'IFERROR(%s/%s,0)' % (WA, OA)),
    O('Replied within your target on this weekday', 'pct', 'IFERROR(COUNTIFS({range:enquiries.weekday},{in:wd},{range:enquiries.reply_flag},%s,{range:enquiries.date},%s)/COUNTIFS({range:enquiries.weekday},{in:wd},{range:enquiries.reply_flag},"<>"&%s,{range:enquiries.date},%s),0)' % (ca('Reply in time'), Y12, ca('No reply yet'), Y12)),
    O('Your reply target, hours', 'int', '{set:reply_hours_target}'), O('Verdict', 'text', 'IF(%s>%s*1.25,%s,%s)' % (WA, OA, c3('Cover this weekday'), c3('Reply cover is fine')))],
    GR('What if', ('Monday', {'wd': '=' + tok('wday', 'Monday')}), ('Wednesday', {'wd': '=' + tok('wday', 'Wednesday')}), ('Friday', {'wd': '=' + tok('wday', 'Friday')}), ('Sunday', {'wd': '=' + tok('wday', 'Sunday')}))))
assert len(tools) == 18, len(tools)
