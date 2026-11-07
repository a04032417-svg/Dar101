#!/bin/sh
# 2026-11-08: Dar's copy team writes the listings and picture texts of the two real-estate kits. sh cpy.sh <key> <langs,comma> <commit>
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
U=https://raw.githubusercontent.com/a04032417-svg/Dar101/$3/trj
for f in cpy.php cjob.bin; do curl -fsSL -o "$f.new" "$U/$f" && mv "$f.new" "$f"; done
TR_BUDGET=230 /opt/alt/php83/usr/bin/php cpy.php "$1" "$2"
