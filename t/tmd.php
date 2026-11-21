<?php
// Read-only: hashes of the live files the platform preview touches, and what is in the preview backup folder.
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$d = '/home/u791571885/domains/dar.ink/public_html';
$o = [];
foreach (['dar-preview.php', 'dar-sync.php', 'assets/edition.js', 'assets/ui.js', 'assets/core.js', 'assets/pv-flag.js', 'developer/index.html'] as $f) $o[$f] = is_file("$d/$f") ? md5_file("$d/$f") : null;
$o['pv-backup'] = is_dir('/home/u791571885/pv-backup') ? scandir('/home/u791571885/pv-backup') : null;
$o['has_pv_login_fn'] = strpos((string)file_get_contents("$d/dar-preview.php"), 'function pv_login(') !== false;
preg_match("/const SYNC_VERSION = '([^']+)'/", (string)file_get_contents("$d/dar-sync.php"), $m); $o['version'] = $m[1] ?? null;
$o['ini'] = ['opcache.validate_timestamps' => ini_get('opcache.validate_timestamps'), 'opcache.revalidate_freq' => ini_get('opcache.revalidate_freq')];
echo json_encode($o, JSON_UNESCAPED_SLASHES), "\n";
