#!/bin/sh
# Schematic -> netlist -> board -> checks. Run inside hardware/kicad/WPT-TX-DISPLAY.
# The board is written into a scratch directory first: pcbnew saves a project file next to a board, and here that
# would replace the rules of this project (WPT-TX-DISPLAY.kicad_pro) by the defaults.
set -e
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
python3 tools/gen_sch.py
kicad-cli sch erc --severity-all --exit-code-violations -o "$tmp/erc.rpt" WPT-TX-DISPLAY.kicad_sch
kicad-cli sch export netlist -o "$tmp/board.net" WPT-TX-DISPLAY.kicad_sch
python3 tools/make_board.py "$tmp/board.net" "$tmp/WPT-TX-DISPLAY.kicad_pcb" | grep -v 'Debug: Adding' || true
cp "$tmp/WPT-TX-DISPLAY.kicad_pcb" WPT-TX-DISPLAY.kicad_pcb
kicad-cli pcb drc --schematic-parity --refill-zones --save-board --severity-all --format json -o "${1:-$tmp/drc.json}" WPT-TX-DISPLAY.kicad_pcb
python3 tools/drc_summary.py "${1:-$tmp/drc.json}"
