<?php
// Read-only (2026-11-08): the live code of Dar's release package — the files of trj/release-files.txt, as they are on the site — for the
// session that builds the next release. Encrypted with that session's own key (given on the command line, never stored); the only file
// written is that encrypted copy (and copies older than two hours are removed). Run: php fxsrc.php <base64 key>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$site = '/home/u791571885/domains/dar.ink/public_html'; $here = __DIR__;
$list = is_file("$here/release-files.txt") ? file("$here/release-files.txt", FILE_IGNORE_NEW_LINES) : []; if (count($list) < 100) { echo "list?\n"; exit(1); }
foreach (glob("$site/fxtr/*/src.bin") ?: [] as $old) if (filemtime($old) < time() - 7200) @unlink($old);
$zp = tempnam(sys_get_temp_dir(), 'fxs'); $z = new ZipArchive(); if ($z->open($zp, ZipArchive::OVERWRITE) !== true) { echo "zip?\n"; exit(1); }
$miss = []; $n = 0;
foreach ($list as $f) { $f = trim($f); if ($f === '' || strpos($f, '..') !== false || $f[0] === '/') continue; $p = "$site/$f"; if (is_file($p)) { $z->addFile($p, $f); $n++; } else $miss[] = $f; }
$z->close(); $data = (string)file_get_contents($zp); @unlink($zp);
$tok = substr(hash('sha256', $K . 'fxsrc'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt($data, 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/src.bin", $iv . $tag . $ct);
file_put_contents("$pub/src.json", json_encode(['at' => gmdate('c'), 'files' => $n, 'missing' => array_slice($miss, 0, 50), 'zip_sha256' => hash('sha256', $data)], JSON_UNESCAPED_SLASHES));
echo "ok $n files\n";
