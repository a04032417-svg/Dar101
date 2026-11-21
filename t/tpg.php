<?php
// One-time: adds a sign-in (user name + password) in front of Dar's buyers' preview (/v/<address>/…), at the owner's request.
// The preview keeps showing sample data only. The password is made here at run time, stored only as a hash (vault pv:login) and
// printed once to the host's cron output. Backups go OUTSIDE public_html; any failed check restores them and removes the login.
// Usage: php tpg.php <site dir> [<backup dir>] [--no-http]
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$dir = rtrim($argv[1] ?? '/home/u791571885/domains/dar.ink/public_html', '/');
$bak = rtrim($argv[2] ?? '/home/u791571885/pv-backup', '/');
$http = !in_array('--no-http', $argv, true);
$o = [];
$P = $dir . '/dar-preview.php'; $S = $dir . '/dar-sync.php';
$p0 = (string)file_get_contents($P); $s0 = (string)file_get_contents($S);
if (strpos($p0, 'function pv_login(') !== false) { $o['state'] = 'already patched'; }
else {
    $A1 = "// ---------------------------------------------------------------- the address\n";
    $A2 = "    \$h = (string)(\$_SERVER['HTTP_X_DAR_PREVIEW'] ?? ''); if (\$h === '' || !pv_valid(\$h)) return null;\n";
    $A3 = "    \$cfg = pv_cfg();\n    if ((\$_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'HEAD') pv_count(\$page);";
    $A4 = "if ((\$method === 'GET' || \$method === 'HEAD') && isset(\$_GET['pv'])) {";
    foreach ([[$p0, $A1], [$p0, $A2], [$p0, $A3], [$s0, $A4]] as $i => $x) if (substr_count($x[0], $x[1]) !== 1) { echo json_encode(['error' => 'anchor ' . ($i + 1) . ' not found once']), "\n"; exit; }
    $GATE = <<<'PHP'
// v3.34.1 — the preview's sign-in (the owner, 2026-11-21: «أعطني الحساب مع كلمة السر»): when a user name and a password are set
// (vault pv:login — the password kept only as a hash), every page of the preview and its AI door ask for them first; a signed,
// HttpOnly cookie keeps the visitor in for 12 hours. Wrong tries: 10 per 10 minutes from one address. The data stays sample data.
function pv_login(): ?array { $a = o2a(jdec((string)(vault_get('pv:login') ?? ''))); return is_array($a) && (string)($a['u'] ?? '') !== '' && (string)($a['h'] ?? '') !== '' ? $a : null; }
function pv_gate_key(array $l, string $t): string { return hash_hmac('sha256', 'pv-gate|' . strtolower($t) . '|' . $l['u'], (string)$l['h']); }
function pv_gate_ok(string $t): bool
{
    $l = pv_login(); if ($l === null) return true;
    if (!preg_match('/^(\d{10})\.([0-9a-f]{64})$/', (string)($_COOKIE['dar_pv'] ?? ''), $m) || (int)$m[1] < time()) return false;
    return hash_equals(hash_hmac('sha256', $m[1], pv_gate_key($l, $t)), $m[2]);
}
function pv_gate(string $t, string $page, string $L): void
{
    $l = pv_login(); $W = ['ar' => ['دخول المعاينة', 'اسم المستخدم', 'كلمة المرور', 'دخول', 'اسم المستخدم أو كلمة المرور غير صحيحة', 'معاينة للاطلاع فقط ببيانات تجريبية.'], 'en' => ['Preview sign-in', 'User name', 'Password', 'Sign in', 'Wrong user name or password', 'View-only preview with sample data.'], 'fr' => ['Connexion à l’aperçu', 'Nom d’utilisateur', 'Mot de passe', 'Se connecter', 'Nom d’utilisateur ou mot de passe incorrect', 'Aperçu en lecture seule avec des données d’exemple.']][$L] ?? null;
    $W = $W ?? ['Preview sign-in', 'User name', 'Password', 'Sign in', 'Wrong user name or password', 'View-only preview with sample data.']; $err = '';
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
        if (limited('pv_login', 10, 600)) { http_response_code(429); header('Retry-After: 600'); exit; }
        $u = strtolower(trim((string)($_POST['pv_user'] ?? ''))); $pw = (string)($_POST['pv_pass'] ?? '');
        if (strlen($pw) <= 200 && hash_equals(strtolower((string)$l['u']), $u) && password_verify($pw, (string)$l['h'])) {
            $exp = (string)(time() + 43200);
            setcookie('dar_pv', $exp . '.' . hash_hmac('sha256', $exp, pv_gate_key($l, $t)), ['expires' => (int)$exp, 'path' => '/', 'secure' => true, 'httponly' => true, 'samesite' => 'Lax']);
            header('Cache-Control: no-store'); header('Location: ' . pv_base() . 'v/' . $t . '/' . $page, true, 303); exit;
        }
        $err = $W[4];
    }
    $dir = $L === 'ar' ? 'rtl' : 'ltr';
    $css = ':root{--b:#2F6FEB;--bg:#F5F7FC;--card:#fff;--tx:#0A1226;--mu:#55627F;--ln:rgba(20,40,90,.16)}@media (prefers-color-scheme:dark){:root{--bg:#0A1022;--card:#111A33;--tx:#EAF0FF;--mu:#97A3C2;--ln:rgba(140,165,230,.24);--b:#7FA5FF}}'
        . '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.6 "IBM Plex Sans Arabic","Segoe UI",system-ui,-apple-system,Tahoma,sans-serif;min-height:100vh;display:grid;place-items:center;padding:18px}'
        . 'form{width:100%;max-width:380px;background:var(--card);border:1px solid var(--ln);border-radius:18px;padding:26px}h1{font-size:1.35rem;margin:0 0 4px}p{margin:0 0 18px;color:var(--mu);font-size:.92rem}'
        . 'label{display:block;font-size:.9rem;margin:12px 0 6px}input{width:100%;padding:11px 12px;border-radius:12px;border:1px solid var(--ln);background:transparent;color:inherit;font:inherit}'
        . 'button{margin-top:18px;width:100%;padding:11px;border:0;border-radius:12px;background:var(--b);color:#fff;font:inherit;font-weight:700;cursor:pointer}.e{color:#E5484D;margin:10px 0 0;font-size:.9rem}';
    $html = '<!doctype html><html lang="' . $L . '" dir="' . $dir . '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>' . pv_e($W[0]) . '</title><style>' . $css . '</style></head><body>'
        . '<form method="post" action="' . pv_e(pv_base() . 'v/' . $t . '/' . $page) . '" autocomplete="off"><h1>' . pv_e($W[0]) . '</h1><p>' . pv_e($W[5]) . '</p>'
        . '<label for="u">' . pv_e($W[1]) . '</label><input id="u" name="pv_user" required maxlength="80" autocapitalize="none" spellcheck="false">'
        . '<label for="p">' . pv_e($W[2]) . '</label><input id="p" name="pv_pass" type="password" required maxlength="200">'
        . ($err !== '' ? '<p class="e" role="alert">' . pv_e($err) . '</p>' : '') . '<button type="submit">' . pv_e($W[3]) . '</button></form></body></html>';
    http_response_code($err !== '' ? 401 : 200); header('Content-Type: text/html; charset=utf-8'); header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0'); header('Pragma: no-cache');
    header('X-Content-Type-Options: nosniff'); header('Referrer-Policy: no-referrer'); header('X-Robots-Tag: noindex, nofollow, noarchive');
    header("Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'");
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'HEAD') echo $html; exit;
}

PHP;
    $p1 = str_replace($A1, $GATE . $A1, $p0);
    $p1 = str_replace($A2, $A2 . "    if (!pv_gate_ok(\$h)) return null; // v3.34.1: the preview's sign-in\n", $p1);
    $p1 = str_replace($A3, "    if (!pv_gate_ok(\$t)) pv_gate(\$t, \$page, \$L); // v3.34.1: the preview's sign-in, when the owner set one\n" . $A3, $p1);
    $s1 = str_replace($A4, "if (isset(\$_GET['pv']) && (\$method === 'GET' || \$method === 'HEAD' || (\$method === 'POST' && isset(\$_POST['pv_user'])))) {", $s0);
    @mkdir($bak, 0700, true); $stamp = date('Ymd-His');
    copy($P, "$bak/dar-preview.php.$stamp"); copy($S, "$bak/dar-sync.php.$stamp"); $o['backup'] = "$bak/*.$stamp";
    $NP = "$bak/dar-preview.php.new"; $NS = "$bak/dar-sync.php.new"; file_put_contents($NP, $p1); file_put_contents($NS, $s1); // (written outside public_html: never served as text)
    $php = PHP_BINARY ?: 'php';
    foreach ([$NP, $NS] as $f) { exec(escapeshellarg($php) . ' -l ' . escapeshellarg($f) . ' 2>&1', $lo, $rc); if ($rc !== 0) { @unlink($NP); @unlink($NS); echo json_encode(['error' => 'syntax', 'lint' => $lo]), "\n"; exit; } }
    rename($NS, $S); rename($NP, $P); $o['state'] = 'patched';
    if (function_exists('opcache_reset')) @opcache_reset();
}
// the login (made once; never in any file of the repository)
chdir($dir); require $dir . '/dar-sync.php';
$user = 'dar-buyer'; $made = null;
if (vault_get('pv:login') === null || in_array('--new-password', $argv, true)) {
    $abc = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'; $made = ''; for ($i = 0; $i < 12; $i++) $made .= $abc[random_int(0, strlen($abc) - 1)];
    vault_put('pv:login', jenc(['u' => $user, 'h' => password_hash($made, PASSWORD_DEFAULT), 'at' => iso()]));
}
$PF = "$bak/pv-login.txt"; // (the demo password of a sample-data preview, kept outside public_html, owner-only, so a later run can print it again)
if ($made !== null) { @file_put_contents($PF, $made); @chmod($PF, 0600); }
$o['user'] = $user; $o['password'] = $made ?? (is_file($PF) ? trim((string)file_get_contents($PF)) : '(set earlier)');
$t = pv_token(); $o['address'] = $t; $o['on'] = pv_cfg()['on'];
// the live checks, over HTTPS from this server: closed without the password, a wrong one refused, the right one opens the page
if ($http && $made !== null && $t !== '') {
    $url = rtrim(site_url(), '/') . "/v/$t/admin";
    $req = function (string $method, array $post = [], string $cookie = '') use ($url) {
        $ch = curl_init($url); curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_HEADER => true, CURLOPT_TIMEOUT => 25, CURLOPT_FOLLOWLOCATION => false]);
        if ($method === 'POST') { curl_setopt($ch, CURLOPT_POST, true); curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($post)); }
        if ($cookie !== '') curl_setopt($ch, CURLOPT_COOKIE, $cookie);
        $r = (string)curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $hs = (int)curl_getinfo($ch, CURLINFO_HEADER_SIZE); curl_close($ch);
        return [$code, substr($r, 0, $hs), substr($r, $hs)];
    };
    [$c1, , $b1] = $req('GET');
    [$c2, , $b2] = $req('POST', ['pv_user' => $user, 'pv_pass' => 'wrong-' . $made]);
    [$c3, $h3] = $req('POST', ['pv_user' => $user, 'pv_pass' => $made]);
    preg_match('/set-cookie:\s*(dar_pv=[^;\r\n]+)/i', $h3, $ck);
    [$c4, , $b4] = $req('GET', [], $ck[1] ?? '');
    $chk = ['closed' => $c1 === 200 && strpos($b1, 'name="pv_pass"') !== false && strpos($b1, 'data-dar-pv') === false,
            'wrong_refused' => $c2 === 401 && strpos($b2, 'data-dar-pv') === false,
            'right_opens' => $c3 === 303 && !empty($ck[1]),
            'page_with_cookie' => $c4 === 200 && strpos($b4, 'data-dar-pv="' . $t . '"') !== false];
    $o['checks'] = $chk + ['codes' => [$c1, $c2, $c3, $c4]];
    if (in_array(false, $chk, true) && isset($stamp)) { // restore everything as it was
        copy("$bak/dar-preview.php.$stamp", $P); copy("$bak/dar-sync.php.$stamp", $S); vault_put('pv:login', null); @unlink($PF); unset($o['password']); $o['state'] = 'ROLLED BACK';
    }
}
echo json_encode($o, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), "\n";
