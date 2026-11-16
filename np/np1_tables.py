"""Nonprofit suite part 1: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np1_lists import *
import np1_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def ORG(): return CA('org', 'Organization', 'text', '{set:org}', 22)
def LIT(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def DEVPH(): return LIT('dev_phone', 'Development manager phone', D.DEV_PHONE)
def BOOKPH(): return LIT('bookkeeper_phone', 'Bookkeeper phone', D.BOOK_PHONE)
def ACCPH(): return LIT('accountant_phone', 'Accountant phone', D.ACC_PHONE)
def DON(col, my='donor_id', w=22, label=None, fmt='text'): return CA(col, label or col.replace('_', ' ').capitalize(), fmt, LKT('donors.' + col, 'donors.donor_id', my), w)
def DONPH(my='donor_id'): return CA('phone', 'Donor phone', 'text', LKT('donors.phone', 'donors.donor_id', my), 18)

MS = 'DATE(YEAR({today}),MONTH({today}),1)'
Y0F = 'DATE(YEAR({today}),1,1)'
ONE = tok('gtype', 'One-time'); REC = tok('gtype', 'Recurring')
DUE = tok('instatus', 'Due'); OVERD = tok('instatus', 'Overdue'); PAIDS = tok('instatus', 'Paid'); WOFF = tok('instatus', 'Written off')
OPENP = tok('plstatus', 'Open'); BANKED = tok('batch', 'Banked'); BOPEN = tok('batch', 'Open')
ACTIVE = tok('recstatus', 'Active'); FAILED = tok('recstatus', 'Failed'); PAUSED = tok('recstatus', 'Paused'); STOPPED = tok('recstatus', 'Stopped')
EXPECTED = tok('mstatus', 'Expected'); REQUESTED = tok('mstatus', 'Requested'); RECEIVED = tok('mstatus', 'Received'); DECLINED = tok('mstatus', 'Declined')
NOTREC = tok('basis', 'Not recorded')
YES = '{list:yesno.yes}'

settings = [
    S('org', 'Your organization name', 'text', COMPANY), S('thankyou_days', 'Working days before a gift counts as unthanked', 'int', THANKYOU_DAYS), S('ack_over', 'Letter above this amount, your own rule', 'money', ACK_OVER),
    S('lapse_months', 'Months without a gift before a donor counts as lapsed', 'int', LAPSE_MONTHS), S('pledge_overdue_days', 'Days late before you chase a pledge instalment', 'int', PLEDGE_OVERDUE_DAYS),
    S('pledge_final_days', 'Days late before a final notice', 'int', 90), S('pledge_writeoff_days', 'Days late before you propose a write-off', 'int', PLEDGE_WRITEOFF_DAYS),
    S('match_chase_days', 'Days waiting before you chase an employer match', 'int', MATCH_CHASE_DAYS), S('bank_tolerance', 'Banking gap allowed before a batch counts as off', 'money', D.BANK_TOL),
    S('statement_year', 'Year of the giving statements you print now', 'int', TODAY.year), S('missed_contact', 'Missed monthly gifts before you contact the donor', 'int', 2),
    S('dup_days', 'Days apart that make two same gifts a duplicate', 'int', 3), S('big_gift_multiple', 'A gift this many times your median gift is checked twice', 'num', 10),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 gifts -------------------------------------------------------------------
GID = '{range:gifts.donor_id},{col:donor_id},{range:gifts.amount},{col:amount},{range:gifts.gift_type},ONEX,{range:gifts.date},">="&({col:date}-{set:dup_days}),{range:gifts.date},"<="&({col:date}+{set:dup_days})'.replace('ONEX', ONE)
ISSUE = ('IF({col:donor_id}="",1,IF({col:fund}="",2,IF(AND({col:gift_type}=%s,COUNTIFS(%s)>1),3,'
         'IF(IFERROR(IF(ABS(INDEX({range:batches.gap},MATCH({col:batch_id},{range:batches.batch_id},0)))>{set:bank_tolerance},1,0),0)=1,4,0))))') % (ONE, GID)
tables.append(T('gifts', 'Gifts', 'Gift Log', 'One row per gift: date, donor, amount, fund, campaign, appeal, channel and method; days waiting, thank-you flag and the check column (missing donor or fund, duplicate, batch off) fill in.', [
    C('gift_id', 'Gift ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('donor_id', 'Donor ID', 'donors.donor_id', 10), CA('donor', 'Donor', 'text', LKT('donors.donor', 'donors.donor_id', 'donor_id'), 24),
    C('amount', 'Amount', 'money', 11), LST('fund', 'Fund', 'fund', 22), LST('campaign', 'Campaign', 'campaign', 20), LST('appeal', 'Appeal', 'appeal', 22), LST('channel', 'Channel', 'channel', 14),
    LST('method', 'Method', 'method', 16), LST('gift_type', 'Gift type', 'gtype', 15), C('restricted', 'Restricted', 'bool', 9), C('ack_sent', 'Thank-you sent', 'date', 11), C('batch_id', 'Batch ID', 'text', 9),
    C('pledge_id', 'Pledge ID', 'text', 9), C('recurring_id', 'Recurring ID', 'text', 10), C('match_for', 'Match for', 'text', 10), LST('weekday', 'Weekday', 'wday', 11),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), DON('contact', w=22, label='Donor contact'), DONPH(),
    CA('days_waiting', 'Days waiting for a thank-you', 'int', 'IF({col:ack_sent}>0,"",MAX(0,{today}-{col:date}))', 11),
    CA('wd_waiting', 'Working days waiting', 'int', 'IF({col:ack_sent}>0,"",MAX(0,NETWORKDAYS({col:date},{today})-1))', 10),
    CA('days_to_thank', 'Days to thank', 'int', 'IF({col:ack_sent}>0,{col:ack_sent}-{col:date},"")', 9),
    CA('thank_late', 'Thank-you late', 'int', 'IF({col:wd_waiting}="","",IF({col:wd_waiting}>{set:thankyou_days},1,0))', 9),
    CA('thank_ok', 'Thanked on time', 'int', 'IF({col:ack_sent}>0,IF(NETWORKDAYS({col:date},{col:ack_sent})-1<={set:thankyou_days},1,0),IF({col:thank_late}=1,0,1))', 9),
    CA('letter_due', 'Letter due', 'int', 'IF(AND({col:days_waiting}<>"",{col:amount}>{set:ack_over}),1,0)', 8),
    CA('filled', 'Donor and fund filled', 'int', 'IF(AND({col:donor_id}<>"",{col:fund}<>""),1,0)', 9),
    CA('issue', 'Issue code', 'int', ISSUE, 8),
    CA('check', 'Check', 'text', 'CHOOSE({col:issue}+1,%s,%s,%s,%s,%s)' % (c('Complete'), c('Donor missing'), c('Fund missing'), c('Possible duplicate'), c('Batch off')), 16),
    CA('issue_rank', 'Issue rank', 'int', 'IF({col:issue}>0,COUNTIFS({range:gifts.issue},"<"&{col:issue},{range:gifts.issue},">0")+COUNTIFS({range:gifts.issue},{col:issue},{range:gifts.date},">"&{col:date})'
       '+COUNTIFS({range:gifts.issue},{col:issue},{range:gifts.date},{col:date},{range:gifts.gift_id},"<"&{col:gift_id})+1,"")', 8),
    CA('thank_rank', 'Thank-you rank', 'int', 'IF({col:days_waiting}="","",COUNTIFS({range:gifts.days_waiting},">"&{col:days_waiting})+COUNTIFS({range:gifts.days_waiting},{col:days_waiting},{range:gifts.gift_id},"<"&{col:gift_id})+1)', 8),
    CA('fund_month_total', 'Gifts to this fund this month', 'money', 'IF({col:fund}="","",SUMIFS({range:gifts.amount},{range:gifts.fund},{col:fund},{range:gifts.month},%s))' % MS, 12),
    CA('idnum', 'ID number', 'int', 'VALUE(RIGHT({col:gift_id},5))', 8), BOOKPH(), ORG()],
    D.gifts_d(), 2600, [A('check', '= ' + c('Donor missing'), 'bad'), A('check', '= ' + c('Fund missing'), 'bad'), A('check', '= ' + c('Possible duplicate'), 'warn'), A('check', '= ' + c('Batch off'), 'warn'),
                       A('thank_late', '= 1', 'warn')]))
# 2 donors ------------------------------------------------------------------
tables.append(T('donors', 'Donors', 'Donor Book', 'One row per donor: name, type, contact person, phone, e-mail and preference, status and dates of the first and last gift; months since the last gift, giving state and duplicate checks fill in.', [
    C('donor_id', 'Donor ID', 'text', 10, required=True), C('donor', 'Donor', 'text', 26), LST('type', 'Type', 'dtype', 18), C('contact', 'Contact person', 'text', 22), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 28),
    LST('contact_pref', 'Contact preference', 'pref', 14), LST('status', 'Status', 'dstatus', 10), C('first_gift', 'First gift', 'date', 11), C('last_gift', 'Last gift', 'date', 11), C('gifts', 'Gifts', 'int', 8),
    C('total_given', 'Total given', 'money', 12),
    CA('months_since', 'Months since last gift', 'int', 'IF({col:last_gift}>0,DATEDIF({col:last_gift},{today},"M"),"")', 10),
    CA('giving_state', 'Giving state', 'text', 'IF({col:months_since}="",%s,IF({col:months_since}>={set:lapse_months},%s,IF({col:months_since}>={set:lapse_months}-3,%s,%s)))' % (c('No gift yet'), c('Lapsed'), c('Lapsing'), c('Active')), 12),
    CA('same_name', 'Records with this name', 'int', 'COUNTIFS({range:donors.donor},{col:donor})', 9), CA('same_email', 'Records with this e-mail and type', 'int', 'COUNTIFS({range:donors.email},{col:email},{range:donors.type},{col:type})', 10),
    CA('dup_extra', 'Extra copy of another record', 'int', 'IF({col:same_email}>1,IF(COUNTIFS({range:donors.email},{col:email},{range:donors.type},{col:type},{range:donors.donor_id},"<"&{col:donor_id})>0,1,0),0)', 9), ORG()],
    D.donors_d(), 2000, [A('giving_state', '= ' + c('Lapsed'), 'warn'), A('dup_extra', '= 1', 'bad')]))
# 3 donor contacts ----------------------------------------------------------
tables.append(T('contacts', 'Donor Contacts', 'Donor Contacts', 'One row per contact person of a donor (a household or business can have several): name, role, phone and e-mail; the number of contacts under the same donor fills in.', [
    C('contact_id', 'Contact ID', 'text', 10, required=True), C('donor_id', 'Donor ID', 'text', 10), C('donor', 'Donor', 'text', 26), C('contact', 'Contact person', 'text', 22), C('role', 'Role', 'text', 16),
    C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 28), CA('contacts', 'Contacts under this donor', 'int', 'COUNTIFS({range:contacts.donor_id},{col:donor_id})', 10)],
    D.contacts_d(), 2200, [A('contacts', '> 1', 'good')]))
# 4 funds -------------------------------------------------------------------
tables.append(T('funds', 'Funds', 'Funds', 'One row per fund: general (free money, no purpose), set aside by the board, or restricted (given for one purpose) with the balance at the start of the year.', [
    LST('fund', 'Fund', 'fund', 24, required=True), LST('restriction', 'Restriction', 'fundkind', 18), C('opening_balance', 'Opening balance', 'money', 14)], D.funds_d(), 50))
# 5 campaigns ---------------------------------------------------------------
tables.append(T('campaigns', 'Campaigns', 'Campaigns', 'One row per campaign and year: dates and the goal; gifts are linked to a campaign in the Gift Log.', [
    C('campaign_id', 'Campaign ID', 'text', 11, required=True), LST('campaign', 'Campaign', 'campaign', 22), C('year', 'Year', 'int', 8), C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11), C('goal', 'Goal', 'money', 12)],
    D.campaigns_d(), 60))
# 6 appeals -----------------------------------------------------------------
tables.append(T('appeals', 'Appeals', 'Appeals', 'One row per appeal (a letter, an e-mail series, a paddle raise): its campaign and the channel it mostly uses.', [
    LST('appeal', 'Appeal', 'appeal', 26, required=True), LST('campaign', 'Campaign', 'campaign', 22), LST('channel', 'Channel', 'channel', 16)], D.appeals_d(), 50))
# 7 gift batches ------------------------------------------------------------
tables.append(T('batches', 'Gift Batches', 'Gift Batches', 'One row per week of gifts to bank: gifts logged, the amount on the bank slip and the date banked; the gap, the off flag and the days to bank fill in.', [
    C('batch_id', 'Batch ID', 'text', 9, required=True), C('week_start', 'Week start', 'date', 11), C('banked_on', 'Banked on', 'date', 11), C('logged_amount', 'Logged amount', 'money', 13), C('gift_count', 'Gifts', 'int', 8),
    C('banked_amount', 'Banked amount', 'money', 13), LST('status', 'Status', 'batch', 10),
    CA('gap', 'Banked less logged', 'money', 'IF({col:status}=%s,ROUND({col:banked_amount}-{col:logged_amount},2),"")' % BANKED, 12),
    CA('off', 'Off by more than allowed', 'int', 'IF({col:gap}="","",IF(ABS({col:gap})>{set:bank_tolerance},1,0))', 10),
    CA('abs_gap', 'Gap, no sign', 'money', 'IF({col:gap}="",0,ABS({col:gap}))', 10),
    CA('check', 'Tie-out', 'text', 'IF({col:status}=%s,%s,IF({col:off}=1,%s,%s))' % (BOPEN, c('Open'), c('Off'), c('Tied')), 10),
    CA('days_to_bank', 'Days to bank', 'int', 'IF({col:banked_on}>0,{col:banked_on}-{col:week_start},"")', 9), LIT('board_phone', 'Board chair phone', D.BOARD_PHONE), BOOKPH(), ORG()],
    D.batches_d(), 260, [A('check', '= ' + c('Off'), 'bad'), A('check', '= ' + c('Tied'), 'good'), A('check', '= ' + c('Open'), 'warn')]))
# 8 thank-you backlog -------------------------------------------------------
def AT(src): return 'IF({col:at}="","",INDEX({range:gifts.%s},{col:at}))' % src
tables.append(T('thankyou', 'Thank-you Backlog', 'Thank-you Backlog', 'The gifts still without a thank-you, oldest first: donor, amount, days waiting and the rule; each row says Send today or On time.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('at', 'Row in the Gift Log', 'int', 'IFERROR(MATCH({col:rank},{range:gifts.thank_rank},0),"")', 9), CA('gift_id', 'Gift ID', 'text', AT('gift_id'), 10),
    CA('donor', 'Donor', 'text', AT('donor'), 24), CA('contact', 'Contact person', 'text', AT('contact'), 22), CA('amount', 'Amount', 'money', AT('amount'), 11), CA('date', 'Gift date', 'date', AT('date'), 11),
    CA('days_waiting', 'Days waiting', 'int', AT('days_waiting'), 9), CA('rule_days', 'Rule, working days', 'int', 'IF({col:at}="","",{set:thankyou_days})', 9),
    CA('late', 'Late', 'int', AT('thank_late'), 7), CA('verdict', 'Verdict', 'text', 'IF({col:at}="","",IF({col:late}=1,%s,%s))' % (c('Send today'), c('On time')), 12), CA('phone', 'Donor phone', 'text', AT('phone'), 18),
    CA('over_n', 'Thank-yous overdue', 'int', 'COUNTIFS({range:gifts.thank_late},1)', 9), CA('oldest_days', 'Oldest wait, days', 'int', 'MAX({range:gifts.days_waiting})', 9),
    CA('session_date', 'Next card session', 'date', '{today}+IF(MOD(5-WEEKDAY({today},2),7)=0,7,MOD(5-WEEKDAY({today},2),7))', 11), DEVPH(), LIT('volunteer_phone', 'Volunteer phone', D.VOL_PHONE), ORG()],
    D.thankyou_d(), 60, [A('verdict', '= ' + c('Send today'), 'bad'), A('verdict', '= ' + c('On time'), 'good')]))
# 9 giving by donor and year -------------------------------------------------
YR_A = '{range:gifts.date},">="&DATE({set:statement_year},1,1),{range:gifts.date},"<="&DATE({set:statement_year},12,31)'
tables.append(T('giving_years', 'Giving by Donor and Year', 'Giving by Donor and Year', 'One row per donor: this year comes from the Gift Log, the two earlier years are carried from your earlier log; the statement total, the missing funds and the statement flag fill in.', [
    REF('donor_id', 'Donor ID', 'donors.donor_id', 10, required=True), C('last_year', 'Last year', 'money', 12), C('two_years_ago', 'Two years ago', 'money', 12),
    CA('donor', 'Donor', 'text', LKT('donors.donor', 'donors.donor_id', 'donor_id'), 26),
    CA('this_year', 'This year', 'money', 'SUMIFS({range:gifts.amount},{range:gifts.donor_id},{col:donor_id},{range:gifts.date},">="&%s)' % Y0F, 12),
    CA('change', 'Change on last year', 'pct', 'IF({col:last_year}>0,{col:this_year}/{col:last_year}-1,"")', 10),
    CA('year', 'Statement year', 'int', '{set:statement_year}', 9),
    CA('statement_total', 'Statement total', 'money', 'IFERROR(CHOOSE(YEAR({today})-{set:statement_year}+1,{col:this_year},{col:last_year},{col:two_years_ago}),0)', 12),
    CA('gifts', 'Gifts in the year', 'int', 'COUNTIFS({range:gifts.donor_id},{col:donor_id},%s)' % YR_A, 9),
    CA('missing_fund', 'Gifts missing a fund', 'int', 'COUNTIFS({range:gifts.donor_id},{col:donor_id},{range:gifts.issue},2,%s)' % YR_A, 9),
    CA('flag', 'Statement flag', 'text', 'IF({col:statement_total}<=0,%s,IF({col:missing_fund}>0,%s,%s))' % (c('No gifts in the year'), c('Gifts missing a fund'), c('Ready')), 18),
    DON('contact', w=22, label='Donor contact'), DONPH(), ORG()],
    D.giving_years_d(), 500, [A('flag', '= ' + c('Ready'), 'good'), A('flag', '= ' + c('Gifts missing a fund'), 'bad')]))
# 10 pledges ----------------------------------------------------------------
IP = '{range:instalments.pledge_id},{col:pledge_id}'
tables.append(T('pledges', 'Pledges', 'Pledges', 'One row per pledge (a promise to give, paid in instalments): total, number of instalments and fund; paid, balance, next due date and days behind fill in from the instalments.', [
    C('pledge_id', 'Pledge ID', 'text', 10, required=True), REF('donor_id', 'Donor ID', 'donors.donor_id', 10), C('pledged_on', 'Pledged on', 'date', 11), C('total', 'Total', 'money', 12), C('instalments', 'Instalments', 'int', 9),
    C('every_months', 'Every months', 'int', 9), LST('fund', 'Fund', 'fund', 20), LST('status', 'Status', 'plstatus', 12), CA('donor', 'Donor', 'text', LKT('donors.donor', 'donors.donor_id', 'donor_id'), 26),
    CA('paid', 'Paid', 'money', 'SUMIFS({range:instalments.amount_paid},%s)' % IP, 11), CA('balance', 'Balance', 'money', 'IF({col:status}=%s,MAX(0,{col:total}-{col:paid}),0)' % OPENP, 11),
    CA('pct_paid', 'Share paid', 'pct', 'IF({col:total}>0,{col:paid}/{col:total},0)', 9),
    CA('paid_n', 'Instalments settled', 'int', 'COUNTIFS(%s,{range:instalments.status},%s)+COUNTIFS(%s,{range:instalments.status},%s)' % (IP, PAIDS, IP, WOFF), 9),
    CA('next_due', 'Next due', 'date', 'IF(AND({col:status}=%s,{col:paid_n}<{col:instalments}),IF(SUMIFS({range:instalments.due_date},%s,{range:instalments.seq},{col:paid_n}+1)=0,"",SUMIFS({range:instalments.due_date},%s,{range:instalments.seq},{col:paid_n}+1)),"")' % (OPENP, IP, IP), 11),
    CA('next_amount', 'Next amount', 'money', 'IF({col:next_due}="","",SUMIFS({range:instalments.amount_due},%s,{range:instalments.seq},{col:paid_n}+1))' % IP, 11),
    CA('behind_days', 'Days behind', 'int', 'IF({col:status}=%s,SUMPRODUCT(MAX(({range:instalments.pledge_id}={col:pledge_id})*(({range:instalments.status}=%s)+({range:instalments.status}=%s))*({today}-{range:instalments.due_date}))),0)' % (OPENP, DUE, OVERD), 9),
    CA('action', 'Action', 'text', 'IF({col:status}<>%s,%s,IF({col:behind_days}>={set:pledge_writeoff_days},%s,IF({col:behind_days}>={set:pledge_final_days},%s,IF({col:behind_days}>={set:pledge_overdue_days},%s,IF({col:behind_days}>0,%s,%s)))))'
       % (OPENP, c('Closed'), c('Propose write-off'), c('Final notice'), c('Chase'), c('Not late yet'), c('On schedule')), 17),
    DON('contact', w=22, label='Donor contact'), DONPH(), ORG()],
    D.pledges_d(), 100, [A('action', '= ' + c('Chase'), 'warn'), A('action', '= ' + c('Final notice'), 'bad'), A('action', '= ' + c('Propose write-off'), 'bad'), A('status', '= ' + OPENP, 'good')]))
# 11 pledge instalments -----------------------------------------------------
def PL(col): return LKT('pledges.' + col, 'pledges.pledge_id', 'pledge_id')
tables.append(T('instalments', 'Pledge Instalments', 'Pledge Instalments', 'One row per instalment: due date, amount due, paid on and amount paid; days overdue, the action (chase, final notice, write-off proposal) and the write-off date fill in.', [
    C('pp_id', 'Instalment ID', 'text', 11, required=True), REF('pledge_id', 'Pledge ID', 'pledges.pledge_id', 10), C('due_date', 'Due date', 'date', 11), C('amount_due', 'Amount due', 'money', 11), C('paid_on', 'Paid on', 'date', 11),
    C('amount_paid', 'Amount paid', 'money', 11), LST('status', 'Status', 'instatus', 12), CA('donor_id', 'Donor ID', 'text', PL('donor_id'), 10), CA('donor', 'Donor', 'text', PL('donor'), 26),
    CA('seq', 'Instalment number', 'int', 'COUNTIFS({range:instalments.pledge_id},{col:pledge_id},{range:instalments.due_date},"<="&{col:due_date})', 9),
    CA('days_overdue', 'Days overdue', 'int', 'IF(OR({col:status}=%s,{col:status}=%s),MAX(0,{today}-{col:due_date}),"")' % (DUE, OVERD), 9),
    CA('action', 'Action', 'text', 'IF({col:days_overdue}="",%s,IF({col:days_overdue}>={set:pledge_writeoff_days},%s,IF({col:days_overdue}>={set:pledge_final_days},%s,IF({col:days_overdue}>={set:pledge_overdue_days},%s,%s))))'
       % (c('Closed'), c('Propose write-off'), c('Final notice'), c('Chase'), c('Not late yet')), 17),
    CA('writeoff_on', 'Write-off proposal date', 'date', 'IF({col:days_overdue}="","",{col:due_date}+{set:pledge_writeoff_days})', 12),
    CA('overdue_rank', 'Overdue rank', 'int', 'IF({col:days_overdue}="","",IF({col:days_overdue}=0,"",COUNTIFS({range:instalments.days_overdue},">"&{col:days_overdue})+COUNTIFS({range:instalments.days_overdue},{col:days_overdue},{range:instalments.amount_due},">"&{col:amount_due})'
       '+COUNTIFS({range:instalments.days_overdue},{col:days_overdue},{range:instalments.amount_due},{col:amount_due},{range:instalments.pp_id},"<"&{col:pp_id})+1))', 8),
    CA('over_count', 'Instalments over the chase days', 'int', 'COUNTIFS({range:instalments.days_overdue},">="&{set:pledge_overdue_days})', 9), CA('limit_days', 'Chase days', 'int', '{set:pledge_overdue_days}', 8),
    DON('contact', w=22, label='Donor contact'), DONPH(), DEVPH(), ORG()],
    D.instalments_d(), 400, [A('action', '= ' + c('Chase'), 'warn'), A('action', '= ' + c('Final notice'), 'bad'), A('action', '= ' + c('Propose write-off'), 'bad'), A('status', '= ' + PAIDS, 'good')]))
# 12 recurring donors -------------------------------------------------------
tables.append(T('recurring', 'Recurring Donors', 'Recurring Donors', 'One row per monthly donor: amount, start date, day of the month, channel, fund, status, last gift received and missed payments; months since the last gift, the action and annual value fill in.', [
    C('recurring_id', 'Recurring ID', 'text', 11, required=True), REF('donor_id', 'Donor ID', 'donors.donor_id', 10), C('amount', 'Monthly amount', 'money', 11), C('start_date', 'Start date', 'date', 11), C('day', 'Day', 'int', 6),
    LST('channel', 'Channel', 'channel', 14), LST('fund', 'Fund', 'fund', 22), LST('status', 'Status', 'recstatus', 10), C('last_received', 'Last received', 'date', 11), C('missed', 'Missed', 'int', 8),
    CA('donor', 'Donor', 'text', LKT('donors.donor', 'donors.donor_id', 'donor_id'), 26), CA('months_since', 'Months since last gift', 'int', 'IF({col:last_received}>0,DATEDIF({col:last_received},{today},"M"),"")', 10),
    CA('annual', 'Annual value', 'money', '{col:amount}*12', 11),
    CA('needs', 'Needs attention', 'int', 'IF(OR({col:status}=%s,AND({col:status}=%s,{col:missed}>=1)),1,0)' % (FAILED, ACTIVE), 9),
    CA('action', 'Action', 'text', 'IF(OR({col:status}=%s,{col:status}=%s),%s,IF(OR({col:status}=%s,{col:missed}>={set:missed_contact}),%s,IF({col:missed}>=1,%s,%s)))'
       % (PAUSED, STOPPED, c('Not active'), FAILED, c('Contact today'), c('Wait one more cycle'), c('Received')), 18),
    CA('chase_rank', 'Chase rank', 'int', 'IF({col:needs}=1,COUNTIFS({range:recurring.needs},1,{range:recurring.amount},">"&{col:amount})+COUNTIFS({range:recurring.needs},1,{range:recurring.amount},{col:amount},{range:recurring.recurring_id},"<"&{col:recurring_id})+1,"")', 8),
    DON('contact', w=22, label='Donor contact'), DONPH(), ORG()],
    D.recurring_d(), 260, [A('action', '= ' + c('Contact today'), 'bad'), A('action', '= ' + c('Wait one more cycle'), 'warn'), A('action', '= ' + c('Received'), 'good')]))
# 13 recurring income by month ----------------------------------------------
tables.append(T('recurring_months', 'Recurring Income by Month', 'Recurring Income by Month', 'One row per month: recurring gifts and amount against all gifts; the recurring share and the change on the month before fill in.', [
    C('month', 'Month', 'date', 11, required=True), C('recurring_gifts', 'Recurring gifts', 'int', 10), C('recurring_amount', 'Recurring amount', 'money', 13), C('all_amount', 'All gifts amount', 'money', 13),
    CA('recurring_share', 'Recurring share', 'pct', 'IF({col:all_amount}>0,{col:recurring_amount}/{col:all_amount},0)', 10),
    CA('prev_amount', 'Month before', 'money', 'SUMIFS({range:recurring_months.recurring_amount},{range:recurring_months.month},EDATE({col:month},-1))', 11),
    CA('change_month', 'Change on the month before', 'pct', 'IF({col:prev_amount}>0,{col:recurring_amount}/{col:prev_amount}-1,0)', 11), DEVPH(), ORG()],
    D.recurring_months_d(), 60, [A('change_month', '< 0', 'warn')]))
# 14 in-kind gifts ----------------------------------------------------------
tables.append(T('inkind', 'In-kind Gifts', 'In-kind Gifts', 'One row per in-kind gift (goods or services given instead of money): item, quantity, fair value and who set it; the value check, unit value and this year total fill in.', [
    C('inkind_id', 'In-kind ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), REF('donor_id', 'Donor ID', 'donors.donor_id', 10), LST('kind', 'Kind', 'ikind', 15), C('item', 'Item', 'text', 28), C('qty', 'Quantity', 'int', 9),
    C('fair_value', 'Fair value', 'money', 11), LST('value_basis', 'Value basis', 'basis', 14), C('ack_sent', 'Thank-you sent', 'date', 11), CA('donor', 'Donor', 'text', LKT('donors.donor', 'donors.donor_id', 'donor_id'), 26),
    CA('unit_value', 'Value of one', 'money', 'IF({col:qty}>0,ROUND({col:fair_value}/{col:qty},2),{col:fair_value})', 10),
    CA('basis_check', 'Value check', 'text', 'IF({col:value_basis}=%s,%s,%s)' % (NOTREC, c('Basis missing'), c('Value recorded')), 15), CA('ack_days', 'Days to thank', 'int', 'IF({col:ack_sent}>0,{col:ack_sent}-{col:date},"")', 9),
    CA('year_value', 'In-kind value this year', 'money', 'SUMIFS({range:inkind.fair_value},{range:inkind.date},">="&%s)' % Y0F, 12), DON('contact', w=22, label='Donor contact'), DONPH(), ACCPH(), ORG()],
    D.inkind_d(), 700, [A('basis_check', '= ' + c('Basis missing'), 'bad')]))
# 15 matching gifts ---------------------------------------------------------
tables.append(T('matching', 'Matching Gifts', 'Matching Gifts', 'One row per matching gift (money an employer adds to a donor gift): employer, ratio, amount expected, when asked and what came; days waiting, the chase flag and the next step fill in.', [
    C('match_id', 'Match ID', 'text', 10, required=True), C('gift_id', 'Gift ID', 'text', 10), REF('donor_id', 'Donor ID', 'donors.donor_id', 10), C('employer', 'Employer', 'text', 26), C('employer_donor_id', 'Employer donor ID', 'text', 11),
    C('ratio', 'Ratio', 'num', 7), C('expected', 'Expected', 'money', 11), C('requested_on', 'Requested on', 'date', 11), C('received_on', 'Received on', 'date', 11), C('received', 'Received', 'money', 11), LST('status', 'Status', 'mstatus', 11),
    CA('donor', 'Donor', 'text', LKT('donors.donor', 'donors.donor_id', 'donor_id'), 26), CA('gift_amount', 'Donor gift', 'money', 'IF({col:ratio}>0,ROUND({col:expected}/{col:ratio},2),"")', 10),
    CA('open', 'Open', 'int', 'IF(OR({col:status}=%s,{col:status}=%s),1,0)' % (EXPECTED, REQUESTED), 7),
    CA('idnum', 'ID number', 'int', 'VALUE(RIGHT({col:match_id},4))', 8),
    CA('days_waiting', 'Days waiting', 'int', 'IF({col:open}=1,IF({col:requested_on}>0,MAX(0,{today}-{col:requested_on}),0),"")', 9),
    CA('chase', 'Past the chase days', 'int', 'IF({col:open}=1,IF(AND({col:requested_on}>0,{col:days_waiting}>{set:match_chase_days}),1,0),"")', 9),
    CA('open_rank', 'Open rank by amount', 'int', 'IF({col:open}=1,COUNTIFS({range:matching.open},1,{range:matching.expected},">"&{col:expected})+COUNTIFS({range:matching.open},1,{range:matching.expected},{col:expected},{range:matching.match_id},"<"&{col:match_id})+1,"")', 8),
    CA('next_step', 'Next step', 'text', 'IF({col:open}=0,%s,IF({col:status}=%s,%s,IF({col:days_waiting}>{set:match_chase_days},%s,%s)))' % (c('Closed'), EXPECTED, c('Send request'), c('Chase now'), c('Wait')), 12),
    DON('contact', w=22, label='Donor contact'), DONPH(), CA('employer_phone', 'Employer phone', 'text', LKT('donors.phone', 'donors.donor_id', 'employer_donor_id'), 18), ORG()],
    D.matching_d(), 150, [A('next_step', '= ' + c('Chase now'), 'bad'), A('next_step', '= ' + c('Send request'), 'warn'), A('status', '= ' + RECEIVED, 'good')]))
# 16 match chase list -------------------------------------------------------
def AM(src): return 'IF({col:at}="","",INDEX({range:matching.%s},{col:at}))' % src
tables.append(T('match_chase', 'Match Chase List', 'Match Chase List', 'The matching gifts still open, biggest first: employer, amount expected, days waiting and the next step (send the request, chase now or wait).', [
    C('rank', 'Rank', 'int', 7, required=True), CA('at', 'Row in Matching Gifts', 'int', 'IFERROR(MATCH({col:rank},{range:matching.open_rank},0),"")', 9), CA('match_id', 'Match ID', 'text', AM('match_id'), 10),
    CA('employer', 'Employer', 'text', AM('employer'), 26), CA('donor', 'Donor', 'text', AM('donor'), 26), CA('expected', 'Expected', 'money', AM('expected'), 11), CA('days_waiting', 'Days waiting', 'int', AM('days_waiting'), 9),
    CA('next_step', 'Next step', 'text', AM('next_step'), 12), CA('employer_phone', 'Employer phone', 'text', AM('employer_phone'), 18), ORG()],
    D.match_chase_d(), 50, [A('next_step', '= ' + c('Chase now'), 'bad'), A('next_step', '= ' + c('Send request'), 'warn')]))
# 17 duplicate finder -------------------------------------------------------
tables.append(T('duplicates', 'Duplicate Finder', 'Duplicate Finder', 'One row per donor record to check: records with the same name or the same e-mail and type, gift pairs on the same day and a verdict (merge into the first record, keep both or check the gifts).', [
    REF('donor_id', 'Donor ID', 'donors.donor_id', 10, required=True), C('found_on', 'Found on', 'date', 11), CA('donor', 'Donor', 'text', LKT('donors.donor', 'donors.donor_id', 'donor_id'), 26),
    CA('email', 'E-mail', 'text', LKT('donors.email', 'donors.donor_id', 'donor_id'), 28), CA('same_name', 'Same name', 'int', LKN('donors.same_name', 'donors.donor_id', 'donor_id'), 8),
    CA('same_email', 'Same e-mail and type', 'int', LKN('donors.same_email', 'donors.donor_id', 'donor_id'), 9),
    CA('keep_id', 'First record', 'text', 'IFERROR(INDEX({range:donors.donor_id},MATCH({col:email},{range:donors.email},0)),"")', 10),
    CA('gift_pairs', 'Gift pairs, same day and amount', 'int', 'ROUNDDOWN(COUNTIFS({range:gifts.donor_id},{col:donor_id},{range:gifts.issue},3)/2,0)', 9),
    CA('flag', 'Verdict', 'text', 'IF({col:same_email}>1,IF({col:keep_id}={col:donor_id},%s,%s),IF({col:gift_pairs}>0,%s,IF({col:same_name}>1,%s,%s)))' % (c('Keep'), c('Merge'), c('Possible duplicate'), c('Keep both'), c('Keep')), 15),
    CA('merge_into', 'Merge into', 'text', 'IF({col:flag}=%s,{col:keep_id},"")' % c('Merge'), 10), CA('records_gifts', 'Gifts on this record', 'int', LKN('donors.gifts', 'donors.donor_id', 'donor_id'), 9),
    DON('contact', w=22, label='Donor contact'), DONPH(), ORG()],
    D.duplicates_d(), 80, [A('flag', '= ' + c('Merge'), 'bad'), A('flag', '= ' + c('Possible duplicate'), 'warn'), A('flag', '= ' + c('Keep both'), 'good')]))
# 18 gift checks ------------------------------------------------------------
def AG(src): return 'IF({col:at}="","",INDEX({range:gifts.%s},{col:at}))' % src
tables.append(T('gift_checks', 'Gift Checks', 'Gift Checks', 'The gifts that need a fix, worst first: check kind, donor, amount and what to do (add the donor, pick a fund, confirm a duplicate, check the bank slip).', [
    C('rank', 'Rank', 'int', 7, required=True), CA('at', 'Row in the Gift Log', 'int', 'IFERROR(MATCH({col:rank},{range:gifts.issue_rank},0),"")', 9), CA('gift_id', 'Gift ID', 'text', AG('gift_id'), 10),
    CA('check', 'Check kind', 'text', AG('check'), 16), CA('donor', 'Donor', 'text', 'IF({col:at}="","",IF(INDEX({range:gifts.donor},{col:at})="",%s,INDEX({range:gifts.donor},{col:at})))' % c('Donor missing'), 24),
    CA('amount', 'Amount', 'money', AG('amount'), 11), CA('date', 'Date', 'date', AG('date'), 11), CA('batch_id', 'Batch ID', 'text', AG('batch_id'), 9),
    CA('fix', 'Fix', 'text', 'IF({col:at}="","",CHOOSE(INDEX({range:gifts.issue},{col:at}),%s,%s,%s,%s))' % (c('Add the donor'), c('Pick a fund'), c('Confirm or delete one'), c('Check the bank slip')), 22), BOOKPH(), ORG()],
    D.gift_checks_d(), 80, [A('check', '= ' + c('Donor missing'), 'bad'), A('check', '= ' + c('Fund missing'), 'bad'), A('check', '= ' + c('Possible duplicate'), 'warn')]))
# 19 gift summary by month ---------------------------------------------------
tables.append(T('gift_months', 'Gift Summary by Month', 'Gift Summary by Month', 'One row per month: gifts, amount, donors, recurring and restricted amounts and the average days to thank, from your full log; the average gift and the shares fill in.', [
    C('month', 'Month', 'date', 11, required=True), C('gifts', 'Gifts', 'int', 8), C('amount', 'Amount', 'money', 12), C('donors', 'Donors', 'int', 8), C('recurring_amount', 'Recurring amount', 'money', 12),
    C('restricted_amount', 'Restricted amount', 'money', 12), C('avg_wait', 'Average days to thank', 'num', 10),
    CA('avg_gift', 'Average gift', 'money', 'IF({col:gifts}>0,ROUND({col:amount}/{col:gifts},2),0)', 10), CA('recurring_share', 'Recurring share', 'pct', 'IF({col:amount}>0,{col:recurring_amount}/{col:amount},0)', 10),
    CA('restricted_share', 'Restricted share', 'pct', 'IF({col:amount}>0,{col:restricted_amount}/{col:amount},0)', 10), ACCPH(), ORG()],
    D.gift_months_d(), 60))
# 20 household view ---------------------------------------------------------
tables.append(T('households', 'Household View', 'Household View', 'One row per household or business donor with several contacts: contacts, gifts, total given, last gift and the years given (of the last three), with a giving state.', [
    REF('donor_id', 'Donor ID', 'donors.donor_id', 10, required=True), CA('donor', 'Donor', 'text', LKT('donors.donor', 'donors.donor_id', 'donor_id'), 26),
    CA('contacts', 'Contacts', 'int', 'COUNTIFS({range:contacts.donor_id},{col:donor_id})', 9), CA('gifts', 'Gifts', 'int', LKN('donors.gifts', 'donors.donor_id', 'donor_id'), 8),
    CA('total_given', 'Total given', 'money', LKN('donors.total_given', 'donors.donor_id', 'donor_id'), 12), CA('last_gift', 'Last gift', 'date', LKD('donors.last_gift', 'donors.donor_id', 'donor_id'), 11),
    CA('years_given', 'Years given, of 3', 'int', '(SUMIFS({range:giving_years.this_year},{range:giving_years.donor_id},{col:donor_id})>0)+(SUMIFS({range:giving_years.last_year},{range:giving_years.donor_id},{col:donor_id})>0)'
       '+(SUMIFS({range:giving_years.two_years_ago},{range:giving_years.donor_id},{col:donor_id})>0)', 9),
    CA('state', 'Giving state', 'text', LKT('donors.giving_state', 'donors.donor_id', 'donor_id'), 12), DON('contact', w=22, label='Donor contact'), DONPH(), ORG()],
    D.households_d(), 100, [A('state', '= ' + c('Lapsed'), 'warn'), A('state', '= ' + c('Active'), 'good')]))
assert len(tables) == 20
