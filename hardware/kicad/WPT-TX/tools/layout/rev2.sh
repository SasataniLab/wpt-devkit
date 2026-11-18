#!/bin/sh
# The commands that turned the board of commit af98404 (70 x 65 mm) into the 70 x 80 mm revision of 2026-11-14.
# A record, like the other scripts here: the board in the repository is the result.
#
# usage: sh rev2.sh OLD.kicad_pcb OLD_REG.json BASE.kicad_pcb MCU.kicad_sch PROJECT_DIR
#   OLD        the board of commit af98404
#   OLD_REG    the list of auto-routed copper that belongs to it (written by nego.py / fillin.py; not kept in git)
#   BASE       the board the STM32 work started from (branch STM_wpt-tx): its copper is never re-shaped
#   MCU.kicad_sch, PROJECT_DIR   the schematic sheet with C16 and the KiCad project directory
# Run it in a scratch directory that holds a copy of these scripts; every stage writes a new board file.
set -e
OLD=$1; REG=$2; BASE=$3; SCH=$4; PRJ=$5
N=WPT-01-TRANSMITTER
prj() { cp "$PRJ/$N.kicad_pro" "$1.kicad_pro"; cp "$PRJ/$N.kicad_dru" "$1.kicad_dru"; }   # a board copy needs both beside it

# 1. outline, mounting holes, USB block to the new top edge, J301 as 1x10 on the grid of J2, C16, BOOT0 net name
python3 mech2.py "$OLD" m1.kicad_pcb "$SCH"; prj m1; cp "$REG" m1_reg.json
# 2. the auto-routed copper of the nets that touch what moved
python3 ripreg.py m1.kicad_pcb m1_reg.json NRST SWDIO SWCLK HRTIM1_FLT4 HRTIM1_FLT3 VSWB_SENSE VSWA_SENSE ZVS_A_IN ZVS_B_IN \
    SCL_3.3V SDA_3.3V HRTIM1_EEV1 HRTIM1_EEV2 '~{WLAT}' ADC_VDC HV_EN_MCU USART1_RX_EXTERNAL USART1_TX_EXTERNAL BOOT0 GPIO_VUSB_SENSE
# 3. obsolete hand copper out, J3 to the west edge, the resistors of J301 into the strip, wall band and silk bars at SW2
python3 mech3.py m1.kicad_pcb m3.kicad_pcb; prj m3; cp m1_reg.json m4_reg.json
# 4. east side of the MCU and the headers by hand (comb on top, tap lines alone on the back)
python3 phys6.py m3.kicad_pcb m4_reg.json m4.kicad_pcb; prj m4
# 5. old routes of the nets whose ends did not move come back; what collides with the new board goes out again
cp m4.kicad_pcb m5.kicad_pcb; cp m4_reg.json m5_reg.json; prj m5
python3 restore_old.py "$OLD" m5.kicad_pcb m5_reg.json HRTIM1_FLT4 HRTIM1_FLT3 USART1_RX_EXTERNAL USART1_TX_EXTERNAL HV_EN_MCU \
    '~{WLAT}' ADC_VDC 'BOOT0=Net-(J1-Pin_1)' NRST SCL_3.3V SDA_3.3V
python3 after_restore.py m5.kicad_pcb m5_reg.json
python3 hv_en_via.py m5.kicad_pcb m5_reg.json; prj m5
# 6. the three connections that are really new: reset to J3, the two I2C lines to the clock generator through the strip
python3 fillin.py m5.kicad_pcb m5_reg.json NRST:sn SCL_3.3V:s SDA_3.3V:s; prj m5
python3 cleanup.py m5.kicad_pcb; prj m5
# 7. everything that is not base-board copper on 0 / 45 / 90 degrees; the stubborn nets once more with a smaller margin
python3 smooth45.py m5.kicad_pcb m5_reg.json "$BASE"; prj m5
python3 cleanup.py m5.kicad_pcb; prj m5
for n in HRTIM1_FLT3 BOOT0 SPI1_CLK_DISP TIM3_CH1_ENCODER USART1_TX_EXTERNAL '~{WLAT}' +3V3 GND 'Net-(U2-VDDA)'; do
    S45_MARGIN=0.0 python3 smooth45.py m5.kicad_pcb m5_reg.json "$BASE" --only "$n"
done
prj m5; python3 cleanup.py m5.kicad_pcb; prj m5
# 8. silkscreen: pin functions of the headers, reference designators of the added parts
python3 silklabel.py m5.kicad_pcb m6.kicad_pcb; prj m6
python3 silkfix.py m6.kicad_pcb m7.kicad_pcb added_refs.json --also C16 --hide-if-stuck TP217; prj m7
# 9. into the project (PCB_SIDE_PY = the board-side netlist sync of the schematic tools), then the checks
#    python3 finalize.py m7.kicad_pcb "$PRJ" PCB_SIDE_PY
python3 lencheck.py m7.kicad_pcb
python3 off45.py m7.kicad_pcb "$BASE"
