# KiCad Hardware Design

This directory contains circuit schematics and PCB layouts for the NV sensor electronics.

## Files

### Circuit Schematics

- `nv_sensor_circuit.sch` - Main circuit schematic
- `nv_sensor_circuit_full.pdf` - Complete schematic (PDF export)

### PCB Layout

- `nv_sensor_pcb.kicad_pcb` - PCB layout file
- `nv_sensor_pcb_gerber.zip` - Gerber files for manufacturing

## Circuit Blocks

### 1. Microcontroller (Arduino Due)
- Main processing unit
- GPIO control for laser and MW generator
- I2C communication with ADC
- USB/Serial for data output

### 2. ADC (ADS1115)
- 16-bit resolution
- 4 differential channels
- I2C interface
- Programmable gain amplifier (PGA)

### 3. Photodiode Amplifier (OPA380)
- Transimpedance amplifier configuration
- Low noise (2.5 nV/√Hz)
- High speed (80 MHz GBW)
- Gain: 10^6 V/A (1MΩ feedback resistor)

### 4. Laser Driver
- MOSFET switch (IRLZ44N) for TTL control
- Adjustable current (optional PWM)
- Protection diode

### 5. High Voltage Supply (LM2577)
- Boost converter 5V → 150V
- For APD bias voltage
- Adjustable output
- Current limiting

### 6. Microwave Generator Interface
- SPI connection to ADF4351 module
- Level shifters (3.3V ↔ 5V)
- Optional: Integrated ADF4351 on PCB

## Bill of Materials

| Component | Value | Package | Quantity | Reference |
|-----------|-------|---------|----------|-----------|
| U1 | ADS1115IDGS | TSSOP-10 | 1 | ADC |
| U2 | OPA380AID | SOIC-8 | 1 | TIA |
| U3 | LM2577S-ADJ | TO-263 | 1 | HV Supply |
| Q1 | IRLZ44N | TO-220 | 1 | Laser Switch |
| R1-R4 | 10kΩ | 0805 | 4 | Pull-ups |
| R5 | 1MΩ | 0805 | 1 | TIA Gain |
| R6 | 100Ω | 0805 | 1 | Current limit |
| C1-C4 | 100nF | 0805 | 4 | Decoupling |
| C5 | 10µF | 1206 | 1 | Filter |
| C6 | 1µF | 1206 | 1 | HV filter |
| L1 | 100µH | Inductor | 1 | Boost inductor |
| D1 | 1N4007 | DO-41 | 1 | Protection |
| D2 | BAV99 | SOT-23 | 1 | ESD protection |
| J1 | USB-B | Connector | 1 | Power/Data |
| J2 | BNC | Connector | 1 | Photodiode |
| J3 | SMA | Connector | 1 | MW output |

## PCB Specifications

- **Size**: 100mm x 80mm
- **Layers**: 2 (signal + ground)
- **Thickness**: 1.6mm
- **Material**: FR-4
- **Finish**: HASL (or ENIG for better contacts)
- **Min trace width**: 0.25mm
- **Min via size**: 0.3mm

## Assembly Notes

1. **ESD sensitive**: Use ESD protection when handling ADS1115 and OPA380
2. **High voltage**: Be careful with LM2577 circuit - up to 150V
3. **Thermal**: Ensure adequate cooling for laser driver MOSFET
4. **Shielding**: Add copper tape shielding around photodiode amplifier

## Manufacturing

Recommended PCB manufacturers:
- JLCPCB (China) - Low cost, good quality
- PCBWay (China) - Fast turnaround
- OSH Park (USA) - Purple PCBs, good for prototypes

Gerber files can be generated from KiCad: File → Fabrication Outputs → Gerbers

## Testing

After assembly, test each block:
1. Power supply (5V and 3.3V)
2. ADC communication (I2C scan)
3. Laser driver (TTL control)
4. Photodiode amplifier (input test signal)
5. High voltage supply (measure 150V output)
6. Full system integration
