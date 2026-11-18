#!/usr/bin/env python3
"""Footprint of the display: writes lib/footprints/WPT_Display.pretty/TFT_0.96in_80x160_FPC13_P0.7mm_Folded.kicad_mod
(run inside hardware/kicad/WPT-TX-DISPLAY).

0.96 inch IPS TFT, 80 x 160, ST7735S, with a flex tail of 13 contacts on 0.7 mm pitch that is soldered to the board.
The tail leaves the module at one short edge, is folded back under the module and soldered there, so the lands lie
under the module. Three parts share this tail and its pin table (drawings read 2026-11-17):

                                   module (mm)             tail end, folded,     contact   fold beyond
                                                           from the module edge  width     the module
  Wisevision N096-1608TBBIG11-H13  13.5 x 27.95 x 1.5      13.3 +/- 0.5          0.35      0.8 max
  Midas MDT0096A2IS-SPI            13.3 x 27.948 x 1.4     13.88 +/- 0.5         0.4       1 max
  Focus LCDs E096GA-SW500-N        same drawing as Midas

Common to all: 13 contacts, pitch 0.7 (8.4 over all), contacts 2 mm long from the tail end, tail end 12.4 wide and
centred on the module, two holes R0.5 in the tail 10.4 apart and 4.0 from its end. Seen from the display side with
the tail at the bottom, contact 1 is on the right.

Origin: centre of a Wisevision module; the fold is at +y. What fixes the position at assembly is the tail (its two
holes over the two circles of the silkscreen), not the module: a Midas or Focus module then lies 0.58 mm further
towards +y, which the courtyard allows for.

Lands: 0.4 x 4.0 mm. The contacts cover the 2 mm from y = 0.675 to 2.675; the lands go 1.5 mm further (to -0.825),
where the soldering iron heats them, and 0.5 mm beyond the other end. No paste: the tail is soldered by hand after
the board is assembled. The zone never joins a land directly (the two ground lands have their own vias), so all
lands take the same heat. The back of the module is a metal frame: nothing bare may lie under it but these lands,
and they are covered with polyimide tape before the module is folded over.
"""
import os

NAME = 'TFT_0.96in_80x160_FPC13_P0.7mm_Folded'
W, L = 13.5, 27.95                       # module (Wisevision)
TAIL_END = L / 2 - 13.3                  # y of the tail end: 0.675
PITCH, N = 0.7, 13
LAND_W, LAND_L = 0.4, 4.0
LAND_Y = TAIL_END + 2.0 - LAND_L / 2 + 0.5        # centre of the lands: 1.175
HOLE_Y, HOLE_X = TAIL_END + 4.0, 5.2
SHIFT, FOLD = 0.58, 1.0                  # Midas / Focus: module further towards +y, and its fold
AA = (10.8, 21.7, 1.7)                   # active area: width, height, distance from the edge opposite to the tail

out = []


def f(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if abs(v) > 1e-9 else '0'


def prop(name, value, y, layer, hide=False, size=1.0):
    out.append('\t(property "%s" "%s"\n\t\t(at 0 %s 0)\n\t\t(layer "%s")%s\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size %s %s)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)'
               % (name, value, f(y), layer, '\n\t\t(hide yes)' if hide else '', f(size), f(size)))


def line(a, b, layer, w):
    out.append('\t(fp_line\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "%s")\n\t)'
               % (f(a[0]), f(a[1]), f(b[0]), f(b[1]), f(w), layer))


def rect(a, b, layer, w):
    out.append('\t(fp_rect\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n\t\t(layer "%s")\n\t)'
               % (f(a[0]), f(a[1]), f(b[0]), f(b[1]), f(w), layer))


def circle(c, r, layer, w):
    out.append('\t(fp_circle\n\t\t(center %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n\t\t(layer "%s")\n\t)'
               % (f(c[0]), f(c[1]), f(c[0] + r), f(c[1]), f(w), layer))


def text(s, at, layer, size=1.0, thick=0.15):
    out.append('\t(fp_text user "%s"\n\t\t(at %s %s 0)\n\t\t(layer "%s")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size %s %s)\n\t\t\t\t(thickness %s)\n\t\t\t)\n\t\t)\n\t)'
               % (s, f(at[0]), f(at[1]), layer, f(size), f(size), f(thick)))


out.append('(footprint "%s"\n\t(version 20260206)\n\t(generator "pcbnew")\n\t(generator_version "10.0")\n\t(layer "F.Cu")' % NAME)
out.append('\t(descr "0.96 inch IPS TFT 80 x 160 with ST7735S: Wisevision N096-1608TBBIG11-H13, Midas MDT0096A2IS-SPI, Focus LCDs E096GA-SW500-N. '
           'Module 13.5 x 27.95 x 1.5 mm, flex tail with 13 contacts on 0.7 mm pitch folded back under the module and soldered to the board. '
           'Origin: centre of the module; the tail folds round the edge at +y. Seen from above with that edge at the bottom, contact 1 is on the right. '
           'Solder the tail first (its two holes over the two circles), cover the joints with polyimide tape, then fold the module over. '
           'The back of the module is a metal frame: no bare copper under it")')
out.append('\t(tags "TFT IPS 0.96 ST7735S FPC")')
prop('Reference', 'REF**', -L / 2 - 1.2, 'F.SilkS')
prop('Value', NAME, L / 2 + SHIFT + FOLD + 1.2, 'F.Fab')
prop('Datasheet', '', 0, 'F.Fab', hide=True, size=1.27)
prop('Description', '', 0, 'F.Fab', hide=True, size=1.27)
out.append('\t(attr smd exclude_from_pos_files)\n\t(duplicate_pad_numbers_are_jumpers no)')

# F.Fab: the module, and the tail as it lies under it
rect((-W / 2, -L / 2), (W / 2, L / 2), 'F.Fab', 0.1)
text('${REFERENCE}', (0, -4.0), 'F.Fab')
TW, NECK = 12.4 / 2, 9.2 / 2                              # half widths of the tail end and of its neck
tail = [(-TW, TAIL_END), (TW, TAIL_END), (TW, TAIL_END + 5.0), (NECK, TAIL_END + 5.0), (NECK, L / 2 + 0.8), (-NECK, L / 2 + 0.8),
        (-NECK, TAIL_END + 5.0), (-TW, TAIL_END + 5.0)]
for a, b in zip(tail, tail[1:] + tail[:1]):
    line(a, b, 'F.Fab', 0.1)
text('tail folded under', (0, TAIL_END + 7.0), 'F.Fab', 0.6, 0.1)
# Dwgs.User: what one looks at
rect((-AA[0] / 2, -L / 2 + AA[2]), (AA[0] / 2, -L / 2 + AA[2] + AA[1]), 'Dwgs.User', 0.1)
text('active area 10.8 x 21.7', (0, -L / 2 + AA[2] + 2.0), 'Dwgs.User', 0.6, 0.1)

# silkscreen: where the tail goes (its end, its two holes, contact 1) and the long edges of the module.
# No marks at the short edges: at one of them the board ends 0.25 mm beyond the module.
for sx in (-1, 1):
    line((sx * TW, TAIL_END), (sx * (TW - 1.3), TAIL_END), 'F.SilkS', 0.12)
    circle((sx * HOLE_X, HOLE_Y), 0.5, 'F.SilkS', 0.12)
    for y0 in (-L / 2 + 1.6, L / 2 - 3.6):
        line((sx * (W / 2 + 0.2), y0), (sx * (W / 2 + 0.2), y0 + 2.0), 'F.SilkS', 0.12)
text('1', (PITCH * (N - 1) / 2 + 1.35, LAND_Y + 0.8), 'F.SilkS', 0.8, 0.15)
rect((-W / 2 - 0.25, -L / 2 - 0.25), (W / 2 + 0.25, L / 2 + SHIFT + FOLD + 0.05), 'F.CrtYd', 0.05)

for k in range(1, N + 1):
    x = PITCH * (N - 1) / 2 - PITCH * (k - 1)             # contact 1 at +4.2
    out.append('\t(pad "%d" smd rect\n\t\t(at %s %s)\n\t\t(size %s %s)\n\t\t(layers "F.Cu" "F.Mask")\n\t\t(zone_connect 0)\n\t)'
               % (k, f(x), f(LAND_Y), f(LAND_W), f(LAND_L)))
out.append('\t(embedded_fonts no)\n)\n')

path = os.path.join('lib', 'footprints', 'WPT_Display.pretty', NAME + '.kicad_mod')
with open(path, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(out))
print('written', path)
