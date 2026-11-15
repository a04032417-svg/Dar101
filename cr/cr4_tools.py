"""Car rental suite part 4: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr4_lists import *
import cr4_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def R(t, c): return '{range:%s.%s}' % (t, c)
def LKI(t, col, idc, inp, kind='N'):
    base = 'INDEX(%s,MATCH(%s,%s,0))' % (R(t, col), inp, R(t, idc))
    if kind == 'N': return 'IFERROR(%s,0)' % base
    if kind == 'T': return 'IFERROR(%s&"","")' % base
    return 'IFERROR(IF(%s=0,"",%s),"")' % (base, base)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
HELD = tok('depstatus', 'Held'); SHORT = tok('payoutstatus', 'Short-paid'); LATE = tok('payoutstatus', 'Late'); EXP = tok('payoutstatus', 'Expected')
CARD = tok('method', 'Card'); PAYO = tok('method', 'Marketplace payout'); KEEPC = c1('Keep for claim'); RELN = c1('Release now')
ST = D.ST
tools = []
LASTM = iso(month_start(1)); PREV = iso(month_start(2))
def DT(s): return '=DATE(%d,%d,%d)' % (int(s[:4]), int(s[5:7]), int(s[8:]))

# 1 ---------------------------------------------------------------- deposit and hold tracker
N1 = 'COUNTIFS(%s,%s)' % (R('deposits', 'verdict'), RELN)
WIN1 = '%s,">"&{today},%s,"<="&({today}+{in:look})' % (R('deposits', 'release_due'), R('deposits', 'release_due'))
tools.append(TOOL('dep_tracker', 'Deposit and Hold Tracker', 'Which holds do I release today',
    'Type how many days to look ahead and a deposit number; the holds taken, the amount held now and the holds to release appear, with the release status of that deposit.', [
    I('look', 'Look ahead, days', 7, 'int'), I('dep', 'Deposit to check', ST['claim_deposit_id'], 'text')], [
    O('Holds held now', 'int', 'COUNTIFS(%s,%s)' % (R('deposits', 'status'), HELD)), O('Liability held now', 'money', 'SUMIFS(%s,%s,%s)' % (R('deposits', 'amount'), R('deposits', 'status'), HELD)),
    O('Holds to release now', 'int', N1), O('Amount to release now', 'money', 'SUMIFS(%s,%s,%s)' % (R('deposits', 'amount'), R('deposits', 'verdict'), RELN)),
    O('Holds past the release date', 'int', 'COUNTIFS(%s,">0")' % R('deposits', 'days_over')),
    O('Holds due in the look-ahead days', 'int', 'COUNTIFS(%s,%s,%s)' % (R('deposits', 'status'), HELD, WIN1)),
    O('Amount due in the look-ahead days', 'money', 'SUMIFS(%s,%s,%s,%s)' % (R('deposits', 'amount'), R('deposits', 'status'), HELD, WIN1)),
    O('Deposit status', 'text', LKI('deposits', 'status', 'deposit_id', '{in:dep}', 'T')), O('Release due', 'date', LKI('deposits', 'release_due', 'deposit_id', '{in:dep}', 'D')),
    O('Days past the release date', 'int', LKI('deposits', 'days_over', 'deposit_id', '{in:dep}')), O('Amount held or kept', 'money', LKI('deposits', 'amount', 'deposit_id', '{in:dep}')),
    O('Kept amount', 'money', LKI('deposits', 'kept_amount', 'deposit_id', '{in:dep}')), O('Refunded amount', 'money', LKI('deposits', 'refunded_amount', 'deposit_id', '{in:dep}')),
    O('Release verdict of this deposit', 'text', LKI('deposits', 'verdict', 'deposit_id', '{in:dep}', 'T')),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (N1, c2('Release holds now'), c2('All holds current')))],
    GR('What if', ('Look ahead 3 days', {'look': 3}), ('Look ahead 14 days', {'look': 14}), ('Look ahead 30 days', {'look': 30}))))

# 2 ---------------------------------------------------------------- holds due this week
HK = R('deposits', 'hold_key')
OV2 = 'COUNTIFS(%s,"<"&({today}-0.5))' % HK
NTH2 = lambda k: 'IFERROR(IF(SMALL(%s,%s+%d)<{today}+{in:days}+0.5,INDEX(%s,MATCH(SMALL(%s,%s+%d),%s,0)),""),"")' % (HK, OV2, k, R('deposits', 'deposit_id'), HK, OV2, k, HK)
NTHV = lambda k, col, fmt: 'IFERROR(IF(SMALL(%s,%s+%d)<{today}+{in:days}+0.5,INDEX(%s,MATCH(SMALL(%s,%s+%d),%s,0)),""),"")' % (HK, OV2, k, R('deposits', col), HK, OV2, k, HK)
CNT2 = 'COUNTIFS(%s,%s,%s,">="&{today},%s,"<="&({today}+{in:days}))' % (R('deposits', 'status'), HELD, R('deposits', 'release_due'), R('deposits', 'release_due'))
tools.append(TOOL('hold_week', 'Holds Due This Week', 'Which holds fall due in the next days, earliest first',
    'Type the days to look ahead; the held deposits that fall due are ranked by release date and amount, with the first three named.', [I('days', 'Look ahead, days', 7, 'int')], [
    O('Holds due in the look-ahead days', 'int', CNT2), O('Amount due', 'money', 'SUMIFS(%s,%s,%s,%s,">="&{today},%s,"<="&({today}+{in:days}))' % (R('deposits', 'amount'), R('deposits', 'status'), HELD, R('deposits', 'release_due'), R('deposits', 'release_due'))),
    O('Holds already past the date', 'int', 'COUNTIFS(%s,">0")' % R('deposits', 'days_over')),
    O('Release first: deposit', 'text', NTH2(1)), O('Release first: date', 'date', NTHV(1, 'release_due', 'date')), O('Release first: amount', 'money', NTHV(1, 'amount', 'money')),
    O('Second: deposit', 'text', NTH2(2)), O('Second: amount', 'money', NTHV(2, 'amount', 'money')), O('Third: deposit', 'text', NTH2(3)), O('Third: amount', 'money', NTHV(3, 'amount', 'money')),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (CNT2, c2('Release the first hold first'), c2('No holds due')))],
    GR('What if', ('Next 3 days', {'days': 3}), ('Next 14 days', {'days': 14}), ('Next 30 days', {'days': 30}))))

# 3 ---------------------------------------------------------------- past-release holds
OK = R('deposits', 'over_key')
M3 = 'MATCH(LARGE(%s,{in:rank}),%s,0)' % (OK, OK)
def P3(col, kind='N'):
    base = 'INDEX(%s,%s)' % (R('deposits', col), M3)
    return {'N': 'IFERROR(%s,0)' % base, 'T': 'IFERROR(%s&"","")' % base}[kind]
tools.append(TOOL('past_release', 'Past-Release Holds', 'Which past-release holds do I release or keep',
    'Holds past the release date are ranked by days overdue and amount; type the rank to see that deposit, its claim and what to do.', [I('rank', 'Rank to look at', 1, 'int')], [
    O('Holds past the release date', 'int', 'COUNTIFS(%s,">0")' % R('deposits', 'days_over')), O('Amount past the release date', 'money', 'SUMIFS(%s,%s,">0")' % (R('deposits', 'amount'), R('deposits', 'days_over'))),
    O('Of those, kept for a claim', 'int', 'COUNTIFS(%s,">0",%s,%s)' % (R('deposits', 'days_over'), R('deposits', 'verdict'), KEEPC)),
    O('Of those, to release now', 'int', 'COUNTIFS(%s,">0",%s,%s)' % (R('deposits', 'days_over'), R('deposits', 'verdict'), RELN)),
    O('Deposit at this rank', 'text', P3('deposit_id', 'T')), O('Booking', 'text', P3('booking_id', 'T')), O('Days past the release date', 'int', P3('days_over')), O('Amount held', 'money', P3('amount')),
    O('Has a claim, 1 for yes', 'int', 'IF(%s<>"",1,0)' % P3('claim_id', 'T')), O('Claim amount', 'money', P3('claim_amount')),
    O('Verdict', 'text', 'IF(%s="","",IF(%s<>"",%s,%s))' % (P3('deposit_id', 'T'), P3('claim_id', 'T'), KEEPC, RELN))],
    GR('What if', ('Second on the list', {'rank': 2}), ('Third on the list', {'rank': 3}), ('Fourth on the list', {'rank': 4}))))

# 4 ---------------------------------------------------------------- deposit liability against cash
LIAB = 'SUMIFS(%s,%s,%s)' % (R('deposits', 'amount'), R('deposits', 'status'), HELD)
LEFT = '(%s-SUM(%s)+SUMIFS(%s,%s,%s,%s,"<="&({today}+28)))' % (LIAB, R('forecast', 'deposits_out'), R('deposits', 'amount'), R('deposits', 'status'), HELD, R('deposits', 'verdict'))
LEFT = '(%s-INDEX(%s,1)-INDEX(%s,2)-INDEX(%s,3)-INDEX(%s,4))' % ((LIAB,) + (R('forecast', 'deposits_out'),) * 4)
tools.append(TOOL('liability_cash', 'Deposit Liability Against Cash', 'Is the money held for deposits covered by cash',
    'Type the cash at the bank and any amount you hold back; deposits held now are set against the cash floor and the lowest week of the cash forecast.', [
    I('cash_bank', 'Cash at the bank now', 24150), I('extra', 'Extra amount you hold back', 0)], [
    O('Liability held now', 'money', LIAB), O('Cash floor', 'money', '{set:cash_floor}'), O('Cash left after the liability', 'money', '{in:cash_bank}-%s-{in:extra}' % LIAB),
    O('Cash needed for liability and floor', 'money', '%s+{set:cash_floor}+{in:extra}' % LIAB), O('Cash to keep aside', 'money', 'MAX(0,%s+{set:cash_floor}+{in:extra}-{in:cash_bank})' % LIAB),
    O('Cash covers the liability, times', 'num', 'IFERROR({in:cash_bank}/%s,0)' % LIAB), O('Lowest forecast cash, four weeks', 'money', 'INDEX(%s,1)' % R('forecast', 'lowest_cash')),
    O('Liability left after four weeks of releases', 'money', LEFT), O('Lowest forecast cash less that liability', 'money', 'INDEX(%s,1)-%s' % (R('forecast', 'lowest_cash'), LEFT)),
    O('Verdict', 'text', 'IF(AND({in:cash_bank}-%s-{in:extra}>={set:cash_floor},INDEX(%s,1)-%s>={set:cash_floor}),%s,%s)' % (LIAB, R('forecast', 'lowest_cash'), LEFT, c2('Liability covered'), c2('Keep cash aside')))],
    GR('What if', ('Cash 15000', {'cash_bank': 15000}), ('Cash 12000', {'cash_bank': 12000}), ('Hold back 3000', {'extra': 3000}), ('Cash 30000', {'cash_bank': 30000}))))

# 5 ---------------------------------------------------------------- payout reconciliation
PF = lambda col: 'SUMIFS(%s,%s,{in:month},%s,{in:channel},%s,"<="&{today})' % (R('payouts', col), R('payouts', 'month'), R('payouts', 'channel'), R('payouts', 'expected_on'))
tools.append(TOOL('payout_recon', 'Payout Reconciliation Tool', 'Which payouts are short or late and what do I chase',
    'Pick a month and a marketplace: booking value, fee, expected and received payout and the difference; open short or late payouts of all months are named.', [
    I('month', 'Month', LASTM, 'date'), IL('channel', 'Marketplace', 'market', 'Marketplace A')], [
    O('Payouts due in the month', 'int', 'COUNTIFS(%s,{in:month},%s,{in:channel},%s,"<="&{today})' % (R('payouts', 'month'), R('payouts', 'channel'), R('payouts', 'expected_on'))),
    O('Booking value', 'money', PF('booking_value')), O('Marketplace fee', 'money', PF('fee')), O('Expected payout', 'money', PF('expected_payout')), O('Received payout', 'money', PF('received')),
    O('Difference', 'money', 'ROUND(%s-%s,2)' % (PF('received'), PF('expected_payout'))),
    O('Fee share charged', 'pct', 'IFERROR(%s/%s,0)' % (PF('fee'), PF('booking_value'))), O('Fee share agreed', 'pct', 'IFERROR(INDEX(%s,MATCH({in:channel},%s,0)),0)' % (R('channels', 'fee_pct'), R('channels', 'channel'))),
    O('Short or late payouts, all months', 'int', 'COUNTIFS(%s,%s)+COUNTIFS(%s,%s)' % (R('payouts', 'status'), SHORT, R('payouts', 'status'), LATE)), O('Amount to chase, all months', 'money', 'SUM(%s)' % R('payouts', 'gap')),
    O('Largest gap to chase', 'money', 'MAX(%s)' % R('payouts', 'gap')),
    O('Largest gap: payout', 'text', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0))&"","")' % (R('payouts', 'payout_id'), R('payouts', 'gap'), R('payouts', 'gap'))),
    O('Verdict', 'text', 'IF(SUM(%s)>0,%s,%s)' % (R('payouts', 'gap'), c2('Chase the difference'), c2('All payouts match')))],
    GR('What if', ('Marketplace B', {'channel': '=' + tok('market', 'Marketplace B')}), ('Two months ago', {'month': DT(PREV)}), ('Two months ago, B', {'month': DT(PREV), 'channel': '=' + tok('market', 'Marketplace B')}))))

# 6 ---------------------------------------------------------------- payout lateness
WINP = '%s,">="&({today}-{in:window})' % R('payouts', 'paid_on')
def AVGD(ch): return 'IFERROR(AVERAGEIFS(%s,%s,%s,%s),0)' % (R('payouts', 'days_to_pay'), R('payouts', 'channel'), ch, WINP)
PRO = 'IFERROR(INDEX(%s,MATCH({in:channel},%s,0)),0)' % (R('channels', 'payout_days'), R('channels', 'channel'))
AVG6 = AVGD('{in:channel}')
tools.append(TOOL('payout_late', 'Payout Lateness', 'Does this marketplace pay when it says it will',
    'Pick a marketplace and a window: the days from return to payout are set against the payout days the marketplace promises.', [
    IL('channel', 'Marketplace', 'market', 'Marketplace B'), I('window', 'Window, days', 120, 'int')], [
    O('Payout days promised', 'int', PRO), O('Average days from return to payout', 'num', AVG6), O('Days later than promised', 'num', '%s-%s' % (AVG6, PRO)),
    O('Payouts paid in the window', 'int', 'COUNTIFS(%s,{in:channel},%s)' % (R('payouts', 'channel'), WINP)),
    O('Paid more than the grace days late', 'int', 'COUNTIFS(%s,{in:channel},%s,%s,">"&{set:payout_grace_days})' % (R('payouts', 'channel'), WINP, R('payouts', 'days_late'))),
    O('Share paid late', 'pct', 'IFERROR(COUNTIFS(%s,{in:channel},%s,%s,">"&{set:payout_grace_days})/COUNTIFS(%s,{in:channel},%s),0)' % (R('payouts', 'channel'), WINP, R('payouts', 'days_late'), R('payouts', 'channel'), WINP)),
    O('Longest delay, days', 'int', 'SUMPRODUCT(MAX((%s={in:channel})*(%s>={today}-{in:window})*(%s-%s)))' % (R('payouts', 'channel'), R('payouts', 'paid_on'), R('payouts', 'paid_on'), R('payouts', 'expected_on'))),
    O('Average days, Marketplace A', 'num', AVGD(tok('market', 'Marketplace A'))), O('Average days, Marketplace B', 'num', AVGD(tok('market', 'Marketplace B'))),
    O('Verdict', 'text', 'IF(%s-%s>=1,%s,IF(%s-%s<=-1,%s,%s))' % (AVG6, PRO, c2('Pays later than promised'), AVG6, PRO, c2('Pays earlier than promised'), c2('Pays as promised')))],
    GR('What if', ('Marketplace A', {'channel': '=' + tok('market', 'Marketplace A')}), ('Last 60 days', {'window': 60}), ('Last 365 days', {'window': 365}))))

# 7 ---------------------------------------------------------------- marketplace fee share
FM = lambda col: 'IFERROR(INDEX(%s,MATCH({in:month},%s,0)),0)' % (R('feeshare', col), R('feeshare', 'month'))
SH = FM('fee_share'); S12 = FM('share_12m')
tools.append(TOOL('fee_trend', 'Marketplace Fee Share', 'Is the marketplace fee share of revenue rising',
    'Pick a month: the marketplace fees as a share of revenue are compared with your own last 12 months and the same month last year.', [
    I('month', 'Month', LASTM, 'date'), I('band', 'Steady band, share points', 0.003, 'pct')], [
    O('Marketplace fees in the month', 'money', FM('marketplace_fees')), O('Revenue in the month', 'money', FM('revenue')), O('Fee share of revenue', 'pct', SH), O('Fee share, last 12 months', 'pct', S12),
    O('Change against the 12 months', 'pct', '%s-%s' % (SH, S12)),
    O('Fee share, same month last year', 'pct', 'SUMIFS(%s,%s,EDATE({in:month},-12))' % (R('feeshare', 'fee_share'), R('feeshare', 'month'))),
    O('Fee share, three months before', 'pct', 'IFERROR(SUMIFS(%s,%s,">="&EDATE({in:month},-3),%s,"<"&{in:month})/SUMIFS(%s,%s,">="&EDATE({in:month},-3),%s,"<"&{in:month}),0)' % (
        R('feeshare', 'marketplace_fees'), R('feeshare', 'month'), R('feeshare', 'month'), R('feeshare', 'revenue'), R('feeshare', 'month'), R('feeshare', 'month'))),
    O('Hotel partner commission in the month', 'money', FM('hotel_commission')),
    O('Verdict', 'text', 'IF(%s>%s+{in:band},%s,IF(%s<%s-{in:band},%s,%s))' % (SH, S12, c2('Share rising'), SH, S12, c2('Share falling'), c2('Share steady')))],
    GR('What if', ('Two months ago', {'month': DT(PREV)}), ('Wider steady band', {'band': 0.01}), ('Narrow band', {'band': 0.001}))))

# 8 ---------------------------------------------------------------- invoice and balance chase
CK8 = R('invoices', 'chase_key')
M8 = 'MATCH(LARGE(%s,1),%s,0)' % (CK8, CK8)
def I8(col, kind='N'):
    base = 'INDEX(%s,%s)' % (R('invoices', col), M8)
    return {'N': 'IFERROR(%s,0)' % base, 'T': 'IFERROR(%s&"","")' % base, 'D': 'IFERROR(%s,"")' % base}[kind]
ID8 = I8('invoice_id', 'T')
CNT8 = 'COUNTIFS(%s,">="&{in:min_days},%s,">="&{in:min_balance})' % (R('invoices', 'days_overdue'), R('invoices', 'balance'))
tools.append(TOOL('inv_chase', 'Invoice and Balance Chase', 'Which account do I chase first',
    'Open balances sit in ageing buckets; the oldest overdue invoice is named with its account, promised date and last contact.', [
    I('min_days', 'Chase invoices at least this many days overdue', 7, 'int'), I('min_balance', 'and with a balance of at least', 100)], [
    O('Open balance', 'money', 'SUM(%s)' % R('invoices', 'balance')), O('Open invoices', 'int', 'COUNTIFS(%s,">0")' % R('invoices', 'balance'))] + [
    O('Balance, %s' % b, 'money', 'INDEX(%s,%d)' % (R('ageing', 'balance'), n + 1)) for n, b in enumerate(BUCKETS)] + [
    O('Invoices to chase', 'int', CNT8), O('Balance to chase', 'money', 'SUMIFS(%s,%s,">="&{in:min_days},%s,">="&{in:min_balance})' % (R('invoices', 'balance'), R('invoices', 'days_overdue'), R('invoices', 'balance'))),
    O('Chase first: account', 'text', I8('account', 'T')), O('Chase first: invoice', 'text', ID8), O('Balance', 'money', I8('balance')), O('Days overdue', 'int', I8('days_overdue')),
    O('Promised on', 'date', 'IFERROR(IF(INDEX(%s,MATCH(%s,%s,0))=0,"",INDEX(%s,MATCH(%s,%s,0))),"")' % (R('promises', 'promised_on'), ID8, R('promises', 'invoice_id'), R('promises', 'promised_on'), ID8, R('promises', 'invoice_id'))),
    O('Last contact', 'date', 'IFERROR(IF(INDEX(%s,MATCH(%s,%s,0))=0,"",INDEX(%s,MATCH(%s,%s,0))),"")' % (R('promises', 'last_contact'), ID8, R('promises', 'invoice_id'), R('promises', 'last_contact'), ID8, R('promises', 'invoice_id'))),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (CNT8, c2('Chase the oldest invoice first'), c2('Nothing overdue')))],
    GR('What if', ('Overdue 31 days or more', {'min_days': 31}), ('Balance of 300 or more', {'min_balance': 300}), ('Any overdue invoice', {'min_days': 1, 'min_balance': 0}))))

# 9 ---------------------------------------------------------------- invoice splitter
LN = D.inv_lines_d()
SPLIT_ID = next((r['invoice_id'] for r in LN if r['damage'] > 0 and D.inv_open(D.IVD[r['invoice_id']])), next(r['invoice_id'] for r in LN if r['damage'] > 0))
def L9(col, kind='N'): return LKI('inv_lines', col, 'invoice_id', '{in:inv}', kind)
tools.append(TOOL('inv_split', 'Invoice Splitter', 'Should I split this invoice into parts',
    'Type an invoice number and any amount the account disputes; the rental, fees and damage lines are shown, with what can be paid now.', [
    I('inv', 'Invoice to split', SPLIT_ID, 'text'), I('disputed', 'Other amount the account disputes', 0)], [
    O('Account', 'text', L9('account', 'T')), O('Invoice balance', 'money', L9('balance')), O('Rental line', 'money', L9('rental')), O('Add-ons and fees line', 'money', L9('addons_fees')), O('Damage line', 'money', L9('damage')),
    O('Total of the lines', 'money', L9('total')), O('Payable now without damage', 'money', 'IFERROR(%s+%s,0)' % (L9('rental'), L9('addons_fees'))),
    O('Amount that can be disputed alone', 'money', '%s+{in:disputed}' % L9('damage')), O('Share of the invoice that can be disputed', 'pct', 'IFERROR((%s+{in:disputed})/%s,0)' % (L9('damage'), L9('total'))),
    O('Lines on the split invoice', 'int', 'IF(%s>0,1,0)+IF(%s>0,1,0)+IF(%s+{in:disputed}>0,1,0)' % (L9('rental'), L9('addons_fees'), L9('damage'))),
    O('Verdict', 'text', 'IF(%s+{in:disputed}>0,%s,%s)' % (L9('damage'), c2('Send split invoice'), c2('One invoice is fine')))],
    GR('What if', ('Account disputes 100', {'disputed': 100}), ('Account disputes 500', {'disputed': 500}))))

# 10 --------------------------------------------------------------- promise tracker
PRD = D.promises_d()
ACC10 = next(D.IVD[r['invoice_id']]['account'] for r in PRD if r['outcome'] == 'pending')
PA = '(%s={in:account})' % R('promises', 'account'); PPEND = '(%s=%s)' % (R('promises', 'outcome'), tok('outcome', 'Pending'))
def CNT10(o): return 'COUNTIFS(%s,{in:account},%s,%s)' % (R('promises', 'account'), R('promises', 'outcome'), tok('outcome', o))
NEXT10 = 'SUMPRODUCT(MIN(%s*%s*%s+(1-%s*%s)*1000000))' % (PA, PPEND, R('promises', 'promised_on'), PA, PPEND)
tools.append(TOOL('promise_tool', 'Promise-to-Pay Tracker', 'Did this account keep its payment promises',
    'Pick a corporate account: promises kept and missed, the next promised date and the open balance give the next step.', [IL('account', 'Account', 'account', ACC10)], [
    O('Promises made', 'int', 'COUNTIFS(%s,{in:account})' % R('promises', 'account')), O('Promises kept', 'int', CNT10('Kept')), O('Promises missed', 'int', CNT10('Missed')), O('Promises pending', 'int', CNT10('Pending')),
    O('Share of promises kept', 'pct', 'IFERROR(%s/(%s+%s),0)' % (CNT10('Kept'), CNT10('Kept'), CNT10('Missed'))),
    O('Next promised date', 'date', 'IF(%s=0,"",%s)' % (CNT10('Pending'), NEXT10)), O('Amount promised, pending', 'money', 'SUMIFS(%s,%s,{in:account},%s,%s)' % (R('promises', 'amount'), R('promises', 'account'), R('promises', 'outcome'), tok('outcome', 'Pending'))),
    O('Days to the next promise', 'int', 'IF(%s=0,0,%s-{today})' % (CNT10('Pending'), NEXT10)), O('Open balance of the account', 'money', 'IFERROR(INDEX(%s,MATCH({in:account},%s,0)),0)' % (R('corporate', 'balance'), R('corporate', 'account'))),
    O('Verdict', 'text', 'IF(%s>0,IF(%s+{set:promise_grace_days}>={today},%s,%s),IF(%s>0,%s,%s))' % (CNT10('Pending'), NEXT10, c1('Chase on promised date'), c1('Escalate'), CNT10('Missed'), c1('Escalate'), c1('Promise kept')))],
    GR('What if', ('Account 2', {'account': '=' + tok('account', 'Corporate account 2')}), ('Account 4', {'account': '=' + tok('account', 'Corporate account 4')}), ('Account 6', {'account': '=' + tok('account', 'Corporate account 6')}))))

# 11 --------------------------------------------------------------- collection rate and days outstanding
def WIN(lo, hi): return '%s,">="&%s,%s,"<"&%s' % (R('invoices', 'due_date'), lo, R('invoices', 'due_date'), hi)
W_NOW = WIN(MS, 'EDATE(%s,1)' % MS); W_3 = WIN('EDATE(%s,-3)' % MS, MS); W_LY = WIN('EDATE(%s,-12)' % MS, 'EDATE(%s,-11)' % MS)
def BILL(w): return 'SUMIFS(%s,%s)' % (R('invoices', 'amount'), w)
def RATE(w): return 'IFERROR((SUMIFS(%s,%s)+SUMIFS(%s,%s))/%s,0)' % (R('invoices', 'paid_amount'), w, R('invoices', 'credit_amount'), w, BILL(w))
def DAYS(w, fb=None): return 'IFERROR(AVERAGEIFS(%s,%s),%s)' % (R('invoices', 'days_to_pay'), w, fb if fb else '0')
D3 = DAYS(W_3); DN = DAYS(W_NOW, D3)
tools.append(TOOL('collect_rate', 'Collection and Days Outstanding', 'Are accounts paying faster or slower than before',
    'Invoices due this month, in the last three months and in the same month last year: billed, collected share and average days to pay.', [I('target', 'Collection rate you want', 0.95, 'pct')], [
    O('Billed, due this month', 'money', BILL(W_NOW)), O('Collected share, due this month', 'pct', RATE(W_NOW)), O('Days to pay, due this month', 'num', DN),
    O('Billed, due in the last 3 months', 'money', BILL(W_3)), O('Collected share, last 3 months', 'pct', RATE(W_3)), O('Days to pay, last 3 months', 'num', D3),
    O('Billed, same month last year', 'money', BILL(W_LY)), O('Collected share, same month last year', 'pct', RATE(W_LY)), O('Days to pay, same month last year', 'num', DAYS(W_LY)),
    O('Days to pay, this month less last 3 months', 'num', '%s-%s' % (DN, D3)), O('Last 3 months against your target', 'pct', '%s-{in:target}' % RATE(W_3)),
    O('Verdict', 'text', 'IF(%s-%s>=1,%s,IF(%s-%s<=-1,%s,%s))' % (DN, D3, c2('Collecting slower'), DN, D3, c2('Collecting faster'), c2('Collecting steady')))],
    GR('What if', ('Target 90%', {'target': 0.9}), ('Target 99%', {'target': 0.99}))))

# 12 --------------------------------------------------------------- cash in by channel and day
DAY = iso(T0 - __import__('datetime').timedelta(days=1)) if False else ago(1)
def REC(m): return round(sum(p['amount'] for p in D.PAY if p['date'] == DAY and p['method'] == m), 2)
CARD_SET = round((REC('Card') + REC('Mobile wallet')) * (1 - CARD_FEE_PCT), 2); BANK_REC = round(REC('Bank transfer') + REC('Marketplace payout'), 2)
def PMD(m): return 'SUMIFS(%s,%s,{in:day},%s,%s)' % (R('payments', 'amount'), R('payments', 'date'), R('payments', 'method'), m)
def PCH(c): return 'SUMIFS(%s,%s,{in:day},%s,%s)' % (R('payments', 'amount'), R('payments', 'date'), R('payments', 'channel'), c)
EXPC = 'ROUND((%s+%s)*(1-{set:card_fee_pct}),2)' % (PMD(CARD), PMD(tok('method', 'Mobile wallet')))
EXPB = '(%s+%s)' % (PMD(tok('method', 'Bank transfer')), PMD(PAYO))
UNEX = 'ABS({in:card_set}-%s)+ABS({in:bank_rec}-%s)' % (EXPC, EXPB)
tools.append(TOOL('cash_reconcile', 'Cash In by Channel and Day', 'Does the money of this day match the card and bank reports',
    'Pick a day and type the card settlement and the bank credits; recorded payments are set against them, with the day split by channel.', [
    I('day', 'Day', DAY, 'date'), I('card_set', 'Card settlement received', CARD_SET), I('bank_rec', 'Bank credits received', BANK_REC)], [
    O('Card and wallet recorded', 'money', '%s+%s' % (PMD(CARD), PMD(tok('method', 'Mobile wallet')))), O('Cash recorded', 'money', PMD(tok('method', 'Cash'))), O('Bank transfers recorded', 'money', PMD(tok('method', 'Bank transfer'))), O('Marketplace payouts recorded', 'money', PMD(PAYO)),
    O('Total recorded', 'money', 'SUMIFS(%s,%s,{in:day})' % (R('payments', 'amount'), R('payments', 'date'))),
    O('Card settlement expected after fees', 'money', EXPC), O('Card difference', 'money', 'ROUND({in:card_set}-%s,2)' % EXPC), O('Bank credits expected', 'money', EXPB), O('Bank difference', 'money', 'ROUND({in:bank_rec}-%s,2)' % EXPB),
    O('Amount unexplained', 'money', 'ROUND(%s,2)' % UNEX), O('Total recorded, average day of the last 30', 'money', 'SUMIFS(%s,%s,">="&({today}-30),%s,"<"&{today})/30' % (R('payments', 'amount'), R('payments', 'date'), R('payments', 'date'))),
    O('Website', 'money', PCH(tok('channel', 'Website'))), O('Phone', 'money', PCH(tok('channel', 'Phone'))), O('Corporate account', 'money', PCH(tok('channel', 'Corporate account'))),
    O('Hotel partner', 'money', PCH(tok('channel', 'Hotel partner'))), O('Marketplace A', 'money', PCH(tok('channel', 'Marketplace A'))), O('Marketplace B', 'money', PCH(tok('channel', 'Marketplace B'))),
    O('Verdict', 'text', 'IF(%s<={set:till_tolerance},%s,%s)' % (UNEX, c2('Day total matches'), c2('Amount unexplained')))],
    GR('What if', ('Bank credits 120 short', {'bank_rec': round(BANK_REC - 120, 2)}), ('Card settlement 45 short', {'card_set': round(CARD_SET - 45, 2)}), ('Two days ago', {'day': DT(ago(2)), 'card_set': round(sum(p['amount'] for p in D.PAY if p['date'] == ago(2) and p['method'] in ('Card', 'Mobile wallet')) * (1 - CARD_FEE_PCT), 2),
        'bank_rec': round(sum(p['amount'] for p in D.PAY if p['date'] == ago(2) and p['method'] in ('Bank transfer', 'Marketplace payout')), 2)}))))

# 13 --------------------------------------------------------------- daily till check
TL = D.till_d()[13]
TCASH = 'SUMIFS(%s,%s,{in:day},%s,%s)' % (R('payments', 'amount'), R('payments', 'date'), R('payments', 'method'), tok('method', 'Cash'))
DIF13 = 'ROUND({in:drawer}-{in:float}-%s,2)' % TCASH
tools.append(TOOL('till_tool', 'Daily Till Check', 'Is the till balanced for this day',
    'Type the day, the cash in the drawer and the float; the cash expected comes from the cash payments of that day.', [
    I('day', 'Day', TL['date'], 'date'), I('drawer', 'Cash in the drawer', round(TL['counted'] + 100, 2)), I('float', 'Float left in the drawer', 100)], [
    O('Cash expected from payments', 'money', TCASH), O('Cash counted after the float', 'money', '{in:drawer}-{in:float}'), O('Difference', 'money', DIF13), O('Difference without sign', 'money', 'ABS(%s)' % DIF13),
    O('Cash payments of the day', 'int', 'COUNTIFS(%s,{in:day},%s,%s)' % (R('payments', 'date'), R('payments', 'method'), tok('method', 'Cash'))),
    O('Tills checked, last 30 days', 'int', 'COUNTIFS(%s,">="&({today}-30))' % R('till', 'date')), O('Tills balanced, last 30 days', 'int', 'COUNTIFS(%s,">="&({today}-30),%s,%s)' % (R('till', 'date'), R('till', 'verdict'), c1('Balanced'))),
    O('Difference added up, last 30 days', 'money', 'SUMIFS(%s,%s,">="&({today}-30))' % (R('till', 'difference'), R('till', 'date'))),
    O('Verdict', 'text', 'IF(ABS(%s)<={set:till_tolerance},%s,IF(%s<0,%s,%s))' % (DIF13, c1('Balanced'), DIF13, c1('Short'), c1('Over')))],
    GR('What if', ('Drawer 20 higher', {'drawer': round(TL['counted'] + 120, 2)}), ('Drawer matches', {'drawer': round(D.CASHDAY[TL['date']] + 100, 2)}), ('Float 150', {'float': 150}))))

# 14 --------------------------------------------------------------- four-week cash forecast
RF = 'IF({in:scen}=%s,1.05,IF({in:scen}=%s,0.85,1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
CF = 'IF({in:scen}=%s,1.05,IF({in:scen}=%s,0.8,1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
KF = 'IF({in:scen}=%s,0.97,IF({in:scen}=%s,1.1,1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
def FI(col, k): return 'INDEX(%s,%d)' % (R('forecast', col), k)
NET = lambda k: '(%s*%s+%s+%s*%s-%s-%s*%s)' % (FI('rentals_in', k), RF, FI('payouts', k), FI('invoices_in', k), CF, FI('deposits_out', k), FI('costs_out', k), KF)
CEND = lambda k: '({in:start}+%s)' % '+'.join(NET(j) for j in range(1, k + 1))
LOW = 'MIN(%s)' % ','.join(CEND(k) for k in range(1, 5))
tools.append(TOOL('cash_forecast_tool', 'Four-Week Cash Forecast', 'Does cash hold above the floor for the next four weeks',
    'Pick Base, Best or Worst and the cash at the bank; payouts, deposits to release, invoice receipts, rental receipts and costs give the cash at each week end.', [
    IL('scen', 'Scenario', 'scen', 'Base'), I('start', 'Cash at the bank now', 24150)], [
    O('Rental receipts factor', 'num', RF), O('Invoice collection factor', 'num', CF), O('Costs factor', 'num', KF)] + [
    O('Net, week %d' % k, 'money', 'ROUND(%s,0)' % NET(k)) for k in range(1, 5)] + [
    O('Cash at the end of week %d' % k, 'money', 'ROUND(%s,0)' % CEND(k)) for k in range(1, 5)] + [
    O('Lowest cash in the four weeks', 'money', 'ROUND(%s,0)' % LOW), O('Cash floor', 'money', '{set:cash_floor}'),
    O('Weeks below the floor', 'int', '+'.join('IF(%s<{set:cash_floor},1,0)' % CEND(k) for k in range(1, 5))),
    O('Verdict', 'text', 'IF(%s>={set:cash_floor},%s,%s)' % (LOW, c1('Cash holds'), c1('Below the floor')))],
    GR('Scenarios', ('Base', {'scen': '=' + tok('scen', 'Base')}), ('Best', {'scen': '=' + tok('scen', 'Best')}), ('Worst', {'scen': '=' + tok('scen', 'Worst')}), ('Worst with 8000 at the bank', {'scen': '=' + tok('scen', 'Worst'), 'start': 8000}))))

# 15 --------------------------------------------------------------- card fee check
CWIN = '%s,%s,%s,">="&({today}-{in:days})' % (R('payments', 'method'), CARD, R('payments', 'date'))
BIG = '%s,">="&{in:threshold}' % R('payments', 'amount')
BIGN = 'COUNTIFS(%s,%s)' % (CWIN, BIG)
BIGF = 'SUMIFS(%s,%s,%s)' % (R('payments', 'card_fee'), CWIN, BIG)
SAVE = '(%s-%s*{in:move_cost})' % (BIGF, BIGN)
tools.append(TOOL('card_fee', 'Card Fee Check', 'Should I offer bank transfer on long rentals',
    'Type the payment size you call a long rental, the window and the cost of a transfer; card fees on large payments are set against what a transfer would cost.', [
    I('threshold', 'Card payments of at least', 500), I('days', 'Window, days', 90, 'int'), I('move_cost', 'Cost of one bank transfer', 0.5), I('min_saving', 'Saving you need in the window', 50)], [
    O('Card payments in the window', 'int', 'COUNTIFS(%s)' % CWIN), O('Card amount in the window', 'money', 'SUMIFS(%s,%s)' % (R('payments', 'amount'), CWIN)),
    O('Card fees in the window', 'money', 'SUMIFS(%s,%s)' % (R('payments', 'card_fee'), CWIN)),
    O('Card share of all payments', 'pct', 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s,">="&({today}-{in:days})),0)' % (R('payments', 'amount'), CWIN, R('payments', 'amount'), R('payments', 'date'))),
    O('Large card payments', 'int', BIGN), O('Amount of large card payments', 'money', 'SUMIFS(%s,%s,%s)' % (R('payments', 'amount'), CWIN, BIG)), O('Fees on large card payments', 'money', BIGF),
    O('Saving if they moved to transfer', 'money', 'ROUND(%s,2)' % SAVE), O('Saving over a year', 'money', 'ROUND(%s*365/{in:days},0)' % SAVE),
    O('Share of all card fees saved', 'pct', 'IFERROR(%s/SUMIFS(%s,%s),0)' % (SAVE, R('payments', 'card_fee'), CWIN)),
    O('Verdict', 'text', 'IF(%s>={in:min_saving},%s,%s)' % (SAVE, c2('Offer transfer on long rentals'), c2('Keep cards')))],
    GR('What if', ('Large means 800 or more', {'threshold': 800}), ('Large means 300 or more', {'threshold': 300}), ('Transfer costs 3', {'move_cost': 3}), ('Last 30 days', {'days': 30}))))

# 16 --------------------------------------------------------------- corporate account credit check
ACC16 = max(D.ACCOUNTS, key=lambda a: sum(max(0, i['amount'] - i['paid_amount']) for i in D.IV if i['account'] == a and D.inv_open(i) and i['due_date'] > D.ago(30)))
ACC16 = D.IVD['IV-0281']['account']
BAL16 = 'IFERROR(INDEX(%s,MATCH({in:account},%s,0)),0)' % (R('corporate', 'balance'), R('corporate', 'account'))
AVG16 = 'IFERROR(INDEX(%s,MATCH({in:account},%s,0)),0)' % (R('corporate', 'avg_days'), R('corporate', 'account'))
OV30 = 'SUMIFS(%s,%s,{in:account},%s,">30")' % (R('invoices', 'balance'), R('invoices', 'account'), R('invoices', 'days_overdue'))
tools.append(TOOL('credit_check', 'Corporate Account Credit Check', 'Do I extend credit to this account for a new booking',
    'Pick an account and the value of a new booking; the open balance, overdue amount and average days to pay are set against your credit limit.', [
    IL('account', 'Account', 'account', ACC16), I('new_booking', 'Value of the new booking', 900), I('max_days', 'Average days to pay you accept', 40, 'int')], [
    O('Open balance', 'money', BAL16), O('Overdue balance', 'money', 'SUMIFS(%s,%s,{in:account},%s,">0")' % (R('invoices', 'balance'), R('invoices', 'account'), R('invoices', 'days_overdue'))),
    O('Balance more than 30 days overdue', 'money', OV30), O('Average days to pay', 'num', AVG16), O('Credit limit', 'money', '{set:credit_limit}'),
    O('Balance after the new booking', 'money', '%s+{in:new_booking}' % BAL16), O('Share of the limit used after it', 'pct', 'IFERROR((%s+{in:new_booking})/{set:credit_limit},0)' % BAL16),
    O('Room left under the limit', 'money', '{set:credit_limit}-%s' % BAL16),
    O('Verdict', 'text', 'IF(%s>0,%s,IF(OR(%s+{in:new_booking}>{set:credit_limit},%s>{in:max_days}),%s,%s))' % (OV30, c2('Ask for payment'), BAL16, AVG16, c2('Hold new bookings'), c2('Extend credit')))],
    GR('What if', ('New booking 3000', {'new_booking': 3000}), ('Account 2', {'account': '=' + tok('account', 'Corporate account 2')}), ('Account 5', {'account': '=' + tok('account', 'Corporate account 5')}), ('Account 6, booking 2500', {'account': '=' + tok('account', 'Corporate account 6'), 'new_booking': 2500}))))

# 17 --------------------------------------------------------------- deposit kept check
SUP17 = '({in:fees}+{in:claim})'
tools.append(TOOL('kept_check', 'Deposit Kept Check', 'Is the amount kept from a deposit backed by fees and claims',
    'Type the amount kept, the fees collected and the claim amount of one booking; the Kept Deposits sheet shows the same check for every kept deposit.', [
    I('kept', 'Amount kept', 120), I('fees', 'Fees collected for the booking', 45), I('claim', 'Claim amount for the booking', 75)], [
    O('Fees plus claim', 'money', SUP17), O('Amount to explain', 'money', 'MAX(0,ROUND({in:kept}-%s,2))' % SUP17), O('Share of the kept amount that is backed', 'pct', 'IFERROR(MIN(1,%s/{in:kept}),0)' % SUP17),
    O('Kept deposits checked', 'int', 'COUNTA(%s)' % R('kept', 'deposit_id')), O('Kept deposits to explain', 'int', 'COUNTIFS(%s,%s)' % (R('kept', 'check'), c1('Amount to explain'))),
    O('Amount to explain, all kept deposits', 'money', 'SUM(%s)' % R('kept', 'unexplained')),
    O('Share of kept deposits backed', 'pct', 'IFERROR(COUNTIFS(%s,%s)/COUNTA(%s),0)' % (R('kept', 'check'), c1('Kept amount supported'), R('kept', 'deposit_id'))),
    O('Verdict', 'text', 'IF(MAX(0,ROUND({in:kept}-%s,2))<={set:till_tolerance},%s,%s)' % (SUP17, c1('Kept amount supported'), c1('Amount to explain')))],
    GR('What if', ('Keep 150', {'kept': 150}), ('Keep 250, no claim', {'kept': 250, 'claim': 0}), ('Keep 45, fees only', {'kept': 45, 'claim': 0}))))

# 18 --------------------------------------------------------------- invoice write-off review
OVB = 'SUMIFS(%s,%s,">"&{in:days})' % (R('invoices', 'balance'), R('invoices', 'days_overdue'))
BILLED = 'SUM(%s)' % R('invoices', 'amount')
AFTER = 'IFERROR((SUM(%s)+%s)/%s,0)' % (R('invoices', 'written_off'), OVB, BILLED)
tools.append(TOOL('writeoff', 'Invoice Write-off Review', 'Do I write off the old balances or keep chasing',
    'Type the age in days and the most you accept to write off as a share of billing; old balances are set against what is already written off.', [
    I('days', 'Balance overdue more than, days', 90, 'int'), I('limit', 'Most you accept to write off, share of billed', 0.01, 'pct')], [
    O('Balance overdue more than the days', 'money', OVB), O('Invoices over that age', 'int', 'COUNTIFS(%s,">"&{in:days},%s,">0")' % (R('invoices', 'days_overdue'), R('invoices', 'balance'))),
    O('Total billed', 'money', BILLED), O('Written off so far', 'money', 'SUM(%s)' % R('invoices', 'written_off')), O('Written off so far, share of billed', 'pct', 'IFERROR(SUM(%s)/%s,0)' % (R('invoices', 'written_off'), BILLED)),
    O('Share written off if you write off now', 'pct', AFTER), O('Amount to write off', 'money', OVB),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<={in:limit},%s,%s))' % (OVB, c2('Nothing overdue'), AFTER, c2('Write off the balance'), c2('Keep chasing')))],
    GR('What if', ('Over 60 days', {'days': 60}), ('Limit 0.5%', {'limit': 0.005}), ('Over 30 days, limit 2%', {'days': 30, 'limit': 0.02}))))
assert len(tools) == 18, len(tools)
