"""English pre-edit for the Short-Term Rental Host suite: ambiguous words become unambiguous ones before machine translation
(the translator sees no context). Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched.
The language comes from translate.py's command line (argv[2])."""
import re, sys
PH = re.compile(r'\{[a-z_0-9]+(?::[a-z0-9_.]+)?\}')
LANG = sys.argv[2] if len(sys.argv) > 2 else ''
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')

EXACT = {
    'Unit': 'Rental unit', 'Units': 'Rental units', 'Listing': 'Rental listing', 'Listings': 'Rental listings', 'Stay': 'Guest stay', 'Stays': 'Guest stays',
    'Booking': 'Guest booking', 'Bookings': 'Guest bookings', 'Channel': 'Booking channel', 'Channels': 'Booking channels', 'Payout': 'Platform payout', 'Payouts': 'Platform payouts',
    'Turnover': 'Cleaning turnover', 'Turnovers': 'Cleaning turnovers', 'Turn': 'Cleaning turnover', 'Linen': 'Bed linen', 'Supplies': 'Guest supplies', 'Host': 'Rental host',
    'Co-host': 'Co-host manager', 'ADR': 'Average daily rate', 'RevPAR': 'Revenue per available night', 'Occupancy': 'Occupancy rate', 'Nights': 'Booked nights', 'Night': 'Booked night',
    'Check-in': 'Guest check-in', 'Check-out': 'Guest check-out', 'Damage': 'Property damage', 'Owner': 'Property owner', 'Owners': 'Property owners',
    'Open': 'Still open', 'Closed': 'Closed item', 'Clear': 'All clear', 'Draft': 'Draft version', 'Kind': 'Type', 'Band': 'Range band', 'Tier': 'Level', 'Lift': 'Price increase',
}
RULES = [(r'\bADR\b', 'average daily rate'), (r'\bRevPAR\b', 'revenue per available night')]
if NONLATIN:
    RULES += [(r'\bKPIs\b', 'performance indicators'), (r'\bKPI\b', 'performance indicator'), (r'\bROI\b', 'return on investment'), (r'\bETA\b', 'expected arrival')]
CRULES = [(re.compile(a), b) for a, b in RULES]
SMALL = {'and', 'of', 'to', 'a', 'an', 'the', 'in', 'for', 'vs', 'or', 'per', 'by', 'on', 'with', 'from', 'at'}


def sentence_case(t, force=False):
    w = t.split(' ')
    if len(w) < 2: return t
    rest = [x for x in w[1:] if x.lower() not in SMALL and x[:1].isalpha()]
    if not rest or not (force or all(x[:1].isupper() for x in rest)): return t
    return ' '.join([w[0]] + [x if (x.lower() in SMALL or x[1:] != x[1:].lower() or x in ('I', 'WhatsApp')) else x.lower() for x in w[1:]])


def rewrite(en, kind='sentence', trainer=True):
    if en in EXACT: r = EXACT[en]
    else:
        parts = PH.split(en); phs = PH.findall(en)
        out = []
        for p in parts:
            for rx, rp in CRULES: p = rx.sub(rp, p)
            out.append(p)
        r = ''.join(x + (phs[i] if i < len(phs) else '') for i, x in enumerate(out))
    if kind in ('sheet', 'label', 'title', 'list', 'setting'): r = sentence_case(r, force=(kind == 'sheet'))
    return r
