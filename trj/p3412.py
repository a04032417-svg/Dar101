#!/usr/bin/env python3
# Dar 3.34.12 (2026-11-08, Claude — read from Dar's own notes after 3.34.11): no file was approved in six hours. Root causes: 1) the first
# critic had to avoid the architect's provider and the second the first's, and their full payload (a 40,000-character design) is larger than
# what Groq's plan takes (8,000 tokens) — with Gemini the only strong architect, no pair of critics could ever be found; 2) a first review was
# kept only three hours while the second critic was awaited, so the scarce strong quota was spent again on the same review; 3) a guessed
# ranking row (the restaurant, src «estimate», score 17,156 from 3.34.4) kept the restaurant out of the researched fields and showed a false
# top score. usage: p3412.py <src dir> [--built ISO]
import sys, os, json, hashlib

SRC = sys.argv[1]; BUILT = sys.argv[sys.argv.index('--built') + 1] if '--built' in sys.argv else '2026-11-08T23:00:00+03:00'
OLDV, NEWV = '3.34.11', '3.34.12'
def rd(p): return open(os.path.join(SRC, p), 'rb').read().decode('utf8')
def wr(p, s): open(os.path.join(SRC, p), 'wb').write(s.encode('utf8'))
def sub1(s, old, new, what):
    n = s.count(old)
    if n != 1: sys.exit(f'PATCH FAIL {what}: found {n}x')
    return s.replace(old, new)

F = rd('dar-fx.php')
R = [
 # 1a. the first critic: another provider than the architect's when one answers, else the architect's own strong model (never a stall)
 ("    else $r = fx_ai($sys, 'Review it now. One JSON object only.', 'deep', 3000, fx_dl($left, 60), ['temp' => 0.2, 'avoid' => $avoid]);\n",
  "    else { $r = fx_ai($sys, 'Review it now. One JSON object only.', 'deep', 3000, fx_dl($left, 60), ['temp' => 0.2, 'avoid' => $avoid]);\n"
  "        if (isset($r['err']) && $avoid && $left() > 40) $r = fx_ai($sys, 'Review it now. One JSON object only.', 'deep', 3000, fx_dl($left, 55), ['temp' => 0.2]); } // v3.34.12: no other strong provider answered — the architect's own strong model reviews; the second critic is another provider\n", 'critic one fallback'),
 # 2. a first review is kept a day while the second critic is awaited (the design does not change meanwhile)
 ("    if (is_array($c1) && (int)($c1['round'] ?? -1) === (int)$it['round'] && (int)($c1['at'] ?? 0) > time() - 10800 && is_array($c1['j'] ?? null))",
  "    if (is_array($c1) && (int)($c1['round'] ?? -1) === (int)$it['round'] && (int)($c1['at'] ?? 0) > time() - 86400 && is_array($c1['j'] ?? null))", 'crit1 a day (read)'),
 ("'at' => (int)($c1['at'] ?? 0) > time() - 10800 && is_array($c1) ? (int)$c1['at'] : time()];",
  "'at' => (int)($c1['at'] ?? 0) > time() - 86400 && is_array($c1) ? (int)$c1['at'] : time()];", 'crit1 a day (keep)'),
 # 1b. the second critic: another provider than the first's, the design in its compact form, so a plan of 8,000 tokens takes it
 ("        $r2 = fx_ai($sys, 'Review it now. One JSON object only.', 'deep', 3000, fx_dl($left, 55), ['temp' => 0.2, 'avoid' => array_values(array_unique(array_merge($avoid, [(string)$r['provider']])))]);\n",
  "        $p0 = mb_strpos($sys, \"\\n\\nTHE FIELD: \"); $sys2 = ($p0 === false ? $sys : mb_substr($sys, 0, $p0)) . \"\\n\\nTHE FIELD: \" . $it['profession'] . \"\\nRESEARCH BRIEF: \" . mb_substr(jenc(['jobs' => $it['brief']['jobs'] ?? [], 'gaps' => $it['brief']['competitor_gaps'] ?? [], 'innovations' => $it['brief']['innovations'] ?? []]), 0, 2500) . \"\\n\\nTHE DESIGN (compact: each column key:type, a calculated one with its formula, the dashboard, charts and forms):\\n\" . fx_spec_compact($it['spec']);\n"
  "        $r2 = fx_ai($sys2, 'Review it now. One JSON object only.', 'deep', 1500, fx_dl($left, 55), ['temp' => 0.2, 'avoid' => [(string)$r['provider']]]); // v3.34.12: another provider than the first critic's (the architect's may judge it)\n", 'second critic compact'),
 # 3. the ranking: a guessed row of a researched field, and guessed scores out of scale
 ("    if (meta_get('fx_rank_v') === '3') { meta_set('fx_rank_v', '4'); fx_search_seed(); meta_set('fx_drop_epoch', (string)now_ms()); } // v3.34.11\n",
  "    if (meta_get('fx_rank_v') === '3') { meta_set('fx_rank_v', '4'); fx_search_seed(); meta_set('fx_drop_epoch', (string)now_ms()); } // v3.34.11\n"
  "    if (meta_get('fx_rank_v') === '4') { meta_set('fx_rank_v', '5'); fx_rank_fix(); } // v3.34.12\n", 'migration 5'),
 ("    foreach ($add as $k => [$p, $d, $c, $price, $why]) if (isset($have[$k]) && !one('SELECT 1 FROM fx_rank WHERE lower(p) = ?', [$k]))\n        q('INSERT INTO fx_rank (p, demand, comp, price, score, why, at, src) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', [$p, $d, $c, $price, round($d * (1 - $c / 200) + 20, 1), $why, time(), 'research']);\n",
  "    foreach ($add as $k => [$p, $d, $c, $price, $why]) if (isset($have[$k]) && !one(\"SELECT 1 FROM fx_rank WHERE lower(p) = ? AND src IN ('research', 'web')\", [$k])) // v3.34.12: a guessed row is replaced\n"
  "        q('INSERT INTO fx_rank (p, demand, comp, price, score, why, at, src) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(p) DO UPDATE SET demand = excluded.demand, comp = excluded.comp, price = excluded.price, score = excluded.score, why = excluded.why, at = excluded.at, src = excluded.src', [$p, $d, $c, $price, round($d * (1 - $c / 200) + 20, 1), $why, time(), 'research']);\n", 'search seed upsert'),
]
for old, new, what in R: F = sub1(F, old, new, what)

ADD = r"""
// ================================================================ v3.34.12 — critics that can be found; the ranking's guessed rows (2026-11-08, Claude)
// the design for a second critic whose plan takes less: every column as key:type (a calculated one with its formula), the lists, settings,
// dashboard, charts, gauges, filters and forms — the whole structure in a few thousand characters
function fx_spec_compact(array $s, int $max = 9500): string
{
    $S = fn($v, int $n) => mb_substr(is_scalar($v) ? (string)$v : jenc($v), 0, $n); $T = [];
    foreach ((array)($s['tables'] ?? []) as $t) { if (!is_array($t)) continue; $cols = [];
        foreach ((array)($t['columns'] ?? []) as $c) { if (!is_array($c)) continue; $x = (string)($c['key'] ?? '') . ':' . (string)($c['type'] ?? '');
            if (($c['type'] ?? '') === 'calc' && isset($c['formula'])) $x .= '=' . $S($c['formula'], 90); elseif (!empty($c['ref'])) $x .= '>' . $S($c['ref'], 40); elseif (!empty($c['list'])) $x .= '[' . $S($c['list'], 30) . ']';
            $cols[] = $x; }
        $T[] = ['sheet' => $S($t['sheet'] ?? '', 40), 'key' => $S($t['key'] ?? '', 30), 'hint' => $S($t['hint'] ?? '', 110), 'columns' => $cols, 'demo_rows' => count((array)($t['demo'] ?? [])), 'alerts' => count((array)($t['alerts'] ?? [])), 'sample' => array_slice((array)($t['demo'] ?? []), 0, 1)]; }
    $d = is_array($s['dashboard'] ?? null) ? $s['dashboard'] : []; $in = is_array($s['insights'] ?? null) ? $s['insights'] : []; $A = fn($v) => array_values(array_filter(is_array($v) ? $v : [], 'is_array'));
    $o = ['name' => $S($s['name'] ?? '', 80), 'tagline' => $S($s['tagline'] ?? '', 120),
        'settings' => array_map(fn($x) => $S($x['label'] ?? $x['key'] ?? '', 40), $A($s['settings'] ?? null)),
        'lists' => array_map(fn($l) => $S($l['key'] ?? '', 30) . ': ' . implode(', ', array_map(fn($v) => is_array($v) ? $S($v['label'] ?? $v['key'] ?? '', 30) : $S($v, 30), array_slice((array)($l['values'] ?? []), 0, 8))), $A($s['lists'] ?? null)),
        'tables' => $T,
        'kpis' => array_map(fn($k) => $S($k['label'] ?? '', 50) . (isset($k['formula']) ? ' = ' . $S($k['formula'], 90) : ''), $A($d['kpis'] ?? null)),
        'monthly' => array_map(fn($x) => $S($x['label'] ?? '', 40), $A($d['monthly']['series'] ?? null)), 'breakdowns' => array_map(fn($b) => $S($b['title'] ?? '', 50) . ' by ' . $S($b['by'] ?? '', 40), $A($d['breakdowns'] ?? null)),
        'charts' => array_map(fn($c) => $S($c['title'] ?? '', 60) . ' (' . $S($c['type'] ?? '', 12) . ')', $A($in['charts'] ?? null)), 'gauges' => array_map(fn($g) => $S($g['title'] ?? '', 60), $A($in['gauges'] ?? null)), 'filters' => array_map(fn($f) => $S($f['label'] ?? '', 40), $A($in['filters'] ?? null)),
        'forms' => array_map(fn($f) => $S($f['sheet'] ?? '', 40) . ': ' . implode(', ', array_map(fn($x) => is_array($x) ? $S($x['label'] ?? '', 30) : '', array_slice((array)($f['fields'] ?? []), 0, 12))) . (!empty($f['lines']) ? ' + item lines' : ''), $A($s['forms'] ?? null)),
        'guide' => array_map(fn($g) => $S($g, 100), array_slice((array)($s['guide'] ?? []), 0, 8))];
    // (shortened step by step while it is too long: the guide and sample rows, then the hints and long formulas, then the KPIs' formulas)
    $j = jenc($o); if (mb_strlen($j) <= $max) return $j;
    unset($o['guide']); foreach ($o['tables'] as $i => $t) unset($o['tables'][$i]['sample']); $j = jenc($o); if (mb_strlen($j) <= $max) return $j;
    foreach ($o['tables'] as $i => $t) { $o['tables'][$i]['hint'] = mb_substr($t['hint'], 0, 50); $o['tables'][$i]['columns'] = array_map(fn($c) => mb_substr($c, 0, 64), $t['columns']); } $j = jenc($o); if (mb_strlen($j) <= $max) return $j;
    $o['kpis'] = array_map(fn($k) => explode(' = ', $k)[0], $o['kpis']); foreach ($o['tables'] as $i => $t) unset($o['tables'][$i]['hint']); $j = jenc($o); if (mb_strlen($j) <= $max) return $j;
    foreach ($o['tables'] as $i => $t) $o['tables'][$i]['columns'] = array_map(fn($c) => mb_substr($c, 0, 40), $t['columns']); return mb_substr(jenc($o), 0, $max);
}
function fx_rank_fix(): void
{
    // a guessed score out of scale (3.34.4's guesses were not on the 0–130 scale) is put back on it, still a guess (it never opens a file)
    q("UPDATE fx_rank SET score = ROUND(demand * (1 - comp / 200.0) * 0.6, 1) WHERE src NOT IN ('research', 'web') AND score > 150");
    // the restaurant: researched from Google's own searches (3.34.11) — its guessed row is replaced, with the searches' weight
    $r = one('SELECT * FROM fx_rank WHERE lower(p) = ?', ['restaurant']);
    if ($r && !in_array((string)$r['src'], ['research', 'web'], true)) { $m = (int)($r['search'] ?? -1); if ($m < 0) $m = 260;
        q("UPDATE fx_rank SET demand = 80, comp = 60, price = 25, score = ?, why = ?, src = 'research', search = ?, at = ? WHERE p = ?", [round(80 * (1 - 60 / 200) + 20 + fx_search_bonus($m), 1), 'Google Keyword Planner (US): «restaurant inventory spreadsheet» ' . $m . ' a month, «restaurant food inventory template» 170, cost per click USD 56–63 — buyers who pay', $m, time(), $r['p']]); }
}
"""
F = F.rstrip('\n') + '\n' + ADD.lstrip('\n')
wr('dar-fx.php', F)

old_tok = json.load(open(os.path.join(SRC, 'lib/manifest.json')))['token']
TOK = NEWV + '-' + hashlib.sha256((NEWV + '\n').encode() + F.encode('utf8')).hexdigest()[:8]
S = rd('dar-sync.php'); S = sub1(S, f"const SYNC_VERSION = '{OLDV}';", f"const SYNC_VERSION = '{NEWV}';", 'sync version'); wr('dar-sync.php', S)
changed = {'dar-fx.php', 'dar-sync.php'}
for root, _, files in os.walk(SRC):
    for fn in files:
        p = os.path.join(root, fn); rel = os.path.relpath(p, SRC)
        if rel == 'lib/manifest.json': continue
        try: s = open(p, 'rb').read().decode('utf8')
        except Exception: continue
        if old_tok in s: open(p, 'wb').write(s.replace(old_tok, TOK).encode('utf8')); changed.add(rel)
C = rd('assets/core.js'); C = sub1(C, f"export const VERSION = '{OLDV}-fx';", f"export const VERSION = '{NEWV}-fx';", 'core version'); wr('assets/core.js', C); changed.add('assets/core.js')
M = json.load(open(os.path.join(SRC, 'lib/manifest.json')))
M['version'] = NEWV; M['token'] = TOK; M['built'] = BUILT
for rel in list(M['files']):
    p = os.path.join(SRC, rel)
    if os.path.isfile(p): M['files'][rel] = hashlib.sha1(open(p, 'rb').read()).hexdigest()
open(os.path.join(SRC, 'lib/manifest.json'), 'w').write(json.dumps(M, ensure_ascii=False, separators=(',', ':')))
print(json.dumps({'token': TOK, 'changed': len(changed)}))
