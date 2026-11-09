<?php
// Read-only (2026-11-09): copies the ready specs of one suite (spec.json of each part) and Dar's public key, gzip + AES-256-GCM
// with the session's own key (never stored), to fxtr/<token>/fxspec.txt. Nothing in Dar changes. Run: php fxspec.php <base64 key> <id,id,...>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$site = '/home/u791571885/domains/dar.ink/public_html'; $ids = array_filter(explode(',', (string)($argv[2] ?? '')), fn($i) => preg_match('/^[a-z0-9-]{3,80}$/', $i));
$S = ['specs' => [], 'index_part' => []];
foreach ($ids as $id) { $p = "$site/.dar/fx/out/$id/spec.json"; if (is_file($p)) $S['specs'][$id] = file_get_contents($p); }
$ix = json_decode((string)@file_get_contents("$site/.dar/fx/out/index.json"), true); $S['pubkey_pem'] = $ix['pubkey_pem'] ?? '';
foreach ((array)($ix['suites'] ?? []) as $su) foreach ($su['parts'] as $pt) if (in_array($pt['id'], $ids, true)) $S['index_part'][$pt['id']] = $pt + ['suite' => $su['key']];
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(gzencode(json_encode($S, JSON_UNESCAPED_UNICODE), 9), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/fxspec.txt", base64_encode($iv . $tag . $ct)); echo "ok " . count($S['specs']) . "\n";
