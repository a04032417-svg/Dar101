"""Wedding suite part 2: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp2_lists import *
import wp2_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def LIT(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def R(t, c_): return '{range:%s.%s}' % (t, c_)
def CPL(): return CA('couple', 'Couple', 'text', '{set:couple}', 20)


YES = '{list:yesno.yes}'; NOB = '{list:yesno.no}'
RY = tok('rsvp', 'Yes'); RN = tok('rsvp', 'No'); RP = tok('rsvp', 'Pending')
UP = tok('cstat', 'Up to date'); CHKIN = tok('cstat', 'Check in'); LOST = tok('cstat', 'Lost touch')
LA = tok('listab', 'A list'); LB = tok('listab', 'B list')
LOCAL = tok('lodging', 'Local'); OWN = tok('lodging', 'Own arrangement')
S1 = tok('side', 'Partner 1'); S2 = tok('side', 'Partner 2'); SS = tok('side', 'Shared')
ADULT = tok('age', 'Adult'); CHILD = tok('age', 'Child')
MEAT = tok('meal', 'Meat'); FISH = tok('meal', 'Fish'); VEG = tok('meal', 'Vegetarian'); VEGAN = tok('meal', 'Vegan'); KIDM = tok('meal', "Children's meal")
FAM = tok('tier', 'Family'); CLOSE = tok('tier', 'Close friends'); FRI = tok('tier', 'Friends')
HR = lambda c_: R('households', c_)
GR_ = lambda c_: R('guests', c_)
SZ = HR('size'); TOT = 'SUM(%s)' % SZ
YESG = 'SUMIFS(%s,%s,%s)' % (SZ, HR('rsvp'), RY)
NOG = 'SUMIFS(%s,%s,%s)' % (SZ, HR('rsvp'), RN)
PENDG = 'SUMIFS(%s,%s,%s)' % (SZ, HR('rsvp'), RP)
LIKELY = 'SUM(%s)' % HR('expected')
LOWT = 'SUM(%s)' % R('forecast', 'low'); HIGHT = 'SUM(%s)' % R('forecast', 'high')
SEATED = '({set:venue_capacity}-{set:seats_others})'
SHORT = v('A table to be set')

settings = [
    S('couple', 'Your names as the couple', 'text', COUPLE),
    S('wedding_day', 'Wedding day', 'date', iso(WEDDING_DAY)),
    S('venue_capacity', 'Seated capacity of the venue, from the venue contract', 'int', VENUE_CAPACITY),
    S('seats_others', 'Seats for the couple and helpers, your count', 'int', 6),
    S('tight_pct', 'Share of the seats that counts as tight, your own rule', 'pct', 0.95),
    S('expected_yes_rate', 'Expected yes rate of pending replies, typical, edit', 'pct', EXPECTED_YES_RATE),
    S('travel_decline_extra', 'Extra decline rate for guests who travel, typical, edit', 'pct', TRAVEL_DECLINE_EXTRA),
    S('forecast_spread', 'Low and high forecast move the yes rate by, your own number', 'pct', 0.15),
    S('rsvp_deadline', 'Reply-by date on your invitation', 'date', iso(RSVP_DEADLINE)),
    S('headcount_date', 'Date the final headcount is due, from the caterer contract', 'date', iso(HEADCOUNT_DATE)),
    S('guarantee_guests', 'Minimum guarantee, guests you pay for, from your contract', 'int', 118),
    S('food_per_guest', 'Food and drink price per guest, your caterer quote', 'money', 70),
    S('invite_lead_weeks', 'Weeks before the wedding for the invitation, typical, edit', 'int', INVITE_LEAD_WEEKS),
    S('paper_spares_pct', 'Spare share of printed pieces, typical, edit', 'pct', 0.10),
    S('agreed_p1', 'Agreed share of guests, partner 1 side, your own split', 'pct', 0.45),
    S('agreed_p2', 'Agreed share of guests, partner 2 side, your own split', 'pct', 0.40),
    S('room_rate', 'Room rate for one night, from the hotel contract', 'money', 139),
    S('room_cutoff', 'Room block cut-off date, from the hotel contract', 'date', iso(ROOM_CUTOFF)),
    S('attrition_pct', 'Share of the room block you must fill, hotel contract', 'pct', 0.80),
    S('chase_gap_days', 'Days to wait before chasing a household again, your own rule', 'int', 5),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 households ---------------------------------------------------------------
HOUSE_REASON = ('IF({col:rsvp}=%s,%s,IF({col:meals_missing}>0,%s,IF({col:open_plus_ones}>0,%s,IF({col:contact_status}<>%s,%s,%s))))') % (
    RP, v('Silent'), v('Meal missing'), v('Plus-one open'), UP, v('Contact check'), v('Nothing to chase'))
HOUSE_SCORE = ('(IF({col:rsvp}=%s,3000000+{col:stake}*10000+MIN({col:silent_days},99)*100+IF({col:contact_status}=%s,30,IF({col:contact_status}=%s,20,0)),'
               'IF({col:meals_missing}>0,2000000+{col:meals_missing}*10000,IF({col:open_plus_ones}>0,1000000+{col:open_plus_ones}*10000,IF({col:contact_status}<>%s,500000,0))))+(1000-{col:idnum})/1000)') % (
    RP, LOST, CHKIN, UP)
TIERW = 'IF({col:tier}=%s,4,IF({col:tier}=%s,3,IF({col:tier}=%s,2,1)))' % (FAM, CLOSE, FRI)
TBL = 'IFERROR(IF(INDEX({range:guests.table},MATCH({col:household_id},{range:guests.household_id},0))="",%s,INDEX({range:guests.table},MATCH({col:household_id},{range:guests.household_id},0))),%s)' % (SHORT, SHORT)
tables.append(T('households', 'Households', 'Households', 'One row per household (one invitation, several people): side, tier, list, region, RSVP and lodging; silent days, expected guests, chase rank and the message links fill in.', [
    C('household_id', 'Household ID', 'text', 10, required=True), C('household', 'Household', 'text', 24), C('contact', 'Contact', 'text', 20), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    LST('side', 'Side', 'side', 12), LST('tier', 'Tier', 'tier', 14), LST('list_ab', 'List', 'listab', 9), LST('region', 'Region', 'region', 14), C('size', 'Guests', 'int', 8), LST('rsvp', 'RSVP', 'rsvp', 9),
    C('save_the_date', 'Save the date', 'date', 12), C('invite_sent', 'Invite sent', 'date', 12), LST('contact_status', 'Contact status', 'cstat', 13), C('last_chase', 'Last chase', 'date', 12),
    LST('chase_channel', 'Chase channel', 'channel', 12), LST('lodging', 'Lodging', 'lodging', 16), C('arrival', 'Arrival', 'date', 12), C('open_plus_ones', 'Open plus-ones', 'int', 10), C('room_booked', 'Room booked', 'bool', 9),
    CA('idnum', 'Order number', 'int', 'IFERROR(VALUE(MID({col:household_id},4,5)),0)', 8),
    CA('silent_days', 'Silent days', 'int', 'IF(AND({col:rsvp}=%s,{col:invite_sent}<>""),MAX(0,{today}-{col:invite_sent}),0)' % RP, 8),
    CA('stake', 'Guests at stake', 'int', 'IF({col:rsvp}=%s,{col:size},0)' % RP, 9),
    CA('meals_missing', 'Meals missing', 'int', 'COUNTIFS({range:guests.household_id},{col:household_id},{range:guests.rsvp},%s,{range:guests.meal},"")' % RY, 9),
    CA('yes_rate', 'Yes rate', 'pct', 'IF(SUMIFS({range:yesrates.rate},{range:yesrates.region},{col:region},{range:yesrates.list_ab},{col:list_ab})=0,{set:expected_yes_rate},SUMIFS({range:yesrates.rate},{range:yesrates.region},{col:region},{range:yesrates.list_ab},{col:list_ab}))', 8),
    CA('expected', 'Expected guests', 'num', 'IF({col:rsvp}=%s,{col:size},IF({col:rsvp}=%s,0,{col:size}*{col:yes_rate}))' % (RY, RN), 10),
    CA('low_guests', 'Low guests', 'num', 'IF({col:rsvp}=%s,{col:size},IF({col:rsvp}=%s,0,{col:size}*MAX(0,{col:yes_rate}-{set:forecast_spread})))' % (RY, RN), 9),
    CA('high_guests', 'High guests', 'num', 'IF({col:rsvp}=%s,{col:size},IF({col:rsvp}=%s,0,{col:size}*MIN(1,{col:yes_rate}+{set:forecast_spread})))' % (RY, RN), 9),
    CA('chase_reason', 'Chase reason', 'text', HOUSE_REASON, 16), CA('chase_score', 'Chase ranking score', 'num', HOUSE_SCORE, 12),
    CA('chase_rank', 'Chase rank', 'int', 'COUNTIFS({range:households.chase_score},">"&{col:chase_score})+1', 8),
    CA('stay_seq', 'Stay order', 'int', 'IF({col:lodging}=%s,"",COUNTIFS({range:households.lodging},"<>"&%s,{range:households.idnum},"<="&{col:idnum}))' % (LOCAL, LOCAL), 8),
    CA('bq_score', 'B list score', 'num', 'IF({col:list_ab}=%s,%s*100+(9-MIN({col:size},9))*10+(1000-{col:idnum})/1000,0)' % (LB, TIERW), 10),
    CA('bq_rank', 'B list rank', 'int', 'IF({col:list_ab}=%s,COUNTIFS({range:households.bq_score},">"&{col:bq_score})+1,"")' % LB, 8),
    CA('table', 'Table', 'text', TBL, 14), CA('wedding_day', 'Wedding day', 'date', '{set:wedding_day}', 12), CA('rsvp_deadline', 'Reply by', 'date', '{set:rsvp_deadline}', 12),
    CA('room_cutoff', 'Room cut-off', 'date', '{set:room_cutoff}', 12), CPL()],
    D.hh_d(), 300, [A('rsvp', '= ' + RP, 'warn'), A('contact_status', '= ' + LOST, 'bad'), A('contact_status', '= ' + CHKIN, 'warn'), A('silent_days', '> 30', 'warn')]))

# 2 guests -------------------------------------------------------------------
tables.append(T('guests', 'Guests', 'Guests', 'One row per guest: household, side, tier, list, age group, RSVP, meal and a short dietary note. Names only, no addresses and no health details.', [
    C('guest_id', 'Guest ID', 'text', 9, required=True), C('guest', 'Guest', 'text', 22), REF('household_id', 'Household ID', 'households.household_id', 10), C('household', 'Household', 'text', 24),
    LST('side', 'Side', 'side', 12), LST('tier', 'Tier', 'tier', 14), LST('list_ab', 'List', 'listab', 9), LST('age_group', 'Age group', 'age', 9), C('plus_one', 'Plus-one', 'bool', 9),
    C('invite_sent', 'Invite sent', 'date', 12), LST('rsvp', 'RSVP', 'rsvp', 9), C('rsvp_date', 'RSVP date', 'date', 12), LST('meal', 'Meal', 'meal', 15), LST('dietary', 'Dietary note', 'dietary', 14), LST('table', 'Table', 'table', 9),
    CA('idnum', 'Order number', 'int', 'IFERROR(VALUE(MID({col:guest_id},4,6)),0)', 8),
    CA('diet_seq', 'Note order', 'int', 'IF({col:dietary}<>"",COUNTIFS({range:guests.dietary},"<>",{range:guests.idnum},"<="&{col:idnum}),"")', 8),
    CA('replied', 'Replied', 'int', 'IF({col:rsvp}=%s,0,1)' % RP, 8),
    CA('meal_done', 'Meal chosen', 'int', 'IF(AND({col:rsvp}=%s,{col:meal}<>""),1,0)' % RY, 8)],
    D.guests_d(), 400, [A('rsvp', '= ' + RP, 'warn'), A('rsvp', '= ' + RY, 'good')]))

# 3 side and tier balance -------------------------------------------------------
tables.append(T('sidebal', 'Side and Tier Balance', 'Side and Tier Balance', 'One row per side and tier: households, guests and share against the split you agreed; the heavy side and the parent message fill in.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('side', 'Side', 'side', 12), LST('tier', 'Tier', 'tier', 14),
    CA('households', 'Households', 'int', 'COUNTIFS(%s,{col:side},%s,{col:tier},%s,"<>")' % (HR('side'), HR('tier'), HR('household_id')), 10),
    CA('guests', 'Guests', 'int', 'SUMIFS(%s,%s,{col:side},%s,{col:tier})' % (SZ, HR('side'), HR('tier')), 9),
    CA('share', 'Share of all guests', 'pct', 'IFERROR({col:guests}/%s,0)' % TOT, 10),
    CA('side_guests', 'Side guests', 'int', 'SUMIFS(%s,%s,{col:side})' % (SZ, HR('side')), 9),
    CA('agreed', 'Agreed share', 'pct', 'IF({col:side}=%s,{set:agreed_p1},IF({col:side}=%s,{set:agreed_p2},1-{set:agreed_p1}-{set:agreed_p2}))' % (S1, S2), 9),
    CA('agreed_guests', 'Agreed guests', 'int', 'ROUND({col:agreed}*%s,0)' % TOT, 9), CA('side_diff', 'Over or under the split', 'int', '{col:side_guests}-{col:agreed_guests}', 11),
    CA('within', 'Guests within the split', 'num', '{col:guests}*MIN(1,{col:agreed_guests}/MAX(1,{col:side_guests}))', 11),
    CA('flag', 'Side check', 'text', 'IF({col:side_diff}>ROUND(0.02*%s,0),%s,IF({col:side_diff}<-ROUND(0.02*%s,0),%s,%s))' % (TOT, v('Heavy'), TOT, v('Light'), v('Balanced')), 10),
    CA('hh_total', 'All households', 'int', 'COUNTIFS(%s,"<>")' % HR('household_id'), 10), CA('guests_total', 'All guests', 'int', TOT, 9),
    CA('agreed_text', 'Agreed share text', 'text', 'ROUND({col:agreed}*100,0)&"%"', 9),
    CA('parent_phone', 'Parent phone', 'text', 'IF({col:side}=%s,"%s",IF({col:side}=%s,"%s","%s"))' % (S1, D.PAR1_PHONE, S2, D.PAR2_PHONE, D.P2_PHONE), 18), CPL()],
    D.sidebal_d(), 50, [A('flag', '= ' + v('Heavy'), 'warn')]))

# 4 expected yes rates ----------------------------------------------------------
tables.append(T('yesrates', 'Expected Yes Rates', 'Expected Yes Rates', 'The share of pending households you expect to say yes by region and list. A typical starting value, not a fact about your area: edit it.', [
    LST('region', 'Region', 'region', 16, required=True), LST('list_ab', 'List', 'listab', 10), C('rate', 'Expected yes rate', 'pct', 12)], D.rates_d(), 50))

# 5 forecast by tier and region --------------------------------------------------
tables.append(T('forecast', 'Forecast by Tier', 'Forecast by Tier and Region', 'One row per tier and region: invited, yes and pending guests, the yes rate and the low, expected and high headcount; the totals and the partner and caterer links fill in.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('tier', 'Tier', 'tier', 14), LST('region', 'Region', 'region', 14),
    CA('invited', 'Invited', 'int', 'SUMIFS(%s,%s,{col:tier},%s,{col:region})' % (SZ, HR('tier'), HR('region')), 9),
    CA('yes', 'Yes', 'int', 'SUMIFS(%s,%s,{col:tier},%s,{col:region},%s,%s)' % (SZ, HR('tier'), HR('region'), HR('rsvp'), RY), 8),
    CA('pending', 'Pending', 'int', 'SUMIFS(%s,%s,{col:tier},%s,{col:region},%s,%s)' % (SZ, HR('tier'), HR('region'), HR('rsvp'), RP), 9),
    CA('expected', 'Expected', 'num', 'SUMIFS(%s,%s,{col:tier},%s,{col:region})' % (HR('expected'), HR('tier'), HR('region')), 9),
    CA('rate', 'Yes rate of pending', 'pct', 'IFERROR(({col:expected}-{col:yes})/{col:pending},0)', 9),
    CA('low', 'Low', 'num', 'SUMIFS(%s,%s,{col:tier},%s,{col:region})' % (HR('low_guests'), HR('tier'), HR('region')), 9),
    CA('high', 'High', 'num', 'SUMIFS(%s,%s,{col:tier},%s,{col:region})' % (HR('high_guests'), HR('tier'), HR('region')), 9),
    CA('low_total', 'Low total', 'int', 'ROUND(%s,0)' % LOWT, 9), CA('likely_total', 'Expected total', 'int', 'ROUND(%s,0)' % LIKELY, 10), CA('high_total', 'High total', 'int', 'ROUND(%s,0)' % HIGHT, 9),
    CA('over', 'Seats over if all say yes', 'int', 'MAX(0,%s+{set:seats_others}-{set:venue_capacity})' % TOT, 11), CA('pending_total', 'Pending guests', 'int', PENDG, 9),
    CA('headcount_date', 'Headcount due', 'date', '{set:headcount_date}', 12), LIT('partner_phone', 'Partner phone', D.P2_PHONE), LIT('caterer_phone', 'Caterer phone', D.CATERER_PHONE),
    LIT('venue_phone', 'Venue phone', D.VENUE_PHONE), CPL()],
    D.forecast_d(), 50, [A('pending', '> 0', 'warn')]))

# 6 B list queue -------------------------------------------------------------------
tables.append(T('bqueue', 'B List Queue', 'B List Queue', 'The B list households in the order you invite them: tier first, smaller households first. Status and the seats each would use fill in from Households.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('household_id', 'Household ID', 'text', 'IFERROR(INDEX({range:households.household_id},MATCH({col:rank},{range:households.bq_rank},0)),"")', 10),
    CA('household', 'Household', 'text', LKT('households.household', 'households.household_id', 'household_id'), 24), CA('tier', 'Tier', 'text', LKT('households.tier', 'households.household_id', 'household_id'), 14),
    CA('size', 'Guests', 'int', LKN('households.size', 'households.household_id', 'household_id'), 8),
    CA('invite_date', 'Invite sent', 'date', LKD('households.invite_sent', 'households.household_id', 'household_id'), 12),
    CA('replied', 'Replied', 'text', 'IF(%s=%s,%s,%s)' % (LKT('households.rsvp', 'households.household_id', 'household_id'), RP, v('No'), v('Yes')), 9),
    CA('status', 'Status', 'text', 'IF({col:invite_date}="",%s,IF(%s=%s,%s,IF(%s=%s,%s,%s)))' % (v('Not yet invited'), LKT('households.rsvp', 'households.household_id', 'household_id'), RP, v('Waiting for a reply'),
                                                                                        LKT('households.rsvp', 'households.household_id', 'household_id'), RY, v('Said yes'), v('Said no')), 18),
    CA('seats', 'Seats it would use', 'int', 'IF({col:status}=%s,0,{col:size})' % v('Said no'), 10),
    CA('wait_rank', 'Rank if still to invite or reply', 'int', 'IF(OR({col:status}=%s,{col:status}=%s),{col:rank},"")' % (v('Not yet invited'), v('Waiting for a reply')), 12)],
    D.bq_d(), 60, [A('status', '= ' + v('Waiting for a reply'), 'warn'), A('status', '= ' + v('Said yes'), 'good'), A('status', '= ' + v('Not yet invited'), 'bad')]))

# 7 RSVP chase list -----------------------------------------------------------------
tables.append(T('chase', 'RSVP Chase List', 'RSVP Chase List', 'Households to chase in order: silent replies first by guests at stake, days silent and contact status, then meals, plus-ones and contact checks. Call order skips households you chased recently.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('household_id', 'Household ID', 'text', 'IFERROR(INDEX({range:households.household_id},MATCH({col:rank},{range:households.chase_rank},0)),"")', 10),
    CA('household', 'Household', 'text', LKT('households.household', 'households.household_id', 'household_id'), 24), CA('contact', 'Contact', 'text', LKT('households.contact', 'households.household_id', 'household_id'), 20),
    CA('phone', 'Phone', 'text', LKT('households.phone', 'households.household_id', 'household_id'), 18), CA('tier', 'Tier', 'text', LKT('households.tier', 'households.household_id', 'household_id'), 14),
    CA('reason', 'Chase reason', 'text', LKT('households.chase_reason', 'households.household_id', 'household_id'), 16), CA('guests', 'Guests', 'int', LKN('households.size', 'households.household_id', 'household_id'), 8),
    CA('stake', 'Guests at stake', 'int', LKN('households.stake', 'households.household_id', 'household_id'), 9), CA('silent_days', 'Silent days', 'int', LKN('households.silent_days', 'households.household_id', 'household_id'), 8),
    CA('status', 'Contact status', 'text', LKT('households.contact_status', 'households.household_id', 'household_id'), 13), CA('last_chase', 'Last chase', 'date', LKD('households.last_chase', 'households.household_id', 'household_id'), 12),
    CA('since_chase', 'Days since chase', 'int', 'IF({col:last_chase}="","",{today}-{col:last_chase})', 9),
    CA('callable', 'Call today', 'int', 'IF(AND({col:reason}=%s,OR({col:last_chase}="",{col:since_chase}>={set:chase_gap_days})),1,0)' % v('Silent'), 8),
    CA('call_order', 'Call order', 'int', 'IF({col:callable}=1,SUMIFS({range:chase.callable},{range:chase.rank},"<="&{col:rank}),"")', 8),
    CA('pending_hh', 'Households silent', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (HR('rsvp'), RP, HR('household_id')), 9), CA('pending_guests', 'Guests silent', 'int', PENDG, 9),
    CA('rsvp_deadline', 'Reply by', 'date', '{set:rsvp_deadline}', 12), LIT('parent1_phone', 'Parent of partner 1 phone', D.PAR1_PHONE), LIT('partner_phone', 'Partner phone', D.P2_PHONE),
    LIT('lead_phone', 'Wedding party lead phone', D.LEAD1_PHONE), CPL()],
    D.chase_d(), 60, [A('reason', '= ' + v('Silent'), 'bad'), A('reason', '= ' + v('Meal missing'), 'warn'), A('since_chase', '< 6', 'good')]))

# 8 replies by week -----------------------------------------------------------------------
RD = GR_('rsvp_date')
def WIN(extra=''): return 'COUNTIFS(%s,">="&{col:week_start},%s,"<"&({col:week_start}+7)%s)' % (RD, RD, extra)
def LISTRSVP(lst, rs): return 'SUMIFS(%s,%s,%s,%s,%s)' % (SZ, HR('list_ab'), lst, HR('rsvp'), rs)
tables.append(T('rweek', 'Replies by Week', 'RSVP Replies by Week', 'One row per week from the first invitation: guests who replied, yes and no, and the share of all guests who have replied by the end of the week.', [
    LST('week', 'Week', 'week', 10, required=True), C('week_start', 'Week start', 'date', 12),
    CA('replies', 'Replies', 'int', WIN(), 9), CA('yes', 'Yes', 'int', WIN(',%s,%s' % (GR_('rsvp'), RY)), 8), CA('no', 'No', 'int', WIN(',%s,%s' % (GR_('rsvp'), RN)), 8),
    CA('cumulative', 'Share replied by week end', 'pct', 'IFERROR(COUNTIFS(%s,"<"&({col:week_start}+7))/%s,0)' % (RD, TOT), 12),
    CA('phase', 'Phase', 'text', 'IF({col:week_start}+7<={today},%s,IF({col:week_start}<={today},%s,%s))' % (v('Past'), v('This week'), v('Coming')), 10),
    CA('yes_a', 'Yes, A list', 'int', LISTRSVP(LA, RY), 9), CA('yes_b', 'Yes, B list', 'int', LISTRSVP(LB, RY), 9), CA('no_a', 'No, A list', 'int', LISTRSVP(LA, RN), 9), CA('no_b', 'No, B list', 'int', LISTRSVP(LB, RN), 9),
    CA('pend_a', 'Pending, A list', 'int', LISTRSVP(LA, RP), 9), CA('pend_b', 'Pending, B list', 'int', LISTRSVP(LB, RP), 9), CPL()],
    D.weeks_d(), 50, [A('phase', '= ' + v('This week'), 'warn')]))

# 9 meal counts ---------------------------------------------------------------------------
tables.append(T('meals', 'Meal Counts', 'Meal Counts', 'One row per meal choice: how many yes guests chose it and its share. Add the spare share on the caterer order tool.', [
    LST('meal', 'Meal', 'meal', 18, required=True), CA('count', 'Guests', 'int', 'COUNTIFS(%s,{col:meal},%s,%s)' % (GR_('meal'), GR_('rsvp'), RY), 9),
    CA('share', 'Share', 'pct', 'IFERROR({col:count}/SUM({range:meals.count}),0)', 9)], D.meals_d(), 50))

# 10 meals by table -------------------------------------------------------------------------
def MT(m): return 'COUNTIFS(%s,{col:table},%s,%s)' % (GR_('table'), GR_('meal'), m)
def MALL(m): return 'COUNTIFS(%s,%s,%s,%s)' % (GR_('meal'), m, GR_('rsvp'), RY)
tables.append(T('mtable', 'Meals by Table', 'Meals by Table', 'One row per table: guests, each meal choice, children and short dietary notes, ready for the caterer and the place cards. The totals feed the caterer messages.', [
    LST('table', 'Table', 'table', 9, required=True), CA('guests', 'Guests', 'int', 'COUNTIFS(%s,{col:table})' % GR_('table'), 8),
    CA('meat', 'Meat', 'int', MT(MEAT), 7), CA('fish', 'Fish', 'int', MT(FISH), 7), CA('vegetarian', 'Vegetarian', 'int', MT(VEG), 10), CA('vegan', 'Vegan', 'int', MT(VEGAN), 7), CA('children', 'Children', 'int', MT(KIDM), 9),
    CA('notes', 'Dietary notes', 'int', 'COUNTIFS(%s,{col:table},%s,"<>")' % (GR_('table'), GR_('dietary')), 9),
    CA('no_meal', 'Without a meal', 'int', 'COUNTIFS(%s,{col:table},%s,%s,%s,"")' % (GR_('table'), GR_('rsvp'), RY, GR_('meal')), 9),
    CA('all_meat', 'All meat', 'int', MALL(MEAT), 8), CA('all_fish', 'All fish', 'int', MALL(FISH), 8), CA('all_veg', 'All vegetarian', 'int', MALL(VEG), 9), CA('all_vegan', 'All vegan', 'int', MALL(VEGAN), 8),
    CA('likely', 'Expected guests', 'int', 'ROUND(%s,0)' % LIKELY, 9), CA('headcount_date', 'Headcount due', 'date', '{set:headcount_date}', 12), LIT('caterer_phone', 'Caterer phone', D.CATERER_PHONE), CPL()],
    D.mtable_d(), 50, [A('no_meal', '> 0', 'warn')]))

# 11 dietary notes -----------------------------------------------------------------------------
tables.append(T('diet', 'Dietary Notes', 'Dietary Notes', 'Every short dietary note in order: guest, note and table. Notes are a few words only, never a health detail or a reason.', [
    C('rank', 'Number', 'int', 8, required=True), CA('guest_id', 'Guest ID', 'text', 'IFERROR(INDEX({range:guests.guest_id},MATCH({col:rank},{range:guests.diet_seq},0)),"")', 9),
    CA('guest', 'Guest', 'text', LKT('guests.guest', 'guests.guest_id', 'guest_id'), 22), CA('note', 'Note', 'text', LKT('guests.dietary', 'guests.guest_id', 'guest_id'), 14),
    CA('table', 'Table', 'text', LKT('guests.table', 'guests.guest_id', 'guest_id'), 9), CA('household', 'Household', 'text', LKT('guests.household', 'guests.guest_id', 'guest_id'), 24),
    CA('rsvp', 'RSVP', 'text', LKT('guests.rsvp', 'guests.guest_id', 'guest_id'), 9)], D.diet_d(), 60))

# 12 policy options and 13 policy results -----------------------------------------------------------
tables.append(T('pol', 'Policy Options', 'Policy Options', 'Four ways to treat plus-ones and children: how many of each you would count. Edit the numbers for your own policy.', [
    LST('policy', 'Policy', 'policy', 34, required=True), C('plusones', 'Plus-ones counted', 'int', 12), C('children', 'Children counted', 'int', 12)], D.pol_d(), 50))
ADULTS_CORE = '(COUNTIFS(%s,%s,%s,"<>")-COUNTIFS(%s,%s,%s,"<>"))' % (GR_('age_group'), ADULT, GR_('guest_id'), GR_('plus_one'), YES, GR_('guest_id'))
tables.append(T('polres', 'Policy Results', 'Policy Results', 'Headcount and food cost for each policy: the adults you invite by name plus the plus-ones and children the policy counts.', [
    LST('policy', 'Policy', 'policy', 34, required=True),
    CA('headcount', 'Headcount', 'int', '%s+INDEX({range:pol.plusones},MATCH({col:policy},{range:pol.policy},0))+INDEX({range:pol.children},MATCH({col:policy},{range:pol.policy},0))' % ADULTS_CORE, 11),
    CA('food_cost', 'Food cost at full price', 'money', '{col:headcount}*{set:food_per_guest}', 13)], D.polres_d(), 50))

# 14 invitation timeline ---------------------------------------------------------------------------
tables.append(T('itime', 'Invitation Timeline', 'Invitation Timeline', 'One row per invitation step with its planned date: weeks before the wedding, days left and a status fill in. Tick Done when it is sent.', [
    C('step', 'Step', 'text', 36, required=True), C('date', 'Date', 'date', 12), C('done', 'Done', 'bool', 8),
    CA('weeks_before', 'Weeks before the wedding', 'int', 'IF({col:date}="","",ROUND(({set:wedding_day}-{col:date})/7,0))', 10), CA('days_left', 'Days left', 'int', 'IF({col:date}="","",{col:date}-{today})', 9),
    CA('status', 'Status', 'text', 'IF({col:done}=%s,%s,IF({col:days_left}="",%s,IF({col:days_left}<0,%s,IF({col:days_left}<=14,%s,%s))))' % (YES, v('Done'), v('No date'), v('Late'), v('Due soon'), v('On time')), 10), CPL()],
    D.itime_d(), 50, [A('status', '= ' + v('Late'), 'bad'), A('status', '= ' + v('Due soon'), 'warn'), A('status', '= ' + v('Done'), 'good')]))

# 15 paper and postage ---------------------------------------------------------------------------------
tables.append(T('paper', 'Paper and Postage', 'Paper and Postage', 'One row per printed piece or postage line: pieces per household or per guest, the quantity with spares and the total. The total goes to the stationery line of your budget.', [
    LST('item', 'Item', 'pitem', 22, required=True), C('per_unit', 'Pieces each', 'int', 9), C('per_guest', 'Per guest', 'bool', 9), LST('region', 'Postage region', 'region', 14), C('unit_cost', 'Unit cost', 'num', 10),
    CA('qty', 'Quantity', 'int', 'IF({col:per_guest}=%s,ROUNDUP(%s,0),IF({col:region}<>"",COUNTIFS(%s,{col:region},%s,"<>"),COUNTIFS(%s,"<>")))*{col:per_unit}' % (YES, LIKELY, HR('region'), HR('household_id'), HR('household_id')), 9),
    CA('spares', 'Spares', 'int', 'IF({col:region}<>"",0,ROUNDUP({col:qty}*{set:paper_spares_pct},0))', 8), CA('total', 'Total', 'money', 'ROUND(({col:qty}+{col:spares})*{col:unit_cost},0)', 11), CA('base_cost', 'Cost before spares', 'num', '{col:qty}*{col:unit_cost}', 12),
    LIT('printer_phone', 'Printer phone', D.PRINTER_PHONE), CPL()],
    D.paper_d(), 50))

# 16 room block ---------------------------------------------------------------------------------------------
tables.append(T('rooms', 'Room Block', 'Room Block', 'One row per night: the rooms the hotel holds for your guests at a set rate and how many are picked up so far.', [
    C('night', 'Night', 'date', 12, required=True), C('rooms_held', 'Rooms held', 'int', 11), C('picked_up', 'Picked up', 'int', 10)], D.rooms_d(), 50))

# 17 room pickup by household -----------------------------------------------------------------------------------
tables.append(T('roomhh', 'Room Pickup', 'Room Pickup by Household', 'Households that stay in the block or arrange their own stay: rooms needed, arrival and whether the room is booked. The block totals feed the hotel messages.', [
    C('rank', 'Number', 'int', 8, required=True), CA('household_id', 'Household ID', 'text', 'IFERROR(INDEX({range:households.household_id},MATCH({col:rank},{range:households.stay_seq},0)),"")', 10),
    CA('household', 'Household', 'text', LKT('households.household', 'households.household_id', 'household_id'), 24), CA('lodging', 'Lodging', 'text', LKT('households.lodging', 'households.household_id', 'household_id'), 16),
    CA('size', 'Guests', 'int', LKN('households.size', 'households.household_id', 'household_id'), 8), CA('rooms_needed', 'Rooms needed', 'int', 'ROUNDUP({col:size}/2,0)', 9),
    CA('arrival', 'Arrival', 'date', LKD('households.arrival', 'households.household_id', 'household_id'), 12),
    CA('booked', 'Booked', 'text', 'IF({col:lodging}=%s,%s,IF(IFERROR(INDEX({range:households.room_booked},MATCH({col:household_id},{range:households.household_id},0)),"")=%s,%s,%s))' % (OWN, v('Own stay'), YES, v('Booked'), v('Not booked')), 11),
    CA('rooms_booked', 'Rooms booked', 'int', 'IF({col:booked}=%s,{col:rooms_needed},0)' % v('Booked'), 9),
    CA('rooms_held_total', 'Rooms held', 'int', 'SUM({range:rooms.rooms_held})', 9), CA('picked_up_total', 'Rooms picked up', 'int', 'SUM({range:rooms.picked_up})', 10),
    CA('to_fill', 'Rooms to fill', 'int', '{col:rooms_held_total}-{col:picked_up_total}', 9), CA('room_cutoff', 'Room cut-off', 'date', '{set:room_cutoff}', 12), CA('extended_cutoff', 'Cut-off, 2 weeks later', 'date', '{set:room_cutoff}+14', 12),
    LIT('hotel_phone', 'Hotel phone', D.HOTEL_PHONE), CPL()],
    D.stay_d(), 80, [A('booked', '= ' + v('Not booked'), 'warn'), A('booked', '= ' + v('Booked'), 'good')]))

# 18 arrivals by day ------------------------------------------------------------------------------------------------
tables.append(T('arrivals', 'Arrivals by Day', 'Arrivals by Day', 'One row per day around the wedding: households and guests who arrive, from the arrival dates in Households.', [
    C('date', 'Date', 'date', 12, required=True), CA('households', 'Households', 'int', 'COUNTIFS(%s,{col:date},%s,"<>")' % (HR('arrival'), HR('household_id')), 11),
    CA('guests', 'Guests', 'int', 'SUMIFS(%s,%s,{col:date})' % (SZ, HR('arrival')), 9)], D.arrivals_d(), 50))

# 19 contact status summary -------------------------------------------------------------------------------------------
tables.append(T('cstat', 'Contact Status', 'Contact Status Summary', 'One row per contact status and tier: households and guests. A household you have lost touch with needs a check of its contact details before you send.', [
    LST('status', 'Contact status', 'cstat', 16, required=True), LST('tier', 'Tier', 'tier', 14), CA('households', 'Households', 'int', 'COUNTIFS(%s,{col:status},%s,{col:tier},%s,"<>")' % (HR('contact_status'), HR('tier'), HR('household_id')), 11),
    CA('guests', 'Guests', 'int', 'SUMIFS(%s,%s,{col:status},%s,{col:tier})' % (SZ, HR('contact_status'), HR('tier')), 9)], D.cstat_d(), 50, [A('households', '> 0', 'good')]))

# 20 capacity traffic light -----------------------------------------------------------------------------------------------
CS = '{col:scenario}'
CHEAD = ('IF(%s=%s,%s+{set:seats_others},IF(%s=%s,ROUND(%s,0)+{set:seats_others},IF(%s=%s,ROUND(%s,0)+{set:seats_others},IF(%s=%s,ROUND(%s,0)+{set:seats_others},'
         'IF(%s=%s,%s+{set:seats_others},{set:venue_capacity})))))') % (
    CS, tok('scen', 'Confirmed yes'), YESG, CS, tok('scen', 'Low'), LOWT, CS, tok('scen', 'Expected'), LIKELY, CS, tok('scen', 'High'), HIGHT, CS, tok('scen', 'Everyone says yes'), TOT)
tables.append(T('capacity', 'Capacity Light', 'Capacity Traffic Light', 'Six headcounts against the seated capacity of the venue, with the couple and helpers seated: fits, tight or over by a number of seats.', [
    LST('scenario', 'Scenario', 'scen', 22, required=True), CA('headcount', 'Headcount seated', 'int', CHEAD, 12),
    CA('verdict', 'Verdict', 'text', 'IF({col:scenario}=%s,%s,IF({col:headcount}>{set:venue_capacity},%s&" "&({col:headcount}-{set:venue_capacity}),IF({col:headcount}>={set:venue_capacity}*{set:tight_pct},%s,%s)))' % (
        tok('scen', 'Seated capacity'), v('Limit'), v('Over by'), v('Tight'), v('Fits')), 14)],
    D.scen_d(), 50, [A('verdict', '= ' + v('Fits'), 'good'), A('verdict', '= ' + v('Tight'), 'warn')]))
assert len(tables) == 20, len(tables)
