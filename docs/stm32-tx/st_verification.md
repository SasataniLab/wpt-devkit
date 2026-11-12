# ST document verification - STM32G474RET6 WPT TX controller

Sources (text conversions, spot-checked against the PDFs where a table layout was ambiguous):

- **DS** = DS12288 Rev 6 (STM32G474xB/xC/xE datasheet)
- **RM** = RM0440 Rev 9 (STM32G4 reference manual)
- **AN** = AN2606 Rev 71 (system memory boot mode)

Conventions: values are quoted from the documents. "not stated" means the three documents do not say.
Lines starting with *Inference* are my own reasoning, not document statements.
**CONFLICT** marks a contradiction with the design facts / design summary.

At fHRTIM = 169.5 MHz: tHRTIM = 5.8997 ns, tick = tHRTIM/32 = 184.37 ps, tDTG(min) = tHRTIM/8 = 737.5 ps,
period 800 ticks = 147.493 ns (derived from the RM definitions quoted in items 11 and 12).

---

## 0. Hardware-relevant findings first

| # | Finding | Source | Action |
|---|---|---|---|
| H1 | **CONFLICT** - In system-bootloader mode PB14 (HRTIM1_CHD1 = leg B **high-side** input) is an actively driven push-pull output: SPI2_MISO, "set to 3.3 V" at bootloader start-up. A 47 kOhm pull-down cannot hold it low. PB12, PB13, PB15 are inputs. | AN Table 118 + footnote 1, p.286; Figure 69, p.287 | Swap the leg-B nets so PB14 drives the **low-side** LI and PB15 the high-side HI (bootloader then holds OutB at GND instead of VPP). Keep the HV enable interlock (PB0 is not among the bootloader pins of Table 118; the state of unlisted pins is not stated, expected to stay in the reset state so R206 keeps EN low - verify on the bench). See item 16. |
| H2 | **CONFLICT** - Positive current injection is not permitted on any FT/TT pin: IINJ(PIN) = -5/0 mA; "Positive injection (when VIN > VDD) is not possible on these I/Os". PA1 and PC1 are TT_a: VIN max = VDD + 0.3 V (operating), 4.0 V (absolute). The "1 kOhm limits the current into the internal diode to < 5 mA" assumption (design summary 21.3.1) has no basis. | DS Table 15 + notes 3-4, p.83; Table 14, p.82; Table 17, p.84; Table 53, p.127 | The pin voltage itself must stay <= 3.6 V: VSW <= 57.6 V with the 1/16 divider (64 V absolute). Add a clamp footprint (Schottky to 3V3, or a lower ratio) at VSWA_CMP / VSWB_CMP, and a trim-capacitor footprint to GND at the divider tap. See item 1. |
| H3 | PB10 / PB11 (FLT3 / FLT4, on J301) and PB12-PB15 are **TT_a**, i.e. 3.6 V tolerant only (VIN <= VDD + 0.3 V), not 5 V tolerant. PC11 / PC12 (EEV2 / EEV1) are FT_f / FT. | DS Table 12, p.63-64, p.68; Table 17, p.84 | Mark J301 pins 7/8 as 3.3 V logic only. EEV pins accept 5 V only while the MCU is powered (limit is min(VDD, VDDA) + 3.6 V, so 3.6 V at VDD = 0). |
| H4 | PC10 (VBUS sense, FT) is fine with 3.0 V at VDD = 0 (limit 3.6 V operating / 4.0 V absolute when unpowered). But PC10 is one of three pins with **0 mA** negative-injection tolerance. In bootloader mode PC10 is USART3_TX (driven output). | DS Table 14 p.82, Table 17 p.84, Table 53 p.127; AN Table 118 p.284 | Fit the optional capacitor across R8. No other change needed. |
| H5 | PA9 / PA10 floating: a high level on PA9 / PA10 switches a 5.1 kOhm pull-down onto PB6 / PB4 until firmware sets UCPD1_DBDIS. In bootloader mode PA9 is a driven output (USART1_TX). | DS Table 12 note 6, p.72; RM PWR_CR3 p.255; AN Table 118 p.284 | PB4 hard-tied by SW2 is unaffected functionally (0.65 mA if tied high). Give PA9 / PA10 a resistor pull-down (>= 10 kOhm), **not** a hard tie to GND. |
| H6 | Sense line: 60 mm of trace (about 4-8 pF) plus pads, header and the MCU pin (5 pF typ, DS Table 54) on a 938 Ohm source gives a 5-14 ns time constant when uncompensated, i.e. the same order as the dead time being measured. | *Inference* (timing budget in the Japanese note, section 3.2) | Put R339/R341 + C338/C339 at the switch node (long run on the low-voltage side), route both channels identically, add the trim-C footprint of H2. |
| H7 | ADC1_IN1 (PA0, 3.4 kOhm source): the configured 2.5-cycle sampling allows 100 Ohm maximum. **CONFLICT** (already listed as issue 8). | DS Table 67, p.141 | Firmware: >= 92.5 cycles at 60 MHz (1.54 us). Optional hardware: capacitor footprint at PA0. |
| H8 | Clock plan 24 MHz / 8 x 113 / 2 is legal (item 4). HSE Gm margin is adequate only if the crystal ESR is as assumed (item 3). Decoupling matches Figure 16 (item 8). | DS Table 46 p.123, Table 41 p.117, Figure 16 p.81 | Verify the FA-128 ESR from Epson. |

---

## Datasheet (DS12288 Rev 6)

### 1. Absolute maximum ratings, injected current

Table 14 "Voltage characteristics", p.82-83:

| Pin class | VIN min | VIN max |
|---|---|---|
| FT_xxx except FT_c | VSS - 0.3 | min(VDD, VDDA) + 4.0 V (notes 3, 4) |
| FT_c | VSS - 0.3 | 5.5 V |
| TT_xx | VSS - 0.3 | 4.0 V |
| any other | VSS - 0.3 | 4.0 V |

- Note 2: "VIN maximum must always be respected. Refer to Table 15 ... for the maximum allowed injected current values."
- Note 4: "To sustain a voltage higher than 4 V the internal pull-up/pull-down resistors must be disabled."

Table 15 "Current characteristics", p.83:

- IINJ(PIN) "Injected current on FT_xxx, TT_xx, NRST pins": **-5/0 mA** (note 4). Sum |IINJ| = +/-25 mA.
- Note 3: "Positive injection (when VIN > VDD) is not possible on these I/Os and does not occur for input voltages lower than the specified maximum value."
- Note 4: "A negative injection is induced by VIN < VSS. IINJ(PIN) must never be exceeded."

Table 17 "General operating conditions", p.84 (functional limits):

- TT_xx: -0.3 V to **VDD + 0.3 V**; FT_c: -0.3 to 5 V; all others: -0.3 V to MIN(MIN(VDD, VDDA) + 3.6 V, 5.5 V).
- Note 3: above min(VDD, VDDA) + 0.3 V the internal pull-up and pull-down must be disabled.

Table 53 "I/O current injection susceptibility", p.127 (functional): all pins except TT_a, PF10, PB8-BOOT0, PC10: -5 mA / NA;
**PF10, PB8-BOOT0, PC10: -0 mA / NA**; **TT_a pins: -5 mA / 0 mA**.

Unpowered case: the FT formula is relative to min(VDD, VDDA), so at VDD = 0 an FT pin tolerates 3.6 V (operating) / 4.0 V (absolute). TT pins: VDD + 0.3 V = 0.3 V operating, 4.0 V absolute.

Consequences:

- **PA1 / PC1 (TT_a)** - **CONFLICT** with the design summary's clamp assumption. Positive injection is not allowed at all, so the 1 kOhm resistor protects only against negative excursions (down to -5 mA). The divided node must stay <= VDD + 0.3 V = 3.6 V (functional) and <= 4.0 V (absolute): VSW <= 57.6 V / 64 V at exactly 1/16. COMP input range is 0 to VDDA (Table 79, p.163).
  *Inference*: with C338/C339 (1 pF) fitted, the fast-edge ratio is set by the capacitor ratio 1 pF : C(tap to GND). Exact compensation needs 15 pF at the tap; with less, edges overshoot at the pin (up to 16/(1 + C_tap/1 pF) times the DC ratio). Check the peak with a probe before fitting R343/R344.
- **PC10 (FT)**: 5.0 V x 15/25 = 3.0 V (3.3 V at 5.5 V) is inside 3.6 V / 4.0 V with VDD = 0. No positive injection path exists, so no back-powering is described. Negative injection tolerance is 0 mA (Table 53).

### 2. I/O structures (Table 12, p.57-72; legend Table 11, p.56)

| Pin | Structure | Page | Pin | Structure | Page |
|---|---|---|---|---|---|
| PA0 | TT_a | 59 | PB10 | TT_a | 63 |
| PA1 | TT_a | 59 | PB11 | TT_a | 63 |
| PC0 | FT_a | 59 | PB12 | TT_a | 63 |
| PC1 | TT_a | 59 | PB13 | TT_a | 63 |
| PC2 | FT_a | 59 | PB14 | TT_a | 63 |
| PC3 | TT_a | 59 | PB15 | TT_a | 64 |
| PC8 | FT_f | 65 | PC10 | FT | 68 |
| PC9 | FT_f | 65 | PC11 | FT_f | 68 |
| PA9 | FT_fda | 66 | PC12 | FT | 68 |
| PA10 | FT_fda | 66 | PC13 | FT, notes 2-3 | 57 |
| PB4 | FT_c, notes 5-6 | 70 | PB8-BOOT0 | FT_f, note 7 | 71 |

Legend: FT = 5 V tolerant, TT = 3.6 V tolerant, _a = analog switch supplied by VDDA, _c = USB Type-C PD capable, _d = Type-C dead-battery function, _f = Fm+ capable.

Footnotes (p.72):

- Note 2: PC13-PC15 are supplied through the power switch (3 mA): output speed <= 2 MHz with 30 pF, not to be used as current sources. (PC13 is an input here: no issue.)
- Note 3: after a backup-domain power-up PC13-PC15 are GPIOs; their function then depends on RTC registers not reset by system reset.
- Note 5: after reset PA13, PA14, PA15, PB3, PB4 are JTAG/SWD alternate functions with internal pull-up on PA15, PA13, **PB4** and pull-down on PA14.
- Note 6: "The pull-down on PB6 (UCPD1_CC1) is activated by high level on PA9 (UCPD1_DBCC1). The pull-down on PB4 (UCPD1_CC2) is activated by high level on PA10 (UCPD1_DBCC2)." Rd = 5.1 kOhm; disabled by UCPD1_DBDIS = 1 in PWR_CR3.
- Note 7: set PB8 to a mode other than analog after start-up if left unconnected.

RM PWR_CR3 (p.255): "After exiting reset, the USB Type-C 'dead battery' behavior is enabled ... It is recommended to disable it in all cases".

If PA9 / PA10 float: the Rd on PB6 / PB4 may switch on unpredictably until firmware sets UCPD1_DBDIS (already planned: "Disable Dead Battery Signals"). PB4 is driven hard by SW2, so its logic level stays valid (3.3 V / 5.1 kOhm = 0.65 mA when tied high). PB6 is unused. What the ROM bootloader does with UCPD1_DBDIS: not stated.

### 3. HSE oscillator (Table 41, p.117; "Guaranteed by design")

- fOSC_IN: 4 MHz min, 8 typ, **48 MHz max**. RF = 200 kOhm typ.
- **Gm "Maximum critical crystal transconductance", condition "Startup": 1.5 mA/V max.**
- IDD(HSE): 5.5 mA max during start-up; 0.44-1.77 mA typ depending on Rm / CL / frequency. tSU(HSE) = 2 ms typ (8 MHz).
- CL1/CL2 "5 pF to 20 pF range (typ.)"; "10 pF can be used as a rough estimate of the combined pin and board capacitance". Crystal selection: refers to AN2867 (not among the provided documents).

gm_crit = 4 x ESR x (2 pi f)^2 x (C0 + CL)^2 at f = 24 MHz, C0 = 1 pF, CL = 10 pF:

| ESR | gm_crit | Gm limit / gm_crit |
|---|---|---|
| 60 Ohm | 0.660 mA/V | 2.27 |
| 80 Ohm | 0.880 mA/V | 1.70 |
| 80 Ohm, CL = 12 pF | 1.230 mA/V | 1.22 |
| 100 Ohm | 1.100 mA/V | 1.36 |

The assumed crystal passes (gm_crit below 1.5 mA/V). **The real ESR of the FA-128 24 MHz part is not verified**; the margin disappears at about 136 Ohm (CL 10 pF). Whether 1.5 mA/V already includes a gain margin: not stated in DS (defined in AN2867).

### 4. PLL (Table 46, p.123; RM RCC_PLLCFGR p.293)

- fPLL_IN: **2.66 to 16 MHz**; duty cycle 45-55 %.
- fVCO_OUT: **96 to 344 MHz** (Range 1), 96 to 128 MHz (Range 2).
- fPLL_P_OUT: 2.0645 to 170 MHz (Range 1 boost) / 150 (Range 1) / 26 (Range 2). fPLL_Q_OUT and fPLL_R_OUT: 8 to **170 MHz** (boost) / 150 / 26.
- tLOCK: 15 us typ, 40 us max. Jitter (system clock 150 MHz): RMS cycle-to-cycle 28.6 ps typ, RMS period 21.4 ps typ.
- RM: 8 <= PLLN <= 127, 1 <= PLLM <= 16.

24 MHz / 8 = 3 MHz (>= 2.66), x 113 = 339 MHz (<= 344), / 2 = 169.5 MHz (<= 170, boost mode): **legal**. Margins are thin but inside: 3 MHz is 13 % above the minimum input, 339 MHz is 1.5 % below the VCO maximum.
Drawback visible in the tables: none. Jitter is specified only as a typical value at 150 MHz; jitter versus input (comparison) frequency is **not stated**. *Inference*: 21 ps RMS period jitter is about 0.12 tick, so it does not limit the 184 ps placement.

### 5. COMP (Table 79, p.163) and DAC3 (Table 76-77, p.157-159; RM Table 183 p.715, Table 191 p.725)

COMP:

- Propagation delay tD ("from COMP input pin to COMP output pin, 200 mV step with 100 mV overdrive, 50 pF load on output"): VDDA >= 2.7 V: **16.7 ns typ, 31 ns max**; VDDA < 2.7 V: 35 ns max. Note 4: the typical value is an average of all comparators.
- Offset: -9 mV min, -6/+2 typ, +3 mV max (full VDDA and temperature range).
- Hysteresis HYST[2:0] = 0..7 (min/typ/max mV): 0; 4/9/16; 7/18/32; 11/27/47; 15/36/63; 19/45/79; 23/54/95; 26/63/110. RM p.770: hysteresis is "non-symmetrical and only acting to falling edge of the comparator output".
- Start-up tSTART: 5 us max. Input range 0 to VDDA. IDDA(COMP): 450 uA typ, 720 uA max.

DAC3 (15 Msps type, internal only):

- 12-bit; "No connection to a GPIO", no output buffer, maximum sampling 15 Msps (RM Table 183).
- Settling "with one comparator on DAC output", VDDA > 2.7 V, full-scale step (typ/max): 10-90 %: 16/22 ns; 1-99 %: 33/46 ns; to 32 LSB: 40/53 ns; to 1 LSB: 64/87 ns. Wake-up 1.4 us typ / 3.5 us max.
- Accuracy: DNL +/-2 LSB, INL +/-5 LSB, TUE +/-5 LSB. IDDV(DAC) from VREF+: 720 uA typ, 955 uA max.
- Update limit (RM p.725): HFSEL must be set above 80 MHz; **HFSEL = 10 for AHB >= 160 MHz: "DAC_DOR update rate up to 7 AHB clock cycles"** (41 ns at 169.5 MHz); updates in the non-allowed period give unpredictable behaviour.

### 6. ADC (Table 66, p.138-139; Table 67, p.141)

- fADC: 0.14 to **60 MHz** (Range 1, single ADC operation); 52 MHz (all ADCs, single-ended, VDDA >= 2.7 V); 42 MHz (VDDA >= 1.62 V); 26 MHz in Range 2.
- Sampling time ts: 2.5 to 640.5 cycles. CADC = 5 pF typ. RAIN max 50 kOhm.

Table 67, 12 bits (sampling cycles at 60 MHz / time / RAIN max fast / slow):

| Cycles | ns | Fast (IN1-IN5) | Slow |
|---|---|---|---|
| 2.5 | 41.67 | 100 Ohm | N/A |
| 6.5 | 108.33 | 330 | 100 |
| 12.5 | 208.33 | 680 | 470 |
| 24.5 | 408.33 | 1500 | 1200 |
| 47.5 | 791.67 | 2200 | 1800 |
| 92.5 | 1541.67 | 4700 | 3900 |
| 247.5 | 4125 | 12000 | 10000 |
| 640.5 | 10675 | 39000 | 33000 |

PA0 = ADC1_IN1 is a fast channel. 3.4 kOhm needs the **92.5-cycle row: >= 1.54 us** (47.5 cycles allows only 2.2 kOhm). **CONFLICT**: the .ioc has ADC_SAMPLETIME_2CYCLES_5 (100 Ohm max). The table is in time at 60 MHz; at a lower fADC choose the setting that still gives >= 1.54 us. PC2 = ADC2_IN8 is a slow channel. The .ioc shows ADC12 clock = 169.5 MHz with no prescaler entry; fADC must be divided down to <= 60 MHz.

### 7. HRTIM electrical characteristics (Tables 59-63, p.134-136)

Table 59:

- fHRTIM "HRTIM input clock for DLL calibration": **max 170 MHz**, tHRTIM min 5.88 ns. A minimum frequency is **not stated** (Min column empty).
- tRES(HRTIM) high-resolution step: **184 ps typ** (fHRTIM = 170 MHz, TA -40 to 105 C). Timer resolution 16 bit.
- **tDTG dead-time generator clock period: 0.125 to 16 tHRTIM (0.735 ns to 94.1 ns at 170 MHz).** Dead-time range: 511 tDTG max (48.09 us at 170 MHz).

Table 60 (fault): digital fault latency FLTx pin to CHxy pin **9 ns typ, 20 ns max**; minimum fault pulse width **7 ns**; analog fault latency COMPx_INP to CHxy **16 ns typ, 31 ns max**.

Table 61 (external events 1-5, low-latency mode EExFAST = 1): digital EEVx pin to CHxy **12 ns typ, 23 ns max** (30 pF); analog COMPx_INP to CHxy **19 ns typ, 31 ns max**; minimum EEV pulse width **7 ns**.

Table 62 (external events 1-10, synchronous mode, filter off, fHRTIM = 170 MHz): digital **56 ns typ, 66 ns max**; analog **62 ns typ, 76 ns max**; minimum pulse width 7 ns; response jitter **1 tHRTIM max**.

Table 63: SYNCIN minimum pulse 2 tHRTIM; response to external sync 3 tHRTIM max.

### 8. Power

Figure 16 "Power supply scheme", p.81, with the caution to decouple each supply pair close to the pins:

| Rail | DS recommendation | Board | Result |
|---|---|---|---|
| VDD (4 pairs on LQFP64: pins 16, 32, 48, 64) | n x 100 nF + 1 x 4.7 uF | 4 x 100 nF + 4.7 uF | matches |
| VDDA | 10 nF + 1 uF | 10 nF + 1 uF | matches |
| VREF+ | 100 nF + 1 uF | 100 nF + 1 uF, tied to VDDA | matches; VREF+ must be between 2 V and VDDA (p.24) |
| VBAT | 1.55-3.6 V; capacitor **not stated** | tied to 3V3 | allowed |

Supply current (Table 21, p.89: Range 1 boost, **170 MHz, all peripherals disabled**, code from Flash): 29.5 mA typ at 25 C, 31 mA typ at 85 C; max 31 / 42 / 48 / 56 mA at 25 / 85 / 105 / 125 C.
A figure "with HRTIM/USB/ADC" is **not stated**; Table 35 (p.109-113) gives per-peripheral typical uA/MHz in boost mode:

| Peripheral | uA/MHz | mA at 169.5 MHz |
|---|---|---|
| HRTIM | 69.98 | 11.86 |
| ADC1/ADC2 (+ independent clock 0.72) | 6.24 | 1.18 |
| DAC3 | 4.62 | 0.78 |
| SYSCFG/COMP/OPAMP/VREFBUF | 1.63 | 0.28 |
| TIM3 | 6.37 | 1.08 |
| USART1 (+ independent clock 7.62) | 2.49 | 1.71 |
| I2C3 (+ independent clock 2.72) | 1.25 | 0.67 |
| SPI1 | 1.99 | 0.34 |
| USB (+ independent clock 1.10 at 48 MHz), CRS 0.74 | 0.46 | 0.26 |
| GPIOA/B/C | 0.29 | 0.05 |
| Sum | | about 18.2 |

Analog adders: COMP 2 x 0.45 mA typ (0.72 max), DAC3 0.72 mA from VREF+, HSI48 0.34 mA typ (Table 44), HSE crystal about 0.5-1 mA, ADC <= 0.2 mA at 1 Msps.
*Inference*: about 51 mA typical at 25 C, about 65 mA at the 85 C maximum, plus I/O switching (four gate signals at 6.78 MHz into about 30 pF: roughly 3 mA). Budget 100 mA on 3V3 for the MCU; the absolute limit is 150 mA total into VDD (Table 15).
USB: transceiver operating range 3.0-3.6 V, crystal-less operation -15 to 85 C, no external series resistors needed (Table 92, p.179).

---

## Reference manual (RM0440 Rev 9)

### 9. External-event and fault mapping (Table 223 p.887, Table 228 p.888; both checked against the PDF)

| Event | Fast mode | Digital filter | Src1 (00) | Src2 (01) | Src3 (10) | Src4 (11) |
|---|---|---|---|---|---|---|
| EEV1 | Yes | - | PC12 | COMP2 | tim1_trgo | adc1_awd1 |
| EEV2 | Yes | - | PC11 | COMP4 | tim2_trgo | adc1_awd2 |
| EEV3 | Yes | - | PB7 | COMP6 | tim3_trgo | adc1_awd3 |
| EEV4 | Yes | - | PB6 | **COMP1** | COMP5 | adc2_awd1 |
| EEV5 | Yes | - | PB9 | **COMP3** | COMP7 | adc2_awd2 |
| EEV6 | - | Yes | PB5 | COMP2 | COMP1 | adc2_awd3 |
| EEV7 | - | Yes | PB4 | COMP4 | tim7_trgo | adc3_awd1 |
| EEV8 | - | Yes | PB8 | COMP6 | COMP3 | adc4_awd1 |
| EEV9 | - | Yes | PB3 | COMP5 | tim15_trgo | COMP4 |
| EEV10 | - | Yes | PC5/PC6 | COMP7 | tim6_trgo | adc5_awd1 |

Balanced-fault use: EEV6/EEV7 for timers A, B, C; EEV8/EEV9 for timers D, E, F.

**"COMP1 -> EEV4, COMP3 -> EEV5" is confirmed** (source 2, EExSRC = 01, both with fast mode). COMP1 is also EEV6 source 3 and COMP3 is EEV8 source 3 (filtered, no fast mode).
Pin facts confirmed: PC12 = EEV1 source 1, PC11 = EEV2 source 1.

| Fault | Pin (FLTxSRC 00) | Internal (01) | Internal (10) |
|---|---|---|---|
| FLT1 | PA12 | COMP2 | EEV1_muxout |
| FLT2 | PA15 | COMP4 | EEV2_muxout |
| FLT3 | **PB10** | COMP6 | EEV3_muxout |
| FLT4 | **PB11** | COMP1 | EEV4_muxout |
| FLT5 | PB0/PC7 | COMP3 | EEV5_muxout |
| FLT6 | PC10 | COMP5 | EEV6_muxout |

System fault (Table 230, p.889): core lockup, PVD, SRAM parity, Flash ECC (each enabled in SYSCFG) and the clock security system ("always enabled"); it disables all outputs whose FAULTy[1:0] is 01, 10 or 11 (p.967).

### 10. External-event timing, capture resolution, filters

- Table 241, p.928: EExFAST = 0: response latency "5 to 6 cycles of fHRTIM clock", response jitter "1 cycle of fHRTIM clock", pulse width "maintained with high-resolution". EExFAST = 1: "minimal latency (depends whether the comparator or digital input is used)", "1 cycle of fHRTIM clock jitter" on the pulse width. Figures 244/245 (p.929) are labelled "6-7 cycles delay". DS Table 62 gives the pin-to-pin figure: 56 ns typ / 66 ns max (about 10-11 cycles). The three figures are not reconciled in the documents.
- Fast-mode restrictions (p.928): level-sensitive only (EExSNS = 00); cannot toggle an output; source and polarity frozen once EExFAST is set; with blanking/windowing EExLTCH must be 0 and there is no window timeout; "**When EExFAST bit is set, the output cannot be changed during the 11 fHRTIM clock periods following the external event**" (64.9 ns at 169.5 MHz, i.e. 88 % of a 73.7 ns half period).
- **Capture resolution**: "The high-resolution is not available for ... Timer counter read and write accesses, Capture unit" (p.890); "The capture is done with fHRTIM resolution: for a clock prescaling ratio below 32 (CKPSC[2:0] < 5), the least significant bits of the register are not significant (read as 0)" (p.902). **So a capture resolves one fHRTIM period, 5.9 ns, not 184 ps.** In addition "there is a delay of 1 to 2 fHRTIM clock periods between the falling edge and the capture event due to an internal resynchronization stage" (p.905).
- External events used for reset, capture, burst, ADC trigger and delayed protection are edge-sensitive even when level sensitivity is selected; all external events are discarded while TxCEN = 0 (p.926).
- Digital filter EExF[3:0] exists only on EEV6-EEV10 (p.926-927).
- Blanking (p.930-931, EExFLTR 0001-1100): from counter reset/roll-over to own CMP1..CMP4, or eight sources from other timers (Table 242); for timer C: TA CMP2, TB CMP1, TB CMP4, TF CMP1, TD CMP1, TD CMP4, **TD2 output**, TE CMP4; for timer D: TA CMP1, TB CMP2, TC CMP1, TC CMP2, **TC2 output**, TE CMP1, TE CMP4, TF CMP4. A Tx2 source masks events "as long as the Tx2 signal is inactive" and does not need the output enabled.
- Windowing (p.932-933, EExFLTR 1101-1111): from counter reset to own CMP2 or CMP3, or to the paired timer's CMP2 (C <-> D). With EExLTCH = 0 "a timeout event is generated at the end of the window" if no event occurred (not in fast mode); with EExLTCH = 1 the event is latched and delivered at the end of the blanking/window period.
- EExFLTR and EExLTCH must not be modified once the counter is enabled; a compare value used for filtering must be > 0 (p.1041).
- External-event counter (p.934-935, HRTIM_EEFxR3 p.1087): **one per timing unit**, after the filter, edge-sensitive events only; the event is passed on when the count reaches EEVACNT[5:0] + 1 (1 to 64); EEVARSTM = 0 resets it every period, EEVARSTM = 1 resets it "only if no event occurs during last counting period". **The count itself is not readable.**
- Whether blanking/window boundaries act on an external event with 184 ps or fHRTIM granularity: **not stated**.

### 11. Dead-time unit and the four-compare alternative

- p.910-913: enabled by DTEN in HRTIM_OUTxR; the pair is built from the output-1 reference waveform (SETx1R / RSTx1R); "HRTIM_SETx2R and HRTIM_RSTx2R registers are not significant when DTEN bit is set".
- "tDTx = +/- DTx[8:0] x tDTG ... tDTG = 2^(DTPRSC[2:0]) x (tHRTIM / 8)" (p.911). Table 237 (p.912) at 170 MHz: DTPRSC 000: **0.73 ns step, 0.38 us max**; 001: 1.47 ns, 0.75 us; 010: 2.94 ns, 1.50 us; 011: 5.89 ns, 3.01 us; ... 111: 94.12 ns, 48.10 us. Range 0 to 511 x tDTG, independently for rising (DTRx) and falling (DTFx) edges.
- **Finest step is tHRTIM/8 = 737.5 ps at 169.5 MHz, four times coarser than the 184 ps edge placement.** Achievable: 11 steps = 8.11 ns, 13 = 9.59 ns, 14 = 10.32 ns.
- Sign bits SDTRx / SDTFx: 1 = negative dead time (overlap). Lock bits DTRLKx, DTFLKx (value and sign) and DTRSLKx, DTFSLKx (sign only) are write-once until the next system reset; DTPRSC becomes read-only once any lock bit is set (p.913, p.1027-1028). Register reset value 0 (no dead time).
- HRTIM_DTxR is preloadable (Table 244, p.943), so the value can change on an update event. DTEN must not be changed while the timer is enabled or its outputs are driven by another timer (p.913).
- Pulses shorter than the dead time: the corresponding dead time is skipped (Figures 227-230, p.912-913).
- Interaction with high resolution: the feature list says "High-resolution deadtime insertion (down to 735 ps)" (p.882); no restriction on small values in normal run mode is stated. Only for the delayed burst-idle entry: dead times below 3 fHRTIM periods fall under the narrow-pulse rules (p.958).

Four compare events (DTEN = 0, CHx1 set/reset on CMP1/CMP2, CHx2 on CMP3/CMP4), restrictions:

- All four compare values within [0x60, PER] (item 12).
- Set and reset of the **same** output closer than 3 tHRTIM lose high resolution (p.922-924); here every pulse and gap on one output is about 64 ns or more, so this is not limiting. The dead time is the spacing of events on two **different** outputs, which this rule does not cover.
- No hardware interlock between the two outputs: nothing in the HRTIM prevents overlap if the registers are wrong. *Inference*: with the LM5113 (no shoot-through protection) every register set must be validated in software and loaded atomically through preload.
- CMP3 / CMP4 are then no longer free for fault blanking windows (item 14).

### 12. High-resolution restrictions

- Table 232, p.893 (CKPSC = 0): period and compare **min 0x0060, max 0xFFDF**. "The minimum value must be greater than or equal to 3 periods of the fHRTIM clock"; 0x0000 is allowed in CMP1 and CMP3 only (null duty-cycle case, p.901). Other prescalers: 0x30/0xFFEF, 0x18/0xFFF7, 0x0C/0xFFFB, 0x06/0xFFFD, 0x03/0xFFFD.
- At 169.5 MHz: 0x60 = 96 ticks = 17.70 ns. Period 800 is legal; compare values must lie in 96..800, i.e. no compare event can be placed in the first 17.7 ns of the counting period.
- "A compare value greater than the period register value does not generate a compare match event" (p.893).
- Values 1..0x5F: "forbidden" (p.901); the resulting behaviour is **not stated**.
- Narrow pulses (p.922-924): events on one output within the same tHRTIM: reset wins, set ignored; interval below 1 tHRTIM across two periods: pulse of 1 tHRTIM; below 2 tHRTIM: pulse of 2 tHRTIM; 2 to 3 tHRTIM: high resolution only if over 2 complete periods; above 3 tHRTIM: always high resolution.
- A set/reset on the **update** event is low resolution, lagging by up to 31/32 tHRTIM (p.899). Low-resolution events also include EXTEVNT1..10, RESYNC and software set (p.924).
- HALF mode: period >= 6 fHRTIM periods (0xC0), CMP1 forced to PER/2 (p.900).
- Prescaler must be written before compare/period registers and cannot change once the timer is enabled; timers that exchange events must use identical prescalers (p.890-891).
- Counter and capture registers have no significant bits below one fHRTIM period when CKPSC < 5 (p.890).
- DLL (p.987, HRTIM_DLLCR p.1116): start with CAL, wait for DLLRDY before starting any counter, then set CALEN for periodic calibration; CALRTE = 00/01/10/11: 1048576 / 131072 / 16384 / 2048 tHRTIM (6.2 ms / 771 us / 96 us / 12 us at 170 MHz). CAL and CALEN must not be set in the same write. The clock must respect "the fHRTIM range for the DLL lock"; only the 170 MHz maximum is given (DS Table 59), the lower limit is **not stated**.
- The relation fPWM = fHRCK / PER is **not written as a formula**; it follows from Table 231 (min PWM frequency 83.0 kHz = 5.44 GHz / 0xFFDF) and the 3-period = 0x60 rule. Confirm 6.780 MHz with a counter on first power-up.

### 13. Two timing units for a full bridge

- Counter reset sources of a timing unit (p.895; HRTIM_RSTDR p.1049): own CMP2, CMP4, update; master period and CMP1..4; EEV1..10; other timers' CMP1, CMP2, CMP4. Reset requests are ORed and only act once TxCEN is set.
- Cross-timer set/reset events (Table 234, p.899): timer C can use TA CMP2/CMP3, TB CMP2/CMP3, **TD CMP2/CMP4**, TE CMP3/CMP4, TF CMP2; timer D can use TA CMP1/CMP4, TB CMP2/CMP4, **TC CMP4**, TE CMP1/CMP4, TF CMP1/CMP3. Master period and CMP1..4 are available to every timer.
- Reference use case "Multiphase converters" (p.991-992): "The master timer is responsible for the phase management: it defines the phase relationship between the converters by resetting the timers periodically".
- High resolution: feature list "Duty cycle, frequency, phase shift ... can be adjusted with full resolution, on all outputs" (p.882). Master and cross-timer compare events are not in the low-resolution list (p.924). An explicit sentence that a counter reset by a master compare keeps the 184 ps fraction, and the latency of such a reset: **not stated**. For CKPSC >= 5 only, the reset is delayed to the next prescaled clock edge (p.895).
- All TxCEN and MCEN bits are in HRTIM_MCR, "This allows to have all timer synchronously started with a single write access" (p.914). Each enable bit "must not be changed within a minimum of 8 cycles of fHRTIM clock" (p.995-996).
- A master compare value has the same 0x60 minimum, so a phase set by a master compare cannot be below 96 ticks from the master roll-over.
- Preload (p.942-946): PREEN per timer; preloadable: PER, REP, CMP1..4, **DTxR**, SETx1R/RSTx1R/SETx2R/RSTx2R, RSTxR (Table 244). Update sources: software (TxSWU, MSWU in HRTIM_CR2), repetition event (TxREPU, MREPU), counter reset/roll-over (TxRSTU), another timer or the master (TyU, MSTU), burst DMA, hrtim_upd_en[3:1]. RSYNCU = 1 defers an update coming from another timer to the next reset/roll-over.
- Glitch-free multi-register change (p.945): set MUDIS / TxUDIS in HRTIM_CR1, write all preload registers, clear the bits; "The transfer from preload to active registers is done as soon as the ... repetition event occurs". A master update caused by a repetition roll-over propagates to timers with MSTU = 1; a software master update does not (Table 245, p.948).

### 14. Fault path and output states

- Asynchronous: "If FLTxF[3:0] bitfield is set to 0000, the signal is not filtered and acts asynchronously, independently from the fHRTIM clock" (p.964). Latency DS Table 60: 9 ns typ / 20 ns max, minimum pulse 7 ns.
- Digital filter FLTxF (Table 251, p.965; p.1120): 0001/0010/0011 = fHRTIM x 2/4/8 samples (11.8 to 47.1 ns), up to 12.05 us; sampling clock divider FLTSD.
- Polarity FLTxP: 0 = active low (reset default), 1 = active high. Enable FLTxE (global) and FLTnEN per timer in HRTIM_FLTxR. Source, polarity and filter may be written only while FLTxE = 0 (p.1120).
- Blanking (Table 252, p.966): FLT3 is tied to **timer C**, FLT4 to **timer D**: window from timer reset/roll-over to CMP3 (FLTxBLKS = 0) or from CMP4 to CMP3 (FLTxBLKS = 1). Fault counter FLTxCNT[3:0] with the same two reset modes as the event counter (p.966, p.1133).
- Output level in fault, FAULTx[1:0] per output (p.953, p.1080): 00 = no action (reset default: **the output ignores faults**), 01 = active, 10 = inactive, 11 = Hi-Z. Not changeable once the timer is enabled with a fault enabled or while in FAULT state.
- States (p.952-954): RUN (TxyOEN = 1), IDLE (default after HRTIM reset; level IDLESx: 0 = inactive), FAULT. "This state is maintained until the output is re-enabled by software" (p.963); with a persistent fault the output stays in FAULT. IDLE has priority over FAULT, FAULT over RUN.
- Lock bits: FLTxLCK (input conditioning) and FLTLCK (per-timer enables), write-once until reset (p.967).
- MCU reset: "all I/Os are set as floating inputs during and after reset" (DS Table 11, p.56); "the I/Os state under and after reset is 'analog state'" (DS 3.11.5, p.25). The external 47 kOhm pull-downs define the level.
- Before HRTIM initialisation (p.988): set POLx, FAULTx, IDLESx first, then switch the GPIOs to the HRTIM alternate function: "From this point on, the HRTIM controls the outputs, which are in the IDLE state." After TxyOEN "the 2 outputs are in the inactive state until the first valid set/reset event"; with DTEN set "it is necessary to force the output state by software, using SST and RST bits, to have the outputs in a complementary state as soon as the RUN mode is entered". "If the HRTIM peripheral is reset with the Reset and Clock Controller, the output control is released to the GPIO controller and the outputs are tri stated."
- Debug halt (p.988-989; DBGMCU_APB2FZR bit 26 DBG_HRTIM_STOP, p.2111, cleared only by power-on reset): 0 = "the HRTIM continues to operate"; 1 = all HRTIM timers stop and "The outputs in RUN mode enter the FAULT state if FAULTx[1:0] = 01,10,11, or keep their current state if FAULTx[1:0] = 00"; this persists after the halt until TxyOEN is set again. Fault inputs stay active during the halt.

### 15. COMP1 / COMP3 (Tables 199-201, p.769-771)

- INP: COMP1: INPSEL 0 = **PA1**, 1 = PB1. COMP3: INPSEL 0 = PA0, **1 = PC1**.
- INM (INMSEL): 000-011 = 1/4, 1/2, 3/4, 1 x VREFINT; **100 = DAC3_CH1 for both COMP1 and COMP3**; 101 = DAC1_CH1 for both; 110 = PA4 (COMP1) / PF1 (COMP3); 111 = PA0 (COMP1) / PC0 (COMP3).
  The shared DAC3 OUT1 threshold is confirmed. Independent thresholds would need DAC1_CH1 on one comparator.
- Blanking sources BLANKSEL 001..111: COMP1: TIM1_OC5, TIM2_OC3, TIM3_OC3, TIM8_OC5, TIM20_OC5, TIM15_OC1, TIM4_OC3. COMP3: TIM1_OC5, TIM3_OC3, TIM2_OC4, TIM8_OC5, TIM20_OC5, TIM15_OC1, TIM4_OC3. **No HRTIM signal can blank a comparator**; blanking synchronous to the HRTIM must be done in the HRTIM event filters (item 10).
- Output routing to the HRTIM is fixed by Tables 223 and 228 (item 9): COMP1 -> EEV4 src 2, EEV6 src 3, FLT4; COMP3 -> EEV5 src 2, EEV8 src 3, FLT5. Polarity and output redirection work independently of the APB clock (p.769).

---

## AN2606 Rev 71

### 16. STM32G47xxx/48xxx bootloader (section 53, p.284-289)

Activation: Pattern 14 (Table 2, p.36, checked against the PDF):

1. BOOT_LOCK = 0, nBoot1 = 1, **Boot0 pin = 1** and nSWBoot0 = 1
2. BOOT_LOCK = 0, nBoot1 = 1, nBoot0 bit = 0 and nSWBoot0 = 0
3. BOOT_LOCK = 0, Boot0 pin = 0, nSWBoot0 = 1, **BFB2 = 1** and both banks do not contain valid code
4. BOOT_LOCK = 0, nBoot0 bit = 1, nSWBoot0 = 0, BFB2 = 1 and both banks do not contain valid code

There is no plain "empty flash" entry without BFB2 = 1. RM Table 5 (p.91) agrees: BOOT0 pin (PB8) = 1 with nBOOT1 = 1 and nSWBOOT0 = 1 selects system memory; the pin is latched "on the 4th edge of the internal startup clock source after reset release" (p.92). With readout protection level 2 the bootloader cannot run (AN p.35).

Clocks: "The system clock frequency is 72 MHz (using the PLL clocked by HSI)"; "CRS is enabled for the DFU to allow USB to be clocked by HSI48 48 MHz". The HSE crystal is not used.

Interfaces and pins (Table 118, p.284-286):

| Interface | Pin | Direction | Stated configuration | Board net |
|---|---|---|---|---|
| USART1 | PA10 RX | input | alternate push-pull, pull-up | unconnected |
| | PA9 TX | **output** | alternate push-pull, pull-up | unconnected |
| USART2 | PA3 RX | input | pull-up | DISP_DC |
| | PA2 TX | **output** | alternate push-pull, pull-up | DISP_CS |
| USART3 | PC11 RX | input | pull-up | HRTIM1_EEV2 / ZVS_B |
| | PC10 TX | **output** | alternate push-pull, pull-up | VBUS sense divider |
| I2C2 | PC4 SCL, PA8 SDA | in/out | open-drain, pull-up | USART1_TX ext / spare |
| I2C3 | PC8 SCL, PC9 SDA | in/out | open-drain, pull-up | control I2C bus |
| I2C4 | PC6 SCL, PC7 SDA | in/out | open-drain, pull-up | encoder A / B |
| SPI1 | PA7 MOSI | input | push-pull, pull-down | display |
| | PA6 MISO | **output** | push-pull, pull-down, footnote 1 | display |
| | PA5 SCK, PA4 NSS | input | no pull / pull-down | display, DISP_RST |
| **SPI2** | **PB15 MOSI** | input | push-pull, pull-down | leg B low-side |
| | **PB14 MISO** | **output** | push-pull, pull-down, footnote 1 | **leg B high-side** |
| | **PB13 SCK** | input | "push-pull, n pull-down mode" (text garbled; SPI1_SCK reads "no pull-up, pull-down") | leg A low-side |
| | **PB12 NSS** | input | push-pull, pull-down | leg A high-side |
| USB DFU | PA11 DM, PA12 DP | in/out | input no pull, no external pull-up needed | USB |

I2C target address 0b1010011x; USART 8-bit, even parity, 1 stop bit; SPI slave, up to 8 MHz.

Footnote 1: "SPI Tx (MISO) is handled by DMA. On the bootloader start-up after SPI initialization as soon as the bit DMATx enable on SPI CR2 register is set to 0x1, **the MISO line is set to 3.3 V**."

When: Figure 69 (p.287) configures USB, I2Cx, SPIx and USARTx in sequence directly after system init, **before** the detection loop. The pins are therefore driven at bootloader start, not after an interface is detected. After detection the bootloader disables "all interrupt sources and other interfaces clocks"; whether the unused pins are released: **not stated**.

Answers:

- PB12-PB15 are configured as SPI2. **Only PB14 is an actively driven output**, and it is driven high.
- PC10 / PC11 are USART3 TX (driven) / RX (pull-up).
- **CONFLICT** with the assumption that 47 kOhm pull-downs keep all four gate-driver inputs low whenever the application is not running. In bootloader mode HI of leg B is high and LI low: the leg-B high-side FET is commanded on (LM5113: HO follows HI while the bootstrap supply is above UVLO). No shoot-through, but OutB is tied to VPP for as long as the bootloader runs.
  *Inference / recommendation*: (a) swap the nets so PB14 = leg-B low-side and PB15 = leg-B high-side; the same condition then parks OutB at GND, and firmware is unaffected because either output of a complementary pair can serve either FET; (b) keep relying on the HV enable: PB0 is not listed as a bootloader pin, so it is expected to stay floating with R206 holding the HV DC-DC off, provided VPP has no other source (AN2606 does not describe unlisted pins: check PB0 and VPP once in bootloader mode); (c) never enter the bootloader with an external bench supply on VPP.
- Other board effects (*inference* from the table): PC10 drives 3.3 V into the R7/R8 divider (harmless, < 0.4 mA); PA2 (DISP_CS) idles high and PA4 (DISP_RST) is pulled low, so the display stays quiet although PA6 is driven; PC11 with its 100 kOhm pull-down against the internal pull-up idles high, so a toggling signal on J301 pin 6 could be taken for USART data; the MCU answers as an I2C target at 0x53 on the control bus (no other master present).
- USB DFU needs only the BOOT0 jumper and USB; clock source HSI48 + CRS.

---

## Items the documents do not state

1. Lower fHRTIM limit for DLL lock (DS Table 59 gives only the 170 MHz maximum).
2. PLL jitter versus input frequency; jitter at 169.5 MHz (typical values at 150 MHz only).
3. Behaviour for compare values inside 1..0x5F ("forbidden" only).
4. Whether a counter reset by a master / other-timer compare keeps sub-fHRTIM resolution, and its latency.
5. Granularity of blanking / window boundaries relative to an external event; readable event count (there is none).
6. The explicit formula fPWM = fHRCK / PER.
7. Reconciliation of "5 to 6 cycles" (RM Table 241), "6-7 cycles" (RM Figures 244/245) and 56 / 66 ns (DS Table 62).
8. VBAT decoupling; a single supply-current figure with HRTIM, USB and ADC running.
9. Whether Gm = 1.5 mA/V includes a gain margin (AN2867); the real ESR of the chosen crystal.
10. Bootloader: release of unused interface pins after detection; pull configuration of PB13; handling of UCPD1_DBDIS.
