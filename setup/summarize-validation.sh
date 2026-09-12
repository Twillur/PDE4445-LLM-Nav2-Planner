#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/humble/setup.bash
for run in "$ROOT"/docs/validation/gazebo-*; do
    test -d "$run" || continue
    # Avoid reading recordings while a case is still running.
    complete=true
    for case_dir in "$run"/v2-*; do
        if test -d "$case_dir" && ! test -f "$case_dir/status.txt"; then
            complete=false
        fi
    done
    if [ "$complete" = true ]; then
        python3 "$ROOT/setup/summarize-simulation.py" "$run"
    fi
done
