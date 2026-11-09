<?php
// Read-only (2026-11-09): where Dar keeps the unfinished parts (p3, p4, p5) of the photographer suite: file tree under .dar/fx,
// every file named like the suite, and the source lines that set the stages. Output: gzip + AES-256-GCM with the session's own key
// (never stored) to fxtr/<token>/fxparts2.txt. Nothing in Dar changes. Run: php fxparts2.php <base64 key>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$site = '/home/u791571885/domains/dar.ink/public_html'; $S = ['tree' => [], 'named' => [], 'files' => [], 'src' => []];
$walk = function ($root, $depth, $cb) use (&$walk) { if ($depth < 0 || !is_dir($root)) return; foreach (scandir($root) as $f) { if ($f === '.' || $f === '..') continue; $p = "$root/$f"; $cb($p, is_dir($p)); if (is_dir($p)) $walk($p, $depth - 1, $cb); } };
$n = 0; $walk("$site/.dar/fx", 3, function ($p, $d) use (&$S, &$n) { if (++$n > 500) return; $S['tree'][] = substr($p, strlen("$site/.dar/fx/")) . ($d ? '/' : ' ' . filesize($p)); });
$walk("$site/.dar", 5, function ($p, $d) use (&$S) { if (stripos(basename($p), '2348-photographer') !== false && count($S['named']) < 80) { $S['named'][] = substr($p, strlen("$site/")) . ($d ? '/' : ' ' . filesize($p));
  if (!$d && filesize($p) < 400000 && preg_match('/\.(json|txt|md)$/', $p)) $S['files'][substr($p, strlen("$site/"))] = file_get_contents($p); } });
foreach (glob("$site/*fx*.php") ?: [] as $f) { $L = @file($f, FILE_IGNORE_NEW_LINES) ?: []; $hits = [];
  foreach ($L as $i => $l) if (preg_match("/'architect'|'critic'|'dropped'|stage'\s*=>|fx_part_path|fx_work_dir|function fx_(drop|step|next|part)/", $l)) $hits[] = ($i + 1) . ': ' . mb_substr(trim($l), 0, 220);
  $S['src'][basename($f)] = ['lines' => count($L), 'hits' => array_slice($hits, 0, 60)]; }
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(gzencode(json_encode($S, JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR | JSON_INVALID_UTF8_SUBSTITUTE), 9), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/fxparts2.txt", base64_encode($iv . $tag . $ct)); echo "ok " . count($S['tree']) . ' ' . count($S['named']) . "\n";
