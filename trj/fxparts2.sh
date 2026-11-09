#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o fxparts2.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/fxparts2.php?t=$(date +%s)" && mv fxparts2.php.new fxparts2.php
/opt/alt/php83/usr/bin/php fxparts2.php "$1"
