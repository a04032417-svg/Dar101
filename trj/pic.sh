#!/bin/sh
# 2026-11-08: Dar's copy team writes the fixed phrases of the factory pictures in 14 languages. sh pic.sh <key> <commit> [langs]
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
U=https://raw.githubusercontent.com/a04032417-svg/Dar101/$2/trj
for f in pic.php pic_en.json; do curl -fsSL -o "$f.new" "$U/$f" && mv "$f.new" "$f"; done
TR_BUDGET=230 /opt/alt/php83/usr/bin/php pic.php "$1" "$3"
