<?php
// After 3.34.19: the upload page (not in the package) takes the new build's token, its fingerprint joins the manifest, the verified
// copy is made again, the install's leftovers go, and the self-check's file layer is read back. Usage: php pf.php
if (PHP_SAPI !== 'cli') exit;
$H = '/home/u791571885'; $D = "$H/domains/dar.ink/public_html"; chdir($D); require $D . '/dar-sync.php';
$out = [];
$f = "$D/upload/index.html"; $s = (string)file_get_contents($f); $n = str_replace('3.34.18-825a3941', '3.34.19-7e87f443', $s); if ($n !== $s) { file_put_contents($f, $n); $out['upload'] = 'token'; }
$m = json_decode((string)file_get_contents("$D/lib/manifest.json"), true);
$m['files']['upload/index.html'] = sha1(doc_norm('upload/index.html', $n)); file_put_contents("$D/lib/manifest.json", json_encode($m, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
$out['golden'] = doc_golden_make($m);
@unlink("$H/p.php"); foreach (['report.json', 'lock', 'pkg.zip', 'site.zip'] as $x) @unlink("$H/xfer-dp/$x"); @rmdir("$H/xfer-dp");
$gz = "$H/domains/wa.dar.ink/public_html/dar-wa-gateway-1.2.0.zip"; $out['gw_zip_left'] = is_file($gz);
$out['files'] = doc_chk_files(true); $out['version'] = SYNC_VERSION;
$out['removed_kept_at'] = is_dir("$H/dar-removed-20261125") ? array_values(array_diff(scandir("$H/dar-removed-20261125"), ['.', '..'])) : [];
echo json_encode($out, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), "\n";
