#!/usr/bin/env python3
# Dar 3.34.13 (2026-11-08, the owner: «اصلح وشغل Anthropic … قلت لك مهن»): 1) Claude (Anthropic) is switched on for the template factory:
# it does the work when no free strong model can (their day spent), within a daily cap, with Opus 5.5 for the deep tier; Dar's other
# work keeps the providers it had; 2) Google's monthly searches leave the ranking: they measured activities searched by the public (couples
# planning a wedding, small shops keeping books, landlords), not professions — no profession's own template phrase reaches Google's
# reporting threshold — so the fields are ranked again by the marketplace evidence of each profession. usage: p3413.py <src dir> [--built ISO]
import sys, os, json, hashlib

SRC = sys.argv[1]; BUILT = sys.argv[sys.argv.index('--built') + 1] if '--built' in sys.argv else '2026-11-08T23:30:00+03:00'
OLDV, NEWV = '3.34.12', '3.34.13'
def rd(p): return open(os.path.join(SRC, p), 'rb').read().decode('utf8')
def wr(p, s): open(os.path.join(SRC, p), 'wb').write(s.encode('utf8'))
def sub1(s, old, new, what):
    n = s.count(old)
    if n != 1: sys.exit(f'PATCH FAIL {what}: found {n}x')
    return s.replace(old, new)

F = rd('dar-fx.php')
R = [
 ("    try { $r = ai_complete($c, $req); } catch (Throwable $e) { if (!($e instanceof DarFail) && function_exists('log_fault')) log_fault($e, 'fx:ai'); return ['err' => 'ai: ' . mb_substr($e->getMessage() . ($e instanceof DarFail && $e->extra ? ' ' . jenc($e->extra) : ''), 0, 300)]; }\n",
  "    $t0 = microtime(true); $r = null; $ex = null;\n"
  "    try { $r = ai_complete($c, $req); } catch (Throwable $e) { $ex = $e; }\n"
  "    // v3.34.13 (the owner, 2026-11-08: «شغل Anthropic»): when no free strong model can answer, Claude (Anthropic) does the work — within the day's cap\n"
  "    if ($ex !== null && empty($o['weak']) && fx_anth_ok() && $dl - (microtime(true) - $t0) >= 20) { $req['paid_ok'] = true; $req['deadline'] = (int)floor($dl - (microtime(true) - $t0)); try { $r = ai_complete($c, $req); $ex = null; } catch (Throwable $e) { $ex = $e; } }\n"
  "    if ($ex !== null) { $e = $ex; if (!($e instanceof DarFail) && function_exists('log_fault')) log_fault($e, 'fx:ai'); return ['err' => 'ai: ' . mb_substr($e->getMessage() . ($e instanceof DarFail && $e->extra ? ' ' . jenc($e->extra) : ''), 0, 300)]; }\n"
  "    if ((string)($r['provider'] ?? '') === 'anthropic') fx_anth_count();\n", 'fx_ai claude fallback'),
 ("    if (meta_get('fx_rank_v') === '4') { meta_set('fx_rank_v', '5'); fx_rank_fix(); } // v3.34.12\n",
  "    if (meta_get('fx_rank_v') === '4') { meta_set('fx_rank_v', '5'); fx_rank_fix(); } // v3.34.12\n"
  "    if (meta_get('fx_rank_v') === '5') { meta_set('fx_rank_v', '6'); fx_rank_professions(); } // v3.34.13\n"
  "    if (meta_get('fx_anth_v') !== '1') { meta_set('fx_anth_v', '1'); fx_anth_on(); } // v3.34.13\n", 'migrations'),
 # (a fresh site: no activity searches, no field researched from Google alone)
 ("const FX_SEARCH = [\n", "const FX_SEARCH = []; // v3.34.13: left out — Google's figures were activities searched by the public, not professions\nconst FX_SEARCH_3411 = [\n", 'search const'),
 ("    $add = ['restaurant' => ['Restaurant', 80, 60, 25, 'Google Keyword Planner (US): restaurant inventory and food-cost spreadsheets searched every month, high cost per click']];\n",
  "    $add = []; // v3.34.13 (the restaurant was researched from Google's activity searches alone)\n", 'search seed add'),
]
for old, new, what in R: F = sub1(F, old, new, what)

ADD = r"""
// ================================================================ v3.34.13 — Claude for the factory; the professions ranked by their own evidence (2026-11-08, Claude)
function fx_anth_cap(): int { $n = (int)(meta_get('fx_anth_cap') ?? 0); return $n > 0 ? min(1000, $n) : 80; } // calls a day (the owner can set fx_anth_cap)
function fx_anth_used(): int { $v = explode('|', (string)(meta_get('fx_anth_day') ?? '')); return ($v[0] ?? '') === gmdate('Y-m-d') ? (int)($v[1] ?? 0) : 0; }
function fx_anth_ok(): bool { return meta_get('ai_anth_scope') === 'fx' && fx_anth_used() < fx_anth_cap(); }
function fx_anth_count(): void { meta_set('fx_anth_day', gmdate('Y-m-d') . '|' . (fx_anth_used() + 1)); }
function fx_anth_on(): void
{
    // Anthropic on, for the factory only (Dar's other work keeps the providers it had); its deep tier Opus 5.5 (not the costlier Mythos tier)
    try { if (!function_exists('ai_cfg') || !function_exists('ai_save')) return; $cfg = ai_cfg(); if (!isset($cfg['providers']['anthropic'])) return;
        $cfg['providers']['anthropic']['enabled'] = true; if ((string)($cfg['providers']['anthropic']['deep'] ?? '') === '') $cfg['providers']['anthropic']['deep'] = 'claude-opus-5-5';
        ai_save($cfg); meta_set('ai_anth_scope', 'fx');
    } catch (Throwable $e) { if (function_exists('log_fault')) log_fault($e, 'fx:anth'); }
}
function fx_rank_professions(): void
{
    // Google's searches out of the ranking (3.34.11's figures were activities, not professions): every researched field back to its marketplace score
    foreach (q("SELECT * FROM fx_rank WHERE search >= 0")->fetchAll() as $r) {
        $why = trim((string)preg_replace('/\s*\|\s*Google \(US\).*$/su', '', (string)$r['why']));
        $sc = in_array((string)$r['src'], ['research', 'web'], true) ? round((int)$r['demand'] * (1 - (int)$r['comp'] / 200) + 20, 1) : (float)$r['score'];
        q('UPDATE fx_rank SET score = ?, why = ?, search = -1, at = ? WHERE p = ?', [$sc, $why, time(), $r['p']]);
    }
    // the restaurant had no marketplace evidence, only Google's activity searches: a guess again (it opens no file)
    q("UPDATE fx_rank SET src = 'estimate', score = ROUND(demand * (1 - comp / 200.0) * 0.6, 1), why = 'estimate: no marketplace evidence read yet' WHERE lower(p) = 'restaurant' AND why LIKE 'Google Keyword Planner%'");
}
"""
F = F.rstrip('\n') + '\n' + ADD.lstrip('\n')
wr('dar-fx.php', F)

A = rd('dar-ai.php')
A = sub1(A, "    if ($public && empty($cfg['public_strong']) && empty($c['pv_strong'])) $ready = array_values(array_filter($ready, fn($id) => !in_array($id, AI_PUBLIC_SKIP, true)));\n",
  "    if ($public && empty($cfg['public_strong']) && empty($c['pv_strong'])) $ready = array_values(array_filter($ready, fn($id) => !in_array($id, AI_PUBLIC_SKIP, true)));\n"
  "    if (empty($req['paid_ok']) && in_array('anthropic', $ready, true) && meta_get('ai_anth_scope') === 'fx') $ready = array_values(array_diff($ready, ['anthropic'])); // v3.34.13: Claude is switched on for the template factory only (the owner, 2026-11-08) — the rest of Dar keeps its providers\n", 'ai anthropic scope')
wr('dar-ai.php', A)

old_tok = json.load(open(os.path.join(SRC, 'lib/manifest.json')))['token']
TOK = NEWV + '-' + hashlib.sha256((NEWV + '\n').encode() + F.encode('utf8')).hexdigest()[:8]
S = rd('dar-sync.php'); S = sub1(S, f"const SYNC_VERSION = '{OLDV}';", f"const SYNC_VERSION = '{NEWV}';", 'sync version'); wr('dar-sync.php', S)
changed = {'dar-fx.php', 'dar-sync.php', 'dar-ai.php'}
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
