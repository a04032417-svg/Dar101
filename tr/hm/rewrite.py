"""English pre-edit for the Handmade Product Maker suite: ambiguous words become unambiguous ones before machine translation
(the translator sees no context). Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched.
The language comes from translate.py's command line (argv[2])."""
import re, sys
PH = re.compile(r'\{[a-z_0-9]+(?::[a-z0-9_.]+)?\}')
LANG = sys.argv[2] if len(sys.argv) > 2 else ''
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')

EXACT = {
    'Batch': 'Production batch', 'Batches': 'Production batches', 'Lot': 'Ingredient lot', 'Lots': 'Ingredient lots', 'Cure': 'Soap curing', 'Curing': 'Soap curing', 'Pour': 'Wax pour',
    'Wick': 'Candle wick', 'Wicks': 'Candle wicks', 'Scent': 'Fragrance', 'Scents': 'Fragrances', 'Throw': 'Scent throw', 'Melt': 'Wax melt', 'Melts': 'Wax melts', 'Lye': 'Lye (sodium hydroxide)',
    'Fair': 'Craft fair', 'Fairs': 'Craft fairs', 'Stockist': 'Retail stockist', 'Stockists': 'Retail stockists', 'Wholesale': 'Wholesale sales', 'Range': 'Product range', 'Label': 'Product label', 'Labels': 'Product labels',
    'Open': 'Still open', 'Closed': 'Closed item', 'Clear': 'All clear', 'Draft': 'Draft version', 'Kind': 'Type', 'Band': 'Range band', 'Tier': 'Level', 'Stock': 'Stock on hand',
}
RULES = [(r'\bscent throw\b', 'fragrance strength'), (r'\bcold throw\b', 'unlit fragrance strength'), (r'\bhot throw\b', 'burning fragrance strength'), (r'\bsuperfat\b', 'superfat percentage')]
if NONLATIN:
    RULES += [(r'\bKPIs\b', 'performance indicators'), (r'\bKPI\b', 'performance indicator'), (r'\bROI\b', 'return on investment')]
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
