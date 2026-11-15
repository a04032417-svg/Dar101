"""Author and self-publisher suite (Dar Templates) - shared demo story for ALL eight parts.

Pure data + tiny helpers + deterministic row generators, independent of call order (one cached world is built on first use). The demo business is "Lanternfield Press"
(fictional): the one-person imprint of an author-publisher (Noor Castellan, AU-01) who writes under two pen names, Tamsin Hartwell (mysteries) and Corvin Ashdale (fantasy).
A part-time virtual assistant (Dario Lindqvist, AU-02) and freelancers paid per job (editors AU-03/AU-04, a cover designer AU-05, a formatter AU-06, narrators AU-07/AU-08, a translator
AU-09, an ad specialist AU-14, a web developer AU-15, a launch coordinator AU-16) plus an accountant (AU-10), a printer for author copies (AU-11), an event organiser (AU-12) and a rights
agent (AU-13) make the team of 16. The catalogue is 22 titles (TL-001..TL-022): four series (Lantern Bay Mysteries 6 books, Quiet Hollow Cases 4, The Ember Crown 5, Tidebound Realms 3),
two standalones and two box sets, in 68 editions (ED-0001..) in ebook, paperback, hardcover (some), large print (some) and audiobook (some). Sales run through five online stores in generic
words (an ebook store with a page-read income line, a print-on-demand service, an audiobook store, a library and lending channel, a wide-distribution service) and the author's direct store, in
six currencies and eight countries (an editable exchange-rate table). Stores pay 45-90 days after month end (the direct store pays out in a week). About 2 years of history; every date is
relative to the build day. A first-time author with 1-3 books uses the same sheets with a few rows; a small press can read the pen-name columns as author columns.

Money model: ONE generic home currency; a store reports in its own currency, home amount = store-currency amount x the month's rate (fx_rate). Royalty per copy: ebook = price x share -
delivery cost; print = price x share - print cost; audio = price x share. Shares are 0..1 fractions; every royalty share, delay and tax percent is an editable demo value ("check each store's
current terms", "confirm with your adviser"). Page reads = pages read x a rate per page (the owner's own number). Direct order net = price - discount + shipping charged - payment fee, minus
delivery cost (sales tax collected is not income). Title cost = sum of the production job quotes; earned back when lifetime royalties (royalty_before + the ledger + page reads) reach it.
Profit by month = royalties + page reads + direct net + event sales + rights received - ads - production paid - expenses - event costs. Cash by month = money received (store payments
on their paid date, event sales, rights instalments) - money paid out (ads, contractor payments, expenses, event costs, author-copy orders, tax set-aside, owner draw).

Story rows (ids from story(), never hard-coded): cost_title (a title not earned back after 18 months; the audiobook drags it), ad_campaign (spends more than the royalties it brings),
series (read-through from book 1 to book 2 below the target), statement (a store payment short-paid against its statement), launch (a book launches next month with checklist steps late),
invoice (a narrator's invoice due this week that pushes cash below the floor).

Exports
  constants: COMPANY SUITE OWNER ASSISTANT LAUNCH_DATE PRE_START and the editable targets AD_RETURN_TARGET AD_SHARE_OF_BREAKEVEN CONVERSION_FLOOR READTHROUGH_WARN_1 READTHROUGH_WARN
             STORE_DEPENDENCE_LIMIT LAUNCH_FIRST_DAYS LAUNCH_WINDOW_DAYS TAX_SET_ASIDE_PCT CASH_COVER_MONTHS MIN_RELEASE_GAP_DAYS TITLE_RETURN_TARGET EVENT_PROFIT_PER_HOUR_FLOOR
             PAGE_READ_RATE CASH_FLOOR OWNER_DRAW_BASE VA_RATE DIRECT_SHARE_TARGET PAYMENT_FEE_PCT PAYMENT_FEE_FIXED SHIPPING_CHARGE AD_DETERIORATION_PCT FEE_FLAG_PCT
  dates: TODAY iso ago ahead to_date month_start add_months months24() week_start; helpers pairs first_name fake_phone fake_email rng fx_rate
  lists: ROLES TEAMS PAY_TYPES PEN_NAMES SERIES GENRES TITLE_STATUS FORMATS EDITION_STATUS STORES COUNTRIES CURRENCIES AD_PLATFORMS AD_STATUS JOB_KINDS JOB_STATUS PAY_STAGES CPAY_STATUS
         STATEMENT_STATUS EXPENSE_CATEGORIES EVENT_KINDS STOCK_MOVES DEAL_KINDS DEAL_STATUS LAUNCH_STEPS TASK_STATUS ARC_STATUS REVIEWER_KINDS SUB_SOURCES SEND_KINDS PROMO_KINDS PROMO_STATUS
  people and reference: team (16), pen_names (2), series_rows, formats, stores, countries, currencies, ad_platforms, cost_categories, launch_steps
  generators (fresh lists of dicts, oldest first; n= thins a long list but keeps the most recent rows; optional dates are '' when blank):
    title_rows edition_rows sales_rows pageread_rows direct_order_rows statement_rows payment_rows campaign_rows ad_day_rows promo_rows job_rows jobpay_rows newsletter_rows subscriber_rows
    swap_rows reviewer_rows arc_rows launch_task_rows event_rows event_sale_rows stock_rows deal_rows instalment_rows expense_rows pnl_rows cash_rows tax_rows draw_rows readthrough_rows
    author_statement_rows
  helpers: title_cost(tid) title_royalty(tid) story()
Lesson: money cells are plain amounts; optional dates (paid_on, delivered_on, done_on) are '' when blank: wrap lookups with IF(x=0,"",x). Links hold NAMES (title, store, country, contractor) or ids
(title TL-001, edition ED-0001, job JB-001, campaign AC-001). Words: no brand, store, platform or real title or author names; no law, tax-form or agency names.
"""
import datetime as dt
import calendar
import random
import hashlib
import math

COMPANY = 'Lanternfield Press'
SUITE = 'fx-20261115-author-publisher'
OWNER = 'Noor Castellan'
ASSISTANT = 'Dario Lindqvist'
import os
TODAY = dt.date.fromisoformat(os.environ['AU_TODAY']) if os.environ.get('AU_TODAY') else dt.date.today()   # AU_TODAY only for date tests
D = dt.date

AD_RETURN_TARGET = 1.0           # royalties per unit of ad spend (1.0 = break-even)
AD_SHARE_OF_BREAKEVEN = 0.35     # target ad cost of sale as a share of the break-even share
CONVERSION_FLOOR = 0.02          # clicks to sales
READTHROUGH_WARN_1 = 0.25        # book 1 to 2
READTHROUGH_WARN = 0.60          # later steps
STORE_DEPENDENCE_LIMIT = 0.70
LAUNCH_FIRST_DAYS = 7
LAUNCH_WINDOW_DAYS = 30
TAX_SET_ASIDE_PCT = 0.25
CASH_COVER_MONTHS = 3
MIN_RELEASE_GAP_DAYS = 45
TITLE_RETURN_TARGET = 0.10
EVENT_PROFIT_PER_HOUR_FLOOR = 15.0
PAGE_READ_RATE = 0.0042
CASH_FLOOR = 8000.0
OWNER_DRAW_BASE = 2800.0
VA_RATE = 24.0
DIRECT_SHARE_TARGET = 0.15
PAYMENT_FEE_PCT = 0.029
PAYMENT_FEE_FIXED = 0.30
SHIPPING_CHARGE = 4.0
AD_DETERIORATION_PCT = 0.20
FEE_FLAG_PCT = 0.03


def day(n): return dt.timedelta(days=n)
def iso(d): return d.isoformat() if hasattr(d, 'isoformat') else d
def ago(days): return iso(TODAY - dt.timedelta(days=days))
def ahead(days): return iso(TODAY + dt.timedelta(days=days))
def to_date(s): return D.fromisoformat(s) if isinstance(s, str) and s else s


def month_start(k):
    y, m = TODAY.year, TODAY.month - k
    while m <= 0: m += 12; y -= 1
    while m > 12: m -= 12; y += 1
    return dt.date(y, m, 1)


def add_months(d, n):
    y, m = d.year, d.month + n
    while m > 12: m -= 12; y += 1
    while m <= 0: m += 12; y -= 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def months24(): return [month_start(k) for k in range(23, -1, -1)]
def week_start(d): return d - day(d.weekday())


def pairs(labels):
    out = []
    for s in labels:
        k = ''.join(ch if ch.isalnum() else '_' for ch in s.lower()).strip('_')
        while '__' in k: k = k.replace('__', '_')
        out.append((k, s))
    return out


def first_name(name): return name.split()[0]
def fake_phone(i): return '+%d %d 555 %04d' % ([1, 44, 49, 61, 33, 34, 351, 31][i % 8], 20 + (i * 7) % 79, 3000 + (i * 37) % 6000)
def fake_email(name, i=0): return name.lower().replace(' ', '.').replace("'", '') + (str(i) if i else '') + '@mail.example.com'
def rng(tag=''): return random.Random('au-core-20261115-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)
def _eom(d): return dt.date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


HISTORY_START = month_start(23)
CUR = month_start(0)
CUR_FRAC = max(0.3, TODAY.day / float(calendar.monthrange(TODAY.year, TODAY.month)[1]))
LAUNCH_DATE = max(TODAY + day(28), add_months(CUR, 1) + day(2))     # the next book launch (next month)
PRE_START = LAUNCH_DATE - day(60)                                     # its pre-order opened this long before release

# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
ROLES = ['Author-publisher', 'Virtual assistant', 'Editor', 'Cover designer', 'Formatter', 'Narrator', 'Translator', 'Accountant', 'Printer', 'Event organiser', 'Rights agent',
         'Ad specialist', 'Web developer', 'Launch coordinator']
TEAMS = ['Owner', 'Assistant', 'Freelancer', 'Service provider']
PAY_TYPES = ['Owner draw', 'Hourly', 'Per job', 'Invoice']
PEN_NAMES = ['Tamsin Hartwell', 'Corvin Ashdale']
SERIES = ['Lantern Bay Mysteries', 'Quiet Hollow Cases', 'The Ember Crown', 'Tidebound Realms', 'Standalone', 'Box set']
GENRES = ['Cosy mystery', 'Crime mystery', 'Epic fantasy', 'Sea fantasy']
TITLE_STATUS = ['Released', 'Pre-order', 'In production']
FORMATS = ['Ebook', 'Paperback', 'Hardcover', 'Large print', 'Audiobook']
EDITION_STATUS = ['Live', 'Pre-order', 'In production', 'Planned']
STORES = ['Ebook store', 'Print-on-demand', 'Audiobook store', 'Library and lending', 'Wide distribution', 'Direct store']
COUNTRIES = ['Home country', 'United States', 'United Kingdom', 'Germany', 'France', 'Australia', 'Canada', 'Rest of world']
CURRENCIES = ['Home currency', 'Dollar', 'Pound', 'Euro', 'Australian dollar', 'Canadian dollar']
AD_PLATFORMS = ['Store ads', 'Social ads', 'Search ads']
AD_STATUS = ['Running', 'Paused', 'Ended']
JOB_KINDS = ['Developmental edit', 'Copy edit', 'Proofread', 'Cover design', 'Formatting', 'Narration', 'Translation', 'Setup and identifiers']
JOB_STATUS = ['Quoted', 'Booked', 'In progress', 'Delivered', 'Paid']
PAY_STAGES = ['Deposit', 'Milestone', 'Final']
CPAY_STATUS = ['Paid', 'Due', 'Scheduled']
STATEMENT_STATUS = ['Paid', 'Short-paid', 'Expected', 'Open']
EXPENSE_CATEGORIES = ['Newsletter service', 'Website and store', 'Software and tools', 'Virtual assistant', 'Review copies', 'Accounting and fees',
                      'Education', 'Office and equipment', 'Business insurance', 'Other']
EVENT_KINDS = ['Book fair', 'Author market', 'Genre convention', 'Library talk', 'Signing at a shop']
STOCK_MOVES = ['Order in', 'Sold at event', 'Damaged or lost', 'Gift or review copy']
DEAL_KINDS = ['Translation', 'Audio licence', 'Other licence']
DEAL_STATUS = ['Offer', 'Signed', 'Delivered', 'Paid in full', 'Expired']
LAUNCH_STEPS = [('Edit finished', -110, 'Editor'), ('Cover approved', -80, 'Cover designer'), ('Formatting finished', -65, 'Formatter'), ('Pre-order upload', -60, 'Author-publisher'),
                ('Reviewer copies sent', -42, 'Launch coordinator'), ('Teaser chapter ready', -35, 'Author-publisher'), ('Newsletter teaser', -21, 'Virtual assistant'),
                ('Reviewer reminders', -10, 'Launch coordinator'), ('Ads prepared', -7, 'Ad specialist'), ('Launch price set', -3, 'Author-publisher'),
                ('Launch day newsletter', 0, 'Virtual assistant'), ('Store pages checked', 1, 'Virtual assistant'), ('Thank the reviewers', 10, 'Launch coordinator')]
LAUNCH_STEP_NAMES = [s[0] for s in LAUNCH_STEPS]
TASK_STATUS = ['Done', 'Open']
ARC_STATUS = ['Review posted', 'Copy sent', 'Reminded', 'No reply', 'Not sent']
REVIEWER_KINDS = ['Reader', 'Blogger', 'Street team', 'Librarian', 'Bookseller']
SUB_SOURCES = ['Reader magnet', 'Newsletter swap', 'Paid promotion', 'Event sign-up', 'Store page link', 'Direct store']
SEND_KINDS = ['Launch push', 'Price promotion', 'Story update', 'Swap feature', 'Re-engagement']
PROMO_KINDS = ['Price drop', 'Box set sale', 'Holiday sale', 'Series sale']
PROMO_STATUS = ['Done', 'Planned']

# ------------------------------------------------------------------ people (AU-01..AU-16)
_P = [('AU-01', 'Noor Castellan', 'Spain', 'Author-publisher', 'Owner', 'Owner draw', 0.0, ''),
      ('AU-02', 'Dario Lindqvist', 'Sweden', 'Virtual assistant', 'Assistant', 'Hourly', 24.0, 'per hour'),
      ('AU-03', 'Priya Nandakumar', 'India', 'Editor', 'Freelancer', 'Per job', 25.0, 'per 1,000 words (developmental)'),
      ('AU-04', 'Leopold Brandt', 'Germany', 'Editor', 'Freelancer', 'Per job', 18.0, 'per 1,000 words (copy edit)'),
      ('AU-05', 'Ines Carvalho', 'Portugal', 'Cover designer', 'Freelancer', 'Per job', 550.0, 'per cover'),
      ('AU-06', 'Tomasz Wrona', 'Poland', 'Formatter', 'Freelancer', 'Per job', 160.0, 'per title'),
      ('AU-07', 'Amara Oyelaran', 'Nigeria', 'Narrator', 'Freelancer', 'Per job', 285.0, 'per finished hour'),
      ('AU-08', 'Gideon Falk', 'Norway', 'Narrator', 'Freelancer', 'Per job', 410.0, 'per finished hour'),
      ('AU-09', 'Yuki Tanabe', 'Japan', 'Translator', 'Freelancer', 'Per job', 55.0, 'per 1,000 words'),
      ('AU-10', 'Renata Bauer', 'Austria', 'Accountant', 'Service provider', 'Invoice', 120.0, 'per quarter'),
      ('AU-11', 'Callum Whitford', 'United Kingdom', 'Printer', 'Service provider', 'Invoice', 0.0, 'per order'),
      ('AU-12', 'Marguerite Lowe', 'France', 'Event organiser', 'Service provider', 'Invoice', 0.0, 'per event'),
      ('AU-13', 'Sven Hallgren', 'Sweden', 'Rights agent', 'Service provider', 'Invoice', 0.15, 'share of a deal'),
      ('AU-14', 'Lucia Ferreira', 'Brazil', 'Ad specialist', 'Freelancer', 'Per job', 90.0, 'per campaign set-up'),
      ('AU-15', 'Mikael Dahl', 'Denmark', 'Web developer', 'Freelancer', 'Per job', 60.0, 'per hour'),
      ('AU-16', 'Hye-jin Seo', 'South Korea', 'Launch coordinator', 'Freelancer', 'Per job', 140.0, 'per launch')]
team = [dict(person_id=a, name=b, role=ro, team=te, pay_type=pt, phone=fake_phone(101 + i), email=fake_email(b), rate=rt, rate_unit=ru, country=c, since=ago(2300 - 120 * i))
        for i, (a, b, c, ro, te, pt, rt, ru) in enumerate(_P)]
PERSON = {x['name']: x for x in team}
PEOPLE_NAMES = [x['name'] for x in team]

pen_names = [dict(pen_name=PEN_NAMES[0], genre='Mystery', author_share=0.70), dict(pen_name=PEN_NAMES[1], genre='Fantasy', author_share=0.70)]
# author_share: demo of the small-press view (the press keeps the rest); a one-author business sets 1.00

_CACHE = {}
def _raw(key, fn):
    if key not in _CACHE: _CACHE[key] = fn()
    return _CACHE[key]
def _cached(key, fn): return [dict(r) for r in _raw(key, fn)]
def _thin(rows, n):
    if not n or n >= len(rows): return rows
    k = min(max(3, n // 5), n)
    if k >= n: return rows[-n:]
    recent = rows[-k:]; rest = rows[:-k]; m = n - k; step = len(rest) / float(m)
    return [rest[int(i * step)] for i in range(m)] + recent
def _wchoice(r, vals, ws):
    x, acc = r.random() * sum(ws), 0
    for v, w in zip(vals, ws):
        acc += w
        if x <= acc: return v
    return vals[-1]


def _split(r, n, ws):
    """n units over weights ws -> list of ints (randomised rounding)"""
    tot = float(sum(ws)); raw = [n * w / tot for w in ws]; out = [int(x) for x in raw]; rem = n - sum(out)
    fr = [x - int(x) + 1e-6 for x in raw]
    while rem > 0:
        i = _wchoice(r, list(range(len(ws))), fr); out[i] += 1; fr[i] = 1e-6; rem -= 1
    return out


# ------------------------------------------------------------------ reference: currencies, countries, stores, formats
_BASE_FX = {'Home currency': 1.0, 'Dollar': 0.92, 'Pound': 1.12, 'Euro': 0.96, 'Australian dollar': 0.60, 'Canadian dollar': 0.67}
_FX_PH = {'Dollar': 0.3, 'Pound': 1.1, 'Euro': 2.0, 'Australian dollar': 3.1, 'Canadian dollar': 4.2}
currencies = [dict(currency=c, rate=_BASE_FX[c]) for c in CURRENCIES]


def fx_rate(cur, M1):
    """home currency per 1 unit of the store currency, in the month M1 (the editable table holds the base rate)"""
    if cur == 'Home currency': return 1.0
    k = M1.year * 12 + M1.month
    return round(_BASE_FX[cur] * (1 + 0.035 * math.sin(k * 0.6 + _FX_PH[cur])), 4)


_CTRY = {'Home country': ('Home currency', 0.10, 3.2), 'United States': ('Dollar', 0.0, 6.4), 'United Kingdom': ('Pound', 0.20, 5.2), 'Germany': ('Euro', 0.19, 5.6),
         'France': ('Euro', 0.20, 5.4), 'Australia': ('Australian dollar', 0.10, 8.9), 'Canada': ('Canadian dollar', 0.05, 7.4), 'Rest of world': ('Dollar', 0.0, 9.5)}
countries = [dict(country=c, currency=_CTRY[c][0], sales_tax_pct=_CTRY[c][1]) for c in COUNTRIES]
_STORE = {  # typical royalty share, low, high, delay days, formats
    'Ebook store': (0.70, 0.35, 0.70, 60, 'Ebook'), 'Print-on-demand': (0.60, 0.60, 0.60, 60, 'Paperback, hardcover, large print'),
    'Audiobook store': (0.40, 0.25, 0.40, 45, 'Audiobook'), 'Library and lending': (0.55, 0.40, 0.55, 75, 'Ebook, audiobook'),
    'Wide distribution': (0.60, 0.35, 0.60, 90, 'All formats'), 'Direct store': (0.90, 0.85, 0.95, 7, 'All formats')}
stores = [dict(store=s, royalty_share=_STORE[s][0], delay_days=_STORE[s][3], share_low=_STORE[s][1], share_high=_STORE[s][2], formats=_STORE[s][4]) for s in STORES]
SDELAY = {s: _STORE[s][3] for s in STORES}
ad_platforms = [dict(platform='Store ads', typical_cpc=0.18, daily_min=1.0), dict(platform='Social ads', typical_cpc=0.22, daily_min=5.0), dict(platform='Search ads', typical_cpc=0.20, daily_min=3.0)]
cost_categories = [dict(kind='Developmental edit', unit='per 1,000 words', rate=25.0), dict(kind='Copy edit', unit='per 1,000 words', rate=18.0), dict(kind='Proofread', unit='per 1,000 words', rate=7.0),
                   dict(kind='Cover design', unit='flat per cover', rate=550.0), dict(kind='Formatting', unit='flat per title', rate=160.0), dict(kind='Narration', unit='per finished hour', rate=285.0),
                   dict(kind='Translation', unit='per 1,000 words', rate=55.0), dict(kind='Setup and identifiers', unit='flat per edition', rate=28.0)]
launch_steps = [dict(step_no=i, step=s, days_from_release=d, owner_role=o) for i, (s, d, o) in enumerate(LAUNCH_STEPS, 1)]
_FMT_BASE = {'Ebook': (0.12, 0.0), 'Paperback': (1.20, 0.0118), 'Hardcover': (6.50, 0.0145), 'Large print': (1.20, 0.0118), 'Audiobook': (0.0, 0.0)}
_FMT_SHARE = {'Ebook': 0.70, 'Paperback': 0.60, 'Hardcover': 0.60, 'Large print': 0.60, 'Audiobook': 0.40}
formats = [dict(format=f, royalty_share=_FMT_SHARE[f], base_cost=_FMT_BASE[f][0]) for f in FORMATS]

# ------------------------------------------------------------------ catalogue: titles and editions
_TP, _CP = PEN_NAMES
_LBM, _QHC, _TEC, _TR = SERIES[:4]
# title, pen, series, order, genre, words, release (days ago, 'L' launch, 'L35' launch + 35), base ebook units a month, ebook price, exclusive (page reads), hardcover, large print, audio (2 = planned or in production)
_T = [('The Salt Pier Letter', _TP, _LBM, 1, 'Cosy mystery', 78000, 1500, 210, 2.99, 0, 1, 1, 1),
      ('The Drowned Ledger', _TP, _LBM, 2, 'Cosy mystery', 82000, 1320, 150, 5.99, 0, 1, 1, 1),
      ('Candle at Gull Point', _TP, _LBM, 3, 'Cosy mystery', 85000, 1150, 105, 5.99, 0, 1, 1, 1),
      ('The Quiet Tide Alibi', _TP, _LBM, 4, 'Cosy mystery', 88000, 930, 88, 5.99, 0, 0, 1, 0),
      ('Knots of Marrow Bay', _TP, _LBM, 5, 'Cosy mystery', 90000, 640, 76, 5.99, 0, 0, 2, 0),
      ('The Last Lamp Out', _TP, _LBM, 6, 'Cosy mystery', 92000, 150, 82, 5.99, 0, 0, 0, 0),
      ('The Orchard Key', _TP, _QHC, 1, 'Crime mystery', 81000, 1240, 140, 2.99, 1, 0, 1, 1),
      ('A Stranger at Fenmoor Mill', _TP, _QHC, 2, 'Crime mystery', 84000, 1000, 95, 5.99, 1, 0, 1, 0),
      ('The Pale Bell Ringers', _TP, _QHC, 3, 'Crime mystery', 86000, 690, 62, 5.99, 1, 0, 0, 0),
      ('Ashes Under Hollow Lane', _TP, _QHC, 4, 'Crime mystery', 88000, 300, 58, 5.99, 1, 0, 0, 0),
      ('Shard of the Ember Crown', _CP, _TEC, 1, 'Epic fantasy', 98000, 1420, 240, 2.99, 0, 1, 0, 1),
      ('The Cinder Court', _CP, _TEC, 2, 'Epic fantasy', 104000, 1180, 185, 6.99, 0, 1, 0, 1),
      ('Oath of Brass Rivers', _CP, _TEC, 3, 'Epic fantasy', 108000, 900, 125, 6.99, 0, 1, 0, 0),
      ('The Hollow Sunrise', _CP, _TEC, 4, 'Epic fantasy', 112000, 520, 100, 6.99, 0, 0, 0, 0),
      ('Crown of Last Embers', _CP, _TEC, 5, 'Epic fantasy', 116000, 'L', 110, 6.99, 0, 2, 0, 2),
      ('The Tidebound Cartographer', _CP, _TR, 1, 'Sea fantasy', 90000, 1080, 380, 0.99, 1, 0, 0, 0),
      ('Salt and Lantern Sky', _CP, _TR, 2, 'Sea fantasy', 94000, 600, 65, 4.99, 1, 0, 0, 0),
      ('The Kelp Throne', _CP, _TR, 3, 'Sea fantasy', 98000, 'L35', 90, 5.99, 1, 0, 0, 0),
      ('A Winter at Saltmere', _TP, 'Standalone', 0, 'Cosy mystery', 76000, 830, 70, 5.99, 0, 0, 1, 0),
      ("The Glassmaker's Orchard", _CP, 'Standalone', 0, 'Epic fantasy', 118000, 560, 55, 6.99, 0, 0, 0, 1),
      ('Lantern Bay Mysteries Books 1-3', _TP, 'Box set', 0, 'Cosy mystery', 245000, 780, 60, 9.99, 0, 0, 0, 1),
      ('The Ember Crown Books 1-3', _CP, 'Box set', 0, 'Epic fantasy', 310000, 380, 48, 10.99, 0, 0, 0, 0)]
_NARR = {'The Glassmaker\'s Orchard': ('Gideon Falk', 450.0), 'Crown of Last Embers': ('Gideon Falk', 500.0)}       # narrator and rate per finished hour (the audio drag)
_FMTF = {'Paperback': 0.24, 'Hardcover': 0.035, 'Large print': 0.05, 'Audiobook': 0.08}
_FMTF_T = {(1, 'Audiobook'): 0.09, (2, 'Audiobook'): 0.09, (3, 'Audiobook'): 0.08, (7, 'Audiobook'): 0.05, (20, 'Audiobook'): 0.012, (21, 'Audiobook'): 0.05, (11, 'Paperback'): 0.20,
           (12, 'Paperback'): 0.20, (13, 'Paperback'): 0.20, (14, 'Paperback'): 0.20, (15, 'Paperback'): 0.20, (16, 'Paperback'): 0.14, (17, 'Paperback'): 0.17, (18, 'Paperback'): 0.17,
           (21, 'Paperback'): 0.28, (22, 'Paperback'): 0.28, (20, 'Paperback'): 0.20}
_DSHARE = {'Ebook': 0.045, 'Paperback': 0.09, 'Hardcover': 0.12, 'Large print': 0.05, 'Audiobook': 0.10}
SC = 1.3                                                                  # global sales scale
_SEAS = {1: 1.12, 2: 1.05, 3: 1.0, 4: 0.97, 5: 0.93, 6: 0.88, 7: 0.84, 8: 0.86, 9: 0.97, 10: 1.04, 11: 1.12, 12: 1.18}


def _build_catalogue():
    titles, eds = [], []
    for i, (name, pen, ser, order, genre, words, rel, A, price, ex, hc, lp, au) in enumerate(_T, 1):
        rd = LAUNCH_DATE if rel == 'L' else (LAUNCH_DATE + day(35) if rel == 'L35' else TODAY - day(rel))
        pages = int(round(words / 260.0))
        st = 'Released' if rd <= TODAY else ('Pre-order' if i == 15 else 'In production')
        titles.append(dict(title_id='TL-%03d' % i, idx=i, title=name, pen_name=pen, series=ser, series_order=order, genre=genre, words=words, pages=pages, release_date=rd, status=st,
                           exclusive=bool(ex), A=A, price=price, wide=not ex))
    TT = {t['title_id']: t for t in titles}
    n = 0

    def add(t, fmt, rd, status, price, pages, hours=0.0):
        nonlocal n
        n += 1
        b, pp = _FMT_BASE[fmt]
        pg = pages * 1.4 if fmt == 'Large print' else pages
        cost = R2(b + pp * pg)
        share = 0.35 if (fmt == 'Ebook' and price < 2.99) else _FMT_SHARE[fmt]
        eds.append(dict(edition_id='ED-%04d' % n, title_id=t['title_id'], title=t['title'], format=fmt, list_price=price, unit_cost=cost, royalty_share=share, identifier='LF-%010d' % (7400000000 + 137 * n),
                        pages=int(round(pg)) if fmt != 'Audiobook' else 0, hours=hours, release_date=rd, status=status))

    for t, row in zip(titles, _T):
        hc, lp, au = row[10], row[11], row[12]; rd = t['release_date']; i = t['idx']; pg = t['pages']
        stt = lambda r_, special=None: ('Live' if r_ <= TODAY else (special or 'Planned'))
        pre = 'Pre-order' if i == 15 else 'In production'
        add(t, 'Ebook', rd, stt(rd, pre), t['price'], pg)
        pbp = 12.99 if pg <= 300 else 13.99 if pg <= 360 else 14.99 if pg <= 460 else 27.99 if pg <= 1000 else 31.99
        add(t, 'Paperback', rd, stt(rd, pre), pbp, pg)
        if hc:
            r_ = rd + day(30) if hc == 1 else rd + day(60)
            add(t, 'Hardcover', r_, stt(r_), 24.99 if pg < 420 else 27.99, pg)
        if lp:
            r_ = rd + day(210) if lp == 1 else TODAY + day(75)
            add(t, 'Large print', r_, stt(r_), 17.99 if pg < 380 else 19.99, pg)
        if au:
            hrs = round(t['words'] / 9300.0, 1)
            if i == 21: hrs = round(sum(x['words'] for x in titles[:3]) / 9300.0, 1)
            r_ = rd + day(110) if au == 1 else LAUNCH_DATE + day(21)
            add(t, 'Audiobook', r_, stt(r_, 'In production'), 14.99 if hrs <= 9 else 17.99 if hrs <= 11.5 else 22.99 if hrs <= 14 else 29.99, 0, hrs)
    return titles, eds


def _cat(): return _raw('cat', _build_catalogue)
def _titles(): return _cat()[0]
def _eds(): return _cat()[1]
def _TT(): return {t['title_id']: t for t in _titles()}
def _EB(): return {x['title_id']: x for x in _eds() if x['format'] == 'Ebook'}
def _age_m(R, M): return (M.year - R.year) * 12 + M.month - R.month


def _ebook_exp(t, M):
    """expected ebook copies a month (all stores, before noise and ads) for title t in month M"""
    if t['idx'] == 15 and M >= _ms(PRE_START) and t['release_date'] > M + day(31):
        return 78.0 * SC
    a = _age_m(t['release_date'], M)
    if a < 0: return 0.0
    launch = 1 + 2.6 * math.exp(-a / 1.4); tail = 0.58 + 0.42 * math.exp(-a / 9.0)
    lift = 0.0
    if t['series'] in SERIES[:4]:
        for k in _titles():
            if k['series'] == t['series'] and k['series_order'] > t['series_order'] and k['release_date'] <= _eom(M):
                lift += (0.15 if t['series'] == _TR else (0.45 if t['series_order'] == 1 else 0.18)) * math.exp(-_age_m(k['release_date'], M) / 2.5)
    return t['A'] * SC * launch * tail * (1 + lift) * _SEAS[M.month]


def _exp(ed, M, TT=None):
    t = (TT or _TT())[ed['title_id']]; f = ed['format']
    rel = to_date(ed['release_date']) if isinstance(ed['release_date'], str) else ed['release_date']
    if t['idx'] == 15 and f in ('Ebook', 'Paperback'):
        base = _ebook_exp(t, M)
        return base * (1.0 if f == 'Ebook' else _FMTF_T.get((15, f), _FMTF[f]))
    if M < _ms(rel): return 0.0
    base = _ebook_exp(t, M)
    return base if f == 'Ebook' else base * _FMTF_T.get((t['idx'], f), _FMTF[f])


def _roy_unit(store, fmt, price, ed):
    """royalty per copy in home currency for one store (price is the price actually paid, home currency)"""
    if store == 'Direct store': return 0.0
    if fmt == 'Ebook':
        sh = {'Ebook store': (0.70 if 2.99 <= price <= 9.99 else 0.35), 'Wide distribution': 0.60, 'Library and lending': 0.55}[store]
        return max(0.0, price * sh - ed['unit_cost'])
    if fmt == 'Audiobook': return price * {'Audiobook store': 0.40, 'Wide distribution': 0.35, 'Library and lending': 0.30}[store]
    return max(0.0, price * (0.60 if store == 'Print-on-demand' else 0.45) - ed['unit_cost'])


_COUNTRY_W = {'Ebook store': [34, 28, 14, 6, 3, 7, 6, 2], 'Print-on-demand': [30, 36, 13, 5, 2, 6, 6, 2], 'Audiobook store': [28, 42, 10, 3, 1, 8, 7, 1],
              'Library and lending': [24, 38, 18, 2, 1, 7, 9, 1], 'Wide distribution': [22, 22, 12, 16, 10, 6, 6, 6], 'Direct store': [30, 30, 14, 6, 3, 8, 7, 2]}


def _store_w(t, fmt):
    ex = t['exclusive']
    if fmt == 'Ebook': return {'Ebook store': 1.0} if ex else {'Ebook store': .64, 'Wide distribution': .28, 'Library and lending': .08}
    if fmt == 'Audiobook': return {'Audiobook store': .88, 'Library and lending': .12} if ex else {'Audiobook store': .70, 'Wide distribution': .20, 'Library and lending': .10}
    return {'Print-on-demand': 1.0} if ex else {'Print-on-demand': .76, 'Wide distribution': .24}


# ------------------------------------------------------------------ price promotions (they lift the ebook units of a month)
def _promos():
    def build():
        r = rng('promo'); TT = _titles(); out = []
        pool = [1, 7, 11, 16, 21, 22, 2, 12, 19, 6, 14, 10, 20, 5, 8, 13]
        for i in range(22):
            M1 = month_start(23 - int(i * 1.02)); d0 = M1 + day(r.randint(2, 21))
            if d0 > TODAY - day(10): d0 = TODAY - day(10 + (i % 5))
            for _ in range(30):
                tt = TT[pool[(i * 3 + _) % len(pool)] - 1]
                if tt['release_date'] < d0 - day(60) and tt['release_date'] <= TODAY: break
            kind = 'Box set sale' if tt['series'] == 'Box set' else r.choice(['Price drop', 'Price drop', 'Holiday sale', 'Series sale'])
            days = r.randint(4, 10) if kind == 'Box set sale' else r.randint(3, 7)
            out.append(dict(tid=tt['title_id'], kind=kind, start=d0, days=days, normal=tt['price'], promo=round(max(0.99, tt['price'] * r.choice([0.17, 0.33, 0.5])), 2) if tt['price'] > 2 else 0.99,
                            cost=float(r.choice([0, 0, 25, 45, 60, 90, 120]))))
        out.append(dict(tid='TL-001', kind='Price drop', start=TODAY + day(14), days=5, normal=2.99, promo=0.99, cost=45.0, planned=True))
        out.sort(key=lambda x: x['start'])
        return out
    return _raw('promos', build)


def _promo_mult():
    mult, pf = {}, {}
    for p in _promos():
        if p.get('planned') or p['start'] > TODAY: continue
        for d in range(p['days']):
            dd = p['start'] + day(d)
            k = (p['tid'], _ms(dd)); mult[k] = mult.get(k, 0.0) + 2.0 / 30.0
            pf[k] = pf.get(k, 0.0) + (1 - p['promo'] / p['normal']) / 30.0
    return mult, pf


# ------------------------------------------------------------------ ads
_AUD = {'Cosy mystery': ['cosy mystery readers', 'cosy series starters', 'similar authors', 'backlist readers'], 'Crime mystery': ['crime fiction readers', 'series starters', 'similar authors', 'backlist readers'],
        'Epic fantasy': ['epic fantasy readers', 'series starters', 'similar authors', 'backlist readers'], 'Sea fantasy': ['sea fantasy readers', 'series starters', 'similar authors', 'backlist readers']}
_PCONV = {'Store ads': 0.07, 'Social ads': 0.045, 'Search ads': 0.05}
_PCTR = {'Store ads': 0.004, 'Social ads': 0.006, 'Search ads': 0.003}
# title idx, platform, start (days ago), end (days ago or None), budget a day, return target (royalties per unit of spend), status
_AD_FIXED = [(1, 'Store ads', 300, None, 8, 2.0, 'Running'), (11, 'Store ads', 260, None, 8, 1.6, 'Running'), (7, 'Store ads', 200, None, 6, 1.25, 'Running'),
             (16, 'Store ads', 75, None, 12, 0.45, 'Running'), (15, 'Social ads', 22, None, 10, 1.3, 'Running'), (22, 'Search ads', 120, None, 6, 1.35, 'Running'),
             (6, 'Social ads', 140, None, 9, 1.1, 'Running'), (12, 'Search ads', 180, 20, 9, 1.2, 'Paused')]


def _short(t):
    if t['series'] in SERIES[:4]: return '%s %d' % (t['series'].replace('The ', '').replace(' Mysteries', '').replace(' Cases', '').replace(' Realms', ''), t['series_order'])
    return t['title'].replace('Lantern Bay Mysteries ', 'Lantern Bay ').replace('The Ember Crown ', 'Ember Crown ').replace("The Glassmaker's Orchard", 'Glassmaker Orchard')[:28]


def _ad_rps(t):
    ed = _EB()[t['title_id']]
    unit = max(0.05, ed['list_price'] * (0.70 if ed['list_price'] >= 2.99 else 0.35) - ed['unit_cost'])
    return unit + (t['pages'] * 0.35 * PAGE_READ_RATE if t['exclusive'] else 0.0), unit


def _ads():
    def build():
        r = rng('ads'); TT = _titles(); camps = []
        for (ti, pl, sa, ea, bud, R, stt) in _AD_FIXED: camps.append((ti, pl, TODAY - day(sa), (TODAY - day(ea)) if ea else None, bud, R, stt))
        pool = [1, 11, 7, 16, 2, 12, 21, 22, 19, 6, 14, 10, 20, 8, 13, 17, 3, 9]
        for i in range(22):
            ti = pool[i % len(pool)]; t = TT[ti - 1]
            for _ in range(10):
                st = TODAY - day(r.randint(70, 700)); du = r.randint(21, 140)
                if t['release_date'] < st: break
                ti = pool[(i + _ + 1) % len(pool)]; t = TT[ti - 1]
            en = min(st + day(du), TODAY - day(35))
            if en <= st + day(14): st = en - day(r.randint(21, 60))
            camps.append((ti, ['Store ads', 'Social ads', 'Search ads'][i % 3], st, en, r.choice([6, 8, 10, 12, 14, 16, 18]), round(r.uniform(0.55, 2.3), 2), 'Ended'))
        camps.sort(key=lambda c: c[2])
        rows, days_ = [], []; _used_names = set()
        for i, (ti, pl, st, en, bud, R, stt) in enumerate(camps, 1):
            t = TT[ti - 1]; rps, unit = _ad_rps(t); conv = _PCONV[pl] * r.uniform(0.85, 1.15)
            cpc = max(0.03, conv * rps / R)
            cid = 'AC-%03d' % i
            name = None
            for j_ in range(8):
                nm_ = '%s - %s' % (_short(t), _AUD[t['genre']][(i + ti + j_) % 4] if j_ < 4 else _AUD[t['genre']][(i + ti + j_) % 4] + ' %d' % (j_ - 2))
                if nm_ not in _used_names: name = nm_; break
            _used_names.add(name)
            camps_row = dict(campaign_id=cid, campaign=name, title_id=t['title_id'], title=t['title'], platform=pl, start_date=iso(st), end_date=iso(en) if en else '', status=stt,
                             daily_budget=float(bud), bid=round(cpc, 2))
            rows.append(camps_row)
            d = st; last = en or TODAY
            while d <= last and d <= TODAY:
                if d < t['release_date'] and not (t['idx'] == 15 and d >= PRE_START):
                    d += day(1); continue
                spend = bud * r.uniform(0.6, 1.0) * (0.85 if d.weekday() >= 5 else 1.0)
                clicks = spend / cpc * r.uniform(0.9, 1.1)
                sales_f = clicks * conv * r.uniform(0.85, 1.15)
                sales = int(sales_f + r.random())
                imp = int(clicks / _PCTR[pl] * r.uniform(0.9, 1.1))
                pr = int(sales * t['pages'] * 0.35 * r.uniform(0.8, 1.2)) if t['exclusive'] else 0
                days_.append(dict(date=d, campaign_id=cid, campaign=name, title_id=t['title_id'], platform=pl, spend=R2(spend), impressions=imp, clicks=int(round(clicks)), sales=sales,
                                  page_reads=pr, royalties=R2(sales * unit + pr * PAGE_READ_RATE)))
                d += day(1)
        return rows, days_
    return _raw('ads', build)


def campaign_rows(n=None): return _thin([dict(x) for x in _ads()[0]], n)


def ad_day_rows(n=None):
    out = [dict(ad_id='AD-%05d' % i, **dict(x, date=iso(x['date']), month=iso(_ms(x['date'])))) for i, x in enumerate(_ads()[1], 1)]
    return _thin(sorted(out, key=lambda x: x['date']), n)


def _ad_units():
    u, pg = {}, {}
    for x in _ads()[1]:
        k = (x['title_id'], _ms(x['date'])); u[k] = u.get(k, 0) + x['sales']; pg[k] = pg.get(k, 0) + x['page_reads']
    return u, pg


# ------------------------------------------------------------------ sales world: ledger, page reads, direct orders
def _sales_world():
    r = rng('sales'); TT = _TT(); eds = _eds(); adu, adp = _ad_units(); pm, pf = _promo_mult(); months = months24()
    ledger, pages, orders = [], [], []
    ship_home = {c: _CTRY[c][2] for c in COUNTRIES}
    oid = 0
    for ed in eds:
        t = TT[ed['title_id']]; f = ed['format']
        for M in months:
            frac = CUR_FRAC if M == CUR else 1.0
            e = _exp(ed, M, TT)
            extra = adu.get((t['title_id'], M), 0) if f == 'Ebook' else 0
            if e <= 0 and not extra: continue
            noise = r.uniform(0.86, 1.14)
            if f == 'Ebook': e *= (1 + pm.get((t['title_id'], M), 0.0))
            tu = int(e * frac * noise + r.random())
            dirsh = _DSHARE[f] * (1.4 if t['exclusive'] and f == 'Ebook' else 1.0)
            dn = int(tu * dirsh + r.random()) if t['idx'] != 15 or f != 'Ebook' or M < CUR else 0
            dn = min(dn, tu)
            nd = tu - dn
            sw = _store_w(t, f); sl = list(sw); parts = _split(r, nd, [sw[s] for s in sl])
            alloc = dict(zip(sl, parts))
            if extra: alloc['Ebook store'] = alloc.get('Ebook store', 0) + extra
            ppf = 1 - pf.get((t['title_id'], M), 0.0) if f == 'Ebook' else 1.0
            for s, u in alloc.items():
                if u <= 0: continue
                cu = _split(r, u, _COUNTRY_W[s])
                for c, uc in zip(COUNTRIES, cu):
                    if uc <= 0: continue
                    cur = _CTRY[c][0]; rate = fx_rate(cur, M)
                    price = round(ed['list_price'] * ppf, 2)
                    ru = _roy_unit(s, f, price, ed)
                    ret = int(uc * 0.03 + r.random()) if (f != 'Ebook' and uc >= 8) else 0
                    ledger.append(dict(month=M, edition_id=ed['edition_id'], title_id=t['title_id'], title=t['title'], format=f, store=s, country=c, currency=cur, units=uc, returns=ret,
                                       gross=R2(uc * price / rate), royalty=R2(uc * ru / rate), rate=rate))
            # direct store orders for this edition-month
            if dn > 0:
                left = dn
                while left > 0:
                    q = min(left, _wchoice(r, [1, 2, 3], [88, 9, 3])); left -= q
                    dd = M + day(r.randint(0, (min(TODAY, _eom(M)) - M).days))
                    c = _wchoice(r, COUNTRIES, _COUNTRY_W['Direct store']); cur = _CTRY[c][0]; rate = fx_rate(cur, M)
                    pr_home = ed['list_price'] * ppf
                    disc = r.choice([0.1, 0.15, 0.2, 0.25]) if r.random() < 0.12 else 0.0
                    up = round(pr_home / rate, 2)
                    gross_l = round(q * up * (1 - disc), 2); tax_l = round(gross_l * _CTRY[c][1], 2)
                    prt = f in ('Paperback', 'Hardcover', 'Large print')
                    ship_l = round(SHIPPING_CHARGE / rate, 2) if prt else 0.0
                    fee_l = round((gross_l + tax_l + ship_l) * PAYMENT_FEE_PCT + PAYMENT_FEE_FIXED / rate, 2)
                    deliv = R2(ed['unit_cost'] * q + (ship_home[c] if prt else 0.0))
                    net = R2((gross_l + ship_l - fee_l) * rate - deliv)
                    oid += 1
                    orders.append(dict(date=dd, edition_id=ed['edition_id'], title_id=t['title_id'], title=t['title'], format=f, country=c, currency=cur, qty=q, unit_price=up,
                                       discount=R2(q * up * disc), tax_collected=tax_l, shipping_charged=ship_l, payment_fee=fee_l, delivery_cost=deliv, rate=rate, net_home=net, month=M))
            # page reads (exclusive titles, ebook edition)
            if f == 'Ebook' and t['exclusive']:
                base = (e * frac * noise) * t['pages'] * 0.55
                pg = int(base + adp.get((t['title_id'], M), 0))
                if pg > 0:
                    rate_pp = round(PAGE_READ_RATE * (1 + 0.06 * math.sin(M.month * 0.9 + t['idx'])), 5)
                    pages.append(dict(month=M, edition_id=ed['edition_id'], title_id=t['title_id'], title=t['title'], pages_read=pg, rate=rate_pp, income=R2(pg * rate_pp)))
    # direct orders into the ledger
    agg = {}
    for o in sorted(orders, key=lambda o: (o['month'], o['edition_id'], o['date'])):
        k = (o['month'], o['edition_id'], o['country'])
        a = agg.setdefault(k, dict(month=o['month'], edition_id=o['edition_id'], title_id=o['title_id'], title=o['title'], format=o['format'], store='Direct store', country=o['country'],
                                   currency=o['currency'], units=0, returns=0, gross=0.0, royalty=0.0, rate=o['rate']))
        a['units'] += o['qty']; a['gross'] += o['qty'] * o['unit_price'] - o['discount']; a['royalty'] += o['net_home'] / o['rate']
    for a in agg.values(): a['gross'] = R2(a['gross']); a['royalty'] = R2(a['royalty'])
    ledger += list(agg.values())
    so = {s: i for i, s in enumerate(STORES)}; co = {c: i for i, c in enumerate(COUNTRIES)}
    ledger.sort(key=lambda x: (x['month'], x['edition_id'], so[x['store']], co[x['country']]))
    pages.sort(key=lambda x: (x['month'], x['edition_id']))
    orders.sort(key=lambda o: (o['date'], o['edition_id']))
    return ledger, pages, orders


def _sw(): return _raw('sw', _sales_world)


def sales_rows(n=None):
    out = [dict(sale_id='SL-%05d' % i, month=iso(x['month']), edition_id=x['edition_id'], title_id=x['title_id'], title=x['title'], format=x['format'], store=x['store'], country=x['country'],
                currency=x['currency'], units=x['units'], returns=x['returns'], gross=x['gross'], royalty=x['royalty'], rate=x['rate'], royalty_home=R2(x['royalty'] * x['rate']))
           for i, x in enumerate(_sw()[0], 1)]
    return _thin(out, n)


def pageread_rows(n=None):
    return _thin([dict(read_id='PR-%04d' % i, month=iso(x['month']), edition_id=x['edition_id'], title_id=x['title_id'], title=x['title'], pages_read=x['pages_read'], rate=x['rate'],
                       income=x['income']) for i, x in enumerate(_sw()[1], 1)], n)


def direct_order_rows(n=None):
    out = []
    for i, o in enumerate(_sw()[2], 1):
        out.append(dict(order_id='DO-%05d' % i, date=iso(o['date']), month=iso(o['month']), country=o['country'], currency=o['currency'], edition_id=o['edition_id'], title=o['title'], format=o['format'],
                        qty=o['qty'], unit_price=o['unit_price'], discount=o['discount'], tax_collected=o['tax_collected'], shipping_charged=o['shipping_charged'], payment_fee=o['payment_fee'],
                        delivery_cost=o['delivery_cost'], rate=o['rate'], net_home=o['net_home']))
    return _thin(out, n)


def _month_store():
    """(month, store) -> earned home amount (royalties of the ledger plus page-read income for the ebook store)"""
    e = {}
    for x in _sw()[0]:
        k = (x['month'], x['store']); e[k] = e.get(k, 0.0) + x['royalty'] * x['rate']
    for x in _sw()[1]:
        k = (x['month'], 'Ebook store'); e[k] = e.get(k, 0.0) + x['income']
    return e


# ------------------------------------------------------------------ statements and payments received
def _stmts():
    def build():
        r = rng('stmt'); e = _month_store(); out = []; k = 0
        pre = [add_months(HISTORY_START, -j) for j in (3, 2, 1)]
        for M in pre + months24():
            for s in STORES:
                amt = R2(e.get((M, s), 0.0))
                if M in pre:
                    amt = R2(e.get((HISTORY_START, s), 0.0) * r.uniform(0.9, 1.05))
                    if _eom(M) + day(SDELAY[s]) < HISTORY_START: continue
                if amt <= 0: continue
                k += 1
                eom = _eom(M); exp_on = eom + day(SDELAY[s])
                row = dict(month=M, store=s, statement_amount=amt, expected_on=exp_on, paid_on='', received=0.0, fee=0.0, fx_loss=0.0, status='Open', story=False)
                if M == CUR: row['status'] = 'Open'; row['expected_on'] = exp_on
                else:
                    if exp_on > TODAY: row['status'] = 'Expected'
                    else:
                        po = min(exp_on + day(r.randint(0, 3)), TODAY)
                        fee = 0.0 if s == 'Direct store' else float(r.choice([5, 8, 10, 12, 15]))
                        fxl = 0.0 if s == 'Direct store' else R2(amt * r.uniform(0.002, 0.011))
                        row.update(paid_on=po, fee=fee, fx_loss=fxl, received=R2(amt - fee - fxl), status='Paid')
                out.append(row)
        # the story: the wide-distribution payment for a month about 5 months back arrived 22% short
        cand = [x for x in out if x['store'] == 'Wide distribution' and x['month'] == month_start(5)]
        x = cand[0]; x['story'] = True
        short = R2(x['statement_amount'] * 0.78)
        x.update(received=short, fee=10.0, fx_loss=0.0, status='Short-paid')
        return out
    return _raw('stmts', build)


def statement_rows(n=None):
    out = []
    for i, x in enumerate(_stmts(), 1):
        out.append(dict(statement_id='ST-%03d' % i, month=iso(x['month']), store=x['store'], statement_amount=x['statement_amount'], expected_on=iso(x['expected_on']),
                        paid_on=iso(x['paid_on']) if x['paid_on'] else '', received=x['received'] if x['paid_on'] else 0.0, status=x['status']))
    return _thin(out, n)


def payment_rows(n=None):
    out = []; k = 0
    for i, x in enumerate(_stmts(), 1):
        if not x['paid_on']: continue
        k += 1
        out.append(dict(payment_id='PY-%04d' % k, statement_id='ST-%03d' % i, store=x['store'], month=iso(x['month']), received_on=iso(x['paid_on']), statement_amount=x['statement_amount'],
                        fee=x['fee'], fx_loss=x['fx_loss'], received=x['received']))
    out.sort(key=lambda x: x['received_on'])
    for j, x in enumerate(out, 1): x['payment_id'] = 'PY-%04d' % j
    return _thin(out, n)


# ------------------------------------------------------------------ production: jobs and contractor payments
def _jobs():
    def build():
        r = rng('jobs'); TT = _titles(); eds = _eds(); jobs = []; pays = []
        def job(t, kind, who, quote, start, due, ed=None, units=0.0, rate=0.0, delivered=None, force_open=False):
            jobs.append(dict(title_id=t['title_id'], title=t['title'], edition_id=ed['edition_id'] if ed else '', kind=kind, contractor=who, quote=R2(quote), start_date=start, due_date=due,
                             units=units, unit_rate=rate, delivered_on=delivered, force_open=force_open))
        for t in TT:
            R, w, k = t['release_date'], t['words'], t['words'] / 1000.0; i = t['idx']; eb = [e for e in eds if e['title_id'] == t['title_id']]
            if t['series'] == 'Box set':
                job(t, 'Cover design', 'Ines Carvalho', 620, R - day(80), R - day(60)); job(t, 'Formatting', 'Tomasz Wrona', 190, R - day(50), R - day(35))
            else:
                first = t['series_order'] in (0, 1)
                job(t, 'Developmental edit', 'Priya Nandakumar', 25 * k * (1.0 if first else 0.6) * r.uniform(0.95, 1.05), R - day(200), R - day(150), units=k, rate=25.0)
                job(t, 'Copy edit', 'Leopold Brandt', 18 * k * r.uniform(0.95, 1.05), R - day(125), R - day(95), units=k, rate=18.0)
                job(t, 'Proofread', 'Leopold Brandt', 7 * k * r.uniform(0.95, 1.05), R - day(60), R - day(40), units=k, rate=7.0)
                job(t, 'Cover design', 'Ines Carvalho', (700 if first else 480) + r.choice([0, 30, 60]), R - day(120), R - day(75))
                job(t, 'Formatting', 'Tomasz Wrona', 160 + (20 if t['pages'] > 400 else 0), R - day(35), R - day(20))
            for e in eb:
                if e['format'] == 'Large print': job(t, 'Formatting', 'Tomasz Wrona', 90.0, to_date(e['release_date']) - day(40), to_date(e['release_date']) - day(25), ed=e)
                if e['format'] == 'Hardcover': job(t, 'Formatting', 'Tomasz Wrona', 110.0, to_date(e['release_date']) - day(40), to_date(e['release_date']) - day(25), ed=e)
                if e['format'] == 'Audiobook' and t['series'] != 'Box set':
                    who, rate = _NARR.get(t['title'], ('Amara Oyelaran', 285.0)); hrs = e['hours']
                    ra = to_date(e['release_date'])
                    if i == 15: st, du = TODAY - day(75), TODAY - day(4)
                    else: st, du = ra - day(100), ra - day(20)
                    job(t, 'Narration', who, round(hrs * rate, -1), st, du, ed=e, units=hrs, rate=rate)
            sp = sum(1 for e in eb) * 28.0
            job(t, 'Setup and identifiers', OWNER, sp, R - day(30), R - day(25))
        # translation in progress for book 1 of the first series
        t1 = TT[0]; job(t1, 'Translation', 'Yuki Tanabe', round(t1['words'] / 1000.0 * 55, -1), TODAY - day(70), TODAY + day(40), units=t1['words'] / 1000.0, rate=55.0)
        # one overdue job (the third book of the sea series: copy edit late)
        for j in jobs:
            if j['title_id'] == 'TL-018' and j['kind'] == 'Copy edit': j['due_date'] = TODAY - day(6); j['force_open'] = True
        jid = 0; jrows = []
        for j in sorted(jobs, key=lambda j: (j['start_date'], j['title_id'])):
            jid += 1; j['job_id'] = 'JB-%03d' % jid
            q = j['quote']; d0, du = j['start_date'], j['due_date']
            deliv = None
            if du <= TODAY and not j['force_open']: deliv = min(du + day(r.randint(-3, 6)), TODAY)
            j['delivered_on'] = deliv
            stages = [('Final', q, (deliv + day(r.randint(5, 12)) if deliv else du + day(10)))] if q < 300 else \
                     ([('Deposit', R2(q * 0.25), d0), ('Milestone', R2(q * 0.35), d0 + (du - d0) // 2), ('Final', R2(q * 0.40), (deliv + day(r.randint(5, 12))) if deliv else du + day(10))] if j['kind'] == 'Narration'
                      else [('Deposit', R2(q * 0.30), d0), ('Final', R2(q * 0.70), (deliv + day(r.randint(5, 12))) if deliv else du + day(10))])
            if j['kind'] == 'Narration' and j['title_id'] == 'TL-015':   # the story invoice: the final payment falls due in 3 days
                stages = [('Deposit', R2(q * 0.15), d0), ('Milestone', R2(q * 0.15), d0 + day(35)), ('Final', R2(q - R2(q * 0.15) - R2(q * 0.15)), TODAY + day(3))]
            paid = 0.0
            for st, a, dd in stages:
                if dd <= TODAY - day(0) and not (j['force_open'] and st == 'Final'): ps = 'Paid'; paid += a
                elif dd <= TODAY + day(14): ps = 'Due'
                else: ps = 'Scheduled'
                if j['kind'] == 'Narration' and j['title_id'] == 'TL-015' and st == 'Final': ps = 'Due'
                pays.append(dict(job_id=j['job_id'], title_id=j['title_id'], contractor=j['contractor'], stage=st, date=dd, amount=a, status=ps))
            j['paid'] = R2(paid)
            if paid >= q - 0.01: stt = 'Paid'
            elif deliv: stt = 'Delivered'
            elif d0 <= TODAY: stt = 'In progress'
            elif d0 <= TODAY + day(30): stt = 'Booked'
            else: stt = 'Quoted'
            j['status'] = stt; jrows.append(j)
        pays.sort(key=lambda p: (p['date'], p['job_id']))
        for i, p in enumerate(pays, 1): p['cpay_id'] = 'CP-%04d' % i
        return jrows, pays
    return _raw('jobs', build)


def job_rows(n=None):
    out = []
    for j in _jobs()[0]:
        out.append(dict(job_id=j['job_id'], title_id=j['title_id'], title=j['title'], edition_id=j['edition_id'], kind=j['kind'], contractor=j['contractor'], quote=j['quote'], units=round(j['units'], 1),
                        unit_rate=j['unit_rate'], start_date=iso(j['start_date']), due_date=iso(j['due_date']), delivered_on=iso(j['delivered_on']) if j['delivered_on'] else '', paid=j['paid'],
                        balance=R2(j['quote'] - j['paid']), status=j['status']))
    return _thin(out, n)


def jobpay_rows(n=None):
    return _thin([dict(cpay_id=p['cpay_id'], job_id=p['job_id'], title_id=p['title_id'], contractor=p['contractor'], stage=p['stage'], date=iso(p['date']), month=iso(_ms(p['date'])),
                       amount=p['amount'], status=p['status']) for p in _jobs()[1]], n)


def title_cost(tid): return R2(sum(j['quote'] for j in _jobs()[0] if j['title_id'] == tid))


def _before(t):
    """royalties earned before the first month of the ledger (expected model, ebook-store mix), per title"""
    tot = 0.0; M = _ms(t['release_date'])
    eds = [e for e in _eds() if e['title_id'] == t['title_id']]
    if t['idx'] == 15: return 0.0
    TT = _TT()
    while M < HISTORY_START:
        for ed in eds:
            u = _exp(ed, M, TT)
            if u <= 0: continue
            roy = _roy_unit('Print-on-demand' if ed['format'] in ('Paperback', 'Hardcover', 'Large print') else ('Audiobook store' if ed['format'] == 'Audiobook' else 'Ebook store'), ed['format'], ed['list_price'], ed)
            tot += u * roy * 0.95
            if ed['format'] == 'Ebook' and t['exclusive']: tot += u * t['pages'] * 0.55 * PAGE_READ_RATE
        M = add_months(M, 1)
    return round(tot, -1)


def title_rows(n=None):
    pre = sum(x['units'] for x in _sw()[0] if x['title_id'] == 'TL-015')
    out = []
    for t in _titles():
        out.append(dict(title_id=t['title_id'], title=t['title'], pen_name=t['pen_name'], series=t['series'], series_order=t['series_order'], genre=t['genre'], words=t['words'], pages=t['pages'],
                        release_date=iso(t['release_date']), status=t['status'], exclusive=t['exclusive'], preorders=pre if t['idx'] == 15 else 0, royalty_before=_raw('before' + t['title_id'], lambda t=t: _before(t))))
    return _thin(out, n)


def edition_rows(n=None):
    return _thin([dict(x, release_date=iso(x['release_date'])) for x in _eds()], n)


def title_royalty(tid):
    s = sum(x['royalty'] * x['rate'] for x in _sw()[0] if x['title_id'] == tid) + sum(x['income'] for x in _sw()[1] if x['title_id'] == tid)
    return R2(s + _raw('before' + tid, lambda: _before(_TT()[tid])))


def series_rows(n=None):
    out = []
    for i, s in enumerate(SERIES, 1):
        ts = [t for t in _titles() if t['series'] == s]
        planned = {_LBM: 7, _QHC: 5, _TEC: 6, _TR: 4}.get(s, len(ts))
        out.append(dict(series_id='SR-%02d' % i, series=s, pen_name=ts[0]['pen_name'] if s not in ('Standalone', 'Box set') else 'Both pen names', genre=ts[0]['genre'] if s not in ('Standalone', 'Box set') else 'Mixed',
                        books_planned=planned, books_released=sum(1 for t in ts if t['release_date'] <= TODAY), gap_days_plan=330 if s in SERIES[:4] else 0,
                        expected_readthrough={_LBM: 0.62, _QHC: 0.58, _TEC: 0.65, _TR: 0.35}.get(s, 0.0)))
    return out


# ------------------------------------------------------------------ newsletter, subscribers, swaps
def _news():
    def build():
        r = rng('news'); out = []; size = 1900; d = HISTORY_START + day(3)
        while d.weekday() != 3: d += day(1)
        launch_months = {_ms(t['release_date']) for t in _titles() if t['release_date'] >= HISTORY_START - day(40)}
        while d <= TODAY:
            near = any(0 <= (t['release_date'] - d).days <= 10 or 0 <= (d - t['release_date']).days <= 6 for t in _titles() if t['release_date'] >= HISTORY_START - day(40))
            promo = any(p['start'] <= d <= p['start'] + day(p['days']) for p in _promos() if not p.get('planned'))
            kind = 'Launch push' if near else ('Price promotion' if promo else _wchoice(r, ['Story update', 'Swap feature', 'Re-engagement'], [60, 25, 15]))
            new = int(r.uniform(14, 34) * (1.5 if kind in ('Swap feature', 'Launch push') else 1.0)) + (r.randint(20, 60) if kind == 'Swap feature' else 0)
            sent = int(size * r.uniform(0.97, 1.0))
            op = r.uniform(0.38, 0.52) * (1.06 if d >= TODAY - day(300) else 1.0); cl = r.uniform(0.04, 0.085) * (1.4 if kind in ('Launch push', 'Price promotion') else 1.0)
            unsub = max(1, int(sent * r.uniform(0.001, 0.004)))
            clicks = int(sent * cl); s7 = int(clicks * r.uniform(0.07, 0.14) * (1.6 if kind in ('Launch push', 'Price promotion') else 1.0))
            out.append(dict(date=d, kind=kind, list_size=size, sent=sent, opens=int(sent * op), clicks=clicks, unsubscribes=unsub, new_subscribers=new, sales_7d=s7, royalty_7d=R2(s7 * r.uniform(2.6, 3.9))))
            size += new - unsub
            d += day(7 if r.random() < 0.8 else 4)
        return out
    return _raw('news', build)


def newsletter_rows(n=None):
    return _thin([dict(send_id='NL-%03d' % i, date=iso(x['date']), month=iso(_ms(x['date'])), kind=x['kind'], list_size=x['list_size'], sent=x['sent'], opens=x['opens'], clicks=x['clicks'],
                       unsubscribes=x['unsubscribes'], new_subscribers=x['new_subscribers'], sales_7d=x['sales_7d'], royalty_7d=x['royalty_7d']) for i, x in enumerate(_news(), 1)], n)


def _swaps():
    def build():
        r = rng('swaps'); out = []; d = HISTORY_START + day(20); k = 0
        names = ['Partner author %02d' % i for i in range(1, 15)]
        while d <= TODAY - day(3):
            k += 1; paid = r.random() < 0.38
            out.append(dict(date=d, partner=names[k % len(names)], kind='Paid promotion' if paid else 'Newsletter swap', cost=float(r.choice([25, 40, 60, 90, 120, 180])) if paid else float(r.choice([0, 0, 0, 15])),
                            subscribers=int(r.uniform(25, 140) * (1.2 if paid else 1.0)), clicks=int(r.uniform(60, 420)), sales_7d=int(r.uniform(2, 24)), title_id=_titles()[[0, 10, 6, 15, 1, 11][k % 6]]['title_id']))
            d += day(r.randint(14, 30))
        return out
    return _raw('swaps', build)


def swap_rows(n=None):
    TT = _TT()
    return _thin([dict(swap_id='SW-%03d' % i, date=iso(x['date']), partner=x['partner'], phone=fake_phone(400 + (i % 14)), kind=x['kind'], title=TT[x['title_id']]['title'], cost=x['cost'], subscribers=x['subscribers'], clicks=x['clicks'],
                       sales_7d=x['sales_7d']) for i, x in enumerate(_swaps(), 1)], n)


def subscriber_rows(n=None):
    r = rng('subs'); out = []; sw = {}
    for x in _swaps():
        k = (_ms(x['date']), x['kind']); sw[k] = sw.get(k, 0.0) + x['cost']
    ws = [38, 22, 14, 8, 10, 8]
    for M in months24():
        new = sum(x['new_subscribers'] for x in _news() if _ms(x['date']) == M); lost = sum(x['unsubscribes'] for x in _news() if _ms(x['date']) == M)
        parts = _split(r, new, ws)
        for s, p in zip(SUB_SOURCES, parts):
            cost = {'Newsletter swap': sw.get((M, 'Newsletter swap'), 0.0), 'Paid promotion': sw.get((M, 'Paid promotion'), 0.0), 'Reader magnet': 12.0, 'Event sign-up': 0.0,
                    'Store page link': 0.0, 'Direct store': 0.0}[s]
            out.append(dict(month=iso(M), source=s, new_subscribers=p, lost=int(lost * p / float(max(1, new)) + 0.5), cost=R2(cost)))
    return [dict(row_id='SU-%03d' % i, **x) for i, x in enumerate(_thin(out, n), 1)]


# ------------------------------------------------------------------ reviewers, advance copies, launch checklist
_RF = ['Elena', 'Marcus', 'Priya', 'Tomas', 'Amara', 'Nikolai', 'Sakura', 'Rafael', 'Leila', 'Declan', 'Fatima', 'Oskar', 'Ingrid', 'Kwame', 'Mei', 'Andre', 'Yara', 'Pavel', 'Noor', 'Callum',
       'Ayesha', 'Jorge', 'Hilda', 'Ravi', 'Dalia', 'Stefan', 'Chiamaka', 'Lucas', 'Sofia', 'Idris', 'Maren', 'Teodor', 'Aiko', 'Gabriela', 'Felix', 'Zainab', 'Anders', 'Lucia', 'Hamid', 'Bianca']
_RL = ['Okafor', 'Lindgren', 'Moreau', 'Castillo', 'Novak', 'Haddad', 'Ferreira', 'Brandt', 'Kowalski', 'Nakamura', 'Duarte', 'Salazar', 'Whitaker', 'Ostrowski', 'Bianchi', 'Hartmann', 'Mensah',
       'Rahimi', 'Larsen', 'Vidal', 'Petrov', 'Gallagher', 'Sorensen', 'Imani', 'Ruiz', 'Lombardi', 'Aydin', 'Fischer', 'Quinn', 'Tran']


def _reviewers():
    def build():
        r = rng('rev'); out = []
        for i in range(90):
            nm = '%s %s' % (_RF[i % len(_RF)], _RL[(i * 7 + i // 40) % len(_RL)])
            out.append(dict(name=nm, kind=_wchoice(r, REVIEWER_KINDS, [40, 22, 18, 10, 10]), email=fake_email(nm), joined_on=HISTORY_START - day(r.randint(-300, 900)) if False else TODAY - day(r.randint(40, 1200)),
                            p=r.uniform(0.2, 0.9)))
        return out
    return _raw('rev', build)


def reviewer_rows(n=None):
    arcs = _arcs(); out = []
    for i, x in enumerate(_reviewers(), 1):
        mine = [a for a in arcs if a['reviewer'] == x['name']]
        out.append(dict(reviewer_id='RV-%03d' % i, name=x['name'], kind=x['kind'], email=x['email'], phone=fake_phone(300 + i), joined_on=iso(x['joined_on']), copies_sent=sum(1 for a in mine if a['sent_on']),
                        reviews_posted=sum(1 for a in mine if a['status'] == 'Review posted')))
    return _thin(out, n)


def _arcs():
    def build():
        r = rng('arc'); revs = _reviewers(); out = []
        for t in _titles():
            R = t['release_date']
            if not (HISTORY_START <= R <= TODAY or t['idx'] == 15) or t['series'] == 'Box set': continue
            cnt = r.randint(30, 38) if t['idx'] != 15 else 40
            for j in range(cnt):
                rv = revs[(j * 5 + t['idx'] * 3) % len(revs)]
                due = R + day(7)
                if t['idx'] == 15:
                    out.append(dict(title_id=t['title_id'], title=t['title'], reviewer=rv['name'], sent_on='', due_on=due, status='Not sent', posted_on='')); continue
                sent = R - day(r.randint(26, 36))
                if r.random() < rv['p']:
                    po = R + day(r.randint(-2, 12))
                    if po > TODAY: out.append(dict(title_id=t['title_id'], title=t['title'], reviewer=rv['name'], sent_on=sent, due_on=due, status='Copy sent', posted_on=''))
                    else: out.append(dict(title_id=t['title_id'], title=t['title'], reviewer=rv['name'], sent_on=sent, due_on=due, status='Review posted', posted_on=po))
                else:
                    stt = _wchoice(r, ['Reminded', 'No reply', 'Copy sent'], [40, 45, 15]) if (TODAY - R).days > 20 else 'Copy sent'
                    out.append(dict(title_id=t['title_id'], title=t['title'], reviewer=rv['name'], sent_on=sent, due_on=due, status=stt, posted_on=''))
        return out
    return _raw('arcs', build)


def arc_rows(n=None):
    out = []
    for i, a in enumerate(_arcs(), 1):
        out.append(dict(arc_id='AR-%04d' % i, title_id=a['title_id'], title=a['title'], reviewer=a['reviewer'], sent_on=iso(a['sent_on']) if a['sent_on'] else '', due_on=iso(a['due_on']),
                        posted_on=iso(a['posted_on']) if a['posted_on'] else '', status=a['status']))
    return _thin(out, n)


def _launch_tasks():
    def build():
        r = rng('launch'); out = []
        for t in _titles():
            R = t['release_date']
            if t['idx'] not in (6, 10, 14, 17, 20, 22, 15, 18): continue
            for step, off, role in LAUNCH_STEPS:
                if t['idx'] == 18 and off > -60: continue
                due = R + day(off); owner = next(p['name'] for p in team if p['role'] == role)
                if t['idx'] == 15:
                    done = '' if (step in ('Reviewer copies sent', 'Teaser chapter ready') or due > TODAY) else min(due + day(r.randint(-4, 2)), TODAY)
                elif t['idx'] == 18:
                    done = '' if due > TODAY else min(due + day(r.randint(-3, 3)), TODAY)
                else:
                    done = min(due + day(r.randint(-4, 5)), TODAY) if due <= TODAY - day(2) else ''
                out.append(dict(title_id=t['title_id'], title=t['title'], step=step, owner=owner, due_date=due, done_on=done, status='Done' if done else 'Open'))
        return out
    return _raw('launch', build)


def launch_task_rows(n=None):
    return _thin([dict(task_id='LT-%03d' % i, title_id=x['title_id'], title=x['title'], step=x['step'], owner=x['owner'], due_date=iso(x['due_date']), done_on=iso(x['done_on']) if x['done_on'] else '',
                       status=x['status']) for i, x in enumerate(_launch_tasks(), 1)], n)


def promo_rows(n=None):
    r = rng('promo-rows'); TT = _TT(); out = []; ex = _month_ebook_units()
    for i, p in enumerate(_promos(), 1):
        t = TT[p['tid']]; base = max(1.0, ex.get((p['tid'], _ms(p['start'])), 30.0) / 30.0); planned = bool(p.get('planned'))
        before = int(base * p['days'] * r.uniform(0.9, 1.1)); during = int(base * p['days'] * r.uniform(2.0, 3.4)); after = int(base * p['days'] * r.uniform(1.0, 1.35))
        pgb = int(before * t['pages'] * 0.5) if t['exclusive'] else 0
        out.append(dict(promo_id='PM-%03d' % i, title_id=p['tid'], title=t['title'], kind=p['kind'], start_date=iso(p['start']), end_date=iso(p['start'] + day(p['days'] - 1)), days=p['days'],
                        normal_price=p['normal'], promo_price=p['promo'], cost=p['cost'], units_before=0 if planned else before, units_during=0 if planned else during,
                        units_after=0 if planned else after, pages_before=0 if planned else pgb, pages_during=0 if planned else int(pgb * r.uniform(1.0, 1.25)),
                        status='Planned' if planned else 'Done'))
    return _thin(out, n)


def _month_ebook_units():
    e = {}
    for x in _sw()[0]:
        if x['format'] == 'Ebook': e[(x['title_id'], x['month'])] = e.get((x['title_id'], x['month']), 0) + x['units']
    return e


# ------------------------------------------------------------------ events and hand-sold stock
_EV = [(690, 'Spring Book Fair', 'Book fair', 'Riverton', 9, 0.0), (610, 'Mill Street Signing', 'Signing at a shop', 'Marlow Green', 3, 0.0), (545, 'Harbour Fantasy Weekend', 'Genre convention', 'Port Alder', 16, 2),
       (470, 'Library Author Night', 'Library talk', 'Elmstead', 2, 0.0), (415, 'Holiday Makers Market', 'Author market', 'Riverton', 7, 0), (350, 'Indie Authors Day', 'Book fair', 'Kestrel Bay', 9, 1),
       (300, 'Coastal Mystery Weekend', 'Genre convention', 'Port Alder', 15, 2), (255, 'Riverside Author Market', 'Author market', 'Riverton', 6, 0), (205, 'Library Author Night', 'Library talk', 'Fenwick', 2, 0),
       (160, 'City Readers Festival', 'Book fair', 'Westbrook', 10, 1), (118, 'Mill Street Signing', 'Signing at a shop', 'Marlow Green', 3, 0), (75, 'Autumn Fantasy Con', 'Genre convention', 'Port Alder', 16, 2),
       (40, 'Riverside Author Market', 'Author market', 'Riverton', 6, 0), (min(10, max(1, TODAY.day - 1)), 'Harvest Book Fair', 'Book fair', 'Elmstead', 8, 0)]


def _events():
    def build():
        r = rng('events'); eds = [e for e in _eds() if e['format'] in ('Paperback', 'Hardcover', 'Large print')]; ev, lines = [], []
        main = [e for e in eds if e['format'] == 'Paperback' and e['title_id'] in ('TL-001', 'TL-002', 'TL-003', 'TL-007', 'TL-011', 'TL-012', 'TL-016', 'TL-019', 'TL-020', 'TL-021', 'TL-022', 'TL-006', 'TL-014')]
        extra = [e for e in eds if e['format'] != 'Paperback' and e['title_id'] in ('TL-001', 'TL-011', 'TL-002')]
        for i, (da, nm, kind, city, hours, nights) in enumerate(_EV, 1):
            d = TODAY - day(da)
            if d < HISTORY_START: continue
            tbl = {'Book fair': 120, 'Author market': 45, 'Genre convention': 210, 'Library talk': 0, 'Signing at a shop': 0}[kind] + r.choice([0, 15, 30])
            travel = {'Riverton': 22, 'Marlow Green': 14, 'Port Alder': 96, 'Elmstead': 18, 'Kestrel Bay': 64, 'Fenwick': 24, 'Westbrook': 58}[city] + r.randint(0, 20)
            lodging = nights * r.choice([85, 95, 110])
            ev.append(dict(date=d, name=nm, kind=kind, city=city, hours=float(hours), table_fee=float(tbl), travel_cost=float(travel), nights=int(nights), lodging_cost=float(lodging)))
            k = r.randint(5, 8); pick = r.sample(main, min(k, len(main))) + ([r.choice(extra)] if r.random() < 0.5 else [])
            scale = {'Genre convention': 1.5, 'Book fair': 1.0, 'Author market': 0.85, 'Library talk': 0.6, 'Signing at a shop': 0.5}[kind]
            if i == 5: scale = 0.35        # one event that did not pay
            for e in pick:
                if to_date(e['release_date']) > d: continue
                c = max(1, int(r.randint(2, 9) * scale + r.random()))
                lines.append(dict(event=len(ev), date=d, edition_id=e['edition_id'], title=e['title'], format=e['format'], copies=c, price=R2(e['list_price'] if r.random() < 0.8 else e['list_price'] - 1.0)))
        return ev, lines
    return _raw('events', build)


def event_rows(n=None):
    ev, lines = _events(); TT = _TT(); out = []
    for i, e in enumerate(ev, 1):
        ls = [l for l in lines if l['event'] == i]; sold = sum(l['copies'] for l in ls)
        taken = sold + int(sold * 0.25) + 6
        rev = R2(sum(l['copies'] * l['price'] for l in ls)); cogs = R2(sum(l['copies'] * next(x['unit_cost'] for x in _eds() if x['edition_id'] == l['edition_id']) for l in ls))
        r = rng('ev%d' % i)
        out.append(dict(event_id='EV-%03d' % i, date=iso(e['date']), name=e['name'], kind=e['kind'], city=e['city'], hours=e['hours'], table_fee=e['table_fee'], travel_cost=e['travel_cost'], nights=e['nights'],
                        lodging_cost=e['lodging_cost'], copies_taken=taken, copies_sold=sold, sales=rev, cost_of_copies=cogs, new_subscribers=int(sold * r.uniform(0.6, 1.4) + 4)))
    return _thin(out, n)


def event_sale_rows(n=None):
    ev, lines = _events()
    return _thin([dict(line_id='EL-%04d' % i, event_id='EV-%03d' % l['event'], date=iso(l['date']), edition_id=l['edition_id'], title=l['title'], format=l['format'], copies=l['copies'], price=l['price'])
                  for i, l in enumerate(lines, 1)], n)


def _stock():
    def build():
        ev, lines = _events(); eds = {e['edition_id']: e for e in _eds()}; stock = {}; out = []; r = rng('stock')
        by_ev = {}
        for l in lines: by_ev.setdefault(l['event'], []).append(l)
        for i, e in enumerate(ev, 1):
            need = {}
            for l in by_ev.get(i, []): need[l['edition_id']] = need.get(l['edition_id'], 0) + l['copies']
            for edid, c in need.items():
                if stock.get(edid, 0) < c + 4:
                    q = max(24, ((c * 2 + 11) // 12) * 12); ed = eds[edid]
                    out.append(dict(date=e['date'] - day(r.randint(12, 20)), edition_id=edid, title=ed['title'], format=ed['format'], move='Order in', copies=q, unit_cost=R2(ed['unit_cost'] + 0.65)))
                    stock[edid] = stock.get(edid, 0) + q
                out.append(dict(date=e['date'], edition_id=edid, title=eds[edid]['title'], format=eds[edid]['format'], move='Sold at event', copies=-c, unit_cost=R2(eds[edid]['unit_cost'] + 0.65)))
                stock[edid] -= c
            if r.random() < 0.5 and need:
                edid = r.choice(sorted(need))
                if stock[edid] > 3:
                    out.append(dict(date=e['date'] + day(1), edition_id=edid, title=eds[edid]['title'], format=eds[edid]['format'], move='Damaged or lost', copies=-1, unit_cost=R2(eds[edid]['unit_cost'] + 0.65)))
                    stock[edid] -= 1
        for edid in ('TL-001', 'TL-011'):   # review and gift copies, paperback of book 1
            ed = next(x for x in _eds() if x['title_id'] == edid and x['format'] == 'Paperback')
            if stock.get(ed['edition_id'], 0) > 6:
                out.append(dict(date=TODAY - day(20), edition_id=ed['edition_id'], title=ed['title'], format=ed['format'], move='Gift or review copy', copies=-4, unit_cost=R2(ed['unit_cost'] + 0.65)))
                stock[ed['edition_id']] -= 4
        out.sort(key=lambda x: (x['date'], x['edition_id']))
        return out
    return _raw('stock', build)


def stock_rows(n=None):
    return _thin([dict(stock_id='SK-%04d' % i, date=iso(x['date']), edition_id=x['edition_id'], title=x['title'], format=x['format'], move=x['move'], copies=x['copies'], unit_cost=x['unit_cost'])
                  for i, x in enumerate(_stock(), 1)], n)


# ------------------------------------------------------------------ rights deals (status and amounts only)
def _deals():
    def build():
        # title idx, kind, language, territory, signed ago, term years, fee, status, instalments [(days from signing or absolute ago/ahead, share)], agent share
        spec = [(1, 'Translation', 'German', 'German-speaking markets', 400, 7, 3200.0, 'Signed', [(400, 0.5, True), (-35, 0.5, False)]),
                (11, 'Translation', 'Spanish', 'Spanish-speaking markets', 260, 7, 2400.0, 'Delivered', [(260, 0.34, True), (120, 0.33, True), (-60, 0.33, False)]),
                (12, 'Audio licence', 'English', 'Worldwide, audio only', 190, 5, 1800.0, 'Signed', [(190, 0.5, True), (-20, 0.5, False)]),
                (7, 'Translation', 'French', 'French-speaking markets', 25, 7, 2000.0, 'Offer', []),
                (19, 'Translation', 'Italian', 'Italian-speaking markets', 600, 7, 1500.0, 'Paid in full', [(600, 0.5, True), (300, 0.5, True)]),
                (16, 'Other licence', 'English', 'Library edition', 480, 3, 900.0, 'Paid in full', [(480, 1.0, True)]),
                (2, 'Translation', 'German', 'German-speaking markets', 1900, 5, 1200.0, 'Expired', [(1900, 1.0, True)]),
                (20, 'Audio licence', 'English', 'Worldwide, audio only', 12, 5, 2800.0, 'Offer', []),
                (8, 'Translation', 'German', 'German-speaking markets', 330, 7, 2100.0, 'Signed', [(330, 0.5, True), (-70, 0.5, False)]),
                (14, 'Audio licence', 'English', 'Worldwide, audio only', 150, 5, 1600.0, 'Paid in full', [(150, 0.5, True), (40, 0.5, True)]),
                (5, 'Other licence', 'English', 'Large print edition', 60, 3, 800.0, 'Signed', [(60, 0.5, True), (-45, 0.5, False)]),
                (12, 'Translation', 'Portuguese', 'Portuguese-speaking markets', 18, 7, 1900.0, 'Offer', [])]
        out = []
        for i, (ti, kind, lang, terr, sg, term, fee, st, ins) in enumerate(spec, 1):
            t = _titles()[ti - 1]; signed = TODAY - day(sg); rows = []
            for (da, sh, rec) in ins:
                dd = (TODAY - day(da)) if da > 0 else (TODAY - day(da))
                if da <= 0: dd = TODAY + day(-da)
                rows.append(dict(due_date=dd, amount=R2(fee * sh), received_on=dd if rec else ''))
            out.append(dict(deal_id='RD-%02d' % i, title_id=t['title_id'], title=t['title'], kind=kind, language=lang, territory=terr, signed_on=signed if st != 'Offer' else '', offered_on=signed, term_years=term,
                            term_end=(signed + day(365 * term)) if st != 'Offer' else '', fee=fee, agent_pct=0.15, status=st, instalments=rows))
        return out
    return _raw('deals', build)


def deal_rows(n=None):
    out = []
    for d in _deals():
        rec = sum(x['amount'] for x in d['instalments'] if x['received_on'])
        out.append(dict(deal_id=d['deal_id'], title_id=d['title_id'], title=d['title'], kind=d['kind'], language=d['language'], territory=d['territory'], offered_on=iso(d['offered_on']),
                        signed_on=iso(d['signed_on']) if d['signed_on'] else '', term_years=d['term_years'], term_end=iso(d['term_end']) if d['term_end'] else '', fee=d['fee'], agent_pct=d['agent_pct'],
                        received=R2(rec), status=d['status']))
    return _thin(out, n)


def instalment_rows(n=None):
    out = []; k = 0
    for d in _deals():
        for x in d['instalments']:
            k += 1; out.append(dict(instalment_id='RI-%03d' % k, deal_id=d['deal_id'], due_date=iso(x['due_date']), amount=x['amount'], received_on=iso(x['received_on']) if x['received_on'] else ''))
    out.sort(key=lambda x: x['due_date'])
    for i, x in enumerate(out, 1): x['instalment_id'] = 'RI-%03d' % i
    return _thin(out, n)


# ------------------------------------------------------------------ expenses (not ads, not production, not event costs)
def expense_rows(n=None):
    def build():
        r = rng('exp'); out = []
        def add(d, cat, vendor, amt, pen='Shared'):
            if HISTORY_START <= d <= TODAY: out.append(dict(date=d, category=cat, vendor=vendor, amount=R2(amt), pen_name=pen))
        for mi in range(24):
            M = month_start(23 - mi); grow = 1 + 0.03 * mi
            add(M, 'Newsletter service', 'Newsletter service provider', 55 + 1.6 * mi + r.uniform(-3, 3))
            add(M + day(8), 'Website and store', 'Website host', 39.0)
            add(M + day(9), 'Software and tools', 'Writing and design tools', 62 + r.randint(0, 24))
            add(M + day(11), 'Accounting and fees', 'Bank', 14.0 + r.randint(0, 6))
            for w in range(4):
                add(M + day(7 * w), 'Virtual assistant', ASSISTANT, VA_RATE * r.uniform(4.0, 7.0) * (1.0 + 0.01 * mi))
            if M.month in (1, 4, 7, 10): add(M + day(14), 'Accounting and fees', 'Renata Bauer', 120 + 20 * (M.month == 1))
            if M.month == 3: add(M + day(12), 'Website and store', 'Website host', 180.0)
            if M.month == 1: add(M + day(9), 'Business insurance', 'Insurer', 210.0)
            if M.month in (2, 8): add(M + day(16), 'Education', 'Course provider', float(r.choice([60, 95, 140, 240])))
            if r.random() < 0.45: add(M + day(r.randint(5, 25)), 'Review copies', 'Gift and postage supplier', r.uniform(25, 85), r.choice(PEN_NAMES))
            if r.random() < 0.3: add(M + day(r.randint(5, 25)), 'Office and equipment', 'Office supplier', r.uniform(30, 260))
            if r.random() < 0.25: add(M + day(r.randint(5, 25)), 'Website and store', 'Mikael Dahl', 60 * r.randint(2, 5))
            if r.random() < 0.2: add(M + day(r.randint(5, 25)), 'Other', 'Various', r.uniform(15, 90))
        out.sort(key=lambda x: (x['date'], x['category']))
        return out
    rows = _raw('expenses', build)
    return _thin([dict(expense_id='EX-%04d' % i, date=iso(x['date']), month=iso(_ms(x['date'])), category=x['category'], vendor=x['vendor'], amount=x['amount'], pen_name=x['pen_name'])
                  for i, x in enumerate(rows, 1)], n)


# ------------------------------------------------------------------ profit and loss, cash, tax set-aside, owner draw
def _by_month(rows, dk, vk):
    o = {}
    for x in rows:
        d = to_date(x[dk]); o[_ms(d)] = o.get(_ms(d), 0.0) + x[vk]
    return o


def _money():
    def build():
        led = _sw()[0]
        roy, dire = {}, {}
        for x in led:
            if x['store'] == 'Direct store': dire[x['month']] = dire.get(x['month'], 0.0) + x['royalty'] * x['rate']
            else: roy[x['month']] = roy.get(x['month'], 0.0) + x['royalty'] * x['rate']
        pr = {}
        for x in _sw()[1]: pr[x['month']] = pr.get(x['month'], 0.0) + x['income']
        ads = {}
        for x in _ads()[1]: ads[_ms(x['date'])] = ads.get(_ms(x['date']), 0.0) + x['spend']
        prod = {}
        for p in _jobs()[1]:
            if p['status'] == 'Paid' and p['date'] <= TODAY: prod[_ms(p['date'])] = prod.get(_ms(p['date']), 0.0) + p['amount']
        exp = _by_month(expense_rows(), 'date', 'amount')
        ev, lines = _events(); evrev, evcost, evcogs = {}, {}, {}
        eds = {e['edition_id']: e for e in _eds()}
        for l in lines:
            m = _ms(l['date']); evrev[m] = evrev.get(m, 0.0) + l['copies'] * l['price']; evcogs[m] = evcogs.get(m, 0.0) + l['copies'] * (eds[l['edition_id']]['unit_cost'] + 0.65)
        for e in ev: m = _ms(e['date']); evcost[m] = evcost.get(m, 0.0) + e['table_fee'] + e['travel_cost'] + e['lodging_cost']
        rights = {}
        for d in _deals():
            for x in d['instalments']:
                if x['received_on']: m = _ms(x['received_on']); rights[m] = rights.get(m, 0.0) + x['amount'] * (1 - d['agent_pct'])
        pnl = []
        for M in months24():
            rev = roy.get(M, 0) + pr.get(M, 0) + dire.get(M, 0) + evrev.get(M, 0) + rights.get(M, 0)
            cost = ads.get(M, 0) + prod.get(M, 0) + exp.get(M, 0) + evcost.get(M, 0) + evcogs.get(M, 0)
            pnl.append(dict(month=M, royalties=R2(roy.get(M, 0)), page_reads=R2(pr.get(M, 0)), direct_net=R2(dire.get(M, 0)), event_sales=R2(evrev.get(M, 0)), rights=R2(rights.get(M, 0)), revenue=R2(rev),
                            ads=R2(ads.get(M, 0)), production=R2(prod.get(M, 0)), expenses=R2(exp.get(M, 0)), event_costs=R2(evcost.get(M, 0) + evcogs.get(M, 0)), costs=R2(cost), profit=R2(rev - cost)))
        # cash
        rec = {}
        for x in _stmts():
            if x['paid_on']: m = _ms(x['paid_on']); rec[m] = rec.get(m, 0.0) + x['received']
        stock = {}
        for x in _stock():
            if x['move'] == 'Order in': m = _ms(x['date']); stock[m] = stock.get(m, 0.0) + x['copies'] * x['unit_cost']
        cash = []; prev = 26000.0; r = rng('cash'); path = {}
        for i, M in enumerate(months24()):
            P = pnl[i]; prev_profit = pnl[i - 1]['profit'] if i else 0.0
            tax = R2(TAX_SET_ASIDE_PCT * max(0.0, prev_profit))
            receipts = R2(rec.get(M, 0) + evrev.get(M, 0) + rights.get(M, 0))
            out = R2(ads.get(M, 0) + prod.get(M, 0) + exp.get(M, 0) + evcost.get(M, 0) + stock.get(M, 0) + tax)
            before = prev + receipts - out
            target = 8900.0 if M == CUR else r.choice([10500, 11800, 12600, 13400, 14200, 15600, 16800])
            draw = R2(min(14000.0 if M == CUR else 6500.0, max(1800.0, before - target)))
            cash.append(dict(month=M, opening=R2(prev), receipts=receipts, ads=R2(ads.get(M, 0)), production=R2(prod.get(M, 0)), expenses=R2(exp.get(M, 0)), event_costs=R2(evcost.get(M, 0)),
                             author_copies=R2(stock.get(M, 0)), tax_set_aside=tax, owner_draw=draw, closing=R2(before - draw)))
            prev = before - draw
        return pnl, cash
    return _raw('money', build)


def pnl_rows(n=None): return _thin([dict(row_id='PL-%02d' % i, **dict(x, month=iso(x['month']))) for i, x in enumerate(_money()[0], 1)], n)
def cash_rows(n=None): return _thin([dict(cash_id='CS-%02d' % i, **dict(x, month=iso(x['month']))) for i, x in enumerate(_money()[1], 1)], n)
def draw_rows(n=None):
    return _thin([dict(draw_id='OD-%02d' % i, month=iso(x['month']), date=iso(min(TODAY, _eom(x['month']) - day(2))), amount=x['owner_draw']) for i, x in enumerate(_money()[1], 1)], n)


def tax_rows(n=None):
    pnl = _money()[0]; pot = 0.0; out = []
    for i, x in enumerate(pnl):
        aside = R2(TAX_SET_ASIDE_PCT * max(0.0, pnl[i - 1]['profit'] if i else 0.0)); pot += aside
        paid = 0.0
        if x['month'].month in (1, 4, 7, 10) and x['month'] < CUR: paid = R2(pot * 0.8); pot -= paid
        out.append(dict(tax_id='TX-%02d' % (i + 1), month=iso(x['month']), profit_month=x['profit'], set_aside_pct=TAX_SET_ASIDE_PCT, set_aside=aside, tax_paid=paid, pot_balance=R2(pot)))
    return _thin(out, n)


def author_statement_rows(n=None):
    """small-press view: each pen name read as an author (share to the author, advance recouped, costs charged back)"""
    led = _sw()[0]; out = []; adv = {PEN_NAMES[0]: 0.0, PEN_NAMES[1]: 2500.0}; k = 0
    for M in months24():
        for pn, sh in ((p['pen_name'], p['author_share']) for p in pen_names):
            earned = R2(sum(x['royalty'] * x['rate'] for x in led if x['month'] == M and x['title_id'] in {t['title_id'] for t in _titles() if t['pen_name'] == pn}))
            gross = R2(earned * sh); rec = R2(min(adv[pn], gross)); adv[pn] = R2(adv[pn] - rec)
            charged = R2(earned * 0.02)
            k += 1
            out.append(dict(statement_id='AS-%03d' % k, month=iso(M), pen_name=pn, royalties_earned=earned, author_share=sh, advance_recouped=rec, advance_left=adv[pn], costs_charged_back=charged,
                            payable=R2(gross - rec - charged)))
    return _thin(out, n)


def readthrough_rows(n=None):
    """read-through per series step over the last 12 months of the ledger (all formats, copies of book n+1 divided by copies of book n)"""
    cut = month_start(12); u = {}
    for x in _sw()[0]:
        if x['month'] >= cut: u[x['title_id']] = u.get(x['title_id'], 0) + x['units']
    out = []; k = 0
    for s in SERIES[:4]:
        ts = sorted([t for t in _titles() if t['series'] == s and t['release_date'] <= TODAY], key=lambda t: t['series_order'])
        for a, b in zip(ts, ts[1:]):
            k += 1; ua, ub = u.get(a['title_id'], 0), u.get(b['title_id'], 0)
            out.append(dict(step_id='RT-%02d' % k, series=s, step=a['series_order'], from_title=a['title'], to_title=b['title'], units_from=ua, units_to=ub, readthrough=round(ub / float(max(1, ua)), 3)))
    return _thin(out, n)


# ------------------------------------------------------------------ story
def story():
    """ids of the story rows: cost_title (+ cost, earned, months, drag_format, drag_cost, drag_earned); ad_campaign (+ spend_60, royalties_60, return_60, campaign name);
    series (+ readthrough, target); statement (+ store, month, statement_amount, received, gap, expected_on); launch (+ title, release_date, days_to_release, late_task_ids, late_steps);
    invoice (+ cpay_id, contractor, job_id, amount, due_date, cash_now, cash_floor, cash_after)"""
    out = {}
    old = [t for t in _titles() if t['release_date'] <= TODAY - day(540)]
    beh = [t for t in old if title_cost(t['title_id']) > title_royalty(t['title_id'])]
    assert len(beh) == 1, [(t['title_id'], title_cost(t['title_id']), title_royalty(t['title_id'])) for t in beh]
    t = beh[0]; aud = [j for j in _jobs()[0] if j['title_id'] == t['title_id'] and j['kind'] == 'Narration'][0]
    ae = sum(x['royalty'] * x['rate'] for x in _sw()[0] if x['title_id'] == t['title_id'] and x['format'] == 'Audiobook')
    out['cost_title'] = dict(title_id=t['title_id'], title=t['title'], cost=title_cost(t['title_id']), earned=title_royalty(t['title_id']), months=_age_m(t['release_date'], CUR), drag_format='Audiobook',
                             drag_cost=aud['quote'], drag_earned=R2(ae))
    cut = TODAY - day(60); camp = {}
    for x in _ads()[1]:
        if x['date'] > cut:
            a = camp.setdefault(x['campaign_id'], [0.0, 0.0]); a[0] += x['spend']; a[1] += x['royalties']
    bad = [(c, v) for c, v in camp.items() if v[1] < v[0] * AD_RETURN_TARGET and v[0] >= 100]
    assert len(bad) == 1, bad
    cid, v = bad[0]; nm = next(c['campaign'] for c in _ads()[0] if c['campaign_id'] == cid)
    out['ad_campaign'] = dict(campaign_id=cid, campaign=nm, spend_60=R2(v[0]), royalties_60=R2(v[1]), return_60=round(v[1] / v[0], 2))
    rt = [x for x in readthrough_rows() if x['step'] == 1]; low = [x for x in rt if x['readthrough'] < READTHROUGH_WARN_1]
    assert len(low) == 1, rt
    out['series'] = dict(series=low[0]['series'], readthrough=low[0]['readthrough'], target=READTHROUGH_WARN_1, from_title=low[0]['from_title'], to_title=low[0]['to_title'])
    sr = [x for x in statement_rows() if x['status'] == 'Short-paid']; assert len(sr) == 1
    x = sr[0]; out['statement'] = dict(statement_id=x['statement_id'], store=x['store'], month=x['month'], statement_amount=x['statement_amount'], received=x['received'], gap=R2(x['statement_amount'] - x['received']),
                                       expected_on=x['expected_on'])
    lt = [y for y in launch_task_rows() if y['title_id'] == 'TL-015' and y['status'] == 'Open' and to_date(y['due_date']) < TODAY]
    t15 = _TT()['TL-015']
    out['launch'] = dict(title_id='TL-015', title=t15['title'], release_date=iso(t15['release_date']), days_to_release=(t15['release_date'] - TODAY).days, late_task_ids=[y['task_id'] for y in lt],
                         late_steps=[y['step'] for y in lt])
    cp = [p for p in jobpay_rows() if p['status'] == 'Due' and TODAY <= to_date(p['date']) <= TODAY + day(7) and p['amount'] > 3000]; assert len(cp) == 1, cp
    p = cp[0]; cash_now = _money()[1][-1]['closing']
    out['invoice'] = dict(cpay_id=p['cpay_id'], contractor=p['contractor'], job_id=p['job_id'], amount=p['amount'], due_date=p['date'], cash_now=cash_now, cash_floor=CASH_FLOOR, cash_after=R2(cash_now - p['amount']))
    return out


_GENS = ['title_rows', 'edition_rows', 'sales_rows', 'pageread_rows', 'direct_order_rows', 'statement_rows', 'payment_rows', 'campaign_rows', 'ad_day_rows', 'promo_rows', 'job_rows', 'jobpay_rows',
         'newsletter_rows', 'subscriber_rows', 'swap_rows', 'reviewer_rows', 'arc_rows', 'launch_task_rows', 'event_rows', 'event_sale_rows', 'stock_rows', 'deal_rows', 'instalment_rows',
         'expense_rows', 'pnl_rows', 'cash_rows', 'tax_rows', 'draw_rows', 'readthrough_rows', 'author_statement_rows', 'series_rows']


def _digest():
    h = hashlib.md5()
    for nm in _GENS: h.update(repr(globals()[nm]()).encode())
    return h.hexdigest()[:12]


if __name__ == '__main__':
    import time
    t0 = time.time(); G = {nm: globals()[nm]() for nm in _GENS}; S = story()
    print('team', len(team), 'currencies', len(currencies), 'countries', len(countries), 'stores', len(stores), 'formats', len(formats))
    print(' '.join('%s %d' % (nm.replace('_rows', ''), len(v)) for nm, v in G.items()))
    ids = {'title_rows': 'title_id', 'edition_rows': 'edition_id', 'sales_rows': 'sale_id', 'pageread_rows': 'read_id', 'direct_order_rows': 'order_id', 'statement_rows': 'statement_id',
           'payment_rows': 'payment_id', 'campaign_rows': 'campaign_id', 'ad_day_rows': 'ad_id', 'promo_rows': 'promo_id', 'job_rows': 'job_id', 'jobpay_rows': 'cpay_id', 'newsletter_rows': 'send_id',
           'subscriber_rows': 'row_id', 'swap_rows': 'swap_id', 'reviewer_rows': 'reviewer_id', 'arc_rows': 'arc_id', 'launch_task_rows': 'task_id', 'event_rows': 'event_id', 'event_sale_rows': 'line_id',
           'stock_rows': 'stock_id', 'deal_rows': 'deal_id', 'instalment_rows': 'instalment_id', 'expense_rows': 'expense_id', 'pnl_rows': 'row_id', 'cash_rows': 'cash_id', 'tax_rows': 'tax_id',
           'draw_rows': 'draw_id', 'author_statement_rows': 'statement_id', 'series_rows': 'series_id', 'team': 'person_id'}
    G['team'] = team
    for nm, k in ids.items(): assert len({x[k] for x in G[nm]}) == len(G[nm]), nm
    assert len({t['title'] for t in G['title_rows']}) == 22 and len(G['title_rows']) == 22
    chk = [('title_rows', 'pen_name', PEN_NAMES), ('title_rows', 'series', SERIES), ('title_rows', 'genre', GENRES), ('title_rows', 'status', TITLE_STATUS), ('edition_rows', 'format', FORMATS),
           ('edition_rows', 'status', EDITION_STATUS), ('sales_rows', 'store', STORES), ('sales_rows', 'country', COUNTRIES), ('sales_rows', 'currency', CURRENCIES), ('sales_rows', 'format', FORMATS),
           ('campaign_rows', 'platform', AD_PLATFORMS), ('campaign_rows', 'status', AD_STATUS), ('job_rows', 'kind', JOB_KINDS), ('job_rows', 'status', JOB_STATUS), ('jobpay_rows', 'stage', PAY_STAGES),
           ('jobpay_rows', 'status', CPAY_STATUS), ('statement_rows', 'status', STATEMENT_STATUS), ('expense_rows', 'category', EXPENSE_CATEGORIES), ('event_rows', 'kind', EVENT_KINDS),
           ('stock_rows', 'move', STOCK_MOVES), ('deal_rows', 'kind', DEAL_KINDS), ('deal_rows', 'status', DEAL_STATUS), ('launch_task_rows', 'step', LAUNCH_STEP_NAMES), ('launch_task_rows', 'status', TASK_STATUS),
           ('arc_rows', 'status', ARC_STATUS), ('reviewer_rows', 'kind', REVIEWER_KINDS), ('subscriber_rows', 'source', SUB_SOURCES), ('newsletter_rows', 'kind', SEND_KINDS), ('promo_rows', 'kind', PROMO_KINDS),
           ('promo_rows', 'status', PROMO_STATUS), ('team', 'role', ROLES), ('team', 'team', TEAMS), ('team', 'pay_type', PAY_TYPES), ('direct_order_rows', 'country', COUNTRIES)]
    for nm, col, vals in chk:
        got = {x[col] for x in G[nm]}; miss = [v for v in vals if v not in got]
        assert not miss, (nm, col, miss)
        extra = {g for g in got if g not in vals and g != ''}; assert not extra, (nm, col, extra)
    for L in (ROLES, TEAMS, PAY_TYPES, PEN_NAMES, SERIES, GENRES, TITLE_STATUS, FORMATS, EDITION_STATUS, STORES, COUNTRIES, CURRENCIES, AD_PLATFORMS, AD_STATUS, JOB_KINDS, JOB_STATUS, PAY_STAGES,
              CPAY_STATUS, STATEMENT_STATUS, EXPENSE_CATEGORIES, EVENT_KINDS, STOCK_MOVES, DEAL_KINDS, DEAL_STATUS, LAUNCH_STEP_NAMES, TASK_STATUS, ARC_STATUS, REVIEWER_KINDS, SUB_SOURCES, SEND_KINDS,
              PROMO_KINDS, PROMO_STATUS):
        for k, _ in pairs(L): assert len(k) <= 21, k
    ms = iso(month_start(0)); t30 = ago(30); td = iso(TODAY)
    def cur(nm, col, lo=1, t=ms):
        n_ = sum(1 for x in G[nm] if x[col] and t <= x[col] <= td); assert n_ >= (lo if TODAY.day >= 8 else 0), (nm, col, n_); return n_
    print('this month:', 'sales', cur('sales_rows', 'month', 20), 'orders', cur('direct_order_rows', 'date', 20), 'ads', cur('ad_day_rows', 'date', 3), 'expenses', cur('expense_rows', 'date', 2),
          'jobpay', cur('jobpay_rows', 'date', 1), 'sends', cur('newsletter_rows', 'date', 1), 'events', cur('event_rows', 'date', 1))
    print('last 30 days:', 'orders', cur('direct_order_rows', 'date', 30, t30), 'ads', cur('ad_day_rows', 'date', 30, t30), 'expenses', cur('expense_rows', 'date', 5, t30), 'jobpay', cur('jobpay_rows', 'date', 2, t30),
          'sends', cur('newsletter_rows', 'date', 3, t30), 'events', cur('event_rows', 'date', 1, t30), 'payments', cur('payment_rows', 'received_on', 3, t30))
    ps = G['pnl_rows']; print('monthly revenue', [round(x['revenue']) for x in ps]); print('monthly profit', [round(x['profit']) for x in ps])
    cr = G['cash_rows']; print('cash closing', [round(x['closing']) for x in cr]); assert min(x['closing'] for x in cr) > CASH_FLOOR, 'cash floor'
    print('draws', [round(x['owner_draw']) for x in cr])
    tot = {s: sum(x['royalty'] * x['rate'] for x in _sw()[0] if x['store'] == s) for s in STORES}; allr = sum(tot.values()); print('royalties by store share', {s: round(v / allr, 3) for s, v in tot.items()})
    fmt = {f: sum(x['royalty'] * x['rate'] for x in _sw()[0] if x['format'] == f) for f in FORMATS}; print('royalties by format', {f: round(v) for f, v in fmt.items()})
    print('ads: spend', round(sum(x['spend'] for x in _ads()[1])), 'royalties', round(sum(x['royalties'] for x in _ads()[1])))
    for t in _titles(): print(t['title_id'], t['title'][:30].ljust(30), str(t['release_date']), 'cost', round(title_cost(t['title_id'])), 'earned', round(title_royalty(t['title_id'])), 'before', _before(t))
    print('readthrough', [(x['series'][:8], x['step'], x['readthrough']) for x in G['readthrough_rows']])
    print('direct share of royalties', round(tot['Direct store'] / allr, 3))
    print('story', S)
    d1 = _digest(); _CACHE.clear()
    for nm in reversed(_GENS): globals()[nm]()
    d2 = _digest(); assert d1 == d2, (d1, d2)
    print('digest', d1, 'secs', round(time.time() - t0, 1))
