"""English pre-edit for the Cleaning Business suite: ambiguous words become unambiguous ones before machine translation
(the translator sees no context). Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched.
The language comes from translate.py's command line (argv[2])."""
import re, sys
PH = re.compile(r'\{[a-z_0-9]+(?::[a-z0-9_.]+)?\}')
LANG = sys.argv[2] if len(sys.argv) > 2 else ''
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')

EXACT = {
    'Job': 'Cleaning job', 'Jobs': 'Cleaning jobs', 'Visit': 'Cleaning visit', 'Visits': 'Cleaning visits', 'Crew': 'Cleaning crew', 'Crews': 'Cleaning crews', 'Route': 'Driving route', 'Routes': 'Driving routes',
    'Re-clean': 'Repeat cleaning visit', 'Re-cleans': 'Repeat cleaning visits', 'Inspection': 'Quality inspection', 'Inspections': 'Quality inspections', 'Add-on': 'Extra service', 'Add-ons': 'Extra services',
    'Deep clean': 'Deep cleaning', 'Move-out': 'Move-out cleaning', 'Supplies': 'Cleaning supplies', 'Stock': 'Supplies stock', 'Lead': 'Team leader', 'Team lead': 'Team leader', 'Frequency': 'Visit frequency',
    'Rate card': 'Price list', 'Contract': 'Service contract', 'Contracts': 'Service contracts', 'Complaint': 'Customer complaint', 'Complaints': 'Customer complaints',
    'Open': 'Still open', 'Closed': 'Closed item', 'Clear': 'All clear', 'Draft': 'Draft version', 'Kind': 'Type', 'Band': 'Range band', 'Lift': 'Price increase', 'Tier': 'Level',
}
RULES = [(r'\bre-clean', 'repeat cleaning visit'), (r'\brate card', 'price list')]
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
