<?php
// Read-only survey of the live Dar install: runtime, layout, data locations, Telegram and templates-factory references.
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$H = '/home/u791571885'; $D = "$H/domains/dar.ink/public_html";
$o = ['php' => PHP_VERSION, 'ext' => array_values(array_filter(['zip', 'openssl', 'phar', 'sqlite3', 'pdo_sqlite', 'zlib', 'sodium'], 'extension_loaded')),
  'mem' => ini_get('memory_limit'), 'free_mb' => (int)(disk_free_space($H) / 1048576)];
function du($p, &$n) { $s = 0; if (is_link($p)) return 0; if (is_file($p)) { $n++; return filesize($p); }
  foreach (@scandir($p) ?: [] as $f) { if ($f === '.' || $f === '..') continue; $s += du("$p/$f", $n); } return $s; }
$top = [];
foreach (scandir($D) as $f) { if ($f === '.' || $f === '..') continue; $n = 0; $s = du("$D/$f", $n); $top[] = [$f, is_dir("$D/$f") ? 'd' : 'f', round($s / 1048576, 2), $n]; }
usort($top, fn($a, $b) => $b[2] <=> $a[2]); $o['top'] = $top;
$home = [];
foreach (scandir($H) as $f) { if ($f === '.' || $f === '..' || $f === 'domains') continue; $n = 0; $s = du("$H/$f", $n); $home[] = [$f, round($s / 1048576, 1), $n]; }
$o['home'] = $home;
$src = @file_get_contents("$D/dar-sync.php") ?: '';
preg_match_all('/[^\n]{0,60}(sqlite:|\.sqlite|\.db[\'"]|DAR_DATA|data_dir)[^\n]{0,80}/', $src, $m); $o['db_lines'] = array_slice(array_map('trim', $m[0]), 0, 8);
$o['version'] = (preg_match('/3\.\d+\.\d+/', @file_get_contents("$D/assets/version.js") ?: (@file_get_contents("$D/app/index.html") ?: ''), $v) ? $v[0] : null);
$tg = []; $fx = []; $nfiles = 0; $lines = 0;
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($D, FilesystemIterator::SKIP_DOTS));
foreach ($it as $f) {
  $p = $f->getPathname(); $r = substr($p, strlen($D) + 1);
  if (!preg_match('/\.(php|js|mjs|html|json|css|txt|md)$/', $p) || $f->getSize() > 3000000) continue;
  if (preg_match('#^(data|uploads|upload|backups?|logs?|cache|tmp)/#', $r)) continue;
  $c = @file_get_contents($p); if ($c === false) continue; $nfiles++; $lines += substr_count($c, "\n");
  $a = preg_match_all('/telegram|tgqr|dar-tg|\btg_/i', $c); if ($a) $tg[$r] = $a;
  $b = preg_match_all('/dar-fx|\bfx_[a-z]|fxd|templates factory|مصنع القوالب/i', $c); if ($b) $fx[$r] = $b;
}
arsort($tg); arsort($fx);
$o['code_files'] = $nfiles; $o['code_lines'] = $lines; $o['tg'] = $tg; $o['fx'] = $fx;
echo json_encode($o, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), "\n";
