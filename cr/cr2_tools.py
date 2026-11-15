"""Car rental suite part 2: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr2_lists import *
from cr2_tables import R, B, BL, VH, CVD, CCD, CAN, NOS, ACT, BKD, CMP, SOLD, CH, FREE, SERV, RENT, RESV, MS, HOLDC, HOLDA, OVL, MINV, MAXV, FREEVEH, CLS_BUF, ADR_CLASS, CARS
import cr2_tables as TB
import cr2_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, dflt): return IN(k, label, 'list', key(lst, dflt), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
PR = lambda c: R('pickups_returns', c)
CXT = lambda c: R('cancellations', c)
CMT = lambda c: R('channel_month', c)
WK = lambda c: R('weekend', c)
IDL = lambda c: R('idle_gaps', c)
PKT = tok('pkind', 'Pickup'); RTT = tok('pkind', 'Return')
def LKV(col, name): return 'INDEX(%s,MATCH(%s,%s,0))' % (VH(col), name, VH('vehicle'))
def LKBK(col, bk): return 'INDEX(%s,MATCH(%s,%s,0))' % (B(col), bk, B('booking_id'))
def FREEC(cls, lo, hi): return 'SUMPRODUCT(%s)' % FREEVEH(cls, lo, hi)
def BESTKEY(cls, lo, hi):
    f = '(%s)' % FREEVEH(cls, lo, hi)
    return 'SUMPRODUCT(MIN(1000000000-%s*(1000000000-(%s*100+%s))))' % (f, VH('odometer'), VH('fleet_no'))
def BESTNAME(cls, lo, hi): return 'IFERROR(INDEX(%s,MATCH(MOD(%s,100),%s,0)),"")' % (VH('vehicle'), BESTKEY(cls, lo, hi), VH('fleet_no'))
def BESTODO(cls, lo, hi): return 'IFERROR(INDEX(%s,MATCH(MOD(%s,100),%s,0)),0)' % (VH('odometer'), BESTKEY(cls, lo, hi), VH('fleet_no'))
TOD = '{today}'
tools = []
ST = D.ST

# 1 finder ---------------------------------------------------------------------------------
CL1, S1, E1 = '{in:cls}', '{in:start}', '{in:end}'
IDX1 = 'MATCH(%s,{range:classes.class},0)' % CL1
NXT1 = 'IFERROR(IF(SMALL(%s,COUNTIF(%s,"<"&(%s*100000+%s))+1)<(%s+1)*100000,SMALL(%s,COUNTIF(%s,"<"&(%s*100000+%s))+1)-%s*100000,""),"")' % (
    CCD('free_key'), CCD('free_key'), IDX1, S1, IDX1, CCD('free_key'), CCD('free_key'), IDX1, S1, IDX1)
FREE1 = FREEC(CL1, S1, E1)
tools.append(TOOL('finder', 'Next Free Date and Class Finder', 'Which car can I offer for these dates',
    'Pick the class and the dates; every car is tested against all bookings and service blocks, the car with the lowest miles is offered, and when none is free the next date the class opens is named.', [
    IL('cls', 'Vehicle class', 'class', 'Compact'), I('start', 'Pickup date', 'today+3', 'date'), I('end', 'Return date', 'today+6', 'date')], [
    O('Days wanted', 'int', '%s-%s+1' % (E1, S1)), O('Cars of the class in the fleet', 'int', 'COUNTIFS(%s,%s,%s,"<>"&%s)' % (VH('class'), CL1, VH('status'), SOLD)), O('Cars free for the whole span', 'int', FREE1),
    O('Car to offer, lowest miles first', 'text', 'IF(%s>0,%s,"-")' % (FREE1, BESTNAME(CL1, S1, E1))), O('Odometer of that car, miles', 'int', 'IF(%s>0,%s,0)' % (FREE1, BESTODO(CL1, S1, E1))),
    O('Next date the class has a free car', 'date', NXT1), O('Free cars that day', 'int', 'IF(%s="",0,SUMIFS(%s,%s,%s,%s,%s))' % (NXT1, CCD('free'), CCD('class'), CL1, CCD('date'), NXT1)),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&%s,IF(%s<>"",%s&" "&%s,%s))' % (FREE1, v('Offer car'), BESTNAME(CL1, S1, E1), NXT1, v('Offer class from the next free date'), CL1, v('Cannot offer')))],
    GR('What if', ('Economy, same dates', {'cls': '=' + tok('class', 'Economy')}), ('Midsize SUV, same dates', {'cls': '=' + tok('class', 'Midsize SUV')}), ('Van for a week', {'cls': '=' + tok('class', '7-seat Van'), 'end': '={in:start}+6'}),
       ('Premium, tomorrow', {'cls': '=' + tok('class', 'Premium'), 'start': '={today}+1', 'end': '={today}+2'}), ('Electric next week', {'cls': '=' + tok('class', 'Electric'), 'start': '={today}+8', 'end': '={today}+11'}))))

# 2 double-booking guard -------------------------------------------------------------------
V2, S2, E2 = '{in:veh}', '{in:start}', '{in:end}'
CLV2 = LKV('class', V2)
BUF2 = CLS_BUF(CLV2)
OV2 = 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s%s)' % (B('vehicle'), V2, B('start_date'), E2, B('end_date'), S2, HOLDC)
COND2 = '(%s=%s)*%s*(%s<=%s)*(%s>=%s)' % (B('vehicle'), V2, HOLDA, B('start_date'), E2, B('end_date'), S2)
FIRST2 = 'SUMPRODUCT(MIN(%s*%s+(1-%s)*1000000))' % (COND2, B('start_date'), COND2)
ID2 = 'IFERROR(INDEX(%s,MATCH(%s&"|"&%s,%s,0)),"")' % (B('booking_id'), V2, FIRST2, B('vkey'))
PCOND = '(%s=%s)*%s*(%s<%s)' % (B('vehicle'), V2, HOLDA, B('end_date'), S2)
PD2 = 'SUMPRODUCT(MAX(%s*(%s+%s)))' % (PCOND, B('end_date'), B('return_time'))
NCOND = '(%s=%s)*%s*(%s>%s)' % (B('vehicle'), V2, HOLDA, B('start_date'), E2)
ND2 = 'SUMPRODUCT(MIN(%s*(%s+%s)+(1-%s)*1000000))' % (NCOND, B('start_date'), B('pickup_time'), NCOND)
GPN2 = 'IF(%s=0,1000000,ROUND(((%s+{in:ph}/24)-%s)*1440,0))' % (PD2, S2, PD2)
GNN2 = 'IF(%s>=1000000,1000000,ROUND((%s-(%s+{in:rh}/24))*1440,0))' % (ND2, ND2, E2)
SV2 = 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)' % (BL('vehicle'), V2, BL('date'), E2, BL('end_date'), S2)
SHORT2 = 'MAX(0,%s-MIN(%s,%s))' % (BUF2, GPN2, GNN2)
tools.append(TOOL('guard', 'Double-Booking Guard', 'Is this booking safe from a double booking',
    'Type the car, the dates and the hours; the new booking is tested against every booking, the class turnaround buffer and the service blocks, and the first clash is named.', [
    I('veh', 'Vehicle', D.VID[ST['overlap_vehicle']]['vehicle'], 'text'), I('start', 'Pickup date', ST['overlap_start'], 'date'), I('end', 'Return date', ST['overlap_end'], 'date'),
    I('ph', 'Pickup hour, 0 to 23', 10, 'int'), I('rh', 'Return hour, 0 to 23', 17, 'int')], [
    O('Class of the car', 'text', CLV2), O('Turnaround buffer of the class, minutes', 'int', BUF2), O('Bookings that overlap the dates', 'int', OV2),
    O('First clashing booking', 'text', 'IF(%s>0,%s,"-")' % (OV2, ID2)), O('Service blocks that overlap the dates', 'int', SV2),
    O('Previous booking of the car returned', 'date', 'IF(%s=0,"",INT(%s))' % (PD2, PD2)), O('Minutes from that return to your pickup', 'int', 'IF(%s=0,"",%s)' % (PD2, GPN2)),
    O('Next booking of the car starts', 'date', 'IF(%s>=1000000,"",INT(%s))' % (ND2, ND2)), O('Minutes from your return to that pickup', 'int', 'IF(%s>=1000000,"",%s)' % (ND2, GNN2)),
    O('Verdict', 'text', 'IF(%s>0,%s,IF(%s>0,%s&" "&%s,IF(%s>0,%s&" "&%s,%s)))' % (SV2, v('Falls in a service block'), OV2, v('Overlaps booking'), ID2, SHORT2, v('Inside turnaround time by'), SHORT2, v('Clear')))],
    GR('What if', ('Dates a week later', {'start': '={in:start}+7', 'end': '={in:end}+7'}), ('One day shorter', {'end': '={in:end}-1'}), ('Pickup at 7', {'ph': 7}), ('Return at 21', {'rh': 21}), ('Starts today', {'start': '={today}', 'end': '={today}+1'}))))

# 3 calendar utilisation heat ----------------------------------------------------------------
V3 = '{in:veh}'
CT3 = 'COUNTIFS(%s,%s)' % (CVD('vehicle'), V3)
FR3 = 'COUNTIFS(%s,%s,%s,%s)' % (CVD('vehicle'), V3, CVD('status'), FREE)
def CNT3(st): return 'COUNTIFS(%s,%s,%s,%s)' % (CVD('vehicle'), V3, CVD('status'), st)
tools.append(TOOL('heat', 'Calendar Utilisation Heat', 'Is this car full, has a gap to fill or sits idle',
    'Type a car; its next 14 days are counted as rented, reserved, in service and free, with the idle runs of the car and of its class.', [I('veh', 'Vehicle', D.VID[ST['low_vehicle']]['vehicle'], 'text')], [
    O('Class', 'text', LKV('class', V3)), O('Rented days, next 14 days', 'int', CNT3(RENT)), O('Reserved days', 'int', CNT3(RESV)), O('Days in service', 'int', CNT3(SERV)), O('Free days', 'int', FR3),
    O('Utilisation, next 14 days', 'pct', 'IFERROR(1-%s/%s,0)' % (FR3, CT3)), O('Idle runs of the car that need action', 'int', 'COUNTIFS(%s,%s,%s,">="&{set:idle_gap_days})' % (IDL('vehicle'), V3, IDL('idle_days'))),
    O('Free car-days of the class, next 14 days', 'int', 'SUMIFS(%s,%s,%s)' % (CCD('free'), CCD('class'), LKV('class', V3))), O('Idle runs in the whole fleet', 'int', 'COUNTIFS(%s,">="&{set:idle_gap_days})' % IDL('idle_days')),
    O('Utilisation of the car, last 90 days', 'pct', 'IFERROR(%s,0)' % LKV('util_90', V3)),
    O('Verdict', 'text', 'IF(%s<=1,%s,IF(%s>=10,%s,%s))' % (FR3, v('Full'), FR3, v('Idle'), v('Gap to fill')))]))

# 4 extension checker ------------------------------------------------------------------------
def _ext_default():
    for e in D.ext_d():
        if e['decision'] == key('extdec', 'Open'):
            b = D.BKD[e['booking_id']]; nx = [x for x in D.HV[b['vehicle']] if x['start_date'] > e['current_end']]
            hasb = any(r['vehicle'] == b['vehicle'] and r['date'] > e['current_end'] for r in D.BLK)
            if nx and hasb and e['requested_end'] >= nx[0]['start_date']: return e['booking_id'], e['requested_end']
    for e in D.ext_d():
        if e['decision'] == key('extdec', 'Open'):
            b = D.BKD[e['booking_id']]; nx = [x for x in D.HV[b['vehicle']] if x['start_date'] > e['current_end']]
            if nx and e['requested_end'] >= nx[0]['start_date']: return e['booking_id'], e['requested_end']
    e = [x for x in D.ext_d() if x['decision'] == key('extdec', 'Open')][0]; return e['booking_id'], e['requested_end']
EXB, EXE = _ext_default()
_b = D.BKD['BK-02411']; EXB, EXE = _b['booking_id'], D.d_add(_b['end_date'], 1)
BK4, NE4 = '{in:bk}', '{in:newend}'
CE4 = LKBK('end_date', BK4); CLS4 = LKBK('class', BK4); VEH4 = LKBK('vehicle', BK4)
NS4 = 'SUMPRODUCT(MIN(%s))' % ('((%s=%s)*%s*(%s>%s)*(%s<>%s))*%s+(1-((%s=%s)*%s*(%s>%s)*(%s<>%s)))*1000000' % (B('vehicle'), VEH4, HOLDA, B('start_date'), CE4, B('booking_id'), BK4, B('start_date'), B('vehicle'), VEH4, HOLDA, B('start_date'), CE4, B('booking_id'), BK4))
NB4 = 'SUMPRODUCT(MIN(((%s=%s)*(%s>%s))*%s+(1-((%s=%s)*(%s>%s)))*1000000))' % (BL('vehicle'), VEH4, BL('date'), CE4, BL('date'), BL('vehicle'), VEH4, BL('date'), CE4)
LIM4 = 'MIN(%s,%s)' % (NS4, NB4)
FR4 = FREEC(CLS4, '(%s+1)' % CE4, NE4)
tools.append(TOOL('ext_check', 'Extension Checker', 'Can the car stay to this date',
    'Type the booking and the new end date; the next booking and service block of the car, the free cars of the class and the extra revenue at the booked rate give the answer.', [
    I('bk', 'Booking ID', EXB, 'text'), I('newend', 'New end date', EXE, 'date')], [
    O('Vehicle', 'text', VEH4), O('Class', 'text', CLS4), O('Current end date', 'date', CE4), O('Extra days', 'int', '%s-%s' % (NE4, CE4)),
    O('Next booking of the car starts', 'date', 'IF(%s>=1000000,"",%s)' % (NS4, NS4)), O('Next service block starts', 'date', 'IF(%s>=1000000,"",%s)' % (NB4, NB4)),
    O('Days the car stays free after the new end', 'int', 'IF(%s>=1000000,99,%s-%s-1)' % (LIM4, LIM4, NE4)), O('Day rate booked', 'money', 'ROUND(%s/%s,2)' % (LKBK('total', BK4), LKBK('days', BK4))),
    O('Extra revenue at the booked rate', 'money', 'ROUND((%s-%s)*%s/%s,2)' % (NE4, CE4, LKBK('total', BK4), LKBK('days', BK4))), O('Free cars of the class for the extra days', 'int', FR4),
    O('Car to swap to, lowest miles first', 'text', 'IF(%s>0,%s,"-")' % (FR4, BESTNAME(CLS4, '(%s+1)' % CE4, NE4))),
    O('Verdict', 'text', 'IF(%s>%s,%s,IF(%s>0,%s&" "&%s,%s))' % (LIM4, NE4, v('Extend'), FR4, v('Extend with a swap to'), BESTNAME(CLS4, '(%s+1)' % CE4, NE4), v('Cannot extend')))],
    GR('What if', ('Keep the end date', {'newend': '={in:newend}-1'}), ('One day longer', {'newend': '={in:newend}+1'}), ('Four days longer', {'newend': '={in:newend}+3'}), ('A week longer', {'newend': '={in:newend}+6'}))))

# 5 mid-rental swap tool ---------------------------------------------------------------------
def _free_cars(b, lo):
    n = 0
    for x in D.vehicles_d():
        if x['class'] != key('class', b['class']) or x['vehicle'] == b['vehicle'] or x['status'] == key('vstatus', 'Sold'): continue
        if any(y['start_date'] <= b['end_date'] and y['end_date'] >= lo for y in D.HV.get(x['vehicle'], [])): continue
        if any(r['vehicle'] == x['vehicle'] and r['date'] <= b['end_date'] and D.block_end(r) >= lo for r in D.BLK): continue
        n += 1
    return n
_act = [b for b in D.HB if b['status'] == 'Active' and b['end_date'] >= ahead(2)]
_act.sort(key=lambda b: -_free_cars(b, ahead(1)))
BK5, SD5 = '{in:bk}', '{in:swapdate}'
CLS5 = LKBK('class', BK5); END5 = LKBK('end_date', BK5)
FR5 = FREEC(CLS5, SD5, END5)
tools.append(TOOL('swap_tool', 'Mid-Rental Swap Tool', 'Which car can replace this one for the rest of the rental',
    'Type the booking and the swap date; the free cars of the same class for the rest of the rental are tested, and the day rate and the mileage allowance from the swap day are worked out.', [
    I('bk', 'Booking ID', _act[0]['booking_id'], 'text'), I('swapdate', 'Swap date', 'today+1', 'date')], [
    O('Car now', 'text', LKBK('vehicle', BK5)), O('Class', 'text', CLS5), O('Rental ends', 'date', END5), O('Days left from the swap date', 'int', 'MAX(0,%s-%s+1)' % (END5, SD5)),
    O('Free cars of the class for those days', 'int', FR5), O('Car to swap to, lowest miles first', 'text', 'IF(%s>0,%s,"-")' % (FR5, BESTNAME(CLS5, SD5, END5))), O('Odometer of that car, miles', 'int', 'IF(%s>0,%s,0)' % (FR5, BESTODO(CLS5, SD5, END5))),
    O('Day rate booked, kept in the same class', 'money', 'ROUND(%s/%s,2)' % (LKBK('total', BK5), LKBK('days', BK5))), O('Miles allowance from the swap day', 'int', 'MAX(0,%s-%s+1)*{set:miles_day}' % (END5, SD5)),
    O('Rental amount still to run', 'money', 'ROUND(MAX(0,%s-%s+1)*%s/%s,2)' % (END5, SD5, LKBK('total', BK5), LKBK('days', BK5))),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&%s,%s)' % (FR5, v('Swap to'), BESTNAME(CLS5, SD5, END5), v('No car of this class is free')))],
    GR('What if', ('Swap today', {'swapdate': '={today}'}), ('Swap in two days', {'swapdate': '={today}+2'}))))

# 6 source fee share report -------------------------------------------------------------------
M6 = 'EDATE(%s,1-{in:months})' % MS
def CM6(col, ch=None): return 'SUMIFS(%s,%s,">="&%s%s)' % (CMT(col), CMT('month'), M6, (',%s,%s' % (CMT('channel'), ch)) if ch else '')
OWN = lambda col: 'SUMIFS(%s,%s,">="&%s,%s,1)' % (CMT(col), CMT('month'), M6, CMT('own'))
C6 = '{in:ch}'
tools.append(TOOL('fee_share', 'Source Fee Share Report', 'What does each channel keep and what is left a day',
    'Pick a channel and the number of months; revenue, fee and net per rented day of the channel are set against all channels and your own channels (website, phone, corporate accounts).', [
    I('months', 'Months to include, this month counts', 3, 'int'), IL('ch', 'Channel', 'channel', 'Marketplace A')], [
    O('Revenue, all channels', 'money', CM6('revenue')), O('Channel fees, all channels', 'money', CM6('fee')), O('Net, all channels', 'money', CM6('net')), O('Net rate per day, all channels', 'money', 'IFERROR(%s/%s,0)' % (CM6('net'), CM6('rented_days'))),
    O('Net rate per day, own channels', 'money', 'IFERROR(%s/%s,0)' % (OWN('net'), OWN('rented_days'))), O('Revenue of the channel', 'money', 'SUMIFS(%s,%s,%s,%s,">="&%s)' % (CMT('revenue'), CMT('channel'), C6, CMT('month'), M6)),
    O('Fee of the channel', 'money', 'SUMIFS(%s,%s,%s,%s,">="&%s)' % (CMT('fee'), CMT('channel'), C6, CMT('month'), M6)), O('Rented days of the channel', 'int', 'SUMIFS(%s,%s,%s,%s,">="&%s)' % (CMT('rented_days'), CMT('channel'), C6, CMT('month'), M6)),
    O('Net rate per day of the channel', 'money', 'IFERROR((SUMIFS(%s,%s,%s,%s,">="&%s)-SUMIFS(%s,%s,%s,%s,">="&%s))/SUMIFS(%s,%s,%s,%s,">="&%s),0)' % (CMT('revenue'), CMT('channel'), C6, CMT('month'), M6, CMT('fee'), CMT('channel'), C6, CMT('month'), M6, CMT('rented_days'), CMT('channel'), C6, CMT('month'), M6)),
    O('Fee share of revenue', 'pct', 'IFERROR(SUMIFS(%s,%s,%s,%s,">="&%s)/SUMIFS(%s,%s,%s,%s,">="&%s),0)' % (CMT('fee'), CMT('channel'), C6, CMT('month'), M6, CMT('revenue'), CMT('channel'), C6, CMT('month'), M6)),
    O('Net lost a day against selling the same rental direct', 'money', 'IFERROR(SUMIFS(%s,%s,%s,%s,">="&%s)/SUMIFS(%s,%s,%s,%s,">="&%s),0)' % (CMT('fee'), CMT('channel'), C6, CMT('month'), M6, CMT('rented_days'), CMT('channel'), C6, CMT('month'), M6)),
    O('Verdict', 'text', 'IF(IFERROR(SUMIFS(%s,%s,%s,%s,">="&%s)/SUMIFS(%s,%s,%s,%s,">="&%s),0)>0.5,%s&" "&%s,%s&" "&%s)' % (CMT('fee'), CMT('channel'), C6, CMT('month'), M6, CMT('rented_days'), CMT('channel'), C6, CMT('month'), M6, C6, v('nets less a day than direct'), C6, v('nets about the same as direct')))],
    GR('What if', ('Marketplace B', {'ch': '=' + tok('channel', 'Marketplace B')}), ('Hotel partner', {'ch': '=' + tok('channel', 'Hotel partner')}), ('Website', {'ch': '=' + tok('channel', 'Website')}), ('Six months', {'months': 6}), ('One month', {'months': 1}))))

# 7 channel mix planner -----------------------------------------------------------------------
A7 = 'INDEX(%s,1)' % CMT('own_nd3'); B7 = 'INDEX(%s,1)' % CMT('mkt_nd3'); CUR7 = 'INDEX(%s,1)' % CMT('mkt_share3'); DAYS7 = 'INDEX(%s,1)' % CMT('days3')
MAX7 = 'IF({in:target}<=%s,1,IF(AND(%s>%s,{in:target}<=%s),IFERROR((%s-{in:target})/(%s-%s),0),0))' % (B7, A7, B7, A7, A7, A7, B7)
tools.append(TOOL('mix', 'Channel Mix Planner', 'How many days can go to marketplaces',
    'Type the net rate per day you want to hold; the net rate of marketplaces and of your own channels over the last 3 months give the largest share of days that can go to marketplaces.', [
    I('target', 'Net rate per day you want to hold', 67.5)], [
    O('Net rate per day, own channels, last 3 months', 'money', A7), O('Net rate per day, marketplaces, last 3 months', 'money', B7), O('Rented days, all channels, last 3 months', 'int', DAYS7),
    O('Share of rented days on marketplaces now', 'pct', CUR7), O('Largest share that holds the target', 'pct', MAX7), O('Room left, share of days', 'pct', '%s-%s' % (MAX7, CUR7)),
    O('Rental days a month that could move', 'int', 'ROUND(MAX(0,%s-%s)*%s/3,0)' % (MAX7, CUR7, DAYS7)),
    O('Net rate per day at the largest share', 'money', '%s+%s*(%s-%s)' % (A7, MAX7, B7, A7)),
    O('Verdict', 'text', 'IF(%s-%s>0.05,%s,IF(%s-%s>0.05,%s,%s))' % (MAX7, CUR7, v('List more cars'), CUR7, MAX7, v('List fewer cars'), v('Hold the mix')))],
    GR('What if', ('Target 66', {'target': 66}), ('Target 67', {'target': 67}), ('Target 68', {'target': 68}), ('Target 68.5', {'target': 68.5}), ('Target 70', {'target': 70}))))

# 8 pickup and return load ---------------------------------------------------------------------
D8 = '{in:day}'
def HL(k): return 'COUNTIFS(%s,%s,%s,%d)' % (PR('date'), D8, PR('hour_load'), k)
PEAK8 = '0'
for k in range(1, 13): PEAK8 = 'IF(%s>0,%d,%s)' % (HL(k), k, PEAK8)
PH8 = 'ROUNDDOWN(AVERAGEIFS(%s,%s,%s,%s,%s),0)' % (PR('hour'), PR('date'), D8, PR('hour_load'), PEAK8)
tools.append(TOOL('load', 'Pickup and Return Load', 'Do I need a second person at the counter',
    'Pick a day of the next 7 days and the staff on the counter; pickups and returns are counted by hour and the busiest hour is set against what your team handles.', [
    I('day', 'Day', 'today+1', 'date'), I('staff', 'Staff on the counter', 1, 'int'), I('cap', 'Pickups and returns one person handles in an hour', 3, 'int')], [
    O('Pickups that day', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (PR('date'), D8, PR('kind'), PKT)), O('Returns that day', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (PR('date'), D8, PR('kind'), RTT)),
    O('Pickups and returns together', 'int', 'COUNTIFS(%s,%s)' % (PR('date'), D8)), O('Most in one hour', 'int', PEAK8), O('Busiest hour', 'int', 'IF(%s=0,0,%s)' % (PEAK8, PH8)),
    O('Handled in an hour by your team', 'int', '{in:staff}*{in:cap}'), O('People needed in the busiest hour', 'int', 'ROUNDUP(%s/{in:cap},0)' % PEAK8),
    O('Deliveries and collections that day', 'int', 'COUNTIFS(%s,%s,%s,"<>"&%s)' % (PR('date'), D8, PR('location'), TB.MAIN)),
    O('Verdict', 'text', 'IF(%s>{in:staff}*{in:cap},%s&" "&%s,%s)' % (PEAK8, v('Second person needed at hour'), PH8, v('Covered')))],
    GR('What if', ('Two on the counter', {'staff': 2}), ('Three an hour each', {'cap': 3, 'staff': 1}), ('Two an hour each', {'cap': 2}), ('Today', {'day': '={today}'}), ('In three days', {'day': '={today}+3'}))))

# 9 overbooking risk ---------------------------------------------------------------------------
def _ob_default():
    best = None
    for cl in CLASSES:
        n = sum(1 for x in D.ACTIVE if x['class'] == cl)
        for k in range(1, 15):
            day = iso(D.td(k))
            busy = len({b['vehicle'] for b in D.HB if b['class'] == cl and D.covers(b, day)}) + sum(1 for r in D.BLK if D.VNAME[r['vehicle']]['class'] == cl and r['date'] <= day <= D.block_end(r))
            if best is None or n - busy < best[0]: best = (n - busy, cl, k)
    return best
_, OBC, OBK = _ob_default()
C9, D9 = '{in:cls}', '{in:day}'
FLT9 = '(COUNTIFS(%s,%s,%s,"<="&%s)-COUNTIFS(%s,%s,%s,"<"&%s))' % (VH('class'), C9, VH('purchase_date'), D9, VH('class'), C9, VH('sold_date'), D9)
BK9 = 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s%s)' % (B('class'), C9, B('start_date'), D9, B('end_date'), D9, HOLDC)
SV9 = 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)' % (BL('class'), C9, BL('date'), D9, BL('end_date'), D9)
MK9 = 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s,%s,%s%s)+COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s,%s,%s%s)' % (
    B('class'), C9, B('start_date'), D9, B('end_date'), D9, B('channel'), CH['Marketplace A'], HOLDC, B('class'), C9, B('start_date'), D9, B('end_date'), D9, B('channel'), CH['Marketplace B'], HOLDC)
FR9 = '(%s-%s-%s-{in:margin})' % (FLT9, SV9, BK9)
tools.append(TOOL('overbook', 'Overbooking Risk', 'Could a marketplace sell a car I do not have',
    'Pick a class and a day; the cars in the fleet, in service and booked are counted, the cars you keep back for late returns are taken off, and the verdict says when to block marketplace listings.', [
    IL('cls', 'Vehicle class', 'class', OBC), I('day', 'Day', 'today+%d' % OBK, 'date'), I('margin', 'Cars kept back for late returns', 1, 'int')], [
    O('Cars of the class in the fleet', 'int', FLT9), O('Cars in a service block', 'int', SV9), O('Cars booked that day', 'int', BK9), O('Of which booked through marketplaces', 'int', MK9),
    O('Pickups that day', 'int', 'COUNTIFS(%s,%s,%s,%s%s)' % (B('class'), C9, B('start_date'), D9, HOLDC)), O('Returns that day', 'int', 'COUNTIFS(%s,%s,%s,%s%s)' % (B('class'), C9, B('end_date'), D9, HOLDC)),
    O('Cars free before the margin', 'int', '%s-%s-%s' % (FLT9, SV9, BK9)), O('Cars free after the margin', 'int', FR9),
    O('Verdict', 'text', 'IF(%s<0,%s&" "&%s,%s)' % (FR9, v('Block marketplace listings for'), C9, v('Safe')))],
    GR('What if', ('No margin', {'margin': 0}), ('Two cars kept back', {'margin': 2}), ('Day after', {'day': '={in:day}+1'}), ('Next week', {'day': '={in:day}+7'}), ('Tomorrow', {'day': '={today}+1'}))))

# 10 weekend shortage and surplus --------------------------------------------------------------
_sat = (5 - T0.weekday()) % 7 if (T0 := D.T) else 0
SA, CL10 = '{in:sat}', '{in:cls}'
FD10 = '(COUNTIFS(%s,%s,%s,"<="&%s)-COUNTIFS(%s,%s,%s,"<"&%s)+COUNTIFS(%s,%s,%s,"<="&(%s+1))-COUNTIFS(%s,%s,%s,"<"&(%s+1))-COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)-COUNTIFS(%s,%s,%s,"<="&(%s+1),%s,">="&(%s+1)))' % (
    VH('class'), CL10, VH('purchase_date'), SA, VH('class'), CL10, VH('sold_date'), SA, VH('class'), CL10, VH('purchase_date'), SA, VH('class'), CL10, VH('sold_date'), SA,
    BL('class'), CL10, BL('date'), SA, BL('end_date'), SA, BL('class'), CL10, BL('date'), SA, BL('end_date'), SA)
BD10 = 'SUMPRODUCT((%s=%s)*%s*%s)' % (B('class'), CL10, HOLDA, OVL(SA, '(%s+1)' % SA, B('start_date'), B('end_date')))
SH10 = 'IFERROR(MIN(1,%s/%s),0)' % (BD10, FD10)
tools.append(TOOL('weekend_tool', 'Weekend Shortage and Surplus', 'Should I close, hold or promote this weekend',
    'Pick a class and the Saturday; booked days are set against fleet days and the share is compared with your target and with the previous four weekends of the whole fleet.', [
    IL('cls', 'Vehicle class', 'class', 'Compact'), I('sat', 'Saturday of the weekend', 'today+%d' % _sat, 'date')], [
    O('Fleet days of the class, Saturday and Sunday', 'int', FD10), O('Booked days of the class', 'int', BD10), O('Weekend booked share of the class', 'pct', SH10), O('Free car-days', 'int', 'MAX(0,%s-%s)' % (FD10, BD10)),
    O('Free cars each day', 'num', 'ROUND(MAX(0,%s-%s)/2,1)' % (FD10, BD10)), O('Share that closes a listing', 'pct', '{set:weekend_target}'), O('Weekend share of the whole fleet, previous 4 weeks', 'pct', 'IFERROR(AVERAGEIFS(%s,%s,">="&(%s-33),%s,"<"&(%s-5)),0)' % (WK('share'), WK('week'), SA, WK('week'), SA)),
    O('Verdict', 'text', 'IF(%s>={set:weekend_target},%s,IF(%s<{set:util_red},%s,%s))' % (SH10, v('Close listing'), SH10, v('Promote'), v('Hold')))],
    GR('What if', ('Economy', {'cls': '=' + tok('class', 'Economy')}), ('Midsize SUV', {'cls': '=' + tok('class', 'Midsize SUV')}), ('7-seat Van', {'cls': '=' + tok('class', '7-seat Van')}), ('Premium', {'cls': '=' + tok('class', 'Premium')}), ('Electric', {'cls': '=' + tok('class', 'Electric')}), ('Weekend after', {'sat': '={in:sat}+7'}))))

# 11 turnaround buffer check -------------------------------------------------------------------
C11 = '{in:cls}'
W11 = '%s,%s,%s,">="&({today}-{in:days}),%s,"<="&{today},%s,">=0"' % (B('class'), C11, B('start_date'), B('start_date'), B('gap_min'))
N11 = 'COUNTIFS(%s,%s,%s,">=0",%s,">="&({today}-{in:days}),%s,"<="&{today})' % (B('class'), C11, B('gap_min'), B('start_date'), B('start_date'))
U11 = 'COUNTIFS(%s,%s,%s,">=0",%s,"<"&{set:tight_turn_hours}*60,%s,">="&({today}-{in:days}),%s,"<="&{today})' % (B('class'), C11, B('gap_min'), B('gap_min'), B('start_date'), B('start_date'))
UB11 = 'COUNTIFS(%s,%s,%s,"<"&%s,%s,">="&({today}-{in:days}),%s,"<="&{today})' % (B('class'), C11, B('gap_min'), CLS_BUF(C11), B('start_date'), B('start_date'))
tools.append(TOOL('buffer_tool', 'Turnaround Buffer Check', 'Is the turnaround buffer of this class long enough',
    'Pick a class and the days to look back; the real time between each return and the next pickup is set against the buffer and your tight-turn limit.', [
    IL('cls', 'Vehicle class', 'class', 'Midsize SUV'), I('days', 'Days to look back', 180, 'int'), I('limit', 'Share of tight turns you accept', 0.05, 'pct')], [
    O('Buffer of the class now, minutes', 'int', CLS_BUF(C11)), O('Turns checked', 'int', N11), O('Average time between return and pickup, hours', 'num', 'IFERROR(ROUND(AVERAGEIFS(%s,%s)/60,1),0)' % (B('gap_min'), W11)),
    O('Turns inside the buffer', 'int', UB11), O('Tight turns, under your limit in hours', 'int', U11), O('Share of tight turns', 'pct', 'IFERROR(%s/%s,0)' % (U11, N11)), O('Share you accept', 'pct', '{in:limit}'),
    O('Suggested buffer, minutes', 'int', 'IF(OR(%s>0,IFERROR(%s/%s,0)>{in:limit}),%s+30,%s)' % (UB11, U11, N11, CLS_BUF(C11), CLS_BUF(C11))),
    O('Verdict', 'text', 'IF(OR(%s>0,IFERROR(%s/%s,0)>{in:limit}),%s&" "&(%s+30),%s)' % (UB11, U11, N11, v('Raise the buffer to'), CLS_BUF(C11), v('Keep the buffer')))],
    GR('What if', ('Accept 10 percent', {'limit': 0.10}), ('Accept 2 percent', {'limit': 0.02}), ('Look back 90 days', {'days': 90}), ('Look back 360 days', {'days': 360}))))

# 12 late-return knock-on ----------------------------------------------------------------------
def _late_default():
    best = None
    for p in D.pr_d():
        if p['kind'] != key('pkind', 'Return'): continue
        b = D.BKD[p['booking_id']]; nx = [x for x in D.HV[b['vehicle']] if x['start_date'] > b['end_date']]
        if nx:
            g = (D.dd(nx[0]['start_date']) - D.dd(b['end_date'])).days * 1440 + D.tm(nx[0]['pickup_time']) - D.tm(b['return_time'])
            if best is None or g < best[0]: best = (g, b['booking_id'])
    return best[1]
BK12 = '{in:bk}'; VEH12 = LKBK('vehicle', BK12); END12 = LKBK('end_date', BK12)
NC12 = '(%s=%s)*%s*(%s>=%s)*(%s<>%s)' % (B('vehicle'), VEH12, HOLDA, B('start_date'), END12, B('booking_id'), BK12)
NS12 = 'SUMPRODUCT(MIN(%s*%s+(1-%s)*1000000))' % (NC12, B('start_date'), NC12)
NT12 = 'SUMPRODUCT(%s*(%s=%s)*%s)' % (NC12, B('start_date'), NS12, B('pickup_time'))
NDT12 = 'SUMPRODUCT(MIN(%s*(%s+%s)+(1-%s)*1000000))' % (NC12, B('start_date'), B('pickup_time'), NC12)
GP12 = 'ROUND((%s-(%s+%s))*1440,0)' % (NDT12, END12, LKBK('return_time', BK12))
GA12 = '(%s-{in:late})' % GP12
NS12 = 'INT(%s)' % NDT12
NT12 = 'MOD(%s,1)' % NDT12
BF12 = CLS_BUF(LKBK('class', BK12))
tools.append(TOOL('late_tool', 'Late-Return Knock-On', 'What does this late return do to the next pickup',
    'Type the booking that is coming back late and the minutes; the next pickup of the same car, the time left, your buffer and the late fee are worked out.', [
    I('bk', 'Booking ID', _late_default(), 'text'), I('late', 'Minutes late', 240, 'int')], [
    O('Car', 'text', VEH12), O('Class', 'text', LKBK('class', BK12)), O('Due back on', 'date', END12), O('Due back at', 'time', LKBK('return_time', BK12)),
    O('Next pickup of the car', 'date', 'IF(%s>=1000000,"",%s)' % (NDT12, NS12)), O('Next pickup time', 'time', 'IF(%s>=1000000,"",%s)' % (NDT12, NT12)),
    O('Minutes between return and next pickup as planned', 'int', 'IF(%s>=1000000,"",%s)' % (NDT12, GP12)), O('Minutes left after the delay', 'int', 'IF(%s>=1000000,"",%s)' % (NDT12, GA12)),
    O('Buffer of the class, minutes', 'int', BF12), O('Late fee, started hours after the grace', 'money', 'IF({in:late}>{set:late_grace_min},ROUNDUP({in:late}/60,0)*{set:late_fee_hour},0)'),
    O('Verdict', 'text', 'IF(%s>=1000000,%s,IF(%s<%s,%s,IF(%s<{set:tight_turn_hours}*60,%s,%s)))' % (NDT12, v('No effect'), GA12, BF12, v('Move the next pickup'), GA12, v('Call the renter'), v('No effect')))],
    GR('What if', ('30 minutes late', {'late': 30}), ('90 minutes late', {'late': 90}), ('6 hours late', {'late': 360}), ('14 hours late', {'late': 840}), ('A day late', {'late': 1440}))))

# 13 cancellation impact -----------------------------------------------------------------------
C13 = '{in:ch}'
BW = '%s,%s,%s,">="&({today}-180),%s,"<="&{today}' % (B('channel'), C13, B('start_date'), B('start_date'))
CN13 = 'COUNTIFS(%s)' % BW
XN13 = 'COUNTIFS(%s,%s,%s)' % (BW, B('status'), CAN)
NN13 = 'COUNTIFS(%s,%s,%s)' % (BW, B('status'), NOS)
SH13 = 'IFERROR((%s+%s)/%s,0)' % (XN13, NN13, CN13)
AL13 = 'IFERROR((COUNTIFS(%s,%s,%s,">="&({today}-180),%s,"<="&{today})+COUNTIFS(%s,%s,%s,">="&({today}-180),%s,"<="&{today}))/COUNTIFS(%s,">="&({today}-180),%s,"<="&{today}),0)' % (
    B('status'), CAN, B('start_date'), B('start_date'), B('status'), NOS, B('start_date'), B('start_date'), B('start_date'), B('start_date'))
RISK13 = 'SUMIFS(%s,%s,%s,%s,%s,%s,">"&{today},%s,"<="&({today}+{in:ahead}))' % (B('total'), B('channel'), C13, B('status'), BKD, B('start_date'), B('start_date'))
tools.append(TOOL('cancel_tool', 'Cancellation Impact', 'Is this channel cancelling too much',
    'Pick a channel; its cancellations and no-shows of the last 180 days, the notice given and the revenue lost are set against your limit, with the revenue at risk in the coming days.', [
    IL('ch', 'Channel', 'channel', 'Corporate account'), I('ahead', 'Days ahead for revenue at risk', 14, 'int')], [
    O('Bookings started, last 180 days', 'int', CN13), O('Cancelled', 'int', XN13), O('No-shows', 'int', NN13), O('Cancellation and no-show share of the channel', 'pct', SH13), O('The same share, all channels', 'pct', AL13),
    O('Average notice given on cancellations, days', 'num', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,%s,%s,%s,%s,">="&({today}-180)),1),0)' % (CXT('notice_days'), CXT('channel'), C13, CXT('kind'), tok('cxkind', 'Cancelled'), CXT('cancelled_on'))),
    O('Revenue lost, last 180 days', 'money', 'SUMIFS(%s,%s,%s,%s,">="&({today}-180))' % (CXT('revenue_lost'), CXT('channel'), C13, CXT('cancelled_on'))),
    O('Booked revenue starting in the days ahead', 'money', RISK13), O('Revenue at risk at the same share', 'money', 'ROUND(%s*%s,2)' % (RISK13, SH13)), O('Share you accept', 'pct', '{set:cancel_limit}'),
    O('Late cancellation fee now', 'money', '{set:cancel_fee}'),
    O('Verdict', 'text', 'IF(%s>{set:cancel_limit},%s,%s)' % (SH13, v('Tighten the cancellation fee'), v('Acceptable')))],
    GR('What if', ('Website', {'ch': '=' + tok('channel', 'Website')}), ('Phone', {'ch': '=' + tok('channel', 'Phone')}), ('Hotel partner', {'ch': '=' + tok('channel', 'Hotel partner')}), ('Marketplace A', {'ch': '=' + tok('channel', 'Marketplace A')}), ('Marketplace B', {'ch': '=' + tok('channel', 'Marketplace B')}), ('30 days ahead', {'ahead': 30}))))

# 14 booking pace forecast ---------------------------------------------------------------------
H14 = '{in:days}'
NOW14 = 'COUNTIFS(%s,">="&{today},%s,"<"&({today}+%s)%s)' % (B('start_date'), B('start_date'), H14, HOLDC)
LYA14 = 'COUNTIFS(%s,">="&({today}-364),%s,"<"&({today}-364+%s),%s,"<="&({today}-364)%s)' % (B('start_date'), B('start_date'), H14, B('created_on'), HOLDC)
LYF14 = 'COUNTIFS(%s,">="&({today}-364),%s,"<"&({today}-364+%s)%s)' % (B('start_date'), B('start_date'), H14, HOLDC)
SF14 = 'IF({in:scen}=%s,1.1,IF({in:scen}=%s,0.9,1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
tools.append(TOOL('pace', 'Booking Pace Forecast', 'Am I ahead of last year for the coming weeks',
    'Bookings already made for the next weeks are set against the same weeks last year at the same point; Base, Best and Worst scenarios project the final count.', [
    I('days', 'Days ahead', 28, 'int'), IL('scen', 'Scenario', 'scen', 'Base')], [
    O('Bookings made for the coming days', 'int', NOW14), O('Bookings made at this point last year for the same days', 'int', LYA14), O('Pace against last year', 'pct', 'IFERROR(%s/%s-1,0)' % (NOW14, LYA14)),
    O('All bookings of the same days last year', 'int', LYF14), O('Scenario factor', 'num', SF14), O('Projected bookings for the coming days', 'int', 'ROUND(IFERROR(%s*%s/%s,%s)*%s,0)' % (LYF14, NOW14, LYA14, NOW14, SF14)),
    O('Still to book to reach the projection', 'int', 'MAX(0,ROUND(IFERROR(%s*%s/%s,%s)*%s,0)-%s)' % (LYF14, NOW14, LYA14, NOW14, SF14, NOW14)),
    O('Bookings behind last year', 'int', 'MAX(0,%s-%s)' % (LYA14, NOW14)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s>%s*(1+{set:pace_tol}),%s,IF(%s>=%s*(1-{set:pace_tol}),%s,%s&" "&(%s-%s))))' % (LYA14, v('Not enough history'), NOW14, LYA14, v('Ahead of last year'), NOW14, LYA14, v('On pace'), v('Behind by'), LYA14, NOW14))],
    GR('What if', ('Best', {'scen': '=' + tok('scen', 'Best')}), ('Worst', {'scen': '=' + tok('scen', 'Worst')}), ('14 days ahead', {'days': 14}), ('42 days ahead', {'days': 42}))))

# 15 vehicle unavailability planner ------------------------------------------------------------
V15, S15, N15, K15 = '{in:veh}', '{in:start}', '{in:days}', '{in:bk}'
E15 = '(%s+%s-1)' % (S15, N15)
AF15 = 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s%s)' % (B('vehicle'), V15, B('start_date'), E15, B('end_date'), S15, HOLDC)
CLS15 = LKBK('class', K15)
FR15 = FREEC(CLS15, LKBK('start_date', K15), LKBK('end_date', K15))
_v15 = [b for b in D.HB if b['status'] == 'Booked' and ahead(2) <= b['start_date'] <= ahead(9)]
tools.append(TOOL('unavail', 'Vehicle Unavailability Planner', 'Which bookings move if this car goes to the workshop',
    'Type the car, the days it will be off the road and the first booking it affects; the bookings in those days are counted and the booking is matched to a free car of the same class.', [
    I('veh', 'Vehicle', _v15[0]['vehicle'], 'text'), I('start', 'First day off the road', _v15[0]['start_date'], 'date'), I('days', 'Days off the road', 3, 'int'), I('bk', 'Booking to move', _v15[0]['booking_id'], 'text')], [
    O('Class of the booking to move', 'text', CLS15), O('Bookings affected', 'int', AF15), O('Revenue of those bookings', 'money', 'SUMIFS(%s,%s,%s,%s,"<="&%s,%s,">="&%s%s)' % (B('total'), B('vehicle'), V15, B('start_date'), E15, B('end_date'), S15, HOLDC)),
    O('Last day off the road', 'date', E15), O('Booking to move starts', 'date', LKBK('start_date', K15)), O('Booking to move ends', 'date', LKBK('end_date', K15)),
    O('Free cars of the class for that booking', 'int', FR15), O('Car to move it to, lowest miles first', 'text', 'IF(%s>0,%s,"-")' % (FR15, BESTNAME(CLS15, LKBK('start_date', K15), LKBK('end_date', K15)))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s>0,%s&" "&%s&" > "&%s,%s&" "&%s))' % (AF15, v('No booking affected'), FR15, v('Move booking'), K15, BESTNAME(CLS15, LKBK('start_date', K15), LKBK('end_date', K15)), v('No car free for booking'), K15))],
    GR('What if', ('One day', {'days': 1}), ('Five days', {'days': 5}), ('Starts a week later', {'start': '={in:start}+7'}), ('Starts today', {'start': '={today}'}))))

# 16 marketplace block list --------------------------------------------------------------------
M16, N16 = '{in:mkt}', '{in:days}'
DW = '%s,">="&{today},%s,"<="&({today}+%s-1)' % (CVD('date'), CVD('date'), N16)
HELD16 = 'COUNTIFS(%s,%s,"<>"&%s)' % (DW, CVD('status'), FREE)
OWN16 = 'COUNTIFS(%s,%s,%s,%s,"<>"&%s)' % (DW, CVD('channel'), M16, CVD('status'), FREE)
TD16 = '%s,{today}' % CVD('date')
tools.append(TOOL('mkt_block', 'Marketplace Block List', 'How many dates must I block on this marketplace today',
    'Pick a marketplace and the days ahead; every day a car is booked directly, through another channel or is in service must be blocked on that listing, and today\'s count is named.', [
    IL('mkt', 'Marketplace', 'channel', 'Marketplace A'), I('days', 'Days ahead, 1 to 14', 14, 'int')], [
    O('Car-days held in the days ahead', 'int', HELD16), O('Of which booked through this marketplace', 'int', OWN16),
    O('Of which booked through the other marketplace', 'int', '(COUNTIFS(%s,%s,%s,%s,"<>"&%s)+COUNTIFS(%s,%s,%s,%s,"<>"&%s))-%s' % (DW, CVD('channel'), CH['Marketplace A'], CVD('status'), FREE, DW, CVD('channel'), CH['Marketplace B'], CVD('status'), FREE, OWN16)),
    O('Of which in service blocks', 'int', 'COUNTIFS(%s,%s,%s)' % (DW, CVD('status'), SERV)), O('Car-days to block on this marketplace', 'int', '%s-%s' % (HELD16, OWN16)),
    O('Car-days to block that start today', 'int', 'COUNTIFS(%s,%s,"<>"&%s)-COUNTIFS(%s,%s,%s,%s,"<>"&%s)' % (TD16, CVD('status'), FREE, TD16, CVD('channel'), M16, CVD('status'), FREE)),
    O('Vehicles with a service block in the days ahead', 'int', 'COUNTIFS(%s,">="&{today},%s,"<="&({today}+%s-1))' % (BL('date'), BL('date'), N16)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s,"<>"&%s)-COUNTIFS(%s,%s,%s,%s,"<>"&%s)>0,(COUNTIFS(%s,%s,"<>"&%s)-COUNTIFS(%s,%s,%s,%s,"<>"&%s))&" "&%s,%s)' % (
        TD16, CVD('status'), FREE, TD16, CVD('channel'), M16, CVD('status'), FREE, TD16, CVD('status'), FREE, TD16, CVD('channel'), M16, CVD('status'), FREE, v('dates to block today'), v('Nothing to block today')))],
    GR('What if', ('Marketplace B', {'mkt': '=' + tok('channel', 'Marketplace B')}), ('7 days', {'days': 7}), ('3 days', {'days': 3}))))

# 17 class substitution advisor ----------------------------------------------------------------
C17, S17, N17 = '{in:cls}', '{in:start}', '{in:days}'
E17 = '(%s+%s-1)' % (S17, N17)
I17 = 'MATCH(%s,{range:classes.class},0)' % C17
UP17 = 'INDEX({range:classes.class},CHOOSE(%s,2,3,5,5,5,5))' % I17
DN17 = 'INDEX({range:classes.class},CHOOSE(%s,1,1,2,3,3,2))' % I17
ADR_W, ADR_U = ADR_CLASS(C17), ADR_CLASS(UP17)
FW17, FU17 = FREEC(C17, S17, E17), FREEC(UP17, S17, E17)
tools.append(TOOL('subst', 'Class Substitution Advisor', 'Class full: upgrade, charge or decline',
    'Pick the class, the start and the days; free cars of the class above and below are counted and your free-upgrade limit decides who pays.', [
    IL('cls', 'Class wanted', 'class', 'Midsize SUV'), I('start', 'Pickup date', 'today+2', 'date'), I('days', 'Days', 3, 'int')], [
    O('Free cars of the class wanted', 'int', FW17), O('Class above', 'text', UP17), O('Free cars of the class above', 'int', FU17), O('Class below', 'text', DN17), O('Free cars of the class below', 'int', FREEC(DN17, S17, E17)),
    O('Average daily rate of the class wanted', 'money', ADR_W), O('Average daily rate of the class above', 'money', ADR_U), O('Price difference a day', 'money', 'MAX(0,%s-%s)' % (ADR_U, ADR_W)),
    O('Price difference for the whole rental', 'money', 'MAX(0,%s-%s)*%s' % (ADR_U, ADR_W, N17)), O('Most a day you absorb', 'money', '{set:upgrade_free}'),
    O('Verdict', 'text', 'IF(%s>0,%s,IF(%s>0,IF(MAX(0,%s-%s)<={set:upgrade_free},%s,%s),%s))' % (FW17, v('Clear'), FU17, ADR_U, ADR_W, v('Free upgrade'), v('Charge the difference'), v('Decline')))],
    GR('What if', ('Economy', {'cls': '=' + tok('class', 'Economy')}), ('Compact', {'cls': '=' + tok('class', 'Compact')}), ('7-seat Van', {'cls': '=' + tok('class', '7-seat Van')}), ('Electric', {'cls': '=' + tok('class', 'Electric')}), ('Next week', {'start': '={today}+9'}))))

# 18 rental length mix -------------------------------------------------------------------------
M18 = 'EDATE(%s,1-{in:months})' % MS
def PD(col, plan): return 'SUMIFS(%s,%s,%s,%s,">="&%s,%s,"<="&{today}%s)' % (B(col), B('plan'), tok('plan', plan), B('start_date'), M18, B('start_date'), HOLDC)
def PB(plan): return 'COUNTIFS(%s,%s,%s,">="&%s,%s,"<="&{today}%s)' % (B('plan'), tok('plan', plan), B('start_date'), M18, B('start_date'), HOLDC)
TOT18 = '(%s+%s+%s)' % (PD('days', 'Daily'), PD('days', 'Weekly'), PD('days', 'Monthly'))
def CON(plan): return 'IFERROR(%s/%s-{in:turn}*%s/%s,0)' % (PD('total', plan), PD('days', plan), PB(plan), PD('days', plan))
tools.append(TOOL('length_mix', 'Rental Length Mix', 'Should I push weekly rentals',
    'Type the cost of turning a car around once; the share of rental days by plan, the average daily rate and the turnaround cost per rented day show which length earns more a day.', [
    I('months', 'Months to include', 3, 'int'), I('turn', 'Cost of one turnaround (cleaning and handover)', 18), I('floor', 'Lowest weekly contribution you accept, share of daily', 0.8, 'pct')], [
    O('Rented days, daily plans', 'int', PD('days', 'Daily')), O('Rented days, weekly plans', 'int', PD('days', 'Weekly')), O('Rented days, monthly plans', 'int', PD('days', 'Monthly')),
    O('Share of days, weekly plans', 'pct', 'IFERROR(%s/%s,0)' % (PD('days', 'Weekly'), TOT18)), O('Share of days, monthly plans', 'pct', 'IFERROR(%s/%s,0)' % (PD('days', 'Monthly'), TOT18)),
    O('Average daily rate, daily plans', 'money', 'IFERROR(%s/%s,0)' % (PD('total', 'Daily'), PD('days', 'Daily'))), O('Average daily rate, weekly plans', 'money', 'IFERROR(%s/%s,0)' % (PD('total', 'Weekly'), PD('days', 'Weekly'))),
    O('Average daily rate, monthly plans', 'money', 'IFERROR(%s/%s,0)' % (PD('total', 'Monthly'), PD('days', 'Monthly'))),
    O('Turnaround cost per rented day, daily plans', 'money', 'IFERROR({in:turn}*%s/%s,0)' % (PB('Daily'), PD('days', 'Daily'))), O('Turnaround cost per rented day, weekly plans', 'money', 'IFERROR({in:turn}*%s/%s,0)' % (PB('Weekly'), PD('days', 'Weekly'))),
    O('Contribution a day, daily plans', 'money', CON('Daily')), O('Contribution a day, weekly plans', 'money', CON('Weekly')),
    O('Verdict', 'text', 'IF(AND(%s>={in:floor}*%s,IFERROR(%s/%s,0)<0.35),%s,%s)' % (CON('Weekly'), CON('Daily'), PD('days', 'Weekly'), TOT18, v('Promote weekly'), v('Hold the mix')))],
    GR('What if', ('Dearer turnaround 30', {'turn': 30}), ('Cheaper turnaround 10', {'turn': 10}), ('Strict floor 95 percent', {'floor': 0.95}), ('Six months', {'months': 6}))))
assert len(tools) == 18, len(tools)
