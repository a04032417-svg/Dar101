<?php
// Creates ONE view-only developer-panel account for buyers' due diligence, through Dar's own invite + accept flow
// (role «viewer»: edits nothing). The password is made here at run time and printed to the host's cron output only.
// Parts it may SEE come from argv[1] (comma list); it never gets ai, accounts, tenants, monitoring, backups, subscriptions.
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
chdir('/home/u791571885/domains/dar.ink/public_html');
require 'dar-sync.php';
$email = 'buyer.preview@dar.ink';
$deny = ['ai', 'accounts', 'tenants', 'monitoring', 'backups', 'subscriptions'];
$view = array_values(array_diff(array_intersect(DEV_PERMS, explode(',', $argv[1] ?? 'services,countries,pricing,payments,texts,appearance,automation')), $deny));
$o = ['email' => $email, 'view' => $view];
$ex = one("SELECT id, rec FROM users WHERE app = 'developer' AND email = ?", [$email]);
if ($ex) { $o['exists'] = $ex['id']; $o['access'] = (o2a(jdec($ex['rec'])) ?: [])['access'] ?? null; echo json_encode($o), "\n"; exit; }
$own = one("SELECT * FROM users WHERE app = 'developer' AND role = 'owner' AND status != 'inactive' ORDER BY created LIMIT 1");
if (!$own) { echo json_encode(['error' => 'no owner']), "\n"; exit; }
$c = ['app' => 'developer', 'user' => user_rec($own), 'row' => $own, 'tenant' => null, 'trow' => null, 'imp' => null, 'dev' => true, 'manager' => true, 'token' => null];
$until = now_ms() + 45 * 86400000;
$inv = op_invite($c, ['email' => $email, 'name' => 'Buyer Preview (view only)', 'role' => 'viewer', 'access' => ['edit' => [], 'view' => $view], 'until' => $until], 'dev');
$pw = substr(str_replace(['+', '/', '='], ['k', 'm', ''], base64_encode(random_bytes(18))), 0, 16);
$c2 = ['app' => 'developer', 'user' => null, 'row' => null, 'tenant' => null, 'trow' => null, 'imp' => null, 'dev' => false, 'manager' => false, 'token' => null];
$acc = op_accept($c2, ['code' => $inv['code'], 'password' => $pw, 'name' => 'Buyer Preview (view only)'], 'dev');
$u = one("SELECT id, role, rec FROM users WHERE app = 'developer' AND email = ?", [$email]);
$o += ['created' => $u['id'] ?? null, 'role' => $u['role'] ?? null, 'access' => (o2a(jdec($u['rec'] ?? '{}')) ?: [])['access'] ?? null, 'until' => iso($until), 'password' => $pw, 'mailed' => $inv['mailed'] ?? null];
echo json_encode($o), "\n";
