<?php
// turns off «card first at sign-up» (billing.checkout_first = false) so a new account starts its free days without a card (CLI only; idempotent)
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
chdir('/home/u791571885/domains/dar.ink/public_html');
require 'dar-sync.php';
$o = ['before' => platform_rec()->billing->checkout_first ?? 'unset', 'on_before' => trial_checkout_first_on(), 'wrote' => false];
tx(function () use (&$o): void {
    $P = platform_rec(); if (!is_object($P->billing ?? null)) $P->billing = new stdClass();
    if (($P->billing->checkout_first ?? true) !== false) {
        if (kv_get('platform', 'bak:nocard:billing') === null) bill_kv_put('platform', 'bak:nocard:billing', jenc($P->billing));
        $P->billing->checkout_first = false; kv_put('platform', 'platform', jenc($P), 'owner-nocard'); $o['wrote'] = true;
    }
});
$o['after'] = platform_rec()->billing->checkout_first ?? 'unset'; $o['on_after'] = trial_checkout_first_on();
// a new office account on a paid plan, as the sign-up builds it: no checkout must come back now
$t = (object)['app' => 'app', 'audience' => 'office', 'plan' => 'basic', 'country' => 'SA', 'status' => 'trial', 'signup_cycle' => 'month'];
$o['signup_checkout'] = trial_checkout_first($t, [], ['result' => 'started', 'code' => '']); $o['signup_status'] = $t->status; $o['plan_days'] = trial_plan_days('office', 'basic', 'month');
$o['waiting_card'] = (int)(one("SELECT COUNT(*) n FROM tenants WHERE status = 'suspended' AND rec LIKE '%\"suspend_reason\":\"card_needed\"%'")['n'] ?? 0);
echo json_encode($o, JSON_UNESCAPED_UNICODE), "\n";
