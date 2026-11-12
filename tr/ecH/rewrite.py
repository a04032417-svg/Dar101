"""English pre-edit for the Project Manager suite: ambiguous words become unambiguous ones before machine translation
(the translator sees no context). Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched.
The language comes from translate.py's command line (argv[2])."""
import re, sys
PH = re.compile(r'\{[a-z_0-9]+(?::[a-z0-9_.]+)?\}')
LANG = sys.argv[2] if len(sys.argv) > 2 else ''
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')

EXACT = {
    'Return': 'Product return', 'Returns': 'Product returns', 'Stock': 'Stock on hand', 'Lead': 'Lead time', 'Lead days': 'Lead time in days',
    'Listing': 'Product listing', 'Listings': 'Product listings', 'Payout': 'Marketplace payout', 'Payouts': 'Marketplace payouts', 'Fees': 'Selling fees',
    'Fee': 'Selling fee', 'Channel': 'Sales channel', 'Channels': 'Sales channels', 'Carrier': 'Shipping carrier', 'Carriers': 'Shipping carriers',
    'Ticket': 'Support ticket', 'Tickets': 'Support tickets', 'Bundle': 'Product bundle', 'Bundles': 'Product bundles', 'Promo': 'Promotion', 'Promos': 'Promotions',
    'Code': 'Discount code', 'Codes': 'Discount codes', 'Cover': 'Stock cover', 'Count': 'Stock count', 'Shrink': 'Stock loss', 'Pick': 'Order picking',
    'Pack': 'Order packing', 'Dispatch': 'Order dispatch', 'Draft': 'Draft version', 'Open': 'Still open', 'Closed': 'Closed item', 'Fine': 'In good order',
    'Clear': 'All clear', 'Short': 'Short payment', 'Kind': 'Type', 'Band': 'Range band', 'Tier': 'Level', 'Claim': 'Damage claim', 'Claims': 'Damage claims',
    'Launch': 'Product launch', 'Drop': 'Price drop', 'Lot': 'Batch lot', 'Landed': 'Landed cost',
}
RULES = [(r'\bpayouts\b', 'marketplace payouts'), (r'\breturns rate\b', 'product return rate'), (r'\bReturns rate\b', 'Product return rate')]
if NONLATIN:
    RULES += [(r'\bKPIs\b', 'performance indicators'), (r'\bKPI\b', 'performance indicator'), (r'\bROI\b', 'return on investment'),
              (r'\bROAS\b', 'return on ad spend'), (r'\bAOV\b', 'average order value'), (r'\bCOGS\b', 'cost of goods sold'), (r'\bCPC\b', 'cost per click'),
              (r'\bCTR\b', 'click-through rate'), (r'\bMOQ\b', 'minimum order quantity'), (r'\bPO\b', 'purchase order'), (r'\bPOs\b', 'purchase orders'),
              (r'\bRMA\b', 'return authorisation'), (r'\bLTV\b', 'customer lifetime value')]
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
