#!/bin/sh
# Build the fabrication / assembly package for WPT-01-TRANSMITTER with kicad-cli (KiCad 10).
#
#   fab/export.sh            -> writes everything into fab/out/ for the HRTIM build, the one that is ordered. It is also
#                               the default population of the schematic and of the board (since 2026-11-18)
#   fab/export.sh all        -> the same for both variants (HRTIM and Legacy)
#   fab/export.sh Legacy     -> the variant "Legacy" only (the fall-back population: the 2020 drive from the Si5351)
#
# Output:
#   out/gerber/              Gerbers for the 4 copper layers, mask, paste, silk, edge + Excellon drill (PTH / NPTH) and drill map
#   out/assembly/<variant>/  BOM and pick-and-place files (all parts / surface-mount only), DNP parts excluded.
#                            bom_<variant>_pcbway.csv is the one to send: one line per manufacturer part number
#                            (fab/bom_pcbway.py)
#   out/doc/                 schematic PDF and front/back assembly drawings of the variant (parts not fitted are crossed out)
#
# Only one variant is written by default so that files of the other population cannot be sent by mistake: the two
# differ in 25 parts and must not be fitted together.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
prj=$(dirname "$here")
pcb="$prj/WPT-01-TRANSMITTER.kicad_pcb"
sch="$prj/WPT-01-TRANSMITTER.kicad_sch"
out="$here/out"
case "${1:-HRTIM}" in
    all) variants="Legacy HRTIM" ;;
    HRTIM|Legacy) variants="${1:-HRTIM}" ;;
    *) echo "usage: $0 [HRTIM|Legacy|all]" >&2; exit 2 ;;
esac

rm -rf "$out"
mkdir -p "$out/gerber" "$out/doc"

# What a file shows without a variant chosen (the GUI, a plug-in, a third-party BOM tool) must be what is ordered:
# the default population and the variant "HRTIM" have to list the same parts, in the schematic and on the board.
echo "== Default population = HRTIM build?"
chk="$out/.default_check"; mkdir -p "$chk"
for v in default HRTIM; do
    if [ "$v" = default ]; then opt=""; else opt="--variant $v"; fi
    kicad-cli sch export bom $opt --exclude-dnp --fields 'Reference' --labels 'Ref' --group-by 'Reference' -o "$chk/sch_$v.csv" "$sch" > /dev/null
    kicad-cli pcb export pos $opt --exclude-dnp --format csv --units mm --side both -o "$chk/pcb_$v.csv" "$pcb" > /dev/null
done
if ! cmp -s "$chk/sch_default.csv" "$chk/sch_HRTIM.csv" || ! cmp -s "$chk/pcb_default.csv" "$chk/pcb_HRTIM.csv"; then
    echo "The default population differs from the HRTIM build (schematic or board). Nothing exported." >&2
    exit 1
fi
rm -rf "$chk"

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
    python3 "$here/bom_pcbway.py" "$d/parts_$v.csv" "$d/placement_$v.csv" "$d/placement_${v}_smd.csv" "$d/bom_${v}_pcbway.csv" "$here/bom_extra.csv"
done

echo "== Documents"
# One set per variant, named after it. (Until 2026-11-18 the default population was the Legacy one, and drawings made
# without --variant crossed out the parts the HRTIM BOM lists.)
for v in $variants; do
    kicad-cli sch export pdf --variant "$v" -o "$out/doc/schematic_$v.pdf" "$sch"
    kicad-cli pcb export pdf --variant "$v" --layers F.Fab,Edge.Cuts --sketch-pads-on-fab-layers \
        --crossout-DNP-footprints-on-fab-layers --exclude-value --mode-single -o "$out/doc/assembly_front_$v.pdf" "$pcb"
    kicad-cli pcb export pdf --variant "$v" --layers B.Fab,Edge.Cuts --mirror --sketch-pads-on-fab-layers \
        --crossout-DNP-footprints-on-fab-layers --exclude-value --mode-single -o "$out/doc/assembly_back_$v.pdf" "$pcb"
done

echo "== Done"
find "$out" -type f | sort | sed "s|$out/||"
