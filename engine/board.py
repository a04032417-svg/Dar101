"""board.py (engine v1.4) — the listing-picture design of the real-estate kits (images4.py), for every product the factory makes: the workbook
shown as a drawing on a blueprint grid, the real sheet in a window with its own tabs, zoomed cells pinned to it with dimension-line leaders.
theme(ink, accent) colours it per product; SH is the folder of the shots (<name>.png)."""
import os, base64
from playwright.sync_api import sync_playwright
SH = '.'
W, H = 2400, 1800
INK, BLUE, BRASS, MIST, RED, LEAF = '#13233A', '#2F6FA3', '#B88A2E', '#E8EDF2', '#C8463D', '#2E8B57'











def img(n): return 'data:image/png;base64,' + base64.b64encode(open(os.path.join(SH, n + '.png'), 'rb').read()).decode()


GRID = ("data:image/svg+xml;utf8," + "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>"
        "<path d='M0 0H240M0 48H240M0 96H240M0 144H240M0 192H240M0 0V240M48 0V240M96 0V240M144 0V240M192 0V240' stroke='%23D5DDE6' stroke-width='1'/>"
        "<path d='M0 0H240M0 0V240' stroke='%23C3CEDA' stroke-width='2'/></svg>")
PLAN = """<svg class="plan" viewBox="0 0 600 420" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="#9FB3C8" stroke-width="3">
<path d="M10 10H590V410H10Z"/><path d="M10 170H230V410"/><path d="M230 10V120M230 150V170H360V410"/><path d="M360 250H590"/><path d="M450 10V250"/>
<path d="M300 170A40 40 0 0 1 340 130" stroke-dasharray="6 6"/><path d="M60 170A50 50 0 0 0 110 120" stroke-dasharray="6 6"/>
<path d="M10 440H590M10 430V450M590 430V450" stroke="#B88A2E"/></svg>"""

def _css():
    return f"""*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{W}px;height:{H}px;overflow:hidden;position:relative;font-family:'Inter',sans-serif;color:{INK};
 background:{MIST} url("{GRID}");}}
.plan{{position:absolute;left:-40px;bottom:-30px;width:760px;opacity:.55}}
.l{{position:absolute;left:110px;top:110px;width:700px}}
.prod{{font-size:30px;font-weight:600;color:{BRASS};letter-spacing:.2px}}
h1{{font-family:'Inter Display','Inter';font-weight:800;font-size:92px;line-height:.98;letter-spacing:-2.6px;margin-top:26px}}
.sub{{font-size:33px;line-height:1.42;color:#3E5068;margin-top:30px}}
.pts{{margin-top:44px;display:flex;flex-direction:column;gap:26px}}
.pt{{display:flex;gap:22px;align-items:flex-start;font-size:30px;line-height:1.35;color:#2A3B52}}
.pt i{{flex:0 0 18px;height:18px;margin-top:12px;background:{BRASS};transform:rotate(45deg)}}
.pt b{{color:{INK}}}
.win{{position:absolute;background:#fff;border-radius:16px;box-shadow:0 46px 100px rgba(19,35,58,.30),0 0 0 1px rgba(19,35,58,.08);overflow:hidden;display:flex;flex-direction:column}}
.bar{{height:58px;background:{INK};color:#fff;display:flex;align-items:center;padding:0 24px;gap:14px;font-size:22px;font-weight:600;flex:0 0 auto}}
.bar s{{width:13px;height:13px;border-radius:50%;background:#3C5476;display:inline-block}}
.bar em{{font-style:normal;opacity:.9;margin-left:12px}}
.sheet{{flex:1;display:flex;align-items:flex-start;justify-content:center;overflow:hidden;padding:18px 18px 0;background:#fff;min-height:0}}
.sheet img{{max-width:100%;max-height:100%;object-fit:contain;object-position:top}}
.tabs{{flex:0 0 46px;background:#F1F4F8;border-top:1px solid #D9E0E8;display:flex;align-items:stretch;overflow:hidden;font-size:19px;color:#55657A;padding-left:14px}}
.tabs span{{padding:0 18px;display:flex;align-items:center;white-space:nowrap;border-right:1px solid #DDE3EA}}
.tabs span.on{{background:#fff;color:{INK};font-weight:700;box-shadow:inset 0 4px 0 {BRASS}}}
.zoom{{position:absolute;background:#fff;border-radius:14px;box-shadow:0 30px 70px rgba(19,35,58,.28);padding:16px 16px 20px;border-top:7px solid {BRASS}}}
.zoom img{{display:block;width:100%}}
.zoom p{{font-size:25px;line-height:1.32;margin-top:14px;color:#2A3B52}}
.zoom p b{{color:{INK}}}
.lead{{position:absolute;border-top:3px solid {BRASS};height:0}}
.lead:before,.lead:after{{content:'';position:absolute;top:-12px;width:3px;height:21px;background:{BRASS}}}
.lead:before{{left:0}}.lead:after{{right:0}}
.foot{{position:absolute;left:110px;bottom:84px;font-size:24px;color:#5A6B80;display:flex;gap:30px}}
.foot span{{display:flex;align-items:center;gap:10px}}.foot span:before{{content:'';width:10px;height:10px;background:{BLUE};border-radius:2px}}
"""

CSS = _css()


def theme(ink, accent):
    global INK, BRASS, CSS
    INK, BRASS = "#" + ink.lstrip("#"), "#" + accent.lstrip("#"); CSS = _css()


def window(shot_, x, y, w, h, fname, tabs, on, rot=0):
    """h=None: the window is as tall as the sheet's picture needs at width w (no empty paper)."""
    if h is None:
        from PIL import Image
        iw, ih = Image.open(os.path.join(SH, shot_ + '.png')).size; h = int(58 + 46 + 18 + (w - 36) * ih / iw) + 4
    t = ''.join(f'<span class="{"on" if n == on else ""}">{n}</span>' for n in tabs)
    return (f'<div class="win" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;transform:rotate({rot}deg)">'
            f'<div class="bar"><s></s><s></s><s></s><em>{fname}</em></div><div class="sheet"><img src="{img(shot_)}"></div><div class="tabs">{t}</div></div>')


def zoom(shot_, x, y, w, text):
    return f'<div class="zoom" style="left:{x}px;top:{y}px;width:{w}px"><img src="{img(shot_)}"><p>{text}</p></div>'


def lead(x, y, w): return f'<div class="lead" style="left:{x}px;top:{y}px;width:{w}px"></div>'


def page(prod, h1, sub, pts, body, foot=None):
    p = ''.join(f'<div class="pt"><i></i><div>{x}</div></div>' for x in pts)
    f = f'<div class="foot">{"".join(f"<span>{x}</span>" for x in foot)}</div>' if foot else ''
    return (f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{PLAN}'
            f'<div class="l"><div class="prod">{prod}</div><h1>{h1}</h1><div class="sub">{sub}</div><div class="pts">{p}</div></div>{body}{f}</body></html>')


def shoot(pages, out, head=''):
    """pages -> PNGs; head (v1.4) is what the language adds to every page (its font, right-to-left, fitting headings)"""
    os.makedirs(out, exist_ok=True); paths = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        for name, html in pages:
            if head: html = html.replace('</head>', head + '</head>', 1)
            f = os.path.join(SH, name + '.html'); open(f, 'w', encoding='utf8').write(html); pg.goto('file://' + f); pg.wait_for_timeout(300 if head else 250)
            o = os.path.join(out, name + '.png'); pg.screenshot(path=o); paths.append(o)
        b.close()
    return paths





def _size(n):
    from PIL import Image
    return Image.open(os.path.join(SH, n + '.png')).size


def stack(win, fname, tabs, on, zooms, x=880, w=1420, top=110, bottom=1710, gap=46, extra=''):
    """the right side: the window on top, its zoomed cells in a row under it, sized so nothing is cut and no paper is left empty."""
    iw, ih = _size(win); hw = int(58 + 46 + 18 + (w - 36) * ih / iw) + 4
    n = len(zooms); zw = ((w - (n - 1) * 70) // n if n > 1 else 760) if n else 0
    def zh(z, width): zi = _size(z[0]); return 32 + (width - 32) * zi[1] / zi[0] + 120
    room = bottom - top - gap
    while n and hw + max(zh(z, zw) for z in zooms) > room and (hw > 520):
        w2 = w - 40; hw = int(58 + 46 + 18 + (w2 - 36) * ih / iw) + 4; w = w2
    hw = min(hw, room - (max(zh(z, zw) for z in zooms) if n else 0))
    total = hw + (gap + max(zh(z, zw) for z in zooms) if n else 0); top = top + max(0, (bottom - top - total) // 2)
    out = window(win, x + (1420 - w), top, w, hw, fname, tabs, on)
    zy = top + hw + gap; zx = x
    for i, z in enumerate(zooms):
        out += zoom(z[0], zx, zy, zw, z[1])
        if i < n - 1: out += lead(zx + zw + 8, zy + 70, 54)
        zx += zw + 70
    return out + extra


def collage(wins, fname, widths=(1180, 1140, 640), x0=880, x1=2300, top=110, bottom=1710):
    """(engine 1.5) the hero overview: three different sheets overlapping like papers on a desk — charts behind on the left, the dashboard on the
    right, a data sheet in front. wins = [(shot, tabs, on)] in that order; widths = their widths."""
    def hh(i, w): iw, ih = _size(wins[i][0]); return int(58 + 46 + 18 + (w - 36) * ih / iw) + 4
    wa, wb_, wc = widths; ha, hb, hc = hh(0, wa), hh(1, wb_), hh(2, wc)
    # a = charts (back, left), c = dashboard (right, middle), b = data sheet (front, lower)
    ya, yc = 0, int(ha * .34); yb = int(max(ha, yc + hc) * .68)
    ext = max(ya + ha, yc + hc, yb + hb)
    k = 1.0
    while ext * k > bottom - top and k > .6: k -= .04
    wa, wb_, wc = int(wa * k), int(wb_ * k), int(wc * k); ha, hb, hc = hh(0, wa), hh(1, wb_), hh(2, wc)
    yc = int(ha * .34); yb = int(max(ha, yc + hc) * .68); ext = max(ha, yc + hc, yb + hb)
    oy = top + max(0, (bottom - top - ext) // 2)
    xa, xc, xb = x0, x1 - wc, x0 + (x1 - x0 - wb_) // 2 - 40
    out = window(wins[0][0], xa, oy, wa, ha, fname, wins[0][1], wins[0][2])
    out += window(wins[2][0], xc, oy + yc, wc, hc, fname, wins[2][1], wins[2][2])
    out += window(wins[1][0], xb, oy + yb, wb_, hb, fname, wins[1][1], wins[1][2])
    return out


CSSW = """.top{position:absolute;left:110px;top:96px;right:110px;display:flex;align-items:flex-end;gap:80px}
.top .a{flex:0 0 1080px}.top h1{font-size:88px}.top .sub{flex:1;margin:0 0 6px;font-size:31px}"""


def page_wide(prod, h1, sub, wins, zooms, top=400, bottom=1730, gap=44):
    """wide tables: the headline across the top, the window(s) across the whole width, the zoomed cells in a row underneath."""
    W_ = W - 220; n = len(zooms)
    def wh(sh, w): iw, ih = _size(sh); return int(58 + 46 + 18 + (w - 36) * ih / iw) + 4
    def zh(z, width): zi = _size(z[0]); return 32 + (width - 32) * zi[1] / zi[0] + 110
    w = W_; zw = (W_ - (n - 1) * 70) // n if n else 0
    while True:
        hs = [wh(x[0], w) for x in wins]; total = sum(hs) + gap * (len(wins) - 1) + (gap + max(zh(z, zw) for z in zooms) if n else 0)
        if total <= bottom - top or w < 560 or sum(hs) + gap * (len(wins) - 1) <= 0.55 * (bottom - top): break   # (engine 1.5: was w < 1200 — a narrow table pushed its zoom card off the picture)
        w -= 40
    y = top + max(0, (bottom - top - total) // 2); x = 110 + (W_ - w) // 2; body = ''
    for (sh, fname, tabs, on), h in zip(wins, hs):
        body += window(sh, x, y, w, h, fname, tabs, on); y += h + gap
    room = bottom - y; cards = []
    for z in zooms:  # each zoom as wide as its share, but never taller than the room left
        zi = _size(z[0]); cw = min(zw, int((room - 142) * zi[0] / zi[1]) + 32); cards.append((z, cw))
    used = sum(c for _, c in cards) + 70 * (n - 1); zx = 110 + (W_ - used) // 2
    for i, (z, cw) in enumerate(cards):
        body += zoom(z[0], zx, y, cw, z[1])
        if i < n - 1: body += lead(zx + cw + 8, y + 70, 54)
        zx += cw + 70
    return (f'<html><head><meta charset="utf-8"><style>{CSS}{CSSW}</style></head><body>{PLAN}'
            f'<div class="top"><div class="a"><div class="prod">{prod}</div><h1>{h1}</h1></div><div class="sub">{sub}</div></div>{body}</body></html>')


def plan_page(prod, h1, sub, rooms, kind_note):
    """«What is inside»: the workbook drawn as a floor plan — each room a part of the business, its sheets as the furniture."""
    css = f""".fp{{position:absolute;left:110px;top:430px;width:2180px;height:1250px;border:6px solid {INK};background:rgba(255,255,255,.72)}}
.rm{{position:absolute;border:3px solid {INK};padding:30px 34px}}
.rm h3{{font-family:'Inter Display';font-weight:800;font-size:42px;letter-spacing:-1px;color:{INK}}}
.rm p{{font-size:23px;color:#56677C;margin-top:6px;line-height:1.3}}
.rm ul{{list-style:none;display:grid;grid-template-columns:repeat(var(--c,2),1fr);gap:14px;margin-top:22px}}
.rm li{{font-size:25px;font-weight:700;padding:12px 16px;border:2px solid {BLUE};color:{BLUE};background:#fff;border-radius:4px;line-height:1.2}}
.rm li small{{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:20px;font-weight:400;color:#56677C;margin-top:4px;line-height:1.25}}
.rm li.n{{border-color:{BRASS};color:#7A5A12;background:#FFF8E6}}
.door{{position:absolute;background:{MIST};}}
.dim{{position:absolute;left:110px;top:1700px;width:2180px;border-top:3px solid {BRASS};font-size:22px;color:#7A5A12;text-align:center;padding-top:8px}}
.dim:before,.dim:after{{content:'';position:absolute;top:-14px;width:3px;height:25px;background:{BRASS}}}.dim:before{{left:0}}.dim:after{{right:0}}"""
    body = '<div class="fp">' + ''.join(
        f'<div class="rm" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;--c:{3 if w > 1000 else 2}"><h3>{t}</h3><p>{d}</p><ul>'
        + ''.join(f'<li class="{"n" if n.startswith("*") else ""}">{n.lstrip("*").split("|")[0]}<small>{(n.split("|") + [""])[1]}</small></li>' for n in names) + '</ul></div>'
        for (x, y, w, h, t, d, names) in rooms) + '</div>'
    return (f'<html><head><meta charset="utf-8"><style>{CSS}{CSSW}{css}</style></head><body>'
            f'<div class="top"><div class="a"><div class="prod">{prod}</div><h1>{h1}</h1></div><div class="sub">{sub}</div></div>{body}<div class="dim">{kind_note}</div></body></html>')
