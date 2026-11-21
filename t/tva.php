<?php
// Audit of the buyer-preview (view-only) developer account: calls every READ operation as that account through Dar's own
// dispatcher and reports which ones answer, and whether an answer carries e-mails, phone numbers or chat text (masked).
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
chdir('/home/u791571885/domains/dar.ink/public_html');
require 'dar-sync.php';
$u = one("SELECT id FROM users WHERE app = 'developer' AND email = 'buyer.preview@dar.ink'");
if (!$u) { echo "no viewer\n"; exit; }
$tok = new_session($u['id'], 'developer');
$skip = '/brief|recall|aware\.now|^now$|search|lookup|radar|google\.report|lab/';
$ops = array_unique(array_merge(DEV_READ_OPS, array_keys(DEV_READ_ACTIONS), array_keys(DEV_READ_UNLESS), ['sync.pull']));
$allow = ['buyer.preview@dar.ink', 'service@dar.ink'];
$out = ['ok' => [], 'denied' => [], 'flag' => []];
foreach ($ops as $op) {
    if (preg_match($skip, $op)) continue;
    $body = (object)['op' => $op, 'payload' => $op === 'sync.pull' ? (object)['since' => 0] : new stdClass(), 'app' => 'developer', 'token' => $tok, 'v' => SYNC_VERSION];
    try { $r = handle($body); $s = jenc($r); }
    catch (DarFail $e) { $out['denied'][] = $op . ':' . $e->getMessage(); continue; }
    catch (Throwable $e) { $out['denied'][] = $op . ':ERR'; continue; }
    preg_match_all('/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/', $s, $m); $em = array_values(array_diff(array_unique($m[0]), $allow));
    preg_match_all('/(?<![\d.])(?:\+?966|00966|0)5\d{8}(?!\d)|(?<![\d.])\+\d{11,13}(?!\d)/', $s, $m2); $ph = array_unique($m2[0]);
    $chat = preg_match_all('/"(role|msg|messages|thread|transcript|chat)"/', $s);
    $out['ok'][] = $op . '(' . strlen($s) . ')';
    if ($em || $ph || $chat) $out['flag'][] = ['op' => $op, 'emails' => count($em), 'email_sample' => array_map(fn($e) => substr($e, 0, 3) . '***@' . substr(strrchr($e, '@'), 1), array_slice($em, 0, 4)), 'phones' => count($ph), 'chat_keys' => $chat];
}
q('DELETE FROM sessions WHERE h = ?', [hash('sha256', $tok)]);
echo json_encode($out, JSON_UNESCAPED_UNICODE), "\n";
