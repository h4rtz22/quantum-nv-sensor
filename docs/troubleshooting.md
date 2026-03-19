# Troubleshooting Guide

Common problems and solutions for the NV sensor.

## Optical Issues

### Problem: No Fluorescence

**Symptoms**: Photodiode shows no signal when laser is on

**Causes & Solutions**:

1. **Laser not aligned**
   - Check laser beam path with IR card
   - Adjust mirror mounts
   - Ensure beam hits diamond center

2. **Diamond not excited**
   - Verify diamond is in holder
   - Check laser wavelength (must be 532nm)
   - Increase laser power

3. **Photodiode not receiving light**
   - Check optical path for blockages
   - Verify filter is not blocking fluorescence
   - Align photodiode with output beam

4. **Diamond damaged**
   - NV centers degrade at >100°C
   - Check for physical damage
   - May need replacement

### Problem: Weak Fluorescence

**Symptoms**: Signal present but very low

**Solutions**:
- Clean optical surfaces
- Increase laser power (careful with heating)
- Check diamond NV density
- Verify photodiode gain setting

### Problem: Unstable Fluorescence

**Symptoms**: Signal fluctuates rapidly

**Causes**:
- Laser instability
- Mechanical vibration
- Electrical noise

**Solutions**:
- Use stable laser power supply
- Mount components rigidly
- Add shielding to photodiode cable

## Electronic Issues

### Problem: No Serial Communication

**Symptoms**: Can't connect to Arduino

**Solutions**:
1. Check USB cable (try different cable)
2. Verify correct COM port /dev/ttyUSB0
3. Reset Arduino
4. Re-upload firmware
5. Check baud rate (115200)

### Problem: ADC Not Responding

**Symptoms**: I2C scan doesn't find ADS1115

**Solutions**:
1. Check I2C wiring (SDA, SCL)
2. Verify pull-up resistors (10kΩ)
3. Check I2C address (0x48 default)
4. Test with I2C scanner sketch
5. Replace ADS1115 if damaged

### Problem: Erratic ADC Readings

**Symptoms**: Values jump around randomly

**Solutions**:
1. Add decoupling capacitors (100nF)
2. Shield analog input cables
3. Use differential measurement
4. Enable averaging in software
5. Check ground connections

### Problem: Laser Won't Turn On

**Symptoms**: Laser stays off despite command

**Solutions**:
1. Check MOSFET connections
2. Verify TTL signal reaches laser
3. Test laser manually (jumper 5V)
4. Check laser power supply
5. Replace laser module if dead

### Problem: High Voltage Not Working

**Symptoms**: No 150V output for APD

**⚠️ DANGER: High voltage present**

**Solutions**:
1. Check input voltage (5V)
2. Verify inductor connections
3. Check feedback resistors
4. Test with multimeter (carefully!)
5. Replace LM2577 if failed

## Microwave Issues

### Problem: No ODMR Signal

**Symptoms**: No dip in fluorescence spectrum

**Solutions**:
1. Check MW generator power
2. Verify coil connections
3. Adjust frequency range (2.8-2.9 GHz)
4. Increase MW power (careful with heating)
5. Check for interference

### Problem: Broad ODMR Peak

**Symptoms**: Dip is very wide, not sharp

**Causes**:
- Too much MW power
- Poor diamond quality
- Strong magnetic field gradients

**Solutions**:
- Reduce MW power
- Check diamond specifications
- Shield from external fields

### Problem: Multiple Peaks

**Symptoms**: Several dips in spectrum

**Causes**:
- Multiple NV orientations (normal)
- Stray magnetic fields
- MW frequency instability

**Solutions**:
- This is normal for bulk diamond
- Identify ms=0 ↔ ms=±1 transitions
- Use frequency lock if needed

## Software Issues

### Problem: Python Import Errors

**Symptoms**: `ModuleNotFoundError`

**Solutions**:
```bash
pip3 install numpy plotly filterpy scipy pyserial
```

If using Raspberry Pi:
```bash
sudo apt-get install python3-scipy python3-numpy
```

### Problem: Serial Permission Denied

**Symptoms**: Can't open /dev/ttyUSB0

**Solutions**:
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Or run with sudo (not recommended)
sudo python3 nv_data_acquisition.py
```

### Problem: Plotly Not Displaying

**Symptoms**: No browser window opens

**Solutions**:
1. Install browser: `sudo apt-get install chromium-browser`
2. Use offline mode: `import plotly.io as pio; pio.renderers.default = "browser"`
3. Save to HTML and open manually

## Navigation Issues

### Problem: Position Drift

**Symptoms**: Position estimate drifts over time

**Causes**:
- IMU bias
- Magnetic interference
- Poor calibration

**Solutions**:
1. Recalibrate IMU
2. Check for magnetic interference
3. Use magnetic map if available
4. Add GPS waypoints for correction

### Problem: Jumping Position

**Symptoms**: Position jumps suddenly

**Causes**:
- Magnetic anomaly
- Software error
- Sensor dropout

**Solutions**:
1. Check magnetic field readings
2. Add outlier rejection in software
3. Verify all sensors working
4. Check data quality flags

## Underwater Issues

### Problem: Leakage

**Symptoms**: Water inside housing

**Solutions**:
1. Check O-rings for damage
2. Verify proper seating
3. Apply silicone grease
4. Check window seal
5. Test at shallow depth first

### Problem: Fogging

**Symptoms**: Condensation inside housing

**Solutions**:
1. Add desiccant packet
2. Seal housing in dry environment
3. Use anti-fog coating
4. Warm up before dive

### Problem: Biofouling

**Symptoms**: Optical window covered in algae

**Solutions**:
1. Apply anti-fouling coating
2. Clean before each dive
3. Use copper-based paint (around window, not on)
4. Regular maintenance

## Performance Issues

### Problem: Low Sensitivity

**Symptoms**: Can't detect small field changes

**Solutions**:
1. Increase integration time
2. Improve optical collection efficiency
3. Use better diamond (higher NV density)
4. Reduce noise (shielding, filtering)

### Problem: Slow Update Rate

**Symptoms**: Position updates too slowly

**Solutions**:
1. Reduce ODMR sweep points
2. Optimize code
3. Use faster microcontroller
4. Parallel processing (Raspberry Pi)

## Getting Help

If problem persists:

1. **Check GitHub Issues**: https://github.com/h4rtz22/quantum-nv-sensor/issues
2. **Quantum Village Discord**: https://discord.gg/quantumvillage
3. **Email**: h4rtz22@gmail.com

When asking for help, include:
- Description of problem
- Steps to reproduce
- Error messages
- Hardware/software versions
- Photos if relevant
