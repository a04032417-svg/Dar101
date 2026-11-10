#!/bin/sh
# Dar 3.34.18 restore, take 2 (2026-11-10): host-install.php answered «again» (nothing done) in ds33418s, because that folder
# already holds this morning's done-install.json. This runs the SAME approved run.sh from a fresh folder (ds33418r), so the
# installer really reinstalls 3.34.18 (backup first, undone by itself if anything fails). Runs once; its output is copied to
# .dar/redo.txt (a folder the web cannot read) so the session can see it. The package key is given on the command line only.
O=/home/u791571885/domains/dar.ink/public_html/.dar/redo.txt
cd "$HOME" || exit 1
if [ -e ds33418r/redo.out ]; then { date -u; tail -c 3000 ds33418r/redo.out; } > "$O" 2>&1; exit 0; fi
mkdir -p ds33418r
curl -fsSL --retry 3 -o ds18r.sh https://raw.githubusercontent.com/a04032417-svg/Dar/72f8216fa73d3d28ea21fb18e6498cd500bdfb91/run.sh || exit 1
sed -i 's#/ds33418s;#/ds33418r;#' ds18r.sh
grep -q '^S=/home/u791571885/ds33418r;' ds18r.sh || { echo "S not switched" > "$O"; exit 1; }
sh ds18r.sh install "$1" > ds33418r/redo.out 2>&1
{ date -u; tail -c 3000 ds33418r/redo.out; } > "$O" 2>&1
