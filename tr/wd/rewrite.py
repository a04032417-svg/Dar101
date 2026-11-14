"""English pre-edit for the Wedding and Event Planner suite: ambiguous words become unambiguous ones before machine translation
(the translator sees no context). Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched.
The language comes from translate.py's command line (argv[2])."""
import re, sys
PH = re.compile(r'\{[a-z_0-9]+(?::[a-z0-9_.]+)?\}')
LANG = sys.argv[2] if len(sys.argv) > 2 else ''
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')

EXACT = {
    'Vendor': 'Event supplier', 'Vendors': 'Event suppliers', 'Venue': 'Event venue', 'Venues': 'Event venues', 'Hold': 'Date hold', 'Holds': 'Date holds',
    'Run-of-show': 'Event timeline', 'Run-of-show items': 'Event timeline items', 'Head count': 'Guest count', 'RSVP': 'Invitation reply', 'RSVPs': 'Invitation replies',
    'Load-in': 'Supplier set-up arrival', 'Load-out': 'Supplier pack-down', 'Call time': 'Team arrival time', 'Plus-one': 'Additional guest', 'Booking': 'Supplier booking', 'Bookings': 'Supplier bookings',
    'Balance': 'Balance due', 'Lead': 'Sales enquiry', 'Leads': 'Sales enquiries', 'Enquiry': 'Client enquiry', 'Enquiries': 'Client enquiries', 'Proposal': 'Price proposal',
    'Crew': 'Freelance crew', 'Coordinator': 'Event coordinator', 'Coordinators': 'Event coordinators', 'Planner': 'Event planner', 'Couple': 'Client couple',
    'Open': 'Still open', 'Closed': 'Closed item', 'Clear': 'All clear', 'Draft': 'Draft version', 'Kind': 'Type', 'Band': 'Range band', 'Tier': 'Level', 'Cue': 'Event cue', 'Cues': 'Event cues',
}
RULES = [(r'\brun-of-show\b', 'event timeline'), (r'\bRSVPs?\b', 'invitation reply'), (r'\bhead count\b', 'guest count')]
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
