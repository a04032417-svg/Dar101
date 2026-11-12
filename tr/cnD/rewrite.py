"""English pre-edit for the Construction Company suite: ambiguous words become unambiguous ones before machine translation
(the translator sees no context). Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched.
The language comes from translate.py's command line (argv[2])."""
import re, sys
PH = re.compile(r'\{[a-z_0-9]+(?::[a-z0-9_.]+)?\}')
LANG = sys.argv[2] if len(sys.argv) > 2 else ''
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')

EXACT = {
    'Retention': 'Retention money', 'Retention held': 'Retention money held', 'Claims': 'Progress payment claims', 'Claim': 'Progress payment claim',
    'Plant': 'Construction equipment', 'Site': 'Construction site', 'Sites': 'Construction sites', 'Snags': 'Defects to fix', 'Snag': 'Defect to fix',
    'Crew': 'Work crew', 'Crews': 'Work crews', 'Hire': 'Equipment rental', 'Stock': 'Stock of materials', 'Held': 'Withheld', 'Released': 'Paid back',
    'Bid': 'Tender offer', 'Bids': 'Tender offers', 'Float': 'Schedule float', 'Order book': 'Secured work remaining', 'Daywork': 'Dayworks (time and materials)',
    'Lead': 'Prospect', 'Leads': 'Prospects', 'Trade': 'Construction trade', 'Trades': 'Construction trades', 'Package': 'Work package', 'Packages': 'Work packages',
    'Near miss': 'Near-miss incident', 'Near misses': 'Near-miss incidents', 'Level': 'Level', 'Bond': 'Bank guarantee', 'Bonds': 'Bank guarantees',
}
RULES = [
    (r'\bprogress claims\b', 'progress payment claims'), (r'\bProgress claims\b', 'Progress payment claims'),
    (r'\bprogress claim\b', 'progress payment claim'), (r'\bProgress claim\b', 'Progress payment claim'),
    (r'(?<!payment )\bclaims\b', 'payment claims'), (r'(?<!payment )\bClaims\b', 'Payment claims'),
    (r'(?<!payment )(?<!time )\bclaim\b', 'payment claim'), (r'(?<!payment )\bClaim\b', 'Payment claim'),
    (r'(?<!money )\bretention\b(?! money)', 'retention money'), (r'\bRetention\b(?! money)', 'Retention money'),
    (r'\bsnag lists?\b', 'list of defects to fix'), (r'\bSnag lists?\b', 'List of defects to fix'), (r'\bsnags\b', 'defects to fix'), (r'\bsnag\b', 'defect to fix'), (r'\bSnag\b', 'Defect'),
    (r'\bpunch list\b', 'list of defects to fix'),
    (r'\bplant\b', 'construction equipment'), (r'\bPlant\b', 'Construction equipment'),
    (r'(?<!construction )(?<!web)\bsite\b', 'construction site'), (r'(?<!construction )\bSite\b', 'Construction site'),
    (r'(?<!construction )\bsites\b', 'construction sites'), (r'\bSites\b', 'Construction sites'),
    (r'\bon hire\b', 'rented'), (r'\boff hire\b', 'returned'), (r'\bhire\b', 'rental'), (r'\bHire\b', 'Rental'), (r'\bhired\b', 'rented'), (r'\bHired\b', 'Rented'),
    (r'\bcrews\b', 'work crews'), (r'\bCrews\b', 'Work crews'), (r'(?<!work )\bcrew\b', 'work crew'), (r'\bCrew\b', 'Work crew'),
    (r'\bgangs\b', 'work crews'), (r'\bgang\b', 'work crew'),
    (r'\bvariations\b', 'contract variations'), (r'\bVariations\b', 'Contract variations'), (r'(?<!contract )\bvariation\b', 'contract variation'), (r'\bVariation\b', 'Contract variation'),
    (r'\bdaywork sheets?\b', 'daywork records'), (r'\bdaywork\b', 'daywork'),
    (r'\bbackcharges\b', 'charges back to subcontractors'), (r'\bBackcharges\b', 'Charges back to subcontractors'), (r'\bbackcharge\b', 'charge back to a subcontractor'), (r'\bBackcharge\b', 'Charge back'),
    (r'\bprovisional sums\b', 'provisional amounts'), (r'\bProvisional sums\b', 'Provisional amounts'), (r'\bprovisional sum\b', 'provisional amount'),
    (r'\bliquidated damages\b', 'delay penalties'), (r'\bLiquidated damages\b', 'Delay penalties'),
    (r'\bpractical completion\b', 'substantial completion'), (r'\bPractical completion\b', 'Substantial completion'),
    (r'\bdefects period\b', 'defects liability period'), (r'\bDefects period\b', 'Defects liability period'),
    (r'\blook-ahead\b', 'short-term'), (r'\bLook-ahead\b', 'Short-term'),
    (r'\btoolbox talks?\b', 'safety briefing'), (r'\bToolbox talks?\b', 'Safety briefing'),
    (r'\bnear misses\b', 'near-miss incidents'), (r'\bnear miss\b', 'near-miss incident'), (r'\bNear misses\b', 'Near-miss incidents'), (r'\bNear miss\b', 'Near-miss incident'),
    (r'\border book\b', 'secured work remaining'), (r'\bOrder book\b', 'Secured work remaining'),
    (r'\bbonding capacity\b', 'guarantee capacity'), (r'\bbonds\b', 'bank guarantees'), (r'\bBonds\b', 'Bank guarantees'), (r'\bbond\b', 'bank guarantee'), (r'\bBond\b', 'Bank guarantee'),
    (r'\bbids\b', 'tender offers'), (r'\bBids\b', 'Tender offers'), (r'(?<!to )\bbid\b', 'tender offer'), (r'\bBid\b', 'Tender offer'),
    (r'\bleads\b', 'prospects'), (r'\bLeads\b', 'Prospects'), (r'\blead time\b', 'delivery time'), (r'\bLead time\b', 'Delivery time'), (r'\blead times\b', 'delivery times'), (r'\bLead times\b', 'Delivery times'),
    (r'\bstock\b', 'stock of materials'), (r'\bStock\b', 'Stock of materials'),
    (r'\bprogramme\b', 'schedule'), (r'\bProgramme\b', 'Schedule'),
    (r'\bfloat\b', 'schedule float'), (r'\bFloat\b', 'Schedule float'),
    (r'\bcube tests?\b', 'concrete compression test'), (r'\bCube tests?\b', 'Concrete compression test'), (r'\bcubes\b', 'concrete test samples'),
    (r'\bpours\b', 'concrete pours'), (r'\bpour\b', 'concrete pour'),
    (r'\bbill of quantities\b', 'bill of quantities'),
    (r'\bprelims\b', 'site overheads'), (r'\bpreliminaries\b', 'site overheads'), (r'\bPreliminaries\b', 'Site overheads'),
    (r'\bsubs\b', 'subcontractors'), (r'\bSubs\b', 'Subcontractors'),
    (r'(?<=money )held\b', 'withheld'), (r'(?<=money )released\b', 'paid back'),
    (r'\btrades\b', 'construction trades'), (r'\bTrades\b', 'Construction trades'),
    (r'\bsign-off\b', 'approval'), (r'\bSign-off\b', 'Approval'),
]
if NONLATIN:
    RULES += [(r'\bRFIs\b', 'requests for information'), (r'\bRFI\b', 'request for information'), (r'\bPPE\b', 'personal protective equipment'),
              (r'\bWIP\b', 'work in progress'), (r'\bEOT\b', 'extension of time'), (r'\bKPIs\b', 'performance indicators'), (r'\bKPI\b', 'performance indicator'),
              (r'\bCPI\b', 'cost performance index'), (r'\bSPI\b', 'schedule performance index'), (r'\bEAC\b', 'estimate at completion'), (r'\bROI\b', 'return on investment'),
              (r'\bDSO\b', 'days sales outstanding'), (r'\bVAT\b', 'VAT')]
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
