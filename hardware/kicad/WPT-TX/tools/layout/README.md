# Layout scripts used for the STM32 MCU/UI section (2026-11-13)

These are the scripts that placed and routed the STM32 section of `WPT-01-TRANSMITTER.kicad_pcb`.
They are kept as a record of how the layout was produced and so that a step can be re-run after a change.
They are not a general-purpose autorouter. All of them use the `pcbnew` Python module and `kicad-cli` of KiCad 10.

| Script | What it does |
|---|---|
| `pcbdump.py BOARD OUT.json` | Dumps footprints, pads, tracks, vias and zones to JSON (mm) |
| `pcbview.py MODEL.json OUT.png --win x0 y0 x1 y1 ...` | Renders the JSON model with mm axes, for checking coordinates |
| `netq.py NETLIST comp|net|find|dump ...` | Queries a KiCad s-expression netlist (pin to net, net to pins, diff dumps) |
| `place_v2.py IN OUT` | Placement table for the new parts, the rigid move of the I2C level-shifter cluster, removal of copper left over from the Arduino sockets, the In2 +3V3 plane outline, the leg-B HRTIM net swap |
| `restore_legacy.py IN OUT removed.json` | Re-creates the proven legacy routes (ADC_VDC, HV enable, WLAT, ALERT) outside the re-worked area; `removed.json` is the list of tracks present in the legacy board but deleted with the Arduino sockets |
| `router.py` | Grid router: the board is rasterised at 0.05 mm, copper of other nets is an obstacle, a track centre keeps clearance + half width from it, a via keeps clearance + radius on every layer. A* over F.Cu / B.Cu with through vias, escape lanes reserved in front of every MCU pad, soft obstacles for rip-up |
| `do_route.py BOARD passes rip_passes [--manual]` | Driver: hand-routed USB / VBUS / CC section first, then DRC -> list of unconnected pairs -> route, repeated; a blocked net may rip up copper this router added earlier |
| `post_route.py BOARD` | Plane stubs for SMD pads that only hang on a pour, stitching vias for isolated ground pour islands, solid connection for starved thermals, removal of dangling stubs |

Order used: `place_v2.py` -> `restore_legacy.py` -> `do_route.py ... --manual` -> `post_route.py`, then the board-side data sync from the schematic netlist (DNP flags, manufacturer fields, variants).

Limits worth knowing before trusting the result:

- Clearances are checked by KiCad DRC after every pass; the router itself is conservative by about 0.07 mm.
- Tracks are 0.2 mm (USB 0.3 mm), vias 0.6 / 0.3 mm. Nothing is length- or impedance-matched except the hand-routed USB pair, which is simply kept short and parallel.
- The router has no notion of signal quality. The four gate signals, the switch-node sense lines and the crystal were checked by eye afterwards, not optimised.
