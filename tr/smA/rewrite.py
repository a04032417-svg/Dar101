"""English pre-edit for the Social Media Management suite: ambiguous words become unambiguous ones before machine translation
(the translator sees no context). Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched.
The language comes from translate.py's command line (argv[2])."""
import re, sys
PH = re.compile(r'\{[a-z_0-9]+(?::[a-z0-9_.]+)?\}')
LANG = sys.argv[2] if len(sys.argv) > 2 else ''
NONLATIN = LANG in ('ar', 'fa', 'ur', 'hi', 'zh', 'ru')
PUBL = LANG in ('fr', 'es', 'it', 'pt', 'ar', 'ru')          # «publication» gives the standard word for a social media post
SOCIAL = LANG in ('zh', 'tr', 'id')                           # «social post» needed, «post» alone becomes mail or a job
WEST = LANG in ('fr', 'es', 'de', 'it', 'pt', 'nl')           # these keep the word «engagement»

EXACT = {
    'Live': 'Running', 'Live now': 'Running now', 'Live no': 'Not running', 'Spend': 'Advertising expenditure', 'Reach': 'Audience reach',
    'Engagement': 'Engagement' if WEST else 'Interactions', 'Shares': 'Reposts', 'Saves': 'Bookmarks', 'Leads': 'Prospects', 'Lead': 'Prospect',
    'Brief': 'Creative brief', 'Posts': 'Publications' if PUBL else ('Social posts' if SOCIAL else 'Posts'),
}

POST = 'publication' if PUBL else ('social post' if SOCIAL else 'post')
RULES = [
    (r'\b[Gg]o live\b', 'launch'), (r'\b[Gg]oes live\b', 'launches'), (r'\b[Ww]ent live\b', 'was published'), (r'\b[Ll]ive and approved\b', 'running and approved'),
    (r'\b[Cc]ampaigns live\b', 'campaigns running'), (r'\b[Ll]ive sessions\b', 'live streams'), (r'\b[Ll]ive [Ss]essions\b', 'Live streams'),
    (r'\bto post\b', 'to publish'), (r'\bposted\b', 'published'), (r'\bPosted\b', 'Published'), (r'\bposting\b', 'publishing'), (r'\bPosting\b', 'Publishing'),
    (r'\bposts\b', POST + 's'), (r'\bPosts\b', POST.capitalize() + 's'), (r'(?<!to )(?<!will )\bpost\b', POST), (r'\bPost\b', POST.capitalize()),
    (r'(?<!to )(?<!can )(?<!will )(?<!you )(?<!we )(?<!not )\breach\b(?! out| the| your| a | an | us| their| it)', 'audience reach'),
    (r'\bReach\b(?! out)', 'Audience reach'),
    (r'\b[Ss]hare of\b', 'proportion of'), (r'\bshare\b(?= of)', 'proportion'), (r'\bMargin share\b', 'Margin percentage'), (r'\bmargin share\b', 'margin percentage'),
    (r'\bleads\b', 'prospects'), (r'\bLeads\b', 'Prospects'), (r'(?<!to )(?<!will )\blead\b', 'prospect'), (r'\bLead\b', 'Prospect'),
    (r'\bbriefs\b', 'creative briefs'), (r'\bBriefs\b', 'Creative briefs'), (r'(?<!creative )\bbrief\b', 'creative brief'), (r'\bBrief\b', 'Creative brief'),
    (r'(?<!content )\bcreators\b', 'content creators'), (r'\bCreators\b', 'Content creators'), (r'(?<!content )\bcreator\b', 'content creator'), (r'\bCreator\b', 'Content creator'),
    (r'\b[Aa]d sets\b', 'ad groups'), (r'\b[Aa]d set\b', 'ad group'),
    (r'\bad spend\b', 'advertising expenditure'), (r'\bAd spend\b', 'Advertising expenditure'),
    (r'(?<!to )(?<!will )(?<!you )(?<!we )(?<!they )(?<!not )\bspend\b', 'expenditure'), (r'\bSpend\b', 'Expenditure'),
    (r'\bpacing\b', 'spending pace'), (r'\bPacing\b', 'Spending pace'),
    (r'\btags\b', 'labels'), (r'\bTags\b', 'Labels'),
    (r'\bslots\b', 'time slots'), (r'\bSlots\b', 'Time slots'), (r'\bslot\b', 'time slot'), (r'\bSlot\b', 'Time slot'),
    (r'\bchurn\b', 'client loss'), (r'\bChurn\b', 'Client loss'),
    (r'\boverruns\b', 'excesses'), (r'\bOverruns\b', 'Excesses'), (r'\boverrun\b', 'excess'), (r'\bOverrun\b', 'Excess'),
    (r'\bupsell\b', 'upgrade sale'), (r'\bUpsell\b', 'Upgrade sale'),
    (r'\bReels\b', 'Short videos'), (r'\breels\b', 'short videos'), (r'\bReel\b', 'Short video'), (r'\breel\b', 'short video'),
    (r'\bUGC\b', 'user-generated content'), (r'\bDMs\b', 'direct messages'), (r'\bDM\b', 'direct message'),
    (r'\bsaves\b', 'bookmarks'), (r'\bSaves\b', 'Bookmarks'),
    (r'\bCreator handle\b', 'Content creator account name'), (r'(?<=[a-z] )\bhandle\b(?= on| ends| has| for)', 'account name'),
    (r'\bHandle\b', 'Account name'),
]
if not WEST: RULES += [(r'\bengagement\b', 'interaction'), (r'\bEngagement\b', 'Interaction')]
if NONLATIN:
    RULES += [(r'\bROAS\b', 'return on advertising expenditure'), (r'\bCTR\b', 'click-through rate'), (r'\bCPM\b', 'cost per thousand impressions'),
              (r'\bCPC\b', 'cost per click'), (r'\bCPA\b', 'cost per result'), (r'\bKPIs\b', 'performance indicators'), (r'\bKPI\b', 'performance indicator'),
              (r'\bROI\b', 'return on investment'), (r'\bAPI\b', 'programming interface')]
CRULES = [(re.compile(a), b) for a, b in RULES]
SMALL = {'and', 'of', 'to', 'a', 'an', 'the', 'in', 'for', 'vs', 'or', 'per', 'by', 'on', 'with', 'from', 'at'}


def sentence_case(t, force=False):
    w = t.split(' ')
    if len(w) < 2: return t
    rest = [x for x in w[1:] if x.lower() not in SMALL and x[:1].isalpha()]
    if not rest or not (force or all(x[:1].isupper() for x in rest)): return t
    keep = {'I', 'Instagram', 'Facebook', 'TikTok', 'LinkedIn', 'YouTube', 'Pinterest', 'Snapchat', 'WhatsApp', 'X'}
    return ' '.join([w[0]] + [x if (x.lower() in SMALL or x[1:] != x[1:].lower() or x in keep) else x.lower() for x in w[1:]])


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
