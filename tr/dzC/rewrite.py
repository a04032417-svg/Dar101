"""English pre-edit for the Interior Designer suite: ambiguous words become unambiguous ones before machine translation
(the translator sees no context). Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched.
The language comes from translate.py's command line (argv[2])."""
import re, sys
PH = re.compile(r'\{[a-z_0-9]+(?::[a-z0-9_.]+)?\}')
LANG = sys.argv[2] if len(sys.argv) > 2 else ''
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')

EXACT = {
    'Spec': 'Product specification', 'Specs': 'Product specifications', 'FF&E': 'Furniture, fixtures and equipment', 'Schedule': 'Item schedule',
    'Trade price': 'Trade discount price', 'Trade': 'Trade account', 'Mark-up': 'Markup on cost', 'Markup': 'Markup on cost', 'Retainer': 'Retainer deposit',
    'Deposit': 'Deposit payment', 'Balance': 'Balance due', 'Lead time': 'Delivery lead time', 'Back-order': 'Back-ordered item', 'Back-ordered': 'Back-ordered item',
    'Install': 'Installation', 'Punch list': 'Snag list', 'Punch List': 'Snag list', 'Swatch': 'Fabric swatch', 'Swatches': 'Fabric swatches',
    'Sample': 'Material sample', 'Samples': 'Material samples', 'Finish': 'Surface finish', 'Finishes': 'Surface finishes', 'Fixture': 'Light fixture',
    'Fixtures': 'Fixtures', 'Scope': 'Project scope', 'Phase': 'Project phase', 'Phases': 'Project phases', 'Concept': 'Design concept', 'Brief': 'Design brief',
    'Moodboard': 'Mood board', 'Rendering': 'Design rendering', 'Open': 'Still open', 'Closed': 'Closed item', 'Clear': 'All clear', 'Draft': 'Draft version',
    'Kind': 'Type', 'Band': 'Range band', 'Tier': 'Level', 'Room': 'Room', 'Approval': 'Client approval', 'Approvals': 'Client approvals',
}
RULES = [(r'\bFF&E\b', 'furniture, fixtures and equipment'), (r'\bpunch list\b', 'snag list')]
if NONLATIN:
    RULES += [(r'\bKPIs\b', 'performance indicators'), (r'\bKPI\b', 'performance indicator'), (r'\bROI\b', 'return on investment'),
              (r'\bPOs\b', 'purchase orders'), (r'\bPO\b', 'purchase order'), (r'\bETA\b', 'expected arrival'), (r'\bSKU\b', 'item code')]
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
