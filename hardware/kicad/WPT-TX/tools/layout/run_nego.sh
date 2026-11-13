#!/bin/sh
# usage: run_nego.sh BOARD MAX_RIPS LOG   (restarts the driver when pcbnew fails to reload the board)
b=$1; n=$2; log=$3
reg=$(echo "$b" | sed 's/\.kicad_pcb$/_reg.json/')
i=0
while [ $i -lt 14 ]; do
    if [ -f "$reg" ]; then python3 -u nego.py "$b" "$n" --no-corridors $EXTRA --resume "$reg" >> "$log" 2>&1; else python3 -u nego.py "$b" "$n" --no-corridors $EXTRA >> "$log" 2>&1; fi
    rc=$?
    echo "=== nego exit $rc" >> "$log"
    [ $rc -ne 3 ] && [ $rc -ne 4 ] && break
    i=$((i + 1))
done
