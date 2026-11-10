<?php
// Dar 3.34.18 — the owner's order (2026-11-10): «ارسل في جميع المحادثات والقروبات بلا اي استثناء، وان تلتزم في رسالتها بالسياق
// السابق حسب كل محادثة… هي من تحدد». «فرح» writes once in EVERY chat of his account (private and groups; only his Saved Messages,
// Telegram's service chat and channels, where no one can write, are left out), each message written by her own tgu_voice() from that
// chat's own past messages — the same function as «اكتب للجميع», without its 6-chat batch or its skips. A chat with no message in her
// log first gets its real recent history from Telegram, so she has its context. Runs from a cron each minute under a lock; each chat
// is done once (its result kept in ~/tgall/done.json); the report goes to .dar/tgall.txt. Nothing in Dar's files changes.
$site = '/home/u791571885/domains/dar.ink/public_html'; $D = getenv('HOME') . '/tgall'; @mkdir($D, 0700, true);
$lk = fopen("$D/lock", 'c'); if (!$lk || !flock($lk, LOCK_EX | LOCK_NB)) exit(0);
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$done = json_decode((string)@file_get_contents("$D/done.json"), true); if (!is_array($done)) $done = [];
$report = function () use (&$done, $site) {
    $n = ['sent' => 0, 'failed' => 0]; foreach ($done as $r) $n[!empty($r['ok']) ? 'sent' : 'failed']++;
    @file_put_contents($site . '/.dar/tgall.txt', json_encode(['at' => gmdate('c'), 'counts' => $n, 'chats' => array_values($done)], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n");
};
if (!tgu_open()) { $done['_'] = ['ok' => false, 'why' => 'his Telegram account is not linked now']; file_put_contents("$D/done.json", json_encode($done)); $report(); exit(0); }
tgu_dialogs(100); // (every chat Telegram lists for him joins her list first)
$self = (string)tgu_self_id(); $t0 = time();
foreach (tgu_chats() as $id => $x) {
    $id = (string)$id; $type = (string)($x['type'] ?? '');
    if ($id === $self || $id === '777000' || $type === 'channel' || isset($done[$id])) continue;
    if (time() - $t0 > 240) break; // (the next minute's run carries on)
    $row = ['id' => substr(hash('sha256', 'tgd|' . $id), 0, 6), 'type' => $type];
    try {
        if (!tgu_log($id)) { // her log has nothing of this chat yet: its real recent messages, from Telegram
            $h = tgu_call('GET', '/history?' . http_build_query(['chat' => $id, 'limit' => 20]));
            foreach (array_reverse(is_array($h['json']['items'] ?? null) ? $h['json']['items'] : []) as $y) { $t = trim((string)($y['text'] ?? '')); if ($t === '') continue;
                tgu_log_add($id, ['at' => 1000 * (int)($y['date'] ?? time()), 'mid' => (int)($y['id'] ?? 0), 'from' => !empty($y['out']) ? 'أنا' : mb_substr((string)($y['from']['name'] ?? ''), 0, 60), 'out' => !empty($y['out']), 't' => mb_substr($t, 0, 4000)]); }
            $row['history'] = count(tgu_log($id));
        }
        $v = tgu_voice('write something natural that fits this chat right now, following what was said before in it', $id);
        if ($v === '') { $row += ['ok' => false, 'why' => 'she could not write it in her voice (AI unavailable or the text was refused)']; }
        else { $r = tgu_send($id, $v, 0, 'all2:' . $id . ':20261110'); $row += ['ok' => !empty($r['ok']), 'why' => !empty($r['ok']) ? '' : (string)($r['why'] ?? 'send failed'), 'text' => $v]; if (!empty($r['ok'])) sleep(4); }
    } catch (Throwable $e) { $row += ['ok' => false, 'why' => 'error: ' . substr($e->getMessage(), 0, 160)]; }
    $done[$id] = $row; file_put_contents("$D/done.json", json_encode($done, JSON_UNESCAPED_UNICODE));
}
$report(); echo "ok\n";
