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

Steps 1 to 10 gave a connected, rule-clean board in which everything except the MCU fan-out and the USB section was auto-routed.
The second pass replaced the auto-routed copper of the nets that matter by hand-made copper and checked the rest:

| Step | Script | What it does |
|---|---|---|
| 11 | `stripnets.py BOARD NET...` | Removes all copper of the nets that are laid out again (gate signals, comparator and sense lines, and the slow nets in their way) |
| 12 | `phys1.py IN OUT`, `phys2.py IN OUT`, `phys3.py IN OUT` | Gate signals (top side across the split of the inner power layer, one via, back side under the +5V plane, each leg a matched pair), comparator lines, compact switch-node dividers of leg B and leg A, R343 at the MCU end of the leg-A sense line. The reasoning is in the header of `phys1.py` |
| 13 | `fillin.py BOARD REG.json NET[:opts] ...` | Routes the open connections of the named nets around the hand-made copper. Options: `b` back side only, `v` vias expensive, `i` inner layer allowed, `r` may push auto-routed nets aside (they are routed again), `k` stay out from under the MCU and away from the crystal, `s` keep a distance from the analog sense lines, `n` accept a legal path only near the straight line (with `r`: rather push others aside than go round the board) |
| 14 | `phys4.py IN REG OUT REG` | Leg-A sense line straight up the gap between the two gate-signal pairs (leg-B pair and the legacy clock move 0.8 mm east to open that gap) |
| 15 | `usbfix.py IN REG OUT REG`, then `fillin.py` for `SCL_3.3V SWDIO:s` | Rule area on F.Cu under the metal shell of the USB-C receptacle, VBUS and D- links moved under its plastic housing; the two auto-routed nets that ran under the shell are routed again |
| 16 | `trimtails.py`, `tidy1.py`, `cleanup.py`, `post_route.py`, `planefix.py`, `smooth.py`, `tidy2.py`, `tidy3.py` | Clean-up as in steps 7 and 8, plus three local corrections: SDA lane extended instead of a second track along the plane edge, SWDIO back from the board edge, HRTIM1_EEV1 away from the leg-A sense line |
| 17 | `finalize.py` (as step 10), then `silkfix.py IN OUT added_refs.json --also TP214,TP215,TP217,X301 --hide-if-stuck TP217` | Reference designators of the added parts set to 0.8 x 0.7 mm and moved to the nearest free place beside their part |
| 18 | `phys5.py IN REG OUT REG`, `fillin.py` for `'Net-(J1-Pin_1):i'`, clean-up and `finalize.py` again | Display SPI: MOSI straight to the MCU through a back-side passage it shares with HRTIM1_FLT3 (86 mm became 17.5 mm); the BOOT0 jumper net, which lost its place, is routed again |

`ripreg.py BOARD REG.json NET...` takes the auto-routed copper of a net out again (hand-made copper stays), for a new `fillin.py` run.
`stub.py BOARD REG.json NET LAYER x,y x,y ...` adds one hand-made track. The fill-in router cannot leave a 0.5 mm pitch pad on its own when the escape track ends inside the pad row; extend the escape by 0.6 mm with this first.

## Checks

| Script | Question it answers |
|---|---|
| `drcsum.py BOARD [--all]` | KiCad DRC summary (zones refilled). Copy the project's `.kicad_pro` **and** `.kicad_dru` next to a board copy first: without the `.kicad_dru` the USB-C locating pegs show up as six hole-clearance errors |
| `audit.py BOARD [REF]` | Every net on the MCU: length per layer, vias, which plane lies under the tracks, which nets run beside it closer than 0.3 mm |
| `netpath.py BOARD NET...` | The copper of a net as ordered chains with coordinates, and its neighbours within 0.45 mm |
| `refplane.py BOARD NET...` | Plane net under each track (F.Cu against In1, B.Cu against In2) and where it changes |
| `planegap.py BOARD [--min MM]` | Outer-layer tracks with no plane copper under them (clearance holes of vias and through-hole pads excluded) |
| `edgechk.py BOARD [MM]` | Tracks closer than a distance to the board outline |
| `cmpnets.py OLD NEW` | Nets whose length, via count or inner-layer length differ between two boards |
| `whyblocked.py BOARD REG.json NET` | For an open connection: which auto-routed nets the cheapest path would have to cross |
| `reach2.py BOARD REG.json NET x y L x y L OUT.png` | Flood fill from both ends of an open connection, with a picture of the two reachable areas |

Helpers: `router.py` (the grid router itself), `pcbdump.py` / `pcbview.py` (board to JSON, JSON to PNG with mm axes), `netq.py` (netlist queries), `win.py` / `win2.py` (list copper in a window).

## How the router works, and its limits

- The board is rasterised at 0.05 mm. Copper of other nets is an obstacle; a track centre keeps clearance + half width from it, a via keeps clearance + radius on every layer. The search is A* over F.Cu / B.Cu with through vias.
- Clearances are checked by KiCad DRC after every stage; the router itself is conservative by about 0.07 mm.
- Tracks are 0.2 mm (USB 0.3 mm, supply stubs 0.25 mm), vias 0.6 / 0.3 mm. Nothing is length- or impedance-matched except the hand-routed USB pair, which is simply kept short and parallel.
- Slow signals listed in `nego.py` (`SLOW`) may use the inner power layer In2, and only inside `router.INNER_BOXES` (the user-interface area west of the MCU). In1 is never touched.
- The router has no notion of signal quality beyond two penalties (`fillin.py` options `k` and `s`). The gate signals, the comparator and sense lines, the crystal and the USB pair are hand-made copper; the rest was not optimised and some of it takes detours.
- A rule area with "no tracks" on a signal layer is an obstacle for the router, so a keep-out drawn in KiCad is honoured.
- `pcbnew`'s `Remove()` leaves the Python bindings unstable in KiCad 10.0.8 (board loads start to fail in the same process). Rip-up is therefore done by deleting the track / via blocks from the board file itself (`nego.rip_text`).
