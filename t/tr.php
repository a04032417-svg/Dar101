<?php
// read-only check of the free-trial settings and the site's health (run once from the host's cron, CLI only)
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
chdir('/home/u791571885/domains/dar.ink/public_html');
require 'dar-sync.php';
$P = platform_rec();
$o = ['checkout_first' => $P->billing->checkout_first ?? 'unset', 'card_ready' => function_exists('trial_card_ready') ? trial_card_ready() : null,
    'cf_on' => function_exists('trial_checkout_first_on') ? trial_checkout_first_on() : null, 'max' => defined('TRIAL_MAX_DAYS') ? TRIAL_MAX_DAYS : null,
    'renew_auto' => function_exists('bill_cfg') ? (bill_cfg($P)['renew']['auto'] ?? null) : null];
foreach (bill_platform_rows('plans') as $p) $o['plans'][] = [$p->code ?? '', $p->audience ?? '', $p->trial_days ?? null, $p->trial_days_month ?? null, $p->trial_days_year ?? null, $p->active ?? null, $p->base_price ?? null];
foreach (bill_platform_rows('trial_plans') as $t) $o['tp'][] = [$t->code ?? '', $t->audience ?? '', $t->days ?? null, $t->start ?? null, $t->active ?? null, !empty($t->card_required)];
$o['cron_cli_at'] = date('c', (int)meta_get('cron_cli_at'));
foreach (['https://dar.ink/', 'https://dar.ink/app/', 'https://dar.ink/dar-sync.php?ping=1'] as $u) {
    $ch = curl_init($u); curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 20, CURLOPT_FOLLOWLOCATION => true, CURLOPT_USERAGENT => 'Mozilla/5.0 (DarCheck)']);
    $b = curl_exec($ch); $o['http'][$u] = [curl_getinfo($ch, CURLINFO_HTTP_CODE), strlen((string)$b), curl_error($ch), preg_match('#<title>(.*?)</title>#si', (string)$b, $m) ? trim($m[1]) : ''];
}
echo json_encode($o, JSON_UNESCAPED_UNICODE), "\n";
