<?php
// Installs an encrypted package on the host. Run by a one-off scheduled command:
//   php deploy.php <package-url> <hex-key> <site-folder>
// app/ is replaced as a whole (the previous one is kept in _deploy/), public files are copied over public_html,
// members' media and the private data folder are never touched.
declare(strict_types=1);
[, $url, $hex, $site] = $argv + [null, null, null, null];
if (!$url || !preg_match('/^[a-f0-9]{64}$/', (string)$hex) || !$site || !is_dir($site)) { fwrite(STDERR, "usage: deploy.php <url> <key> <site>\n"); exit(1); }
$c = curl_init($url); curl_setopt_array($c, [CURLOPT_RETURNTRANSFER => true, CURLOPT_FOLLOWLOCATION => true, CURLOPT_TIMEOUT => 120]); $blob = curl_exec($c); $st = curl_getinfo($c, CURLINFO_HTTP_CODE); curl_close($c);
if (($st !== 200 && !str_starts_with($url, 'file://')) || !is_string($blob) || strlen($blob) < 40) { fwrite(STDERR, "download failed: HTTP $st\n"); exit(1); }
$data = openssl_decrypt(substr($blob, 28), 'aes-256-gcm', hex2bin($hex), OPENSSL_RAW_DATA, substr($blob, 0, 12), substr($blob, 12, 16), 'jaww-deploy');
if ($data === false) { fwrite(STDERR, "the package did not decrypt (wrong key or damaged file)\n"); exit(1); }
$ts = gmdate('Ymd-His'); $work = "$site/_deploy/$ts"; @mkdir($work, 0700, true); @chmod("$site/_deploy", 0700);
file_put_contents("$work/pkg.tar.gz", $data); (new PharData("$work/pkg.tar.gz"))->extractTo("$work/x", null, true);
if (!is_file("$work/x/app/boot.php") || !is_file("$work/x/public/index.php")) { fwrite(STDERR, "package incomplete\n"); exit(1); }
$copy = function (string $from, string $to) use (&$copy): int { $n = 0; @mkdir($to, 0755, true);
    foreach (scandir($from) as $e) { if ($e === '.' || $e === '..') continue; $a = "$from/$e"; $b = "$to/$e"; if (is_dir($a)) $n += $copy($a, $b); else { copy($a, $b) || throw new RuntimeException("cannot write $b"); chmod($b, 0644); $n++; } } return $n; };
if (is_dir("$site/app")) rename("$site/app", "$work/app.prev"); rename("$work/x/app", "$site/app");
$pub = "$site/public_html"; if (is_file("$pub/default.php")) rename("$pub/default.php", "$work/default.php.prev");
if (is_dir("$pub/assets")) rename("$pub/assets", "$work/assets.prev");
$n = $copy("$work/x/public", $pub);
if (!is_dir("$site/private")) mkdir("$site/private", 0700, true); @chmod("$site/private", 0700);
foreach (glob("$site/_deploy/*", GLOB_ONLYDIR) as $d) if (basename($d) < gmdate('Ymd-His', time() - 14 * 86400)) { exec_rm($d); }
function exec_rm(string $d): void { foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator($d, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST) as $f) $f->isDir() ? rmdir($f->getPathname()) : unlink($f->getPathname()); rmdir($d); }
@unlink("$work/pkg.tar.gz"); exec_rm("$work/x");
echo json_encode(['installed' => $ts, 'public_files' => $n, 'php' => PHP_VERSION, 'pdo_sqlite' => extension_loaded('pdo_sqlite'), 'gd' => extension_loaded('gd'), 'zip' => class_exists('ZipArchive')]), "\n";
