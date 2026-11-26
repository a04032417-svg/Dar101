<?php
// Copies the AI provider keys from Dar into this app's own vault, so the app keeps them even after they are removed from Dar.
// Dar is only read: its database is opened read-only and nothing of Dar is changed. Keys are never printed — only provider
// names, how many keys each has, and whether a test call answered.
// Run on the host: php copy-dar-keys.php [dar-site-folder] [this-app-site-folder]
declare(strict_types=1);
$home = getenv('HOME');
$dar = $argv[1] ?? "$home/domains/dar.ink"; $site = $argv[2] ?? "$home/domains/alpine-magenta-cod-14.hostingersite.com";
$dataDir = null; foreach (["$dar/dar-data", "$dar/public_html/.dar/data"] as $d) if (is_file("$d/dar.sqlite") && is_file("$d/vault.key")) { $dataDir = $d; break; }
if (!$dataDir) { fwrite(STDERR, "Dar data not found\n"); exit(1); }
$dk = base64_decode(trim((string)file_get_contents("$dataDir/vault.key")), true); if ($dk === false || strlen($dk) !== 32) { fwrite(STDERR, "Dar vault key unreadable\n"); exit(1); }
$ro = new PDO('sqlite:' . "$dataDir/dar.sqlite", null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC, PDO::SQLITE_ATTR_OPEN_FLAGS => PDO::SQLITE_OPEN_READONLY]);
$cfgRow = $ro->query("SELECT v FROM meta WHERE k='ai_cfg'")->fetch(); $cfg = $cfgRow ? (json_decode((string)$cfgRow['v'], true) ?: []) : [];
// Dar's provider table, read from its own source so new providers there come along
$src = (string)@file_get_contents("$dar/public_html/dar-ai.php"); $presets = [];
if (preg_match('/const AI_PRESETS = (\[.*?\n\]);/s', $src, $m)) { try { $presets = eval('return ' . $m[1] . ';'); } catch (Throwable $e) { $presets = []; } }
if (!$presets) $presets = ['anthropic' => ['Anthropic (Claude)', 'https://api.anthropic.com/v1', 'claude-haiku-4-5-20251001', 'claude-sonnet-5-5', 'anthropic'], 'groq' => ['Groq', 'https://api.groq.com/openai/v1', 'openai/gpt-oss-20b', 'openai/gpt-oss-120b', 'openai'], 'gemini' => ['Google Gemini', 'https://generativelanguage.googleapis.com/v1beta', 'gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini'], 'openrouter' => ['OpenRouter', 'https://openrouter.ai/api/v1', 'openrouter/free', 'google/gemma-4-31b-it:free', 'openai'], 'cerebras' => ['Cerebras', 'https://api.cerebras.ai/v1', 'gpt-oss-120b', 'gpt-oss-120b', 'openai'], 'mistral' => ['Mistral', 'https://api.mistral.ai/v1', 'mistral-small-latest', 'mistral-medium-latest', 'openai'], 'deepseek' => ['DeepSeek', 'https://api.deepseek.com/v1', 'deepseek-chat', 'deepseek-chat', 'openai'], 'huggingface' => ['Hugging Face', 'https://router.huggingface.co/v1', 'openai/gpt-oss-120b:fastest', 'openai/gpt-oss-120b:fastest', 'openai']];
$order = array_values(array_unique(array_merge(array_filter((array)($cfg['order'] ?? []), 'is_string'), array_keys($presets))));
$keys = [];
foreach ($ro->query("SELECT name, enc FROM vault WHERE name LIKE 'ai:%' ORDER BY name") as $r) {
    if (!preg_match('/^ai:([a-z0-9_-]+):/', $r['name'], $mm)) continue; $b = base64_decode((string)$r['enc'], true); if ($b === false || strlen($b) < 29) continue;
    $v = openssl_decrypt(substr($b, 28), 'aes-256-gcm', $dk, OPENSSL_RAW_DATA, substr($b, 0, 12), substr($b, 12, 16), 'dar:' . $r['name']); if ($v === false || $v === '') continue;
    $keys[$mm[1]][] = ['name' => $r['name'], 'key' => $v];
}
$ro = null;

// this app, in the same process
$root = $site; $c2 = is_file("$root/private/config.php") ? (array)require "$root/private/config.php" : [];
define('APP_PUBLIC', $c2['public'] ?? "$root/public_html"); define('APP_DATA', $c2['data'] ?? "$root/private"); define('APP_ENV', 'prod');
require "$root/app/boot.php";
$have = (array)setting('ai.providers', []); $byId = []; foreach ($have as $p) if (!empty($p['id'])) $byId[$p['id']] = $p;
$report = []; $added = 0;
foreach ($order as $id) {
    if (empty($keys[$id])) continue; $pr = $presets[$id] ?? null; $o = (array)($cfg['providers'][$id] ?? []);
    $groups = [];
    foreach ($keys[$id] as $k) { $base = $id === 'cloudflare' ? (string)($cfg['kbase'][$k['name']] ?? '') : (string)(($o['base'] ?? '') ?: ($pr[1] ?? '')); $groups[$base][] = $k; }
    $n = 0;
    foreach ($groups as $base => $ks) {
        $pid = $n ? substr($id, 0, 20) . ($n + 1) : $id; $n++;
        $model = (string)(($o['economy'] ?? '') ?: ($pr[2] ?? '')); $strong = (string)(($o['deep'] ?? '') ?: (($o['standard'] ?? '') ?: ($pr[3] ?? $model)));
        // every key is kept here, whatever Dar does later; a provider without an address or a model waits switched off
        foreach ($ks as $k) vault_put('ai.' . $pid . '.' . substr(sha1($k['key']), 0, 8), $k['key']);
        if (!preg_match('#^https://[\w.\-/:]{4,200}$#', $base)) { $report[] = ['provider' => $pid, 'keys' => count($ks), 'copied' => true, 'listed' => false, 'why' => 'key kept; needs its address in the admin panel']; continue; }
        $byId[$pid] = ['id' => $pid, 'name' => (string)($pr[0] ?? $id), 'base' => $base, 'model' => $model, 'strong' => $strong ?: $model, 'type' => in_array($pr[4] ?? 'openai', ['openai', 'anthropic', 'gemini'], true) ? ($pr[4] ?? 'openai') : 'openai', 'off' => $model === '', 'open' => false] + ($byId[$pid] ?? []);
        $report[] = ['provider' => $pid, 'keys' => count($ks), 'copied' => true, 'listed' => true] + ($model === '' ? ['why' => 'switched off until a model is chosen in the admin panel'] : []); $added++;
    }
}
// Dar's order first, then anything the owner already added here
$list = []; foreach ($report as $x) if (!empty($x['listed']) && isset($byId[$x['provider']])) { $list[] = $byId[$x['provider']]; unset($byId[$x['provider']]); } foreach ($byId as $p) $list[] = $p;
setting_set('ai.providers', $list); audit(null, 'ai.copied_from_dar', '', ['providers' => $added]);
// a short live check of each copied provider (answers "ok"); failures only mark that provider, the others still serve
foreach ($report as &$x) if (!empty($x['listed']) && empty($x['why'])) { $t = integration_test('ai.' . $x['provider'], ['email' => '']); $x['test'] = $t['ok'] ? 'answered' : 'no answer: ' . substr((string)$t['note'], 0, 80); }
echo json_encode(['dar_providers_with_keys' => count($keys), 'copied' => $added, 'providers' => $report], JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT), "\n";
if (str_contains(__FILE__, '/ck.php')) @unlink(__FILE__);
