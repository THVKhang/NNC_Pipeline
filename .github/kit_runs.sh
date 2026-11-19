#!/usr/bin/env bash
# Run the recorded runs of a design's reproduction kit with make only, and compare each one with its
# recorded result (nnc kit-check --run). Used by CI; also works by hand on Linux or inside WSL.
#   .github/kit_runs.sh <design>                  every run of sim/configs/runs.tsv
#   .github/kit_runs.sh <design> --skip-primary   all but the first (primary) run, which the kit job runs
#   .github/kit_runs.sh <design> --only <label>   one run, e.g. min.s2
# Logs: designs/<design>/sim/runlogs/<label>/{sim.log,results.xml}. Exit 1 if any outcome differs.
set -u
design=$1
skip=${2:-}
only=${3:-}
sim=designs/$design/sim
tsv=$sim/configs/runs.tsv
if [ ! -f "$tsv" ]; then
  echo "$design: no run set (no $tsv): the kit job runs its one recorded run"
  exit 0
fi
fail=0
first=1
while IFS=$'\t' read -r label folder seed; do
  case "$label" in "#"*|"") continue ;; esac
  if [ $first = 1 ] && [ "$skip" = "--skip-primary" ]; then first=0; continue; fi
  first=0
  if [ "$skip" = "--only" ] && [ "$label" != "$only" ]; then continue; fi
  echo "::group::$design $label (sim/$folder, seed $seed)"
  ( cd "$sim/$folder" && rm -f results.xml sim.log && make regression SEED="$seed" > sim.log 2>&1 )
  echo "make returned $? (failing tests are compared below, not judged by the return code)"
  mkdir -p "$sim/runlogs/$label"
  cp "$sim/$folder/sim.log" "$sim/$folder/results.xml" "$sim/runlogs/$label/" 2>/dev/null
  "${PYTHON:-python3}" -m nnc kit-check "$design" --run "$label" || fail=1
  echo "::endgroup::"
done < "$tsv"
exit $fail
