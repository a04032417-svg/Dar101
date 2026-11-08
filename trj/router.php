<?php
// the host's rewrite rules the installer's canary needs when a copy of the site is served by php -S (it reads no .htaccess);
// usage: DAR_DATA_DIR=<data> DAR_SELF_URL=http://127.0.0.1:8099 php -S 127.0.0.1:8099 -t <site> router.php   (ROOT below = <site>)
$u = (string)parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH); $root = getenv('DAR_SITE_ROOT') ?: '/home/claude/site/live';
if (preg_match('#^/assets/v/[A-Za-z0-9._-]{1,60}/(.+)$#', $u, $m)) { $f = $root . '/assets/' . $m[1]; if (!is_file($f)) { http_response_code(404); exit; }
    $t = ['js' => 'application/javascript', 'mjs' => 'application/javascript', 'css' => 'text/css', 'json' => 'application/json', 'png' => 'image/png', 'svg' => 'image/svg+xml', 'webmanifest' => 'application/manifest+json'][strtolower(pathinfo($f, PATHINFO_EXTENSION))] ?? 'application/octet-stream';
    header('Content-Type: ' . $t); readfile($f); exit; }
if ($u === '/sitemap.xml') { $_GET['sitemap'] = 1; require $root . '/dar-sync.php'; exit; }
if ($u === '/robots.txt') { $_GET['robots'] = 1; require $root . '/dar-sync.php'; exit; }
return false;
