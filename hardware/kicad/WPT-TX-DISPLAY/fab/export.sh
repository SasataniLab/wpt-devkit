#!/bin/sh
# Build the fabrication / assembly package for the display board with kicad-cli (KiCad 10).
#
#   fab/export.sh      -> writes everything into fab/out/
#
# Output:
#   out/gerber/     Gerbers for the 2 copper layers, mask, paste, silk, edge + Excellon drill (PTH / NPTH) and drill map
#   out/assembly/   bom_pcbway.csv (the BOM to send: one line per manufacturer part number, PCBWay's columns),
#                   placement.csv / placement_smd.csv (all placed parts / surface-mount only)
#   out/doc/        schematic PDF and front / back assembly drawings
#
# The display DS1 is in the BOM with the type LOOSE and is in no placement file: it is fitted by hand after assembly
# (its Assembly Note says how). The BOM script is the one of the transmitter board (../WPT-TX/fab/bom_pcbway.py).
set -eu

here=$(cd "$(dirname "$0")" && pwd)
prj=$(dirname "$here")
pcb="$prj/WPT-TX-DISPLAY.kicad_pcb"
sch="$prj/WPT-TX-DISPLAY.kicad_sch"
out="$here/out"

rm -rf "$out"
mkdir -p "$out/gerber" "$out/assembly" "$out/doc"

echo "== Gerbers"
kicad-cli pcb export gerbers \
    --layers F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
    --subtract-soldermask --check-zones \
    -o "$out/gerber/" "$pcb"

echo "== Drill"
kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th \
    --generate-map --map-format pdf \
    -o "$out/gerber/" "$pcb"

echo "== BOM and placement"
d="$out/assembly"
kicad-cli pcb export pos --format csv --units mm --side both -o "$d/placement.csv" "$pcb"
kicad-cli pcb export pos --smd-only --format csv --units mm --side both -o "$d/placement_smd.csv" "$pcb"
kicad-cli sch export bom --exclude-dnp \
    --fields 'Reference,Value,Footprint,Manufacturer,Manufacturer Part Number,Description,Assembly Note' \
    --labels 'Ref,Value,Footprint,Manufacturer,MPN,Description,Note' \
    -o "$d/parts.csv" "$sch"
python3 "$prj/../WPT-TX/fab/bom_pcbway.py" "$d/parts.csv" "$d/placement.csv" "$d/placement_smd.csv" "$d/bom_pcbway.csv" "$here/bom_extra.csv" --loose=DS1

echo "== Documents"
kicad-cli sch export pdf -o "$out/doc/schematic.pdf" "$sch"
kicad-cli pcb export pdf --layers F.Fab,Edge.Cuts --sketch-pads-on-fab-layers --exclude-value --mode-single \
    -o "$out/doc/assembly_front.pdf" "$pcb"
kicad-cli pcb export pdf --layers B.Fab,Edge.Cuts --mirror --sketch-pads-on-fab-layers --exclude-value --mode-single \
    -o "$out/doc/assembly_back.pdf" "$pcb"

echo "== Done"
find "$out" -type f | sort | sed "s|$out/||"
