"""Part 8 demo rows from wp_core (every row table whole; the aggregated tables are built from the full generator output)."""
import sys, os, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp8_lists import *

dd = to_date
def nb(d): return {k: v for k, v in d.items() if v not in ('', None, 0, 0.0)}
def mon(s): return iso(month_start_of(dd(s)))
def month_start_of(d): return D(d.year, d.month, 1)

TEAM = {t['team_id']: t for t in team}
PARTNER_PHONE = TEAM['WP-01']['phone']; PARTNER2_PHONE = TEAM['WP-02']['phone']
P1PARENT_PHONE = TEAM['WP-03']['phone']; P2PARENT_PHONE = TEAM['WP-04']['phone']
LEAD_PHONE = TEAM['WP-07']['phone']; FRIEND_PHONE = TEAM['WP-09']['phone']
HH = {h['household_id']: h for h in household_rows()}
VD = {v['vendor_id']: v for v in vendor_rows()}
ST = story()

DIYF = diy_rows(); SUPF = supply_rows(); ATTF = attire_rows(); GFT = gift_rows(); THK = thankyou_rows()


def diy_d():
    return [nb(dict(diy_id=x['diy_id'], project=key('project', x['project']), basis=key('basis', x['basis']), hours=x['hours'], buy_cost=x['buy_cost'],
                    status=key('dstatus', x['status']), start_by=x['start_by'], owner=key('owner', x['owner']))) for x in DIYF]


def supplies_d():
    return [nb(dict(supply_id=x['supply_id'], diy_id=x['diy_id'], project=key('project', x['project']), item=x['item'], basis=key('basis', x['basis']), qty_per=x['qty_per'],
                    unit_cost=x['unit_cost'], status=key('sstatus', x['status']), bought_on=x['bought_on'])) for x in SUPF]


N_SHOP = sum(1 for x in SUPF if x['status'] != 'Bought')
def shopping_d(): return [dict(rank=i) for i in range(1, N_SHOP + 1)]


def attire_d():
    out = []
    for a in ATTF:
        v = VD.get(a['vendor_id'], {})
        out.append(nb(dict(attire_id=a['attire_id'], item=a['item'], for_person=a['for_person'], kind=key('akind', a['kind']), vendor_id=a['vendor_id'], vendor=v.get('vendor', ''),
                           phone=v.get('phone', ''), cost=a['cost'], status=key('sstatus', a['status']), order_by=a['order_by'], in_budget=bool(a['in_budget']))))
        if not a['in_budget']: out[-1]['in_budget'] = False
    return out


CASH = [g for g in GFT if g['amount'] > 0]
_USE = ['b', 'b', 'b', 'h', 'b', 'h', 'h', 'b', 'h', 'n', 'h', 'n', 'n', 'b', 'h', 'n']
USE = {g['gift_id']: {'b': 'Wedding budget', 'h': 'Honeymoon fund', 'n': 'Not decided'}[_USE[i % len(_USE)]] for i, g in enumerate(CASH)}
VIA = {g['gift_id']: (i % 2 == 0) for i, g in enumerate(CASH)}


def gifts_d():
    out = []
    for g in GFT:
        h = HH[g['household_id']]
        cash = g['amount'] > 0
        r = nb(dict(gift_id=g['gift_id'], date=g['date'], month=mon(g['date']), household_id=g['household_id'], household=g['household'], event=key('gevent', g['event']),
                    kind=key('gkind', g['kind']), description=g['description'], amount=g['amount'], contact=h['contact'], phone=h['phone']))
        r['via_provider'] = bool(cash and VIA[g['gift_id']])
        if cash: r['cash_use'] = key('cuse', USE[g['gift_id']])
        out.append(r)
    return out


UNSENT = {'TY-028', 'TY-029'}   # written and waiting for a stamp: the demo shows written but not sent
def thanks_d():
    return [nb(dict(note_id=n['note_id'], gift_id=n['gift_id'], household=n['household'], written_on=n['written_on'], sent_on='' if n['note_id'] in UNSENT else n['sent_on'],
                    month=mon(n['written_on']), channel=key('tchannel', n['channel']))) for n in THK]


NOTED = {n['gift_id'] for n in THK}
N_BACKLOG = sum(1 for g in GFT if g['gift_id'] not in NOTED)
def backlog_d(): return [dict(rank=i) for i in range(1, N_BACKLOG + 1)]
def gift_events_d(): return [dict(row=r) for r in ['Engagement party', 'Shower', 'Sent early', 'Cash gifts', 'All gifts']]
def cash_d(): return [dict(rank=i) for i in range(1, len(CASH) + 1)]

FUNDF = funding_rows()
def _sum(src, status=None): return sum(f['amount'] for f in FUNDF if f['source'] == src and (status is None or f['status'] in status))
def fundlink_d():
    out = []
    for s in FUND_SOURCES:
        got = _sum(s, ('Received', 'Promised'))
        agreed = {'Partner 1 savings': 10200.0, 'Partner 2 savings': 10200.0, 'Partner 1 family': 8500.0, 'Partner 2 family': 5100.0, 'Cash gifts': 0.0}[s]
        out.append(dict(source=s, agreed=agreed))
    out.append(dict(source='All sources', agreed=float(TOTAL_BUDGET)))
    return out


def funding_d():
    return [dict(fund_id=f['fund_id'], source=key('source', f['source']), date=f['date'], amount=f['amount'], status=key('fstatus', f['status'])) for f in FUNDF]


def honeyfund_d():
    return [dict(hf_id=h['hf_id'], date=h['date'], month=h['month'], source=key('hsource', h['source']), amount=h['amount'], status=key('fstatus', h['status'])) for h in honeymoon_fund_rows()]


BUD = budget_rows()
def budget_d(): return [dict(line_id=b['line_id'], category=key('category', b['category']), planned=b['planned'], committed=b['committed'], paid=b['paid']) for b in BUD]
def final_d(): return [dict(category=key('category', b['category'])) for b in BUD]
def perguest_d(): return [dict(item=i) for i in ['Plan', 'Committed, the final cost so far', 'Paid so far', 'Still due', 'Plan not yet committed']]

SCH = payment_schedule_rows()
def balances_d():
    out = []
    for v in vendor_rows():
        if v['status'] != 'Booked': continue
        rows = [p for p in SCH if p['vendor_id'] == v['vendor_id']]
        paid = sum(p['amount_paid'] for p in rows)
        unpaid = sorted(p['due_date'] for p in rows if p['amount_paid'] < p['amount_due'])
        fin = [p['due_date'] for p in rows if p['kind'] == 'Final balance' and p['amount_paid'] < p['amount_due']]
        out.append(nb(dict(vendor_id=v['vendor_id'], vendor=v['vendor'], phone=v['phone'], contract_total=v['contract_total'], paid=paid, next_due=unpaid[0] if unpaid else '',
                           final_due=fin[0] if fin else '')))
    return out


_RS = {'RT-01': 'Arranged', 'RT-02': 'Arranged', 'RT-05': 'Arranged', 'RT-06': 'Arranged', 'RT-11': 'Done'}
def returns_d():
    out = []
    for r in return_rows():
        v = VD.get(r['vendor_id'], {})
        item, due = r['item'], r['due_date']
        if r['return_id'] == 'RT-11': item, due = 'Items borrowed for the shower, returned to family', ago(20)
        out.append(nb(dict(return_id=r['return_id'], item=item, vendor_id=r['vendor_id'], vendor=v.get('vendor', ''), phone=v.get('phone', ''), kind=key('rkind', r['kind']),
                           due_date=due, refund=r['refund'], status=key('rstatus', _RS.get(r['return_id'], 'Not due')))))
    return out


def paperwork_d():
    out = []
    for p in paperwork_rows():
        st = 'In progress' if p['item_id'] == 'PW-05' else p['status']
        out.append(dict(item_id=p['item_id'], item=p['item'], kind=key('pkind', p['kind']), optional=bool(p['optional']), due_date=p['due_date'], status=key('pstatus', st), owner=key('owner', p['owner'])))
    return out


_seen = []
for g in GFT:
    if g['household_id'] not in _seen: _seen.append(g['household_id'])
def ledger_d(): return [dict(household_id=h) for h in _seen]
def wrapup_d():
    return [dict(check=x) for x in ['Vendor balances still unpaid', 'Rentals and borrowed items not yet returned', 'Deposits and credits not yet received', 'Gifts without a thank-you note',
                                   'Notes written but not sent', 'Cash gifts with no plan for them', 'Marriage paperwork steps still open', 'Optional name change and record steps open',
                                   'DIY projects not done', 'Budget lines still over plan']]

if __name__ == '__main__':
    for n in ['diy_d', 'supplies_d', 'shopping_d', 'attire_d', 'gifts_d', 'thanks_d', 'backlog_d', 'cash_d', 'fundlink_d', 'funding_d', 'honeyfund_d', 'budget_d', 'balances_d', 'returns_d', 'paperwork_d', 'ledger_d']:
        print(n, len(globals()[n]()))
    print(balances_d()[:3]); print(fundlink_d()); print(gifts_d()[0])
    print(sum(g['amount'] for g in CASH), collections.Counter(USE.values()))
