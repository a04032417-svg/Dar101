"""English pre-edit for the Therapy Private Practice suite: ambiguous words become unambiguous ones before machine translation
(the translator sees no context). Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched.
The language comes from translate.py's command line (argv[2])."""
import re, sys
PH = re.compile(r'\{[a-z_0-9]+(?::[a-z0-9_.]+)?\}')
LANG = sys.argv[2] if len(sys.argv) > 2 else ''
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')

EXACT = {
    'Session': 'Therapy session', 'Sessions': 'Therapy sessions', 'Intake': 'New client intake', 'Intakes': 'New client intakes', 'Claim': 'Insurance claim', 'Claims': 'Insurance claims',
    'Payer': 'Insurance payer', 'Payers': 'Insurance payers', 'Caseload': 'Client caseload', 'Associate': 'Associate therapist', 'Associates': 'Associate therapists',
    'Supervision': 'Clinical supervision', 'Supervisor': 'Clinical supervisor', 'Discharge': 'Client discharge', 'Discharged': 'Client discharged', 'No-show': 'Missed session', 'No-shows': 'Missed sessions',
    'Late cancel': 'Late cancellation', 'Late cancels': 'Late cancellations', 'Sliding scale': 'Income-based reduced fee', 'Waitlist': 'Waiting list', 'Note': 'Session note', 'Notes': 'Session notes',
    'Plan review': 'Treatment plan review', 'Credits': 'Continuing education credits', 'Credit': 'Continuing education credit', 'Room': 'Therapy room', 'Rooms': 'Therapy rooms', 'Group': 'Therapy group',
    'Groups': 'Therapy groups', 'Referral': 'Client referral', 'Referrals': 'Client referrals', 'Referrer': 'Referral source', 'Renewal': 'Renewal date', 'Denied': 'Claim denied', 'Denial': 'Claim denial',
    'Write-off': 'Amount written off', 'Copay': 'Client co-payment', 'Statement': 'Client statement', 'Package': 'Prepaid package', 'Packages': 'Prepaid packages', 'Online': 'Online session',
    'Open': 'Still open', 'Closed': 'Closed item', 'Clear': 'All clear', 'Draft': 'Draft version', 'Kind': 'Type', 'Band': 'Range band', 'Tier': 'Level', 'Score': 'Questionnaire score',
}
RULES = [(r'\bno-show', 'missed session'), (r'\blate cancel\b', 'late cancellation'), (r'\bsliding scale\b', 'income-based reduced fee'), (r'\bcaseload\b', 'client caseload')]
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
