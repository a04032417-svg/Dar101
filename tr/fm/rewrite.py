"""English pre-edit for the Farm suite: ambiguous words become unambiguous ones before machine translation
(the translator sees no context). Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched.
The language comes from translate.py's command line (argv[2])."""
import re, sys
PH = re.compile(r'\{[a-z_0-9]+(?::[a-z0-9_.]+)?\}')
LANG = sys.argv[2] if len(sys.argv) > 2 else ''
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')

EXACT = {
    'Head': 'Number of animals', 'Block': 'Field block', 'Cover': 'Insurance cover', 'Fine': 'In good order', 'Draft': 'Draft application', 'Short': 'Underpaid',
    'Fair': 'Fair condition', 'Clear': 'Cleared for sale', 'Running': 'Trial running', 'Drop': 'Drop the variety', 'Adopt': 'Adopt the variety', 'Fixed': 'Problem fixed',
    'Stones': 'Stones in the soil', 'Lime': 'Agricultural lime', 'Drip': 'Drip irrigation', 'Plot': 'Trial plot', 'Sire': 'Male parent', 'Dam': 'Female parent',
    'Fat': 'Milk fat', 'Gain': 'Yield gain', 'Principal': 'Loan principal', 'Interest': 'Interest charge', 'Class': 'Asset class', 'Part': 'Spare part', 'Store': 'Storage location',
    'Lots': 'Batches', 'Lot': 'Batch', 'Kind': 'Type', 'Fill': 'Fill level', 'Casual': 'Casual worker', 'Stretch target': 'Ambitious target', 'Services': 'Machine services',
    'Hire': 'Equipment rental', 'Service': 'Service', 'Combine': 'Combine harvester', 'Drill': 'Seed drill', 'Dip': 'Sheep dip', 'Pivot': 'Centre pivot irrigator',
}
RULES = [
    (r'\blots\b', 'batches'), (r'\bLots\b', 'Batches'), (r'\blot\b', 'batch'), (r'\bLot\b', 'Batch'),
    (r'\bcombine\b(?! harvester)', 'combine harvester'), (r'\bCombine\b(?! harvester)', 'Combine harvester'),
    (r'\bdrill\b(?<!seed drill)', 'seed drill'), (r'\bseed seed drill\b', 'seed drill'),
    (r'\bpivot\b', 'centre pivot irrigator'), (r'\blayers\b', 'laying hens'), (r'\blayer\b', 'laying hen'),
    (r'\bsire\b', 'male parent'), (r'\bSire\b', 'Male parent'), (r'\bdam\b', 'female parent'), (r'\bDam\b', 'Female parent'),
    (r'\bhead\b of', 'head of'), (r'\bheads\b', 'animals'),
    (r'\bPPE\b', 'protective equipment'),
]
if NONLATIN:
    RULES += [(r'\bKPIs\b', 'performance indicators'), (r'\bKPI\b', 'performance indicator'), (r'\bROI\b', 'return on investment'),
              (r'\bGDD\b', 'growing degree days'), (r'\bPHI\b', 'pre-harvest interval'), (r'\bFCR\b', 'feed conversion ratio'), (r'\bDSCR\b', 'debt service coverage ratio'),
              (r'\bEID\b', 'electronic ID'), (r'\bMRL\b', 'maximum residue limit')]
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
