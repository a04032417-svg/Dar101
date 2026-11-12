"""English pre-edit for the Project Manager suite: ambiguous words become unambiguous ones before machine translation
(the translator sees no context). Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched.
The language comes from translate.py's command line (argv[2])."""
import re, sys
PH = re.compile(r'\{[a-z_0-9]+(?::[a-z0-9_.]+)?\}')
LANG = sys.argv[2] if len(sys.argv) > 2 else ''
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')

EXACT = {
    'Minutes': 'Meeting minutes', 'Minute': 'Meeting minute', 'Change': 'Project change', 'Changes': 'Project changes', 'Issue': 'Project issue', 'Issues': 'Project issues',
    'Float': 'Schedule float', 'Lag': 'Time lag', 'Lead': 'Team leader', 'Board': 'Task board', 'Card': 'Task card', 'Cards': 'Task cards', 'Story': 'User story',
    'Points': 'Story points', 'Draw': 'Budget draw', 'Build': 'Build phase', 'Chair': 'Meeting chair', 'Apologies': 'Apologies for absence', 'Gate': 'Stage gate',
    'Release': 'Software release', 'Champion': 'Change champion', 'Sponsor': 'Project sponsor', 'Booked': 'Reserved', 'Clash': 'Scheduling clash', 'Amber': 'Amber status',
    'Claim': 'Payment claim', 'Claims': 'Payment claims', 'Stand-up': 'Daily stand-up meeting', 'Retro': 'Retrospective', 'Spike': 'Research task', 'Velocity': 'Team velocity',
    'Bench': 'Unassigned staff', 'Charter': 'Project charter', 'Fixed': 'Problem fixed', 'Open': 'Still open', 'Closed': 'Closed item', 'Fair': 'Fair condition',
    'Clear': 'All clear', 'Fine': 'In good order', 'Draft': 'Draft version', 'Short': 'Too short', 'Kind': 'Type', 'Band': 'Range band', 'Tier': 'Level',
}
RULES = [
    (r'\bminutes\b(?= (?:of|for|sent|approved|ready|overdue|due|missing))', 'meeting minutes'), (r'\bMinutes\b(?= (?:Log|Sheet|Register|Tracker|of|for|sent|approved|ready|overdue|due|missing))', 'Meeting minutes'),
    (r'\bstand-ups?\b', 'stand-up meetings'), (r'\bStand-ups\b', 'Stand-up meetings'), (r'\bretros\b', 'retrospectives'), (r'\bRetros\b', 'Retrospectives'),
    (r'\bburn rate\b', 'spending rate'), (r'\bBurn Rate\b', 'Spending Rate'), (r'\bBurn rate\b', 'Spending rate'),
    (r'\bburndown\b', 'burndown chart'), (r'\bBurndown\b', 'Burndown chart'),
]
if NONLATIN:
    RULES += [(r'\bKPIs\b', 'performance indicators'), (r'\bKPI\b', 'performance indicator'), (r'\bROI\b', 'return on investment'),
              (r'\bCPI\b', 'cost performance index'), (r'\bSPI\b', 'schedule performance index'), (r'\bEAC\b', 'estimate at completion'),
              (r'\bETC\b', 'estimate to complete'), (r'\bBAC\b', 'budget at completion'), (r'\bVAC\b', 'variance at completion'),
              (r'\bRAID\b', 'risks, assumptions, issues and dependencies'), (r'\bRACI\b', 'responsibility matrix'), (r'\bWIP\b', 'work in progress'),
              (r'\bEV\b', 'earned value'), (r'\bPV\b', 'planned value'), (r'\bQA\b', 'quality assurance'), (r'\bUAT\b', 'user acceptance testing')]
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
