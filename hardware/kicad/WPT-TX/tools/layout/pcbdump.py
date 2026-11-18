#!/usr/bin/env python3
"""Dump a KiCad board to a JSON model (mm units) for analysis/rendering.

usage: pcbdump.py BOARD.kicad_pcb OUT.json
"""
import json
import sys

import pcbnew

MM = 1e-6


def mm(v):
    return round(v * MM, 4)


def pt(p):
    return [mm(p.x), mm(p.y)]


def layer_names(board, lset):
    return [board.GetLayerName(i) for i in lset.Seq()]


def poly_outlines(sps):
    out = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i)
        out.append([pt(o.CPoint(k)) for k in range(o.PointCount())])
    return out


def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    m = {'file': sys.argv[1]}
    m['copper_layers'] = [board.GetLayerName(i) for i in board.GetEnabledLayers().Seq() if pcbnew.IsCopperLayer(i)]
    bb = board.GetBoardEdgesBoundingBox()
    m['bbox'] = [mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())]

    # graphics (edge cuts etc.)
    m['drawings'] = []
    for d in board.GetDrawings():
        ln = board.GetLayerName(d.GetLayer())
        e = {'layer': ln, 'class': d.GetClass()}
        if d.GetClass() == 'PCB_SHAPE':
            e['shape'] = d.SHAPE_T_asString()
            e['start'] = pt(d.GetStart())
            e['end'] = pt(d.GetEnd())
            if d.GetShape() == pcbnew.SHAPE_T_ARC:
                e['mid'] = pt(d.GetArcMid())
                e['center'] = pt(d.GetCenter())
            if d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                e['center'] = pt(d.GetCenter())
                e['radius'] = mm(d.GetRadius())
            if d.GetShape() == pcbnew.SHAPE_T_POLY:
                e['poly'] = poly_outlines(d.GetPolyShape())
            e['width'] = mm(d.GetWidth())
        elif d.GetClass() in ('PCB_TEXT',):
            e['text'] = d.GetText()
            e['pos'] = pt(d.GetPosition())
        m['drawings'].append(e)

    m['footprints'] = []
    for fp in board.GetFootprints():
        bbx = fp.GetBoundingBox(False)
        try:
            cy = fp.GetCourtyard(pcbnew.F_CrtYd if not fp.IsFlipped() else pcbnew.B_CrtYd)
            cyb = cy.BBox()
            court = [mm(cyb.GetLeft()), mm(cyb.GetTop()), mm(cyb.GetRight()), mm(cyb.GetBottom())] if cy.OutlineCount() else None
        except Exception:
            court = None
        f = {
            'ref': fp.GetReference(), 'value': fp.GetValue(), 'fpid': fp.GetFPIDAsString(),
            'pos': pt(fp.GetPosition()), 'rot': fp.GetOrientationDegrees(),
            'side': 'B' if fp.IsFlipped() else 'F',
            'bbox': [mm(bbx.GetLeft()), mm(bbx.GetTop()), mm(bbx.GetRight()), mm(bbx.GetBottom())],
            'court': court,
            'dnp': bool(fp.IsDNP()), 'locked': bool(fp.IsLocked()),
            'path': fp.GetPath().AsString(), 'sheet': fp.GetSheetname(),
            'attrs': fp.GetAttributes(),
            'pads': [],
        }
        for pad in fp.Pads():
            sz = pad.GetSize(pcbnew.F_Cu) if hasattr(pad, 'GetSize') else None
            try:
                shape = pad.ShowPadShape(pcbnew.F_Cu)
            except Exception:
                shape = str(pad.GetShape(pcbnew.F_Cu))
            p = {
                'num': pad.GetNumber(), 'net': pad.GetNetname(), 'pos': pt(pad.GetPosition()),
                'size': [mm(sz.x), mm(sz.y)], 'rot': pad.GetOrientationDegrees(), 'shape': shape,
                'attr': pad.ShowPadAttr(), 'drill': mm(pad.GetDrillSize().x),
                'layers': [n for n in layer_names(board, pad.GetLayerSet()) if n.endswith('.Cu')],
                'pinfn': pad.GetPinFunction(),
            }
            bb2 = pad.GetBoundingBox()
            p['bbox'] = [mm(bb2.GetLeft()), mm(bb2.GetTop()), mm(bb2.GetRight()), mm(bb2.GetBottom())]
            f['pads'].append(p)
        m['footprints'].append(f)

    m['tracks'] = []
    m['vias'] = []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            m['vias'].append({'pos': pt(t.GetPosition()), 'size': mm(t.GetWidth(pcbnew.F_Cu)), 'drill': mm(t.GetDrillValue()),
                              'net': t.GetNetname(), 'layers': [board.GetLayerName(t.TopLayer()), board.GetLayerName(t.BottomLayer())],
                              'locked': bool(t.IsLocked())})
        elif t.GetClass() == 'PCB_ARC':
            m['tracks'].append({'start': pt(t.GetStart()), 'end': pt(t.GetEnd()), 'mid': pt(t.GetMid()), 'width': mm(t.GetWidth()),
                                'layer': board.GetLayerName(t.GetLayer()), 'net': t.GetNetname(), 'arc': True})
        else:
            m['tracks'].append({'start': pt(t.GetStart()), 'end': pt(t.GetEnd()), 'width': mm(t.GetWidth()),
                                'layer': board.GetLayerName(t.GetLayer()), 'net': t.GetNetname()})

    m['zones'] = []
    for z in board.Zones():
        zz = {
            'name': z.GetZoneName(), 'net': z.GetNetname(), 'layers': layer_names(board, z.GetLayerSet()),
            'priority': z.GetAssignedPriority(), 'rule_area': bool(z.GetIsRuleArea()),
            'outline': poly_outlines(z.Outline()),
            'min_width': mm(z.GetMinThickness()), 'clearance': mm(z.GetLocalClearance() or 0),
            'pad_conn': z.GetPadConnection(), 'filled': bool(z.IsFilled()),
            'thermal_gap': mm(z.GetThermalReliefGap()), 'thermal_spoke': mm(z.GetThermalReliefSpokeWidth()),
            'island_mode': z.GetIslandRemovalMode(),
        }
        if z.GetIsRuleArea():
            zz['no_tracks'] = bool(z.GetDoNotAllowTracks())
            zz['no_vias'] = bool(z.GetDoNotAllowVias())
            zz['no_pour'] = bool(z.GetDoNotAllowZoneFills())
            zz['no_pads'] = bool(z.GetDoNotAllowPads())
            zz['no_fp'] = bool(z.GetDoNotAllowFootprints())
        m['zones'].append(zz)

    json.dump(m, open(sys.argv[2], 'w'))
    print(f"layers={m['copper_layers']} bbox={m['bbox']} fps={len(m['footprints'])} tracks={len(m['tracks'])} vias={len(m['vias'])} zones={len(m['zones'])}")


if __name__ == '__main__':
    main()
