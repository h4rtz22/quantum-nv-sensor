# 3D Models for Quantum NV Sensor

This directory contains OpenSCAD files for 3D printed parts of the NV sensor.

## Files

### diamond_holder.scad
Holder for the 3x3x0.5mm NV diamond. Includes:
- Diamond cavity with precise dimensions
- Light paths for laser input and fluorescence output
- Mounting holes for M1.5 screws
- Integrated microwave coil holder

**Print settings:**
- Material: PETG or ABS (not PLA - degrades in water)
- Layer height: 0.1mm
- Infill: 50%
- Supports: No

### optical_base.scad
Base plate for mounting all optical components:
- Compatible with 30mm cage system (Thorlabs)
- Mounting positions for laser, dichroic mirror, diamond holder, and detector
- Cable management channels
- M3 mounting holes on 30mm grid

**Print settings:**
- Material: PETG or ABS
- Layer height: 0.2mm
- Infill: 30%
- Supports: No

### underwater_housing.scad
IP68 waterproof housing for underwater use:
- Rated for 50m depth
- Optical window mount (sapphire or borosilicate glass)
- Cable gland for waterproof cable entry
- Mounting bracket for diver's equipment
- O-ring grooves for sealing

**Print settings:**
- Material: ABS (required for waterproofing)
- Layer height: 0.2mm
- Infill: 50%
- Wall thickness: 4+ perimeters
- Supports: Yes (for overhangs)
- Post-processing: Sand and apply epoxy coating

## Exporting STL Files

Open each .scad file in OpenSCAD and render (F6), then export as STL (F7).

```bash
# Command line export (Linux/Mac)
openscad -o diamond_holder.stl diamond_holder.scad
```

## Assembly Notes

1. **Diamond mounting**: Use UV-curable optical adhesive (Norland NOA61) to fix diamond in holder
2. **Optical alignment**: Ensure all optical paths are perpendicular within 1 degree
3. **Waterproofing**: Use silicone O-rings (2mm cross-section) and waterproof grease
4. **Cable gland**: Use marine-grade epoxy to seal cable entry

## Bill of Materials (Printed Parts)

| Part | Quantity | Material | Time |
|------|----------|----------|------|
| Diamond holder | 1 | PETG | 2h |
| Optical base | 1 | PETG | 6h |
| Laser mount | 1 | PETG | 1h |
| Dichroic mount | 1 | PETG | 1h |
| Main housing | 1 | ABS | 8h |
| End cap | 1 | ABS | 3h |
| Cable gland | 1 | ABS | 1h |
| Mounting bracket | 1 | ABS | 2h |

Total print time: ~24 hours
