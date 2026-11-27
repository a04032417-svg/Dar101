<?php
// Installs an encrypted package on the host. Run by a one-off scheduled command (the host limits a command to 255 characters):
//   php deploy.php <hex-key> [package-url] [site-folder]
// then runs one scheduler pass and prints the owner's one-time setup code while no owner exists.
// app/ is replaced as a whole (the previous one is kept in _deploy/), public files are copied over public_html,
// members' media and the private data folder are never touched.
declare(strict_types=1);
[, $hex, $url, $site] = $argv + [null, null, null, null];
$url = $url ?: 'https://raw.githubusercontent.com/a04032417-svg/Dar101/jaww/jaww.pkg'; $site = $site ?: getenv('HOME') . '/domains/alpine-magenta-cod-14.hostingersite.com';
if (!$url || !preg_match('/^[a-f0-9]{64}$/', (string)$hex) || !$site || !is_dir($site)) { fwrite(STDERR, "usage: deploy.php <key> [url] [site]\n"); exit(1); }
$c = curl_init($url); curl_setopt_array($c, [CURLOPT_RETURNTRANSFER => true, CURLOPT_FOLLOWLOCATION => true, CURLOPT_TIMEOUT => 120]); $blob = curl_exec($c); $st = curl_getinfo($c, CURLINFO_HTTP_CODE); curl_close($c);
if (($st !== 200 && !str_starts_with($url, 'file://')) || !is_string($blob) || strlen($blob) < 40) { fwrite(STDERR, "download failed: HTTP $st\n"); exit(1); }
$data = openssl_decrypt(substr($blob, 28), 'aes-256-gcm', hex2bin($hex), OPENSSL_RAW_DATA, substr($blob, 0, 12), substr($blob, 12, 16), 'jaww-deploy');
if ($data === false) { fwrite(STDERR, "the package did not decrypt (wrong key or damaged file)\n"); exit(1); }
$ts = gmdate('Ymd-His'); $work = "$site/_deploy/$ts"; @mkdir($work, 0700, true); @chmod("$site/_deploy", 0700);
file_put_contents("$work/pkg.tar.gz", $data); (new PharData("$work/pkg.tar.gz"))->extractTo("$work/x", null, true);
if (!is_file("$work/x/app/boot.php") || !is_file("$work/x/public/index.php")) { fwrite(STDERR, "package incomplete\n"); exit(1); }
$copy = function (string $from, string $to) use (&$copy): int { $n = 0; @mkdir($to, 0755, true);
    foreach (scandir($from) as $e) { if ($e === '.' || $e === '..') continue; $a = "$from/$e"; $b = "$to/$e"; if (is_dir($a)) $n += $copy($a, $b); else { copy($a, $b) || throw new RuntimeException("cannot write $b"); chmod($b, 0644); $n++; } } return $n; };
// full backup of what is being replaced: the old app, and every file of public_html except members' media (m/) — kept 14 days
$pub = "$site/public_html"; $bak = new PharData("$work/public_html.prev.tar"); $nb = 0;
foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator($pub, FilesystemIterator::SKIP_DOTS)) as $f) { $rel = substr($f->getPathname(), strlen($pub) + 1); if (str_starts_with($rel, 'm/') || str_starts_with($rel, 'pm/')) continue; $bak->addFile($f->getPathname(), $rel); $nb++; }
if (is_file("$site/private/config.php")) copy("$site/private/config.php", "$work/config.php.prev");
echo "backup: $nb files of public_html + app -> _deploy/$ts\n";
if (is_dir("$site/app")) rename("$site/app", "$work/app.prev"); rename("$work/x/app", "$site/app");
if (is_file("$pub/default.php")) rename("$pub/default.php", "$work/default.php.prev");
if (is_dir("$pub/assets")) rename("$pub/assets", "$work/assets.prev");
foreach (["web.php", "admin.php", "api.php"] as $old) if (is_file("$pub/$old")) rename("$pub/$old", "$work/$old.prev");
$n = $copy("$work/x/public", $pub);
if (!is_dir("$site/private")) mkdir("$site/private", 0700, true); @chmod("$site/private", 0700);
foreach (glob("$site/_deploy/*", GLOB_ONLYDIR) as $d) if (basename($d) < gmdate('Ymd-His', time() - 14 * 86400)) { exec_rm($d); }
function exec_rm(string $d): void { foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator($d, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST) as $f) $f->isDir() ? rmdir($f->getPathname()) : unlink($f->getPathname()); rmdir($d); }
@unlink("$work/pkg.tar.gz"); exec_rm("$work/x");
echo json_encode(['installed' => $ts, 'public_files' => $n, 'php' => PHP_VERSION, 'pdo_sqlite' => extension_loaded('pdo_sqlite'), 'gd' => extension_loaded('gd'), 'zip' => class_exists('ZipArchive')]), "\n";
if (dirname(__FILE__) === getenv('HOME')) @unlink(__FILE__);
// first run of the new code, in this same process (the host does not allow starting other programs)
$argv = [$site . '/app/cli.php', 'cron']; ob_start(); require $site . '/app/cli.php'; $o = ob_get_clean(); echo 'cron ', trim($o), "\n"; echo 'setup ', setup_code() ?? 'owner exists', "\n";
