#!/bin/sh
# Revision 7 in one go. usage: sh rev7.sh BASE.kicad_pcb WORKDIR      (run inside tools/layout)
#   BASE     the board of revision 6 (git show 54b4246:hardware/kicad/WPT-TX/WPT-01-TRANSMITTER.kicad_pcb > BASE)
#   WORKDIR  an empty directory outside the repository for the intermediate boards
# The schematic must already carry ../schematic/edit_sch11.py. The result is written into the project by finalize.py,
# which also runs KiCad's DRC with the comparison against the schematic.
set -e
base=$1; w=$2; prj=../..
mkdir -p "$w"
cp $prj/WPT-01-TRANSMITTER.kicad_pro $prj/WPT-01-TRANSMITTER.kicad_dru "$w"/
kicad-cli sch export netlist --format kicadsexpr -o "$w/rev7.net" $prj/WPT-01-TRANSMITTER.kicad_sch > /dev/null
run() {                                 # a step; pcbnew's "memory leak" chatter is dropped, a failure stops the run
    if ! python3 "$@" > "$w/step.log" 2>&1; then cat "$w/step.log"; exit 1; fi
    grep -v 'memory leak' "$w/step.log" || true
}
run mech11.py "$base" "$w/a.kicad_pcb" "$w/rev7.net"            # comparators to the back side
run mech12.py "$w/a.kicad_pcb" "$w/b.kicad_pcb" "$w/rev7.net"   # J2, its signals, clock link
run mech13.py "$w/b.kicad_pcb" "$w/c.kicad_pcb"                 # silkscreen texts
run silkfix.py "$w/c.kicad_pcb" "$w/WPT-01-TRANSMITTER.kicad_pcb" added_refs.json \
    --also U308,U309,C340,C341,C342,C343,C344,C345,R334,R335,R336,R337,R338,R340,R342,R345,R346,R331,R332,U307
run finalize.py "$w/WPT-01-TRANSMITTER.kicad_pcb" $prj ../schematic/pcb_side.py
