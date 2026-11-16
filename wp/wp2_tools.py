"""Wedding suite part 2: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp2_lists import *
import wp2_data as D
from wp2_tables import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v_} for l, v_ in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def LKUP(t, rc, kc, val): return 'INDEX(%s,MATCH(%s,%s,0))' % (R(t, rc), val, R(t, kc))
def W(*parts): return '&" "&'.join(parts)


tools = []
HID = 'COUNTIFS(%s,"<>")' % HR('household_id')
TODAYM = '({today}-WEEKDAY({today},2))'

# 1 ------------------------------------------------------------ side balance check
G1 = '(SUMIFS(%s,%s,%s)-{in:cut_p1})' % (SZ, HR('side'), S1); G2 = '(SUMIFS(%s,%s,%s)-{in:cut_p2})' % (SZ, HR('side'), S2); G3 = 'SUMIFS(%s,%s,%s)' % (SZ, HR('side'), SS)
TT = '(%s+%s+%s)' % (G1, G2, G3)
A1 = 'ROUND({set:agreed_p1}*%s,0)' % TT; A2 = 'ROUND({set:agreed_p2}*%s,0)' % TT; A3 = 'ROUND((1-{set:agreed_p1}-{set:agreed_p2})*%s,0)' % TT
D1 = '(%s-%s)' % (G1, A1); D2 = '(%s-%s)' % (G2, A2); D3 = '(%s-%s)' % (G3, A3)
tools.append(TOOL('side_balance', 'Side Balance Check', 'Is the guest list balanced between the two sides',
    'Type the guests you would cut from each side; the tool compares each side with the split you agreed and says which side is heavy and by how many guests.', [
    I('tolerance', 'Difference you accept, share of all guests', 0.02, 'pct'), I('cut_p1', 'Guests you cut, partner 1 side', 0, 'int'), I('cut_p2', 'Guests you cut, partner 2 side', 0, 'int')], [
    O('Guests, partner 1 side', 'int', G1), O('Guests, partner 2 side', 'int', G2), O('Guests, shared friends', 'int', G3), O('Guests after your cuts', 'int', TT),
    O('Agreed guests, partner 1 side', 'int', A1), O('Agreed guests, partner 2 side', 'int', A2), O('Agreed guests, shared friends', 'int', A3),
    O('Over or under, partner 1 side', 'int', D1), O('Over or under, partner 2 side', 'int', D2), O('Over or under, shared friends', 'int', D3),
    O('Guests you accept as a difference', 'int', 'ROUND({in:tolerance}*%s,0)' % TT),
    O('Verdict', 'text', 'IF(MAX(%s,%s,%s)<=ROUND({in:tolerance}*%s,0),%s,IF(AND(%s>=%s,%s>=%s),%s&" "&%s&" "&%s,IF(%s>=%s,%s&" "&%s&" "&%s,%s&" "&%s&" "&%s)))' % (
        D1, D2, D3, TT, v('Balanced'), D1, D2, D1, D3, S1, v('side heavy by'), D1, D2, D3, S2, v('side heavy by'), D2, SS, v('heavy by'), D3))],
    GR('What if', ('As it is', {'cut_p1': 0, 'cut_p2': 0}), ('Cut 5 from partner 1', {'cut_p1': 5}), ('Cut 3 from partner 1', {'cut_p1': 3}), ('Cut 5 from partner 2', {'cut_p2': 5}), ('Accept 5% difference', {'tolerance': 0.05}))))

# 2 ------------------------------------------------------------ capacity traffic light
EXP2 = '(ROUND(%s+{in:extra}*{set:expected_yes_rate},0)+{set:seats_others})' % LIKELY
CAP2 = '({set:venue_capacity}+{in:seats_change})'
ALL2 = '(%s+{in:extra}+{set:seats_others})' % TOT
def TL(h, cap): return 'IF(%s>%s,%s&" "&(%s-%s),IF(%s>=%s*{set:tight_pct},%s,%s))' % (h, cap, v('Over by'), h, cap, h, cap, v('Tight'), v('Fits'))
tools.append(TOOL('capacity_tool', 'Capacity Traffic Light Tool', 'Do we fit in the venue',
    'Type guests you would add and seats you would gain or lose; the tool tests the confirmed, expected and everyone-says-yes headcounts against the seated capacity.', [
    I('extra', 'Guests you add to the list', 0, 'int'), I('seats_change', 'Seats gained or lost', 0, 'int')], [
    O('Seated capacity', 'int', CAP2), O('Seats for the couple and helpers', 'int', '{set:seats_others}'), O('Guests on the list', 'int', '%s+{in:extra}' % TOT), O('Confirmed yes, seated', 'int', '%s+{set:seats_others}' % YESG),
    O('Expected headcount, seated', 'int', EXP2), O('Everyone says yes, seated', 'int', ALL2), O('Seats left at the expected headcount', 'int', '%s-%s' % (CAP2, EXP2)),
    O('Seats over if everyone says yes', 'int', 'MAX(0,%s-%s)' % (ALL2, CAP2)), O('Everyone-says-yes verdict', 'text', TL(ALL2, CAP2)), O('Verdict', 'text', TL(EXP2, CAP2))],
    GR('What if', ('As it is', {'extra': 0, 'seats_change': 0}), ('Add 5 guests', {'extra': 5}), ('Add 12 guests', {'extra': 12}), ('A room 10 seats bigger', {'seats_change': 10}), ('Cut 10 guests', {'extra': -10}))))

# 3 ------------------------------------------------------------ B list cascade
NOTYET = v('Not yet invited'); WAITS = v('Waiting for a reply')
OPEN3 = 'MAX(0,%s+{in:seats_change}-ROUND(%s,0))' % (SEATED, LIKELY)
NEXT3 = 'IFERROR(INDEX(%s,MATCH(SMALL(%s,1),%s,0)),"")' % (R('bqueue', 'household'), R('bqueue', 'wait_rank'), R('bqueue', 'rank'))
NEXTST3 = 'IFERROR(INDEX(%s,MATCH(SMALL(%s,1),%s,0)),"")' % (R('bqueue', 'status'), R('bqueue', 'wait_rank'), R('bqueue', 'rank'))
tools.append(TOOL('b_cascade', 'B List Cascade', 'Which B list household do we invite next',
    'Type the seats you gain or lose; the tool counts the seats open at the expected headcount and names the next B list household by rank to invite, or the first one still to reply.', [
    I('seats_change', 'Seats gained or lost', 0, 'int'), I('b_yes_rate', 'Share of B list guests who say yes, your estimate', 0.8, 'pct')], [
    O('Seats you can fill', 'int', '%s+{in:seats_change}' % SEATED), O('Expected guests now', 'int', 'ROUND(%s,0)' % LIKELY), O('Open seats', 'int', OPEN3),
    O('B list households not yet invited', 'int', 'COUNTIFS(%s,%s)' % (R('bqueue', 'status'), NOTYET)), O('B list households waiting for a reply', 'int', 'COUNTIFS(%s,%s)' % (R('bqueue', 'status'), WAITS)),
    O('B list guests waiting for a reply', 'int', 'SUMIFS(%s,%s,%s)' % (R('bqueue', 'size'), R('bqueue', 'status'), WAITS)),
    O('Next B household to invite or chase', 'text', NEXT3), O('Its status', 'text', NEXTST3),
    O('Guests to invite to fill the open seats', 'int', 'ROUNDUP(%s/MAX(0.01,{in:b_yes_rate}),0)' % OPEN3),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s=%s,%s&" "&%s&" "&%s,IF(%s=%s,%s&" "&%s&" "&%s,%s)))' % (OPEN3, v('No seats open'), NEXTST3, NOTYET, v('Invite'), NEXT3, v('next'), NEXTST3, WAITS, v('Chase'), NEXT3, v('first'), v('No B household left')))],
    GR('What if', ('As it is', {'seats_change': 0}), ('Ten seats fewer', {'seats_change': -10}), ('Twenty seats fewer', {'seats_change': -20}), ('Five seats more', {'seats_change': 5}), ('Ten seats more', {'seats_change': 10}))))

# 4 ------------------------------------------------------------ last send date for the B list
LAST4 = '({set:rsvp_deadline}-7*{in:reply_weeks}-{in:post_days})'
tools.append(TOOL('b_send_date', 'Last Send Date B List', 'What is the last day a B list invitation can go out',
    'Type the weeks you give guests to reply and the days the post takes; the tool counts back from your reply-by date to the latest send date.', [
    I('reply_weeks', 'Weeks you give a guest to reply', 2, 'int'), I('post_days', 'Days for the invitation to arrive', 4, 'int')], [
    O('Reply-by date', 'date', '{set:rsvp_deadline}'), O('Latest send date', 'date', LAST4), O('Days from today to the latest send date', 'int', 'IF({set:rsvp_deadline}="","",%s-{today})' % LAST4),
    O('Days a guest has to reply if you send today', 'int', 'IF({set:rsvp_deadline}="","",{set:rsvp_deadline}-{today}-{in:post_days})'), O('Reply-by date, weeks before the wedding', 'num', 'ROUND(({set:wedding_day}-{set:rsvp_deadline})/7,1)'),
    O('Typical invitation lead, weeks, typical, edit', 'int', '{set:invite_lead_weeks}'),
    O('Verdict', 'text', 'IF(%s<{today},%s&" "&({today}-%s)&" "&%s,%s&" "&(%s-{today})&" "&%s)' % (LAST4, v('Too late by'), LAST4, v('days'), v('Send within'), LAST4, v('days')))],
    GR('What if', ('As it is', {'reply_weeks': 2, 'post_days': 4}), ('Three weeks to reply', {'reply_weeks': 3}), ('One week to reply', {'reply_weeks': 1}), ('Post takes 10 days', {'post_days': 10}), ('Send by e-mail, no post', {'post_days': 0}))))

# 5 ------------------------------------------------------------ final headcount forecast
YG = YESG; OPENP = 'SUM(%s)' % HR('open_plus_ones')
LOW5 = 'ROUND(MIN(%s+%s,MAX(%s,%s+%s*{in:shift})),0)' % (YG, PENDG, YG, LOWT, PENDG)
LIK5 = 'ROUND(MIN(%s+%s,MAX(%s,%s+%s*{in:shift})),0)' % (YG, PENDG, YG, LIKELY, PENDG)
HIGH5 = 'ROUND(MIN(%s+%s,MAX(%s,%s+%s*{in:shift})),0)' % (YG, PENDG, YG, HIGHT, PENDG)
GIVE5 = '(%s+ROUND(%s*{in:take},0)+{in:spare})' % (LIK5, OPENP)
tools.append(TOOL('headcount_forecast', 'Final Headcount Forecast', 'How many guests do we give the caterer',
    'Confirmed yes plus pending households at the expected yes rate by region, with a shift you can type; low, likely and high with the cost of each and the number for the caterer.', [
    I('shift', 'Move every yes rate by', 0, 'pct'), I('take', 'Share of open plus-ones who will come, your estimate', 0.5, 'pct'), I('spare', 'Spare meals you add, your own number', 0, 'int')], [
    O('Confirmed yes', 'int', YG), O('Pending guests', 'int', PENDG), O('Open plus-one slots', 'int', OPENP), O('Low headcount', 'int', LOW5), O('Likely headcount', 'int', LIK5), O('High headcount', 'int', HIGH5),
    O('Open plus-ones who will come', 'int', 'ROUND(%s*{in:take},0)' % OPENP), O('Number for the caterer', 'int', GIVE5),
    O('Food cost at the low headcount', 'money', '%s*{set:food_per_guest}' % LOW5), O('Food cost at the likely headcount', 'money', '%s*{set:food_per_guest}' % LIK5), O('Food cost at the high headcount', 'money', '%s*{set:food_per_guest}' % HIGH5),
    O('Minimum guarantee in your contract', 'int', '{set:guarantee_guests}'), O('Guarantee less the number for the caterer', 'int', '{set:guarantee_guests}-%s' % GIVE5),
    O('Days to the headcount date', 'int', 'IF({set:headcount_date}="","",{set:headcount_date}-{today})'), O('Verdict', 'text', '%s&" "&%s' % (v('Give the caterer'), GIVE5))],
    GR('What if', ('As it is', {'shift': 0, 'take': 0.5, 'spare': 0}), ('Everyone pending is 10% likelier', {'shift': 0.1}), ('Everyone pending is 20% less likely', {'shift': -0.2}), ('No open plus-ones come', {'take': 0}), ('Add 3 spare meals', {'spare': 3}))))

# 6 ------------------------------------------------------------ guarantee exposure
EXPN = 'ROUND(%s,0)' % LIKELY; LOWN = 'ROUND(%s,0)' % LOWT
def EXPO(n): return 'MAX(0,{in:guaranteed}-%s)*{in:price}' % n
tools.append(TOOL('guarantee_exposure', 'Guarantee Exposure', 'What do we pay for empty seats if fewer guests come',
    'Type the minimum guarantee and the price per guest; a ladder of five headcounts shows the empty seats you pay for and what they cost.', [
    I('guaranteed', 'Minimum guarantee, guests you pay for', 118, 'int'), I('price', 'Price per guest', 70), I('step', 'Guests between rungs of the ladder', 5, 'int')], [
    O('Expected headcount', 'int', EXPN), O('Low headcount', 'int', LOWN), O('Exposure at the expected headcount', 'money', EXPO(EXPN)), O('Exposure at the low headcount', 'money', EXPO(LOWN)),
    O('Exposure at the low headcount less one step', 'money', EXPO('(%s-{in:step})' % LOWN)), O('Exposure at the low headcount less two steps', 'money', EXPO('(%s-2*{in:step})' % LOWN)),
    O('Exposure at the low headcount less three steps', 'money', EXPO('(%s-3*{in:step})' % LOWN)), O('Empty seats you pay for at the low headcount', 'int', 'MAX(0,{in:guaranteed}-%s)' % LOWN),
    O('Verdict', 'text', 'IF(%s=0,%s&" "&%s&" "&%s,%s&" "&%s&" "&%s&" "&%s&" "&%s)' % (EXPO(LOWN), v('No exposure at'), LOWN, v('guests'), v('Exposure'), EXPO(LOWN), v('at'), LOWN, v('guests')))],
    GR('What if', ('As it is', {'guaranteed': 118, 'price': 70}), ('Guarantee 110', {'guaranteed': 110}), ('Guarantee 125', {'guaranteed': 125}), ('Price 85 a guest', {'price': 85}), ('Steps of 10', {'step': 10}))))

# 7 ------------------------------------------------------------ RSVP chase ranker
def CH(col, n): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),%s)' % (R('chase', col), n, R('chase', 'call_order'), '""' if col in ('household', 'phone') else '0')
tools.append(TOOL('chase_ranker', 'RSVP Chase Ranker', 'Who do we call first',
    'Type how many calls you can make today; silent households are ranked by guests at stake, days silent and contact status, and households you chased recently are skipped.', [
    I('calls', 'Calls you can make today', 5, 'int')], [
    O('Households silent', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (HR('rsvp'), RP, HR('household_id'))), O('Guests silent', 'int', PENDG),
    O('Call first', 'text', CH('household', 1)), O('Phone of the first call', 'text', CH('phone', 1)), O('Guests at stake, first call', 'int', CH('stake', 1)), O('Days silent, first call', 'int', CH('silent_days', 1)),
    O('Call second', 'text', CH('household', 2)), O('Call third', 'text', CH('household', 3)),
    O('Guests at stake in today calls', 'int', 'SUMIFS(%s,%s,"<="&{in:calls})' % (R('chase', 'stake'), R('chase', 'call_order'))),
    O('Silent households you chased in the last days', 'int', 'COUNTIFS(%s,%s)-SUM(%s)' % (R('chase', 'reason'), v('Silent'), R('chase', 'callable'))),
    O('Verdict', 'text', 'IF(%s="",%s,%s&" "&%s&" "&%s)' % (CH('household', 1), v('No call today'), v('Call'), CH('household', 1), v('today')))],
    GR('What if', ('Three calls', {'calls': 3}), ('One call', {'calls': 1}), ('Five calls', {'calls': 5}), ('Eight calls', {'calls': 8}), ('Ten calls', {'calls': 10}))))

# 8 ------------------------------------------------------------ reply pace forecast
RDATE = GR_('rsvp_date')
REP8 = 'COUNTIFS(%s,">"&(%s-7*{in:weeks}),%s,"<="&%s)' % (RDATE, TODAYM, RDATE, TODAYM)
PACE8 = '(%s/MAX(1,{in:weeks}))' % REP8
WK8 = 'MAX(0,({set:rsvp_deadline}-{today})/7)'
PROJ8 = 'IF({in:slow}=0,%s*%s,%s*(1-{in:slow})*(1-POWER(1-{in:slow},%s))/MAX(0.01,{in:slow}))' % (PACE8, WK8, PACE8, WK8)
tools.append(TOOL('reply_pace', 'Reply Pace Forecast', 'Will the replies arrive before the reply-by date',
    'Replies per week over the last complete weeks, slowed each week by the share you type, times the weeks left, against the guests still to reply.', [
    I('weeks', 'Complete weeks used for the pace', 2, 'int'), I('slow', 'Replies slow by this share each week, your estimate', 0.6, 'pct')], [
    O('Replies in the last complete weeks', 'int', REP8), O('Pace, replies a week', 'num', PACE8), O('Weeks to the reply-by date', 'num', 'ROUND(%s,1)' % WK8), O('Guests still to reply', 'int', PENDG),
    O('Replies still to come at your slowdown', 'int', 'ROUND(%s,0)' % PROJ8), O('Replies needed a week to finish', 'num', 'ROUND(%s/MAX(0.1,%s),1)' % (PENDG, WK8)),
    O('Guests who stay silent at your slowdown', 'int', 'MAX(0,ROUND(%s-%s,0))' % (PENDG, PROJ8)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s&" "&ROUND(%s-%s,0)&" "&%s)' % (PROJ8, PENDG, v('On pace'), v('Behind by'), PENDG, PROJ8, v('replies')))],
    GR('What if', ('As it is', {'weeks': 2, 'slow': 0.6}), ('Replies hold steady', {'slow': 0}), ('Replies slow by a third', {'slow': 0.33}), ('Pace of the last week only', {'weeks': 1}), ('Pace of four weeks', {'weeks': 4}))))

# 9 ------------------------------------------------------------ travel decline sensitivity
PL = 'SUMIFS(%s,%s,%s,%s,%s)' % (SZ, HR('rsvp'), RP, HR('region'), tok('region', 'Local'))
PT = '(%s-%s)' % (PENDG, PL)
def LIKE9(b, e): return 'ROUND(%s+%s*%s+%s*MAX(0,%s-%s),0)' % (YESG, PL, b, PT, b, e)
tools.append(TOOL('travel_sens', 'Travel Decline Sensitivity', 'How many guests will travel decline cost us',
    'Pending guests who live nearby reply at your base rate; pending guests who travel reply at the base rate less the extra decline rate. A step moves both to show the range.', [
    I('base', 'Base yes rate of pending guests', 0.8, 'pct'), I('extra', 'Extra decline rate for guests who travel', 0.1, 'pct'), I('step', 'Step for the low and high ends', 0.05, 'pct')], [
    O('Confirmed yes', 'int', YESG), O('Pending guests who live nearby', 'int', PL), O('Pending guests who travel', 'int', PT), O('Likely headcount', 'int', LIKE9('{in:base}', '{in:extra}')),
    O('Low headcount, more declines', 'int', LIKE9('({in:base}-{in:step})', '({in:extra}+{in:step})')), O('High headcount, fewer declines', 'int', LIKE9('({in:base}+{in:step})', '({in:extra}-{in:step})')),
    O('Declines from the extra rate', 'num', 'ROUND(%s*{in:extra},1)' % PT), O('Expected declines from all travel guests, your own rate', 'int', 'ROUND(SUMIFS(%s,%s,"<>"&%s,%s,%s)*{set:travel_decline_extra},0)' % (SZ, HR('region'), tok('region', 'Local'), HR('rsvp'), RP)),
    O('Verdict', 'text', '%s&" "&%s&" "&%s&" "&%s' % (v('Likely'), LIKE9('({in:base}-{in:step})', '({in:extra}+{in:step})'), v('to'), LIKE9('({in:base}+{in:step})', '({in:extra}-{in:step})')))],
    GR('What if', ('As it is', {'base': 0.8, 'extra': 0.1}), ('Extra decline 0', {'extra': 0}), ('Extra decline 20%', {'extra': 0.2}), ('Base rate 70%', {'base': 0.7}), ('Base rate 90%', {'base': 0.9}))))

# 10 ------------------------------------------------------------ meal reconciliation
CHOSEN = 'SUM(%s)' % GR_('meal_done')
KY = 'COUNTIFS(%s,%s,%s,%s)' % (GR_('age_group'), CHILD, GR_('rsvp'), RY)
KM = 'COUNTIFS(%s,%s,%s,%s)' % (GR_('meal'), KIDM, GR_('rsvp'), RY)
tools.append(TOOL('meal_recon', 'Meal Reconciliation', 'Do the meals match the headcount',
    'Type the yes replies still to come; the tool compares the meals chosen with the yes headcount and shows who has not chosen yet.', [
    I('late_yes', 'Yes replies still to come', 0, 'int')], [
    O('Yes guests', 'int', '%s+{in:late_yes}' % YESG), O('Meals chosen', 'int', CHOSEN), O('Meals still missing', 'int', '%s+{in:late_yes}-%s' % (YESG, CHOSEN)),
    O('Households with a meal missing', 'int', 'COUNTIFS(%s,">0")' % HR('meals_missing')), O('Children yes', 'int', KY), O("Children's meals chosen", 'int', KM),
    O('Share of yes guests with a meal', 'pct', 'IFERROR(%s/(%s+{in:late_yes}),0)' % (CHOSEN, YESG)),
    O('Verdict', 'text', 'IF(%s+{in:late_yes}=%s,%s,%s&" "&%s&", "&%s&" "&(%s+{in:late_yes}))' % (YESG, CHOSEN, v('Meals match'), v('Chosen'), CHOSEN, v('headcount'), YESG))],
    GR('What if', ('As it is', {'late_yes': 0}), ('Five more yes', {'late_yes': 5}), ('Ten more yes', {'late_yes': 10}), ('Fifteen more yes', {'late_yes': 15}), ('Eighteen more yes', {'late_yes': 18}))))

# 11 ------------------------------------------------------------ caterer meal order
def MC(m): return 'SUMIFS(%s,%s,%s)' % (R('meals', 'count'), R('meals', 'meal'), m)
TOTM = 'SUM(%s)' % R('meals', 'count')
ORD = 'ROUNDUP(%s*(1+{in:spare}),0)' % LIKELY
def OR_(m): return 'ROUNDUP(%s*%s/MAX(1,%s),0)' % (ORD, MC(m), TOTM)
tools.append(TOOL('meal_order', 'Caterer Meal Order', 'What do we order for each meal',
    'Meals chosen so far set the shares; the expected headcount plus your spare share gives the number to order for each meal.', [
    I('spare', 'Spare share of meals', 0.05, 'pct')], [
    O('Expected headcount', 'int', 'ROUND(%s,0)' % LIKELY), O('Meals to order in all', 'int', ORD), O('Meat chosen', 'int', MC(MEAT)), O('Fish chosen', 'int', MC(FISH)), O('Vegetarian chosen', 'int', MC(VEG)), O('Vegan chosen', 'int', MC(VEGAN)),
    O("Children's meals chosen", 'int', MC(KIDM)), O('Order meat', 'int', OR_(MEAT)), O('Order fish', 'int', OR_(FISH)), O('Order vegetarian', 'int', OR_(VEG)), O('Order vegan', 'int', OR_(VEGAN)), O("Order children's meals", 'int', OR_(KIDM)),
    O('Verdict', 'text', '%s&" "&%s&" "&%s&", "&%s&" "&%s&", "&%s&" "&%s&", "&%s&" "&%s' % (v('Order'), OR_(MEAT), v('meat'), OR_(FISH), v('fish'), OR_(VEG), v('vegetarian'), OR_(VEGAN), v('vegan')))],
    GR('What if', ('As it is', {'spare': 0.05}), ('No spare', {'spare': 0}), ('Spare 10%', {'spare': 0.1}), ('Spare 3%', {'spare': 0.03}), ('Spare 15%', {'spare': 0.15}))))

# 12 ------------------------------------------------------------ table meal and dietary sheet
TN = 'INDEX(%s,{in:table_no})' % R('mtable', 'table')
def MTL(c_): return 'IFERROR(INDEX(%s,{in:table_no}),0)' % R('mtable', c_)
def NOTE(n): return 'COUNTIFS(%s,%s,%s,%s)' % (GR_('table'), TN, GR_('dietary'), tok('dietary', n))
tools.append(TOOL('table_sheet', 'Table Meal Sheet', 'What does this table eat',
    'Type a table number from the Meals by Table list; the tool gives its guests, each meal choice and the short dietary notes, ready to print for the caterer or the place cards.', [
    I('table_no', 'Table number, 1 to 13', 3, 'int')], [
    O('Table', 'text', TN), O('Guests at the table', 'int', MTL('guests')), O('Meat', 'int', MTL('meat')), O('Fish', 'int', MTL('fish')), O('Vegetarian', 'int', MTL('vegetarian')), O('Vegan', 'int', MTL('vegan')), O("Children's meals", 'int', MTL('children')),
    O('Dietary notes at the table', 'int', MTL('notes')), O('No nuts', 'int', NOTE('No nuts')), O('Gluten free', 'int', NOTE('Gluten free')), O('No dairy', 'int', NOTE('No dairy')), O('No shellfish', 'int', NOTE('No shellfish')), O('No mushrooms', 'int', NOTE('No mushrooms')),
    O('Guests without a meal', 'int', MTL('no_meal')),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&%s,%s)' % (MTL('no_meal'), MTL('no_meal'), v('guests without a meal'), v('Sheet ready')))],
    GR('What if', ('Table 3', {'table_no': 3}), ('Head table', {'table_no': 1}), ('Table 5', {'table_no': 5}), ('Table 8', {'table_no': 8}), ('Table 12', {'table_no': 12}))))

# 13 ------------------------------------------------------------ plus-one and children policy test
PH = LKUP('polres', 'headcount', 'policy', '{in:policy}'); PCH = LKUP('pol', 'children', 'policy', '{in:policy}')
tools.append(TOOL('policy_test', 'Plus-one Children Policy', 'Which plus-one and children policy do we choose',
    'Pick a policy; the tool shows its headcount, the food cost with children at your child price and whether it fits the venue, and names the cheapest and the most inclusive policy.', [
    IL('policy', 'Policy', 'policy', 'Named guests only'), I('child_pct', 'Child meal price as a share of the full price', 0.5, 'pct')], [
    O('Headcount under this policy', 'int', PH), O('Children counted', 'int', PCH), O('Food cost with children at your child price', 'money', '(%s-%s)*{set:food_per_guest}+%s*{set:food_per_guest}*{in:child_pct}' % (PH, PCH, PCH)),
    O('Seated with the couple and helpers', 'int', '%s+{set:seats_others}' % PH), O('Seats left or over', 'int', '{set:venue_capacity}-%s-{set:seats_others}' % PH),
    O('Cheapest policy', 'text', 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (R('polres', 'policy'), R('polres', 'food_cost'), R('polres', 'food_cost'))),
    O('Most inclusive policy', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('polres', 'policy'), R('polres', 'headcount'), R('polres', 'headcount'))),
    O('Cost gap, most inclusive less cheapest', 'money', 'MAX(%s)-MIN(%s)' % (R('polres', 'food_cost'), R('polres', 'food_cost'))),
    O('Verdict', 'text', '%s&" "&INDEX(%s,MATCH(MIN(%s),%s,0))&", "&%s&" "&INDEX(%s,MATCH(MAX(%s),%s,0))' % (v('Cheapest'), R('polres', 'policy'), R('polres', 'food_cost'), R('polres', 'food_cost'), v('most inclusive'),
                                                                                                         R('polres', 'policy'), R('polres', 'headcount'), R('polres', 'headcount')))],
    GR('What if', ('Children at half price', {'child_pct': 0.5}), ('Children at a quarter', {'child_pct': 0.25}), ('Children at three quarters', {'child_pct': 0.75}), ('Children at full price', {'child_pct': 1}), ('Children free', {'child_pct': 0}))))

# 14 ------------------------------------------------------------ open plus-one resolver
OPEN14 = 'COUNTIFS(%s,">0")' % HR('open_plus_ones')
tools.append(TOOL('plusone_resolver', 'Open Plus-one Resolver', 'Who still has to name a plus-one',
    'Households with an open plus-one slot, how many extra guests you expect and what they add to the headcount and the food cost.', [
    I('take', 'Share of open slots who will come, your estimate', 0.5, 'pct'), I('ask_days', 'Days before the reply-by date you ask for a name', 7, 'int')], [
    O('Households with an open plus-one', 'int', OPEN14), O('Open plus-one slots', 'int', OPENP), O('Extra guests you expect', 'num', 'ROUND(%s*{in:take},1)' % OPENP),
    O('Food cost of the extra guests', 'money', 'ROUND(%s*{in:take}*{set:food_per_guest},0)' % OPENP), O('Expected headcount with them', 'int', 'ROUND(%s+%s*{in:take},0)' % (LIKELY, OPENP)),
    O('Seats left after them', 'int', '%s-ROUND(%s+%s*{in:take},0)' % (SEATED, LIKELY, OPENP)), O('Ask for a name by', 'date', '{set:rsvp_deadline}-{in:ask_days}'),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s)' % (OPEN14, v('No open plus-ones'), v('Ask'), OPEN14, v('households to name a guest')))],
    GR('What if', ('As it is', {'take': 0.5}), ('All open slots come', {'take': 1}), ('None come', {'take': 0}), ('Ask 14 days before', {'ask_days': 14}), ('Ask 3 days before', {'ask_days': 3}))))

# 15 ------------------------------------------------------------ invitation timeline builder
WD_ = '{set:wedding_day}'
INV15 = '(%s-7*({in:invite_weeks}+{in:travel}*{in:extra_weeks}))' % WD_
REP15 = '(%s+7*{in:reply_weeks})' % INV15
tools.append(TOOL('timeline_builder', 'Invitation Timeline Builder', 'When do the invitation steps go out',
    'From the wedding day: the save-the-date, invitation, reminders and reply-by dates, earlier when guests travel. Compare them with the dates you used.', [
    I('save_weeks', 'Weeks before the wedding: save-the-date, typical, edit', 27, 'int'), I('invite_weeks', 'Weeks before the wedding: invitation, typical, edit', 8, 'int'),
    I('travel', 'Many guests travel: 1 yes, 0 no', 1, 'int'), I('extra_weeks', 'Extra weeks of notice for guests who travel', 26, 'int'), I('reply_weeks', 'Weeks you give guests to reply', 9, 'int')], [
    O('Save-the-date goes out', 'date', '%s-7*({in:save_weeks}+{in:travel}*{in:extra_weeks})' % WD_), O('Invitations go out', 'date', INV15), O('First reminder', 'date', '%s-14' % REP15),
    O('Last reminder and phone calls', 'date', '%s-7' % REP15), O('Reply-by date', 'date', REP15), O('Final headcount to the caterer', 'date', '{set:headcount_date}'),
    O('Your A list invitations went out on', 'date', 'IF(COUNT(%s)=0,"",MIN(%s))' % (HR('invite_sent'), HR('invite_sent'))), O('Days from today to the invitation date', 'int', 'IF({set:wedding_day}="","",%s-{today})' % INV15), O('Weeks of notice for the reply-by date', 'num', 'ROUND((%s-%s)/7,1)' % (WD_, REP15)),
    O('Verdict', 'text', 'IF(%s>={today},%s&" "&(%s-{today})&" "&%s,IF(COUNT(%s)=0,%s,IF(MIN(%s)<=%s,%s,%s&" "&(MIN(%s)-%s)&" "&%s)))' % (INV15, v('Send in'), INV15, v('days'), HR('invite_sent'), v('Send now'), HR('invite_sent'), INV15, v('Sent on time'), v('Late by'), HR('invite_sent'), INV15, v('days')))],
    GR('What if', ('As it is', {'travel': 1}), ('Nobody travels', {'travel': 0}), ('Typical 6 weeks for the invitation', {'travel': 0, 'invite_weeks': 6}), ('Extra notice 12 weeks', {'extra_weeks': 12}), ('Reply window 6 weeks', {'reply_weeks': 6}))))

# 16 ------------------------------------------------------------ paper and postage cost
PRINT16 = 'SUMIFS(%s,%s,"")*(1+{in:spare})' % (R('paper', 'base_cost'), R('paper', 'region'))
POST16 = 'SUMIFS(%s,%s,"<>")' % (R('paper', 'base_cost'), R('paper', 'region'))
TOT16 = 'ROUND(%s+%s,0)' % (PRINT16, POST16)
tools.append(TOOL('paper_cost', 'Paper and Postage Cost', 'What do the invitations cost to print and post',
    'Type the spare share and your stationery line; the tool prices the printed pieces and the postage by region from Paper and Postage and says if it feeds the budget.', [
    I('spare', 'Spare share of printed pieces', 0.1, 'pct'), I('budget_line', 'Stationery and postage line in your budget', 750)], [
    O('Households to invite', 'int', HID), O('Invitation suites to print with spares', 'int', 'ROUNDUP(%s*(1+{in:spare}),0)' % HID),
    O('Postage pieces, local', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (HR('region'), tok('region', 'Local'), HR('household_id'))), O('Postage pieces, same country', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (HR('region'), tok('region', 'Same country'), HR('household_id'))),
    O('Postage pieces, abroad', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (HR('region'), tok('region', 'Abroad'), HR('household_id'))), O('Printed pieces with spares', 'money', 'ROUND(%s,0)' % PRINT16), O('Postage', 'money', 'ROUND(%s,0)' % POST16),
    O('Paper and postage total', 'money', TOT16), O('Your stationery line', 'money', '{in:budget_line}'), O('Over or under the line', 'money', '%s-{in:budget_line}' % TOT16),
    O('Cost per household', 'num', 'ROUND(%s/MAX(1,%s),2)' % (TOT16, HID)), O('Verdict', 'text', '%s&" "&%s&", "&%s' % (v('Paper total'), TOT16, v('feeds the budget')))],
    GR('What if', ('As it is', {'spare': 0.1}), ('No spares', {'spare': 0}), ('Spares 20%', {'spare': 0.2}), ('Line 1,000', {'budget_line': 1000}), ('Line 500', {'budget_line': 500}))))

# 17 ------------------------------------------------------------ room block pickup forecast
HELD = 'SUM(%s)' % R('rooms', 'rooms_held'); PICK = 'SUM(%s)' % R('rooms', 'picked_up')
WK17 = 'MAX(0,({set:room_cutoff}-{today})/7)'
tools.append(TOOL('room_pickup_tool', 'Room Block Pickup Forecast', 'Will the room block fill by the cut-off date',
    'Type the rooms you expect to be picked up each week; the tool projects the pickup to the cut-off date and says how many rooms are still to fill.', [
    I('pace', 'Rooms picked up a week, your estimate', 0.6, 'num')], [
    O('Rooms held for the nights', 'int', HELD), O('Rooms picked up', 'int', PICK), O('Rooms still to fill', 'int', '%s-%s' % (HELD, PICK)), O('Cut-off date', 'date', '{set:room_cutoff}'),
    O('Days to the cut-off date', 'int', 'IF({set:room_cutoff}="","",{set:room_cutoff}-{today})'), O('Rooms to book a week to fill the block', 'num', 'ROUND((%s-%s)/MAX(0.1,%s),1)' % (HELD, PICK, WK17)),
    O('Projected pickup at your pace', 'int', 'MIN(%s,ROUND(%s+{in:pace}*%s,0))' % (HELD, PICK, WK17)), O('Rooms short at the cut-off at your pace', 'int', 'MAX(0,%s-ROUND(%s+{in:pace}*%s,0))' % (HELD, PICK, WK17)),
    O('Households still to book a room', 'int', 'COUNTIFS(%s,%s)' % (R('roomhh', 'booked'), v('Not booked'))),
    O('Verdict', 'text', 'IF(%s-%s<=0,%s,%s&" "&(%s-%s)&" "&%s&" "&({set:room_cutoff}-{today})&" "&%s)' % (HELD, PICK, v('Block filled'), v('Fill'), HELD, PICK, v('rooms in'), v('days')))],
    GR('What if', ('As it is', {'pace': 0.6}), ('One room a week', {'pace': 1}), ('Two rooms a week', {'pace': 2}), ('A slow half room a week', {'pace': 0.5}), ('No more pickup', {'pace': 0}))))

# 18 ------------------------------------------------------------ room block attrition exposure
REQ18 = 'ROUNDUP(%s*{set:attrition_pct},0)' % HELD
SHORT18 = 'MAX(0,%s-{in:expected_final})' % REQ18
tools.append(TOOL('attrition_tool', 'Room Block Attrition', 'What do we pay if the block is not filled',
    'Type the rooms you expect to be picked up by the attrition date; the tool compares them with the share of the block you must fill and prices the shortfall at your room rate.', [
    I('expected_final', 'Room-nights you expect picked up, your estimate', 30, 'int'), I('rate', 'Room rate for one night', 139), I('att_date', 'Attrition date, from the hotel contract', iso(ROOM_CUTOFF - day(15)), 'date')], [
    O('Room-nights held', 'int', HELD), O('Share of the block you must fill', 'pct', '{set:attrition_pct}'), O('Room-nights you must fill', 'int', REQ18), O('Room-nights picked up now', 'int', PICK),
    O('Room-nights you expect picked up', 'int', '{in:expected_final}'), O('Shortfall in room-nights', 'int', SHORT18), O('Exposure if not filled', 'money', '%s*{in:rate}' % SHORT18),
    O('Exposure if no more rooms book', 'money', 'MAX(0,%s-%s)*{in:rate}' % (REQ18, PICK)), O('Days to the attrition date', 'int', 'IF({in:att_date}="","",{in:att_date}-{today})'),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s*{in:rate})' % (SHORT18, v('Safe'), v('Exposure'), SHORT18))],
    GR('What if', ('As it is', {'expected_final': 30}), ('Block fills to 37', {'expected_final': 37}), ('Only 25 picked up', {'expected_final': 25}), ('Rate 160', {'rate': 160}), ('No more pickup', {'expected_final': 21}))))
assert len(tools) == 18, len(tools)
