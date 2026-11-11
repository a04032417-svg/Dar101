"""Property management suite — part 1: Rentals & Leasing (owners, properties, units, tenants, leases, rent roll, payments, deposits,
applicants, viewings, renewals, notices, payment plans, move-outs)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from lib import *

SUITE = 'fx-20261111-property-management'
YES, NO = LV('yesno', 'yes'), LV('yesno', 'no')

settings = [
    S('company', 'Your company name', 'text', 'Your Property Management'),
    S('grace', 'Grace days before rent is late', 'int', 5),
    S('late_pct', 'Late fee, share of the overdue rent', 'pct', 0.05),
    S('late_min', 'Smallest late fee', 'money', 25),
    S('expiring', 'Days before a lease ends to start the renewal', 'int', 90),
    S('escal', 'Usual yearly rent increase', 'pct', 0.03),
    S('rent_cap', 'Largest increase allowed at renewal', 'pct', 0.05),
    S('income_x', 'Monthly income needed, times the rent', 'num', 3),
    S('dep_days', 'Days to return a deposit after move-out', 'int', 30),
    S('min_score', 'Lowest screening score to approve', 'int', 70),
]
lists = [
    L('prop_type', 'Property Type', [('apt', 'Apartment building'), ('villas', 'Villa compound'), ('mixed', 'Mixed-use building'), ('retail', 'Retail strip'), ('houses', 'Single houses')]),
    L('unit_type', 'Unit Type', [('studio', 'Studio'), ('b1', '1 bedroom'), ('b2', '2 bedrooms'), ('b3', '3 bedrooms'), ('villa', 'Villa'), ('shop', 'Shop'), ('office', 'Office')]),
    L('unit_state', 'Unit Status', [('occupied', 'Occupied'), ('reserved', 'Reserved'), ('vacant', 'Vacant')]),
    L('freq', 'Rent Paid', [('monthly', 'Monthly'), ('quarterly', 'Every 3 months'), ('half', 'Every 6 months'), ('yearly', 'Yearly')]),
    L('lease_state', 'Lease Status', [('active', 'Active'), ('expiring', 'Ending soon'), ('upcoming', 'Starts later'), ('ended', 'Ended')]),
    L('charge_type', 'Charge Type', [('rent', 'Rent'), ('late', 'Late fee'), ('utility', 'Utilities'), ('service', 'Service charge'), ('parking', 'Parking'), ('repair', 'Damage repair'), ('other', 'Other')]),
    L('charge_state', 'Charge Status', [('paid', 'Paid'), ('partial', 'Part paid'), ('open', 'Not due yet'), ('overdue', 'Overdue')]),
    L('method', 'Payment Method', [('bank', 'Bank transfer'), ('card', 'Card'), ('cash', 'Cash'), ('cheque', 'Cheque'), ('online', 'Online payment')]),
    L('source', 'Lead Source', [('portal', 'Listing website'), ('site', 'Our website'), ('referral', 'Referral'), ('board', 'Sign board'), ('walkin', 'Walk-in'), ('repeat', 'Past tenant')]),
    L('app_state', 'Application Status', [('new', 'New enquiry'), ('viewing', 'Viewing booked'), ('applied', 'Applied'), ('approved', 'Approved'), ('declined', 'Declined'), ('signed', 'Lease signed'), ('lost', 'Lost')]),
    L('outcome', 'Viewing Outcome', [('booked', 'Booked'), ('liked', 'Interested'), ('applied', 'Applied'), ('no', 'Not interested'), ('noshow', 'Did not come')]),
    L('decision', 'Renewal Decision', [('pending', 'Waiting for answer'), ('renewed', 'Renewed'), ('talks', 'Negotiating'), ('leaving', 'Moving out')]),
    L('notice_type', 'Notice Type', [('late', 'Late rent'), ('entry', 'Entry for inspection or repair'), ('renewal', 'Renewal offer'), ('increase', 'Rent increase'), ('breach', 'Breach of lease'), ('vacate', 'Notice to vacate')]),
    L('via', 'Delivered By', [('wa', 'WhatsApp'), ('email', 'E-mail'), ('letter', 'Letter'), ('hand', 'By hand')]),
    L('held', 'Deposit Held By', [('trust', 'Our client account'), ('owner', 'The owner'), ('scheme', 'Deposit scheme')]),
    L('plan_state', 'Plan Status', [('on_track', 'On track'), ('behind', 'Behind'), ('done', 'Paid off')]),
    L('mo_state', 'Move-out Status', [('notice', 'Notice received'), ('inspected', 'Inspected'), ('settled', 'Deposit settled')]),
    L('flag', 'Alert', [('ok', 'OK'), ('overdue', 'Overdue'), ('due', 'Balance due'), ('expiring', 'Lease ending'), ('vacant', 'Vacant'), ('late_ret', 'Deposit return late'), ('follow', 'Follow up')]),
]
F = lambda k: LV('flag', k)

# ------------------------------------------------------------------ demo data: 5 buildings, 50 units, 14 months of rent
owners_d = [
    ('OW-01', 'Hassan Al-Mansour', '+971 50 210 3301', 'h.mansour@example.com', 'Bank transfer · account ending 4410'),
    ('OW-02', 'Clara Jensen', '+45 20 31 44 12', 'clara.jensen@example.com', 'Bank transfer · account ending 0921'),
    ('OW-03', 'Rahul Mehta', '+91 98 2004 7781', 'rahul.mehta@example.com', 'Bank transfer · account ending 3307'),
    ('OW-04', 'Sofia Romano', '+39 333 410 2290', 'sofia.romano@example.com', 'Bank transfer · account ending 7720'),
    ('OW-05', 'Haddad Family Trust', '+962 79 555 0182', 'trust@haddad.example.com', 'Bank transfer · account ending 5512'),
    ('OW-06', 'Mei Lin Chen', '+65 9123 4471', 'meilin.chen@example.com', 'Bank transfer · account ending 6604'),
    ('OW-07', 'Peter Novak', '+420 602 118 330', 'p.novak@example.com', 'Cheque by post'),
    ('OW-08', 'Layla Kassem', '+961 3 441 902', 'layla.kassem@example.com', 'Bank transfer · account ending 1187'),
    ('OW-09', 'Grupo Vega Inversiones', '+34 611 204 877', 'admin@vega.example.com', 'Bank transfer · account ending 9031'),
    ('OW-10', 'Daniel Okafor', '+234 803 555 1290', 'd.okafor@example.com', 'Bank transfer · account ending 2276'),
    ('OW-11', 'Yusuf Demir', '+90 532 640 1188', 'yusuf.demir@example.com', 'Bank transfer · account ending 4093'),
    ('OW-12', 'Anna Schmidt', '+49 151 2290 4410', 'anna.schmidt@example.com', 'Bank transfer · account ending 7348'),
]
props_d = [  # id, name, type, city, district, owner, built, units: list of (type, beds, m2, rent)
    ('PR-01', 'Palm Residence', 'apt', 'Dubai', 'Al Barsha', 'OW-01', 2016, [('studio', 0, 38, 1150)] * 3 + [('b1', 1, 62, 1650)] * 6 + [('b2', 2, 96, 2300)] * 3),
    ('PR-02', 'Cedar Court', 'apt', 'Dubai', 'JVC', 'OW-02', 2019, [('b1', 1, 58, 1500)] * 5 + [('b2', 2, 90, 2100)] * 4),
    ('PR-03', 'Marina Villas', 'villas', 'Dubai', 'Arabian Ranches', 'OW-03', 2012, [('villa', 4, 280, 5200)] * 4),
    ('PR-04', 'Old Town Shops', 'retail', 'Sharjah', 'Al Majaz', 'OW-04', 2008, [('shop', 0, 70, 2600)] * 4 + [('office', 0, 120, 3400)] * 2),
    ('PR-05', 'Harbor View', 'mixed', 'Sharjah', 'Al Khan', 'OW-05', 2021, [('b2', 2, 88, 1800)] * 3 + [('b3', 3, 130, 2600)] * 3),
    ('PR-06', 'Garden Terraces', 'apt', 'Abu Dhabi', 'Al Reem', 'OW-06', 2018, [('b1', 1, 64, 1700)] * 4 + [('b2', 2, 101, 2450)] * 3),
    ('PR-07', 'Oak House', 'houses', 'Ajman', 'Al Nuaimiya', 'OW-07', 2010, [('b3', 3, 160, 2200)] * 2),
    ('PR-08', 'Sunset Lofts', 'apt', 'Dubai', 'Business Bay', 'OW-08', 2020, [('studio', 0, 42, 1350)] * 4 + [('b1', 1, 66, 1900)] * 2),
    ('PR-09', 'Vega Business Center', 'mixed', 'Abu Dhabi', 'Khalidiya', 'OW-09', 2014, [('office', 0, 95, 3100)] * 3 + [('shop', 0, 60, 2300)] * 2),
    ('PR-10', 'Lagoon Townhouses', 'villas', 'Dubai', 'Damac Hills', 'OW-10', 2017, [('villa', 3, 210, 3900)] * 3),
    ('PR-11', 'Bosphorus Flats', 'apt', 'Sharjah', 'Al Nahda', 'OW-11', 2015, [('b1', 1, 60, 1300)] * 3 + [('b2', 2, 92, 1750)] * 2),
    ('PR-12', 'Linden Court', 'apt', 'Abu Dhabi', 'Al Raha', 'OW-12', 2022, [('b2', 2, 98, 2550)] * 3),
]
FIRST = ['Liam', 'Aisha', 'Mateo', 'Yuki', 'Noor', 'Daniel', 'Fatima', 'Lucas', 'Elena', 'Karim', 'Grace', 'Arjun', 'Mia', 'Tariq', 'Sara', 'Ivan',
         'Leila', 'Ethan', 'Hana', 'Omar', 'Chloe', 'Samir', 'Ana', 'Jonas', 'Rania', 'Victor', 'Maya', 'Bilal', 'Zoe', 'Hamza', 'Ines', 'Adam',
         'Lina', 'Marco', 'Dina', 'Felix', 'Salma', 'Ravi', 'Nadia', 'Paul', 'Yara', 'Kenji', 'Rosa', 'Ali', 'Emma', 'Tomas', 'Huda', 'Leo', 'Amira', 'Ben']
LAST = ['Walker', 'Rahman', 'Silva', 'Tanaka', 'Haddad', 'Novak', 'Khan', 'Moreau', 'Petrova', 'Aziz', 'Owens', 'Nair', 'Fischer', 'Saleh', 'Costa',
        'Ivanov', 'Farah', 'Brooks', 'Sato', 'Yousef', 'Martin', 'Qureshi', 'Lopez', 'Berg', 'Nasser', 'Dumas', 'Patel', 'Anwar', 'Clarke', 'Darwish',
        'Garcia', 'Kowalski', 'Hamdan', 'Bianchi', 'Saad', 'Wagner', 'Mourad', 'Iyer', 'Kassem', 'Reid', 'Sabbagh', 'Mori', 'Vega', 'Rizvi', 'Taylor',
        'Horvat', 'Jaber', 'Klein', 'Mansour', 'Cohen']

units, leases, tenants, charges, payments, deposits = [], [], [], [], [], []
ti = 0
for pid, pname, ptype, city, dist, own, built, ulist in props_d:
    for n, (ut, beds, m2, rent) in enumerate(ulist):
        uid = f'{pid[-2:]}-{101 + n if ut not in ("villa",) else n + 1:03d}'
        uid = f'U{pid[-2:]}{n + 1:02d}'
        unit_no = (f'{(n // 6) + 1}{(n % 6) + 1:02d}' if ut not in ('villa', 'shop', 'office') else ('V' if ut == 'villa' else 'S' if ut == 'shop' else 'O') + str(n + 1))
        mkt = round(rent * R.choice([1.0, 1.02, 1.04, 1.05, 1.08]) / 10) * 10
        units.append({'unit_id': uid, 'prop': pid, 'unit_no': unit_no, 'utype': ut, 'beds': beds, 'area': m2 + R.choice([-4, -2, 0, 0, 3, 5]), 'floor': str((n // 6) + 1) if ut not in ('villa',) else 'G', 'market': mkt})
        vacant = (pid, n) in {('PR-01', 3), ('PR-02', 7), ('PR-04', 5), ('PR-05', 6)}
        if vacant:  # an ended lease, the unit empty now
            tid = f'T-{1001 + ti}'; ti += 1
            st = add_months(month_start(13), 0); en = TODAY - dt.timedelta(days=R.choice([24, 41, 63, 88]))
            tenants.append({'tenant_id': tid, 'name': f'{FIRST[ti % 50]} {LAST[(ti * 7) % 50]}', 'phone': f'+971 55 4{ti:02d} 7{ti:03d}', 'email': f't{ti}@example.com', 'id_no': f'P{3200000 + ti * 37}', 'emergency': f'{FIRST[(ti + 9) % 50]} · +971 50 1{ti:02d} 22{ti:02d}'})
            leases.append({'lease_id': f'L-{2001 + len(leases)}', 'unit': uid, 'tenant': tid, 'signed': iso(st - dt.timedelta(days=12)), 'start': iso(st), 'end': iso(en), 'rent': rent, 'freq': 'monthly', 'deposit': rent, 'escal': 0.03, 'due_day': 1})
            continue
        tid = f'T-{1001 + ti}'; ti += 1
        tenants.append({'tenant_id': tid, 'name': f'{FIRST[ti % 50]} {LAST[(ti * 7) % 50]}', 'phone': f'+971 55 4{ti:02d} 7{ti:03d}', 'email': f't{ti}@example.com', 'id_no': f'P{3200000 + ti * 37}', 'emergency': f'{FIRST[(ti + 9) % 50]} · +971 50 1{ti:02d} 22{ti:02d}'})
        smonths = R.choice([3, 5, 7, 9, 11, 13, 13, 14, 14])
        st = month_start(smonths)
        en = add_months(st, 12) - dt.timedelta(days=1)
        if en < TODAY: en = add_months(st, 24) - dt.timedelta(days=1)
        freq = 'monthly' if ut not in ('shop', 'office', 'villa') else R.choice(['quarterly', 'monthly', 'yearly' if ut == 'villa' else 'quarterly'])
        per = {'monthly': 1, 'quarterly': 3, 'half': 6, 'yearly': 12}[freq]
        leases.append({'lease_id': f'L-{2001 + len(leases)}', 'unit': uid, 'tenant': tid, 'signed': iso(st - dt.timedelta(days=R.choice([9, 14, 21]))), 'start': iso(st), 'end': iso(en),
                       'rent': rent * per, 'freq': freq, 'deposit': rent * (2 if ut in ('shop', 'office', 'villa') else 1), 'escal': R.choice([0.03, 0.03, 0.04, 0.05]), 'due_day': 1})
        if smonths <= 5:  # the previous tenant left just before
            pt = f'T-{1001 + ti}'; ti += 1
            tenants.append({'tenant_id': pt, 'name': f'{FIRST[ti % 50]} {LAST[(ti * 7) % 50]}', 'phone': f'+971 56 2{ti:02d} 4{ti:03d}', 'email': f't{ti}@example.com', 'id_no': f'P{3300000 + ti * 41}', 'emergency': f'{FIRST[(ti + 13) % 50]} · +971 50 3{ti:02d} 61{ti:02d}'})
            pe = st - dt.timedelta(days=R.choice([6, 11, 18])); ps = add_months(dt.date(pe.year, pe.month, 1), -11)
            leases.append({'lease_id': f'L-{2001 + len(leases)}', 'unit': uid, 'tenant': pt, 'signed': iso(ps - dt.timedelta(days=14)), 'start': iso(ps), 'end': iso(pe),
                           'rent': round(rent * 0.97 / 10) * 10, 'freq': 'monthly', 'deposit': rent, 'escal': 0.03, 'due_day': 1})
# tenants with a payment habit: most on time, some late, a few in arrears
habit = {}
for k, l in enumerate(leases): habit[l['lease_id']] = 'arrears' if k % 11 == 4 else 'late' if k % 5 == 2 else 'ontime'
for l in leases:
    per = {'monthly': 1, 'quarterly': 3, 'half': 6, 'yearly': 12}[l['freq']]
    d = dt.date.fromisoformat(l['start']); end = dt.date.fromisoformat(l['end'])
    if end < month_start(13): continue
    while d <= min(end, TODAY):
        if d < month_start(13): d = add_months(d, per); continue
        cid = f'C-{5001 + len(charges)}'
        charges.append({'ch_id': cid, 'lease': l['lease_id'], 'due': iso(d), 'ctype': 'rent', 'amount': l['rent'], 'memo': 'Rent ' + d.strftime('%b %Y')})
        age = (TODAY - d).days
        h = habit[l['lease_id']]
        if age >= 0:
            if h == 'arrears' and age < 75: pass  # last two or three months unpaid
            elif h == 'arrears' and age < 110:
                payments.append({'pay_id': f'P-{8001 + len(payments)}', 'date': iso(d + dt.timedelta(days=R.choice([18, 25, 33]))), 'charge': cid, 'amount': round(l['rent'] * 0.5), 'method': R.choice(['bank', 'cash']), 'ref': f'TRX{700000 + len(payments) * 13}'})
            else:
                lag = R.choice([0, 1, 2, 3]) if h == 'ontime' else R.choice([4, 8, 12, 17, 26])
                pd_ = d + dt.timedelta(days=lag)
                if pd_ <= TODAY:
                    payments.append({'pay_id': f'P-{8001 + len(payments)}', 'date': iso(pd_), 'charge': cid, 'amount': l['rent'], 'method': R.choice(['bank', 'bank', 'bank', 'card', 'online', 'cheque', 'cash']), 'ref': f'TRX{700000 + len(payments) * 13}'})
                    if h == 'late' and lag > 5:
                        lf = max(25, round(l['rent'] * 0.05)); lid = f'C-{5001 + len(charges)}'
                        charges.append({'ch_id': lid, 'lease': l['lease_id'], 'due': iso(pd_), 'ctype': 'late', 'amount': lf, 'memo': 'Late fee ' + d.strftime('%b %Y')})
                        if R.random() < 0.7: payments.append({'pay_id': f'P-{8001 + len(payments)}', 'date': iso(pd_ + dt.timedelta(days=3)), 'charge': lid, 'amount': lf, 'method': 'bank', 'ref': f'TRX{700000 + len(payments) * 13}'})
        d = add_months(d, per)
    # utilities and parking on some leases
    if l['unit'].startswith('U01') and int(l['unit'][-2:]) % 3 == 0:
        for k in range(1, 4):
            cid = f'C-{5001 + len(charges)}'; amt = R.choice([85, 92, 110, 124])
            charges.append({'ch_id': cid, 'lease': l['lease_id'], 'due': iso(month_start(k) + dt.timedelta(days=14)), 'ctype': 'utility', 'amount': amt, 'memo': 'Water and power share'})
            if k > 1 or habit[l['lease_id']] == 'ontime': payments.append({'pay_id': f'P-{8001 + len(payments)}', 'date': iso(month_start(k) + dt.timedelta(days=19)), 'charge': cid, 'amount': amt, 'method': 'online', 'ref': f'TRX{700000 + len(payments) * 13}'})
charges.sort(key=lambda c: c['due']); payments.sort(key=lambda p: p['date'])
for i, c in enumerate(charges): pass
for l in leases:
    dep = {'dep_id': f'D-{l["lease_id"][2:]}', 'lease': l['lease_id'], 'received': l['signed'], 'amount': l['deposit'], 'held': R.choice(['trust', 'trust', 'scheme', 'owner'])}
    if dt.date.fromisoformat(l['end']) < TODAY:
        if l['unit'] in ('U0104', 'U0408'): dep.update({'deductions': 0})
        else:
            ded = R.choice([0, 0, 75, 140, 220, 310, 465, 580])
            dep.update({'returned_on': iso(dt.date.fromisoformat(l['end']) + dt.timedelta(days=R.choice([9, 14, 21, 26, 34]))), 'deductions': ded,
                        'reason': '' if not ded else R.choice(['Wall repainting', 'Broken blind and deep cleaning', 'Missing keys and lock change', 'Carpet cleaning', 'Unpaid water bill', 'Damaged kitchen cabinet door'])})
    deposits.append(dep)

ended = [l for l in leases if dt.date.fromisoformat(l['end']) < TODAY]
moveouts = [{'mo_id': f'M-{30 + i}', 'lease': l['lease_id'], 'notice_on': iso(dt.date.fromisoformat(l['end']) - dt.timedelta(days=30)), 'move_out': l['end'],
             'inspection': iso(dt.date.fromisoformat(l['end']) + dt.timedelta(days=1)), 'meter': f'E {41200 + i * 317} · W {880 + i * 41}', 'state': 'settled' if any(d.get('returned_on') for d in deposits if d['lease'] == l['lease_id']) else 'inspected'} for i, l in enumerate(ended)]
expiring = sorted([l for l in leases if 0 <= (dt.date.fromisoformat(l['end']) - TODAY).days <= 120], key=lambda l: l['end'])
renewals = []
for i, l in enumerate(expiring[:14]):
    renewals.append({'rn_id': f'RN-{40 + i}', 'lease': l['lease_id'], 'offer_on': iso(TODAY - dt.timedelta(days=R.choice([3, 8, 15, 22]))), 'proposed': round(l['rent'] * (1 + R.choice([0.03, 0.04, 0.05, 0.07])) / 5) * 5,
                     'decision': ['pending', 'renewed', 'talks', 'pending', 'leaving', 'renewed', 'pending', 'talks', 'renewed', 'pending', 'leaving', 'renewed', 'talks', 'pending'][i], 'new_end': iso(add_months(dt.date.fromisoformat(l['end']), 12))})
for r in renewals:
    if r['decision'] == 'leaving':
        l = next(x for x in leases if x['lease_id'] == r['lease'])
        moveouts.append({'mo_id': f'M-{30 + len(moveouts)}', 'lease': l['lease_id'], 'notice_on': iso(TODAY - dt.timedelta(days=4)), 'move_out': l['end'], 'inspection': l['end'], 'meter': '', 'state': 'notice'})
vac_units = [u['unit_id'] for u in units if not any(l['unit'] == u['unit_id'] and dt.date.fromisoformat(l['end']) >= TODAY for l in leases)]
apps, viewings = [], []
for i in range(26):
    u = vac_units[i % len(vac_units)] if i % 3 else R.choice([x['unit_id'] for x in units])
    st = ['new', 'viewing', 'applied', 'approved', 'declined', 'signed', 'lost'][i % 7]
    rent = next(x['market'] for x in units if x['unit_id'] == u)
    inc = round(rent * R.choice([2.4, 2.9, 3.2, 3.6, 4.1, 5.0]) / 50) * 50
    apps.append({'app_id': f'A-{601 + i}', 'created': ago(70 - i * 2), 'name': f'{FIRST[(i * 3 + 7) % 50]} {LAST[(i * 11 + 3) % 50]}', 'phone': f'+971 52 3{i:02d} 81{i:02d}', 'email': f'lead{i}@example.com',
                 'unit': u, 'income': inc, 'household': R.choice([1, 2, 2, 3, 4, 5]), 'move_in': ahead(R.choice([10, 20, 35, 50])), 'source': R.choice(['portal', 'portal', 'site', 'referral', 'board', 'walkin', 'repeat']),
                 'refs': R.choice(['yes', 'yes', 'no']), 'state': st})
    if st not in ('new',):
        viewings.append({'v_id': f'V-{901 + len(viewings)}', 'date': ago(66 - i * 2), 'time': R.choice(['10:00', '11:30', '16:00', '17:30', '18:15']), 'applicant': f'A-{601 + i}', 'unit': u, 'agent': R.choice(['Nadia', 'Marco', 'Yousef']),
                         'outcome': {'viewing': 'booked', 'applied': 'applied', 'approved': 'applied', 'declined': 'applied', 'signed': 'applied', 'lost': 'no'}[st], 'feedback': R.choice(['Liked the light', 'Wants parking', 'Price is high', 'Asked about pets', ''])})
for i in range(6):
    viewings.append({'v_id': f'V-{901 + len(viewings)}', 'date': ahead(i + 1), 'time': ['10:00', '12:00', '16:30', '17:00', '18:00', '11:00'][i], 'applicant': f'A-{601 + (i * 4) % 26}', 'unit': vac_units[i % len(vac_units)], 'agent': R.choice(['Nadia', 'Marco']), 'outcome': 'booked', 'feedback': ''})
arrears_t = [l['tenant'] for l in leases if habit[l['lease_id']] == 'arrears' and dt.date.fromisoformat(l['end']) >= TODAY]
notices = []
for i, t in enumerate(arrears_t): notices.append({'no_id': f'N-{70 + len(notices)}', 'date': ago(20 - i), 'tenant': t, 'ntype': 'late', 'via': ['wa', 'letter', 'email', 'hand'][i % 4], 'deadline': ahead(7 + i), 'response': R.choice(['Promised to pay on the 25th', 'Asked for a payment plan', ''])})
for i, r in enumerate(renewals[:5]): notices.append({'no_id': f'N-{70 + len(notices)}', 'date': r['offer_on'], 'tenant': next(l['tenant'] for l in leases if l['lease_id'] == r['lease']), 'ntype': 'renewal', 'via': R.choice(['email', 'wa']), 'deadline': iso(dt.date.fromisoformat(r['offer_on']) + dt.timedelta(days=30)), 'response': ''})
for i in range(4): notices.append({'no_id': f'N-{70 + len(notices)}', 'date': ago(9 - i * 2), 'tenant': tenants[i * 5]['tenant_id'], 'ntype': 'entry', 'via': 'wa', 'deadline': ahead(2 + i), 'response': 'Confirmed'})
plans = [{'pp_id': f'PP-{80 + i}', 'tenant': t, 'agreed': ago(25 - i * 4), 'total': 0, 'inst': 3, 'first_due': ahead(5 + i * 2)} for i, t in enumerate(arrears_t[:5])]
late_t = [l['tenant'] for l in leases if habit[l['lease_id']] == 'late']
for i, t in enumerate(late_t[:8]):  # older plans that were paid off
    agreed = TODAY - dt.timedelta(days=150 + i * 22); amt = next(l['rent'] for l in leases if l['tenant'] == t)
    plans.append({'pp_id': f'PP-{60 + i}', 'tenant': t, 'agreed': iso(agreed), 'total': amt, 'inst': R.choice([2, 3, 4]), 'first_due': iso(agreed + dt.timedelta(days=10))})
for p in plans[:5]:  # what was owed when agreed
    p['total'] = sum(c['amount'] for c in charges if next(l['tenant'] for l in leases if l['lease_id'] == c['lease']) == p['tenant'] and c['ctype'] == 'rent' and 30 < (TODAY - dt.date.fromisoformat(c['due'])).days < 75)

# ------------------------------------------------------------------ tables
LK = LOOK
tables = [
    T('owners', 'Owners', 'Owners', 'One row per owner you manage for: contact, how they are paid, and what their portfolio earns and owes today.', [
        C('owner_id', 'Owner ID', 'text', 10, required=True), C('name', 'Owner', 'text', 26, required=True), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
        C('payout', 'Payout details', 'text', 30),
        CALC('n_props', 'Properties', 'int', 'COUNTIFS({range:properties.owner},{col:owner_id})', 10),
        CALC('n_units', 'Units', 'int', 'COUNTIFS({range:units.owner},{col:owner_id})', 8),
        CALC('n_vacant', 'Vacant units', 'int', 'COUNTIFS({range:units.owner},{col:owner_id},{range:units.state},%s)' % LV('unit_state', 'vacant'), 9),
        CALC('roll', 'Monthly rent roll', 'money', 'SUMIFS({range:units.cur_rent},{range:units.owner},{col:owner_id})', 14, visual='bar'),
        CALC('collected', 'Collected, last 30 days', 'money', 'SUMIFS({range:payments.amount},{range:payments.owner},{col:owner_id},{range:payments.date},">="&({today}-29))', 14),
        CALC('arrears', 'Rent owed by tenants', 'money', 'SUMIFS({range:charges.balance},{range:charges.owner},{col:owner_id},{range:charges.state},%s)' % LV('charge_state', 'overdue'), 14)],
      [dict(owner_id=o[0], name=o[1], phone=o[2], email=o[3], payout=o[4]) for o in owners_d], 200, [A('arrears', '> 0', 'warn'), A('n_vacant', '> 0', 'warn')]),
    T('properties', 'Properties', 'Properties', 'One row per building or compound: where it is, whose it is, and its live occupancy, rent roll and arrears.', [
        C('prop_id', 'Property ID', 'text', 10, required=True), C('name', 'Property', 'text', 22, required=True), LST('ptype', 'Type', 'prop_type', 18),
        C('city', 'City', 'text', 12), C('district', 'District', 'text', 16), REF('owner', 'Owner ID', 'owners.owner_id', 10), C('built', 'Year built', 'int', 9),
        CALC('owner_name', 'Owner', 'text', LK('owners.name', 'owners.owner_id', 'owner'), 24),
        CALC('n_units', 'Units', 'int', 'COUNTIFS({range:units.prop},{col:prop_id})', 7),
        CALC('n_occ', 'Occupied', 'int', 'COUNTIFS({range:units.prop},{col:prop_id},{range:units.state},%s)' % LV('unit_state', 'occupied'), 9),
        CALC('occ', 'Occupancy', 'pct', 'IFERROR({col:n_occ}/{col:n_units},"")', 10, visual='up'),
        CALC('roll', 'Monthly rent roll', 'money', 'SUMIFS({range:units.cur_rent},{range:units.prop},{col:prop_id})', 14),
        CALC('potential', 'Rent if full at market', 'money', 'SUMIFS({range:units.market},{range:units.prop},{col:prop_id})', 14),
        CALC('loss', 'Rent lost to vacancy and below-market', 'money', 'IF({col:potential}="","",{col:potential}-{col:roll})', 15, visual='down'),
        CALC('arrears', 'Overdue rent', 'money', 'SUMIFS({range:charges.balance},{range:charges.prop},{col:prop_id},{range:charges.state},%s)' % LV('charge_state', 'overdue'), 12)],
      [dict(prop_id=p[0], name=p[1], ptype=p[2], city=p[3], district=p[4], owner=p[5], built=p[6]) for p in props_d], 200, [A('occ', '< 0.9', 'warn'), A('arrears', '> 0', 'bad')]),
    T('units', 'Units', 'Units', 'Every flat, villa, shop or office. Status, tenant, current rent, rent per square metre and the gap to market fill in from the leases.', [
        C('unit_id', 'Unit ID', 'text', 9, required=True), REF('prop', 'Property ID', 'properties.prop_id', 10), C('unit_no', 'Unit no.', 'text', 8), LST('utype', 'Type', 'unit_type', 12),
        C('beds', 'Bedrooms', 'int', 9), C('area', 'Area m²', 'num', 8), C('floor', 'Floor', 'text', 6), C('market', 'Market rent / month', 'money', 12),
        CALC('owner', 'Owner ID', 'text', LK('properties.owner', 'properties.prop_id', 'prop'), 9),
        CALC('lease_now', 'Current lease', 'text', 'IFERROR(INDEX({range:leases.lease_id},MATCH({col:unit_id},{range:leases.unit_on},0)),"")', 10),
        CALC('state', 'Status', 'text', 'IF({col:unit_id}="","",IF({col:lease_now}<>"",%s,IF(COUNTIFS({range:leases.unit},{col:unit_id},{range:leases.state},%s)>0,%s,%s)))' % (LV('unit_state', 'occupied'), LV('lease_state', 'upcoming'), LV('unit_state', 'reserved'), LV('unit_state', 'vacant')), 10),
        CALC('tenant', 'Tenant', 'text', LK('leases.tenant_name', 'leases.lease_id', 'lease_now'), 24),
        CALC('cur_rent', 'Rent / month', 'money', 'IF({col:lease_now}="",0,%s)' % LK('leases.monthly', 'leases.lease_id', 'lease_now'), 11),
        CALC('lease_end', 'Lease ends', 'date', LK('leases.end', 'leases.lease_id', 'lease_now'), 11),
        CALC('per_m2', 'Rent per m²', 'num', 'IFERROR(IF({col:cur_rent}>0,{col:cur_rent},{col:market})/{col:area},"")', 9),
        CALC('gap', 'Below market by', 'money', 'IF(OR({col:cur_rent}=0,{col:market}=""),"",MAX(0,{col:market}-{col:cur_rent}))', 11),
        CALC('last_end', 'Last lease ended', 'date', 'IF({col:state}=%s,IFERROR(1/(1/SUMPRODUCT(MAX(({range:leases.unit}={col:unit_id})*({range:leases.end}<{today})*{range:leases.end}))),""),"")' % LV('unit_state', 'vacant'), 11),
        CALC('days_vacant', 'Days vacant', 'int', 'IF(ISNUMBER({col:last_end}),{today}-{col:last_end},"")', 9),
        CALC('lost', 'Rent lost while vacant', 'money', 'IF(ISNUMBER({col:days_vacant}),ROUND({col:days_vacant}*{col:market}*12/365,0),"")', 12)],
      units, 600, [A('state', '= %s' % LV('unit_state', 'vacant'), 'bad'), A('gap', '> 0', 'warn')]),
    T('tenants', 'Tenants', 'Tenants', 'One row per tenant: contact, ID, emergency contact, current unit and the money position — billed, paid, balance, overdue and on-time record.', [
        C('tenant_id', 'Tenant ID', 'text', 9, required=True), C('name', 'Tenant', 'text', 22, required=True), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 22),
        C('id_no', 'ID or passport no.', 'text', 14), C('emergency', 'Emergency contact', 'text', 26),
        CALC('lease_now', 'Current lease', 'text', 'IFERROR(INDEX({range:leases.lease_id},MATCH({col:tenant_id},{range:leases.tenant_on},0)),"")', 10),
        CALC('unit', 'Unit', 'text', LK('leases.unit', 'leases.lease_id', 'lease_now'), 8),
        CALC('billed', 'Billed', 'money', 'SUMIFS({range:charges.amount},{range:charges.tenant},{col:tenant_id})', 11),
        CALC('paid', 'Paid', 'money', 'SUMIFS({range:payments.amount},{range:payments.tenant},{col:tenant_id})', 11),
        CALC('balance', 'Balance', 'money', 'IF({col:tenant_id}="","",{col:billed}-{col:paid})', 11, visual='down'),
        CALC('overdue', 'Overdue', 'money', 'SUMIFS({range:charges.balance},{range:charges.tenant},{col:tenant_id},{range:charges.state},%s)' % LV('charge_state', 'overdue'), 11),
        CALC('oldest', 'Days the oldest debt is late', 'int', 'IF({col:overdue}>0,SUMPRODUCT(MAX(({range:charges.tenant}={col:tenant_id})*({range:charges.state}=%s)*({today}-{range:charges.due}))),"")' % LV('charge_state', 'overdue'), 11),
        CALC('on_time', 'Paid on time', 'pct', 'IFERROR(COUNTIFS({range:charges.tenant},{col:tenant_id},{range:charges.on_time},%s)/(COUNTIFS({range:charges.tenant},{col:tenant_id},{range:charges.on_time},%s)+COUNTIFS({range:charges.tenant},{col:tenant_id},{range:charges.on_time},%s)),"")' % (YES, YES, NO), 10, visual='up'),
        CALC('flag', 'Alert', 'text', 'IF({col:tenant_id}="","",IF({col:overdue}>0,%s,IF({col:balance}>0,%s,%s)))' % (F('overdue'), F('due'), F('ok')), 10)],
      tenants, 600, [A('flag', '= %s' % F('overdue'), 'bad'), A('on_time', '< 0.8', 'warn')]),
    T('leases', 'Leases', 'Leases', 'One row per lease: unit, tenant, dates, rent and how often it is paid, deposit and yearly increase. Status, days left and balance work themselves out.', [
        C('lease_id', 'Lease ID', 'text', 9, required=True), REF('unit', 'Unit ID', 'units.unit_id', 9), REF('tenant', 'Tenant ID', 'tenants.tenant_id', 9),
        C('signed', 'Signed on', 'date', 11), C('start', 'Starts', 'date', 11), C('end', 'Ends', 'date', 11), C('rent', 'Rent per payment', 'money', 11),
        LST('freq', 'Paid', 'freq', 13), C('deposit', 'Deposit', 'money', 10), C('escal', 'Yearly increase', 'pct', 9), C('due_day', 'Due day of month', 'int', 8),
        CALC('tenant_name', 'Tenant', 'text', LK('tenants.name', 'tenants.tenant_id', 'tenant'), 24),
        CALC('phone', 'Phone', 'text', LK('tenants.phone', 'tenants.tenant_id', 'tenant'), 18),
        CALC('prop', 'Property ID', 'text', LK('units.prop', 'units.unit_id', 'unit'), 9),
        CALC('monthly', 'Rent / month', 'money', 'IF({col:rent}="","",ROUND({col:rent}/IF({col:freq}=%s,3,IF({col:freq}=%s,6,IF({col:freq}=%s,12,1))),2))' % (LV('freq', 'quarterly'), LV('freq', 'half'), LV('freq', 'yearly')), 11),
        CALC('state', 'Status', 'text', 'IF({col:start}="","",IF({col:start}>{today},%s,IF({col:end}<{today},%s,IF({col:end}-{today}<={set:expiring},%s,%s))))' % (LV('lease_state', 'upcoming'), LV('lease_state', 'ended'), LV('lease_state', 'expiring'), LV('lease_state', 'active')), 11),
        CALC('unit_on', 'Unit, if running today', 'text', 'IF(AND({col:start}<>"",{col:start}<={today},{col:end}>={today}),{col:unit},"")', 9),
        CALC('tenant_on', 'Tenant, if running today', 'text', 'IF(AND({col:start}<>"",{col:start}<={today},{col:end}>={today}),{col:tenant},"")', 9),
        CALC('days_left', 'Days left', 'int', 'IF({col:end}="","",MAX(0,{col:end}-{today}))', 8),
        CALC('balance', 'Balance', 'money', 'SUMIFS({range:charges.balance},{range:charges.lease},{col:lease_id})', 11),
        CALC('next_rent', 'Rent after the yearly increase', 'money', 'IF({col:rent}="","",ROUND({col:rent}*(1+{col:escal}),0))', 12)],
      leases, 600, [A('state', '= %s' % LV('lease_state', 'expiring'), 'warn'), A('balance', '> 0', 'bad')]),
    T('charges', 'Rent Roll', 'Rent roll and charges', 'Every amount a tenant owes: rent for each period, late fees, utilities, service charges. Paid, balance, days late and on-time status are worked out from Payments.', [
        C('ch_id', 'Charge ID', 'text', 9, required=True), REF('lease', 'Lease ID', 'leases.lease_id', 9), C('due', 'Due date', 'date', 11), LST('ctype', 'Type', 'charge_type', 13),
        C('amount', 'Amount', 'money', 11), C('memo', 'Description', 'text', 20),
        CALC('tenant', 'Tenant ID', 'text', LK('leases.tenant', 'leases.lease_id', 'lease'), 24),
        CALC('name', 'Tenant', 'text', LK('tenants.name', 'tenants.tenant_id', 'tenant'), 24),
        CALC('phone', 'Phone', 'text', LK('tenants.phone', 'tenants.tenant_id', 'tenant'), 18),
        CALC('unit', 'Unit ID', 'text', LK('leases.unit', 'leases.lease_id', 'lease'), 8),
        CALC('prop', 'Property ID', 'text', LK('units.prop', 'units.unit_id', 'unit'), 9),
        CALC('owner', 'Owner ID', 'text', LK('units.owner', 'units.unit_id', 'unit'), 9),
        CALC('paid', 'Paid', 'money', 'SUMIFS({range:payments.amount},{range:payments.charge},{col:ch_id})', 10),
        CALC('balance', 'Balance', 'money', 'IF({col:amount}="","",{col:amount}-{col:paid})', 10, visual='down'),
        CALC('last_paid', 'Last paid on', 'date', 'IF({col:paid}=0,"",SUMPRODUCT(MAX(({range:payments.charge}={col:ch_id})*{range:payments.date})))', 11),
        CALC('days_late', 'Days late', 'int', 'IF({col:due}="","",IF({col:balance}>0,MAX(0,{today}-{col:due}),IF({col:last_paid}="",0,MAX(0,{col:last_paid}-{col:due}))))', 8),
        CALC('state', 'Status', 'text', 'IF({col:amount}="","",IF({col:balance}<=0,%s,IF({today}-{col:due}>{set:grace},%s,IF({col:paid}>0,%s,%s))))' % (LV('charge_state', 'paid'), LV('charge_state', 'overdue'), LV('charge_state', 'partial'), LV('charge_state', 'open')), 10),
        CALC('on_time', 'Paid on time', 'text', 'IF({col:amount}="","",IF({col:balance}<=0,IF({col:days_late}<={set:grace},%s,%s),IF({today}-{col:due}>{set:grace},%s,"")))' % (YES, NO, NO), 9),
        CALC('fee', 'Late fee if charged now', 'money', 'IF(AND({col:ctype}=%s,{col:state}=%s),ROUND(MAX({set:late_min},{col:balance}*{set:late_pct}),0),0)' % (LV('charge_type', 'rent'), LV('charge_state', 'overdue')), 11)],
      charges, 1500, [A('state', '= %s' % LV('charge_state', 'overdue'), 'bad'), A('state', '= %s' % LV('charge_state', 'partial'), 'warn')]),
    T('payments', 'Payments', 'Payments received', 'Every payment, linked to the charge it settles. Tenant, unit, property and owner fill in by themselves, so owner statements and the dashboard stay right.', [
        C('pay_id', 'Payment ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('charge', 'Charge ID', 'charges.ch_id', 9), C('amount', 'Amount', 'money', 11),
        LST('method', 'Method', 'method', 14), C('ref', 'Reference', 'text', 13),
        CALC('tenant', 'Tenant ID', 'text', LK('charges.tenant', 'charges.ch_id', 'charge'), 24),
        CALC('name', 'Tenant', 'text', LK('charges.name', 'charges.ch_id', 'charge'), 24),
        CALC('phone', 'Phone', 'text', LK('charges.phone', 'charges.ch_id', 'charge'), 18),
        CALC('unit', 'Unit ID', 'text', LK('charges.unit', 'charges.ch_id', 'charge'), 8),
        CALC('prop', 'Property ID', 'text', LK('charges.prop', 'charges.ch_id', 'charge'), 9),
        CALC('owner', 'Owner ID', 'text', LK('charges.owner', 'charges.ch_id', 'charge'), 9),
        CALC('for_what', 'For', 'text', LK('charges.memo', 'charges.ch_id', 'charge'), 18)],
      payments, 1500),
    T('deposits', 'Deposits', 'Security deposits', 'Every deposit held: who holds it, when it came in, deductions with their reason, and the date it must be returned after move-out.', [
        C('dep_id', 'Deposit ID', 'text', 9, required=True), REF('lease', 'Lease ID', 'leases.lease_id', 9), C('received', 'Received', 'date', 11), C('amount', 'Amount', 'money', 10),
        LST('held', 'Held by', 'held', 17), C('returned_on', 'Returned on', 'date', 11), C('deductions', 'Deductions', 'money', 10), C('reason', 'Reason for deductions', 'text', 22),
        CALC('tenant', 'Tenant', 'text', LK('leases.tenant_name', 'leases.lease_id', 'lease'), 24),
        CALC('lease_end', 'Lease ended', 'date', 'IF(%s<{today},%s,"")' % (LK('leases.end', 'leases.lease_id', 'lease'), LK('leases.end', 'leases.lease_id', 'lease')), 11),
        CALC('due_back', 'Return by', 'date', 'IF({col:lease_end}="","",{col:lease_end}+{set:dep_days})', 11),
        CALC('refund', 'Refund', 'money', 'IF({col:amount}="","",{col:amount}-IF({col:deductions}="",0,{col:deductions}))', 10),
        CALC('flag', 'Alert', 'text', 'IF({col:dep_id}="","",IF(AND({col:due_back}<>"",{col:returned_on}="",{col:due_back}<{today}),%s,IF(AND({col:lease_end}<>"",{col:returned_on}=""),%s,%s)))' % (F('late_ret'), F('follow'), F('ok')), 12)],
      deposits, 600, [A('flag', '= %s' % F('late_ret'), 'bad'), A('flag', '= %s' % F('follow'), 'warn')]),
    T('applicants', 'Applicants', 'Applicants and enquiries', 'Every enquiry from first call to signed lease: the unit wanted, income, household, references and a screening score against your rules.', [
        C('app_id', 'Applicant ID', 'text', 10, required=True), C('created', 'Enquiry date', 'date', 11), C('name', 'Name', 'text', 20, required=True), C('phone', 'Phone', 'text', 18),
        C('email', 'E-mail', 'text', 20), REF('unit', 'Unit wanted', 'units.unit_id', 9), C('income', 'Monthly income', 'money', 11), C('household', 'People', 'int', 7),
        C('move_in', 'Wants to move in', 'date', 11), LST('source', 'Came from', 'source', 14), LST('refs', 'References checked', 'yesno', 10), LST('state', 'Stage', 'app_state', 14),
        CALC('rent', 'Unit rent', 'money', LK('units.market', 'units.unit_id', 'unit'), 10),
        CALC('ratio', 'Income ÷ rent', 'num', 'IFERROR(ROUND({col:income}/{col:rent},2),"")', 9),
        CALC('score', 'Screening score', 'int', 'IF({col:name}="","",MIN(100,ROUND(IFERROR(MIN({col:ratio}/{set:income_x},1.2),0)*60,0)+IF({col:refs}=%s,25,0)+IF({col:household}<=MAX(2,%s*2),15,5)))' % (YES, LK('units.beds', 'units.unit_id', 'unit')), 9, visual='up'),
        CALC('verdict', 'Meets your rules', 'text', 'IF({col:score}="","",IF({col:score}>={set:min_score},%s,%s))' % (YES, NO), 10),
        CALC('days', 'Days open', 'int', 'IF({col:created}="","",{today}-{col:created})', 8)],
      apps, 800, [A('verdict', '= %s' % NO, 'warn'), A('score', '>= {set:min_score}', 'good')]),
    T('viewings', 'Viewings', 'Viewings', 'Every viewing booked: day, time, unit, who shows it and what the applicant thought. Upcoming viewings come first on the dashboard.', [
        C('v_id', 'Viewing ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('time', 'Time', 'time', 7), REF('applicant', 'Applicant ID', 'applicants.app_id', 10),
        REF('unit', 'Unit ID', 'units.unit_id', 8), C('agent', 'Shown by', 'text', 12), LST('outcome', 'Outcome', 'outcome', 13), C('feedback', 'Feedback', 'text', 22),
        CALC('name', 'Applicant', 'text', LK('applicants.name', 'applicants.app_id', 'applicant'), 24),
        CALC('phone', 'Phone', 'text', LK('applicants.phone', 'applicants.app_id', 'applicant'), 18),
        CALC('prop', 'Property', 'text', LK('properties.name', 'properties.prop_id', 'prop_id'), 16),
        CALC('prop_id', 'Property ID', 'text', LK('units.prop', 'units.unit_id', 'unit'), 9),
        CALC('when', 'In days', 'int', 'IF({col:date}="","",{col:date}-{today})', 7)],
      viewings, 800, [A('when', '>= 0', 'good')]),
    T('renewals', 'Renewals', 'Lease renewals', 'Every lease coming up for renewal: the offer, the change against today\'s rent, whether it is inside your cap, and the tenant\'s answer.', [
        C('rn_id', 'Renewal ID', 'text', 9, required=True), REF('lease', 'Lease ID', 'leases.lease_id', 9), C('offer_on', 'Offer sent', 'date', 11), C('proposed', 'Proposed rent per payment', 'money', 12),
        LST('decision', 'Answer', 'decision', 15), C('new_end', 'New end date', 'date', 11),
        CALC('tenant', 'Tenant', 'text', LK('leases.tenant_name', 'leases.lease_id', 'lease'), 24),
        CALC('phone', 'Phone', 'text', LK('leases.phone', 'leases.lease_id', 'lease'), 18),
        CALC('unit', 'Unit ID', 'text', LK('leases.unit', 'leases.lease_id', 'lease'), 8),
        CALC('end', 'Lease ends', 'date', LK('leases.end', 'leases.lease_id', 'lease'), 11),
        CALC('current', 'Current rent per payment', 'money', LK('leases.rent', 'leases.lease_id', 'lease'), 12),
        CALC('change', 'Change', 'pct', 'IFERROR({col:proposed}/{col:current}-1,"")', 8),
        CALC('in_cap', 'Within your cap', 'text', 'IF({col:change}="","",IF({col:change}<={set:rent_cap},%s,%s))' % (YES, NO), 9),
        CALC('days_left', 'Days to lease end', 'int', 'IF({col:end}="","",{col:end}-{today})', 9)],
      renewals, 400, [A('in_cap', '= %s' % NO, 'bad'), A('decision', '= %s' % LV('decision', 'leaving'), 'warn')]),
    T('notices', 'Notices', 'Notices log', 'Every formal notice served: late rent, entry, renewal, rent increase, breach, notice to vacate — how it was delivered, the deadline and the answer.', [
        C('no_id', 'Notice ID', 'text', 9, required=True), C('date', 'Served on', 'date', 11), REF('tenant', 'Tenant ID', 'tenants.tenant_id', 9), LST('ntype', 'Notice', 'notice_type', 20),
        LST('via', 'Delivered by', 'via', 12), C('deadline', 'Deadline', 'date', 11), C('response', 'Tenant\'s answer', 'text', 24),
        CALC('name', 'Tenant', 'text', LK('tenants.name', 'tenants.tenant_id', 'tenant'), 24),
        CALC('phone', 'Phone', 'text', LK('tenants.phone', 'tenants.tenant_id', 'tenant'), 18),
        CALC('unit', 'Unit ID', 'text', LK('tenants.unit', 'tenants.tenant_id', 'tenant'), 8),
        CALC('days', 'Days to deadline', 'int', 'IF({col:deadline}="","",{col:deadline}-{today})', 9)],
      notices, 400, [A('days', '< 0', 'bad'), A('days', '<= 3', 'warn')]),
    T('plans', 'Payment Plans', 'Payment plans for arrears', 'An agreed plan to clear what a tenant owes: total, instalments, first due date, what has been paid since, and whether the plan is on track.', [
        C('pp_id', 'Plan ID', 'text', 8, required=True), REF('tenant', 'Tenant ID', 'tenants.tenant_id', 9), C('agreed', 'Agreed on', 'date', 11), C('total', 'Amount owed', 'money', 11),
        C('inst', 'Instalments', 'int', 9), C('first_due', 'First instalment due', 'date', 11),
        CALC('name', 'Tenant', 'text', LK('tenants.name', 'tenants.tenant_id', 'tenant'), 24),
        CALC('phone', 'Phone', 'text', LK('tenants.phone', 'tenants.tenant_id', 'tenant'), 18),
        CALC('each', 'Each instalment', 'money', 'IFERROR(ROUND({col:total}/{col:inst},2),"")', 11),
        CALC('paid', 'Paid since agreed', 'money', 'IF({col:agreed}="","",SUMIFS({range:payments.amount},{range:payments.tenant},{col:tenant},{range:payments.date},">="&{col:agreed}))', 11),
        CALC('left', 'Still owed', 'money', 'IF({col:total}="","",MAX(0,{col:total}-{col:paid}))', 10),
        CALC('due_now', 'Should have paid by today', 'money', 'IF({col:first_due}="","",IF({today}<{col:first_due},0,MIN({col:total},({col:each})*(1+INT(({today}-{col:first_due})/30)))))', 12),
        CALC('state', 'Status', 'text', 'IF({col:total}="","",IF({col:left}=0,%s,IF({col:paid}>={col:due_now},%s,%s)))' % (LV('plan_state', 'done'), LV('plan_state', 'on_track'), LV('plan_state', 'behind')), 10)],
      plans, 200, [A('state', '= %s' % LV('plan_state', 'behind'), 'bad')]),
    T('moveouts', 'Move-outs', 'Move-outs', 'Every tenant leaving: notice date, move-out day, inspection, final meter readings and the deposit settlement status.', [
        C('mo_id', 'Move-out ID', 'text', 9, required=True), REF('lease', 'Lease ID', 'leases.lease_id', 9), C('notice_on', 'Notice received', 'date', 11), C('move_out', 'Move-out day', 'date', 11),
        C('inspection', 'Inspection', 'date', 11), C('meter', 'Final meter readings', 'text', 18), LST('state', 'Stage', 'mo_state', 15),
        CALC('tenant', 'Tenant', 'text', LK('leases.tenant_name', 'leases.lease_id', 'lease'), 24),
        CALC('phone', 'Phone', 'text', LK('leases.phone', 'leases.lease_id', 'lease'), 18),
        CALC('unit', 'Unit ID', 'text', LK('leases.unit', 'leases.lease_id', 'lease'), 8),
        CALC('owed', 'Rent still owed', 'money', LK('leases.balance', 'leases.lease_id', 'lease'), 11),
        CALC('deposit', 'Deposit held', 'money', 'SUMIFS({range:deposits.amount},{range:deposits.lease},{col:lease})', 10),
        CALC('return_by', 'Return deposit by', 'date', 'IF({col:move_out}="","",{col:move_out}+{set:dep_days})', 11)],
      moveouts, 300, [A('owed', '> 0', 'bad')]),
]

# ------------------------------------------------------------------ tools
tools = [
    TOOL('prorate', 'Prorated Rent', 'First or last month\'s rent for part of a month', 'Type the monthly rent and the move-in (or move-out) date.', [
        IN('rent', 'Monthly rent', 'money', 2300), IN('day', 'Move-in date', 'date', ahead(9)), IN('move_out', 'This is a move-out date (1 = yes)', 'int', 0)], [
        OUT('Days in that month', 'int', 'DAY(EOMONTH({in:day},0))'),
        OUT('Days charged', 'int', 'IF({in:move_out}=1,DAY({in:day}),DAY(EOMONTH({in:day},0))-DAY({in:day})+1)'),
        OUT('Rent per day', 'money', 'ROUND({in:rent}/DAY(EOMONTH({in:day},0)),2)'),
        OUT('Rent for the part month', 'money', 'ROUND({in:rent}*IF({in:move_out}=1,DAY({in:day}),DAY(EOMONTH({in:day},0))-DAY({in:day})+1)/DAY(EOMONTH({in:day},0)),2)'),
        OUT('Rent by the yearly method (365 days)', 'money', 'ROUND({in:rent}*12/365*IF({in:move_out}=1,DAY({in:day}),DAY(EOMONTH({in:day},0))-DAY({in:day})+1),2)')]),
    TOOL('latefee', 'Late Fee Calculator', 'What a late payer owes today', 'Type the overdue amount, the due date and the day of payment; your grace days and fee come from Start.', [
        IN('owed', 'Overdue rent', 'money', 2100), IN('due', 'Due date', 'date', ago(19)), IN('paid_on', 'Payment day', 'date', iso(TODAY)), IN('daily', 'Extra fee per day after grace (0 if none)', 'money', 0)], [
        OUT('Days late', 'int', 'MAX(0,{in:paid_on}-{in:due})'),
        OUT('Days late after grace', 'int', 'MAX(0,{in:paid_on}-{in:due}-{set:grace})'),
        OUT('Late fee', 'money', 'IF({in:paid_on}-{in:due}>{set:grace},ROUND(MAX({set:late_min},{in:owed}*{set:late_pct})+{in:daily}*MAX(0,{in:paid_on}-{in:due}-{set:grace}),2),0)'),
        OUT('Total to collect', 'money', '{in:owed}+IF({in:paid_on}-{in:due}>{set:grace},ROUND(MAX({set:late_min},{in:owed}*{set:late_pct})+{in:daily}*MAX(0,{in:paid_on}-{in:due}-{set:grace}),2),0)')]),
    TOOL('increase', 'Rent Increase Calculator', 'A fair, defensible renewal rent', 'Type the current rent, the market rent for the unit and inflation; your cap comes from Start.', [
        IN('current', 'Current monthly rent', 'money', 1650), IN('market', 'Market rent for this unit', 'money', 1820), IN('cpi', 'Inflation over the last year', 'pct', 0.034), IN('good', 'Good tenant discount', 'pct', 0.01)], [
        OUT('Rent by inflation', 'money', 'ROUND({in:current}*(1+{in:cpi}),0)'),
        OUT('Gap to market', 'pct', 'IFERROR({in:market}/{in:current}-1,0)'),
        OUT('Increase you can defend', 'pct', 'MAX(0,MIN({set:rent_cap},MAX({in:cpi},IFERROR({in:market}/{in:current}-1,0))-{in:good}))'),
        OUT('Proposed monthly rent', 'money', 'ROUND({in:current}*(1+MAX(0,MIN({set:rent_cap},MAX({in:cpi},IFERROR({in:market}/{in:current}-1,0))-{in:good}))),0)'),
        OUT('Extra rent over 12 months', 'money', '12*(ROUND({in:current}*(1+MAX(0,MIN({set:rent_cap},MAX({in:cpi},IFERROR({in:market}/{in:current}-1,0))-{in:good}))),0)-{in:current})'),
        OUT('Still below market by', 'money', 'MAX(0,{in:market}-ROUND({in:current}*(1+MAX(0,MIN({set:rent_cap},MAX({in:cpi},IFERROR({in:market}/{in:current}-1,0))-{in:good}))),0))')],
        {"title": "Other increases", "rows": [{"label": "+2%", "values": {"current": "={in:current}*1.02"}}, {"label": "+3%", "values": {"current": "={in:current}*1.03"}}, {"label": "+5%", "values": {"current": "={in:current}*1.05"}}]}),
    TOOL('afford', 'Tenant Affordability', 'Can this applicant afford the unit?', 'Type the applicant\'s income and debts and the rent; your income rule comes from Start.', [
        IN('income', 'Monthly income after tax', 'money', 6200), IN('debts', 'Monthly loan and card payments', 'money', 450), IN('rent', 'Monthly rent of the unit', 'money', 1650),
        IN('fees', 'Move-in fees (admin, keys, etc.)', 'money', 150), IN('dep_m', 'Deposit, in months of rent', 'num', 1)], [
        OUT('Income ÷ rent', 'num', 'IFERROR(ROUND({in:income}/{in:rent},2),0)'),
        OUT('Rent as a share of income', 'pct', 'IFERROR({in:rent}/{in:income},0)'),
        OUT('Rent plus debts as a share of income', 'pct', 'IFERROR(({in:rent}+{in:debts})/{in:income},0)'),
        OUT('Highest rent your rule allows', 'money', 'ROUND({in:income}/{set:income_x},0)'),
        OUT('Meets your income rule', 'text', 'IF({in:income}>={in:rent}*{set:income_x},%s,%s)' % (YES, NO)),
        OUT('Cash needed to move in', 'money', '{in:rent}+{in:rent}*{in:dep_m}+{in:fees}')]),
    TOOL('lease_break', 'Lease Break Cost', 'What ending a lease early costs each side', 'Type the rent, the months left and your lease\'s break terms.', [
        IN('rent', 'Monthly rent', 'money', 2100), IN('left', 'Months left on the lease', 'int', 5), IN('fee_m', 'Break fee in the lease, months of rent', 'num', 2),
        IN('relet', 'Days to find a new tenant', 'int', 35), IN('cost', 'Cost to re-let (ads, cleaning, commission)', 'money', 900)], [
        OUT('Rent left on the lease', 'money', '{in:rent}*{in:left}'),
        OUT('Break fee the tenant pays', 'money', '{in:rent}*{in:fee_m}'),
        OUT('Rent the owner loses while empty', 'money', 'ROUND({in:rent}*12/365*{in:relet},0)'),
        OUT('Owner\'s total cost', 'money', 'ROUND({in:rent}*12/365*{in:relet},0)+{in:cost}'),
        OUT('Owner better or worse off', 'money', '{in:rent}*{in:fee_m}-ROUND({in:rent}*12/365*{in:relet},0)-{in:cost}')]),
    TOOL('dep_return', 'Deposit Return', 'Settle a deposit fairly and on time', 'Type the deposit and each deduction; the return date comes from your rule on Start.', [
        IN('deposit', 'Deposit held', 'money', 2300), IN('rent_owed', 'Rent still owed', 'money', 0), IN('cleaning', 'Professional cleaning', 'money', 180), IN('damage', 'Repairs beyond normal wear', 'money', 240),
        IN('utilities', 'Final utility bills', 'money', 95), IN('moved', 'Move-out day', 'date', ago(6))], [
        OUT('Total deductions', 'money', '{in:rent_owed}+{in:cleaning}+{in:damage}+{in:utilities}'),
        OUT('Refund to the tenant', 'money', 'MAX(0,{in:deposit}-({in:rent_owed}+{in:cleaning}+{in:damage}+{in:utilities}))'),
        OUT('Tenant still owes', 'money', 'MAX(0,({in:rent_owed}+{in:cleaning}+{in:damage}+{in:utilities})-{in:deposit})'),
        OUT('Share of the deposit kept', 'pct', 'IFERROR(MIN(1,({in:rent_owed}+{in:cleaning}+{in:damage}+{in:utilities})/{in:deposit}),0)'),
        OUT('Return it by', 'date', '{in:moved}+{set:dep_days}'),
        OUT('Days left to return it', 'int', '{in:moved}+{set:dep_days}-{today}')]),
]

# ------------------------------------------------------------------ printables
forms = [
    FORM('statement', 'Tenant Statement', 'Tenant statement of account', 'tenants.tenant_id', [
        FV('Tenant', 'tenants.name'), FV('Unit', 'tenants.unit'), FV('Phone', 'tenants.phone'), FV('Billed', 'tenants.billed'), FV('Paid', 'tenants.paid'),
        FV('Balance', 'tenants.balance'), FV('Overdue', 'tenants.overdue'), FV('Paid on time', 'tenants.on_time')],
        {"from": "charges", "match": "charges.tenant", "columns": ["due", "memo", "amount", "paid", "balance", "state"], "max": 40}),
    FORM('invoice', 'Rent Invoice', 'Rent invoice', 'charges.ch_id', [
        FV('Tenant', 'charges.name'), FV('Unit', 'charges.unit'), FV('Property', 'charges.prop'), FV('Description', 'charges.memo'), FV('Due date', 'charges.due'),
        FV('Amount', 'charges.amount'), FV('Already paid', 'charges.paid'), FV('To pay', 'charges.balance'), FV('Late fee if paid today', 'charges.fee')]),
    FORM('receipt', 'Rent Receipt', 'Payment receipt', 'payments.pay_id', [
        FV('Received from', 'payments.name'), FV('Date', 'payments.date'), FV('Amount', 'payments.amount'), FV('For', 'payments.for_what'),
        FV('Unit', 'payments.unit'), FV('Method', 'payments.method'), FV('Reference', 'payments.ref')]),
    FORM('lease_card', 'Lease Summary', 'Lease summary', 'leases.lease_id', [
        FV('Tenant', 'leases.tenant_name'), FV('Unit', 'leases.unit'), FV('Starts', 'leases.start'), FV('Ends', 'leases.end'), FV('Rent per payment', 'leases.rent'),
        FV('Paid', 'leases.freq'), FV('Rent / month', 'leases.monthly'), FV('Deposit', 'leases.deposit'), FV('Status', 'leases.state'), FV('Days left', 'leases.days_left'),
        FV('Balance', 'leases.balance'), FV('Rent after the yearly increase', 'leases.next_rent')],
        {"from": "charges", "match": "charges.lease", "columns": ["due", "memo", "amount", "balance"], "max": 30}),
]
documents = [
    DOC('lease_doc', 'Lease Agreement', 'Residential lease agreement', 'leases.lease_id', [
        'This lease is made on {col:leases.signed} between the landlord, represented by the managing agent, and {col:leases.tenant_name} (the tenant).',
        '1. The property: unit {col:leases.unit} in property {col:leases.prop}, let for residential use only.',
        '2. Term: from {col:leases.start} to {col:leases.end}. Renewal is by written agreement before the end date.',
        '3. Rent: {col:leases.rent} paid {col:leases.freq}, due on day {col:leases.due_day} of the period. Rent paid after the grace period carries the late fee set out by the managing agent.',
        '4. Deposit: {col:leases.deposit}, held as security and returned within the agreed days after move-out, less any lawful deductions for unpaid rent or damage beyond normal wear.',
        '5. Use and care: the tenant keeps the unit clean, reports repairs promptly, does not sublet without written consent and allows entry for inspection or repair after notice.',
        '6. Rent review: at renewal the rent may change by up to the agreed yearly increase of {col:leases.escal}, unless both parties agree otherwise in writing.',
        '7. Ending the lease: either party gives written notice as required by law. Keys, meter readings and an inspection report are exchanged at move-out.'],
        ['Landlord or managing agent', 'Tenant', 'Witness']),
    DOC('late_notice', 'Late Rent Notice', 'Notice of overdue rent', 'tenants.tenant_id', [
        'Dear {col:tenants.name},',
        'Our records show an overdue balance of {col:tenants.overdue} on your account for unit {col:tenants.unit}. The oldest unpaid amount is {col:tenants.oldest} days late.',
        'Please pay the full amount within 7 days of this notice, or contact us today to agree a payment plan. Late fees continue to apply as set out in your lease.',
        'If you have already paid, please send us the payment reference so we can update your account. Thank you.'],
        ['Property manager']),
    DOC('renewal_offer', 'Renewal Offer', 'Lease renewal offer', 'renewals.rn_id', [
        'Dear {col:renewals.tenant},',
        'Your lease for unit {col:renewals.unit} ends on {col:renewals.end}. We would be glad to have you stay.',
        'We offer to renew your lease until {col:renewals.new_end} at a rent of {col:renewals.proposed} per payment (currently {col:renewals.current}).',
        'Please reply within 30 days to accept, or contact us to discuss. If we do not hear from you, we will start preparing the unit for new tenants.'],
        ['Property manager', 'Tenant (accepted)']),
    DOC('entry_notice', 'Entry Notice', 'Notice of entry', 'notices.no_id', [
        'Dear {col:notices.name},',
        'This is to let you know that we need to enter unit {col:notices.unit} for an inspection or repair.',
        'Planned date: {col:notices.deadline}. The visit will take place during normal working hours and we will keep it short.',
        'If the date does not suit you, please reply so that we can agree another time. Thank you for your cooperation.'],
        ['Property manager']),
]
checklists = [
    CHK('new_tenant', 'From enquiry to signed lease', 'applicants', 'applicants.created', [
        ('Reply to the enquiry and send the unit details', 0), ('Book the viewing', 1), ('Show the unit and note the feedback', 3), ('Collect the application, ID and proof of income', 5),
        ('Check references and the screening score', 7), ('Approve or decline in writing', 8), ('Send the lease and the move-in costs', 9), ('Sign the lease and take the deposit', 12)]),
    CHK('move_in', 'Move-in', 'leases', 'leases.signed', [
        ('Deposit and first rent received', 0), ('Utilities moved to the tenant\'s name', 3), ('Unit cleaned and keys counted', 5), ('Move-in inspection with photos, signed by both', 7),
        ('Meter readings recorded', 7), ('Keys handed over and welcome message sent', 7), ('Check-in call after the first week', 14)]),
    CHK('move_out', 'Move-out and deposit', 'moveouts', 'moveouts.notice_on', [
        ('Confirm the notice and the move-out day in writing', 0), ('Send move-out instructions', 2), ('Pre-move-out visit to list repairs', 14), ('Move-out inspection with photos', 31),
        ('Final meter readings and keys back', 31), ('Deposit deductions agreed and refund sent', 45), ('Unit advertised again', 20)]),
    CHK('renewal', 'Lease renewal', 'renewals', 'renewals.offer_on', [
        ('Check the market rent and the tenant\'s payment record', -10), ('Agree the offer with the owner', -5), ('Send the renewal offer', 0), ('Follow up if there is no answer', 14),
        ('Sign the renewal or start marketing the unit', 30), ('Update the lease dates and rent', 31)]),
]
P = 'Hello'
messages = [
    MSG('rent_due', 'Rent due soon', 'charges', 'charges.phone', 'Hello {name}, a friendly reminder that {memo} of {amount} for unit {unit} is due on {due}. Thank you!'),
    MSG('rent_late', 'Rent overdue', 'charges', 'charges.phone', 'Hello {name}, we have not yet received {memo} ({balance}) for unit {unit}, due on {due}. Please pay today or let us know when you will.'),
    MSG('late_fee', 'Late fee added', 'charges', 'charges.phone', 'Hello {name}, as your payment is {days_late} days late, a late fee of {fee} applies in line with your lease. Please contact us if you need help.'),
    MSG('receipt', 'Payment received', 'payments', 'payments.phone', 'Hello {name}, thank you! We received {amount} on {date} for {for_what}. Reference: {ref}.'),
    MSG('renew_soon', 'Lease ending soon', 'leases', 'leases.phone', 'Hello {tenant_name}, your lease for unit {unit} ends on {end}. We would love you to stay — we will send you a renewal offer shortly.'),
    MSG('renew_offer', 'Renewal offer sent', 'renewals', 'renewals.phone', 'Hello {tenant}, we have sent you a renewal offer for unit {unit}: {proposed} per payment until {new_end}. We look forward to your answer.'),
    MSG('view_confirm', 'Viewing confirmed', 'viewings', 'viewings.phone', 'Hello {name}, your viewing of unit {unit} is confirmed for {date} at {time}. {agent} will meet you there. See you soon!'),
    MSG('app_got', 'Application received', 'applicants', 'applicants.phone', 'Hello {name}, thank you for applying for unit {unit}. We are checking your documents and will reply within two working days.'),
    MSG('app_ok', 'Application approved', 'applicants', 'applicants.phone', 'Good news {name}! Your application for unit {unit} is approved. We will send the lease and the move-in costs today.'),
    MSG('app_no', 'Application declined', 'applicants', 'applicants.phone', 'Hello {name}, thank you for your interest in unit {unit}. We are unable to offer it to you this time. We will let you know about other units that may suit you.'),
    MSG('docs', 'Documents needed', 'applicants', 'applicants.phone', 'Hello {name}, to complete your application for unit {unit} please send a copy of your ID and your last three payslips or bank statements.'),
    MSG('welcome', 'Welcome to your home', 'tenants', 'tenants.phone', 'Welcome home {name}! For anything you need in unit {unit}, message us here. Rent is paid by bank transfer or card; we send a reminder before each due date.'),
    MSG('inspect', 'Inspection visit', 'notices', 'notices.phone', 'Hello {name}, we plan a short visit to unit {unit} on {deadline}. Please reply if another time suits you better.'),
    MSG('plan_due', 'Instalment due', 'plans', 'plans.phone', 'Hello {name}, your next instalment of {each} under your payment plan is due. Paid so far: {paid}; still owed: {left}. Thank you for keeping to the plan.'),
    MSG('moveout_info', 'Move-out instructions', 'moveouts', 'moveouts.phone', 'Hello {tenant}, we have your notice for unit {unit}. Move-out day: {move_out}. Please leave the unit clean, return all keys and we will read the meters together.'),
    MSG('dep_back', 'Deposit refunded', 'moveouts', 'moveouts.phone', 'Hello {tenant}, your deposit settlement for unit {unit} is complete. Thank you for being our tenant — we wish you all the best.'),
]
for m in messages:  # phone columns: tenants, applicants etc. carry 'phone'
    pass

dashboard = {"title": "Rentals Dashboard", "kpis": [
    KPI('Units', 'COUNTA({range:units.unit_id})', 'int'),
    KPI('Occupied units', 'COUNTIFS({range:units.state},%s)' % LV('unit_state', 'occupied'), 'int'),
    KPI('Occupancy', 'IFERROR(COUNTIFS({range:units.state},%s)/COUNTA({range:units.unit_id}),"")' % LV('unit_state', 'occupied'), 'pct'),
    KPI('Vacant units', 'COUNTIFS({range:units.state},%s)' % LV('unit_state', 'vacant'), 'int'),
    KPI('Monthly rent roll', 'SUM({range:units.cur_rent})', 'money'),
    KPI('Rent if full at market', 'SUM({range:units.market})', 'money'),
    KPI('Billed, last 30 days', 'SUMIFS({range:charges.amount},{range:charges.due},">="&({today}-29),{range:charges.due},"<="&{today})', 'money'),
    KPI('Collected, last 30 days', 'SUMIFS({range:payments.amount},{range:payments.date},">="&({today}-29))', 'money'),
    KPI('Overdue rent', 'SUMIFS({range:charges.balance},{range:charges.state},%s)' % LV('charge_state', 'overdue'), 'money'),
    KPI('Tenants with overdue rent', 'COUNTIFS({range:tenants.flag},%s)' % F('overdue'), 'int'),
    KPI('Overdue over 30 days', 'SUMIFS({range:charges.balance},{range:charges.state},%s,{range:charges.days_late},">30")' % LV('charge_state', 'overdue'), 'money'),
    KPI('Collection rate, 12 months', 'IFERROR(SUMIFS({range:charges.paid},{range:charges.due},">="&({today}-365),{range:charges.due},"<="&{today})/SUMIFS({range:charges.amount},{range:charges.due},">="&({today}-365),{range:charges.due},"<="&{today}),"")', 'pct'),
    KPI('Rent paid on time', 'IFERROR(COUNTIFS({range:charges.on_time},%s)/(COUNTIFS({range:charges.on_time},%s)+COUNTIFS({range:charges.on_time},%s)),"")' % (YES, YES, NO), 'pct'),
    KPI('Leases ending soon', 'COUNTIFS({range:leases.state},%s)' % LV('lease_state', 'expiring'), 'int'),
    KPI('Renewals waiting for an answer', 'COUNTIFS({range:renewals.decision},%s)' % LV('decision', 'pending'), 'int'),
    KPI('Deposits held', 'SUMIFS({range:deposits.amount},{range:deposits.returned_on},"")', 'money'),
    KPI('Deposits late to return', 'COUNTIFS({range:deposits.flag},%s)' % F('late_ret'), 'int'),
    KPI('Rent lost to vacancy so far', 'SUM({range:units.lost})', 'money'),
    KPI('Average days vacant', 'IFERROR(AVERAGE({range:units.days_vacant}),"")', 'int'),
    KPI('Open applicants', 'COUNTIFS({range:applicants.state},%s)+COUNTIFS({range:applicants.state},%s)+COUNTIFS({range:applicants.state},%s)' % (LV('app_state', 'new'), LV('app_state', 'viewing'), LV('app_state', 'applied')), 'int'),
    KPI('Viewings in the next 7 days', 'COUNTIFS({range:viewings.date},">="&{today},{range:viewings.date},"<="&({today}+7))', 'int'),
    KPI('Average rent per m²', 'IFERROR(AVERAGEIFS({range:units.per_m2},{range:units.state},%s),"")' % LV('unit_state', 'occupied'), 'num'),
    KPI('Payment plans behind', 'COUNTIFS({range:plans.state},%s)' % LV('plan_state', 'behind'), 'int'),
    KPI('Notices past their deadline', 'COUNTIFS({range:notices.days},"<0")', 'int')],
    "monthly": {"title": "Billed and collected by month", "date": "charges.due", "series": [{"label": "Billed", "sum": "charges.amount"}, {"label": "Collected", "sum": "charges.paid"}]},
    "breakdowns": [{"title": "Unpaid balance by charge type", "by": "charges.ctype", "value": "charges.balance", "agg": "sum"},
                   {"title": "Rent roll by property", "by": "units.prop", "value": "units.cur_rent", "agg": "sum"},
                   {"title": "Payments by method", "by": "payments.method", "value": "payments.amount", "agg": "sum"},
                   {"title": "Applicants by source", "by": "applicants.source", "value": "applicants.app_id", "agg": "count"}]}
insights = {"filters": [{"label": "Property", "ref": "properties.prop_id"}, {"label": "Charge type", "list": "charge_type"}],
    "gauges": [{"title": "Occupancy", "num": AGG('count', 'units', where=[('state', '=', LV('unit_state', 'occupied'))]), "den": AGG('count', 'units')},
               {"title": "Collected of billed", "num": AGG('sum', 'charges', 'charges.paid'), "den": AGG('sum', 'charges', 'charges.amount')},
               {"title": "Rent paid on time", "num": AGG('count', 'charges', where=[('on_time', '=', YES)]), "den": AGG('count', 'charges', where=[('state', '<>', LV('charge_state', 'open'))])},
               {"title": "Applicants who signed", "num": AGG('count', 'applicants', where=[('state', '=', LV('app_state', 'signed'))]), "den": AGG('count', 'applicants')}],
    "charts": [CHART('Billed and collected by month', 'combo', 'month', [AGG('sum', 'charges', 'charges.amount', 'charges.due', label='Billed'), AGG('sum', 'charges', 'charges.paid', 'charges.due', label='Collected')], 1),
               CHART('Overdue rent by month it fell due', 'column', 'month', [AGG('sum', 'charges', 'charges.balance', 'charges.due', [('state', '=', LV('charge_state', 'overdue'))], 'Overdue')]),
               CHART('Rent roll by property', 'bar', 'units.prop', [AGG('sum', 'units', 'units.cur_rent', label='Rent / month')]),
               CHART('Vacant units by property', 'column', 'units.prop', [AGG('count', 'units', where=[('state', '=', LV('unit_state', 'vacant'))], label='Vacant units')]),
               CHART('Units by type', 'doughnut', 'units.utype', [AGG('count', 'units', label='Units')]),
               CHART('Payments by method', 'pie', 'payments.method', [AGG('sum', 'payments', 'payments.amount', label='Paid')]),
               CHART('New leases by month', 'line', 'month', [AGG('count', 'leases', date='leases.start', label='New leases')]),
               CHART('Applicants by source', 'bar', 'applicants.source', [AGG('count', 'applicants', label='Applicants')]),
               CHART('Applicants by stage', 'column', 'applicants.state', [AGG('count', 'applicants', label='Applicants')]),
               CHART('Charges by type', 'doughnut', 'charges.ctype', [AGG('sum', 'charges', 'charges.amount', label='Billed')]),
               CHART('Viewings by outcome', 'pie', 'viewings.outcome', [AGG('count', 'viewings', label='Viewings')])]}

signature = [
    {"name": "Live rent roll with arrears ageing", "why": "every charge knows what was paid, when, how many days late and whether it counts as on time — no manual ticking", "where": "Rent Roll"},
    {"name": "Units that tell you what they earn and lose", "why": "status, tenant, rent per m², the gap to market and the rent lost each day a unit stays empty", "where": "Units"},
    {"name": "Owner portfolio view", "why": "each owner's units, vacancies, rent roll, collections and arrears update by themselves — the base for owner statements", "where": "Owners"},
    {"name": "Renewals inside your cap", "why": "offers checked against today's rent and your largest allowed increase before they go out", "where": "Renewals"},
    {"name": "Applicant screening score", "why": "income-to-rent, references and household size scored against your own approval rules", "where": "Applicants"},
    {"name": "Deposit control", "why": "who holds each deposit, deductions with reasons and an alert when a refund is late", "where": "Deposits"},
    {"name": "Arrears payment plans", "why": "instalments due to date versus paid since the agreement, with on-track or behind status", "where": "Payment Plans"},
    {"name": "Notices log with deadlines", "why": "late-rent, entry, renewal, increase, breach and vacate notices tracked to their deadlines", "where": "Notices"},
    {"name": "16 ready WhatsApp messages", "why": "reminders, receipts, renewals, viewings and move-out texts filled from each row in one click", "where": "Messages"},
    {"name": "Six leasing calculators", "why": "prorated rent, late fees, defensible increases, affordability, lease-break cost and deposit returns", "where": "Rent Increase Calculator"}]
competitors = [
    {"what": "typical Etsy rental property spreadsheets", "lacks": "track rent per property only — no tenant ledger, arrears ageing, deposits, renewals or notices"},
    {"what": "landlord income and expense trackers", "lacks": "built for one owner; nothing for a manager running many owners, units and leases"},
    {"what": "property management apps on monthly subscriptions", "lacks": "cost every month, keep your data on their servers and still need exports to analyse"},
    {"what": "free rent ledger templates", "lacks": "one tenant per sheet, no occupancy, no market-rent gap, no screening or move-out workflow"}]
guide = [
    'Open Start and type your company name, grace days, late fee, renewal window, largest increase, income rule and deposit return days in the yellow cells.',
    'List your owners on Owners, then each building on Properties with its owner ID.',
    'Add every unit on Units with its type, size and market rent. Status, tenant and rent fill in from the leases.',
    'Add each tenant on Tenants and each lease on Leases: unit, tenant, dates, rent, how often it is paid, deposit and yearly increase.',
    'Post every amount due on Rent Roll — one row per rent period, fee or bill — and every payment on Payments against its charge ID.',
    'Record deposits on Deposits; the return date and late alerts work themselves out after the lease ends.',
    'Log enquiries on Applicants and visits on Viewings; the screening score compares each applicant with your rules.',
    'Ninety days before a lease ends it shows as ending soon: make the offer on Renewals and check it is inside your cap.',
    'Serve and track formal notices on Notices; agree payment plans for arrears on Payment Plans.',
    'Print a tenant statement, invoice, receipt or lease summary from the printable sheets by choosing the ID in the yellow cell.',
    'Send reminders and receipts from the Messages links: each opens WhatsApp with the text filled in.',
    'Read the Rentals Dashboard and the Charts every week: occupancy, collections, arrears and renewals at a glance.']
listing = {"title": "Property Management Excel Template: Rent Roll, Tenant Ledger, Leases, Arrears, Deposits, Renewals, Screening, 15 Languages",
    "headline": "Run rentals for many owners: rent roll, arrears, leases, renewals",
    "tags": ["property management", "rent roll", "landlord template", "tenant tracker", "lease tracker", "rental property", "rent ledger", "property manager", "rental income", "tenant screening", "security deposit", "lease renewal", "excel template"],
    "description": ("Property management in one Excel workbook, built for managers who look after many owners, buildings and units.\n\n"
        "Every rent period, fee and bill sits on a live rent roll. Payments are matched to the charge they settle, so each charge knows what was paid, "
        "when, how many days late and whether it was on time. Tenants, leases, units, properties and owners all update from the same records: balances, "
        "arrears ageing, occupancy, rent per square metre, the gap to market rent and the rent lost while a unit stands empty.\n\n"
        "Renewals are checked against your largest allowed increase before the offer goes out. Applicants get a screening score against your own income "
        "and reference rules. Deposits show who holds them, the deductions and the date they must be returned. Payment plans show whether a tenant in "
        "arrears is on track. Every formal notice is logged with its deadline.\n\n"
        "Six calculators answer daily questions: prorated rent, late fees, a defensible rent increase, tenant affordability, the cost of a lease break "
        "and a fair deposit return. Print a tenant statement, rent invoice, receipt or lease summary, or a lease agreement, late-rent notice, renewal offer "
        "or entry notice filled from your data. Sixteen WhatsApp messages open with the tenant's details already written in.\n\n"
        "This is part one of the Property Management suite. Standard .xlsx files for Microsoft Excel and LibreOffice, no macros, no subscription, "
        "15 languages in one purchase, with a demo copy full of sample data to explore first."),
    "features": ["Live rent roll: paid, balance, days late, on-time status", "Tenant ledger with arrears ageing and on-time rate", "Units with rent per m², gap to market and vacancy loss",
                 "Owner portfolio: units, vacancies, rent roll, arrears", "Renewals checked against your increase cap", "Applicant screening score and viewings",
                 "Deposits with deductions and late-return alerts", "Payment plans and a notices log with deadlines", "Six leasing calculators",
                 "Statement, invoice, receipt, lease and notices to print", "16 ready WhatsApp messages", "Dashboard with 24 live figures and 10 charts"]}

s = spec(id=f'{SUITE}-p1', slug='property-management-rentals', profession='Property management', name='Rentals & Leasing',
         tagline='Rent roll, tenants, leases, arrears, deposits and renewals for every owner', price_usd=29,
         colors={"primary": "#1E3A5F", "accent": "#C8963E"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 6, "focus": "Rent roll, tenants, leases, arrears, deposits and renewals"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(__file__), 'pm1.en.json'))
    print({k: len(v) for k, v in s.items() if isinstance(v, list)}, {t['key']: len(t['demo']) for t in tables})
