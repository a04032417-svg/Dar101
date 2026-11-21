<?php
// 1) Switches OFF the real-data view-only account made earlier (it showed real e-mails/phones) — status inactive, nothing deleted.
// 2) Reads Dar's own Buyers' Preview (sample data in the visitor's browser, no real data) and turns it on if it is off.
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
chdir('/home/u791571885/domains/dar.ink/public_html');
require 'dar-sync.php';
$o = [];
$own = one("SELECT * FROM users WHERE app = 'developer' AND role = 'owner' AND status != 'inactive' ORDER BY created LIMIT 1");
$c = ['app' => 'developer', 'user' => user_rec($own), 'row' => $own, 'tenant' => null, 'trow' => null, 'imp' => null, 'dev' => true, 'manager' => true, 'token' => null];
$v = one("SELECT id, status FROM users WHERE app = 'developer' AND email = 'buyer.preview@dar.ink'");
if ($v && $v['status'] !== 'inactive') { try { op_devusers_save($c, ['id' => $v['id'], 'status' => 'inactive']); } catch (Throwable $e) { $o['off_err'] = $e->getMessage(); } }
$v = one("SELECT id, status FROM users WHERE app = 'developer' AND email = 'buyer.preview@dar.ink'"); $o['viewer_status'] = $v['status'] ?? null;
q("DELETE FROM sessions WHERE uid = ?", [$v['id'] ?? '']); $o['viewer_sessions_left'] = (int)(one("SELECT COUNT(*) n FROM sessions WHERE uid = ?", [$v['id'] ?? ''])['n'] ?? 0);
if (!function_exists('pv_cfg')) { $o['preview'] = 'missing'; echo json_encode($o), "\n"; exit; }
$cfg = pv_cfg(); $o['preview_before'] = ['on' => $cfg['on'], 'slug' => $cfg['slug'] !== '', 'ai' => $cfg['ai']];
if (!$cfg['on']) { $cfg['on'] = true; pv_save($cfg); }
$t = pv_token(true); $o['preview_on'] = pv_cfg()['on']; $o['links'] = pv_links($t); $o['stats'] = pv_stats();
echo json_encode($o, JSON_UNESCAPED_SLASHES), "\n";
