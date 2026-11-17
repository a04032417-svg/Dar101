"""hf4 python model of the payoff cascade (used only to check the workbook formulas)."""
import math

def nper(r, p, b):
    if p <= b * r + 1e-9: return None
    return math.log(p / (p - b * r)) / math.log(1 + r)

def cascade(debts, order, X, W=0.0):
    """debts: list of dict(b, rate, m); order: list of indexes (priority). returns (months total, interest total, per-slot [(S, interest)])"""
    slots = [dict(debts[i]) for i in order]
    bc = 0.0
    for s in slots:
        s['b0'] = s['b']; s['b'] = max(0.0, s['b'] - max(0.0, W - bc)); bc += s['b0']
    sp = 0; mroll = 0.0; res = []
    for s in slots:
        r = max(s['rate'] / 12, 1e-9); b = s['b']; m = s['m']
        if b <= 0: res.append((sp, 0.0)); mroll += m; continue
        g = (1 + r) ** sp; bal0 = b * g - m * (g - 1) / r
        if bal0 <= 0.005:
            tm = math.ceil(nper(r, m, b) - 1e-12); tot = m * (tm - 1) + (b * (1 + r) ** (tm - 1) - m * ((1 + r) ** (tm - 1) - 1) / r) * (1 + r)
            res.append((sp, tot - b)); mroll += m; continue
        P = m + X + mroll
        n = nper(r, P, bal0)
        if n is None: return 999, 0.0, res + [(999, 0.0)]
        nf = math.ceil(n - 1e-12); S = sp + nf
        tot = m * sp + P * (nf - 1) + (bal0 * (1 + r) ** (nf - 1) - P * ((1 + r) ** (nf - 1) - 1) / r) * (1 + r)
        res.append((S, tot - b)); sp = S; mroll += m
    return max(s for s, _ in res), sum(i for _, i in res), res

def simulate(debts, order, X):
    bal = [debts[i]['b'] for i in order]; rt = [max(debts[i]['rate'] / 12, 1e-9) for i in order]; mn = [debts[i]['m'] for i in order]
    n = 0; interest = 0.0
    while any(b > 0.005 for b in bal) and n < 400:
        n += 1
        for k in range(len(bal)):
            if bal[k] > 0: ii = bal[k] * rt[k]; interest += ii; bal[k] += ii
        focus = next((k for k in range(len(bal)) if bal[k] > 0.005), None)
        # cleared slots ahead of the focus release their minimum to the focus
        for k in range(len(bal)):
            if bal[k] <= 0: continue
            pay = mn[k]
            if k == focus: pay = mn[k] + X + sum(mn[j] for j in range(k) if bal[j] <= 0.005)
            pay = min(pay, bal[k]); bal[k] -= pay
    return n, interest

if __name__ == '__main__':
    from hf_core import debt_rows
    D = [dict(b=d['balance'], rate=d['rate'], m=d['min_payment']) for d in debt_rows()]
    snow = sorted(range(5), key=lambda i: D[i]['b']); aval = sorted(range(5), key=lambda i: -D[i]['rate'])
    for nm, o in (('snow', snow), ('aval', aval)):
        print(nm, o, cascade(D, o, 300)[:2], simulate(D, o, 300))
    print(cascade(D, aval, 300)[2])
