# Theory of Operation

This document explains the physics behind the NV diamond sensor.

## NV Centers in Diamond

### What are NV Centers?

Nitrogen-Vacancy (NV) centers are point defects in the diamond crystal lattice where:
- A carbon atom is replaced by a nitrogen atom
- An adjacent lattice site is vacant (missing carbon)

This creates a color center that absorbs green light (532nm) and emits red fluorescence (637nm).

### Energy Level Structure

The NV center has a unique energy level structure:

```
Excited State (¹E)
       |
   637nm emission
       |
   Triplet State (³E) -------- Microwave transition (2.87 GHz)
      / \
     /   \
    /     \
   |  ms=0 |  ms=±1
   |       |
   | 2.87  | GHz
   |  split|
   |       |
Ground State (³A₂)
```

Key transitions:
- **Optical**: 532nm excitation → 637nm fluorescence
- **Spin**: ms=0 ↔ ms=±1 at 2.87 GHz (zero-field splitting)

## Optically Detected Magnetic Resonance (ODMR)

### Principle

When microwaves are applied at the resonant frequency:
1. Electrons in ms=0 state are pumped to ms=±1
2. ms=±1 states have lower fluorescence intensity
3. This creates a dip in the fluorescence spectrum

### Magnetic Field Sensing

The resonant frequency depends on the magnetic field:

```
f = D ± γ * B∥

Where:
- D = 2.87 GHz (zero-field splitting)
- γ = 28.024 GHz/T (gyromagnetic ratio)
- B∥ = magnetic field parallel to NV axis
```

The frequency shift is proportional to the magnetic field strength.

### Vector Magnetometry

Diamond has four NV orientations along crystallographic axes. By measuring all four, we can reconstruct the full magnetic field vector:

```
B = (Bx, By, Bz)
```

## Navigation Principle

### Magnetic Map Matching

The Earth has a magnetic field that varies with position:

```
B(x,y,z) = B_earth + B_local(x,y,z)
```

By measuring B and comparing to a pre-recorded map, we can estimate position.

### Sensor Fusion

The NV magnetometer alone has drift. We combine it with:

1. **Gyroscope**: Measures rotation rate
   - Integrate to get orientation
   - No drift in orientation (short term)

2. **Accelerometer**: Measures acceleration
   - Double integrate to get position
   - High drift (needs correction)

3. **NV Magnetometer**: Measures magnetic field
   - Reference to magnetic map
   - Low drift, absolute reference

### Kalman Filter

We use an Extended Kalman Filter to fuse sensors:

**State vector**: x = [x, y, z, vx, vy, vz, roll, pitch, yaw]ᵀ

**Prediction** (from IMU):
```
xₖ = F·xₖ₋₁ + B·uₖ
Pₖ = F·Pₖ₋₁·Fᵀ + Q
```

**Update** (from magnetometer):
```
y = z - h(xₖ)
S = H·Pₖ·Hᵀ + R
K = Pₖ·Hᵀ·S⁻¹
xₖ = xₖ + K·y
Pₖ = (I - K·H)·Pₖ
```

## Performance Characteristics

### Sensitivity

Theoretical sensitivity:
```
η ≈ (ℏ / gₑμ_B) * √(1 / N·T₂*·t)

Where:
- N = number of NV centers (~10¹²)
- T₂* = coherence time (~1 µs)
- t = measurement time
```

Typical values: 1-10 nT/√Hz

### Spatial Resolution

Depends on:
- Magnetic field gradient (~10-100 nT/m)
- Sensor sensitivity (~1 nT)
- Map accuracy

Typical: 1-10 meters

### Update Rate

Limited by:
- ODMR sweep time (~10-100 ms)
- Data processing (~1-10 ms)

Typical: 10-100 Hz

## Advantages vs Other Technologies

| Technology | Precision | Drift | Size | Cost |
|------------|-----------|-------|------|------|
| NV Diamond | ~1m | Low | Small | Medium |
| MEMS IMU | ~km | High | Tiny | Low |
| Fiber Optic Gyro | ~10m | Medium | Large | High |
| Atomic Vapor | ~0.1m | Low | Medium | Very High |

## Limitations

### Temperature Sensitivity

The zero-field splitting D changes with temperature:
```
dD/dT ≈ -74 kHz/K
```

Requires temperature compensation or stabilization.

### Magnetic Interference

Nearby ferromagnetic materials affect measurements. Solutions:
- Shielding (mu-metal)
- Calibration
- Background subtraction

### Depth Limitations

Underwater operation challenges:
- Pressure (mechanical stress)
- Biofouling (optical window)
- Limited GPS for calibration

## Further Reading

1. Doherty et al., "The nitrogen-vacancy colour centre in diamond," Physics Reports, 2013
2. Rondin et al., "Magnetometry with nitrogen-vacancy defects in diamond," Rep. Prog. Phys., 2014
3. Barry et al., "Sensitivity optimization for NV-diamond magnetometry," Rev. Mod. Phys., 2020
