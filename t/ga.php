<?php
// The owner (2026-11-25): stop the automatic replies sent from his own Gmail (linked to an office in Dar, signed «المكتب التجريبي»).
// Turns off the automatic replies of that Gmail link only (the same switch as the office's own «Gmail» settings: auto = false);
// the link itself, the office's WhatsApp and everything else stay as they are. Prints what it found and what it changed.
if (PHP_SAPI !== 'cli') exit;
$H = '/home/u791571885'; $D = "$H/domains/dar.ink/public_html"; chdir($D); require $D . '/dar-sync.php';
@unlink("$H/p.php");
$mask = fn(string $e): string => preg_replace('/^(.).*(@.*)$/', '$1***$2', $e);
$out = ['links' => []];
conn_db();
foreach (q("SELECT ns, provider, data FROM conn_links WHERE provider IN ('gmail', 'outlook')")->fetchAll() as $row) {
    $ns = (string)$row['ns']; $prov = (string)$row['provider']; $l = o2a(jdec($row['data'])) ?: [];
    $acct = strtolower((string)($l['account']['name'] ?? ''));
    $T = tenant_obj(one('SELECT * FROM tenants WHERE id = ?', [$ns]));
    $it = ['ns' => $ns, 'office' => (string)($T->name ?? ''), 'provider' => $prov, 'account' => $mask($acct), 'status' => (string)($l['status'] ?? ''), 'auto_before' => conn_auto($prov, $l)];
    if ($prov === 'gmail' && $acct === 'a04032417@gmail.com') {
        $l['auto'] = false; conn_link_put($ns, $prov, $l);
        $it['auto_after'] = conn_auto($prov, conn_link($ns, $prov));
        $c = wat_cfg($ns, $T); $rules = flow_rows($ns, 'reply_rules');
        $it['rules_on'] = (bool)$c['on']; $it['rules'] = count($rules);
        $it['rules_for_email'] = count(array_filter($rules, function ($r) { $ch = $r['channels'] ?? ($r['channel'] ?? ''); $ch = is_array($ch) ? $ch : array_filter(explode(',', (string)$ch)); return !$ch || array_intersect($ch, ['email', 'gmail', 'all']); }));
        $it['away_set'] = trim((string)($c['away'] ?? '')) !== ''; $it['welcome_set'] = trim((string)($c['welcome'] ?? '')) !== '';
        $since = gmdate('Y-m-d', time() - 14 * 86400); $via = [];
        foreach (flow_rows($ns, 'messages') as $m) if (($m['channel'] ?? '') === 'email' && ($m['direction'] ?? '') === 'out' && strcmp((string)($m['created'] ?? ''), $since) >= 0) { $k = (string)($m['via'] ?? '-'); $via[$k] = ($via[$k] ?? 0) + 1; }
        $it['email_out_14d_by_via'] = $via;
    }
    $out['links'][] = $it;
}
$out['done'] = gmdate('c');
echo json_encode($out, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), "\n";
