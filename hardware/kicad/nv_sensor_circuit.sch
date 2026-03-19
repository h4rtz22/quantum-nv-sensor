EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "NV Sensor Circuit"
Date "2026-03-19"
Rev "1.0"
Comp "Hartz"
Comment1 "Quantum NV Diamond Sensor"
Comment2 "Underwater Navigation System"
$EndDescr

# Power supply
$Comp
L power:GND #PWR01
U 1 1 60000000
P 1000 2000
F 0 "#PWR01" H 1000 1750 50  0001 C CNN
F 1 "GND" H 1005 1827 50  0000 C CNN
F 2 "" H 1000 2000 50  0001 C CNN
F 3 "" H 1000 2000 50  0001 C CNN
	1    1000 2000
	1    0    0    -1  
$EndComp

$Comp
L power:+5V #PWR02
U 1 1 60000001
P 1000 1000
F 0 "#PWR02" H 1000 850 50  0001 C CNN
F 1 "+5V" H 1015 1173 50  0000 C CNN
F 2 "" H 1000 1000 50  0001 C CNN
F 3 "" H 1000 1000 50  0001 C CNN
	1    1000 1000
	1    0    0    -1  
$EndComp

$Comp
L power:+3.3V #PWR03
U 1 1 60000002
P 1500 1000
F 0 "#PWR03" H 1500 850 50  0001 C CNN
F 1 "+3.3V" H 1515 1173 50  0000 C CNN
F 2 "" H 1500 1000 50  0001 C CNN
F 3 "" H 1500 1000 50  0001 C CNN
	1    1500 1000
	1    0    0    -1  
$EndComp

# Microcontroller - Arduino Due
$Comp
L MCU_Module:Arduino_Due_X A1
U 1 1 60000010
P 4000 3000
F 0 "A1" H 4000 4500 50  0000 C CNN
F 1 "Arduino_Due" H 4000 4400 50  0000 C CNN
F 2 "Module:Arduino_Due" H 4000 3000 50  0001 C CNN
F 3 "https://store.arduino.cc/arduino-due" H 4000 3000 50  0001 C CNN
	1    4000 3000
	1    0    0    -1  
$EndComp

# ADC - ADS1115
$Comp
L Analog_ADC:ADS1115IDGS U1
U 1 1 60000020
P 6000 3000
F 0 "U1" H 6000 3500 50  0000 C CNN
F 1 "ADS1115" H 6000 3400 50  0000 C CNN
F 2 "Package_SO:TSSOP-10_3x3mm_P0.5mm" H 6000 3000 50  0001 C CNN
F 3 "http://www.ti.com/lit/ds/symlink/ads1115.pdf" H 6000 3000 50  0001 C CNN
	1    6000 3000
	1    0    0    -1  
$EndComp

# Laser driver
$Comp
L Transistor_FET:IRLZ44N Q1
U 1 1 60000030
P 7500 2000
F 0 "Q1" H 7700 2050 50  0000 L CNN
F 1 "IRLZ44N" H 7700 1950 50  0000 L CNN
F 2 "Package_TO_SOT_THT:TO-220-3_Vertical" H 7700 2000 50  0001 C CNN
F 3 "https://www.infineon.com/dgdl/irlz44n.pdf" H 7700 2000 50  0001 C CNN
	1    7500 2000
	1    0    0    -1  
$EndComp

# Photodiode amplifier
$Comp
L Amplifier_Operational:OPA380A U2
U 1 1 60000040
P 6000 4500
F 0 "U2" H 6000 4800 50  0000 L CNN
F 1 "OPA380A" H 6000 4700 50  0000 L CNN
F 2 "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" H 6000 4500 50  0001 C CNN
F 3 "http://www.ti.com/lit/ds/symlink/opa380.pdf" H 6000 4500 50  0001 C CNN
	1    6000 4500
	1    0    0    -1  
$EndComp

# High voltage supply for APD
$Comp
L Regulator_Switching:LM2577S-ADJ U3
U 1 1 60000050
P 8000 3500
F 0 "U3" H 8000 3800 50  0000 C CNN
F 1 "LM2577-ADJ" H 8000 3700 50  0000 C CNN
F 2 "Package_TO_SOT_SMD:TO-263-5_TabPin3" H 8000 3500 50  0001 C CNN
F 3 "http://www.ti.com/lit/ds/symlink/lm2577.pdf" H 8000 3500 50  0001 C CNN
	1    8000 3500
	1    0    0    -1  
$EndComp

# Connections (simplified)
Wire Wire Line
	4000 2500 6000 2500
Wire Wire Line
	6000 2500 6000 2800

Text Notes 1000 6000 0    50   ~ 0
NV Sensor Circuit Diagram\nConnections simplified for clarity\nFull schematic in nv_sensor_circuit_full.pdf
$EndSCHEMATC
