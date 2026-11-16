"""Nonprofit suite part 2: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np2_lists import *
import np2_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def ORG(): return CA('org', 'Organization', 'text', '{set:org}', 24)
def PH(k, label, phone): return CA(k, label, 'text', '"%s"' % phone, 18)
def R(t, c): return '{range:%s.%s}' % (t, c)
def DPH(): return CA('phone', 'Phone', 'text', LKT('donors.phone', 'donors.donor_id', 'donor_id'), 18)
THIS, LASTY, TWO = tok('yr', 'This year'), tok('yr', 'Last year'), tok('yr', 'Two years ago')
THIS2, LAST2 = tok('yr2', 'This year'), tok('yr2', 'Last year')
ALL = tok('dgroup', 'All donors')
S_RET, S_NEW, S_REC, S_LAP, S_NOT = [tok('gstate', x) for x in GSTATE]
F_UP, F_DOWN, F_STEADY, F_NO = [tok('gflag', x) for x in GFLAG]
CLOSED, COMMITTED, ASKMADE, CULT, IDENT = tok('pstage', 'Closed'), tok('pstage', 'Committed'), tok('pstage', 'Ask made'), tok('pstage', 'Cultivation'), tok('pstage', 'Identified')
YEARN = 'YEAR({today})'

settings = [
    S('org', 'Your organization name', 'text', COMPANY),
    S('retention_target', 'Retention you want to match, your own last year', 'pct', 0.47),
    S('cost_per_dollar', 'Cost to raise one dollar, starting point, set your own', 'num', COST_PER_DOLLAR),
    S('reserve_months', 'Months of reserve, starting point, set your own', 'num', RESERVE_MONTHS),
    S('upgrade_uplift', 'Upgrade ask: raise on the average gift', 'pct', 0.20),
    S('downgrade_drop', 'Giving fall that counts as a downgrade', 'pct', 0.30),
    S('win1', 'Your estimate: lapsed 1 year, share who return', 'pct', 0.15),
    S('win2', 'Your estimate: lapsed 2 years, share who return', 'pct', 0.08),
    S('win3', 'Your estimate: lapsed 3 years, share who return', 'pct', 0.04),
    S('major_goal', 'Major-gift goal this year', 'money', 45000),
    S('major_min', 'Yearly giving that counts as a major donor', 'money', 2500),
    S('prob_identified', 'Your estimate: identified prospect gives', 'pct', PROB_IDENTIFIED),
    S('prob_cultivation', 'Your estimate: prospect in cultivation gives', 'pct', PROB_CULTIVATION),
    S('prob_ask', 'Your estimate: prospect asked gives', 'pct', PROB_ASK),
    S('prob_committed', 'Your estimate: committed prospect gives', 'pct', PROB_COMMITTED),
    S('free_money', 'Free money now (cash less restricted and designated)', 'money', D.FREE_MONEY),
    S('monthly_expense', 'Average monthly expense', 'money', D.MONTHLY_EXPENSE),
    S('conc_watch', 'Share from the top 5 donors you are comfortable with', 'pct', 0.15),
    S('call_min', 'Last 3 years of giving worth a personal call', 'money', 1000),
    S('let_go_below', 'Last 3 years of giving below which you let go', 'money', 40),
]
assert len(settings) == 20
tables = []

# 1 gifts -------------------------------------------------------------------
tables.append(T('gifts', 'Gifts', "This year's gifts with appeal and channel",
    "One row per gift this year: date, donor, amount, appeal, campaign, channel, fund and type; new donors in the appeal and channel and the donor phone fill in. The full log is in part 1.", [
    C('gift_id', 'Gift ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('donor_id', 'Donor ID', 'text', 10), C('donor', 'Donor', 'text', 24), C('amount', 'Amount', 'money', 11),
    LST('appeal', 'Appeal', 'appeal', 22), LST('campaign', 'Campaign', 'campaign', 18), LST('channel', 'Channel', 'channel', 14), LST('fund', 'Fund', 'fund', 20), LST('gift_type', 'Gift type', 'gtype', 14),
    CA('new_in_appeal', 'First gift to this appeal this year', 'int', 'IF(COUNTIFS({range:gifts.donor_id},{col:donor_id},{range:gifts.appeal},{col:appeal},{range:gifts.date},"<"&{col:date})=0,1,0)', 12),
    CA('new_in_channel', 'First gift by this channel this year', 'int', 'IF(COUNTIFS({range:gifts.donor_id},{col:donor_id},{range:gifts.channel},{col:channel},{range:gifts.date},"<"&{col:date})=0,1,0)', 12),
    DPH(), ORG()], D.gifts_d(), 3000))
# 2 donors ------------------------------------------------------------------
tables.append(T('donors', 'Donors', 'Donor list with first and last gift',
    'One row per donor: type, status, how they joined, first and last gift, gift count and total; the full donor book is in part 1.', [
    C('donor_id', 'Donor ID', 'text', 10, required=True), C('donor', 'Donor', 'text', 24), LST('type', 'Type', 'dtype', 16), LST('status', 'Status', 'dstatus', 10), LST('joined_via', 'Joined via', 'channel', 14),
    C('first_gift', 'First gift', 'date', 11), C('last_gift', 'Last gift', 'date', 11), C('gifts', 'Gifts', 'int', 8), C('total_given', 'Total given', 'money', 12), C('last_amount', 'Last gift amount', 'money', 11),
    C('contact', 'Contact person', 'text', 22), C('phone', 'Phone', 'text', 18), LST('contact_pref', 'Contact preference', 'pref', 14), ORG()], D.donors_d(), 1800,
    [A('status', '= ' + tok('dstatus', 'Lapsed'), 'warn')]))
# 3 giving ------------------------------------------------------------------
G = lambda c: R('giving', c)
tables.append(T('giving', 'Giving by Donor and Year', 'Giving by donor and year with state, change and ranks',
    'One row per donor: total given in each of the last 4 years (from your gift log); state this year, years given, change and the ranking scores fill in. At the new year move each total one column.', [
    C('donor_id', 'Donor ID', 'text', 10, required=True), C('y0', 'Given this year', 'num', 11), C('y1', 'Given last year', 'num', 11), C('y2', 'Given 2 years ago', 'num', 11), C('y3', 'Given 3 years ago', 'num', 11),
    CA('donor', 'Donor', 'text', LKT('donors.donor', 'donors.donor_id', 'donor_id'), 24), CA('type', 'Type', 'text', LKT('donors.type', 'donors.donor_id', 'donor_id'), 16),
    CA('source', 'Joined via', 'text', LKT('donors.joined_via', 'donors.donor_id', 'donor_id'), 14),
    CA('first_year', 'First gift year', 'int', 'IFERROR(IF(INDEX({range:donors.first_gift},MATCH({col:donor_id},{range:donors.donor_id},0))=0,"",YEAR(INDEX({range:donors.first_gift},MATCH({col:donor_id},{range:donors.donor_id},0)))),"")', 9),
    CA('years_given', 'Years given', 'int', '({col:y0}>0)+({col:y1}>0)+({col:y2}>0)+({col:y3}>0)', 8),
    CA('gap_years', 'Years since last gift', 'int', 'IF({col:y0}>0,0,IF({col:y1}>0,1,IF({col:y2}>0,2,IF({col:y3}>0,3,""))))', 9),
    CA('last_given', 'Last year given, amount', 'money', 'IF({col:y0}>0,{col:y0},IF({col:y1}>0,{col:y1},IF({col:y2}>0,{col:y2},{col:y3})))', 11),
    CA('state', 'State this year', 'text', 'IF({col:y0}>0,IF({col:y1}>0,%s,IF({col:first_year}=%s,%s,%s)),IF({col:y1}>0,%s,%s))' % (S_RET, YEARN, S_NEW, S_REC, S_LAP, S_NOT), 12),
    CA('change', 'Change on last year', 'money', '{col:y0}-{col:y1}', 11),
    CA('flag', 'Giving change', 'text', 'IF(AND({col:y0}>0,{col:y1}>0),IF({col:y0}>={col:y1}*(1+{set:upgrade_uplift}),%s,IF({col:y0}<={col:y1}*(1-{set:downgrade_drop}),%s,%s)),%s)' % (F_UP, F_DOWN, F_STEADY, F_NO), 12),
    CA('idn', 'Donor number', 'int', 'VALUE(RIGHT({col:donor_id},4))', 8),
    CA('lapsed_start', 'Lapsed at the start of the year', 'int', 'IF(AND(NOT({col:y1}>0),OR({col:y2}>0,{col:y3}>0)),1,0)', 10),
    CA('outreach', 'Outreach', 'text', 'IF({col:state}=%s,IF({col:y1}+{col:y2}+{col:y3}>={set:call_min},%s,IF({col:y1}+{col:y2}+{col:y3}<{set:let_go_below},%s,%s)),"")' % (S_LAP, va('Call'), va('Let go'), va('Write')), 9),
    CA('lapsed_score', 'Lapsed rank score', 'num', 'IF({col:state}=%s,ROUND({col:y1}+{col:y2}+{col:y3},0)+(2000-{col:idn})/10000,"")' % S_LAP, 11),
    CA('upgrade_score', 'Upgrade rank score', 'num', 'IF(AND({col:years_given}>=3,{col:y0}>0,{col:y1}>0,{col:flag}<>%s),ROUND({col:y0},0)+(2000-{col:idn})/10000,"")' % F_UP, 11),
    CA('down_score', 'Downgrade rank score', 'num', 'IF({col:flag}=%s,ROUND({col:y1}-{col:y0},0)+(2000-{col:idn})/10000,"")' % F_DOWN, 11),
    CA('top_score', 'Top donor rank score', 'num', 'IF({col:y0}>0,ROUND({col:y0},0)+(2000-{col:idn})/10000,"")', 11),
    CA('in_top10', 'In the top 10 donors', 'int', 'IF({col:y0}>0,IF(COUNTIFS({range:giving.top_score},">"&{col:top_score})<10,1,0),0)', 9),
    CA('phone', 'Phone', 'text', LKT('donors.phone', 'donors.donor_id', 'donor_id'), 18), ORG()], D.giving_d(), 1800,
    [A('state', '= ' + S_LAP, 'warn'), A('flag', '= ' + F_DOWN, 'warn'), A('flag', '= ' + F_UP, 'good')]))
# 4 retention by donor type (3 columns) ------------------------------------
tables.append(T('donor_types', 'Retention by Donor Type', 'Donors and retention by donor type',
    'One row per donor type: donors who gave this year and the share of last year donors of that type who gave again, from Giving by Donor and Year. This year is to date.', [
    LST('type', 'Type', 'dtype', 18, required=True), CA('donors', 'Donors', 'int', 'COUNTIFS(%s,{col:type},%s,">0")' % (G('type'), G('y0')), 9),
    CA('retention', 'Retention', 'pct', 'IFERROR(COUNTIFS(%s,{col:type},%s,">0",%s,">0")/COUNTIFS(%s,{col:type},%s,">0"),0)' % (G('type'), G('y0'), G('y1'), G('type'), G('y1')), 10)], D.donor_types_d(), 50))
# 5 retention detail --------------------------------------------------------
TY = '%s,{col:crit}' % G('type')
def RV(f):
    """f(cur, prev, pp) with the giving columns of this year (b0) or last year (b1)"""
    return 'IF({col:year}=%s,%s,%s)' % (THIS2, f(G('y0'), G('y1'), G('y2')), f(G('y1'), G('y2'), G('y3')))
tables.append(T('ret_detail', 'Retention Detail', 'Retained, new, lapsed and recaptured donors by group',
    'One row per year and donor group: donors, retained, new, lapsed and recaptured, retention, new-donor and repeat-donor retention against the year before. This year is to date.', [
    LST('year', 'Year', 'yr2', 12, required=True), LST('group', 'Donor group', 'dgroup', 18), C('review_on', 'Review date', 'date', 11),
    CA('crit', 'Group filter', 'text', 'IF({col:group}=%s,"*",{col:group})' % ALL, 12), CA('yearnum', 'Calendar year', 'int', '%s-IF({col:year}=%s,0,1)' % (YEARN, THIS2), 9),
    CA('donors', 'Donors', 'int', RV(lambda c, p, q: 'COUNTIFS(%s,%s,">0")' % (TY, c)), 9),
    CA('base', 'Donors the year before', 'int', RV(lambda c, p, q: 'COUNTIFS(%s,%s,">0")' % (TY, p)), 10),
    CA('retained', 'Retained', 'int', RV(lambda c, p, q: 'COUNTIFS(%s,%s,">0",%s,">0")' % (TY, c, p)), 9),
    CA('new', 'New', 'int', RV(lambda c, p, q: 'COUNTIFS(%s,%s,">0",%s,{col:yearnum})' % (TY, c, G('first_year'))), 8),
    CA('lapsed', 'Lapsed', 'int', '{col:base}-{col:retained}', 8),
    CA('recaptured', 'Recaptured', 'int', RV(lambda c, p, q: 'COUNTIFS(%s,%s,">0",%s,"<"&{col:yearnum})' % (TY, c, G('first_year'))) + '-{col:retained}', 10),
    CA('retention', 'Retention', 'pct', 'IF({col:base}>0,{col:retained}/{col:base},0)', 10),
    CA('new_ret', 'New-donor retention', 'pct', RV(lambda c, p, q: 'IFERROR(COUNTIFS(%s,%s,{col:yearnum}-1,%s,">0")/COUNTIFS(%s,%s,{col:yearnum}-1),0)' % (TY, G('first_year'), c, TY, G('first_year'))), 11),
    CA('repeat_ret', 'Repeat-donor retention', 'pct', RV(lambda c, p, q: 'IFERROR(COUNTIFS(%s,%s,">0",%s,"<"&({col:yearnum}-1),%s,">0")/COUNTIFS(%s,%s,">0",%s,"<"&({col:yearnum}-1)),0)' % (TY, p, G('first_year'), c, TY, p, G('first_year'))), 11),
    CA('last_ret', 'Last year own retention', 'pct', RV(lambda c, p, q: 'IFERROR(COUNTIFS(%s,%s,">0",%s,">0")/COUNTIFS(%s,%s,">0"),0)' % (TY, p, q, TY, q)), 11),
    CA('amount', 'Amount given', 'money', RV(lambda c, p, q: 'SUMIFS(%s,%s)' % (c, TY)), 12), PH('ed_phone', 'Executive director phone', D.ED_PHONE), ORG()], D.ret_detail_d(), 60))
# 6 lapsed list -------------------------------------------------------------
def GP(col, blank='""'): return 'IF({col:pos}="",%s,INDEX({range:giving.%s},{col:pos}))' % (blank, col)
def GPT(src, kc, blank='""'): return 'IF({col:donor_id}="",%s,%s)' % (blank, LKT(src, kc, 'donor_id'))
tables.append(T('lapsed', 'Lapsed List', 'Lapsed donors ranked for outreach',
    'One row per rank: donors who gave last year and not this year, ranked by what they gave in the last 3 years; last gift, years given, next step (Call, Write or Let go) and phone fill in.', [
    C('rank', 'Rank', 'int', 7, required=True), LST('caller', 'Caller', 'owner', 16), C('contact_by', 'Contact by', 'date', 11),
    CA('pos', 'Position', 'int', 'IFERROR(MATCH(LARGE({range:giving.lapsed_score},{col:rank}),{range:giving.lapsed_score},0),"")', 8),
    CA('donor_id', 'Donor ID', 'text', GP('donor_id'), 10), CA('donor', 'Donor', 'text', GP('donor'), 24),
    CA('last_gift', 'Last gift', 'date', 'IF({col:donor_id}="","",IFERROR(IF(INDEX({range:donors.last_gift},MATCH({col:donor_id},{range:donors.donor_id},0))=0,"",INDEX({range:donors.last_gift},MATCH({col:donor_id},{range:donors.donor_id},0))),""))', 11),
    CA('last_amount', 'Last gift amount', 'money', 'IF({col:donor_id}="","",' + LKN('donors.last_amount', 'donors.donor_id', 'donor_id') + ')', 11),
    CA('years_given', 'Years given', 'int', GP('years_given'), 8), CA('last_year', 'Given last year', 'money', GP('y1'), 11), CA('three_years', 'Given in the 3 years before this one', 'money', 'IF({col:pos}="","",INDEX({range:giving.y1},{col:pos})+INDEX({range:giving.y2},{col:pos})+INDEX({range:giving.y3},{col:pos}))', 13),
    CA('next_step', 'Next step', 'text', GP('outreach'), 10), CA('appeal', 'Invite to', 'text', '{list:appeal.year_end_letter}', 18),
    CA('week_calls', 'Calls planned this week', 'int', 'COUNTIFS({range:lapsed.contact_by},">="&{today},{range:lapsed.contact_by},"<="&({today}+6),{range:lapsed.next_step},%s)' % va('Call'), 9),
    CA('write_n', 'Notes to write', 'int', 'COUNTIFS({range:lapsed.next_step},%s)' % va('Write'), 9), CA('note_date', 'Writing day', 'date', 'WORKDAY({today},3)', 11),
    CA('phone', 'Donor phone', 'text', GPT('donors.phone', 'donors.donor_id'), 18), PH('dm_phone', 'Development manager phone', D.DM_PHONE), PH('vol_phone', 'Volunteer phone', D.VOL['phone']), ORG()], D.lapsed_d(), 150,
    [A('next_step', '= ' + va('Call'), 'warn')]))
# 7 upgrade -----------------------------------------------------------------
tables.append(T('upgrade', 'Upgrade Ask List', 'Regular donors to ask for more',
    'One row per rank: donors who gave in 3 or more years and in both of the last two, ranked by this year; the suggested ask is their own average gift plus your uplift. Add the date you last asked.', [
    C('rank', 'Rank', 'int', 7, required=True), C('ask_on', 'Planned ask date', 'date', 11), C('last_asked', 'Last asked on', 'date', 11),
    CA('pos', 'Position', 'int', 'IFERROR(MATCH(LARGE({range:giving.upgrade_score},{col:rank}),{range:giving.upgrade_score},0),"")', 8),
    CA('donor_id', 'Donor ID', 'text', GP('donor_id'), 10), CA('donor', 'Donor', 'text', GP('donor'), 24), CA('years_given', 'Years given', 'int', GP('years_given'), 8),
    CA('this_year', 'Given this year', 'money', GP('y0'), 11), CA('last_year', 'Given last year', 'money', GP('y1'), 11),
    CA('avg_gift', 'Average gift', 'money', 'IF({col:donor_id}="","",IFERROR(ROUND(INDEX({range:donors.total_given},MATCH({col:donor_id},{range:donors.donor_id},0))/INDEX({range:donors.gifts},MATCH({col:donor_id},{range:donors.donor_id},0)),0),0))', 10),
    CA('suggested_ask', 'Suggested ask', 'money', 'IF({col:avg_gift}="","",MAX(ROUND({col:avg_gift}*(1+{set:upgrade_uplift})/5,0)*5,{col:avg_gift}+5))', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:pos}="","",IF({col:last_asked}>0,IF({today}-{col:last_asked}<365,%s,%s),%s))' % (va('Wait'), va('Ask now'), va('Ask now')), 10),
    DPH(), ORG()], D.upgrade_d(), 100, [A('verdict', '= ' + va('Ask now'), 'good')]))
# 8 downgrade ---------------------------------------------------------------
tables.append(T('downgrade', 'Downgrade Watch', 'Donors whose giving fell',
    'One row per rank: donors who gave less this year than last by more than your set share, ranked by the fall; a verdict says who to call this month. This year is to date.', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('pos', 'Position', 'int', 'IFERROR(MATCH(LARGE({range:giving.down_score},{col:rank}),{range:giving.down_score},0),"")', 8),
    CA('donor_id', 'Donor ID', 'text', GP('donor_id'), 10), CA('donor', 'Donor', 'text', GP('donor'), 24), CA('last_year', 'Given last year', 'money', GP('y1'), 11), CA('this_year', 'Given this year', 'money', GP('y0'), 11),
    CA('drop', 'Drop', 'money', 'IF({col:pos}="","",{col:last_year}-{col:this_year})', 10), CA('drop_pct', 'Drop share', 'pct', 'IF({col:pos}="","",IF({col:last_year}>0,{col:drop}/{col:last_year},0))', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:pos}="","",IF({col:last_year}>={set:call_min}/2,%s,%s))' % (va('Call this month'), va('Note')), 14), DPH(), ORG()], D.ranks_d(40), 80,
    [A('verdict', '= ' + va('Call this month'), 'warn')]))
# 9 bands -------------------------------------------------------------------
tables.append(T('bands', 'Gift Size Bands', "Donors and money by size of this year's giving",
    "One row per band: donors whose total this year falls in the band, the money and its share of the year. Change the limits if you like.", [
    LST('band', 'Band', 'band', 18, required=True), C('lower', 'From', 'money', 10), C('upper', 'Below', 'money', 12),
    CA('donors', 'Donors', 'int', 'COUNTIFS(%s,">="&{col:lower},%s,"<"&{col:upper})' % (G('y0'), G('y0')), 9),
    CA('amount', 'Amount', 'money', 'SUMIFS(%s,%s,">="&{col:lower},%s,"<"&{col:upper})' % (G('y0'), G('y0'), G('y0')), 12),
    CA('share', 'Share of the year', 'pct', 'IFERROR({col:amount}/SUM(%s),0)' % G('y0'), 10), CA('avg_donor', 'Average per donor', 'money', 'IF({col:donors}>0,ROUND({col:amount}/{col:donors},0),0)', 10)], D.bands_d(), 50))
# 10 first-time donors ------------------------------------------------------
tables.append(T('first_time', 'First-Time Donors', 'First-time donors and their second gift',
    'One row per donor with the date of the first gift, its amount and appeal and the date of the second gift (blank if none); days to the second gift and a flag fill in.', [
    C('donor_id', 'Donor ID', 'text', 10, required=True), C('first_gift', 'First gift', 'date', 11), C('first_amount', 'First gift amount', 'money', 11), LST('first_appeal', 'First appeal', 'appeal', 22), C('second_gift', 'Second gift', 'date', 11),
    CA('donor', 'Donor', 'text', LKT('donors.donor', 'donors.donor_id', 'donor_id'), 24),
    CA('days_to_second', 'Days to second gift', 'int', 'IF({col:second_gift}>0,{col:second_gift}-{col:first_gift},"")', 9),
    CA('flag', 'Second gift', 'text', 'IF({col:second_gift}>0,IF({col:second_gift}-{col:first_gift}<=365,%s,%s),IF({today}-{col:first_gift}<=365,%s,%s))' % (vb('Second gift in time'), vb('Second gift late'), vb('Waiting for second gift'), vb('No second gift')), 20),
    CA('ask_by', 'Second gift window ends', 'date', 'EDATE({col:first_gift},12)', 11), DPH(), ORG()], D.first_time_d(), 1800))
# 11 conversion -------------------------------------------------------------
FT = lambda c: R('first_time', c)
COH_A = '%s,">="&EDATE({today},-24),%s,"<"&EDATE({today},-12)' % (FT('first_gift'), FT('first_gift'))
COH_B = '%s,">="&EDATE({today},-36),%s,"<"&EDATE({today},-24)' % (FT('first_gift'), FT('first_gift'))
tables.append(T('conversion', 'Second-Gift Conversion', 'Second-gift conversion by appeal',
    'One row per appeal: first-time donors whose first gift was 12 to 24 months ago, how many gave again within 12 months, the rate and your own rate for the year before.', [
    LST('appeal', 'Appeal', 'appeal', 24, required=True),
    CA('first_timers', 'First-time donors', 'int', 'COUNTIFS(%s,{col:appeal},%s)' % (FT('first_appeal'), COH_A), 10),
    CA('gave_again', 'Gave again within 12 months', 'int', 'COUNTIFS(%s,{col:appeal},%s,%s,"<=365")' % (FT('first_appeal'), COH_A, FT('days_to_second')), 12),
    CA('conversion', 'Conversion', 'pct', 'IF({col:first_timers}>0,{col:gave_again}/{col:first_timers},0)', 10),
    CA('earlier_timers', 'First-time donors the year before', 'int', 'COUNTIFS(%s,{col:appeal},%s)' % (FT('first_appeal'), COH_B), 12),
    CA('last_conv', 'Own conversion the year before', 'pct', 'IFERROR(COUNTIFS(%s,{col:appeal},%s,%s,"<=365")/{col:earlier_timers},0)' % (FT('first_appeal'), COH_B, FT('days_to_second')), 12),
    CA('gap_points', 'Difference, points', 'pct', '{col:conversion}-{col:last_conv}', 10),
    CA('verdict', 'Against own last year', 'text', 'IF({col:gap_points}>0.02,%s,IF({col:gap_points}<-0.02,%s,%s))' % (vb('Above own last year'), vb('Below own last year'), vb('Level with last year')), 18), ORG()], D.conversion_d(), 50))
# 12 prospects --------------------------------------------------------------
PR = lambda c: R('prospects', c)
tables.append(T('prospects', 'Prospects', 'Major-gift prospects with stage and next step',
    'One row per prospect: capacity, stage, ask amount, next step with date, owner and last contact; probability, weighted value, days overdue and a verdict fill in. Probabilities are your estimate.', [
    C('prospect_id', 'Prospect ID', 'text', 10, required=True), C('donor_id', 'Donor ID', 'text', 10), C('donor', 'Donor', 'text', 24), C('capacity', 'Capacity', 'money', 11), LST('capband', 'Capacity band', 'capband', 15),
    LST('stage', 'Stage', 'pstage', 12), C('ask_amount', 'Ask amount', 'money', 11), C('next_step', 'Next step', 'text', 28), C('next_step_date', 'Next step date', 'date', 11), LST('owner', 'Owner', 'owner', 16),
    C('last_contact', 'Last contact', 'date', 11), C('expected_close', 'Expected close', 'date', 11),
    CA('probability', 'Probability, your estimate', 'pct', 'IF({col:stage}=%s,{set:prob_identified},IF({col:stage}=%s,{set:prob_cultivation},IF({col:stage}=%s,{set:prob_ask},IF({col:stage}=%s,{set:prob_committed},1))))' % (IDENT, CULT, ASKMADE, COMMITTED), 11),
    CA('weighted_value', 'Weighted value', 'money', '{col:ask_amount}*{col:probability}', 11),
    CA('overdue_days', 'Days overdue', 'int', 'IF(AND({col:stage}<>%s,{col:next_step_date}>0,{col:next_step_date}<{today}),{today}-{col:next_step_date},0)' % CLOSED, 9),
    CA('days_quiet', 'Days since contact', 'int', 'IF({col:last_contact}>0,{today}-{col:last_contact},0)', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:stage}=%s,%s,IF({col:days_quiet}>90,%s,IF(OR({col:stage}=%s,{col:stage}=%s),%s,%s)))' % (CLOSED, va('Closed'), va('Pause'), ASKMADE, COMMITTED, va('Ask'), va('Cultivate')), 10),
    CA('pnum', 'Prospect number', 'int', 'VALUE(RIGHT({col:prospect_id},3))', 8),
    CA('ask_score', 'Ask list score', 'num', 'IF(AND(OR({col:stage}=%s,{col:stage}=%s),{col:next_step_date}<={today}+30),ROUND({col:weighted_value},0)+(1000-{col:pnum})/10000,"")' % (CULT, ASKMADE), 10),
    CA('chase_score', 'Overdue chase score value', 'num', 'IF({col:overdue_days}>0,{col:overdue_days}*100000+ROUND({col:weighted_value},0)+(1000-{col:pnum})/10000,"")', 14),
    CA('next_key', 'Next step sort key value', 'num', 'IF({col:stage}<>%s,{col:next_step_date}*1000+{col:pnum},"")' % CLOSED, 14),
    CA('goal', 'Major-gift goal', 'money', '{set:major_goal}', 11),
    CA('pipeline_value', 'Pipeline weighted value', 'money', 'SUMIFS(%s,%s,"<>"&%s)' % (PR('weighted_value'), PR('stage'), CLOSED), 12),
    CA('phone', 'Donor phone', 'text', LKT('donors.phone', 'donors.donor_id', 'donor_id'), 18), PH('board_phone', 'Board member phone', D.BOARD_CHAIR['phone']), ORG()], D.prospects_d(), 100,
    [A('overdue_days', '> 0', 'warn'), A('stage', '= ' + CLOSED, 'good')]))
# 13 pipeline (3 columns) ---------------------------------------------------
tables.append(T('pipeline', 'Pipeline by Stage', 'Prospects and weighted value by stage',
    'One row per stage: prospects and their weighted value (ask times your stage estimate), from the Prospects sheet.', [
    LST('stage', 'Stage', 'pstage', 14, required=True), CA('prospects', 'Prospects', 'int', 'COUNTIFS(%s,{col:stage})' % PR('stage'), 10), CA('weighted', 'Weighted value', 'money', 'SUMIFS(%s,%s,{col:stage})' % (PR('weighted_value'), PR('stage')), 12)],
    D.pipeline_d(), 50))
# 14 next steps -------------------------------------------------------------
def PP(col, blank='""'): return 'IF({col:pos}="",%s,INDEX({range:prospects.%s},{col:pos}))' % (blank, col)
tables.append(T('next_steps', 'Next Steps Due', 'Open prospects by next step date',
    'One row per rank: the open prospects whose next step comes first, with days overdue, value and a verdict (Act today, Reschedule or On schedule).', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('pos', 'Position', 'int', 'IFERROR(MATCH(SMALL({range:prospects.next_key},{col:rank}),{range:prospects.next_key},0),"")', 8),
    CA('prospect_id', 'Prospect ID', 'text', PP('prospect_id'), 10), CA('donor', 'Donor', 'text', PP('donor'), 24), CA('next_step', 'Next step', 'text', PP('next_step'), 28), CA('next_step_date', 'Next step date', 'date', PP('next_step_date'), 11),
    CA('days_overdue', 'Days overdue', 'int', PP('overdue_days'), 9), CA('ask_amount', 'Ask amount', 'money', PP('ask_amount'), 11), CA('weighted', 'Weighted value', 'money', PP('weighted_value'), 11),
    CA('owner', 'Owner', 'text', PP('owner'), 16),
    CA('verdict', 'Verdict', 'text', 'IF({col:pos}="","",IF({col:days_overdue}>14,%s,IF({col:days_overdue}>0,%s,IF({col:next_step_date}={today},%s,%s))))' % (va('Reschedule'), va('Act today'), va('Act today'), va('On schedule')), 12),
    CA('overdue_n', 'Next steps overdue', 'int', 'COUNTIFS(%s,">0")' % PR('overdue_days'), 9), CA('oldest', 'Oldest overdue, days', 'int', 'MAX(%s)' % PR('overdue_days'), 9),
    CA('ask_n', 'Ask list prospects', 'int', 'COUNT(%s)' % PR('ask_score'), 9), CA('ask_value', 'Ask list weighted value', 'money', 'SUMIFS(%s,%s,">0")' % (PR('weighted_value'), PR('ask_score')), 12),
    CA('phone', 'Donor phone', 'text', 'IF({col:pos}="","",INDEX({range:prospects.phone},{col:pos}))', 18), PH('dm_phone', 'Development manager phone', D.DM_PHONE), ORG()], D.ranks_d(25), 60,
    [A('verdict', '= ' + va('Reschedule'), 'bad'), A('verdict', '= ' + va('Act today'), 'warn')]))
# 15 appeal results ---------------------------------------------------------
AC = lambda c: R('appeal_costs', c)
tables.append(T('appeal_results', 'Appeal Results', 'Results and cost per dollar by appeal',
    "One row per appeal: this year's gifts, donors, amount, cost and cost to raise one dollar against the setting and your own last year, with a verdict (Keep, Fix or Stop).", [
    LST('appeal', 'Appeal', 'appeal', 24, required=True),
    CA('gifts_n', 'Gifts', 'int', 'COUNTIFS({range:gifts.appeal},{col:appeal})', 8), CA('donors', 'Donors', 'int', 'SUMIFS({range:gifts.new_in_appeal},{range:gifts.appeal},{col:appeal})', 8),
    CA('amount', 'Amount', 'money', 'SUMIFS({range:gifts.amount},{range:gifts.appeal},{col:appeal})', 12), CA('avg_gift', 'Average gift', 'money', 'IF({col:gifts_n}>0,{col:amount}/{col:gifts_n},0)', 10),
    CA('cost', 'Cost', 'money', 'SUMIFS(%s,%s,{col:appeal},%s,%s)' % (AC('cost'), AC('appeal'), AC('year'), YEARN), 11),
    CA('cost_per_dollar', 'Cost per dollar', 'num', 'IF({col:amount}>0,{col:cost}/{col:amount},0)', 9),
    CA('last_cpd', 'Own cost per dollar last year', 'num', 'IFERROR(SUMIFS(%s,%s,{col:appeal},%s,%s-1)/SUMIFS(%s,%s,{col:appeal},%s,%s-1),0)' % (AC('cost'), AC('appeal'), AC('year'), YEARN, AC('raised'), AC('appeal'), AC('year'), YEARN), 11),
    CA('verdict', 'Verdict', 'text', 'IF({col:cost_per_dollar}<={set:cost_per_dollar},%s,IF(AND({col:cost_per_dollar}>2*{set:cost_per_dollar},{col:cost_per_dollar}>{col:last_cpd}),%s,%s))' % (va('Keep'), va('Stop'), va('Fix')), 9),
    CA('fix_n', 'Appeals to fix or stop', 'int', 'COUNTIFS({range:appeal_results.verdict},%s)+COUNTIFS({range:appeal_results.verdict},%s)' % (va('Fix'), va('Stop')), 9),
    PH('board_phone', 'Board member phone', D.BOARD_CHAIR['phone']), PH('committee_phone', 'Fundraising committee phone', D.FR_MEMBER['phone']), ORG()], D.results_d(), 50,
    [A('verdict', '= ' + va('Stop'), 'bad'), A('verdict', '= ' + va('Fix'), 'warn'), A('verdict', '= ' + va('Keep'), 'good')]))
# 16 source results (3 columns) ---------------------------------------------
tables.append(T('source_results', 'Source Results', 'Cost per dollar and retention by channel',
    "One row per channel: cost to raise one dollar this year and the share of last year's donors it brought who gave again.", [
    LST('channel', 'Channel', 'channel', 16, required=True),
    CA('cost_per_dollar', 'Cost per dollar', 'num', 'IFERROR(SUMIFS(%s,%s,{col:channel},%s,%s)/SUMIFS({range:gifts.amount},{range:gifts.channel},{col:channel}),0)' % (AC('cost'), AC('channel'), AC('year'), YEARN), 11),
    CA('retention', 'Retention of donors it brought', 'pct', 'IFERROR(COUNTIFS(%s,{col:channel},%s,">0",%s,">0")/COUNTIFS(%s,{col:channel},%s,">0"),0)' % (G('source'), G('y1'), G('y0'), G('source'), G('y1')), 12)],
    D.source_d(), 50))
# 17 appeal costs -----------------------------------------------------------
tables.append(T('appeal_costs', 'Appeal Costs', 'Cost of each appeal, this year and last year',
    'One row per appeal and year: what it cost, the channel it ran through, pieces sent and, for last year, what it raised. Keep one row per cost line.', [
    C('appeal_id', 'Cost ID', 'text', 9, required=True), LST('appeal', 'Appeal', 'appeal', 24), C('year', 'Year', 'int', 7), C('cost', 'Cost', 'money', 10), LST('channel', 'Channel', 'channel', 14), C('pieces', 'Pieces sent', 'int', 9),
    C('raised', 'Raised, closed years', 'money', 12), C('cost_note', 'What it covers', 'text', 30), C('review_on', 'Review date', 'date', 11),
    CA('cost_piece', 'Cost per piece', 'money', 'IF({col:pieces}>0,{col:cost}/{col:pieces},0)', 10), PH('bookkeeper_phone', 'Bookkeeper phone', D.BK_PHONE), PH('printer_phone', 'Printer phone', D.PR_PHONE), ORG()],
    D.appeal_costs_d(), 60))
# 18 top donors -------------------------------------------------------------
tables.append(T('top_donors', 'Top Donors', 'Top donors this year with share of the year',
    "One row per rank: the biggest donors this year, their share of all giving and the running share; what their loss would do to free money fills in. This year is to date.", [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('pos', 'Position', 'int', 'IFERROR(MATCH(LARGE({range:giving.top_score},{col:rank}),{range:giving.top_score},0),"")', 8),
    CA('donor_id', 'Donor ID', 'text', GP('donor_id'), 10), CA('donor', 'Donor', 'text', GP('donor'), 24), CA('amount', 'Given this year', 'money', GP('y0'), 11), CA('last_year', 'Given last year', 'money', GP('y1'), 11),
    CA('years_given', 'Years given', 'int', GP('years_given'), 8), CA('share', 'Share of the year', 'pct', 'IF({col:pos}="","",{col:amount}/SUM(%s))' % G('y0'), 9),
    CA('cum_share', 'Running share', 'pct', 'IF({col:pos}="","",SUMIFS({range:top_donors.amount},{range:top_donors.rank},"<="&{col:rank})/SUM(%s))' % G('y0'), 9),
    CA('yearly', 'Giving at risk', 'money', 'IF({col:pos}="","",MAX({col:amount},{col:last_year}))', 11),
    CA('months_if_left', 'Months of reserve if they left', 'num', 'IF({col:pos}="","",({set:free_money}-{col:yearly})/{set:monthly_expense})', 11),
    CA('top5_share', 'Share from the top 5', 'pct', 'SUMIFS({range:top_donors.amount},{range:top_donors.rank},"<=5")/SUM(%s)' % G('y0'), 9),
    DPH(), PH('ed_phone', 'Executive director phone', D.ED_PHONE), ORG()], D.ranks_d(30), 60))
# 19 scenarios --------------------------------------------------------------
LAPMAJ = 'SUMIFS(%s,%s,%s,%s,">="&{set:major_min})' % (G('y1'), G('state'), S_LAP, G('y1'))
tables.append(T('scenarios', 'Concentration Scenarios', 'What losing large donors does to free money',
    'One row per scenario: top donors who leave, the share lost and lapsing major donors who do not return; income lost, months of reserve left and the gap fill in.', [
    C('scenario', 'Scenario', 'text', 44, required=True), C('top_n', 'Top donors affected', 'int', 9), C('lost_pct', 'Share of their giving lost', 'pct', 10), C('lapsed_pct', 'Share of lapsing major donors lost', 'pct', 11), C('review_on', 'Review date', 'date', 11),
    CA('income_lost', 'Income lost', 'money', 'SUMIFS({range:top_donors.amount},{range:top_donors.rank},"<="&{col:top_n})*{col:lost_pct}+%s*{col:lapsed_pct}' % LAPMAJ, 12),
    CA('share_lost', 'Share of this year', 'pct', '{col:income_lost}/SUM(%s)' % G('y0'), 9),
    CA('months_left', 'Months of reserve left', 'num', '({set:free_money}-{col:income_lost})/{set:monthly_expense}', 10),
    CA('gap', 'Gap to your reserve months', 'money', 'MAX(0,{set:reserve_months}*{set:monthly_expense}-({set:free_money}-{col:income_lost}))', 12),
    CA('verdict', 'Verdict', 'text', 'IF({col:gap}>0,%s,%s)' % (va('Gap'), va('Covered')), 9), ORG()], D.scenarios_d(), 50,
    [A('verdict', '= ' + va('Gap'), 'bad'), A('verdict', '= ' + va('Covered'), 'good')]))
# 20 three-year story -------------------------------------------------------
def YV(f):
    return 'IF({col:year}=%s,%s,IF({col:year}=%s,%s,%s))' % (THIS, f(G('y0'), G('y1')), LASTY, f(G('y1'), G('y2')), f(G('y2'), G('y3')))
def TOP5(c): return '+'.join('SUMPRODUCT(LARGE((((%s={col:group})+({col:group}=%s))>0)*%s,%d))' % (G('type'), ALL, c, k) for k in range(1, 6))
TYC = '%s,{col:crit}' % G('type')
tables.append(T('three_year', 'Three-Year Story', 'Three years of donors and money, by donor group',
    'One row per year and donor group: donors, money, average gift, lapsed donors and the share from the top 5, with a plain sentence about the trend. This year is to date.', [
    C('row_id', 'Row', 'text', 8, required=True), LST('year', 'Year', 'yr', 14), LST('group', 'Donor group', 'dgroup', 18), C('gifts', 'Gifts', 'int', 8), C('review_on', 'Review date', 'date', 11),
    CA('crit', 'Group filter', 'text', 'IF({col:group}=%s,"*",{col:group})' % ALL, 10),
    CA('donors', 'Donors', 'int', YV(lambda c, p: 'COUNTIFS(%s,%s,">0")' % (TYC, c)), 9), CA('amount', 'Amount', 'money', YV(lambda c, p: 'SUMIFS(%s,%s)' % (c, TYC)), 12),
    CA('donors_prev', 'Donors the year before', 'int', YV(lambda c, p: 'COUNTIFS(%s,%s,">0")' % (TYC, p)), 10), CA('amount_prev', 'Amount the year before', 'money', YV(lambda c, p: 'SUMIFS(%s,%s)' % (p, TYC)), 12),
    CA('retained', 'Retained donors', 'int', YV(lambda c, p: 'COUNTIFS(%s,%s,">0",%s,">0")' % (TYC, c, p)), 9),
    CA('retention', 'Retention', 'pct', 'IF({col:donors_prev}>0,{col:retained}/{col:donors_prev},0)', 10),
    CA('lapsed', 'Lapsed donors', 'int', YV(lambda c, p: 'COUNTIFS(%s,%s,">0")-COUNTIFS(%s,%s,">0",%s,">0")' % (TYC, p, TYC, p, c)), 9),
    CA('avg_gift', 'Average gift', 'money', 'IF({col:gifts}>0,{col:amount}/{col:gifts},0)', 10),
    CA('top_share', 'Share from the top 5', 'pct', 'IF({col:amount}>0,(%s)/{col:amount},0)' % YV(lambda c, p: TOP5(c)), 10),
    CA('d_idx', 'Donors step', 'int', 'IF({col:donors}>{col:donors_prev}*1.02,1,IF({col:donors}<{col:donors_prev}*0.98,3,2))', 8),
    CA('m_idx', 'Money step', 'int', 'IF({col:amount}>{col:amount_prev}*1.02,1,IF({col:amount}<{col:amount_prev}*0.98,3,2))', 8),
    CA('d_dir', 'Donors trend', 'text', 'CHOOSE({col:d_idx},%s,%s,%s)' % (vb('Donors up'), vb('Donors flat'), vb('Donors down')), 12),
    CA('m_dir', 'Money trend', 'text', 'CHOOSE({col:m_idx},%s,%s,%s)' % (vb('Money up'), vb('Money flat'), vb('Money down')), 12),
    CA('story', 'Story', 'text', 'CHOOSE(({col:d_idx}-1)*3+{col:m_idx},%s)' % ','.join(vc(s) for s in STORY), 36), ORG()], D.three_year_d(), 60))
assert len(tables) == 20, len(tables)
