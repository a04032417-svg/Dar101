<?php
// One-off probe: which image models can draw sticker art for free (Cloudflare Workers AI with the stored key, Gemini image,
// Pollinations). Saves the pictures to /_t/ for a visual check (removed later). Keys are never printed.
declare(strict_types=1);
$site = getenv('HOME') . '/domains/alpine-magenta-cod-14.hostingersite.com';
define('APP_PUBLIC', "$site/public_html"); define('APP_DATA', "$site/private"); define('APP_ENV', 'prod');
require "$site/app/boot.php"; @set_time_limit(200);
@mkdir(APP_PUBLIC . '/_t', 0755);
$P = 'A cute laughing little child, kawaii die-cut sticker, bold clean dark outline, vibrant flat colors with soft cel shading, big shiny eyes, centered, full body, isolated on a plain solid light gray background, no text, professional vector illustration';
$prov = []; foreach ((array)setting('ai.providers', []) as $p) $prov[$p['id']] = $p;
echo 'providers: ', implode(',', array_map(fn($p) => $p['id'] . '(' . ($p['type'] ?? 'openai') . ')', $prov)), "\n";
function save_img(string $name, string $bytes): string { $f = APP_PUBLIC . "/_t/$name"; file_put_contents($f, $bytes); $sz = @getimagesizefromstring($bytes); return strlen($bytes) . ' bytes ' . ($sz ? $sz[0] . 'x' . $sz[1] . ' ' . $sz['mime'] : 'not an image'); }
function key_of(string $pid): string { $n = vault_names("ai.$pid."); return $n ? (string)vault_get($n[0]) : ''; }
// Cloudflare Workers AI
if (isset($prov['cloudflare'])) {
    $base = preg_replace('#/ai/v1/?$#', '', rtrim($prov['cloudflare']['base'], '/')); $k = key_of('cloudflare');
    foreach (['@cf/black-forest-labs/flux-1-schnell' => ['prompt' => $P, 'steps' => 8], '@cf/bytedance/stable-diffusion-xl-lightning' => ['prompt' => $P, 'num_steps' => 8, 'width' => 768, 'height' => 768], '@cf/leonardo/lucid-origin' => ['prompt' => $P, 'width' => 768, 'height' => 768], '@cf/leonardo/phoenix-1.0' => ['prompt' => $P, 'width' => 768, 'height' => 768]] as $m => $body) {
        $t0 = microtime(true); $r = http_call('POST', "$base/ai/run/$m", ['authorization: Bearer ' . $k, 'content-type: application/json'], $body, 90); $ms = (int)((microtime(true) - $t0) * 1000);
        $ct = $r['headers']['content-type'] ?? ''; $img = '';
        if (str_starts_with($ct, 'image/')) $img = $r['body']; else { $j = jdec($r['body'], []); $b64 = $j['result']['image'] ?? ''; if ($b64) $img = base64_decode($b64); }
        $nm = 'cf-' . preg_replace('/[^a-z0-9]+/', '-', strtolower(basename($m))) . '.' . (str_contains($ct, 'png') ? 'png' : 'jpg');
        echo "cloudflare $m: status {$r['status']} {$ms}ms ", $img ? save_img($nm, $img) . " → /_t/$nm" : substr(preg_replace('/\s+/', ' ', $r['body']), 0, 160), "\n";
    }
}
// Gemini image
if (isset($prov['gemini'])) { $k = key_of('gemini');
    foreach (['gemini-2.5-flash-image', 'gemini-2.0-flash-preview-image-generation'] as $m) {
        $t0 = microtime(true); $r = http_call('POST', "https://generativelanguage.googleapis.com/v1beta/models/$m:generateContent", ['x-goog-api-key: ' . $k, 'content-type: application/json'], ['contents' => [['parts' => [['text' => $P]]]], 'generationConfig' => ['responseModalities' => ['TEXT', 'IMAGE']]], 90); $ms = (int)((microtime(true) - $t0) * 1000);
        $img = ''; foreach ((jdec($r['body'], [])['candidates'][0]['content']['parts'] ?? []) as $pt) if (!empty($pt['inlineData']['data'])) $img = base64_decode($pt['inlineData']['data']);
        echo "gemini $m: status {$r['status']} {$ms}ms ", $img ? save_img("gm-$m.png", $img) . " → /_t/gm-$m.png" : substr(preg_replace('/\s+/', ' ', $r['body']), 0, 160), "\n";
    } }
// Pollinations (no key)
$t0 = microtime(true); $r = http_call('GET', 'https://image.pollinations.ai/prompt/' . rawurlencode($P) . '?width=768&height=768&model=flux&nologo=true&seed=7', [], null, 90); $ms = (int)((microtime(true) - $t0) * 1000);
echo "pollinations flux: status {$r['status']} {$ms}ms ", str_starts_with($r['headers']['content-type'] ?? '', 'image/') ? save_img('po-flux.jpg', $r['body']) . ' → /_t/po-flux.jpg' : substr(preg_replace('/\s+/', ' ', $r['body']), 0, 160), "\n";
@unlink(__FILE__);
