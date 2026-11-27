#!/bin/sh
# One-off runner: install the package (key in $1, release commit in $2), copy Dar's AI keys (read-only on Dar), then a live check.
# Everything is pinned to the release commit (branch URLs are cached for minutes); the log is kept in ~/jw-install.log. Removes itself.
cd "$HOME" || exit 1
R=${2:-jaww}; B=https://raw.githubusercontent.com/a04032417-svg/Dar101/$R; P=/opt/alt/php83/usr/bin/php; LOG=$HOME/jw-install.log
echo "== release $R $(date -u +%FT%TZ)" > $LOG
for f in d c l; do curl -fsSL -o "$f.php" "$B/$f.php" || { echo "download $f failed" >> $LOG; exit 1; }; done
echo "== install" >> $LOG; $P d.php "$1" "$B/jaww.pkg" >> $LOG 2>&1
echo "== keys" >> $LOG; $P c.php >> $LOG 2>&1
echo "== live check" >> $LOG; $P l.php >> $LOG 2>&1
cat $LOG
rm -f d.php c.php l.php r.sh
