#!/bin/sh
D=$HOME/trj; mkdir -p "$D"; cd "$D" || exit 1
curl -fsSL -o fxspec.php.new "https://raw.githubusercontent.com/a04032417-svg/Dar101/trj/trj/fxspec.php?t=$(date +%s)" && mv fxspec.php.new fxspec.php
/opt/alt/php83/usr/bin/php fxspec.php "$1" "${2:-fx-20261107-2348-photographer,fx-20261107-2348-photographer-p2}"
