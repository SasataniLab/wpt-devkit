#!/usr/bin/env python3
"""One BOM line per manufacturer part number, in the column layout of PCBWay's assembly BOM.

usage: bom_pcbway.py PARTS.csv PLACEMENT_ALL.csv PLACEMENT_SMD.csv OUT.csv

PARTS.csv          one row per fitted part: Ref, Value, Footprint, Manufacturer, MPN, Description, Note
                   (fab/export.sh writes it with `kicad-cli sch export bom`, DNP parts excluded)
PLACEMENT_ALL.csv  kicad-cli position file with every placed part
PLACEMENT_SMD.csv  the same with --smd-only; a part that is in the first file but not in this one is through-hole

The schematic export groups by value and footprint, so one part number can appear on several lines when the libraries
name the same part differently ("10k" in Resistor_SMD and "10kF" in yageo). An assembler buys by part number, so this
script groups by part number alone and lists every designator once. Parts without a part number are grouped by value and
footprint and marked; the script stops with an error if a fitted part has neither a part number nor a placement.
"""
import csv
import re
import sys

parts_csv, pos_all_csv, pos_smd_csv, out_csv = sys.argv[1:5]

# footprint -> package name an assembler recognises
PACKAGE = {
    'C_0402_1005Metric': '0402', 'R_0402_1005Metric': '0402', 'GRM15': '0402', 'R_0402': '0402',
    'GRM18': '0603', 'R_0603': '0603', 'BLM18': '0603',
    'GRM21': '0805', 'GRM31': '1206', 'R_1206': '1206', 'GRM32': '1210',
    'LQFP-64_10x10mm_P0.5mm': 'LQFP-64 10x10 mm, 0.5 mm pitch',
    'SOT-23-6': 'SOT-23-6', 'microchip_SOT23-5LD-PL-1': 'SOT-23-5', 'SOT-353_SC-70-5_Diodes': 'SOT-353 (SC-70-5)',
    'SOT-223-3_TabPin2': 'SOT-223', 'SOD-123FA_OnSemi': 'SOD-123FA', 'SOD-323': 'SOD-323',
    'SOD-523F_STMicroelectronics': 'SOD-523', 'SOD-523F_Diodes': 'SOD-523',
    'Texas_S-PWSON-N10_ThermalVias': 'WSON-10 4x4 mm (DPR)', 'Texas_S-PDSO-G8': 'VSSOP-8 (DCU)',
    'QFN-16-1EP_3x3mm_Pitch0.5mm_Semtech': 'QFN-16 3x3 mm', 'DFN-10-1EP_3x3mm_Pitch0.5mm_microchip_9Q': 'DFN-10 3x3 mm',
    'TSSOP-14_4.4x5mm_P0.65mm': 'TSSOP-14', 'Siliconlabs_MSOP-10_3x3mm_Pitch0.5mm': 'MSOP-10',
    'Crystal_SMD_SeikoEpson_FA128-4Pin_2.0x1.6mm': '2.0 x 1.6 mm, 4 pads', 'FA-238': '3.2 x 2.5 mm, 4 pads',
    'EPC2007C': 'LGA 1.7 x 1.1 mm (bumped die)', 'EPC2038': 'BGA 0.9 x 0.9 mm (bumped die)',
    'PinHeader_1x02_P2.54mm_Vertical': 'pin header 1x02, 2.54 mm', 'PinHeader_1x04_P2.54mm_Vertical': 'pin header 1x04, 2.54 mm',
    'PinHeader_1x10_P2.54mm_Vertical': 'pin header 1x10, 2.54 mm', 'PinHeader_1x12_P2.54mm_Vertical': 'pin header 1x12, 2.54 mm',
    'FTSH-107-01-L-D-K_2x07_P1.27mm_Vertical': 'header 2x07, 1.27 mm, keyed shroud',
    'USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal': 'USB-C receptacle, 16 pads, top mount',
    'RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm': 'rotary encoder, vertical, 20 mm shaft',
    'SW_E-Switch_EG2219_DPDT_Angled': 'slide switch DPDT, right angle',
    'NR5040': '5.0 x 5.0 mm', '2929SQ': '7.5 x 7.2 mm air core',
}


def natural(ref):
    m = re.match(r'([A-Za-z]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def placed(path):
    with open(path, newline='', encoding='utf-8') as f:
        return {r['Ref']: r for r in csv.DictReader(f)}


pos_all, pos_smd = placed(pos_all_csv), placed(pos_smd_csv)
with open(parts_csv, newline='', encoding='utf-8') as f:
    parts = list(csv.DictReader(f))

groups, order = {}, []
problems = []
for p in sorted(parts, key=lambda r: natural(r['Ref'])):
    ref = p['Ref']
    mpn = p['MPN'].strip()
    fp = p['Footprint'].split(':')[-1]
    if ref not in pos_all:
        problems.append('%s is in the BOM but not in the placement file' % ref)
    key = mpn if mpn else ('', p['Value'], fp)
    if key not in groups:
        groups[key] = []
        order.append(key)
    groups[key].append(p)
if problems:
    sys.exit('\n'.join(problems))

rows = []
for n, key in enumerate(order, 1):
    g = groups[key]
    refs = [p['Ref'] for p in g]
    fps = sorted({p['Footprint'].split(':')[-1] for p in g})
    pkgs = sorted({PACKAGE.get(x, x) for x in fps})
    kinds = {'SMD' if r in pos_smd else 'THT' for r in refs}
    values = sorted({p['Value'] for p in g}, key=len)
    desc = sorted({p['Description'] for p in g if p['Description'] and p['Description'] != '~'}, key=len)
    makers = sorted({p['Manufacturer'].strip() for p in g if p['Manufacturer'].strip()})
    notes = sorted({p['Note'].strip() for p in g if p.get('Note', '').strip()})
    mpn = key if isinstance(key, str) else ''
    if not mpn:
        notes.insert(0, 'no manufacturer part number in the design data')
    if len(makers) > 1 or len(pkgs) > 1 or len(kinds) > 1:
        sys.exit('one part number, different manufacturers / packages / mounting: %s %s %s %s' % (mpn, makers, pkgs, kinds))
    kind_word = {'C': 'capacitor', 'R': 'resistor', 'L': 'inductor', 'FB': 'ferrite bead', 'D': 'diode'}.get(re.match(r'[A-Za-z]+', refs[0]).group(0), '')
    generic = {'Unpolarized capacitor', 'Resistor', ''}
    text = ' / '.join(values)
    if desc and desc[0] not in generic and desc[0] not in values:
        text += ' - ' + desc[0]
    elif kind_word and text != mpn:
        text = kind_word + ' ' + text
    rows.append([n, ','.join(refs), len(refs), makers[0] if makers else '', mpn, text, pkgs[0], kinds.pop(), '; '.join(notes)])

with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Item #', 'Designator', 'Qty', 'Manufacturer', 'Mfg Part #', 'Description / Value', 'Package/Footprint', 'Type', 'Your Instructions / Notes'])
    w.writerows(rows)
n_parts = sum(r[2] for r in rows)
print('%s: %d lines, %d parts (%d surface-mount, %d through-hole), %d lines without a part number'
      % (out_csv.split('/')[-1], len(rows), n_parts, sum(r[2] for r in rows if r[7] == 'SMD'), sum(r[2] for r in rows if r[7] == 'THT'),
         sum(1 for r in rows if not r[4])))
