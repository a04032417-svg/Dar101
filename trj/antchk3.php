<?php
// One-off read-only check (2026-11-09, Claude), second round: Dar's own research request (its system text, 3,000 tokens of room) to
// Claude Sonnet 5.5 as Dar sends it, and with no up-front thinking — what comes back (code, stop reason, block kinds, thinking tokens,
// text length, time). No key and no answer text is written. Run: php antchk3.php <base64 key>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$here = __DIR__; $site = '/home/u791571885/domains/dar.ink/public_html';
$lk = fopen("$here/antchk3.lock", 'c'); if (!flock($lk, LOCK_EX | LOCK_NB)) { echo "busy\n"; exit(0); }
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$S = ['at' => gmdate('c'), 'version' => defined('SYNC_VERSION') ? SYNC_VERSION : '', 'runs' => []];
try {
  $cfg = ai_cfg(); $slots = ai_slots($cfg, 'anthropic'); $key = $slots ? (string)(vault_get($slots[0]) ?? '') : '';
    $sys = "FX-STAGE: research\nYou are the market researcher of Dar's Template Factory: premium Excel workbooks sold worldwide (Etsy, Whop, Shopify) to people in one profession or business type. Study the field you are given as a buyer would, and as the best competitor would.\n"
        . 'Return ONE JSON object: {"profession":"the field, in English, as buyers name it","audience":"who pays for it (size of business, countries where it sells best)","buyers":["the buyer personas that matter, with their situation"],'
        . '"jobs":["every job-to-be-done the workbook must do for them, concrete"],"pays_for":["what they already pay for today (software, templates, services) and roughly how much"],"competitor_gaps":["what the usual templates for this field miss or get wrong"],"innovations":["3 to 6 things NO template for this field does today that its professionals would gladly pay for — what it does, which daily job it saves, why it is new (not a usual sheet)"],'
        . '"must_have_sheets":["the data sheets: name — what one row is"],"calculations":["the calculations that save them real time (formulas in words)"],"kpis":["the numbers the owner wants to see first"],"charts":["the charts and gauges the owner would read every week, and the filters he would pick (a person, a place, a project…)"],'
        . '"forms":["the one-record documents they print or send (invoice, receipt, work order, report…), if any"],"demo_world":"what realistic demo data looks like for this field","price_usd":29,"name_ideas":["product names, at most 40 characters"],"suite":[' . (fx_cfg()['parts'] ? 'at most ' . fx_cfg()['parts'] : 'as many as this field\'s work truly needs: one per distinct area (a small trade may need one, a complex practice several — never filler)') . ' files, none overlapping: {"focus":"the area (e.g. money & invoicing, clients & bookings, operations, staff, compliance & documents, reports)","covers":["the sheets this file holds: name — what one row is"]}]}'
        . "\nBe specific to this field (its own words, documents, rules of thumb). No generic business advice. English only.";
  $sys .= "\nKeep it tight: at most 8 items in any list, each item one line of at most 25 words; the whole answer under 1,800 words.";
  $sys .= "\n\nAnswer with one JSON object only — no words before or after it, no code fences.";
  $usr = 'The field: Classroom teacher. Research it now.';
  $base = ['model' => 'claude-sonnet-5-5', 'max_tokens' => 3000, 'system' => $sys, 'messages' => [['role' => 'user', 'content' => $usr]]];
  $variants = ['tight_no_upfront_thinking' => $base + ['thinking' => ['type' => 'between_tools']], 'tight_as_dar_sends' => $base, 'tight_fable_low' => ['model' => 'claude-fable-5-1'] + $base + ['output_config' => ['effort' => 'low']]];
  foreach ($variants as $nm => $body) {
    if ($key === '') break; $t = microtime(true);
    [$code, $res, $err] = array_pad(ai_http('POST', 'https://api.anthropic.com/v1/messages', ['Content-Type: application/json', 'x-api-key: ' . $key, 'anthropic-version: 2023-06-01'], json_encode($body), 90), 3, '');
    $j = json_decode((string)$res, true); $types = []; $tl = 0; $txt = '';
    foreach ((array)($j['content'] ?? []) as $b) { $types[] = (string)($b['type'] ?? '?'); if (($b['type'] ?? '') === 'text') { $tl += mb_strlen((string)($b['text'] ?? '')); $txt .= (string)($b['text'] ?? ''); } }
    $S['runs'][$nm] = ['code' => (int)$code, 'ms' => (int)round((microtime(true) - $t) * 1000), 'stop' => (string)($j['stop_reason'] ?? ''), 'blocks' => $types, 'text_len' => $tl,
      'json_ok' => is_array(json_decode(trim((string)preg_replace('/^```(?:json)?\s*|\s*```$/m', '', trim($txt))), true)), 'out' => $j['usage']['output_tokens'] ?? null,
      'thinking' => $j['usage']['output_tokens_details']['thinking_tokens'] ?? null, 'error' => mb_substr((string)($j['error']['message'] ?? $err), 0, 300)];
  }
} catch (Throwable $e) { $S['err'] = $e->getMessage() . ' @' . $e->getLine(); }
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(gzencode(json_encode($S, JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR), 9), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/antchk3.txt", base64_encode($iv . $tag . $ct)); echo "ok\n";
