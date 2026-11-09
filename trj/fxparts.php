<?php
// Read-only (2026-11-09): lists the photographer suites' parts (index entries, files in each part's folder, small notes) and copies
// their spec.json files, gzip + AES-256-GCM with the session's own key (never stored), to fxtr/<token>/fxparts.txt. Nothing in Dar changes.
// Run: php fxparts.php <base64 key>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$site = '/home/u791571885/domains/dar.ink/public_html'; $out = "$site/.dar/fx/out";
$cut = function ($v) use (&$cut) { if (is_string($v)) return mb_substr($v, 0, 400); if (is_array($v)) return array_map($cut, $v); return $v; };
$S = ['dirs' => [], 'index' => [], 'specs' => [], 'notes' => []];
$ix = json_decode((string)@file_get_contents("$out/index.json"), true) ?: [];
foreach ((array)($ix['suites'] ?? []) as $su) if (stripos(json_encode($su), 'photographer') !== false) $S['index'][] = $cut($su);
foreach (glob("$out/*photographer*", GLOB_ONLYDIR) ?? [] as $d) {
  $id = basename($d); $S['dirs'][$id] = [];
  foreach (scandir($d) as $f) { if ($f === '.' || $f === '..') continue; $p = "$d/$f"; $S['dirs'][$id][$f] = is_file($p) ? filesize($p) : 'dir';
    if (is_file($p) && $f === 'spec.json') $S['specs'][$id] = file_get_contents($p);
    elseif (is_file($p) && filesize($p) < 20000 && preg_match('/\.(json|txt|md|log)$/', $f)) $S['notes'][$id][$f] = mb_substr((string)file_get_contents($p), 0, 3000); }
}
$S['pubkey_pem'] = $ix['pubkey_pem'] ?? '';
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(gzencode(json_encode($S, JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR | JSON_INVALID_UTF8_SUBSTITUTE), 9), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/fxparts.txt", base64_encode($iv . $tag . $ct)); echo "ok " . count($S['dirs']) . ' ' . count($S['specs']) . "\n";
