#!/bin/sh
# Round 3 (2026-11-07): Dar's AI fixes the strings left in English, then writes the store listings in 14 languages. sh run2.sh <key> <langs,comma>
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
U=https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj
for f in fixtr.php fix.bin ltr.php ljob.bin; do curl -fsSL -o "$f.new" "$U/$f?t=$(date +%s)" && mv "$f.new" "$f"; done
TR_BUDGET=130 /opt/alt/php83/usr/bin/php fixtr.php "$1" "$2"
TR_BUDGET=130 /opt/alt/php83/usr/bin/php ltr.php "$1" "$2"
