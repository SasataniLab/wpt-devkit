#!/bin/sh
# Build the fabrication / assembly package for WPT-01-TRANSMITTER with kicad-cli (KiCad 10).
#
#   fab/export.sh            -> writes everything into fab/out/
#
# Output:
#   out/gerber/              Gerbers for the 4 copper layers, mask, paste, silk, edge + Excellon drill (PTH / NPTH) and drill map
#   out/assembly/<variant>/  BOM and pick-and-place files (all parts / surface-mount only) for each assembly variant
#                            (Legacy, HRTIM), DNP parts excluded. bom_<variant>_pcbway.csv is the one to send:
#                            one line per manufacturer part number (fab/bom_pcbway.py)
#   out/doc/                 schematic PDF and front/back assembly drawings, one set per variant (parts not fitted are crossed out)
set -eu

here=$(cd "$(dirname "$0")" && pwd)
prj=$(dirname "$here")
pcb="$prj/WPT-01-TRANSMITTER.kicad_pcb"
sch="$prj/WPT-01-TRANSMITTER.kicad_sch"
out="$here/out"
variants="Legacy HRTIM"

rm -rf "$out"
mkdir -p "$out/gerber" "$out/doc"

echo "== Gerbers"
kicad-cli pcb export gerbers \
    --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
    --subtract-soldermask --check-zones \
    -o "$out/gerber/" "$pcb"

echo "== Drill"
kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th \
    --generate-map --map-format pdf \
    -o "$out/gerber/" "$pcb"

for v in $variants; do
    d="$out/assembly/$v"
    mkdir -p "$d"
    echo "== BOM and placement: $v"
    # one line per distinct part; DNP parts are left out
    kicad-cli sch export bom --variant "$v" --exclude-dnp \
        --fields '${ITEM_NUMBER},Reference,${QUANTITY},Value,Description,Footprint,Manufacturer,Manufacturer Part Number' \
        --labels 'Line,Designator,Qty,Value,Description,Package,Manufacturer,Mfg Part #' \
        --group-by 'Value,Footprint,Manufacturer Part Number' \
        --ref-range-delimiter '' \
        -o "$d/bom_$v.csv" "$sch"
    kicad-cli pcb export pos --variant "$v" --exclude-dnp --format csv --units mm --side both \
        -o "$d/placement_$v.csv" "$pcb"
    # the assembler's machine file: surface-mount parts only
    kicad-cli pcb export pos --variant "$v" --exclude-dnp --smd-only --format csv --units mm --side both \
        -o "$d/placement_${v}_smd.csv" "$pcb"
    # the BOM to send: one line per manufacturer part number, PCBWay's columns, SMD / THT marked
    kicad-cli sch export bom --variant "$v" --exclude-dnp \
        --fields 'Reference,Value,Footprint,Manufacturer,Manufacturer Part Number,Description,Assembly Note' \
        --labels 'Ref,Value,Footprint,Manufacturer,MPN,Description,Note' \
        -o "$d/parts_$v.csv" "$sch"
    python3 "$here/bom_pcbway.py" "$d/parts_$v.csv" "$d/placement_$v.csv" "$d/placement_${v}_smd.csv" "$d/bom_${v}_pcbway.csv"
done

echo "== Documents"
# One set per variant. Without --variant kicad-cli draws the default population, which is the Legacy one: the drawings
# would then cross out the parts the HRTIM BOM lists and show the parts it leaves out.
for v in $variants; do
    kicad-cli sch export pdf --variant "$v" -o "$out/doc/schematic_$v.pdf" "$sch"
    kicad-cli pcb export pdf --variant "$v" --layers F.Fab,Edge.Cuts --sketch-pads-on-fab-layers \
        --crossout-DNP-footprints-on-fab-layers --exclude-value --mode-single -o "$out/doc/assembly_front_$v.pdf" "$pcb"
    kicad-cli pcb export pdf --variant "$v" --layers B.Fab,Edge.Cuts --mirror --sketch-pads-on-fab-layers \
        --crossout-DNP-footprints-on-fab-layers --exclude-value --mode-single -o "$out/doc/assembly_back_$v.pdf" "$pcb"
done

echo "== Done"
find "$out" -type f | sort | sed "s|$out/||"
