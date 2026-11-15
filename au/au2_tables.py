"""Author and Self-Publisher suite, part 2: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au2_lists import *
import au2_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
CASHNOW = 'SUMIFS({range:cash_month.closing},{range:cash_month.month},%s)' % MS
PAID = tok('cpaystatus', 'Paid'); JPAID = tok('jstatus', 'Paid'); JQUOTED = tok('jstatus', 'Quoted'); JIP = tok('jstatus', 'In progress'); JDEL = tok('jstatus', 'Delivered')
JBOOK = tok('jstatus', 'Booked')
K_DEV, K_COPY, K_PROOF = tok('jobkind', 'Developmental edit'), tok('jobkind', 'Copy edit'), tok('jobkind', 'Proofread')
K_COVER, K_FMT, K_NAR = tok('jobkind', 'Cover design'), tok('jobkind', 'Formatting'), tok('jobkind', 'Narration')
K_TR, K_SET = tok('jobkind', 'Translation'), tok('jobkind', 'Setup and identifiers')
F_EB, F_PB = tok('format', 'Ebook'), tok('format', 'Paperback')
RELEASED, PREORD, INPROD = tok('tstatus', 'Released'), tok('tstatus', 'Pre-order'), tok('tstatus', 'In production')
ROLE_VA, ROLE_AUTH, ROLE_ACC, ROLE_TR = tok('role', 'Virtual assistant'), tok('role', 'Author-publisher'), tok('role', 'Accountant'), tok('role', 'Translator')
PB, ONT, BEH, NOS = ca('Paid back'), ca('On track'), ca('Behind'), ca('Not on sale yet')


def PH(role): return 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.role},0))&"","")' % role
def PHN(role): return 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % role
def CPH(): return CA('phone', 'Phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:contractor},{range:team.name},0))&"","")', 18)
def IMPRINT(): return CA('imprint', 'Imprint', 'text', '{set:company}', 22)
def VAPH(): return CA('va_phone', 'Assistant phone', 'text', PH(ROLE_VA), 18)
def AUPH(): return CA('author_phone', 'Author phone', 'text', PH(ROLE_AUTH), 18)


settings = [
    S('company', 'Your imprint name', 'text', COMPANY), S('cash_floor', 'Lowest cash balance you want to keep', 'money', CASH_FLOOR),
    S('payback_target_months', 'Months a title should take to earn back its cost', 'int', 24),
    S('budget_tolerance_pct', 'Quote above the typical rate that you accept', 'pct', 0.10), S('unit_tolerance_pct', 'Cost per unit away from your own average that you accept', 'pct', 0.15),
    S('go_payback_months', 'Payback in months that makes a new edition a go', 'int', 12),
    S('stretch_months', 'Payback in months that is still a stretch', 'int', 24),
    S('translate_go_months', 'Payback in months that makes a translation a go', 'int', 30),
    S('concentration_limit', 'Largest share of production spend for one contractor', 'pct', 0.35),
    S('invoice_days', 'Days ahead for the invoice cash test', 'int', 7), S('due_window_days', 'Days ahead that count as due soon', 'int', 30),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 jobs
tables.append(T('jobs', 'Jobs', 'Contractor job ledger',
    'One row per job: contractor, quote, units, dates, paid and status; the balance, days late, the overdue flag, the act-first rank and the message fields fill in by themselves.', [
    C('job_id', 'Job ID', 'text', 9, required=True), REF('title_id', 'Title ID', 'titles.title_id', 9), REF('title', 'Title', 'titles.title', 26), REF('edition_id', 'Edition ID', 'editions.edition_id', 10),
    LST('kind', 'Kind', 'jobkind', 18), REF('contractor', 'Contractor', 'team.name', 22), C('quote', 'Quote', 'money', 12), C('units', 'Units, thousand words or hours', 'num', 11), C('unit_rate', 'Unit rate', 'money', 11),
    C('start_date', 'Start date', 'date', 11), C('due_date', 'Due date', 'date', 11), C('delivered_on', 'Delivered on', 'date', 11), C('paid', 'Paid', 'money', 12), LST('status', 'Status', 'jstatus', 12),
    CA('balance', 'Balance', 'money', 'IF(ABS({col:quote}-{col:paid})<0.05,0,ROUND({col:quote}-{col:paid},2))', 12),
    CA('days_late', 'Days late', 'int', 'IF({col:delivered_on}>0,MAX(0,{col:delivered_on}-{col:due_date}),MAX(0,{today}-{col:due_date}))', 9),
    CA('late_open', 'Overdue now', 'int', 'IF({col:delivered_on}>0,0,IF(AND({col:due_date}<{today},{col:status}<>%s),1,0))' % JPAID, 9),
    CA('owed', 'Owed for booked work', 'money', 'IF(OR({col:status}=%s,{col:status}=%s),0,{col:balance})' % (JPAID, JQUOTED), 12),
    CA('attn_key', 'Act-first key', 'num', 'IF(OR({col:status}=%s,{col:status}=%s),"",{col:due_date}+VALUE(RIGHT({col:job_id},3))/10000)' % (JPAID, JQUOTED), 11),
    CA('attn_rank', 'Act-first rank', 'int', 'IF({col:attn_key}="","",COUNTIFS({range:jobs.attn_key},"<"&{col:attn_key})+1)', 9),
    CA('words', 'Words in the title', 'int', LKN('titles.words', 'titles.title_id', 'title_id'), 10), CPH(), IMPRINT(), VAPH(), AUPH()],
    D.jobs_d(), 400, [A('days_late', '> 0', 'warn'), A('status', '= ' + JDEL, 'warn'), A('status', '= ' + JPAID, 'good'), A('late_open', '= 1', 'bad')]))
# ---------------------------------------------------------------- 2 job payments
tables.append(T('jobpay', 'Job Payments', 'Contractor payments by stage',
    'One row per payment of a job: stage, date (the paid date, or the due date of an open payment), amount and status; the title, the job kind, the open-payment rank and the phone fill in by themselves.', [
    C('cpay_id', 'Payment ID', 'text', 10, required=True), REF('job_id', 'Job ID', 'jobs.job_id', 9), REF('title_id', 'Title ID', 'titles.title_id', 9), REF('contractor', 'Contractor', 'team.name', 22),
    LST('stage', 'Stage', 'stage', 11), C('date', 'Date', 'date', 11), C('amount', 'Amount', 'money', 12), LST('status', 'Status', 'cpaystatus', 11),
    CA('title', 'Title', 'text', LKT('titles.title', 'titles.title_id', 'title_id'), 26), CA('kind', 'Job kind', 'text', LKT('jobs.kind', 'jobs.job_id', 'job_id'), 18),
    CA('open_key', 'Open key', 'num', 'IF({col:status}=%s,"",{col:date}+VALUE(RIGHT({col:cpay_id},4))/100000)' % PAID, 11),
    CA('open_rank', 'Due order', 'int', 'IF({col:open_key}="","",COUNTIFS({range:jobpay.open_key},"<"&{col:open_key})+1)', 9), CPH(), IMPRINT()],
    D.jobpay_d(), 500, [A('status', '= ' + tok('cpaystatus', 'Due'), 'warn'), A('status', '= ' + PAID, 'good')]))
# ---------------------------------------------------------------- 3 titles
tables.append(T('titles', 'Titles', 'Titles with production cost and royalties to date',
    'One row per title: pen name, series, release date, status, words and royalties earned before the months on Royalties by Month; the total cost and royalties to date fill in.', [
    C('title_id', 'Title ID', 'text', 9, required=True), C('title', 'Title', 'text', 28), LST('pen_name', 'Pen name', 'penname', 16), LST('series', 'Series', 'series', 20), C('release_date', 'Release date', 'date', 11),
    LST('status', 'Status', 'tstatus', 12), C('words', 'Words', 'int', 9), C('royalty_before', 'Royalties before the months below', 'money', 13),
    CA('total_cost', 'Production cost', 'money', 'SUMIFS({range:jobs.quote},{range:jobs.title_id},{col:title_id})', 12),
    CA('royalties_to_date', 'Royalties to date', 'money', '{col:royalty_before}+SUMIFS({range:roy_month.royalties},{range:roy_month.title},{col:title})', 12),
    CA('cost_per_1000', 'Cost per 1,000 words', 'money', 'IF({col:words}>0,ROUND({col:total_cost}/({col:words}/1000),2),0)', 11)],
    D.titles_d(), 80, [A('status', '= ' + PREORD, 'good')]))
# ---------------------------------------------------------------- 4 editions
tables.append(T('editions', 'Editions', 'Editions with price, cost and royalty per copy',
    'One row per edition: format, list price, unit cost (print cost, delivery cost or 0), royalty share (check each store\'s current terms), hours and release date; the royalty per copy fills in by itself.', [
    C('edition_id', 'Edition ID', 'text', 10, required=True), REF('title_id', 'Title ID', 'titles.title_id', 9), REF('title', 'Title', 'titles.title', 26), LST('format', 'Format', 'format', 12),
    C('list_price', 'List price', 'money', 11), C('unit_cost', 'Unit cost', 'money', 11), C('royalty_share', 'Royalty share', 'pct', 10), C('hours', 'Finished hours', 'num', 9),
    C('release_date', 'Release date', 'date', 11), LST('status', 'Status', 'estatus', 12),
    CA('royalty_per_copy', 'Royalty per copy', 'money', 'MAX(0,ROUND({col:list_price}*{col:royalty_share}-{col:unit_cost},2))', 11)],
    D.editions_d(), 200))
# ---------------------------------------------------------------- 5 cost categories
tables.append(T('cost_cat', 'Cost Categories', 'Typical rate by kind of job',
    'One row per kind of job: the unit and your typical rate (a typical range, check current terms); the Budget vs Actual sheet sets every quote against it.', [
    LST('kind', 'Kind', 'jobkind', 20, required=True), C('unit', 'Unit', 'text', 18), C('rate', 'Typical rate', 'money', 12)], D.cost_cat_d(), 50))
# ---------------------------------------------------------------- 6 team
tables.append(T('team', 'Team', 'Team and outside contacts',
    'One row per person you work with: role, phone, e-mail and the usual rate; the message links and phone lookups read this sheet.', [
    C('person_id', 'Person ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    C('rate', 'Usual rate', 'money', 10), C('rate_unit', 'Rate unit', 'text', 28)], D.team_d(), 50))
# ---------------------------------------------------------------- 7 budget vs actual
JL = lambda c: LKT('jobs.%s' % c, 'jobs.job_id', 'job_id')
JN = lambda c: LKN('jobs.%s' % c, 'jobs.job_id', 'job_id')
tables.append(T('budget', 'Budget vs Actual', 'Typical-rate budget against the actual quote of each job',
    'One row per job (setup jobs left out): the quote at your typical rate against the actual quote; the amount over or under, the flag and the rank inside the title fill in.', [
    REF('job_id', 'Job ID', 'jobs.job_id', 9, required=True), CA('title_id', 'Title ID', 'text', JL('title_id'), 9), CA('title', 'Title', 'text', JL('title'), 26), CA('kind', 'Kind', 'text', JL('kind'), 18),
    CA('units', 'Units', 'num', JN('units'), 8),
    CA('typical_quote', 'Quote at the typical rate', 'money', 'IF({col:units}>0,ROUND(SUMIFS({range:cost_cat.rate},{range:cost_cat.kind},{col:kind})*{col:units},2),SUMIFS({range:cost_cat.rate},{range:cost_cat.kind},{col:kind}))', 13),
    CA('quote', 'Actual quote', 'money', JN('quote'), 12), CA('paid', 'Paid', 'money', JN('paid'), 12), CA('balance', 'Balance', 'money', JN('balance'), 12),
    CA('over_amount', 'Over (+) or under (-) the typical rate', 'money', 'ROUND({col:quote}-{col:typical_quote},2)', 13),
    CA('over_pct', 'Over or under, %', 'pct', 'IF({col:typical_quote}>0,{col:over_amount}/{col:typical_quote},0)', 10),
    CA('over_only', 'Amount over', 'money', 'MAX(0,{col:over_amount})', 11),
    CA('flag', 'Rate check', 'text', 'IF({col:over_pct}>{set:budget_tolerance_pct},%s,IF({col:over_pct}<-{set:budget_tolerance_pct},%s,%s))' % (ca('Over the typical rate'), ca('Under the typical rate'), ca('Within the typical rate')), 16),
    CA('title_rank', 'Rank inside the title', 'int', 'COUNTIFS({range:budget.title_id},{col:title_id},{range:budget.over_amount},">"&{col:over_amount})+1', 9),
    CA('rank_key', 'Rank key', 'text', '{col:title_id}&"|"&{col:title_rank}', 11), CA('author_phone', 'Author phone', 'text', PH(ROLE_AUTH), 18), IMPRINT()],
    D.budget_d(), 400, [A('flag', '= ' + ca('Over the typical rate'), 'bad'), A('flag', '= ' + ca('Under the typical rate'), 'good')]))
# ---------------------------------------------------------------- 8 cost per title
def KSUM(*ks): return '+'.join('SUMIFS({range:jobs.quote},{range:jobs.title_id},{col:title_id},{range:jobs.kind},%s)' % k for k in ks)
TL = lambda c: LKT('titles.%s' % c, 'titles.title_id', 'title_id')
tables.append(T('cost_title', 'Cost per Title', 'Production cost per title by kind of job',
    'One row per title: editing, cover, formatting, narration, translation and other cost from the Jobs sheet, the total, the cost per 1,000 words and the amount over the typical-rate budget.', [
    REF('title_id', 'Title ID', 'titles.title_id', 9, required=True), CA('title', 'Title', 'text', TL('title'), 28),
    CA('editing', 'Editing', 'money', KSUM(K_DEV, K_COPY, K_PROOF), 11), CA('cover', 'Cover', 'money', KSUM(K_COVER), 11), CA('formatting', 'Formatting', 'money', KSUM(K_FMT), 11),
    CA('narration', 'Narration', 'money', KSUM(K_NAR), 11), CA('translation', 'Translation', 'money', KSUM(K_TR), 11), CA('other', 'Setup and other', 'money', KSUM(K_SET), 11),
    CA('total', 'Total cost', 'money', 'SUMIFS({range:jobs.quote},{range:jobs.title_id},{col:title_id})', 12),
    CA('words', 'Words in the title', 'int', LKN('titles.words', 'titles.title_id', 'title_id'), 9),
    CA('cost_per_1000', 'Cost per 1,000 words', 'money', 'IF({col:words}>0,ROUND({col:total}/({col:words}/1000),2),0)', 11),
    CA('over_typical', 'Over (+) or under (-) typical rates', 'money', 'ROUND(SUMIFS({range:budget.over_amount},{range:budget.title_id},{col:title_id}),2)', 13),
    CA('over_key', 'Amount over, ranking key', 'num', '{col:over_typical}+VALUE(RIGHT({col:title_id},3))/100000', 11),
    CA('over_rank', 'Rank by amount over', 'int', 'COUNTIFS({range:cost_title.over_key},">"&{col:over_key})+1', 9),
    CA('accountant', 'Accountant', 'text', PHN(ROLE_ACC), 22), CA('accountant_phone', 'Accountant phone', 'text', PH(ROLE_ACC), 18), IMPRINT()],
    D.cost_title_d(), 80, [A('over_rank', '<= 3', 'warn')]))
# ---------------------------------------------------------------- 9 cost per edition
EL = lambda c: LKT('editions.%s' % c, 'editions.edition_id', 'edition_id')
EN = lambda c: LKN('editions.%s' % c, 'editions.edition_id', 'edition_id')
tables.append(T('cost_edition', 'Cost per Edition', 'Cost, royalty per copy and break-even copies per edition',
    'One row per edition: copies sold and royalties earned to date (type them from your ledger); the allocated cost, break-even copies and share reached fill in by themselves.', [
    REF('edition_id', 'Edition ID', 'editions.edition_id', 10, required=True), C('copies_sold', 'Copies sold to date', 'int', 11), C('royalties_earned', 'Royalties earned to date', 'money', 12),
    CA('title_id', 'Title ID', 'text', EL('title_id'), 9), CA('title', 'Title', 'text', EL('title'), 26), CA('format', 'Format', 'text', EL('format'), 12),
    CA('series', 'Series', 'text', 'IFERROR(INDEX({range:titles.series},MATCH({col:title_id},{range:titles.title_id},0))&"","")', 20),
    CA('own_cost', 'Cost of this edition only', 'money', 'SUMIFS({range:jobs.quote},{range:jobs.edition_id},{col:edition_id})', 12),
    CA('shared_cost', 'Share of the title cost', 'money', 'IF(OR({col:format}=%s,{col:format}=%s),ROUND((SUMIFS({range:jobs.quote},{range:jobs.title_id},{col:title_id})-SUMIFS({range:cost_edition.own_cost},{range:cost_edition.title_id},{col:title_id}))/2,2),0)' % (F_EB, F_PB), 12),
    CA('alloc_cost', 'Allocated cost', 'money', 'ROUND({col:own_cost}+{col:shared_cost},2)', 12), CA('rpc', 'Royalty per copy', 'money', EN('royalty_per_copy'), 10),
    CA('break_even', 'Break-even copies', 'int', 'IF({col:rpc}>0,ROUNDUP({col:alloc_cost}/{col:rpc},0),"")', 10),
    CA('share_reached', 'Share of break-even reached', 'pct', 'IF({col:break_even}="","",IF({col:break_even}>0,{col:copies_sold}/{col:break_even},1))', 11),
    CA('net', 'Royalties minus cost', 'money', 'ROUND({col:royalties_earned}-{col:alloc_cost},0)', 12), CA('cost_gap', 'Cost still to earn', 'money', 'MAX(0,ROUND({col:alloc_cost}-{col:royalties_earned},0))', 12),
    CA('net_rank', 'Rank, weakest first', 'int', 'COUNTIFS({range:cost_edition.title_id},{col:title_id},{range:cost_edition.net},"<"&{col:net})+1', 9),
    CA('net_key', 'Rank key', 'text', '{col:title_id}&"|"&{col:net_rank}', 11),
    CA('copies_month', 'Copies a month since release', 'num', 'IF(%s>{today},0,ROUND({col:copies_sold}/MAX(1,({today}-%s)/30.4),1))' % (EN('release_date'), EN('release_date')), 11),
    CA('has_audio', 'Title has audio', 'int', 'IF(COUNTIFS({range:cost_edition.title_id},{col:title_id},{range:cost_edition.format},%s,{range:cost_edition.copies_sold},">0")>0,1,0)' % tok('format', 'Audiobook'), 8),
    CA('has_lp', 'Title has large print', 'int', 'IF(COUNTIFS({range:cost_edition.title_id},{col:title_id},{range:cost_edition.format},%s,{range:cost_edition.copies_sold},">0")>0,1,0)' % tok('format', 'Large print'), 8),
    CA('has_hc', 'Title has hardcover', 'int', 'IF(COUNTIFS({range:cost_edition.title_id},{col:title_id},{range:cost_edition.format},%s,{range:cost_edition.copies_sold},">0")>0,1,0)' % tok('format', 'Hardcover'), 8),
    CA('author_phone', 'Author phone', 'text', PH(ROLE_AUTH), 18), IMPRINT()],
    D.cost_edition_d(), 200, [A('share_reached', '>= 1', 'good'), A('cost_gap', '> 1000', 'warn')]))
# ---------------------------------------------------------------- 10 payback by title
tables.append(T('payback', 'Payback by Title', 'Months to pay back each title from actual royalties',
    'One row per title: cost, royalties to date, your own monthly average of 6 months and the months still needed; the verdict and the format that drags the title fill in.', [
    REF('title_id', 'Title ID', 'titles.title_id', 9, required=True), CA('title', 'Title', 'text', TL('title'), 28), CA('series', 'Series', 'text', TL('series'), 20), CA('status', 'Status', 'text', TL('status'), 12),
    CA('cost', 'Production cost', 'money', LKN('cost_title.total', 'cost_title.title_id', 'title_id'), 12), CA('to_date', 'Royalties to date', 'money', LKN('titles.royalties_to_date', 'titles.title_id', 'title_id'), 12),
    CA('gap', 'Still to earn back', 'money', 'MAX(0,ROUND({col:cost}-{col:to_date},0))', 12),
    CA('months_on_sale', 'Months on sale', 'int', 'IF(%s>{today},0,INT(({today}-%s)/30.4375))' % (LKN('titles.release_date', 'titles.title_id', 'title_id'), LKN('titles.release_date', 'titles.title_id', 'title_id')), 9),
    CA('avg_monthly', 'Own monthly average, last 6 months', 'money', 'IFERROR(AVERAGEIFS({range:roy_month.royalties},{range:roy_month.title},{col:title},{range:roy_month.month},">="&EDATE(%s,-6),{range:roy_month.month},"<"&%s),IFERROR(AVERAGEIFS({range:roy_month.royalties},{range:roy_month.title},{col:title},{range:roy_month.month},">="&EDATE(%s,-6)),0))' % (MS, MS, MS), 13),
    CA('months_to_pay', 'Months still needed', 'num', 'IF({col:cost}<=0,"",IF({col:to_date}>={col:cost},0,IF({col:avg_monthly}>0,ROUND(({col:cost}-{col:to_date})/{col:avg_monthly},1),"")))', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:cost}<=0,%s,IF({col:to_date}>={col:cost},%s,IF({col:months_to_pay}="",IF({col:status}=%s,%s,%s),IF({col:months_on_sale}+{col:months_to_pay}<={set:payback_target_months},%s,%s))))' % (NOS, PB, INPROD, NOS, BEH, ONT, BEH), 14),
    CA('pct_back', 'Share earned back', 'pct', 'IF({col:cost}>0,{col:to_date}/{col:cost},"")', 9),
    CA('drag_format', 'Format that drags the title', 'text', 'IFERROR(INDEX({range:cost_edition.format},MATCH({col:title_id}&"|1",{range:cost_edition.net_key},0))&"","")', 14),
    CA('drag_net', 'Royalties minus cost of that format', 'money', 'SUMIFS({range:cost_edition.net},{range:cost_edition.net_key},{col:title_id}&"|1")', 13),
    CA('behind_gap', 'Gap of a title behind', 'money', 'IF({col:verdict}=%s,{col:gap},0)' % BEH, 11),
    CA('unpaid_key', 'Newest unpaid key', 'num', 'IF(AND({col:cost}>{col:to_date},{col:status}<>%s),%s,"")' % (INPROD, LKN('titles.release_date', 'titles.title_id', 'title_id')), 11),
    CA('ok_m20', 'On track, sales down 20%', 'int', 'IF({col:cost}<=0,0,IF({col:gap}<=0,1,IF({col:avg_monthly}>0,IF({col:months_on_sale}+{col:gap}/({col:avg_monthly}*0.8)<={set:payback_target_months},1,0),0)))', 8),
    CA('ok_0', 'On track, sales as now', 'int', 'IF({col:cost}<=0,0,IF({col:gap}<=0,1,IF({col:avg_monthly}>0,IF({col:months_on_sale}+{col:gap}/{col:avg_monthly}<={set:payback_target_months},1,0),0)))', 8),
    CA('ok_p20', 'On track, sales up 20%', 'int', 'IF({col:cost}<=0,0,IF({col:gap}<=0,1,IF({col:avg_monthly}>0,IF({col:months_on_sale}+{col:gap}/({col:avg_monthly}*1.2)<={set:payback_target_months},1,0),0)))', 8),
    CA('author_phone', 'Author phone', 'text', PH(ROLE_AUTH), 18), IMPRINT()],
    D.payback_d(), 80, [A('verdict', '= ' + BEH, 'bad'), A('verdict', '= ' + PB, 'good'), A('verdict', '= ' + ONT, 'warn')]))
# ---------------------------------------------------------------- 11 break-even by series and format
CE = lambda col, extra='': 'SUMIFS({range:cost_edition.%s},{range:cost_edition.series},{col:series},{range:cost_edition.format},{col:format}%s)' % (col, extra)
tables.append(T('be_series', 'Break-Even by Series', 'Break-even copies by series and format',
    'One row per series and format: allocated cost, copies sold and royalties earned; the royalty per copy you earn, the break-even copies and the share reached fill in.', [
    LST('series', 'Series', 'series', 20, required=True), LST('format', 'Format', 'format', 12),
    CA('editions', 'Editions', 'int', 'COUNTIFS({range:cost_edition.series},{col:series},{range:cost_edition.format},{col:format})', 8), CA('cost', 'Allocated cost', 'money', CE('alloc_cost'), 12),
    CA('copies', 'Copies sold', 'int', CE('copies_sold'), 10), CA('earned', 'Royalties earned', 'money', CE('royalties_earned'), 12),
    CA('rpc', 'Royalty per copy, actual', 'money', 'IF({col:copies}>0,ROUND({col:earned}/{col:copies},2),"")', 11),
    CA('break_even', 'Break-even copies', 'int', 'IF({col:rpc}="","",IF({col:rpc}>0,ROUNDUP({col:cost}/{col:rpc},0),""))', 10),
    CA('share_reached', 'Share of break-even reached', 'pct', 'IF({col:cost}>0,{col:earned}/{col:cost},"")', 11)],
    D.be_series_d(), 60, [A('share_reached', '< 1', 'warn'), A('share_reached', '>= 1', 'good')]))
# ---------------------------------------------------------------- 12 contractor totals
CJ = lambda col, k: 'SUMIFS({range:jobs.%s},{range:jobs.contractor},{col:contractor},{range:jobs.kind},%s)' % (col, k)
UNITS_K = [K_DEV, K_COPY, K_PROOF, K_TR]
tables.append(T('contractors', 'Contractor Totals', 'What each contractor quoted, was paid and is owed',
    'One row per contractor: jobs, quoted, paid in 12 months and all time, balance owed and late jobs; the share of spend and the cost per 1,000 words and per hour fill in.', [
    LST('contractor', 'Contractor', 'contractor', 22, required=True),
    CA('role', 'Role', 'text', 'IFERROR(INDEX({range:team.role},MATCH({col:contractor},{range:team.name},0))&"","")', 18),
    CA('jobs', 'Jobs', 'int', 'COUNTIFS({range:jobs.contractor},{col:contractor})', 7), CA('quoted', 'Quoted', 'money', 'SUMIFS({range:jobs.quote},{range:jobs.contractor},{col:contractor})', 12),
    CA('paid_12m', 'Paid, last 12 months', 'money', 'SUMIFS({range:jobpay.amount},{range:jobpay.contractor},{col:contractor},{range:jobpay.status},%s,{range:jobpay.date},">="&({today}-365))' % PAID, 12),
    CA('paid_all', 'Paid, all time', 'money', 'SUMIFS({range:jobpay.amount},{range:jobpay.contractor},{col:contractor},{range:jobpay.status},%s)' % PAID, 12),
    CA('balance_owed', 'Balance owed for booked work', 'money', 'SUMIFS({range:jobs.owed},{range:jobs.contractor},{col:contractor})', 12),
    CA('late_jobs', 'Late jobs, all time', 'int', 'COUNTIFS({range:jobs.contractor},{col:contractor},{range:jobs.days_late},">0")', 8),
    CA('share12', 'Share of spend, 12 months', 'pct', 'IF(SUM({range:contractors.paid_12m})>0,{col:paid_12m}/SUM({range:contractors.paid_12m}),0)', 10),
    CA('cost_1000', 'Cost per 1,000 words', 'money', 'IFERROR((%s)/(%s),0)' % ('+'.join(CJ('quote', k) for k in UNITS_K), '+'.join(CJ('units', k) for k in UNITS_K)), 11),
    CA('cost_hour', 'Cost per finished hour', 'money', 'IFERROR(%s/%s,0)' % (CJ('quote', K_NAR), CJ('units', K_NAR)), 11)],
    D.contractors_d(), 50, [A('late_jobs', '> 2', 'warn'), A('share12', '> {set:concentration_limit}', 'bad')]))
# ---------------------------------------------------------------- 13 invoices due
RK = lambda c: 'IFERROR(INDEX({range:jobpay.%s},MATCH({col:rank_no},{range:jobpay.open_rank},0))&"","")' % c
tables.append(T('due', 'Invoices Due', 'Open invoices in due order against your cash floor',
    'Rows 1 to 14 list the open payments, nearest due date first, from the Job Payments sheet; the cash after paying all invoices up to that one and the floor check fill in by themselves.', [
    C('rank_no', 'Order', 'int', 8, required=True), CA('cpay_id', 'Payment ID', 'text', RK('cpay_id'), 10), CA('job_id', 'Job ID', 'text', RK('job_id'), 9),
    CA('contractor', 'Contractor', 'text', RK('contractor'), 22), CA('title', 'Title', 'text', RK('title'), 26), CA('stage', 'Stage', 'text', RK('stage'), 10),
    CA('due_date', 'Due date', 'date', 'IFERROR(INDEX({range:jobpay.date},MATCH({col:rank_no},{range:jobpay.open_rank},0)),"")', 11),
    CA('amount', 'Amount', 'money', 'IFERROR(INDEX({range:jobpay.amount},MATCH({col:rank_no},{range:jobpay.open_rank},0)),"")', 12),
    CA('days_to_due', 'Days to due date', 'int', 'IF({col:cpay_id}="","",{col:due_date}-{today})', 9),
    CA('cum_due', 'Open invoices up to this one', 'money', 'IF({col:cpay_id}="","",SUMIFS({range:jobpay.amount},{range:jobpay.open_rank},"<="&{col:rank_no}))', 13),
    CA('cash_after', 'Cash after paying them', 'money', 'IF({col:cpay_id}="","",ROUND(%s-{col:cum_due},0))' % CASHNOW, 12),
    CA('floor_flag', 'Cash check', 'text', 'IF({col:cpay_id}="","",IF({col:cash_after}<{set:cash_floor},%s,%s))' % (ca('Below the floor'), ca('Above the floor')), 14),
    CA('window', 'Due window', 'text', 'IF({col:cpay_id}="","",IF({col:days_to_due}<=7,%s,IF({col:days_to_due}<={set:due_window_days},%s,%s)))' % (ca('Due in 7 days'), ca('Due in 30 days'), ca('Due later')), 14),
    CA('cash_alone', 'Cash after paying this one alone', 'money', 'IF({col:cpay_id}="","",ROUND(%s-{col:amount},0))' % CASHNOW, 12),
    CA('phone', 'Contractor phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:contractor},{range:team.name},0))&"","")', 18), VAPH(), AUPH(), IMPRINT()],
    D.rank_d(14), 50, [A('floor_flag', '= ' + ca('Below the floor'), 'bad'), A('window', '= ' + ca('Due in 7 days'), 'warn')]))
# ---------------------------------------------------------------- 14 overdue and unpaid jobs
RJ = lambda c: 'IFERROR(INDEX({range:jobs.%s},MATCH({col:rank_no},{range:jobs.attn_rank},0))&"","")' % c
RJN = lambda c: 'IFERROR(INDEX({range:jobs.%s},MATCH({col:rank_no},{range:jobs.attn_rank},0)),"")' % c
tables.append(T('attention', 'Overdue and Unpaid Jobs', 'Booked and open jobs, nearest due date first',
    'Rows 1 to 14 list every job that is booked, in progress or delivered but not paid, oldest due date first; the days late, the balance owed and the reason fill in by themselves.', [
    C('rank_no', 'Order', 'int', 8, required=True), CA('job_id', 'Job ID', 'text', RJ('job_id'), 9), CA('title', 'Title', 'text', RJ('title'), 26), CA('kind', 'Kind', 'text', RJ('kind'), 18),
    CA('contractor', 'Contractor', 'text', RJ('contractor'), 22), CA('due_date', 'Due date', 'date', RJN('due_date'), 11), CA('days_late', 'Days late', 'int', RJN('days_late'), 9),
    CA('balance', 'Balance owed', 'money', RJN('balance'), 12),
    CA('reason', 'Why it is listed', 'text', 'IF({col:job_id}="","",IF(IFERROR(INDEX({range:jobs.late_open},MATCH({col:rank_no},{range:jobs.attn_rank},0)),0)=1,%s,IF(IFERROR(INDEX({range:jobs.status},MATCH({col:rank_no},{range:jobs.attn_rank},0)),"")=%s,%s,IF(IFERROR(INDEX({range:jobs.status},MATCH({col:rank_no},{range:jobs.attn_rank},0)),"")=%s,%s,%s))))' % (ca('Overdue'), JDEL, ca('Delivered, not paid'), JIP, ca('In progress'), ca('Booked')), 18),
    CA('overdue_count', 'Jobs overdue now', 'int', 'SUM({range:jobs.late_open})', 9),
    CA('phone', 'Contractor phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:contractor},{range:team.name},0))&"","")', 18), VAPH(), AUPH(), IMPRINT()],
    D.rank_d(14), 50, [A('reason', '= ' + ca('Overdue'), 'bad'), A('reason', '= ' + ca('Delivered, not paid'), 'warn')]))
# ---------------------------------------------------------------- 15 unit cost check
tables.append(T('unitcost', 'Unit Cost Check', 'Cost per unit against your own average',
    'One row per job priced by the unit (edits, narration, translation): the cost per unit against your own average for that kind; the difference and the check (fair, high or low) fill in by themselves.', [
    REF('job_id', 'Job ID', 'jobs.job_id', 9, required=True), CA('title', 'Title', 'text', JL('title'), 26), CA('kind', 'Kind', 'text', JL('kind'), 18), CA('contractor', 'Contractor', 'text', JL('contractor'), 22),
    CA('units', 'Units', 'num', JN('units'), 8), CA('quote', 'Quote', 'money', JN('quote'), 12), CA('cost_per_unit', 'Cost per unit', 'money', 'IF({col:units}>0,ROUND({col:quote}/{col:units},2),0)', 11),
    CA('own_avg', 'Own average for the kind', 'money', 'IFERROR(ROUND(SUMIFS({range:jobs.quote},{range:jobs.kind},{col:kind},{range:jobs.units},">0")/SUMIFS({range:jobs.units},{range:jobs.kind},{col:kind}),2),0)', 12),
    CA('diff_pct', 'Difference', 'pct', 'IF({col:own_avg}>0,{col:cost_per_unit}/{col:own_avg}-1,0)', 10),
    CA('flag', 'Unit cost check', 'text', 'IF({col:diff_pct}>{set:unit_tolerance_pct},%s,IF({col:diff_pct}<-{set:unit_tolerance_pct},%s,%s))' % (ca('High for the kind'), ca('Low for the kind'), ca('Fair for the kind')), 16)],
    D.unitcost_d(), 200, [A('flag', '= ' + ca('High for the kind'), 'bad'), A('flag', '= ' + ca('Low for the kind'), 'good')]))
# ---------------------------------------------------------------- 16 go or no-go
tables.append(T('gonogo', 'Edition Go or No-go', 'Go or no-go cases with low, mid and high sales',
    'One row per new edition you weigh: one-off cost, royalty per copy and copies a month (low, mid, high); the payback months and the verdict (produce, wait or skip) fill in.', [
    C('case_id', 'Case ID', 'text', 9, required=True), REF('title', 'Title', 'titles.title', 26), LST('format', 'New format', 'gofmt', 12), C('opened_on', 'Opened on', 'date', 11), C('one_off_cost', 'One-off cost', 'money', 12),
    C('list_price', 'List price', 'money', 10), C('royalty_per_copy', 'Royalty per copy', 'money', 10), C('copies_low', 'Copies a month, low', 'int', 9), C('copies_mid', 'Copies a month, mid', 'int', 9),
    C('copies_high', 'Copies a month, high', 'int', 9), LST('status', 'Case status', 'gostatus', 10),
    CA('payback_low', 'Payback months, low', 'num', 'IF({col:copies_low}*{col:royalty_per_copy}>0,ROUND({col:one_off_cost}/({col:copies_low}*{col:royalty_per_copy}),1),"")', 10),
    CA('payback_mid', 'Payback months, mid', 'num', 'IF({col:copies_mid}*{col:royalty_per_copy}>0,ROUND({col:one_off_cost}/({col:copies_mid}*{col:royalty_per_copy}),1),"")', 10),
    CA('payback_high', 'Payback months, high', 'num', 'IF({col:copies_high}*{col:royalty_per_copy}>0,ROUND({col:one_off_cost}/({col:copies_high}*{col:royalty_per_copy}),1),"")', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:payback_mid}="",%s,IF({col:payback_mid}<={set:go_payback_months},%s,IF({col:payback_mid}<={set:stretch_months},%s,%s)))' % (ca('Skip'), ca('Produce'), ca('Wait'), ca('Skip')), 12),
    AUPH(), IMPRINT()],
    D.gonogo_d(), 60, [A('verdict', '= ' + ca('Produce'), 'good'), A('verdict', '= ' + ca('Skip'), 'bad'), A('verdict', '= ' + ca('Wait'), 'warn')]))
# ---------------------------------------------------------------- 17 translation cases
tables.append(T('translation', 'Translation Cases', 'Translation business cases',
    'One row per title and language: translation, edit and cover cost, royalty per copy and the copies a month you expect; the total cost, payback months and verdict fill in.', [
    C('case_id', 'Case ID', 'text', 9, required=True), REF('title', 'Title', 'titles.title', 26), LST('language', 'Language', 'language', 12), C('translation_cost', 'Translation cost', 'money', 12),
    C('edit_cost', 'Edit cost', 'money', 10), C('cover_cost', 'Cover cost', 'money', 10), C('price', 'Price', 'money', 9), C('royalty', 'Royalty per copy', 'money', 10), C('copies_month', 'Copies a month', 'int', 9),
    CA('total_cost', 'Total cost', 'money', '{col:translation_cost}+{col:edit_cost}+{col:cover_cost}', 12),
    CA('payback', 'Months to pay back', 'num', 'IF({col:copies_month}*{col:royalty}>0,ROUND({col:total_cost}/({col:copies_month}*{col:royalty}),1),"")', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:payback}="",%s,IF({col:payback}<={set:translate_go_months},%s,IF({col:payback}<=2*{set:translate_go_months},%s,%s)))' % (ca('Skip'), ca('Translate'), ca('Wait'), ca('Sell the rights instead')), 20),
    CA('translator', 'Translator', 'text', PHN(ROLE_TR), 22), CA('phone', 'Translator phone', 'text', PH(ROLE_TR), 18), IMPRINT()],
    D.translation_d(), 60, [A('verdict', '= ' + ca('Translate'), 'good'), A('verdict', '= ' + ca('Sell the rights instead'), 'warn')]))
# ---------------------------------------------------------------- 18 quote comparison
tables.append(T('quotes', 'Quote Comparison', 'Quotes received for coming jobs against your own average',
    'One row per quote you received: kind, title, contractor, price, units and days to deliver; the price per unit, your own average for the kind and the difference fill in by themselves.', [
    C('quote_id', 'Quote ID', 'text', 9, required=True), C('asked_on', 'Asked on', 'date', 11), LST('kind', 'Job kind', 'jobkind', 18), REF('title', 'Title', 'titles.title', 26), REF('contractor', 'Contractor', 'team.name', 22),
    C('quote', 'Quote', 'money', 11), C('units', 'Units', 'num', 8), C('days_to_deliver', 'Days to deliver', 'int', 9),
    CA('price_per_unit', 'Price per unit', 'money', 'IF({col:units}>0,ROUND({col:quote}/{col:units},2),0)', 11),
    CA('own_avg', 'Own average per unit', 'money', 'IF(SUMIFS({range:jobs.units},{range:jobs.kind},{col:kind})>0,IFERROR(ROUND(SUMIFS({range:jobs.quote},{range:jobs.kind},{col:kind},{range:jobs.units},">0")/SUMIFS({range:jobs.units},{range:jobs.kind},{col:kind}),2),0),IFERROR(ROUND(AVERAGEIFS({range:jobs.quote},{range:jobs.kind},{col:kind}),2),0))', 12),
    CA('diff_pct', 'Difference from your average', 'pct', 'IF({col:own_avg}>0,{col:price_per_unit}/{col:own_avg}-1,0)', 11),
    CA('flag', 'Quote check', 'text', 'IF({col:diff_pct}>{set:unit_tolerance_pct},%s,%s)' % (ca('Above your average'), ca('Below your average')), 16),
    CPH(), AUPH(), IMPRINT()],
    D.quotes_d(), 80, [A('flag', '= ' + ca('Above your average'), 'warn'), A('flag', '= ' + ca('Below your average'), 'good')]))
# ---------------------------------------------------------------- 19 royalties by title and month
tables.append(T('roy_month', 'Royalties by Month', 'Royalties by title and month (home currency)',
    'One row per title and month: the royalties and page reads you earned, type them from your royalty ledger; the payback and the royalty charts read this sheet. The series comes from the Titles sheet.', [
    C('roy_id', 'Row ID', 'text', 9, required=True), REF('title', 'Title', 'titles.title', 26), C('month', 'Month', 'date', 11), LST('series', 'Series', 'series', 20), C('royalties', 'Royalties', 'money', 12)],
    D.roy_month_d(), 600))
# ---------------------------------------------------------------- 20 cash by month
tables.append(T('cash_month', 'Cash by Month', 'Closing cash by month against the floor',
    'One row per month: the closing cash balance, typed from your cash records; the free cash above your floor and the contractor payments of the month fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), C('closing', 'Closing cash', 'money', 12),
    CA('free_cash', 'Free cash above the floor', 'money', '{col:closing}-{set:cash_floor}', 13),
    CA('paid_month', 'Contractor payments of the month', 'money', 'SUMIFS({range:jobpay.amount},{range:jobpay.status},%s,{range:jobpay.date},">="&{col:month},{range:jobpay.date},"<"&EDATE({col:month},1))' % PAID, 13),
    CA('accountant', 'Accountant', 'text', PHN(ROLE_ACC), 22), CA('accountant_phone', 'Accountant phone', 'text', PH(ROLE_ACC), 18), IMPRINT()],
    D.cash_d(), 50, [A('free_cash', '< 0', 'bad')]))
assert len(tables) == 20
