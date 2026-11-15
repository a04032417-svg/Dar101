#!/bin/bash
# wait for out/<x>/p1..pN to be built ok, then push build/<x>/suite.json (starts suite-pack)
X=$1; N=$2; cd /home/claude/suite
while true; do
  ok=0; bad=""
  for i in $(seq 1 $N); do
    if git fetch -q origin out/$X/p$i 2>/dev/null; then
      r=$(git show FETCH_HEAD:result.json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok' if d.get('ok') else 'fail:'+str(d.get('stage')))" 2>/dev/null)
      [ "$r" = ok ] && ok=$((ok+1)) || bad="$bad p$i:$r"
    fi
  done
  echo "$(date +%H:%M) built $ok/$N $bad"
  case "$bad" in *fail*) echo "FAILED $bad"; exit 1;; esac
  [ $ok -eq $N ] && break
  sleep 60
done
cp /home/claude/work/$X/suite.json build/$X/suite.json && python3 -c "import json; d=json.load(open('build/$X/suite.json')); json.dump(d, open('build/$X/suite.json','w'), ensure_ascii=False, separators=(',',':'))"
git add build/$X/suite.json && git commit -qm "$X suite.json (pack)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: scheduled pipeline run" && git push -q origin HEAD:suite && echo "PUSHED suite.json"
