<?php
// read-only: Dar's plan prices as the site has them (CLI only)
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
chdir('/home/u791571885/domains/dar.ink/public_html');
require 'dar-sync.php';
$P = platform_rec();
$o = ['base_currency' => $P->base_currency ?? null, 'base_usd_rate' => $P->base_usd_rate ?? null, 'default_country' => $P->default_country ?? null,
    'yearly' => function_exists('bill_yearly_on') ? bill_yearly_on() : null, 'tax_note' => $P->tax_note ?? null];
foreach (bill_platform_rows('plans') as $p) if (($p->active ?? true) !== false && in_array($p->audience ?? '', ['office', 'builder'], true))
    $o['plans'][] = ['code' => $p->code ?? '', 'aud' => $p->audience ?? '', 'name' => $p->name_ar ?? '', 'base' => $p->base_price ?? null, 'prices' => $p->prices ?? null,
        'disc' => $p->discount_pct ?? null, 'disc_until' => $p->discount_until ?? null, 'months_free' => $p->months_free ?? null, 'sort' => $p->sort ?? null];
$cs = jdec(kv_get('platform', 'db:platform:countries'));
if (is_array($cs)) foreach ($cs as $c) if (is_object($c) && strtoupper((string)($c->code ?? '')) === 'SA') $o['SA'] = array_intersect_key(get_object_vars($c), array_flip(['code', 'currency', 'rate', 'usd_rate', 'tax_rate', 'price_factor', 'active']));
echo json_encode($o, JSON_UNESCAPED_UNICODE), "\n";
