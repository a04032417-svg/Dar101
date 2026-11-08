# Releasing a fix to Dar (dar.ink) — the owner's rule: only through Dar's own pipeline

Never edit dar.ink files any other way. Every key below is made fresh for the release and given only on a command line; none is stored.

1. **The live code.** Make a random 32-byte key K (base64). Hostinger cron (username u791571885, `* * * * *`):
   `sh -c 'cd $HOME && mkdir -p trj && curl -fsSL -o trj/fxsrc.sh "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/fxsrc.sh?t=$(date +%s)" && sh trj/fxsrc.sh K' 2>&1`
   After 1–2 minutes read `https://dar.ink/fxtr/<sha256(K bytes + b"fxsrc") hex[:20]>/src.json` and `src.bin` (Composio workbench `requests.get`; the shell cannot reach dar.ink), then DELETE the cron.
   `src.bin` = iv(12) | tag(16) | ct, AES-256-GCM → a zip of the files of `trj/release-files.txt` as they are live (its sha256 is in src.json).
2. **The fix.** A patch script like `trj/p3411.py`: exact replacements that must match once (`sub1`), new functions appended, then the version
   everywhere: `SYNC_VERSION` in dar-sync.php, `VERSION = '<v>-fx'` in assets/core.js, the build token of lib/manifest.json replaced in every file,
   manifest `version`/`token`/`built` and every file's sha1. `php -l` every changed file. Tests: a PHP file that boots the tree with
   `DAR_DEBUG=1` and its own `DAR_DATA_DIR`, drives the factory with `$GLOBALS['fx_test_ai']` (see 3.34.10/3.34.11 tests) — all must pass.
3. **Trial install** on a local copy of the live tree: serve it with `php -S 127.0.0.1:8099 -t <copy> trj/router.php` (`DAR_SITE_ROOT=<copy>`),
   then `DAR_INSTALL_TEST=1 DAR_DATA_DIR=<data> DAR_SELF_URL=http://127.0.0.1:8099 php host-install.php install <copy> <key> <zip sha256>`
   (host-install.php: repo a04032417-svg/Dar, branch claude/dar-release-3320, hash = HI in run.sh). It must answer ok with `canary ok, checked 31`.
4. **The package.** Zip the patched tree in the order of release-files.txt (deflate, fixed date), encrypt with a NEW key (iv|tag|ct), split into
   parts of 700,000 bytes `dar.zip.enc.1..N`, commit them to a04032417-svg/Dar branch claude/dar-release-3320 (Composio GitHub Git Data API:
   blobs → tree → commit → PATCH the ref; one request stays under ~700 KB), then a second commit changing run.sh: the header version,
   `S=/home/u791571885/ds<ver>s`, `SRC=` the package commit's raw URL, `ZH=` zip sha256, `ENC=` joined sha256, `NP=` parts. Read the parts back
   from raw.githubusercontent.com and check the joined sha256.
5. **Install.** Hostinger cron `* * * * *`: `sh -c 'cd $HOME && curl -fsSL -o ds<ver>.sh https://raw.githubusercontent.com/a04032417-svg/Dar/<run.sh commit>/run.sh && sh ds<ver>.sh install <new key>' 2>&1`.
   The site's own installer backs up, installs, runs its 31-check canary and rolls back by itself on any failure. After 2–5 minutes check
   `https://dar.ink/dar-sync.php?op=health` and `assets/core.js` show the new version, then DELETE the cron.
6. If the package's file list changed, update trj/release-files.txt.
