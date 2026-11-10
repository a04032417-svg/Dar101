#!/bin/sh
# Dar 3.34.18 restore (2026-11-10, the owner: «اصلح ذلك فورا»): dar-tg.php on the site had been overwritten outside Dar's pipeline
# by a 74-line stub. This reinstalls the SAME approved 3.34.18 package through its own run.sh (backup first, undone by itself if
# anything fails). Runs once: later runs show its saved output. The package key is given on the command line only.
cd "$HOME/ds33418s" || exit 1
if [ -e redo.out ]; then cat redo.out; exit 0; fi
[ -e install.out ] && mv install.out install.1.out
curl -fsSL --retry 3 -o "$HOME/ds18r.sh" https://raw.githubusercontent.com/a04032417-svg/Dar/72f8216fa73d3d28ea21fb18e6498cd500bdfb91/run.sh || exit 1
sh "$HOME/ds18r.sh" install "$1" > redo.out 2>&1
cat redo.out
