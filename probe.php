<?php
// Host capability probe for the Jaww app. Prints facts only; writes nothing outside a temp file it removes.
$o = ['php' => PHP_VERSION, 'sapi' => PHP_SAPI, 'user' => get_current_user(), 'home' => getenv('HOME') ?: '', 'cwd' => getcwd()];
foreach (['pdo_sqlite', 'sqlite3', 'sodium', 'gd', 'curl', 'zip', 'mbstring', 'intl', 'fileinfo', 'exif', 'openssl', 'opcache'] as $e) $o['ext'][$e] = extension_loaded($e);
$o['webp'] = function_exists('imagewebp'); $o['sqlite'] = class_exists('SQLite3') ? SQLite3::version()['versionString'] : null;
try { $d = new PDO('sqlite::memory:'); $d->exec('CREATE VIRTUAL TABLE t USING fts5(a, tokenize="unicode61 remove_diacritics 2")'); $o['fts5'] = true; } catch (Throwable $e) { $o['fts5'] = $e->getMessage(); }
$o['mail'] = function_exists('mail'); $o['limits'] = ['memory' => ini_get('memory_limit'), 'upload' => ini_get('upload_max_filesize'), 'post' => ini_get('post_max_size'), 'time' => ini_get('max_execution_time')];
$o['p256'] = (bool)@openssl_pkey_new(['curve_name' => 'prime256v1', 'private_key_type' => OPENSSL_KEYTYPE_EC]);
foreach (['https://itunes.apple.com/search?term=fairuz&media=music&limit=1', 'https://photon.komoot.io/api/?q=riyadh&limit=1', 'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=jNQXAC9IVRw&format=json', 'https://api.groq.com/openai/v1/models'] as $u) { $c = curl_init($u); curl_setopt_array($c, [CURLOPT_RETURNTRANSFER => 1, CURLOPT_TIMEOUT => 10, CURLOPT_USERAGENT => 'JawwProbe/1.0']); $b = curl_exec($c); $o['net'][parse_url($u, PHP_URL_HOST)] = curl_getinfo($c, CURLINFO_HTTP_CODE) . ' ' . strlen((string)$b); curl_close($c); }
$site = getenv('HOME') . '/domains/' . ($argv[1] ?? ''); $o['site_dir'] = is_dir($site) ? scandir($site) : 'missing';
$o['public_html'] = is_dir("$site/public_html") ? array_slice(scandir("$site/public_html"), 0, 20) : 'missing';
$o['php_bins'] = array_values(array_filter(glob('/opt/alt/php8*/usr/bin/php') ?: []));
$o['free_mb'] = (int)(disk_free_space(getenv('HOME')) / 1048576);
echo json_encode($o, JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT), "\n";
