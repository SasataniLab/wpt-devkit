#!/bin/sh
# Revision 8 in one go. usage: sh rev8.sh BASE.kicad_pcb WORKDIR      (run inside tools/layout)
#   BASE     the board of revision 7b (git show b593d54:hardware/kicad/WPT-TX/WPT-01-TRANSMITTER.kicad_pcb > BASE)
#   WORKDIR  an empty directory outside the repository for the intermediate boards
# The schematic must already carry ../schematic/edit_sch12.py. The result is written into the project by finalize.py,
# which also runs KiCad's DRC with the comparison against the schematic.
set -e
base=$1; w=$2; prj=../..
mkdir -p "$w"
cp $prj/WPT-01-TRANSMITTER.kicad_pro $prj/WPT-01-TRANSMITTER.kicad_dru "$w"/
kicad-cli sch export netlist --format kicadsexpr -o "$w/rev8.net" $prj/WPT-01-TRANSMITTER.kicad_sch > /dev/null
run() {                                 # a step; pcbnew's chatter is dropped, a failure stops the run
    if ! python3 "$@" > "$w/step.log" 2>&1; then cat "$w/step.log"; exit 1; fi
    grep -v 'memory leak\|Debug' "$w/step.log" || true
}
run mech19.py "$base" "$w/a.kicad_pcb" "$w/rev8.net"                                   # the changes themselves
run weld.py "$w/a.kicad_pcb" "$w/WPT-01-TRANSMITTER.kicad_pcb" --all --skip VBUS       # pieces left in one line become one
run finalize.py "$w/WPT-01-TRANSMITTER.kicad_pcb" $prj ../schematic/pcb_side.py
