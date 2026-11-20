<?php
// sets the free trial of Dar's paid plans to 5 days (run from the host's cron, CLI only); idempotent: writes only when a value differs
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
chdir('/home/u791571885/domains/dar.ink/public_html');
require 'dar-sync.php';
$N = 5; $o = ['before' => [], 'after' => [], 'tp' => [], 'wrote' => []];
$plans = bill_platform_rows('plans'); $ch = false;
foreach ($plans as $p) {
    $o['before'][] = [$p->code ?? '', $p->trial_days ?? null, $p->trial_days_month ?? null, $p->trial_days_year ?? null];
    if (($p->active ?? true) === false) continue;
    if (is_numeric($p->trial_days ?? null) && (int)$p->trial_days > 0 && (int)$p->trial_days !== $N) { $p->trial_days = $N; $ch = true; }
    foreach (['trial_days_month', 'trial_days_year'] as $k) if (isset($p->$k) && is_numeric($p->$k) && (int)$p->$k > 0 && (int)$p->$k !== $N) { $p->$k = $N; $ch = true; }
    $o['after'][] = [$p->code ?? '', $p->trial_days ?? null, $p->trial_days_month ?? null, $p->trial_days_year ?? null];
}
if ($ch) {
    if (kv_get('platform', 'bak:trial5:plans') === null) bill_kv_put('platform', 'bak:trial5:plans', jenc(bill_platform_rows('plans')));
    bill_kv_put('platform', 'db:platform:plans', jenc($plans)); $o['wrote'][] = 'plans';
}
$tps = bill_platform_rows('trial_plans'); $ch = false;
foreach ($tps as $t) {
    if (is_numeric($t->days ?? null) && (int)$t->days !== $N && ($t->active ?? true) !== false) { $t->days = $N; $ch = true; }
    $o['tp'][] = [$t->code ?? '', $t->days ?? null, $t->start ?? null];
}
if ($ch) {
    if (kv_get('platform', 'bak:trial5:trial_plans') === null) bill_kv_put('platform', 'bak:trial5:trial_plans', jenc(bill_platform_rows('trial_plans')));
    bill_kv_put('platform', 'db:platform:trial_plans', jenc($tps)); $o['wrote'][] = 'trial_plans';
}
foreach (bill_platform_rows('plans') as $p) $o['check'][] = [$p->code ?? '', function_exists('trial_plan_days') ? trial_plan_days((string)($p->audience ?? ''), (string)($p->code ?? ''), 'month') : null];
echo json_encode($o, JSON_UNESCAPED_UNICODE), "\n";
