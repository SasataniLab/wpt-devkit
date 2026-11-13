# Layout scripts used for the STM32 MCU / UI section (2026-11-13 and 14)

These scripts placed and routed the STM32 section of `WPT-01-TRANSMITTER.kicad_pcb`.
They are kept as a record of how the layout was produced and so that a step can be re-run after a change.
They are not a general-purpose autorouter. All of them use the `pcbnew` Python module and `kicad-cli` of KiCad 10.
The board file in the repository is the result; nothing here has to be run to use it.

## Order that produced the board

| Step | Script | What it does |
|---|---|---|
| 1 | `place_v2.py IN OUT` | Placement table for the new parts, the rigid move of the I2C level-shifter cluster, removal of copper left over from the Arduino sockets, the In2 +3V3 plane outline, the leg-B HRTIM net swap |
| 2 | `restore_legacy.py IN OUT removed.json` | Re-creates the proven legacy routes (ADC_VDC, HV enable, WLAT, ALERT) outside the re-worked area; `removed.json` lists the tracks present in the legacy board but deleted with the Arduino sockets |
| 3 | `do_route.py BOARD 0 0 --manual` | Hand-routed USB-C / VBUS / CC section (the `manual()` function), kept as fixed copper |
| 4 | `fan.py IN OUT` | Hand-designed fan-out of the MCU: one escape per pin, supply vias beside the decoupling capacitors, the crystal, and the part moves that make room for it (C2, C10, C12, R1, R2) |
| 5 | `do_route.py BOARD 2 0 --planes-only --no-corridors` | Short stubs and vias for the remaining GND / +3V3 pads |
| 6 | `run_nego.sh BOARD 250 LOG` with `EXTRA=--inner` | `nego.py`: every open connection is routed in turn; when there is no legal path the connection is routed across copper this router added earlier, the nets it crossed are ripped up and queued again. Restarted until a round ends without a rip-up |
| 7 | `padfix.py`, `cleanup.py`, `trimtails.py` | Track ends that sit exactly on a pad edge are extended to the pad centre; dead-end copper is removed (every removal is checked against connectivity); tails beyond a junction are trimmed |
| 8 | `post_route.py`, `planefix.py`, `fix3.py` | Stitching vias for isolated ground pour pieces, solid connection for starved thermals, own via for every surface-mount supply pad that only hung on a pour, three local hand fixes (C15, C210, R338) |
| 9 | `improve.py BOARD REG.json 2 --inner` | Re-routes one net at a time with everything else in place and keeps the new route only when it is shorter |
| 10 | `finalize.py BOARD PROJECT_DIR PCB_SIDE_PY` | Board-side data sync from the schematic netlist (DNP flags, manufacturer fields, variants, values), board-only mounting holes, DRC with schematic parity |

Helpers: `router.py` (the grid router itself), `pcbdump.py` / `pcbview.py` (board to JSON, JSON to PNG with mm axes), `netq.py` (netlist queries), `win.py` (list copper in a window).

## How the router works, and its limits

- The board is rasterised at 0.05 mm. Copper of other nets is an obstacle; a track centre keeps clearance + half width from it, a via keeps clearance + radius on every layer. The search is A* over F.Cu / B.Cu with through vias.
- Clearances are checked by KiCad DRC after every stage; the router itself is conservative by about 0.07 mm.
- Tracks are 0.2 mm (USB 0.3 mm, supply stubs 0.25 mm), vias 0.6 / 0.3 mm. Nothing is length- or impedance-matched except the hand-routed USB pair, which is simply kept short and parallel.
- Slow signals listed in `nego.py` (`SLOW`) may use the inner power layer In2, and only inside `router.INNER_BOXES` (the user-interface area west of the MCU). In1 is never touched.
- The router has no notion of signal quality. The gate signals, the switch-node sense lines and the crystal were laid out or checked by hand, the rest was not optimised: auto-routed tracks consist of many short segments and some take detours.
- `pcbnew`'s `Remove()` leaves the Python bindings unstable in KiCad 10.0.8 (board loads start to fail in the same process). Rip-up is therefore done by deleting the track / via blocks from the board file itself (`nego.rip_text`).
