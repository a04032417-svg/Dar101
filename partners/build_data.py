import json, re, html, urllib.request

W = '/home/claude/work'
whop = json.load(open(f'{W}/deliv/whop_pub.json'))
docs = json.load(open(f'{W}/deliv/docs.json'))
old = json.load(open(f'{W}/old7/old7_en.json'))
RAW = 'https://raw.githubusercontent.com/a04032417-svg/Dar101/refs/heads/out/{k}/pack/'
SHOP = 'https://cdn.shopify.com/s/files/1/1007/1887/0832/files/'
LANGS = ('English, Arabic, French, Spanish, German, Italian, Portuguese, Turkish, Dutch, Russian, '
         'Persian, Urdu, Hindi, Chinese and Indonesian')
BANNED = re.compile(r'(Microsoft|Windows|\bMac\b|macOS|[Cc]ompatib|Excel 20\d\d|\b20(16|19|21)\b|\b365\b|Apple|Numbers app)')

L15 = dict(ac='accounting-bookkeeping-excel-15-languages', bk='home-bakery-cake-business-excel-suite',
           bs='beauty-studio-excel-suite', cl='cleaning-business-excel-suite', cn='construction-company-excel-15-languages',
           dz='interior-designer-excel-15-languages', ec='online-seller-excel-15-languages', fm='farm-management-excel-15-languages',
           hm='handmade-product-maker-excel-suite', pj='project-management-excel-15-languages', pm='property-management-excel-15-languages',
           pt='personal-training-excel-15-languages', ri='real-estate-investor-excel-suite', sm='social-media-management-excel-15-languages',
           ta='travel-agent-excel-15-languages', tk='trucking-excel-15-languages', wd='wedding-event-planner-excel-suite')
ENG = dict(ho=('home-management-excel-suite', 'Home-Management-Suite-8-workbooks-English.zip?v=1794991827'),
           hf=('household-finance-excel-suite', 'Household-Finance-Suite-8-workbooks-English.zip?v=1794991827'),
           wp=('wedding-planning-excel-suite', 'Wedding-Planning-Suite-8-workbooks-English.zip?v=1794991827'),
           th=('therapy-private-practice-excel-suite', 'Therapy-Private-Practice-Suite-8-workbooks-English.zip?v=1794991827'),
           cc=('childcare-center-excel-suite', 'Home-Daycare-and-Childcare-Center-Suite-8-workbooks-English.zip?v=1794991827'),
           hc=('home-care-agency-excel-suite', 'Home-Care-Agency-Business-Suite-8-workbooks-English.zip?v=1794991827'),
           cr=('car-rental-business-excel-suite', 'Car-Rental-Business-Suite-8-workbooks-English.zip?v=1794991827'),
           au=('author-publisher-excel-suite', 'Author-and-Self-Publisher-Business-Suite-8-workbooks-English.zip?v=1794991827'),
           du=('doula-business-excel-suite', 'Doula-Business-Suite-8-workbooks-English.zip?v=1794991827'),
           np=('nonprofit-organization-excel-suite', 'Nonprofit-Organization-Suite-8-workbooks-English.zip?v=1794991827'),
           hv=('hvac-plumbing-excel-suite', 'HVAC-and-Plumbing-Contractor-Suite-8-workbooks-English.zip?v=1794991829'))
OLD = dict(photo=('photographer-studio-suite-excel-15-languages', ['Photographer-Studio-Suite-2-workbooks-15-languages.zip?v=1794995336'], 2),
           cx=('contractor-job-costing-excel-15-languages', ['BuildLedger-Contractor-Job-Costing-15-languages.zip?v=1794995336'], 1),
           rs=('restaurant-recipe-costing-excel-15-languages', ['Restaurant-Recipe-Costing-Excel-15-languages.zip?v=1794995336'], 1),
           hs=('salon-excel-bookings-staff-pay-15-languages', ['SalonDesk-Manager-15-languages-part1-of-2.zip?v=1794995336',
                                                              'SalonDesk-Manager-15-languages-part2-of-2.zip?v=1794995336'], 1),
           tc=('teacher-gradebook-attendance-excel-15-languages', ['ClassMark-Teacher-Planner-15-languages.zip?v=1794995336'], 1))


def clean_title(t, suffix='', colon=', '):
    t = t.replace(' – ', ', ').replace(' - ', ', ').replace(': ', colon).replace(':', ' ')
    t = t.replace('&', 'and').replace('(', '').replace(')', '').replace('–', ',')
    t = re.sub(r'\s+', ' ', t).strip(' ,')
    if suffix and len(t) + len(suffix) <= 120:
        t += suffix
    while len(t) > 120 and ',' in t:
        t = t.rsplit(',', 1)[0]
    return t[:120]


def short(s):
    s = re.sub(r'\s+', ' ', s.replace(' – ', ', ')).strip()
    if len(s) <= 158:
        return s
    s = s[:155].rsplit(' ', 1)[0].rstrip(',;')
    return s + '.'


def drop_banned(text):
    parts = re.split(r'(?<=[.!?])\s+', text)
    return ' '.join(p for p in parts if not BANNED.search(p))


def paras(desc):
    out = []
    for p in re.split(r'\n\s*\n|\n', desc):
        p = drop_banned(p.strip())
        if p:
            out.append('<p>' + html.escape(p) + '</p>')
    return ''.join(out)


def from_copy(c, receive):
    body = paras(c['description'])
    feats = [drop_banned(f) for f in c['features']]
    feats = [f for f in feats if f]
    body += '<p>What you can do:</p><ul>' + ''.join('<li>' + html.escape(f) + '</li>' for f in feats) + '</ul>'
    body += '<p>' + html.escape(receive) + '</p>'
    return body


def words(h):
    return len(re.sub('<[^>]+>', ' ', h).split())


data = []
for k, h in L15.items():
    c = json.load(open(f'{W}/copy/{k}/en.json'))
    n = re.search(r'ZIP \((\d+) workbooks', docs[k]['text']).group(1)
    receive = (f'You receive one ZIP with {n} connected Excel workbooks, each in 15 languages ({LANGS}), with a '
               f'right-to-left layout for Arabic, Persian and Urdu. Every workbook opens with sample data, so you see '
               f'every alert and dashboard before you type your own. Works in Excel and LibreOffice.')
    g = json.load(urllib.request.urlopen(RAW.format(k=k) + 'gallery.json'))
    data.append(dict(k=k, h=h, title=clean_title(c['seo_title'], ' in 15 Languages'), short=short(c['seo_description']),
                     long=from_copy(c, receive), contents=f'1 ZIP: {n} Excel workbooks, each in 15 languages, with sample data',
                     tags=c['tags'][:8], price=17,
                     zips=[dict(u=f'https://assets-2-prod.whop.com/public/uploads/2026-11-18/{whop[k]}/application.zip',
                                n=g['zip'])],
                     imgs=[RAW.format(k=k) + p for p in g['gallery']['en'][:8]]))

for k, (h, z) in ENG.items():
    c = json.load(open(f'/home/claude/pipe/copy/{k}/en.json'))
    receive = ('You receive one ZIP with 8 connected Excel workbooks in English that also open in Google Sheets. Every '
               'workbook opens with sample data, so every verdict and dashboard works before you type your own. No macros.')
    data.append(dict(k=k, h=h, title=clean_title(c['seo_title']), short=short(c['seo_description']),
                     long=from_copy(c, receive), contents='1 ZIP: 8 Excel workbooks with sample data',
                     tags=c['tags'][:8], price=29, zips=[dict(u=SHOP + z, n=z.split('?')[0])], imgs='SHOPIFY'))

for k, (h, zs, n) in OLD.items():
    o = old[k]
    imgs = o['I'] if isinstance(o['I'], list) else json.loads(o['I'].replace("'", '"'))
    tags = o['G'] if isinstance(o['G'], list) else json.loads(o['G'].replace("'", '"'))
    long = o['H']
    long = re.sub(r'<p>[^<]*(Microsoft|Windows|Mac|[Cc]ompatib|365|20(19|21))[^<]*</p>', '', long)
    long = re.sub(r'<li>[^<]*(Microsoft|Windows|Mac|[Cc]ompatib|365|20(19|21))[^<]*</li>', '', long)
    long += ('<p>' + html.escape(short(o['S'])) + '</p><p>You receive ' + (f'{len(zs)} ZIP files' if len(zs) > 1 else 'one ZIP') + f' with the workbooks in 15 languages ({LANGS}), with a right-to-left layout for Arabic, Persian and Urdu, plus an English demo copy with sample data so you can see every report before you type your own. Works in Excel and LibreOffice.</p>')
    cont = (f'{len(zs)} ZIP files: ' if len(zs) > 1 else '1 ZIP: ') + (f'{n} Excel workbooks' if n > 1 else 'Excel workbook') + ', each in 15 languages'
    data.append(dict(k=k, h=h, title=clean_title(o['T'].replace(' – 15 Languages', ''), ' in 15 Languages', ' for '), short=short(o['S']),
                     long=long, contents=cont, tags=tags[:8], price=17,
                     zips=[dict(u=SHOP + z, n=z.split('?')[0]) for z in zs], imgs=imgs[:8]))

bad = []
for d in data:
    txt = d['title'] + ' ' + d['short'] + ' ' + re.sub('<[^>]+>', ' ', d['long'])
    if BANNED.search(txt):
        bad.append((d['k'], BANNED.search(txt).group(0)))
    if words(d['long']) < 200 or len(d['short']) > 160 or len(d['title']) > 120 or ':' in d['title']:
        bad.append((d['k'], 'len', words(d['long']), len(d['short']), len(d['title'])))
json.dump(data, open('/home/claude/work/eloq/eloq_data.json', 'w'), ensure_ascii=False)
for d in data:
    print(d['k'], d['price'], len(d['title']), words(d['long']), '|', d['title'])
print('BAD', bad, len(data))
