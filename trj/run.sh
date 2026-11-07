#!/bin/sh
# One-off (2026-11-07): Dar's own AI translates the two real-estate kits — see tr.php. sh trj.sh <key> <langs,comma>
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
U=https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj
[ -s tr.php ] || curl -fsSL -o tr.php $U/tr.php || exit 1
[ -s job.bin ] || curl -fsSL -o job.bin $U/job.bin || exit 1
/opt/alt/php83/usr/bin/php tr.php "$1" "$2"
