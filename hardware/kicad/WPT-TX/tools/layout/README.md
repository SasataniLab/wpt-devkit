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

The third pass is the mechanical revision of 2026-11-14 (board 70 x 80 mm, mounting holes on a 5 mm grid, tracks on 0 / 45 / 90 degrees).
`rev2.sh` holds the exact command sequence.

| Step | Script | What it does |
|---|---|---|
| 19 | `../schematic/edit_sch2.py` | Schematic: C16 (10 nF at PA0, ADC_VDC), net label BOOT0, J301 becomes 1x10 with +3V3 and GND on pins 9 / 10 |
| 20 | `mech2.py IN OUT MCU.kicad_sch` | Outline 10 mm more at the top and 5 mm more at the bottom, four M3 holes 5 mm from the edges, USB block to the new top edge, J301 on the 2.54 mm grid of J2, footprint for C16, the net name BOOT0. Then `ripreg.py` for the 20 nets that touch what moved |
| 21 | `mech3.py IN OUT` | Obsolete hand copper out, J3 to the west edge, the eight resistors of J301 to the top side in one row north of it, the area under the slide switch as a band under the walls of its metal cover (four rectangles of one name) with silkscreen bars, the two solder-mask lines of the old top edge out |
| 22 | `phys6.py IN REG OUT` | East side of the MCU and the two headers by hand: the pins that go north leave as a comb on the top side without vias (HV_SW_STATE, EEV1, EEV2, SWCLK, SWDIO, then the USB pair), the back side east of the MCU carries only the two divider-tap lines to J301, GPIO_VUSB_SENSE crosses both on In2. The reasoning is in its header |
| 23 | `restore_old.py OLD BOARD REG NET[=OLDNAME]...`, `after_restore.py`, `hv_en_via.py` | The routes of the nets whose ends did not move come back from the previous board; pieces that now collide (DRC: clearance, short, keep-out) are removed again. Routing those nets from nothing gave longer routes than before |
| 24 | `fillin.py` for `NRST:sn SCL_3.3V:s SDA_3.3V:s`, `cleanup.py` | The three connections that are really new |
| 25 | `smooth45.py BOARD REG BASE [--only NET,...]`, `cleanup.py` | Every run of track that is not copper of the base board is laid out again on 0 / 45 / 90 degrees with as few segments as the clearances allow (farthest reachable vertex by one straight piece or one dog-leg, no turn sharper than 90 degrees). KiCad's DRC decides: a net that shows a new violation gets its old copper back. `S45_MARGIN` sets the margin on the raster (default 0.03 mm; 0 for a second try on the nets that kept an off-angle piece) |
| 26 | `silklabel.py IN OUT`, `silkfix.py` (as step 17, `--also C16`) | Pin functions of J2 / J3 / J4 / J301 and the name of the BOOT0 jumper on the top silkscreen; reference designators of the added parts |
| 27 | `finalize.py` (as step 10) | Into the project; the custom rule for vias under the slide switch is in `WPT-01-TRANSMITTER.kicad_dru` |

Third revision (2026-11-14):

| Step | Script | What it does |
|---|---|---|
| 28 | `../schematic/edit_sch3.py`, `../schematic/edit_sch4.py` (in the project directory) | J3 becomes the ST debug connector STDC14 (Samtec FTSH-107-01-L-D-K, footprint in `lib/footprints/Connector_Samtec_FTSH.pretty`); the sense path to the comparators is fitted in variant HRTIM (R343 / R344 100 ohm, C338 / C339 0.5 pF) |
| 29 | `mech4.py IN OUT ROOT.kicad_sch` | Outline corners as arcs of 5 mm radius around the mounting holes; the new J3 at the west edge with SWDIO / SWCLK / NRST laid in by hand (the old run passed under the washer of the mounting hole) |
| 30 | `silkfix.py` (as step 17, `--also C16,J3`), `finalize.py` | Reference designators, then into the project |
| 31 | `mech5.py IN OUT` (IN = the project board) | Three tracks out of the reach of the hardware on the holes (`holechk.py` found them), three fiducials per side |
| 32 | `finalize.py`, `lencheck.py`, `off45.py`, `holechk.py`, `nearchk.py` | Into the project, then the checks |
| 33 | `../schematic/edit_sch5.py` | BOM clean-up, nothing electrical: test points out of BOM and placement, one spelling per manufacturer, part numbers as the manufacturers write them, replacements for the two parts that are no longer made, part numbers for the pin headers, assembly notes. The jumper shunts of the two supply selectors are in `fab/bom_extra.csv` |
| 34 | `../schematic/edit_sch6.py`, `mech6.py IN OUT` | Changes from the pre-order review: 560 ohm at the LM5113 inputs, 100 nF bootstrap capacitors, 0.2 W divider resistors, 2.2 k for the enable LED, encoder symbol with frame pins; on the board the two frame lugs of SW1 get the GND net |
| 35 | `silknote.py IN OUT`, `finalize.py` | "3.3 V MAX" notes for the headers; into the project. `finalize.py` now takes `../schematic/pcb_side.py` (with `sx.py`) as its third argument: it carries values, part numbers, assembly notes, datasheet links and the variant flags from the netlist to the board |

Fourth revision (2026-11-14):

| Step | Script | What it does |
|---|---|---|
| 36 | `../schematic/edit_sch7.py` (in the project directory) | The virtual COM port of J3 (pins 13 / 14) to USART1, R12 560 ohm in the receive line, J4 no longer fitted |
| 37 | `mech7.py IN OUT NETLIST` (IN = the project board, NETLIST = `kicad-cli sch export netlist --format kicadsexpr`) | The two lines through the slide switch: transmit on In2 between the pin columns, receive on the back west of them; one ground stitching via out of the way |
| 38 | `finalize.py`, the checks | Into the project |
| 39 | `../schematic/edit_sch8.py` | Fast comparators U308 / U309 (TLV3601) with threshold from PB11, capacitor-compensated dividers, test pads; J301, R333 and TP223 removed; net of PB11 renamed |
| 40 | `mech8.py IN OUT NETLIST` | Placement and routing of step 39: the top strip where J301 stood, C340 / C341 and R343 at the dividers, silkscreen legends |
| 41 | `finalize.py`, the checks, `../../fab/export.sh` | Into the project; fabrication data |

`newfp.py` holds what `mech7.py` / `mech8.py` share: footprints of new symbols straight from the netlist (symbol link, sheet, value, description, pad nets), tracks, vias, removals. With pcbnew, `board.Remove()` of a track makes later `FootprintLoad()` calls fail, so removals are collected and carried out at the end (`flush`).

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
| `lencheck.py BOARD [REF...] [--min RATIO]` | Every signal net on the MCU and the headers: routed length against the shortest possible on 0 / 45 / 90 degrees (octilinear spanning tree over its pads), vias, length on In2, segments off those angles |
| `off45.py BOARD BASE` | The segments that are not on 0 / 45 / 90 degrees and are not copper of the base board |
| `freemap.py BOARD OUT.png [x0 y0 x1 y1]` | Where the board is free of parts on both sides (where a through-hole part could still go) |
| `holechk.py BOARD [R_COPPER R_PART]` | Tracks, vias and pads of other nets within the reach of a washer / standoff / screw head around every mounting hole (M3: 3.6 mm from the centre, smaller holes: drill / 2 + 2 mm). DRC only checks the clearance to the pad |
| `nearchk.py BOARD` | Assembly clearances DRC does not look at: SMD pads beside the solder joints of through-hole parts (< 1 mm), courtyards near the board edge, courtyards that touch |
| `fidspot.py BOARD x,y[,F\|B] ...` | Nearest track, via, pad, courtyard and silkscreen to a spot, for placing fiducials |
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
- The router's own output is a staircase on the 0.05 mm raster. `smooth45.py` turns it into long 0 / 45 / 90 degree pieces afterwards (`smooth.py`, used before, straightened to any angle).
- `pcbnew`'s `Remove()` leaves the Python bindings unstable in KiCad 10.0.8 (board loads start to fail in the same process). Rip-up is therefore done by deleting the track / via blocks from the board file itself (`nego.rip_text`).
