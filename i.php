<?php
// Read-only look at which Dar account answers the owner's Gmail (no secrets printed, nothing written). Removes itself.
$d = getenv('HOME') . '/domains/dar.ink'; $dir = null; foreach (["$d/dar-data", "$d/public_html/.dar/data"] as $x) if (is_file("$x/dar.sqlite")) { $dir = $x; break; }
$p = new PDO('sqlite:' . "$dir/dar.sqlite", null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC, PDO::SQLITE_ATTR_OPEN_FLAGS => PDO::SQLITE_OPEN_READONLY]);
$o = ['links' => []];
try { foreach ($p->query("SELECT ns, provider, data, upd FROM conn_links WHERE provider IN ('gmail','outlook')") as $r) { $j = json_decode($r['data'], true) ?: []; $t = $p->prepare('SELECT * FROM tenants WHERE id = ?'); $t->execute([$r['ns']]); $tr = $t->fetch() ?: [];
  $o['links'][] = ['ns' => $r['ns'], 'tenant_cols' => array_keys($tr), 'tenant_name' => $tr['name'] ?? ($tr['title'] ?? null), 'provider' => $r['provider'], 'status' => $j['status'] ?? null, 'auto' => $j['auto'] ?? null, 'account' => $j['account']['name'] ?? null, 'polled_at' => $j['polled_at'] ?? null, 'linked_at' => $j['at'] ?? null]; } } catch (Throwable $e) { $o['links_err'] = $e->getMessage(); }
try { $k = $p->query("SELECT v FROM kv WHERE ns='platform' AND k='db:platform:oauth_apps'")->fetch(); foreach ((array)json_decode($k['v'] ?? '[]', true) as $a) if (($a['platform'] ?? '') === 'google') $o['google_apps'][] = ['id' => $a['id'] ?? null, 'project_number' => explode('-', (string)($a['client_id'] ?? ''))[0], 'active' => $a['active'] ?? null, 'connect' => $a['connect'] ?? null]; } catch (Throwable $e) { $o['apps_err'] = $e->getMessage(); }
try { $c = $p->query("SELECT v FROM meta WHERE k='connect_cfg'")->fetch(); $o['connect_cfg_google'] = (json_decode($c['v'] ?? '{}', true)['google'] ?? null); } catch (Throwable $e) {}
echo json_encode($o, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), "\n";
if (dirname(__FILE__) === getenv('HOME')) @unlink(__FILE__);
