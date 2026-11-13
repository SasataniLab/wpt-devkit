#!/usr/bin/env python3
"""Re-create the proven legacy routes (outside the re-worked area) for nets that used to reach the Arduino sockets."""
import json, sys
import pcbnew
MM = 1e6
def V(x, y): return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
board = pcbnew.LoadBoard(sys.argv[1])
lid = {board.GetLayerName(i): i for i in board.GetEnabledLayers().Seq()}
rem = json.load(open(sys.argv[3]))
RENAME = {'/WPT-01-TRANSMITTER-POWER/HVDCDC_EN': '/HV_EN_SW'}
WANT = {'/WPT-01-TRANSMITTER-POWER/ADC_VDC', '/WPT-01-TRANSMITTER-POWER/HVDCDC_EN', '/WPT-01-TRANSMITTER-POWER/~{WLAT}',
        '/WPT-01-TRANSMITTER-POWER/~{ALERT}'}
YMIN = 164.0
n = 0
for t in rem['tracks']:
    if t['net'] not in WANT or t['width'] > 0.5:
        continue
    if min(t['start'][1], t['end'][1]) < (163.8 if 'ALERT' in t['net'] else YMIN):
        continue
    if 'WLAT' in t['net'] and min(t['start'][1], t['end'][1]) < 168.0:
        continue          # would run under the BOOT0 jumper now
    net = RENAME.get(t['net'], t['net'])
    tr = pcbnew.PCB_TRACK(board)
    tr.SetStart(V(*t['start'])); tr.SetEnd(V(*t['end'])); tr.SetWidth(int(t['width'] * MM)); tr.SetLayer(lid[t['layer']])
    tr.SetNet(board.FindNet(net)); board.Add(tr); n += 1
for v in rem['vias']:
    if v['net'] in WANT and v['pos'][1] >= (163.8 if 'ALERT' in v['net'] else YMIN):
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(V(*v['pos'])); via.SetWidth(int(v['size'] * MM)); via.SetDrill(int(v['drill'] * MM))
        via.SetLayerPair(lid['F.Cu'], lid['B.Cu']); via.SetNet(board.FindNet(RENAME.get(v['net'], v['net']))); board.Add(via); n += 1
pcbnew.SaveBoard(sys.argv[2], board)
print('restored', n, 'legacy items')
