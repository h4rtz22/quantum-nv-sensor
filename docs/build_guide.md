# Build Guide - Quantum NV Sensor

Step-by-step instructions for building the NV diamond sensor.

## Phase 1: Component Acquisition (1-2 weeks)

### Critical Components
Order these first (longest lead times):

1. **NV Diamond** - [Adamas Nanotechnologies](https://www.adamasnano.com/)
   - Product: High density NV diamond
   - Specs: 3x3x0.5mm, polished, irradiated
   - Cost: ~$100-200
   - Lead time: 1-2 weeks

2. **Laser Module** - [Thorlabs CPS532](https://www.thorlabs.com/thorproduct.cfm?partnumber=CPS532)
   - Alternative: eBay 532nm 50mW TTL
   - Cost: $30-110

3. **Photodiode** - [Thorlabs PDA36A2](https://www.thorlabs.com/thorproduct.cfm?partnumber=PDA36A2)
   - Integrated amplifier
   - Cost: ~$280

### Electronics
- Arduino Due or Raspberry Pi 4
- ADS1115 ADC module
- ADF4351 microwave generator module (eBay)
- Various resistors, capacitors, connectors

### Optics
- Dichroic mirror: DMLP550 (Thorlabs)
- Long-pass filter: FEL0600 (Thorlabs)
- Objective lens: 10x microscope objective

### 3D Printed Parts
- Print all parts from `hardware/3d_models/`
- Material: PETG or ABS (waterproof)
- Total print time: ~24 hours

## Phase 2: Optical Assembly (2-3 days)

### Step 1: Diamond Holder
1. Clean diamond with isopropyl alcohol
2. Apply small amount of UV adhesive (Norland NOA61) to holder cavity
3. Place diamond with polished face up
4. Cure with UV lamp (365nm) for 5 minutes
5. Verify diamond is securely fixed

### Step 2: Laser Alignment
1. Mount laser in printed holder
2. Align laser beam perpendicular to optical base
3. Use IR card to visualize beam path
4. Ensure beam hits center of diamond holder position

### Step 3: Dichroic Mirror
1. Mount dichroic mirror at 45° angle
2. Position to reflect laser beam toward diamond
3. Verify reflected beam hits diamond center

### Step 4: Fluorescence Collection
1. Mount objective lens above diamond
2. Position to collect fluorescence (red light)
3. Add long-pass filter to block green laser light
4. Align photodiode to receive filtered light

### Step 5: Microwave Coil
1. Wind 3-5 turns of copper wire around diamond
2. Connect to MW generator output
3. Ensure coil doesn't block optical paths

## Phase 3: Electronics Assembly (1-2 days)

### Step 1: PCB Assembly
1. Solder components following schematic
2. Start with smallest components (resistors, capacitors)
3. Then ICs (ADS1115, OPA380)
4. Finally connectors and large components

### Step 2: Wiring
1. Connect photodiode to PCB input
2. Connect laser TTL to PCB output
3. Connect MW generator SPI to PCB
4. Connect Arduino/Raspberry Pi to PCB

### Step 3: Initial Testing
1. Power up (5V supply)
2. Check voltage rails (5V, 3.3V, 150V)
3. Test I2C communication with ADC
4. Verify laser control (ON/OFF)

## Phase 4: Software Setup (1 day)

### Install Dependencies
```bash
pip3 install numpy plotly filterpy scipy pyserial
```

### Upload Firmware
1. Open `firmware/nv_sensor_firmware.ino` in Arduino IDE
2. Select board: "Arduino Due"
3. Compile and upload
4. Open Serial Monitor (115200 baud)

### Test Software
```bash
# Test data acquisition
python3 software/nv_data_acquisition.py --port /dev/ttyUSB0 --duration 10

# Test navigation (simulation)
python3 software/quantum_navigator.py --simulate
```

## Phase 5: Calibration (1 day)

### Step 1: ODMR Spectrum
1. Run `MEASURE` command via Serial
2. Verify spectrum shows dip at ~2.87 GHz
3. Adjust MW frequency range if needed

### Step 2: Magnetic Field Calibration
1. Place sensor in known magnetic field (or shielded environment)
2. Run `CALIBRATE` command
3. Save calibration to EEPROM

### Step 3: Position Calibration
1. Move sensor to known positions
2. Record magnetic field readings
3. Build magnetic map of area

## Phase 6: Underwater Housing (2-3 days)

### Step 1: Assembly
1. Mount optical assembly in housing
2. Install optical window with O-ring
3. Route cables through cable gland
4. Seal all openings with marine epoxy

### Step 2: Pressure Testing
1. Test in shallow water (1m depth)
2. Check for leaks
3. Gradually increase depth
4. Rated depth: 50m

### Step 3: Buoyancy Adjustment
1. Add foam or weights as needed
2. Target: Neutral buoyancy
3. Secure mounting bracket

## Phase 7: Field Testing (ongoing)

### Pool Testing
1. Test in controlled environment
2. Verify all functions work underwater
3. Practice deployment and recovery

### Open Water Testing
1. Start in shallow, calm water
2. Compare with GPS (when surfaced)
3. Record accuracy data
4. Iterate and improve

## Troubleshooting

### No Fluorescence
- Check laser alignment
- Verify diamond is excited
- Check photodiode connections
- Increase laser power

### No ODMR Signal
- Verify MW generator output
- Check coil connections
- Adjust frequency range
- Increase MW power

### Erratic Readings
- Check electrical connections
- Verify grounding
- Shield from interference
- Calibrate sensor

### Water Ingress
- Check O-rings
- Verify seals
- Re-apply epoxy
- Test at shallow depth first

## Safety Notes

⚠️ **Laser Safety**
- Class 3B laser - never look directly at beam
- Use laser safety glasses (532nm)
- Keep beam path enclosed

⚠️ **High Voltage**
- 150V present on PCB
- Disconnect power before servicing
- Use insulated tools

⚠️ **Diving Safety**
- Always dive with buddy
- Test equipment before deep dives
- Have backup navigation
- Follow dive tables/computer

## Support

For help:
- GitHub Issues: https://github.com/h4rtz22/quantum-nv-sensor/issues
- Quantum Village Discord: https://discord.gg/quantumvillage
- Email: h4rtz22@gmail.com
