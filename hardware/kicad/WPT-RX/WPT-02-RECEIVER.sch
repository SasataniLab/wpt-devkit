EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A3 16535 11693
encoding utf-8
Sheet 1 1
Title "WPT - Receiver Block"
Date "2020-03-09"
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L murata:BLM18PG330SN1D FB?
U 1 1 5C9C41E5
P 12400 1850
AR Path="/5C9ACAA6/5C9C41E5" Ref="FB?"  Part="1" 
AR Path="/5C9C41E5" Ref="FB101"  Part="1" 
F 0 "FB101" H 12400 2042 40  0000 C CNN
F 1 "BLM18PG330SN1D" H 12400 1966 40  0000 C CNN
F 2 "murata:BLM18" H 12400 1850 30  0001 C CNN
F 3 "http://search.murata.co.jp/Ceramy/image/img/PDF/ENG/L0110S0100BLM18P.pdf" H 12375 1850 60  0001 C CNN
F 4 "Murata Electronics " H 12500 2050 50  0001 C CNN "Manufacturer"
F 5 "BLM18PG330SN1D" H 12600 2150 50  0001 C CNN "Manufacturer Part Number"
	1    12400 1850
	1    0    0    -1  
$EndComp
Wire Wire Line
	4300 1950 4300 1850
Wire Wire Line
	4300 1850 4200 1850
Wire Wire Line
	3900 1850 3900 1950
Wire Wire Line
	3900 2950 4300 2950
$Comp
L samsung:CL31A106KBHNNNE C?
U 1 1 5CA422AF
P 5200 2150
AR Path="/5C9C60CA/5CA422AF" Ref="C?"  Part="1" 
AR Path="/5CA422AF" Ref="C107"  Part="1" 
F 0 "C107" V 5100 2150 40  0000 C CNN
F 1 "10u/50(X5R)" V 5300 2150 40  0000 C CNN
F 2 "murata:GRM31" H 5200 2080 10  0001 C CNN
F 3 "http://www.samsungsem.com/kr/support/product-search/mlcc/CL31A106KBHNNNE.jsp" H 5200 2230 10  0001 C CNN
F 4 "3216" V 5250 2150 10  0000 C CNN "Size"
F 5 "Samsung Electro-Mechanics" H -1350 500 50  0001 C CNN "Manufacturer"
F 6 "CL31A106KBHNNNE" H -1350 500 50  0001 C CNN "Manufacturer Part Number"
	1    5200 2150
	1    0    0    -1  
$EndComp
Connection ~ 4300 1850
Connection ~ 4300 2950
$Comp
L power:VPP #PWR?
U 1 1 5CA422B8
P 3900 1850
AR Path="/5C9C60CA/5CA422B8" Ref="#PWR?"  Part="1" 
AR Path="/5CA422B8" Ref="#PWR0102"  Part="1" 
F 0 "#PWR0102" H 3900 1700 50  0001 C CNN
F 1 "VPP" H 3915 2023 50  0000 C CNN
F 2 "" H 3900 1850 50  0001 C CNN
F 3 "" H 3900 1850 50  0001 C CNN
	1    3900 1850
	1    0    0    -1  
$EndComp
Text Notes 4650 1650 0    40   ~ 0
VPP=DC7.5V-40V
$Comp
L testpooint:TP1.0 TP?
U 1 1 5CA422BF
P 5650 1850
AR Path="/5C9C60CA/5CA422BF" Ref="TP?"  Part="1" 
AR Path="/5CA422BF" Ref="TP102"  Part="1" 
F 0 "TP102" H 5500 1950 40  0000 L CNN
F 1 "TP1.0" H 5400 1900 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 5650 1850 50  0001 C CNN
F 3 "" H 5650 1850 50  0000 C CNN
	1    5650 1850
	1    0    0    -1  
$EndComp
$Comp
L testpooint:TP1.0 TP?
U 1 1 5CA422C6
P 5650 2950
AR Path="/5C9C60CA/5CA422C6" Ref="TP?"  Part="1" 
AR Path="/5CA422C6" Ref="TP104"  Part="1" 
F 0 "TP104" H 5703 2988 40  0000 L CNN
F 1 "TP1.0" H 5703 2912 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 5650 2950 50  0001 C CNN
F 3 "" H 5650 2950 50  0000 C CNN
	1    5650 2950
	1    0    0    -1  
$EndComp
Connection ~ 5650 1850
Connection ~ 3900 1850
$Comp
L power:PWR_FLAG #FLG?
U 1 1 5CA422DD
P 4200 1850
AR Path="/5C9C60CA/5CA422DD" Ref="#FLG?"  Part="1" 
AR Path="/5CA422DD" Ref="#FLG0101"  Part="1" 
F 0 "#FLG0101" H 4200 1925 50  0001 C CNN
F 1 "PWR_FLAG" H 4200 2024 50  0001 C CNN
F 2 "" H 4200 1850 50  0001 C CNN
F 3 "" H 4200 1850 50  0001 C CNN
	1    4200 1850
	1    0    0    -1  
$EndComp
Connection ~ 4200 1850
Wire Wire Line
	4200 1850 3900 1850
$Comp
L murata:GRM1555C1H102JA01D C?
U 1 1 5CA422E7
P 4650 2150
AR Path="/5C9C60CA/5CA422E7" Ref="C?"  Part="1" 
AR Path="/5CA422E7" Ref="C105"  Part="1" 
F 0 "C105" H 4800 2125 40  0000 L CNN
F 1 "1000p/50(C0G)" H 4400 2225 40  0000 L CNN
F 2 "murata:GRM15" V 4800 2188 20  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 4650 2150 20  0001 C CNN
F 4 "1005" H 4640 2190 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 4650 2150 50  0001 C CNN "Manufacturer"
F 6 "GRM1555C1H102JA01D" H 4650 2150 50  0001 C CNN "Manufacturer Part Number"
	1    4650 2150
	0    1    1    0   
$EndComp
Connection ~ 5200 1850
Wire Wire Line
	5200 1850 5400 1850
Connection ~ 5200 2950
Wire Wire Line
	5200 2950 5400 2950
Wire Wire Line
	4650 2100 4650 1850
Connection ~ 4650 1850
Wire Wire Line
	4650 1850 4925 1850
Wire Wire Line
	4650 2200 4650 2950
Wire Wire Line
	4300 2950 4650 2950
Connection ~ 4650 2950
Wire Wire Line
	4650 2950 4925 2950
$Comp
L murata:GCM21BR72A104KA37L C?
U 1 1 5CA422FA
P 4925 2150
AR Path="/5C9C60CA/5CA422FA" Ref="C?"  Part="1" 
AR Path="/5CA422FA" Ref="C106"  Part="1" 
F 0 "C106" H 5075 2100 40  0000 L CNN
F 1 "0.1u/100(X7R)" H 4725 2200 40  0000 L CNN
F 2 "murata:GRM21" V 5075 2188 30  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 4925 2150 30  0001 C CNN
F 4 "2012" V 4925 2150 10  0000 C CNN "Size"
F 5 "Murata Electronics" H 4925 2150 50  0001 C CNN "Manufacturer"
F 6 "GCM21BR72A104KA37L" H 4925 2150 50  0001 C CNN "Manufacturer Part Number"
	1    4925 2150
	0    1    1    0   
$EndComp
Wire Wire Line
	4925 2100 4925 1850
Wire Wire Line
	4925 2200 4925 2950
Connection ~ 4925 1850
Wire Wire Line
	4925 1850 5200 1850
Connection ~ 4925 2950
Wire Wire Line
	4925 2950 5200 2950
$Comp
L on_semiconductor:MM3Z39VT1G D?
U 1 1 5CA42307
P 5400 2200
AR Path="/5C9C60CA/5CA42307" Ref="D?"  Part="1" 
AR Path="/5CA42307" Ref="D104"  Part="1" 
F 0 "D104" H 5500 2300 40  0000 L CNN
F 1 "MM3Z39VT1G" H 5200 2350 40  0000 L CNN
F 2 "Diodes_SMD:SOD-323" H 5400 2200 60  0001 C CNN
F 3 "http://www.onsemi.com/pub/Collateral/MM3Z2V4T1-D.PDF" H 5400 2332 60  0001 C CNN
F 4 "ON Semiconductor" H 5400 2200 50  0001 C CNN "Manufacturer"
F 5 "MM3Z39VT1G" H 5400 2200 50  0001 C CNN "Manufacturer Part Number"
	1    5400 2200
	0    1    1    0   
$EndComp
Wire Wire Line
	5400 2000 5400 1850
Connection ~ 5400 1850
Wire Wire Line
	5400 1850 5650 1850
Wire Wire Line
	5400 2400 5400 2950
Connection ~ 5400 2950
Wire Wire Line
	5400 2950 5650 2950
Wire Wire Line
	4300 1850 4650 1850
Wire Wire Line
	5200 1850 5200 2100
Wire Wire Line
	5200 2200 5200 2950
$Comp
L power:PWR_FLAG #FLG?
U 1 1 5CA5D62B
P 7850 1850
AR Path="/5C9C60CA/5CA5D62B" Ref="#FLG?"  Part="1" 
AR Path="/5CA5D62B" Ref="#FLG0102"  Part="1" 
F 0 "#FLG0102" H 7850 1925 50  0001 C CNN
F 1 "PWR_FLAG" H 7850 2016 40  0000 C CNN
F 2 "" H 7850 1850 50  0001 C CNN
F 3 "" H 7850 1850 50  0001 C CNN
	1    7850 1850
	1    0    0    -1  
$EndComp
$Comp
L yageo:RL1206FR-070R027L R?
U 1 1 5CA5D636
P 7500 1850
AR Path="/5C9C60CA/5CA5D636" Ref="R?"  Part="1" 
AR Path="/5CA5D636" Ref="R103"  Part="1" 
F 0 "R103" H 7500 2038 40  0000 C CNN
F 1 "27mF(1/4W)" H 7500 1962 40  0000 C CNN
F 2 "yageo:R_1206" H 7500 1780 10  0001 C CNN
F 3 "http://rohmfs.rohm.com/jp/products/databook/datasheet/passive/resistor/chip_resistor/mcr_g-j.pdf" H 7500 1930 10  0001 C CNN
F 4 "3216" H 7500 1911 10  0000 C CNN "Size"
F 5 "Yageo" H 7700 2150 50  0001 C CNN "Manufacturer"
F 6 "RL1206FR-070R027L" H 7800 2250 50  0001 C CNN "Manufacturer Part Number"
F 7 "Ever Ohms Tech" H 7900 2350 50  0001 C CNN "Substitute Manufacturer"
F 8 "CR1206F0R027P05" H 8000 2450 50  0001 C CNN "Substitute Manufacturer Part Number"
	1    7500 1850
	1    0    0    -1  
$EndComp
Wire Wire Line
	7850 1850 8100 1850
Connection ~ 7850 1850
$Comp
L testpooint:TP1.0 TP?
U 1 1 5CA5D647
P 8100 1850
AR Path="/5C9C60CA/5CA5D647" Ref="TP?"  Part="1" 
AR Path="/5CA5D647" Ref="TP103"  Part="1" 
F 0 "TP103" H 8178 1888 40  0000 L CNN
F 1 "TP1.0" H 8178 1812 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 8000 1850 50  0001 C CNN
F 3 "" H 8100 1850 50  0000 C CNN
	1    8100 1850
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR?
U 1 1 5CA6EBB6
P 5650 3100
AR Path="/5C9C60CA/5CA6EBB6" Ref="#PWR?"  Part="1" 
AR Path="/5CA6EBB6" Ref="#PWR0112"  Part="1" 
F 0 "#PWR0112" H 5650 2850 50  0001 C CNN
F 1 "GND" H 5550 3000 40  0000 C CNN
F 2 "" H 5650 3100 50  0001 C CNN
F 3 "" H 5650 3100 50  0001 C CNN
	1    5650 3100
	1    0    0    -1  
$EndComp
Wire Wire Line
	5650 3100 5650 2950
Connection ~ 5650 2950
Wire Wire Line
	2800 7350 2800 7450
$Comp
L microchip:MCP73871T-1CCI_ML U?
U 1 1 5CB02246
P 4200 8100
AR Path="/5C9C60CA/5CB02246" Ref="U?"  Part="1" 
AR Path="/5CB02246" Ref="U104"  Part="1" 
F 0 "U104" H 4200 8994 40  0000 C CNN
F 1 "MCP73871T-1CCI_ML" H 4200 8918 40  0000 C CNN
F 2 "Housings_DFN_QFN:QFN-20-1EP_4x4mm_Pitch0.5mm_microchip_ML" H 4100 8000 50  0001 C CNN
F 3 "http://ww1.microchip.com/downloads/en/DeviceDoc/20002090D.pdf" H 4200 8100 50  0001 C CNN
F 4 "microchip" H 4200 8100 40  0001 C CNN "Manufacturer"
F 5 "MCP73871T-1CCI/ML" H 4200 8100 40  0001 C CNN "Manufacturer Part Number"
	1    4200 8100
	1    0    0    -1  
$EndComp
Wire Wire Line
	3650 7550 3600 7550
Wire Wire Line
	3600 7550 3600 7450
Connection ~ 3600 7450
Wire Wire Line
	3600 7450 3650 7450
Wire Wire Line
	3600 7650 3600 7550
Wire Wire Line
	3650 7650 3600 7650
Connection ~ 3600 7550
$Comp
L murata:GCM155R71H104KE02D C?
U 1 1 5CB02255
P 2950 7650
AR Path="/5C9C60CA/5CB02255" Ref="C?"  Part="1" 
AR Path="/5CB02255" Ref="C119"  Part="1" 
F 0 "C119" H 3000 7750 40  0000 L CNN
F 1 "0.1u/50(X7R)" H 2750 7700 40  0000 L CNN
F 2 "murata:GRM15" V 3100 7688 20  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 2950 7650 20  0001 C CNN
F 4 "1005" H 2935 7615 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 2950 7650 50  0001 C CNN "Manufacturer"
F 6 "GCM155R71H104KE02D" H 2950 7650 50  0001 C CNN "Manufacturer Part Number"
	1    2950 7650
	0    -1   1    0   
$EndComp
Wire Wire Line
	2950 7600 2950 7450
Connection ~ 2950 7450
Wire Wire Line
	2950 7450 3100 7450
$Comp
L power:GND #PWR?
U 1 1 5CB0225F
P 2950 7850
AR Path="/5C9C60CA/5CB0225F" Ref="#PWR?"  Part="1" 
AR Path="/5CB0225F" Ref="#PWR0127"  Part="1" 
F 0 "#PWR0127" H 2950 7600 50  0001 C CNN
F 1 "GND" H 2955 7684 40  0000 C CNN
F 2 "" H 2950 7850 50  0001 C CNN
F 3 "" H 2950 7850 50  0001 C CNN
	1    2950 7850
	1    0    0    -1  
$EndComp
Wire Wire Line
	2950 7850 2950 7700
$Comp
L murata:GRM188R61C475KAAJD C?
U 1 1 5CB02267
P 4950 7550
AR Path="/5C9C60CA/5CB02267" Ref="C?"  Part="1" 
AR Path="/5CB02267" Ref="C117"  Part="1" 
F 0 "C117" V 4899 7603 40  0000 L CNN
F 1 "4.7u/16(X5R)" V 4975 7603 40  0000 L CNN
F 2 "murata:GRM18" H 5050 7575 10  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 4950 7550 10  0001 C CNN
F 4 "1608" V 5026 7603 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 4950 7550 50  0001 C CNN "Manufacturer"
F 6 "GRM188R61C475KAAJD" H 4950 7550 50  0001 C CNN "Manufacturer Part Number"
	1    4950 7550
	0    1    1    0   
$EndComp
Wire Wire Line
	4750 7550 4850 7550
Wire Wire Line
	4850 7550 4850 7450
Wire Wire Line
	4850 7450 4750 7450
Wire Wire Line
	4950 7500 4950 7450
Wire Wire Line
	4950 7450 4850 7450
Connection ~ 4850 7450
$Comp
L power:GND #PWR?
U 1 1 5CB02274
P 4950 7600
AR Path="/5C9C60CA/5CB02274" Ref="#PWR?"  Part="1" 
AR Path="/5CB02274" Ref="#PWR0124"  Part="1" 
F 0 "#PWR0124" H 4950 7350 50  0001 C CNN
F 1 "GND" H 5050 7500 40  0000 C CNN
F 2 "" H 4950 7600 50  0001 C CNN
F 3 "" H 4950 7600 50  0001 C CNN
	1    4950 7600
	1    0    0    -1  
$EndComp
Wire Wire Line
	4750 7750 4850 7750
Wire Wire Line
	4850 7750 4850 7850
Wire Wire Line
	4850 7850 4750 7850
Wire Wire Line
	4750 7950 4850 7950
Wire Wire Line
	4850 7950 4850 7850
Connection ~ 4850 7850
Wire Wire Line
	4850 7750 4950 7750
Wire Wire Line
	4950 7750 4950 7800
Connection ~ 4850 7750
$Comp
L murata:GRM188R61C475KAAJD C?
U 1 1 5CB02284
P 4950 7850
AR Path="/5C9C60CA/5CB02284" Ref="C?"  Part="1" 
AR Path="/5CB02284" Ref="C120"  Part="1" 
F 0 "C120" V 4899 7903 40  0000 L CNN
F 1 "4.7u/16(X5R)" V 4975 7903 40  0000 L CNN
F 2 "murata:GRM18" H 5050 7875 10  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 4950 7850 10  0001 C CNN
F 4 "1608" V 5026 7903 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 4950 7850 50  0001 C CNN "Manufacturer"
F 6 "GRM188R61C475KAAJD" H 4950 7850 50  0001 C CNN "Manufacturer Part Number"
	1    4950 7850
	0    1    1    0   
$EndComp
$Comp
L power:GND #PWR?
U 1 1 5CB0228B
P 4950 7900
AR Path="/5C9C60CA/5CB0228B" Ref="#PWR?"  Part="1" 
AR Path="/5CB0228B" Ref="#PWR0128"  Part="1" 
F 0 "#PWR0128" H 4950 7650 50  0001 C CNN
F 1 "GND" H 5050 7800 40  0000 C CNN
F 2 "" H 4950 7900 50  0001 C CNN
F 3 "" H 4950 7900 50  0001 C CNN
	1    4950 7900
	1    0    0    -1  
$EndComp
Wire Wire Line
	4950 7450 5100 7450
Connection ~ 4950 7450
Wire Wire Line
	4750 8550 4850 8550
Wire Wire Line
	4850 8550 4850 8650
Wire Wire Line
	4850 8650 4750 8650
Wire Wire Line
	4750 8750 4850 8750
Wire Wire Line
	4850 8750 4850 8650
Connection ~ 4850 8650
Wire Wire Line
	4850 8750 4850 8950
Connection ~ 4850 8750
$Comp
L power:GND #PWR?
U 1 1 5CB0229B
P 4850 9050
AR Path="/5C9C60CA/5CB0229B" Ref="#PWR?"  Part="1" 
AR Path="/5CB0229B" Ref="#PWR0133"  Part="1" 
F 0 "#PWR0133" H 4850 8800 50  0001 C CNN
F 1 "GND" H 4950 8950 40  0000 C CNN
F 2 "" H 4850 9050 50  0001 C CNN
F 3 "" H 4850 9050 50  0001 C CNN
	1    4850 9050
	1    0    0    -1  
$EndComp
Wire Wire Line
	4850 8950 3600 8950
Connection ~ 4850 8950
Wire Wire Line
	4850 8950 4850 9050
$Comp
L murata:GRM188R61C475KAAJD C?
U 1 1 5CB022A5
P 2800 7650
AR Path="/5C9C60CA/5CB022A5" Ref="C?"  Part="1" 
AR Path="/5CB022A5" Ref="C118"  Part="1" 
F 0 "C118" H 2850 7550 40  0000 L CNN
F 1 "4.7u/16(X5R)" H 2600 7600 40  0000 L CNN
F 2 "murata:GRM18" H 2900 7675 10  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 2800 7650 10  0001 C CNN
F 4 "1608" H 2750 7675 10  0000 C CNN "Size"
F 5 "Murata Electronics " H 2800 7650 50  0001 C CNN "Manufacturer"
F 6 "GRM188R61C475KAAJD" H 2800 7650 50  0001 C CNN "Manufacturer Part Number"
	1    2800 7650
	0    1    1    0   
$EndComp
Wire Wire Line
	2800 7600 2800 7450
Wire Wire Line
	2800 7450 2950 7450
Wire Wire Line
	2800 7700 2800 7850
$Comp
L power:GND #PWR?
U 1 1 5CB022AF
P 2800 7850
AR Path="/5C9C60CA/5CB022AF" Ref="#PWR?"  Part="1" 
AR Path="/5CB022AF" Ref="#PWR0126"  Part="1" 
F 0 "#PWR0126" H 2800 7600 50  0001 C CNN
F 1 "GND" H 2805 7684 40  0000 C CNN
F 2 "" H 2800 7850 50  0001 C CNN
F 3 "" H 2800 7850 50  0001 C CNN
	1    2800 7850
	1    0    0    -1  
$EndComp
$Comp
L yageo:RC0402FR-07100KL R?
U 1 1 5CB022B6
P 3200 8150
AR Path="/5C9C60CA/5CB022B6" Ref="R?"  Part="1" 
AR Path="/5CB022B6" Ref="R120"  Part="1" 
F 0 "R120" H 3100 8100 40  0000 L CNN
F 1 "100kF" H 2850 8100 40  0000 L CNN
F 2 "yageo:R_0402" H 3200 8080 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 3200 8230 30  0001 C CNN
F 4 "1005" H 3110 8140 10  0000 L CNN "Size"
F 5 "Yageo" H 3200 8150 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-07100KL" H 3200 8150 50  0001 C CNN "Manufacturer Part Number"
	1    3200 8150
	0    1    1    0   
$EndComp
Wire Wire Line
	3200 8200 3200 8250
Wire Wire Line
	3200 8250 3650 8250
Wire Wire Line
	3200 8100 3200 7450
Connection ~ 3200 7450
Wire Wire Line
	3650 8350 3600 8350
Wire Wire Line
	3600 8350 3600 8450
Text Notes 3650 9225 0    40   ~ 0
PROG2=L: USB100mA
Text Notes 3650 9125 0    40   ~ 0
SEL=H: AC-DC Adaptor
Wire Wire Line
	3650 8450 3600 8450
Connection ~ 3600 8450
Wire Wire Line
	3600 8450 3600 8950
Text Notes 3650 9300 0    40   ~ 0
~TE~=L: Timer Enable
$Comp
L yageo:RC0402FR-07100KL R?
U 1 1 5CB022CA
P 3100 8150
AR Path="/5C9C60CA/5CB022CA" Ref="R?"  Part="1" 
AR Path="/5CB022CA" Ref="R119"  Part="1" 
F 0 "R119" H 3000 8100 40  0000 L CNN
F 1 "OPEN" H 2750 8100 40  0000 L CNN
F 2 "yageo:R_0402" H 3100 8080 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 3100 8230 30  0001 C CNN
F 4 "1005" H 3010 8140 10  0000 L CNN "Size"
	1    3100 8150
	0    1    1    0   
$EndComp
Wire Wire Line
	3100 8100 3100 7450
Connection ~ 3100 7450
Wire Wire Line
	3100 7450 3200 7450
Wire Wire Line
	3100 8200 3100 8550
Wire Wire Line
	3100 8550 3650 8550
Text Notes 5050 9100 0    40   ~ 0
PROG1: Fast charge current regulation setting: IREG(mA) = 1000(V)/RPROG1(kohm)
Text Notes 5050 9200 0    40   ~ 0
PROG3: Charge terminate current: ITERM(mA) = 1000(V)/RPROG3(kohm)
$Comp
L power:VCC #PWR?
U 1 1 5CB022D8
P 5100 7350
AR Path="/5C9C60CA/5CB022D8" Ref="#PWR?"  Part="1" 
AR Path="/5CB022D8" Ref="#PWR0122"  Part="1" 
F 0 "#PWR0122" H 5100 7200 50  0001 C CNN
F 1 "VCC" H 5115 7523 50  0000 C CNN
F 2 "" H 5100 7350 50  0001 C CNN
F 3 "" H 5100 7350 50  0001 C CNN
	1    5100 7350
	1    0    0    -1  
$EndComp
Wire Wire Line
	5100 7350 5100 7450
Wire Wire Line
	5000 8700 5000 8350
Wire Wire Line
	5000 8350 4750 8350
Wire Wire Line
	5000 8800 5000 8950
Wire Wire Line
	5000 8950 4850 8950
Wire Wire Line
	5250 8700 5250 8550
Wire Wire Line
	5250 8250 4750 8250
Wire Wire Line
	5250 8800 5250 8950
Wire Wire Line
	5250 8950 5000 8950
Connection ~ 5000 8950
Wire Notes Line
	4950 8650 5450 8650
Wire Notes Line
	5450 8650 5450 8900
Wire Notes Line
	5450 8900 4950 8900
Wire Notes Line
	4950 8900 4950 8650
Text Notes 5300 8950 0    40   ~ 0
!!!TEMPORARY VALUE!!!
Text Notes 6700 7900 0    40   ~ 0
Connect to LiPo
Wire Wire Line
	3650 8050 3500 8050
Wire Wire Line
	3500 8050 3500 9500
Wire Wire Line
	3500 9500 4100 9500
Wire Wire Line
	3650 7950 3400 7950
Wire Wire Line
	3400 7950 3400 9600
Wire Wire Line
	3400 9600 4100 9600
Wire Wire Line
	3650 7850 3300 7850
Wire Wire Line
	3300 7850 3300 9700
Wire Wire Line
	3300 9700 4100 9700
Text Label 3650 9700 0    50   ~ 0
~CHG_PG
Text Label 3650 9600 0    50   ~ 0
CHG_STAT2
Text Label 3650 9500 0    50   ~ 0
CHG_STAT1
Wire Wire Line
	3100 8550 3100 8700
Connection ~ 3100 8550
Text Label 3650 9400 0    50   ~ 0
CHG_EN
Connection ~ 4950 7750
$Comp
L power:+5V #PWR?
U 1 1 5CB02304
P 2800 7350
AR Path="/5C9C60CA/5CB02304" Ref="#PWR?"  Part="1" 
AR Path="/5CB02304" Ref="#PWR0121"  Part="1" 
F 0 "#PWR0121" H 2800 7200 50  0001 C CNN
F 1 "+5V" H 2815 7523 50  0000 C CNN
F 2 "" H 2800 7350 50  0001 C CNN
F 3 "" H 2800 7350 50  0001 C CNN
	1    2800 7350
	1    0    0    -1  
$EndComp
Connection ~ 5250 8950
Connection ~ 2800 7450
Wire Wire Line
	4750 8050 5750 8050
$Comp
L jst:S2B-PH-SM4-TB(LF)(SN) CN?
U 1 1 5CB0230F
P 6600 8000
AR Path="/5C9C60CA/5CB0230F" Ref="CN?"  Part="1" 
AR Path="/5CB0230F" Ref="CN104"  Part="1" 
F 0 "CN104" H 6800 8000 40  0000 C CNN
F 1 "S2B-PH-SM4-TB(LF)(SN)" H 7100 7900 40  0000 C CNN
F 2 "Connectors_JST:S2B-PH-SM4-TB" H 6600 7850 60  0001 C CNN
F 3 "http://www.jst-mfg.com/product/pdf/eng/ePH.pdf" H 6600 7850 60  0001 C CNN
F 4 "JST" H -8200 4250 50  0001 C CNN "Manufacturer"
F 5 "S2B-PH-SM4-TB(LF)(SN)" H -8200 4250 50  0001 C CNN "Manufacturer Part Number"
	1    6600 8000
	1    0    0    -1  
$EndComp
Wire Wire Line
	6400 7900 6250 7900
Wire Wire Line
	6250 7900 6250 7750
Wire Wire Line
	6250 7750 5650 7750
Wire Wire Line
	6400 8000 6300 8000
Wire Wire Line
	6150 8000 6150 8050
$Comp
L murata:NCP15XH103F03RC R?
U 1 1 5CB0231C
P 5800 8050
AR Path="/5C9C60CA/5CB0231C" Ref="R?"  Part="1" 
AR Path="/5CB0231C" Ref="R118"  Part="1" 
F 0 "R118" H 5800 8242 40  0000 C CNN
F 1 "NCP15XH103F03RC" H 5800 8166 40  0000 C CNN
F 2 "murata:NTC_0402" H 5700 8050 50  0001 C CNN
F 3 "https://www.murata.com/en-us/api/pdfdownloadapi?cate=&partno=NCP15XH103F03RC" H 5800 8150 50  0001 C CNN
F 4 "Murata Electronics" H 5800 8050 50  0001 C CNN "Manufacturer"
F 5 "NCP15XH103F03RC" H 5800 8050 50  0001 C CNN "Manufacturer Part Number"
	1    5800 8050
	1    0    0    -1  
$EndComp
Wire Wire Line
	5850 8050 6150 8050
Connection ~ 6150 8050
Wire Wire Line
	6150 8050 6150 8550
Wire Wire Line
	3200 7450 3600 7450
$Comp
L yageo:RC0402FR-07100KL R?
U 1 1 5CB02328
P 3100 8750
AR Path="/5C9C60CA/5CB02328" Ref="R?"  Part="1" 
AR Path="/5CB02328" Ref="R126"  Part="1" 
F 0 "R126" H 3150 8700 40  0000 L CNN
F 1 "100kF" H 3050 8850 40  0000 L CNN
F 2 "yageo:R_0402" H 3100 8680 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 3100 8830 30  0001 C CNN
F 4 "1005" H 3080 8780 10  0000 L CNN "Size"
F 5 "Yageo" H 3100 8750 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-07100KL" H 3100 8750 50  0001 C CNN "Manufacturer Part Number"
	1    3100 8750
	0    1    1    0   
$EndComp
Wire Wire Line
	3100 8800 3100 8950
Wire Wire Line
	3100 8950 3600 8950
Connection ~ 3600 8950
Wire Wire Line
	3100 8550 2950 8550
Wire Wire Line
	2950 8550 2950 9400
Wire Wire Line
	2950 9400 4100 9400
Wire Wire Line
	6400 8100 6300 8100
Wire Wire Line
	6300 8100 6300 8000
Connection ~ 6300 8000
Wire Wire Line
	6300 8000 6150 8000
$Comp
L yageo:RC0603FR-07100KL R?
U 1 1 5CB0233A
P 5000 8750
AR Path="/5C9C60CA/5CB0233A" Ref="R?"  Part="1" 
AR Path="/5CB0233A" Ref="R123"  Part="1" 
F 0 "R123" V 4950 8775 40  0000 L CNN
F 1 "100kF" V 5025 8775 40  0000 L CNN
F 2 "yageo:R_0603" V 4930 8750 10  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" V 5080 8750 10  0001 C CNN
F 4 "1608" V 5075 8800 10  0000 L CNN "Size"
F 5 "Yageo" H 5000 8750 50  0001 C CNN "Manufacturer"
F 6 "RC0603FR-07100KL" H 5000 8750 50  0001 C CNN "Manufacturer Part Number"
	1    5000 8750
	0    1    1    0   
$EndComp
$Comp
L yageo:RC0603FR-0710KL R?
U 1 1 5CB02342
P 5250 8750
AR Path="/5C9C60CA/5CB02342" Ref="R?"  Part="1" 
AR Path="/5CB02342" Ref="R124"  Part="1" 
F 0 "R124" V 5200 8800 40  0000 L CNN
F 1 "10kF" V 5300 8800 40  0000 L CNN
F 2 "yageo:R_0603" V 5180 8750 10  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" V 5330 8750 10  0001 C CNN
F 4 "1608" H 5230 8720 10  0000 L CNN "Size"
F 5 "Yageo" H 5250 8750 50  0001 C CNN "Manufacturer"
F 6 "RC0603FR-0710KL" H 5250 8750 50  0001 C CNN "Manufacturer Part Number"
	1    5250 8750
	0    1    1    0   
$EndComp
Wire Wire Line
	5250 8950 6150 8950
Wire Wire Line
	12600 1850 13100 1850
$Comp
L power:+5V #PWR?
U 1 1 5CB29C45
P 13100 1800
AR Path="/5C9C60CA/5CB29C45" Ref="#PWR?"  Part="1" 
AR Path="/5CB29C45" Ref="#PWR0101"  Part="1" 
F 0 "#PWR0101" H 13100 1650 50  0001 C CNN
F 1 "+5V" H 13115 1966 40  0000 C CNN
F 2 "" H 13100 1800 50  0001 C CNN
F 3 "" H 13100 1800 50  0001 C CNN
	1    13100 1800
	1    0    0    -1  
$EndComp
Wire Wire Line
	13100 1800 13100 1850
$Comp
L testpooint:TP1.0 TP?
U 1 1 5CB3705E
P 13100 1850
AR Path="/5C9ACAA6/5CB3705E" Ref="TP?"  Part="1" 
AR Path="/5CB3705E" Ref="TP101"  Part="1" 
F 0 "TP101" H 13178 1888 40  0000 L CNN
F 1 "TP1.0" H 13178 1812 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 13000 1850 50  0001 C CNN
F 3 "" H 13100 1850 50  0000 C CNN
	1    13100 1850
	1    0    0    -1  
$EndComp
Connection ~ 13100 1850
$Comp
L power:GND #PWR0136
U 1 1 5CB37F5F
P 9200 8700
F 0 "#PWR0136" H 9200 8450 50  0001 C CNN
F 1 "GND" H 9205 8534 40  0000 C CNN
F 2 "" H 9200 8700 50  0001 C CNN
F 3 "" H 9200 8700 50  0001 C CNN
	1    9200 8700
	1    0    0    -1  
$EndComp
$Comp
L murata:GRM188R61A226ME15D C122
U 1 1 5CB37F66
P 12250 8350
F 0 "C122" H 12250 8300 40  0000 L CNN
F 1 "22u/10(X5R)" H 12030 8410 40  0000 L CNN
F 2 "murata:GRM18" H 12350 8375 10  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 12250 8350 10  0001 C CNN
F 4 "1608" H 12180 8370 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 12250 8350 50  0001 C CNN "Manufacturer"
F 6 "GRM188R61A226ME15D" H 12250 8350 50  0001 C CNN "Manufacturer Part Number"
	1    12250 8350
	0    1    1    0   
$EndComp
$Comp
L power:GND #PWR?
U 1 1 5CB37FAF
P 12250 8850
AR Path="/5C9C60CA/5CB37FAF" Ref="#PWR?"  Part="1" 
AR Path="/5CB37FAF" Ref="#PWR0130"  Part="1" 
F 0 "#PWR0130" H 12250 8600 50  0001 C CNN
F 1 "GND" H 12255 8684 40  0000 C CNN
F 2 "" H 12250 8850 50  0001 C CNN
F 3 "" H 12250 8850 50  0001 C CNN
	1    12250 8850
	1    0    0    -1  
$EndComp
Wire Wire Line
	10650 8050 10650 8300
Wire Wire Line
	10650 8400 10650 8550
Wire Wire Line
	11900 8550 12050 8550
Connection ~ 12250 8550
Wire Wire Line
	10650 8050 10950 8050
Wire Wire Line
	12250 8050 12250 8300
Wire Wire Line
	12500 8050 12450 8050
Connection ~ 12250 8050
$Comp
L murata:GRM188R61A226ME15D C123
U 1 1 5CB37FCE
P 12950 8350
F 0 "C123" V 12899 8403 40  0000 L CNN
F 1 "OPEN" V 12975 8403 40  0000 L CNN
F 2 "murata:GRM18" H 13050 8375 10  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 12950 8350 10  0001 C CNN
F 4 "1608" V 13026 8403 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 12950 8350 50  0001 C CNN "Manufacturer"
F 6 "GRM18" H 12950 8350 50  0001 C CNN "Manufacturer Part Number"
	1    12950 8350
	0    1    1    0   
$EndComp
Wire Wire Line
	12950 8300 12950 8050
Wire Wire Line
	12950 8050 12900 8050
Wire Wire Line
	10950 8100 10950 8050
Connection ~ 10950 8050
Wire Wire Line
	10950 8050 12250 8050
Wire Wire Line
	10950 8200 10950 8350
Wire Wire Line
	10950 8550 10650 8550
Wire Wire Line
	8850 8200 8850 7950
$Comp
L power:GND #PWR0135
U 1 1 5CB37FE4
P 8850 8350
F 0 "#PWR0135" H 8850 8100 50  0001 C CNN
F 1 "GND" H 8855 8184 40  0000 C CNN
F 2 "" H 8850 8350 50  0001 C CNN
F 3 "" H 8850 8350 50  0001 C CNN
	1    8850 8350
	1    0    0    -1  
$EndComp
Wire Wire Line
	8850 8350 8850 8300
$Comp
L power:VCC #PWR0132
U 1 1 5CB37FF2
P 8300 7900
F 0 "#PWR0132" H 8300 7750 50  0001 C CNN
F 1 "VCC" H 8315 8073 50  0000 C CNN
F 2 "" H 8300 7900 50  0001 C CNN
F 3 "" H 8300 7900 50  0001 C CNN
	1    8300 7900
	1    0    0    -1  
$EndComp
Wire Wire Line
	8300 7900 8300 7950
Text Notes 9450 7100 0    40   ~ 0
VOUT = 0.496*(1+820k/91k) = 4.965V
$Comp
L power:PWR_FLAG #FLG0103
U 1 1 5CB3801A
P 13150 8050
F 0 "#FLG0103" H 13150 8125 50  0001 C CNN
F 1 "PWR_FLAG" H 13150 8224 50  0001 C CNN
F 2 "" H 13150 8050 50  0001 C CNN
F 3 "" H 13150 8050 50  0001 C CNN
	1    13150 8050
	1    0    0    -1  
$EndComp
Connection ~ 13150 8050
Wire Wire Line
	12250 8400 12250 8550
$Comp
L power:GND #PWR?
U 1 1 5CB4D1A3
P 12950 8850
AR Path="/5C9C60CA/5CB4D1A3" Ref="#PWR?"  Part="1" 
AR Path="/5CB4D1A3" Ref="#PWR0131"  Part="1" 
F 0 "#PWR0131" H 12950 8600 50  0001 C CNN
F 1 "GND" H 12955 8684 40  0000 C CNN
F 2 "" H 12950 8850 50  0001 C CNN
F 3 "" H 12950 8850 50  0001 C CNN
	1    12950 8850
	1    0    0    -1  
$EndComp
Wire Wire Line
	12950 8400 12950 8850
$Comp
L RF_Solutions:CON-SMA-EDGE-S CN101
U 1 1 5CAFDA5C
P 1450 2250
F 0 "CN101" H 2150 2300 40  0000 C CNN
F 1 "CON-SMA-EDGE-S" H 1900 2200 40  0000 C CNN
F 2 "RF_Solutions:CON-SMA-EDGE-S" H 1350 2250 40  0001 C CNN
F 3 "https://media.digikey.com/pdf/Data%20Sheets/RF%20Solutions%20PDFs/CON-SMA-EDGE.pdf" H 1450 2250 50  0001 C CNN
F 4 "RF Solutions" H 1450 2250 40  0001 C CNN "Manufacturer"
F 5 "CON-SMA-EDGE-S" H 1450 2250 40  0001 C CNN "Manufacturer Part Number"
	1    1450 2250
	-1   0    0    -1  
$EndComp
Wire Wire Line
	7550 1850 7600 1850
$Comp
L murata:GCM155R71H104KE02D C?
U 1 1 5CBDA4BB
P 9200 5350
AR Path="/5CB4C022/5CBDA4BB" Ref="C?"  Part="1" 
AR Path="/5CBDA4BB" Ref="C116"  Part="1" 
F 0 "C116" H 9275 5475 40  0000 L CNN
F 1 "0.1u/50(X7R)" H 9100 5425 40  0000 L CNN
F 2 "murata:GRM15" V 9350 5388 20  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 9200 5350 20  0001 C CNN
F 4 "1005" H 9185 5315 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 9200 5350 50  0001 C CNN "Manufacturer"
F 6 "GCM155R71H104KE02D" H 9200 5350 50  0001 C CNN "Manufacturer Part Number"
	1    9200 5350
	0    -1   1    0   
$EndComp
Wire Wire Line
	9200 5300 9200 5200
Wire Wire Line
	9200 5200 9300 5200
Wire Wire Line
	9200 5600 9300 5600
Wire Wire Line
	9200 5400 9200 5600
Wire Wire Line
	9200 5600 9200 5700
Wire Wire Line
	9200 5700 9300 5700
Connection ~ 9200 5600
Connection ~ 9200 5200
$Comp
L yageo:RC0603FR-070RL R?
U 1 1 5CBDA4DA
P 10500 5850
AR Path="/5CB4C022/5CBDA4DA" Ref="R?"  Part="1" 
AR Path="/5CBDA4DA" Ref="R117"  Part="1" 
F 0 "R117" H 10500 5950 40  0000 C CNN
F 1 "0" H 10500 5900 40  0000 C CNN
F 2 "yageo:R_0603" H 10500 5780 10  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 10500 5930 10  0001 C CNN
F 4 "1608" H 10500 5820 10  0000 C CNN "Size"
F 5 "Yageo" H 10500 5850 50  0001 C CNN "Manufacturer"
F 6 "RC0603FR-070RL" H 10500 5850 50  0001 C CNN "Manufacturer Part Number"
	1    10500 5850
	0    1    1    0   
$EndComp
$Comp
L power:GND #PWR?
U 1 1 5CBDA4E1
P 10500 6000
AR Path="/5CB4C022/5CBDA4E1" Ref="#PWR?"  Part="1" 
AR Path="/5CBDA4E1" Ref="#PWR0120"  Part="1" 
F 0 "#PWR0120" H 10500 5750 50  0001 C CNN
F 1 "GND" H 10600 5900 40  0000 C CNN
F 2 "" H 10500 6000 50  0001 C CNN
F 3 "" H 10500 6000 50  0001 C CNN
	1    10500 6000
	1    0    0    -1  
$EndComp
Wire Wire Line
	10500 6000 10500 5900
$Comp
L power:GND #PWR?
U 1 1 5CBDA4E8
P 9200 6000
AR Path="/5CB4C022/5CBDA4E8" Ref="#PWR?"  Part="1" 
AR Path="/5CBDA4E8" Ref="#PWR0119"  Part="1" 
F 0 "#PWR0119" H 9200 5750 50  0001 C CNN
F 1 "GND" H 9300 5900 40  0000 C CNN
F 2 "" H 9200 6000 50  0001 C CNN
F 3 "" H 9200 6000 50  0001 C CNN
	1    9200 6000
	1    0    0    -1  
$EndComp
Wire Wire Line
	9200 6000 9200 5700
Connection ~ 9200 5700
Wire Wire Line
	10400 5200 10500 5200
Wire Wire Line
	10500 5800 10500 5200
Connection ~ 7600 1850
Wire Wire Line
	7600 1850 7850 1850
Wire Wire Line
	12950 8050 13150 8050
Connection ~ 12950 8050
Text Notes 9450 7200 0    40   ~ 0
VOUT = 0.496*(1+820k/143k) = 3.340V
Wire Wire Line
	11900 8300 12050 8300
Wire Wire Line
	12050 8300 12050 8550
Wire Wire Line
	11500 8550 10950 8550
Connection ~ 10950 8550
Wire Wire Line
	11700 8400 11700 8550
Wire Wire Line
	11700 8550 11800 8550
Wire Wire Line
	11800 8300 11700 8300
Text Label 13750 8050 0    50   ~ 0
VOUT
Wire Wire Line
	3900 2150 3900 2250
$Comp
L Nidec_Copal_Electronics:CUS-12TB SW101
U 1 1 5CDC56C9
P 11550 7250
F 0 "SW101" H 11323 7206 40  0000 R CNN
F 1 "CUS-12TB" H 11323 7282 40  0000 R CNN
F 2 "Nidec_Copal_Electronics:CUS-12TB" H 11675 7350 20  0001 C CNN
F 3 "https://www.nidec-copal-electronics.com/e/catalog/switch/cus.pdf" H 11675 7350 20  0001 C CNN
F 4 "Nidec Copal Electronics" H 11450 7560 50  0001 C CNN "Manufacturer"
F 5 "CUS-12TB" H 11550 7710 50  0001 C CNN "Manufacturer Part Number"
	1    11550 7250
	1    0    0    1   
$EndComp
Wire Wire Line
	11400 7350 11400 8400
Wire Wire Line
	11400 8400 11700 8400
Wire Wire Line
	11700 7350 11700 8300
$Comp
L power:GND #PWR?
U 1 1 5CE27D4D
P 12200 7300
AR Path="/5C9C60CA/5CE27D4D" Ref="#PWR?"  Part="1" 
AR Path="/5CE27D4D" Ref="#PWR0123"  Part="1" 
F 0 "#PWR0123" H 12200 7050 50  0001 C CNN
F 1 "GND" H 12205 7134 40  0000 C CNN
F 2 "" H 12200 7300 50  0001 C CNN
F 3 "" H 12200 7300 50  0001 C CNN
	1    12200 7300
	1    0    0    -1  
$EndComp
Wire Wire Line
	12200 7300 12200 7200
$Comp
L bourns:CG0402MLC-3.3LG VD101
U 1 1 5CE3BB2E
P 11850 7600
F 0 "VD101" H 11797 7562 40  0000 R CNN
F 1 "CG0402MLC-3.3LG" H 11797 7638 40  0000 R CNN
F 2 "bourns:CG0402" V 11750 7600 30  0001 C CNN
F 3 "https://www.bourns.com/docs/Product-Datasheets/MLC.pdf" V 11910 7554 60  0001 C CNN
F 4 "Bourns Inc." V 12050 7650 50  0001 C CNN "Manufacturer"
F 5 "CG0402MLC-3.3LG" V 12150 7750 50  0001 C CNN "Manufacturer Part Number"
	1    11850 7600
	-1   0    0    1   
$EndComp
Wire Wire Line
	11850 7650 11850 7700
$Comp
L power:GND #PWR?
U 1 1 5CE63F18
P 11850 7700
AR Path="/5C9C60CA/5CE63F18" Ref="#PWR?"  Part="1" 
AR Path="/5CE63F18" Ref="#PWR0125"  Part="1" 
F 0 "#PWR0125" H 11850 7450 50  0001 C CNN
F 1 "GND" H 11855 7534 40  0000 C CNN
F 2 "" H 11850 7700 50  0001 C CNN
F 3 "" H 11850 7700 50  0001 C CNN
	1    11850 7700
	1    0    0    -1  
$EndComp
Wire Wire Line
	11600 7350 11600 7450
Wire Wire Line
	11850 7550 11850 7450
Wire Wire Line
	11850 7450 11600 7450
Wire Wire Line
	11500 7450 11500 8550
Wire Wire Line
	1450 2250 1450 1400
Wire Wire Line
	1450 1400 2400 1400
Wire Wire Line
	3250 1400 3250 2250
Wire Wire Line
	3250 2250 3900 2250
Connection ~ 3900 2250
Wire Wire Line
	4300 2400 3250 2400
Wire Wire Line
	3250 2400 3250 3400
Wire Wire Line
	1450 2300 1450 3400
Text Notes 11100 7050 0    40   ~ 0
3.3V/5.0V Output Voltage Selector
Wire Wire Line
	13150 8050 13350 8050
$Comp
L power:GND #PWR?
U 1 1 5CE18FBA
P 14600 8300
AR Path="/5C9C60CA/5CE18FBA" Ref="#PWR?"  Part="1" 
AR Path="/5CE18FBA" Ref="#PWR0129"  Part="1" 
F 0 "#PWR0129" H 14600 8050 50  0001 C CNN
F 1 "GND" H 14605 8134 40  0000 C CNN
F 2 "" H 14600 8300 50  0001 C CNN
F 3 "" H 14600 8300 50  0001 C CNN
	1    14600 8300
	1    0    0    -1  
$EndComp
$Comp
L jst:SM04B-SRSS-TB(LF)(SN) CN103
U 1 1 5CE37C5D
P 13050 5650
F 0 "CN103" H 13128 5683 40  0000 L CNN
F 1 "SM04B-SRSS-TB(LF)(SN)" H 13128 5607 40  0000 L CNN
F 2 "Connectors_JST:SM04B-SRSS-TB" H 13050 5500 60  0001 C CNN
F 3 "http://www.jst-mfg.com/product/pdf/eng/eSH.pdf" H 13050 5500 60  0001 C CNN
F 4 "JST" H 13150 6000 50  0001 C CNN "Manufacturer"
F 5 "SM04B-SRSS-TB(LF)(SN)" H 13250 6100 50  0001 C CNN "Manufacturer Part Number"
	1    13050 5650
	1    0    0    -1  
$EndComp
Wire Wire Line
	12850 5400 12550 5400
Wire Wire Line
	12150 5700 12150 5850
$Comp
L power:GND #PWR?
U 1 1 5CE73E23
P 12150 5850
AR Path="/5C9C60CA/5CE73E23" Ref="#PWR?"  Part="1" 
AR Path="/5CE73E23" Ref="#PWR0118"  Part="1" 
F 0 "#PWR0118" H 12150 5600 50  0001 C CNN
F 1 "GND" H 12155 5684 40  0000 C CNN
F 2 "" H 12150 5850 50  0001 C CNN
F 3 "" H 12150 5850 50  0001 C CNN
	1    12150 5850
	1    0    0    -1  
$EndComp
Text Label 12150 5400 0    50   ~ 0
VEXT
Text Label 12150 5600 0    50   ~ 0
SCL
Text Label 12150 5500 0    50   ~ 0
SDA
Text Notes 13200 5300 0    50   ~ 0
Connect to \nTransmitter\n(For Debug)
Text Label 11550 5400 2    50   ~ 0
SCL
Text Label 11550 5500 2    50   ~ 0
SDA
Text Label 10950 5700 2    50   ~ 0
~ALERT
$Comp
L yageo:RC0402FR-0710KL R?
U 1 1 5CEB353E
P 11000 5250
AR Path="/5D28FBB5/5CEB353E" Ref="R?"  Part="1" 
AR Path="/5D26E750/5CEB353E" Ref="R?"  Part="1" 
AR Path="/5C9ACAA6/5CEB353E" Ref="R?"  Part="1" 
AR Path="/5CEB353E" Ref="R116"  Part="1" 
F 0 "R116" V 10949 5298 40  0000 L CNN
F 1 "10kF" V 11025 5298 40  0000 L CNN
F 2 "yageo:R_0402" H 11000 5180 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 11000 5330 30  0001 C CNN
F 4 "1005" V 11076 5298 10  0000 L CNN "Size"
F 5 "Yageo" H 11200 5350 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-0710KL" H 11250 5400 50  0001 C CNN "Manufacturer Part Number"
	1    11000 5250
	0    1    1    0   
$EndComp
Wire Wire Line
	11000 5300 11000 5700
$Comp
L testpooint:TP1.0 TP?
U 1 1 5CEF01F0
P 11000 5700
AR Path="/5C9ACAA6/5CEF01F0" Ref="TP?"  Part="1" 
AR Path="/5CEF01F0" Ref="TP109"  Part="1" 
F 0 "TP109" H 11078 5738 40  0000 L CNN
F 1 "TP1.0" H 11078 5662 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 10900 5700 50  0001 C CNN
F 3 "" H 11000 5700 50  0000 C CNN
	1    11000 5700
	1    0    0    -1  
$EndComp
$Comp
L testpooint:TP1.0 TP?
U 1 1 5CF4CABE
P 12550 5400
AR Path="/5C9ACAA6/5CF4CABE" Ref="TP?"  Part="1" 
AR Path="/5CF4CABE" Ref="TP106"  Part="1" 
F 0 "TP106" H 12350 5450 40  0000 L CNN
F 1 "TP1.0" H 12650 5450 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 12450 5400 50  0001 C CNN
F 3 "" H 12550 5400 50  0000 C CNN
	1    12550 5400
	1    0    0    -1  
$EndComp
Wire Wire Line
	12150 5700 12550 5700
$Comp
L testpooint:TP1.0 TP?
U 1 1 5CF4D2F5
P 12550 5500
AR Path="/5C9ACAA6/5CF4D2F5" Ref="TP?"  Part="1" 
AR Path="/5CF4D2F5" Ref="TP107"  Part="1" 
F 0 "TP107" H 12350 5550 40  0000 L CNN
F 1 "TP1.0" H 12650 5550 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 12450 5500 50  0001 C CNN
F 3 "" H 12550 5500 50  0000 C CNN
	1    12550 5500
	1    0    0    -1  
$EndComp
Wire Wire Line
	12550 5500 12850 5500
$Comp
L testpooint:TP1.0 TP?
U 1 1 5CF4D3AD
P 12550 5600
AR Path="/5C9ACAA6/5CF4D3AD" Ref="TP?"  Part="1" 
AR Path="/5CF4D3AD" Ref="TP108"  Part="1" 
F 0 "TP108" H 12350 5650 40  0000 L CNN
F 1 "TP1.0" H 12650 5650 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 12450 5600 50  0001 C CNN
F 3 "" H 12550 5600 50  0000 C CNN
	1    12550 5600
	1    0    0    -1  
$EndComp
Wire Wire Line
	12550 5600 12850 5600
$Comp
L testpooint:TP1.0 TP?
U 1 1 5CF4D467
P 12550 5700
AR Path="/5C9ACAA6/5CF4D467" Ref="TP?"  Part="1" 
AR Path="/5CF4D467" Ref="TP110"  Part="1" 
F 0 "TP110" H 12350 5750 40  0000 L CNN
F 1 "TP1.0" H 12650 5750 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 12450 5700 50  0001 C CNN
F 3 "" H 12550 5700 50  0000 C CNN
	1    12550 5700
	1    0    0    -1  
$EndComp
Wire Wire Line
	12550 5700 12750 5700
Wire Wire Line
	10400 5700 11000 5700
Connection ~ 11000 5700
$Comp
L testpooint:TP1.0 TP?
U 1 1 5D009AD5
P 14600 8050
AR Path="/5C9ACAA6/5D009AD5" Ref="TP?"  Part="1" 
AR Path="/5D009AD5" Ref="TP111"  Part="1" 
F 0 "TP111" H 14350 8150 40  0000 L CNN
F 1 "TP1.0" H 14350 8100 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 14500 8050 50  0001 C CNN
F 3 "" H 14600 8050 50  0000 C CNN
	1    14600 8050
	1    0    0    -1  
$EndComp
$Comp
L testpooint:TP1.0 TP?
U 1 1 5D009F81
P 14600 8150
AR Path="/5C9ACAA6/5D009F81" Ref="TP?"  Part="1" 
AR Path="/5D009F81" Ref="TP112"  Part="1" 
F 0 "TP112" H 14350 8100 40  0000 L CNN
F 1 "TP1.0" H 14350 8050 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 14500 8150 50  0001 C CNN
F 3 "" H 14600 8150 50  0000 C CNN
	1    14600 8150
	1    0    0    -1  
$EndComp
$Comp
L testpooint:TP1.0 TP?
U 1 1 5D00A164
P 8300 7950
AR Path="/5C9ACAA6/5D00A164" Ref="TP?"  Part="1" 
AR Path="/5D00A164" Ref="TP113"  Part="1" 
F 0 "TP113" H 8378 7988 40  0000 L CNN
F 1 "TP1.0" H 8378 7912 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 8200 7950 50  0001 C CNN
F 3 "" H 8300 7950 50  0000 C CNN
	1    8300 7950
	1    0    0    -1  
$EndComp
Connection ~ 8300 7950
Wire Wire Line
	2100 2200 2400 2200
Wire Wire Line
	2400 2200 2400 1400
Connection ~ 2400 1400
Wire Wire Line
	2100 2300 2400 2300
Wire Wire Line
	2400 2300 2400 3400
Connection ~ 2400 3400
Wire Wire Line
	2400 3400 1450 3400
Wire Wire Line
	11800 5400 11800 5600
Wire Wire Line
	10400 5400 11800 5400
Wire Wire Line
	11800 5600 12550 5600
Wire Wire Line
	10400 5500 12550 5500
Wire Wire Line
	12050 5400 12050 4350
Wire Wire Line
	12050 4350 11600 4350
Wire Wire Line
	12050 5400 12550 5400
Wire Wire Line
	11000 4350 11000 5200
Wire Wire Line
	11000 4350 9200 4350
Wire Wire Line
	9200 4350 9200 5200
Connection ~ 11000 4350
$Comp
L yageo:RC0402FR-070RL R115
U 1 1 5D27FCA4
P 11550 4350
F 0 "R115" H 11550 4538 40  0000 C CNN
F 1 "0" H 11550 4462 40  0000 C CNN
F 2 "yageo:R_0402" H 11550 4280 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 11550 4430 30  0001 C CNN
F 4 "1005" H 11550 4411 10  0000 C CNN "Size"
F 5 "Yageo" H 11750 4450 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-070RL" H 11800 4500 50  0001 C CNN "Manufacturer Part Number"
	1    11550 4350
	1    0    0    -1  
$EndComp
Wire Wire Line
	11500 4350 11000 4350
$Comp
L yageo:RC0402FR-070RL R114
U 1 1 5D27FFAB
P 9200 4200
F 0 "R114" V 9149 4248 40  0000 L CNN
F 1 "OPEN" V 9225 4248 40  0000 L CNN
F 2 "yageo:R_0402" H 9200 4130 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 9200 4280 30  0001 C CNN
F 4 "1005" V 9276 4248 10  0000 L CNN "Size"
F 5 "Yageo" H 9400 4300 50  0001 C CNN "Manufacturer"
F 6 "RC0402" H 9450 4350 50  0001 C CNN "Manufacturer Part Number"
	1    9200 4200
	0    1    1    0   
$EndComp
Wire Wire Line
	9200 4250 9200 4350
Connection ~ 9200 4350
Wire Wire Line
	9200 4150 9200 4050
$Comp
L power:+5V #PWR?
U 1 1 5D2C4066
P 9200 4050
AR Path="/5C9C60CA/5D2C4066" Ref="#PWR?"  Part="1" 
AR Path="/5D2C4066" Ref="#PWR0113"  Part="1" 
F 0 "#PWR0113" H 9200 3900 50  0001 C CNN
F 1 "+5V" H 9215 4216 40  0000 C CNN
F 2 "" H 9200 4050 50  0001 C CNN
F 3 "" H 9200 4050 50  0001 C CNN
	1    9200 4050
	1    0    0    -1  
$EndComp
Connection ~ 12550 5400
Connection ~ 12550 5500
Connection ~ 12550 5600
Connection ~ 12550 5700
Wire Wire Line
	7600 3200 9750 3200
Wire Wire Line
	9750 3200 9750 4600
Wire Wire Line
	7600 1850 7600 3200
Wire Wire Line
	9600 4600 9600 3400
Wire Wire Line
	9600 3400 7400 3400
Wire Wire Line
	7400 3400 7400 1850
Connection ~ 7400 1850
Wire Wire Line
	7400 1850 7450 1850
Text Notes 8150 4850 0    80   ~ 0
Current Monitor
Text Notes 2100 6900 0    80   ~ 0
LiPo Charger
Text Notes 8600 6850 0    80   ~ 0
DC-DC Converter (Step-Up/Down)
Wire Notes Line
	600  6450 15850 6450
Wire Notes Line
	7850 6500 7850 11050
Text Notes 1550 1000 0    80   ~ 0
RF Receiver
$Comp
L Nexperia:PMEG6010AESBYL D101
U 1 1 5CBCB8E2
P 3900 2050
F 0 "D101" H 3950 1950 40  0000 L CNN
F 1 "PMEG6010AESBYL" H 3700 2150 40  0000 L CNN
F 2 "Diodes_SMD:SOD-993_Nexperia" H 3915 2050 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/PMEG6010AESB.pdf" H 3915 2050 50  0001 C CNN
F 4 "Nexperia" H 3900 2050 50  0001 C CNN "Manufacturer"
F 5 "PMEG6010AESBYL" H 4100 2350 50  0001 C CNN "Manufacturer Part Number"
	1    3900 2050
	0    1    1    0   
$EndComp
$Comp
L Nexperia:PMEG6010AESBYL D102
U 1 1 5CC52144
P 4300 2050
F 0 "D102" H 4350 1950 40  0000 L CNN
F 1 "PMEG6010AESBYL" H 4100 2150 40  0000 L CNN
F 2 "Diodes_SMD:SOD-993_Nexperia" H 4315 2050 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/PMEG6010AESB.pdf" H 4315 2050 50  0001 C CNN
F 4 "Nexperia" H 4300 2050 50  0001 C CNN "Manufacturer"
F 5 "PMEG6010AESBYL" H 4300 2050 50  0001 C CNN "Manufacturer Part Number"
	1    4300 2050
	0    1    1    0   
$EndComp
Wire Wire Line
	4300 2150 4300 2400
$Comp
L Nexperia:PMEG6010AESBYL D106
U 1 1 5CC73B37
P 4300 2600
F 0 "D106" H 4350 2500 40  0000 L CNN
F 1 "PMEG6010AESBYL" H 4100 2700 40  0000 L CNN
F 2 "Diodes_SMD:SOD-993_Nexperia" H 4315 2600 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/PMEG6010AESB.pdf" H 4315 2600 50  0001 C CNN
F 4 "Nexperia" H 4300 2600 50  0001 C CNN "Manufacturer"
F 5 "PMEG6010AESBYL" H 4300 2600 50  0001 C CNN "Manufacturer Part Number"
	1    4300 2600
	0    1    1    0   
$EndComp
Wire Wire Line
	4300 2700 4300 2950
Wire Wire Line
	4300 2500 4300 2400
Connection ~ 4300 2400
$Comp
L Nexperia:PMEG6010AESBYL D105
U 1 1 5CCB6F0C
P 3900 2600
F 0 "D105" H 3950 2500 40  0000 L CNN
F 1 "PMEG6010AESBYL" H 3700 2700 40  0000 L CNN
F 2 "Diodes_SMD:SOD-993_Nexperia" H 3915 2600 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/PMEG6010AESB.pdf" H 3915 2600 50  0001 C CNN
F 4 "Nexperia" H 3900 2600 50  0001 C CNN "Manufacturer"
F 5 "PMEG6010AESBYL" H 3900 2600 50  0001 C CNN "Manufacturer Part Number"
	1    3900 2600
	0    1    1    0   
$EndComp
Wire Wire Line
	3900 2250 3900 2500
Wire Wire Line
	3900 2700 3900 2950
$Comp
L MPS:MP2155GQ-Z U102
U 1 1 5CE086E0
P 9850 8150
F 0 "U102" H 9150 8650 40  0000 L CNN
F 1 "MP2155GQ-Z" H 9150 8550 40  0000 L CNN
F 2 "Housings_DFN_QFN:DFN-10-1EP_3x3mm_Pitch0.5mm_MPS" H 9850 8150 30  0001 C CIN
F 3 "https://www.monolithicpower.com/pub/media/document/MP2155_r1.0.pdf" H 9850 8250 10  0001 C CNN
F 4 "Monolithic Power Systems Inc." H 9750 8650 80  0001 C CNN "Manufacturer"
F 5 "MP2155GQ-Z" H 9850 8750 80  0001 C CNN "Manufacturer Part Number"
	1    9850 8150
	1    0    0    -1  
$EndComp
$Comp
L yageo:RC0402FR-07820KL R111
U 1 1 5CE2A341
P 10650 8350
F 0 "R111" V 10599 8398 40  0000 L CNN
F 1 "820kF" V 10675 8398 40  0000 L CNN
F 2 "yageo:R_0402" H 10650 8280 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 10650 8430 30  0001 C CNN
F 4 "1005" V 10726 8398 10  0000 L CNN "Size"
F 5 "Yageo" H 10850 8450 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-07820KL" H 10900 8500 50  0001 C CNN "Manufacturer Part Number"
	1    10650 8350
	0    1    1    0   
$EndComp
$Comp
L yageo:RC0402FR-07750KL R109
U 1 1 5CE2AA1F
P 10950 8150
F 0 "R109" V 10899 8198 40  0000 L CNN
F 1 "750kF" V 10975 8198 40  0000 L CNN
F 2 "yageo:R_0402" H 10950 8080 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 10950 8230 30  0001 C CNN
F 4 "1005" V 11026 8198 10  0000 L CNN "Size"
F 5 "Yageo" H 11150 8250 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-07750KL" H 11200 8300 50  0001 C CNN "Manufacturer Part Number"
	1    10950 8150
	0    1    1    0   
$EndComp
Wire Wire Line
	12250 8550 12250 8850
$Comp
L yageo:RC0402FR-0791KL R110
U 1 1 5CE4AA19
P 11850 8300
F 0 "R110" H 11850 8488 40  0000 C CNN
F 1 "91kF" H 11850 8412 40  0000 C CNN
F 2 "yageo:R_0402" H 11850 8230 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 11850 8380 30  0001 C CNN
F 4 "1005" H 11850 8361 10  0000 C CNN "Size"
F 5 "Yageo" H 12050 8400 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-0791KL" H 12100 8450 50  0001 C CNN "Manufacturer Part Number"
	1    11850 8300
	1    0    0    -1  
$EndComp
$Comp
L yageo:RC0402FR-07143KL R121
U 1 1 5CE4AEFE
P 11850 8550
F 0 "R121" H 11850 8738 40  0000 C CNN
F 1 "143kF" H 11850 8662 40  0000 C CNN
F 2 "yageo:R_0402" H 11850 8480 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 11850 8630 30  0001 C CNN
F 4 "1005" H 11850 8611 10  0000 C CNN "Size"
F 5 "Yageo" H 12050 8650 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-07143KL" H 12100 8700 50  0001 C CNN "Manufacturer Part Number"
	1    11850 8550
	1    0    0    -1  
$EndComp
$Comp
L murata:GRM188R61A226ME15D C112
U 1 1 5CE6A676
P 12450 8350
F 0 "C112" H 12450 8300 40  0000 L CNN
F 1 "22u/10(X5R)" H 12230 8410 40  0000 L CNN
F 2 "murata:GRM18" H 12550 8375 10  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 12450 8350 10  0001 C CNN
F 4 "1608" H 12380 8370 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 12450 8350 50  0001 C CNN "Manufacturer"
F 6 "GRM188R61A226ME15D" H 12450 8350 50  0001 C CNN "Manufacturer Part Number"
	1    12450 8350
	0    1    1    0   
$EndComp
Wire Wire Line
	12450 8300 12450 8050
Connection ~ 12450 8050
Wire Wire Line
	12450 8050 12250 8050
Wire Wire Line
	12450 8400 12450 8550
Wire Wire Line
	12450 8550 12250 8550
Wire Wire Line
	10350 8050 10650 8050
Connection ~ 10650 8050
Wire Wire Line
	10350 8250 10450 8250
Wire Wire Line
	10450 8250 10450 8550
Wire Wire Line
	10450 8550 10650 8550
Connection ~ 10650 8550
Wire Wire Line
	10950 8450 10950 8550
Connection ~ 8850 7950
Wire Wire Line
	9350 8050 9300 8050
Wire Wire Line
	9300 8050 9300 7950
Wire Wire Line
	8850 7950 9050 7950
Connection ~ 9300 7950
Wire Wire Line
	9300 7950 9350 7950
Wire Wire Line
	9350 8350 9050 8350
Wire Wire Line
	9050 8350 9050 7950
Connection ~ 9050 7950
Wire Wire Line
	9050 7950 9200 7950
Wire Wire Line
	9200 8100 9200 7950
Connection ~ 9200 7950
Wire Wire Line
	9200 7950 9300 7950
Wire Wire Line
	9200 8200 9200 8250
Wire Wire Line
	9200 8250 9350 8250
Connection ~ 9200 8250
Wire Wire Line
	9200 8250 9200 8500
Wire Wire Line
	9200 8700 9200 8600
Wire Wire Line
	9750 8650 9750 8750
Wire Wire Line
	9750 8750 9850 8750
Wire Wire Line
	9850 8750 9850 8650
Wire Wire Line
	9850 8750 9950 8750
Wire Wire Line
	9950 8750 9950 8650
Connection ~ 9850 8750
Wire Wire Line
	9850 8750 9850 8850
Wire Wire Line
	8300 7950 8850 7950
$Comp
L power:GND #PWR0117
U 1 1 5D1A62E0
P 9850 8850
F 0 "#PWR0117" H 9850 8600 50  0001 C CNN
F 1 "GND" H 9855 8684 40  0000 C CNN
F 2 "" H 9850 8850 50  0001 C CNN
F 3 "" H 9850 8850 50  0001 C CNN
	1    9850 8850
	1    0    0    -1  
$EndComp
Wire Wire Line
	12050 8550 12050 8750
Wire Wire Line
	12050 8750 9950 8750
Connection ~ 12050 8550
Connection ~ 9950 8750
Wire Wire Line
	10000 7650 10000 7550
Wire Wire Line
	10000 7550 9950 7550
Wire Wire Line
	9700 7650 9700 7550
Wire Wire Line
	9700 7550 9750 7550
$Comp
L murata:DFE252012P-3R3M=P2 L102
U 1 1 5D20A7A8
P 9850 7550
F 0 "L102" H 9850 7740 50  0000 C CNN
F 1 "DFE252012P-3R3M=P2" H 9850 7649 50  0000 C CNN
F 2 "murata:DFE252012C" H 9850 7550 50  0001 C CNN
F 3 "http://bec.co.uk/downloads/dfe252012p.pdf" H 9825 7550 60  0001 C CNN
F 4 "Murata Electronics" H 9950 7800 80  0001 C CNN "Manufacturer"
F 5 "DFE252012P" H 10050 7900 80  0001 C CNN "Manufacturer Part Number"
	1    9850 7550
	1    0    0    -1  
$EndComp
$Comp
L yageo:RC0402FR-070RL R113
U 1 1 5D20B553
P 9200 8550
F 0 "R113" V 9149 8598 40  0000 L CNN
F 1 "0" V 9225 8598 40  0000 L CNN
F 2 "yageo:R_0402" H 9200 8480 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 9200 8630 30  0001 C CNN
F 4 "1005" V 9276 8598 10  0000 L CNN "Size"
F 5 "Yageo" H 9400 8650 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-070RL" H 9450 8700 50  0001 C CNN "Manufacturer Part Number"
	1    9200 8550
	0    1    1    0   
$EndComp
$Comp
L yageo:RC0402FR-070RL R108
U 1 1 5D20BCF6
P 9200 8150
F 0 "R108" V 9149 8198 40  0000 L CNN
F 1 "OPEN" V 9225 8198 40  0000 L CNN
F 2 "yageo:R_0402" H 9200 8080 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 9200 8230 30  0001 C CNN
F 4 "1005" V 9276 8198 10  0000 L CNN "Size"
F 5 "Yageo" H 9400 8250 50  0001 C CNN "Manufacturer"
F 6 "RC0402" H 9450 8300 50  0001 C CNN "Manufacturer Part Number"
	1    9200 8150
	0    1    1    0   
$EndComp
$Comp
L murata:GRM188R61E106MA73D C111
U 1 1 5D20BFBF
P 8850 8250
F 0 "C111" H 8850 8150 40  0000 L CNN
F 1 "10u/25(X5R)" H 8610 8330 40  0000 L CNN
F 2 "murata:GRM18" H 8950 8275 10  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx" H 8850 8250 10  0001 C CNN
F 4 "1608" H 8830 8290 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 9050 8550 50  0001 C CNN "Manufacturer"
F 6 "GRM188R61E106MA73D" H 9150 8650 50  0001 C CNN "Manufacturer Part Number"
	1    8850 8250
	0    1    1    0   
$EndComp
$Comp
L murata:BLM18PG330SN1D FB102
U 1 1 5D20E178
P 12700 8050
F 0 "FB102" H 12700 8242 40  0000 C CNN
F 1 "BLM18PG330SN1D" H 12700 8166 40  0000 C CNN
F 2 "murata:BLM18" H 12700 8050 30  0001 C CNN
F 3 "http://search.murata.co.jp/Ceramy/image/img/PDF/ENG/L0110S0100BLM18P.pdf" H 12675 8050 60  0001 C CNN
F 4 "Murata Electronics " H 12800 8250 50  0001 C CNN "Manufacturer"
F 5 "BLM18PG330SN1D" H 12900 8350 50  0001 C CNN "Manufacturer Part Number"
	1    12700 8050
	1    0    0    -1  
$EndComp
$Comp
L murata:GCM1555C1H680JA16D C113
U 1 1 5D231A28
P 10950 8400
F 0 "C113" V 10899 8453 40  0000 L CNN
F 1 "68p/50(C0G)" V 10975 8453 40  0000 L CNN
F 2 "murata:GRM15" H 11100 8438 20  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx" H 10950 8400 20  0001 C CNN
F 4 "1005" V 11026 8453 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 11150 8700 50  0001 C CNN "Manufacturer"
F 6 "GCM1555C1H680JA16D" H 11250 8800 50  0001 C CNN "Manufacturer Part Number"
	1    10950 8400
	0    1    1    0   
$EndComp
Text Label 10450 3200 0    50   ~ 0
PWRGD_5V
$Comp
L yageo:RC0402FR-0710KL R?
U 1 1 5E5CAC0C
P 10950 3000
AR Path="/5D28FBB5/5E5CAC0C" Ref="R?"  Part="1" 
AR Path="/5D26E750/5E5CAC0C" Ref="R?"  Part="1" 
AR Path="/5E5CAC0C" Ref="R104"  Part="1" 
F 0 "R104" V 10899 3048 40  0000 L CNN
F 1 "10kF" V 10975 3048 40  0000 L CNN
F 2 "yageo:R_0402" H 10950 2930 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 10950 3080 30  0001 C CNN
F 4 "1005" V 11026 3048 10  0000 L CNN "Size"
F 5 "Yageo" H 11150 3100 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-0710KL" H 11200 3150 50  0001 C CNN "Manufacturer Part Number"
	1    10950 3000
	0    1    1    0   
$EndComp
Wire Wire Line
	10950 3050 10950 3200
Wire Wire Line
	10400 3200 10950 3200
Wire Wire Line
	10950 2850 10950 2950
$Comp
L testpooint:TP1.0 TP114
U 1 1 5E5CAC15
P 10950 3200
F 0 "TP114" H 11028 3238 40  0000 L CNN
F 1 "TP1.0" H 11028 3162 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 10850 3200 50  0001 C CNN
F 3 "" H 10950 3200 50  0000 C CNN
	1    10950 3200
	1    0    0    -1  
$EndComp
Connection ~ 10950 3200
Wire Wire Line
	9250 1850 9150 1850
Wire Wire Line
	9250 1950 9150 1950
Wire Wire Line
	9150 1950 9150 1850
Connection ~ 9150 1850
Wire Wire Line
	9150 1850 8850 1850
Wire Wire Line
	9250 2050 9150 2050
Wire Wire Line
	9150 2050 9150 1950
Connection ~ 9150 1950
Wire Wire Line
	9250 2250 9050 2250
$Comp
L testpooint:TP1.0 TP105
U 1 1 5E5CAC25
P 9050 2250
F 0 "TP105" H 9100 2350 40  0000 L CNN
F 1 "TP1.0" H 9100 2300 40  0000 L CNN
F 2 "TestPoint:TP_1mm" H 8950 2250 50  0001 C CNN
F 3 "" H 9050 2250 50  0000 C CNN
	1    9050 2250
	1    0    0    -1  
$EndComp
Wire Wire Line
	9250 2750 9150 2750
Wire Wire Line
	9150 2750 9150 2900
$Comp
L power:GND #PWR0114
U 1 1 5E5CAC2D
P 9150 2900
F 0 "#PWR0114" H 9150 2650 50  0001 C CNN
F 1 "GND" H 9150 2750 40  0000 C CNN
F 2 "" H 9150 2900 50  0001 C CNN
F 3 "" H 9150 2900 50  0001 C CNN
	1    9150 2900
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR0115
U 1 1 5E5CAC33
P 10250 2900
F 0 "#PWR0115" H 10250 2650 50  0001 C CNN
F 1 "GND" H 10250 2750 40  0000 C CNN
F 2 "" H 10250 2900 50  0001 C CNN
F 3 "" H 10250 2900 50  0001 C CNN
	1    10250 2900
	1    0    0    -1  
$EndComp
Wire Wire Line
	10150 2750 10250 2750
Wire Wire Line
	10250 2750 10250 2900
Wire Wire Line
	10150 2650 10250 2650
Wire Wire Line
	10250 2650 10250 2750
Connection ~ 10250 2750
Wire Wire Line
	10150 2550 10250 2550
Wire Wire Line
	10250 2550 10250 2650
Connection ~ 10250 2650
Wire Wire Line
	10150 1850 10250 1850
Wire Wire Line
	10250 1850 10250 1950
Wire Wire Line
	10250 1950 10150 1950
Wire Wire Line
	10150 2050 10250 2050
Wire Wire Line
	10250 2050 10250 1950
Connection ~ 10250 1950
Wire Wire Line
	10150 2150 10250 2150
Wire Wire Line
	10250 2150 10250 2050
Connection ~ 10250 2050
Wire Wire Line
	8850 2000 8850 1850
Connection ~ 8850 1850
Wire Wire Line
	8850 1850 8600 1850
Wire Wire Line
	8850 2100 8850 2250
$Comp
L power:GND #PWR0104
U 1 1 5E5CAC4E
P 8850 2250
F 0 "#PWR0104" H 8850 2000 50  0001 C CNN
F 1 "GND" H 8850 2100 40  0000 C CNN
F 2 "" H 8850 2250 50  0001 C CNN
F 3 "" H 8850 2250 50  0001 C CNN
	1    8850 2250
	1    0    0    -1  
$EndComp
$Comp
L Semtech:TS30042-M000QFNR U101
U 1 1 5E5CAC56
P 9700 2250
F 0 "U101" H 9700 2952 40  0000 C CNN
F 1 "TS30042-M000QFNR" H 9700 2876 40  0000 C CNN
F 2 "Housings_DFN_QFN:QFN-16-1EP_3x3mm_Pitch0.5mm_Semtech" H 9700 2250 30  0001 C CIN
F 3 "https://semtech.my.salesforce.com/sfc/dist/version/download/?oid=00DE0000000JelG&ids=06844000005gjKqAAI&d=/a/44000000MCKn/3e48v2lP4vpbRsfOboAxhxdut0jxr3IIftfBJdJulOE&operationContext=DELIVERY&asPdf=true&viewId=05H2R000000nRiTUAU&dpt=" H 9700 2300 60  0001 C CNN
F 4 "Semtech" H 9700 2250 40  0001 C CNN "Manufacturer"
F 5 "TS30042-M000QFNR" H 9700 2250 40  0001 C CNN "Manufacturer Part Number"
	1    9700 2250
	1    0    0    -1  
$EndComp
$Comp
L samsung:CL31A106KBHNNNE C102
U 1 1 5E5CAC5F
P 8600 2050
F 0 "C102" V 8450 1850 40  0000 L CNN
F 1 "10u/50(X5R)" V 8525 1850 40  0000 L CNN
F 2 "murata:GRM31" H 8600 1980 10  0001 C CNN
F 3 "http://www.samsungsem.com/kr/support/product-search/mlcc/CL31A106KBHNNNE.jsp" H 8600 2130 10  0001 C CNN
F 4 "3216" H 8625 2000 10  0000 L CNN "Size"
F 5 "Samsung Electro-Mechanics" H 8800 2350 50  0001 C CNN "Manufacturer"
F 6 "CL31A106KBHNNNE" H 8900 2450 50  0001 C CNN "Manufacturer Part Number"
	1    8600 2050
	1    0    0    -1  
$EndComp
$Comp
L murata:GCM155R71H104KE02D C103
U 1 1 5E5CAC68
P 8850 2050
F 0 "C103" H 9000 1900 40  0000 L CNN
F 1 "0.1u/50(X7R)" H 8650 1975 40  0000 L CNN
F 2 "murata:GRM15" H 9000 2088 20  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 8850 2050 20  0001 C CNN
F 4 "1005" V 8900 2075 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 9050 2350 50  0001 C CNN "Manufacturer"
F 6 "GCM155R71H104KE02D" H 9150 2450 50  0001 C CNN "Manufacturer Part Number"
	1    8850 2050
	0    1    1    0   
$EndComp
Wire Wire Line
	8600 2100 8600 2250
$Comp
L power:GND #PWR0103
U 1 1 5E5CAC6F
P 8600 2250
F 0 "#PWR0103" H 8600 2000 50  0001 C CNN
F 1 "GND" H 8600 2100 40  0000 C CNN
F 2 "" H 8600 2250 50  0001 C CNN
F 3 "" H 8600 2250 50  0001 C CNN
	1    8600 2250
	1    0    0    -1  
$EndComp
Wire Wire Line
	8600 2000 8600 1850
Connection ~ 8600 1850
Wire Wire Line
	8600 1850 8100 1850
$Comp
L on_semiconductor:S210FA D103
U 1 1 5E5CAC7A
P 10450 2050
F 0 "D103" H 10500 2150 40  0000 L CNN
F 1 "S210FA" H 10350 2200 40  0000 L CNN
F 2 "Diodes_SMD:SOD-123FA_OnSemi" H 10465 2050 50  0001 C CNN
F 3 "https://www.onsemi.com/pub/Collateral/SS29FA-D.pdf" H 10465 2050 50  0001 C CNN
F 4 "ON Semiconductor" H 10550 2250 50  0001 C CNN "Manufacturer"
F 5 "S210FA" H 10650 2350 50  0001 C CNN "Manufacturer Part Number"
	1    10450 2050
	0    1    1    0   
$EndComp
Wire Wire Line
	10250 1850 10450 1850
Connection ~ 10250 1850
Wire Wire Line
	10150 2250 10650 2250
$Comp
L power:+5V #PWR?
U 1 1 5E5CAC83
P 10950 2850
AR Path="/5D28FBB5/5E5CAC83" Ref="#PWR?"  Part="1" 
AR Path="/5D26E750/5E5CAC83" Ref="#PWR?"  Part="1" 
AR Path="/5E5CAC83" Ref="#PWR0111"  Part="1" 
F 0 "#PWR0111" H 10950 2700 50  0001 C CNN
F 1 "+5V" H 10965 3023 50  0000 C CNN
F 2 "" H 10950 2850 50  0001 C CNN
F 3 "" H 10950 2850 50  0001 C CNN
	1    10950 2850
	1    0    0    -1  
$EndComp
Wire Wire Line
	10150 2450 10400 2450
Wire Wire Line
	10400 2450 10400 3200
$Comp
L murata:GRM155R71H223KA12D C101
U 1 1 5E5CAC8E
P 10300 1750
F 0 "C101" H 10300 1943 40  0000 C CNN
F 1 "0.022u/50(X7R)" H 10300 1867 40  0000 C CNN
F 2 "murata:GRM15" V 10450 1788 20  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 10300 1750 20  0001 C CNN
F 4 "1005" H 10300 1816 10  0000 C CNN "Size"
F 5 "Murata Electronics " H 10500 2050 50  0001 C CNN "Manufacturer"
F 6 "GRM155R71H223KA12D" H 10600 2150 50  0001 C CNN "Manufacturer Part Number"
	1    10300 1750
	1    0    0    -1  
$EndComp
Wire Wire Line
	10150 1750 10250 1750
Wire Wire Line
	10350 1750 10550 1750
Wire Wire Line
	10550 1750 10550 1850
Wire Wire Line
	10450 1850 10450 1950
Connection ~ 10450 1850
Wire Wire Line
	10450 1850 10550 1850
Connection ~ 10550 1850
Wire Wire Line
	10550 1850 10650 1850
$Comp
L murata:GCM155R71H104KE02D C104
U 1 1 5E5CAC9F
P 11000 2050
F 0 "C104" H 11150 1900 40  0000 L CNN
F 1 "0.1u/50(X7R)" H 10800 1975 40  0000 L CNN
F 2 "murata:GRM15" H 11150 2088 20  0001 C CNN
F 3 "http://www.murata.com/~/media/webrenewal/support/library/catalog/products/capacitor/mlcc/c02e.ashx?la=en" H 11000 2050 20  0001 C CNN
F 4 "1005" H 10925 2025 10  0000 L CNN "Size"
F 5 "Murata Electronics " H 11200 2350 50  0001 C CNN "Manufacturer"
F 6 "GCM155R71H104KE02D" H 11300 2450 50  0001 C CNN "Manufacturer Part Number"
	1    11000 2050
	0    1    1    0   
$EndComp
Wire Wire Line
	10850 1850 11000 1850
Wire Wire Line
	11000 1850 11000 2000
Wire Wire Line
	11000 1850 11200 1850
Wire Wire Line
	11200 1850 11200 2000
Connection ~ 11000 1850
Wire Wire Line
	11200 1850 11400 1850
Wire Wire Line
	11400 1850 11400 2000
Connection ~ 11200 1850
Wire Wire Line
	10650 2250 10650 2500
Wire Wire Line
	11750 2600 11750 2500
Wire Wire Line
	10650 2500 11750 2500
Wire Wire Line
	11750 2700 11750 2800
$Comp
L power:GND #PWR0110
U 1 1 5E5CACB1
P 11750 2800
F 0 "#PWR0110" H 11750 2550 50  0001 C CNN
F 1 "GND" H 11850 2700 40  0000 C CNN
F 2 "" H 11750 2800 50  0001 C CNN
F 3 "" H 11750 2800 50  0001 C CNN
	1    11750 2800
	1    0    0    -1  
$EndComp
$Comp
L yageo:CC0402KRX7R9BB103 C110
U 1 1 5E5CACBA
P 11600 2050
F 0 "C110" V 11450 1850 40  0000 L CNN
F 1 "10n/50(X7R)" V 11525 1850 40  0000 L CNN
F 2 "murata:GRM15" H 11600 1980 10  0001 C CNN
F 3 "http://www.yageo.com/documents/recent/UPY-GPHC_X7R_6.3V-to-50V_18.pdf" H 11600 2130 10  0001 C CNN
F 4 "1005" V 11575 2075 10  0000 L CNN "Size"
F 5 "Yageo" H 11800 2350 50  0001 C CNN "Manufacturer"
F 6 "CC0402KRX7R9BB103" H 11900 2450 50  0001 C CNN "Manufacturer Part Number"
	1    11600 2050
	1    0    0    -1  
$EndComp
Wire Wire Line
	11600 2000 11600 1850
Wire Wire Line
	11600 1850 11400 1850
Connection ~ 11400 1850
Wire Wire Line
	11600 1850 11750 1850
Wire Wire Line
	11750 1850 11750 2000
Connection ~ 11600 1850
Wire Wire Line
	11600 2100 11600 2250
Wire Wire Line
	11600 2250 11750 2250
Wire Wire Line
	11750 2250 11750 2100
Wire Wire Line
	11750 2250 11750 2500
Connection ~ 11750 2250
Connection ~ 11750 2500
Wire Wire Line
	11750 1850 12200 1850
Connection ~ 11750 1850
$Comp
L samsung:CL21A226MOCLRNC C109
U 1 1 5E5CACD1
P 11400 2050
F 0 "C109" V 11250 1850 40  0000 L CNN
F 1 "22u/16(X5R)" V 11325 1850 40  0000 L CNN
F 2 "murata:GRM21" H 11400 1980 10  0001 C CNN
F 3 "http://www.samsungsem.com/kr/support/product-search/mlcc/CL21B105KBFNNNG.jsp" H 11400 2130 10  0001 C CNN
F 4 "2012" V 11375 2075 10  0000 L CNN "Size"
F 5 "Samsung Electro-Mechanics" H 11600 2350 50  0001 C CNN "Manufacturer"
F 6 "CL21A226MOCLRNC" H 11700 2450 50  0001 C CNN "Manufacturer Part Number"
	1    11400 2050
	1    0    0    -1  
$EndComp
$Comp
L samsung:CL21A226MOCLRNC C108
U 1 1 5E5CACDA
P 11200 2050
F 0 "C108" V 11050 1850 40  0000 L CNN
F 1 "22u/16(X5R)" V 11125 1850 40  0000 L CNN
F 2 "murata:GRM21" H 11200 1980 10  0001 C CNN
F 3 "http://www.samsungsem.com/kr/support/product-search/mlcc/CL21B105KBFNNNG.jsp" H 11200 2130 10  0001 C CNN
F 4 "2012" V 11175 2075 10  0000 L CNN "Size"
F 5 "Samsung Electro-Mechanics" H 11400 2350 50  0001 C CNN "Manufacturer"
F 6 "CL21A226MOCLRNC" H 11500 2450 50  0001 C CNN "Manufacturer Part Number"
	1    11200 2050
	1    0    0    -1  
$EndComp
Wire Wire Line
	10450 2150 10450 2300
$Comp
L power:GND #PWR0105
U 1 1 5E5CACE1
P 10450 2300
F 0 "#PWR0105" H 10450 2050 50  0001 C CNN
F 1 "GND" H 10550 2200 40  0000 C CNN
F 2 "" H 10450 2300 50  0001 C CNN
F 3 "" H 10450 2300 50  0001 C CNN
	1    10450 2300
	1    0    0    -1  
$EndComp
Wire Wire Line
	11400 2100 11400 2300
$Comp
L power:GND #PWR0108
U 1 1 5E5CACE8
P 11400 2300
F 0 "#PWR0108" H 11400 2050 50  0001 C CNN
F 1 "GND" H 11500 2200 40  0000 C CNN
F 2 "" H 11400 2300 50  0001 C CNN
F 3 "" H 11400 2300 50  0001 C CNN
	1    11400 2300
	1    0    0    -1  
$EndComp
Wire Wire Line
	11200 2100 11200 2300
$Comp
L power:GND #PWR0107
U 1 1 5E5CACEF
P 11200 2300
F 0 "#PWR0107" H 11200 2050 50  0001 C CNN
F 1 "GND" H 11300 2200 40  0000 C CNN
F 2 "" H 11200 2300 50  0001 C CNN
F 3 "" H 11200 2300 50  0001 C CNN
	1    11200 2300
	1    0    0    -1  
$EndComp
Wire Wire Line
	11000 2100 11000 2300
$Comp
L power:GND #PWR0106
U 1 1 5E5CACF6
P 11000 2300
F 0 "#PWR0106" H 11000 2050 50  0001 C CNN
F 1 "GND" H 11100 2200 40  0000 C CNN
F 2 "" H 11000 2300 50  0001 C CNN
F 3 "" H 11000 2300 50  0001 C CNN
	1    11000 2300
	1    0    0    -1  
$EndComp
Text Notes 8900 1800 0    25   ~ 0
VCC(abs,max)=42V
$Comp
L taiyo-yuden:NR5040T4R7N L101
U 1 1 5E5CACFF
P 10750 1850
F 0 "L101" H 10625 2000 40  0000 C CNN
F 1 "NR5040T4R7N" H 10950 1925 40  0000 C CNN
F 2 "taiyo-yuden:NR5040" H 10750 1850 50  0001 C CNN
F 3 "https://ds.yuden.co.jp/TYCOMPAS/ut/detail?pn=NR5040T4R7N%20%20&u=M" H 10725 1850 60  0001 C CNN
F 4 "Taiyo Yuden" H 10850 2100 80  0001 C CNN "Manufacturer"
F 5 "NR5040T4R7N" H 10950 2200 80  0001 C CNN "Manufacturer Part Number"
	1    10750 1850
	1    0    0    -1  
$EndComp
$Comp
L yageo:RC0402FR-0718KL R?
U 1 1 5E5CAD08
P 11750 2650
AR Path="/5D28FBB5/5E5CAD08" Ref="R?"  Part="1" 
AR Path="/5D26E750/5E5CAD08" Ref="R?"  Part="1" 
AR Path="/5E5CAD08" Ref="R102"  Part="1" 
F 0 "R102" V 11699 2698 40  0000 L CNN
F 1 "18kF" V 11775 2698 40  0000 L CNN
F 2 "yageo:R_0402" H 11750 2580 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 11750 2730 30  0001 C CNN
F 4 "1005" V 11826 2698 10  0000 L CNN "Size"
F 5 "Yageo" H 11950 2750 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-0718KL" H 12000 2800 50  0001 C CNN "Manufacturer Part Number"
	1    11750 2650
	0    1    1    0   
$EndComp
$Comp
L yageo:RC0402FR-0782KL R101
U 1 1 5E5CAD11
P 11750 2050
F 0 "R101" V 11699 2098 40  0000 L CNN
F 1 "82kF" V 11775 2098 40  0000 L CNN
F 2 "yageo:R_0402" H 11750 1980 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 11750 2130 30  0001 C CNN
F 4 "1005" V 11826 2098 10  0000 L CNN "Size"
F 5 "Yageo" H 11950 2150 50  0001 C CNN "Manufacturer"
F 6 "RC0402FR-0782KL" H 12000 2200 50  0001 C CNN "Manufacturer Part Number"
	1    11750 2050
	0    1    1    0   
$EndComp
Text Notes 11050 1700 0    50   ~ 0
Vout\n = 0.9 * (1 + 82k / 18k)\n = 5.0 V
Wire Wire Line
	2400 1400 3250 1400
Wire Wire Line
	2400 3400 3250 3400
$Comp
L ulo:ULO-PH409-1*2SF11 CN107
U 1 1 5E5A8864
P 6600 2350
F 0 "CN107" H 6678 2383 40  0000 L CNN
F 1 "ULO-PH409-1*2SF11" H 6678 2307 40  0000 L CNN
F 2 "ulo:ULO-PH409-1x2SX1" H 6600 2250 50  0001 C CNN
F 3 "http://www.ulogroup.com/upload/2013101815053045.pdf" H 6600 2250 50  0001 C CNN
F 4 "ULO Electronic" H 6700 2600 50  0001 C CNN "Manufacturer"
F 5 "ULO-PH409-1x2SX1" H 6800 2700 50  0001 C CNN "Manufacturer Part Number"
	1    6600 2350
	1    0    0    -1  
$EndComp
Wire Wire Line
	6400 2400 6300 2400
$Comp
L ulo:ULO-PH409-1*2SF11 CN105
U 1 1 5E642E0E
P 13950 1900
F 0 "CN105" H 14028 1933 40  0000 L CNN
F 1 "ULO-PH409-1*2SF11" H 14028 1857 40  0000 L CNN
F 2 "ulo:ULO-PH409-1x2SX1" H 13950 1800 50  0001 C CNN
F 3 "http://www.ulogroup.com/upload/2013101815053045.pdf" H 13950 1800 50  0001 C CNN
F 4 "ULO Electronic" H 14050 2150 50  0001 C CNN "Manufacturer"
F 5 "ULO-PH409-1x2SX1" H 14150 2250 50  0001 C CNN "Manufacturer Part Number"
	1    13950 1900
	1    0    0    -1  
$EndComp
Wire Wire Line
	13750 1850 13100 1850
Wire Wire Line
	13750 1950 13650 1950
$Comp
L power:GND #PWR0109
U 1 1 5E6C6D49
P 13650 2300
F 0 "#PWR0109" H 13650 2050 50  0001 C CNN
F 1 "GND" H 13750 2200 40  0000 C CNN
F 2 "" H 13650 2300 50  0001 C CNN
F 3 "" H 13650 2300 50  0001 C CNN
	1    13650 2300
	1    0    0    -1  
$EndComp
Wire Wire Line
	5650 1850 6200 1850
Wire Wire Line
	6400 2300 6200 2300
Wire Wire Line
	6200 2300 6200 1850
Connection ~ 6200 1850
Wire Wire Line
	6200 1850 7400 1850
Wire Wire Line
	6300 2950 5650 2950
$Comp
L ulo:ULO-PH409-1*2SF11 CN110
U 1 1 5E7F475D
P 6500 8500
F 0 "CN110" H 6578 8533 40  0000 L CNN
F 1 "ULO-PH409-1*2SF11" H 6578 8457 40  0000 L CNN
F 2 "ulo:ULO-PH409-1x2SX1" H 6500 8400 50  0001 C CNN
F 3 "http://www.ulogroup.com/upload/2013101815053045.pdf" H 6500 8400 50  0001 C CNN
F 4 "ULO Electronic" H 6600 8750 50  0001 C CNN "Manufacturer"
F 5 "ULO-PH409-1x2SX1" H 6700 8850 50  0001 C CNN "Manufacturer Part Number"
	1    6500 8500
	1    0    0    -1  
$EndComp
$Comp
L testpooint:SHORT_JUMPER R112
U 1 1 5E82A9B1
P 5250 8500
F 0 "R112" V 5199 8544 40  0000 L CNN
F 1 "SHORT_JUMPER" V 5275 8544 40  0000 L CNN
F 2 "TestPoint:JP_SMD" H 5250 8430 10  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 5250 8580 10  0001 C CNN
F 4 "1608" V 5326 8544 10  0000 L CNN "Size"
	1    5250 8500
	0    1    1    0   
$EndComp
Wire Wire Line
	5250 8450 5250 8250
Wire Wire Line
	5250 8250 5950 8250
Wire Wire Line
	5950 8250 5950 8450
Wire Wire Line
	5950 8450 6300 8450
Connection ~ 5250 8250
Wire Wire Line
	6300 8550 6150 8550
Connection ~ 6150 8550
Wire Wire Line
	6150 8550 6150 8950
Text Notes 6600 8700 0    40   ~ 0
Through Hole for\nExternal Resistor Setting
$Comp
L ulo:ULO-PH409-1*2SF11 CN111
U 1 1 5E866869
P 15000 8100
F 0 "CN111" H 15078 8133 40  0000 L CNN
F 1 "ULO-PH409-1*2SF11" H 15078 8057 40  0000 L CNN
F 2 "ulo:ULO-PH409-1x2SX1" H 15000 8000 50  0001 C CNN
F 3 "http://www.ulogroup.com/upload/2013101815053045.pdf" H 15000 8000 50  0001 C CNN
F 4 "ULO Electronic" H 15100 8350 50  0001 C CNN "Manufacturer"
F 5 "ULO-PH409-1x2SX1" H 15200 8450 50  0001 C CNN "Manufacturer Part Number"
	1    15000 8100
	1    0    0    -1  
$EndComp
Text Notes 15050 8350 0    40   ~ 0
Through Hole for\nChecking VOUT Voltage
$Comp
L ulo:ULO-PH409-1*4SF11 CN112
U 1 1 5E8D90FB
P 4300 9550
F 0 "CN112" H 4378 9591 50  0000 L CNN
F 1 "ULO-PH409-1*4SF11" H 4378 9500 50  0000 L CNN
F 2 "ulo:ULO-PH409-1x4SX1" H 4200 9700 50  0001 C CNN
F 3 "http://www.ulogroup.com/upload/2013101815053045.pdf" H 4300 9800 50  0001 C CNN
F 4 "ULO Electric" H 4400 9900 50  0001 C CNN "Manufacturer"
F 5 "ULO-PH409-1*4SF11" H 4500 10000 50  0001 C CNN "Manufacturer Part Number"
	1    4300 9550
	1    0    0    -1  
$EndComp
Text Notes 4400 9900 0    40   ~ 0
Through Hole for\nControl & Check Chager condition
$Comp
L yageo:RL1206FR-070R027L R?
U 1 1 5E9AA112
P 13500 8050
AR Path="/5C9C60CA/5E9AA112" Ref="R?"  Part="1" 
AR Path="/5E9AA112" Ref="R107"  Part="1" 
F 0 "R107" H 13500 8000 40  0000 C CNN
F 1 "27mF(1/4W)" H 13500 7950 40  0000 C CNN
F 2 "yageo:R_1206" H 13500 7980 10  0001 C CNN
F 3 "http://rohmfs.rohm.com/jp/products/databook/datasheet/passive/resistor/chip_resistor/mcr_g-j.pdf" H 13500 8130 10  0001 C CNN
F 4 "3216" H 13500 8111 10  0000 C CNN "Size"
F 5 "Yageo" H 13700 8350 50  0001 C CNN "Manufacturer"
F 6 "RL1206FR-070R027L" H 13800 8450 50  0001 C CNN "Manufacturer Part Number"
F 7 "Ever Ohms Tech" H 13900 8550 50  0001 C CNN "Substitute Manufacturer"
F 8 "CR1206F0R027P05" H 14000 8650 50  0001 C CNN "Substitute Manufacturer Part Number"
	1    13500 8050
	1    0    0    -1  
$EndComp
Wire Wire Line
	13550 8050 13650 8050
$Comp
L microchip:PAC1720-1-AIA-TR U?
U 1 1 5CBDA4B3
P 9850 5300
AR Path="/5CB4C022/5CBDA4B3" Ref="U?"  Part="1" 
AR Path="/5CBDA4B3" Ref="U103"  Part="1" 
F 0 "U103" H 9850 4783 40  0000 C CNN
F 1 "PAC1720-1-AIA-TR" H 9850 4707 40  0000 C CNN
F 2 "Housings_DFN_QFN:DFN-10-1EP_3x3mm_Pitch0.5mm_microchip_9Q" H 9750 5000 50  0001 C CNN
F 3 "http://ww1.microchip.com/downloads/en/DeviceDoc/20005386B.pdf" H 9850 5300 50  0001 C CNN
F 4 "microchip" H 9850 5300 40  0001 C CNN "Manufacturer"
F 5 "PAC1720-1-AIA-TR" H 9850 5300 40  0001 C CNN "Manufacturer Part Number"
	1    9850 5300
	1    0    0    -1  
$EndComp
Wire Wire Line
	9950 3750 14200 3750
Wire Wire Line
	14200 3750 14200 6800
Wire Wire Line
	14200 6800 13350 6800
Wire Wire Line
	13350 6800 13350 8050
Wire Wire Line
	9950 3750 9950 4600
Connection ~ 13350 8050
Wire Wire Line
	13350 8050 13450 8050
Wire Wire Line
	13650 8050 13650 6900
Wire Wire Line
	13650 6900 14300 6900
Wire Wire Line
	14300 6900 14300 3650
Wire Wire Line
	14300 3650 10100 3650
Connection ~ 13650 8050
Wire Wire Line
	10100 3650 10100 4600
Text Notes 1700 1950 0    40   ~ 0
Through Hole for \nAntenna
$Comp
L yageo:RC0402 R105
U 1 1 5E69A2EA
P 5900 7100
F 0 "R105" H 5900 7288 40  0000 C CNN
F 1 "OPEN" H 5900 7212 40  0000 C CNN
F 2 "yageo:R_0402" H 5900 7030 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 5900 7180 30  0001 C CNN
F 4 "1005" H 5900 7161 10  0000 C CNN "Size"
F 5 "Yageo" H 6100 7200 50  0001 C CNN "Manufacturer"
F 6 "RC0402" H 6150 7250 50  0001 C CNN "Manufacturer Part Number"
	1    5900 7100
	1    0    0    -1  
$EndComp
$Comp
L yageo:RC0402 R106
U 1 1 5E6A0826
P 6050 7250
F 0 "R106" V 5999 7298 40  0000 L CNN
F 1 "OPEN" V 6075 7298 40  0000 L CNN
F 2 "yageo:R_0402" H 6050 7180 30  0001 C CNN
F 3 "http://www.yageo.com/NewPortal/yageodocoutput?fileName=/pdf/R-Chip/PYu-RC_Group_51_RoHS_L_3.pdf" H 6050 7330 30  0001 C CNN
F 4 "1005" V 6126 7298 10  0000 L CNN "Size"
F 5 "Yageo" H 6250 7350 50  0001 C CNN "Manufacturer"
F 6 "RC0402" H 6300 7400 50  0001 C CNN "Manufacturer Part Number"
	1    6050 7250
	0    1    1    0   
$EndComp
$Comp
L power:GND #PWR?
U 1 1 5E6A2249
P 6050 7500
AR Path="/5C9C60CA/5E6A2249" Ref="#PWR?"  Part="1" 
AR Path="/5E6A2249" Ref="#PWR0116"  Part="1" 
F 0 "#PWR0116" H 6050 7250 50  0001 C CNN
F 1 "GND" H 6150 7400 40  0000 C CNN
F 2 "" H 6050 7500 50  0001 C CNN
F 3 "" H 6050 7500 50  0001 C CNN
	1    6050 7500
	1    0    0    -1  
$EndComp
Wire Wire Line
	6050 7500 6050 7400
Wire Wire Line
	6050 7200 6050 7100
Wire Wire Line
	6050 7100 5950 7100
Wire Wire Line
	5850 7100 5650 7100
$Comp
L ulo:ULO-PH409-1*2SF11 CN109
U 1 1 5E72017F
P 6600 7150
F 0 "CN109" H 6678 7183 40  0000 L CNN
F 1 "ULO-PH409-1*2SF11" H 6678 7107 40  0000 L CNN
F 2 "ulo:ULO-PH409-1x2SX1" H 6600 7050 50  0001 C CNN
F 3 "http://www.ulogroup.com/upload/2013101815053045.pdf" H 6600 7050 50  0001 C CNN
F 4 "ULO Electronic" H 6700 7400 50  0001 C CNN "Manufacturer"
F 5 "ULO-PH409-1x2SX1" H 6800 7500 50  0001 C CNN "Manufacturer Part Number"
	1    6600 7150
	1    0    0    -1  
$EndComp
Wire Wire Line
	6050 7100 6400 7100
Connection ~ 6050 7100
Wire Wire Line
	6400 7200 6300 7200
Wire Wire Line
	6300 7200 6300 7400
Wire Wire Line
	6300 7400 6050 7400
Connection ~ 6050 7400
Wire Wire Line
	6050 7400 6050 7300
Wire Wire Line
	5650 7100 5650 7750
Connection ~ 5650 7750
Wire Wire Line
	5650 7750 4950 7750
Text Notes 6700 7050 0    40   ~ 0
For Battery Monitor\nConnect to ADC
Text Notes 13900 1750 0    50   ~ 0
Through Hole for\n+5V/GND
Text Notes 6450 2200 0    50   ~ 0
Through Hole for\nVPP/GND
$Comp
L ulo:ULO-PH409-1*2SF11 CN102
U 1 1 5D02BBE9
P 1900 2250
F 0 "CN102" H 1819 2492 40  0000 C CNN
F 1 "ULO-PH409-1*2SF11" H 1819 2416 40  0000 C CNN
F 2 "ulo:ULO-PH409-1x2SX1" H 1900 2150 50  0001 C CNN
F 3 "http://www.ulogroup.com/upload/2013101815053045.pdf" H 1900 2150 50  0001 C CNN
F 4 "ULO Electronic" H 2000 2500 50  0001 C CNN "Manufacturer"
F 5 "ULO-PH409-1x2SX1" H 2100 2600 50  0001 C CNN "Manufacturer Part Number"
	1    1900 2250
	-1   0    0    -1  
$EndComp
Wire Wire Line
	12850 5800 12750 5800
Wire Wire Line
	12750 5800 12750 5700
Connection ~ 12750 5700
Wire Wire Line
	12750 5700 12850 5700
Wire Wire Line
	6300 2400 6300 2950
Wire Wire Line
	13650 1950 13650 2300
Wire Wire Line
	14600 8150 14800 8150
Wire Wire Line
	14600 8300 14600 8150
Connection ~ 14600 8150
Wire Wire Line
	14600 8050 14800 8050
Wire Wire Line
	13650 8050 14600 8050
Connection ~ 14600 8050
Connection ~ 11600 7450
Wire Wire Line
	11600 7450 11500 7450
Wire Wire Line
	11800 7350 12050 7350
Wire Wire Line
	12050 7350 12050 7200
Wire Wire Line
	12050 7200 12200 7200
$EndSCHEMATC
